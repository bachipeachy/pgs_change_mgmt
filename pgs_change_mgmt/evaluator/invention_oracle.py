"""Invention oracle (Phase 5c) — did the builder introduce anything the Build Sheet did not authorise?

The thin-slice lesson was that an FQDN-only invention check has a blind spot: a builder can copy every
FQDN faithfully yet still invent a *field*, a *routing outcome*, or a *store* — design decisions that
never appear as FQDNs. This oracle closes that blind spot, and (Patch 3) separates two severities:

  STRUCTURAL invention (ERROR) — a token that changes the artifact's contract: an unauthorised FQDN,
      JSONPath field, routing-outcome label, or store. The sheet under-specified it, or the builder
      disobeyed. This is an architectural failure and must gate.

  TEXT invention (WARN) — the same kind of token appearing only in prose / descriptive lines (the
      builder editorialised) without entering a structural position. Documentation drift, not a
      contract change. Worth surfacing, not worth failing the build.

Authority lives in the sheet: `authorized_tokens` derives the permitted set from the (now
projection-complete) Build Sheet — FQDNs, composition/IO fields, routing labels, entity stores.
Anything outside that set, in a structural position, is structural invention.

This module — not `convergence` — owns invention (Patch 4): convergence measures builder agreement;
the oracle measures conformance to the specification. Two responsibilities, two modules.
"""

from __future__ import annotations

import re

from ..engine.build_sheet import BuildSheetModel, code_part

_FQDN = re.compile(r"(?:[a-z][a-z0-9_.]*::)?((?:CC|CS|CT|IN|WF|RB|EV|AC|STRUCTURE|TI)_[A-Z0-9_]*_V\d+)")
# an UPPER_SNAKE label that is NOT an artifact FQDN (e.g. SUCCESS, VIOLATION, ALREADY_EXISTS, ACK, NACK)
_LABEL = re.compile(r"\b([A-Z][A-Z0-9]+(?:_[A-Z0-9]+)*)\b")
# a JSONPath reference, e.g. $.results.CC_X.block_hash  /  $.payload.height — the LEAF is the field
_JSONPATH = re.compile(r"\$\.[A-Za-z0-9_.\[\]]+")
# JSONPath structural roots, not fields (the addressable envelope, governed by the runtime, not the sheet)
_JSONPATH_ROOTS = {"results", "payload", "data", "state", "input", "inputs", "output", "outputs", "context"}
# tokens that are UPPER_SNAKE but are structural noise, never routing outcomes
_LABEL_NOISE = {"GAP", "STOP", "RULES", "PART", "NEW", "EXTEND", "REPLACE", "EXIT", "OK", "TODO", "NA"}

# a line carries CONTRACT structure (vs prose) if it is a table row, a JSONPath, or a routing arrow
_STRUCTURAL_LINE = re.compile(r"[|]|\$\.|→|->")


def artifact_codes(text: str) -> set[str]:
    return {m for m in _FQDN.findall(text or "") if m}


def sheet_codes(sheet: BuildSheetModel) -> set[str]:
    """Every FQDN the Build Sheet authorises — the artifact plus every code in any field."""
    codes: set[str] = set()
    if (cp := code_part(sheet.code)):
        codes.add(cp)
    for fv in sheet.all_fields().values():
        codes |= _codes_in(fv.value)
    return codes


def _codes_in(v) -> set[str]:
    out: set[str] = set()
    if isinstance(v, list):
        for r in v:
            out |= _codes_in(r)
    elif isinstance(v, dict):
        for vv in v.values():
            out |= _codes_in(vv)
    else:
        out |= {m for m in _FQDN.findall(str(v) if v is not None else "")}
    return out


def _strings(v) -> list[str]:
    if isinstance(v, list):
        return [s for r in v for s in _strings(r)]
    if isinstance(v, dict):
        return [s for vv in v.values() for s in _strings(vv)]
    return [str(v)] if v is not None else []


def authorized_tokens(sheet: BuildSheetModel) -> dict[str, set[str]]:
    """The permitted token set, by category, derived from the Build Sheet's governed fields."""
    fqdns = sheet_codes(sheet)

    # routing labels — UPPER_SNAKE tokens in the sheet's routing/outcome fields
    labels: set[str] = set()
    for name in ("result_routing", "outcomes", "execution_graph", "admission"):
        for fv in (sheet.part_b.get(name),):
            if fv is not None:
                for s in _strings(fv.value):
                    labels |= {m for m in _LABEL.findall(s) if m not in _LABEL_NOISE}
    labels -= fqdns  # FQDNs are their own category

    # fields — composition IO + declared inputs/outputs + the governed entity vocabulary (block_id, …),
    # grounded from compiled entities so a builder transcribing a canonical field is never flagged.
    fields: set[str] = set(getattr(sheet, "entity_fields", ()) or ())
    for name in ("inputs", "outputs", "pipeline"):
        fv = sheet.part_b.get(name)
        if fv is None:
            continue
        for s in _strings(fv.value):
            fields |= {t.strip() for t in re.split(r"[,\s;|]+", s) if re.fullmatch(r"[a-z][a-z0-9_]+", t.strip() or "")}

    # stores — entity-store identifiers
    stores: set[str] = set()
    fv = sheet.part_b.get("entity_stores")
    if fv is not None:
        for s in _strings(fv.value):
            stores |= {t for t in re.split(r"[\s,;|]+", s) if t and (t.endswith(".json") or t.endswith(".jsonl") or t.isupper())}

    return {"fqdns": fqdns, "labels": labels, "fields": fields, "stores": stores}


def _candidates(artifact_md: str) -> dict[str, dict[str, bool]]:
    """Each structural-looking token in the artifact → whether it ever appears on a structural line.

    Returns {category: {token: appears_structurally}}. A token appearing only on prose lines is a
    TEXT-invention candidate; one appearing on any structural line is a STRUCTURAL-invention candidate.
    """
    cats: dict[str, dict[str, bool]] = {"fqdns": {}, "labels": {}, "fields": {}}
    for line in (artifact_md or "").splitlines():
        structural = bool(_STRUCTURAL_LINE.search(line))
        for tok in _FQDN.findall(line):
            cats["fqdns"][tok] = cats["fqdns"].get(tok, False) or True  # an FQDN is always structural
        if "→" in line or "->" in line or "rout" in line.lower() or "outcome" in line.lower():
            for tok in _LABEL.findall(line):
                if tok not in _LABEL_NOISE:
                    cats["labels"][tok] = cats["labels"].get(tok, False) or structural
        for path in _JSONPATH.findall(line):
            segs = [s for s in re.split(r"[.\[\]]+", path) if s and s != "$"]
            leaf = segs[-1] if segs else ""
            if re.fullmatch(r"[a-z][a-z0-9_]+", leaf) and leaf not in _JSONPATH_ROOTS:
                cats["fields"][leaf] = True  # a JSONPath leaf is a structural field position
    return cats


def structural_invention(artifact_md: str, sheet: BuildSheetModel) -> dict[str, list[str]]:
    """Unauthorised tokens in STRUCTURAL positions, by category (ERROR severity). Empty ⇒ the artifact
    introduces no design beyond the sheet at field/label/store level (ASSERT_ZERO_DESIGN_INVENTION)."""
    auth = authorized_tokens(sheet)
    cand = _candidates(artifact_md)
    out: dict[str, list[str]] = {}
    for cat, key in (("fqdns", "fqdns"), ("labels", "labels"), ("fields", "fields")):
        bad = sorted(t for t, structural in cand[cat].items()
                     if structural and t not in auth[key])
        if bad:
            out[cat] = bad
    return out


def text_invention(artifact_md: str, sheet: BuildSheetModel) -> dict[str, list[str]]:
    """Unauthorised structural-looking tokens appearing only in PROSE (WARN severity) — documentation
    drift, not a contract change. Excludes anything already flagged structurally."""
    auth = authorized_tokens(sheet)
    cand = _candidates(artifact_md)
    out: dict[str, list[str]] = {}
    for cat, key in (("labels", "labels"),):
        bad = sorted(t for t, structural in cand[cat].items()
                     if not structural and t not in auth[key])
        if bad:
            out[cat] = bad
    return out


def zero_invention(artifact_md: str, sheet: BuildSheetModel) -> list[str]:
    """The FQDN-level structural invention slice — kept for continuity with the Phase-5 measures."""
    return structural_invention(artifact_md, sheet).get("fqdns", [])

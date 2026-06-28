"""Design-Intent (Stage 6b) cross-register oracle — binding-FQDN integrity.

The generic structural oracle (`DossierStageRenderer.check`) validates each register in isolation:
required-population, per-row traceability, controlled vocabulary, business-language, and FQDN
well-formedness. Stage 6b additionally needs CROSS-register guarantees no single register can
express, because 6b assigns the IMMUTABLE binding FQDNs the whole build depends on:

  * referenced ⇒ declared — a NEW code used in topology/RB must be a row in `new_artifacts`
                            (catches CTs/EVs referenced but never declared)
  * genuinely new        — a `new_artifacts` code must NOT already exist in the snapshot (collision)
  * reconciled counts    — `artifact_summary` NEW total == rows of `new_artifacts`
  * one canonical spelling — a near-duplicate of a more-frequent sibling token is a likely typo
                            (the GENESIS→GENEISIS class that silently mints a second artifact)

These run after the generic check; their issues mark the offending register dirty so the stage's
governed coverage drops — a typo'd binding FQDN can no longer score 5/5.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

# code-part extractor: optional domain prefix, then PREFIX_NAME_V<n>
_CODE = re.compile(r"(?:[a-z][a-z0-9_.]*::)?((?:CC|CS|CT|IN|WF|RB|EV|AC|STRUCTURE|TI)_[A-Z0-9_]*_V\d+)")
_FAMILY = {"CC", "CS", "CT", "IN", "WF", "RB", "EV", "AC", "STRUCTURE", "TI"}
_TERMINALS = {"EXIT", "EXIT_SUCCESS"}


def _code_part(s: Any) -> str | None:
    m = _CODE.search(str(s))
    return m.group(1) if m else None


def _codes_in(rows: list | None, *keys: str) -> set[str]:
    out: set[str] = set()
    for r in rows or []:
        if isinstance(r, str):                       # back-compat: a free-form handoff is a str list
            cp = _code_part(r)
            if cp:
                out.add(cp)
            continue
        if not isinstance(r, dict):
            continue
        for k in keys:
            cp = _code_part(r.get(k, ""))
            if cp:
                out.add(cp)
    return out


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a or not b:
        return max(len(a), len(b))
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _common_prefix_len(a: str, b: str) -> int:
    n = 0
    for ca, cb in zip(a, b):
        if ca != cb:
            break
        n += 1
    return n


def _semantic_tokens(code: str) -> list[str]:
    """The semantic tokens of a code — family prefix and version suffix dropped."""
    parts = [p for p in code.split("_") if p and not re.fullmatch(r"V\d+", p)]
    if parts and parts[0] in _FAMILY:
        parts = parts[1:]
    return parts


def _exists(grounding, code_part: str) -> bool:
    """Does this code resolve in the snapshot? A grounding failure returns False (don't false-flag)."""
    try:
        env = grounding.query("vocab_search", term=code_part)
    except Exception:
        return False
    res = env.get("result") if isinstance(env, Mapping) else None
    return bool(res)


def check_design_intent(data: dict[str, list[dict[str, Any]]], grounding) -> list[tuple[str, str]]:
    """Cross-register checks for Stage 6b. Returns (register_id, message) issues."""
    issues: list[tuple[str, str]] = []
    new_rows = data.get("new_artifacts") or []
    declared_new = {cp for r in new_rows if (cp := _code_part(r.get("code", "")))}
    existing = _codes_in(data.get("existing_inventory"), "fqdn")
    declared = declared_new | existing

    referenced = _codes_in(data.get("execution_topology"), "node")
    referenced |= _codes_in(data.get("rb_declarations"),
                            "rb_code", "binds_wf", "cs_bindings", "storage_structure")
    referenced |= _codes_in(data.get("structure_stores"), "used_by")

    # 1. referenced ⇒ declared
    for code in sorted(referenced - declared):
        if code in _TERMINALS:
            continue
        if not _exists(grounding, code):
            issues.append(("new_artifacts",
                f"'{code}' is referenced (topology/RB) but neither declared in new_artifacts "
                f"nor existing in the snapshot — undeclared artifact"))

    # 2. genuinely new — a new code must not already exist
    for code in sorted(declared_new):
        if _exists(grounding, code):
            issues.append(("new_artifacts",
                f"'{code}' is marked NEW but already exists in the snapshot — collision "
                f"(reuse via existing_inventory, do not re-mint)"))

    # 3. count reconciliation
    summary = data.get("artifact_summary") or []
    if summary:
        new_total = 0
        for r in summary:
            if str(r.get("action", "")).strip().upper() == "NEW":
                digits = re.sub(r"[^0-9]", "", str(r.get("count", "0")))
                new_total += int(digits or 0)
        if new_total != len(declared_new):
            issues.append(("artifact_summary",
                f"artifact_summary NEW total ({new_total}) != new_artifacts rows "
                f"({len(declared_new)}) — reconcile §7 with §3"))

    # 4. one canonical spelling — an INTERNAL near-duplicate of a sibling token is a likely typo.
    # Morphological suffix variants (REGISTER/REGISTERED, VALIDATE/VALIDATOR, BLOCK/BLOCKS) share a
    # long common prefix and diverge only near the END — legitimate, not typos. A typo like
    # GENESIS→GENEISIS diverges INTERNALLY (early). The common-prefix test separates the two.
    freq: dict[str, int] = {}
    for code in declared_new | referenced:
        for tok in _semantic_tokens(code):
            if len(tok) >= 5:
                freq[tok] = freq.get(tok, 0) + 1
    toks = list(freq.items())
    seen: set[tuple[str, str]] = set()
    for a, (t, ft) in enumerate(toks):
        for u, fu in toks[a + 1:]:
            if _levenshtein(t, u) > 2:
                continue
            if _common_prefix_len(t, u) >= min(len(t), len(u)) - 2:  # diverges late ⇒ morphological
                continue
            key = tuple(sorted((t, u)))
            if key in seen:
                continue
            seen.add(key)
            rare, common = (t, u) if ft <= fu else (u, t)
            issues.append(("new_artifacts",
                f"token '{rare}' is a near-duplicate of '{common}' (internal difference) — likely "
                f"a misspelling that mints a second immutable artifact (use one spelling)"))
    return issues


def check_cc_composition(data: dict[str, list[dict[str, Any]]], grounding) -> list[tuple[str, str]]:
    """Cross-register checks for Stage 6b §6 Capability Composition (optional during rollout).

    Composition declares the inside of each new CC — the CT/CS steps it is built from. Checks:

      * each `cc_code` is a declared CC (new_artifacts / existing_inventory) that also appears as a
        node in `execution_topology` — a composed CC with no routed home is orphaned
      * each `capability` is a CT or CS (a CC composes only CT/CS), and is declared in new_artifacts
        or grounded existing — codes verbatim, same immutability as every binding FQDN
      * the `kind` cell matches the capability family (a CT row ⇒ CT_ code; a CS row ⇒ CS_)

    Empty register ⇒ no issues (optional during rollout). Issues mark `cc_composition` dirty.
    """
    issues: list[tuple[str, str]] = []
    rows = data.get("cc_composition") or []
    if not rows:
        return issues

    declared_new = {cp for r in (data.get("new_artifacts") or []) if (cp := _code_part(r.get("code", "")))}
    declared = declared_new | _codes_in(data.get("existing_inventory"), "fqdn")
    topo_nodes = _codes_in(data.get("execution_topology"), "node")

    for r in rows:
        if not isinstance(r, dict):
            continue
        cc = _code_part(r.get("cc_code", ""))
        cap = _code_part(r.get("capability", ""))
        kind = str(r.get("kind", "")).strip().upper()

        if cc:
            if cc not in declared and not _exists(grounding, cc):
                issues.append(("cc_composition",
                    f"composed CC '{cc}' is not a declared CC (new_artifacts / existing_inventory)"))
            elif cc not in topo_nodes:
                issues.append(("cc_composition",
                    f"composed CC '{cc}' does not appear as a node in execution_topology — orphaned composition"))

        if cap:
            fam = cap.split("_", 1)[0]
            if fam not in {"CT", "CS"}:
                issues.append(("cc_composition",
                    f"composition step '{cap}' is a {fam} — a CC composes only CT/CS capabilities"))
            elif cap not in declared and not _exists(grounding, cap):
                issues.append(("cc_composition",
                    f"capability '{cap}' is neither declared in new_artifacts nor existing in the snapshot"))
            if kind in {"CT", "CS"} and kind != fam:
                issues.append(("cc_composition",
                    f"step kind '{kind}' != capability family '{fam}' for '{cap}'"))
    return issues


def check_authoring_mandate(data: dict[str, list], upstream: dict[str, list]) -> list[tuple[str, str]]:
    """Cross-STAGE checks for Stage 7 (Authoring Mandate). S7 must ORDER the codes Stage 6b
    assigned — never introduce or re-spell one. `upstream` is the consumed Stage 6b projection.

      * every code in build_order / critical_path / field_declarations traces to a Stage 6b
        register (`new_artifacts` or `existing_inventory`) — blocks typo re-introduction
      * `step` numbering is contiguous from 1 (a gap = a silently dropped artifact)
      * `mandate_artifact_summary` NEW total reconciles with Stage 6b `new_artifacts`
    """
    issues: list[tuple[str, str]] = []
    declared = _codes_in(upstream.get("new_artifacts"), "code") \
        | _codes_in(upstream.get("existing_inventory"), "fqdn")

    for rid in ("build_order", "critical_path", "field_declarations"):
        for r in data.get(rid) or []:
            cp = _code_part(r.get("code", "")) if isinstance(r, dict) else _code_part(r)
            if cp and cp not in declared:
                issues.append((rid,
                    f"'{cp}' is not in any Stage 6b register (new_artifacts / existing_inventory) — "
                    f"S7 orders codes, it does not introduce or re-spell them"))

    steps = [int(s) for r in (data.get("build_order") or [])
             if isinstance(r, dict) and (s := str(r.get("step", "")).strip()).isdigit()]
    if steps and sorted(steps) != list(range(1, len(steps) + 1)):
        issues.append(("build_order",
            f"step numbering is not contiguous from 1: {sorted(steps)} — a gap means a dropped artifact"))

    summary = data.get("mandate_artifact_summary") or []
    if summary:
        new_total = sum(int(re.sub(r"[^0-9]", "", str(r.get("count", "0"))) or 0)
                        for r in summary if str(r.get("action", "")).strip().upper() == "NEW")
        declared_new = len(_codes_in(upstream.get("new_artifacts"), "code"))
        if new_total != declared_new:
            issues.append(("mandate_artifact_summary",
                f"NEW count ({new_total}) != Stage 6b new_artifacts ({declared_new}) — reconcile with §3"))
    return issues

"""Build Sheet projection (Stage 8) — the construction projection.

S8 is not authored; it is **projected**, the same way S2→S5→S6b→S7 are projections of design
intent. `project_build_sheets` reads the governed upstream registers (S2/S5/S6b/S7) and derives one
Build Sheet per S7 `build_order` row — assembling, never inventing. Where a required field has no
governed source it becomes a classified GAP, not a guess.

Design (per the Phase-4 architecture patches):
  * MODEL FIRST — `project_build_sheets` returns a pure `BuildSheetSetModel`; `render_markdown` is a
    separate function. Future JSON / HTML / protocol-generator renderers reuse the same model.
  * PROVENANCE IS THE ATOM — every field is a `FieldValue {sources, confidence, status, value}`.
    Prose values are RESOLVED from upstream (copied with provenance), never composed by Python; the
    `sources` make drift detectable. (A later step can drop `value` and resolve refs at render time.)
  * NO DESIGN — the projection only relocates governed facts. Per-CC composition comes verbatim from
    S6b `cc_composition`; a CC outcome surface from `execution_topology`; authority from a constitution
    table; nothing is decided here.

Readiness (monotonic): DESIGNED → BUILDABLE → CONSTRUCTION_READY → CONSTRUCTION_CLOSED → IMPLEMENTED →
RUNTIME_VALIDATED. The projection assigns up to BUILDABLE; the static oracle (build_sheet_oracle)
raises to CONSTRUCTION_READY; CONSTRUCTION_CLOSED is demonstrated empirically (zero design invention),
never statically proven.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..renderer.template_compiler import header_to_key

_REG_MARK = re.compile(r"<!--\s*register:([a-z0-9_]+)")


def parse_registers(text: str) -> dict[str, list[dict]]:
    """Parse a rendered dossier doc's `<!-- register:X -->` tables into {register_id: [row dicts]}.

    The upstream stage documents are the governed source of truth on disk; the projection reads them
    deterministically (row keys normalised exactly as the engine does, via `header_to_key`).
    """
    lines = text.splitlines()
    data: dict[str, list[dict]] = {}
    i = 0
    while i < len(lines):
        m = _REG_MARK.search(lines[i])
        if not m:
            i += 1
            continue
        rid = m.group(1)
        i += 1
        while i < len(lines) and not lines[i].lstrip().startswith("|"):
            i += 1
        if i >= len(lines):
            break
        keys = [header_to_key(h.strip()) for h in lines[i].strip().strip("|").split("|")]
        i += 2
        rows: list[dict] = []
        while i < len(lines) and lines[i].lstrip().startswith("|"):
            cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            if set("".join(cells)) <= set("-: "):
                i += 1
                continue
            rows.append({k: v for k, v in zip(keys, cells)})
            i += 1
        data[rid] = rows
    return data

def load_registers(handoff_dir: Path | str, stages: tuple[str, ...] = ("5", "6b", "7")) -> dict[str, list[dict]]:
    """Merge the governed JSON handoffs of `stages` into the `up` register dict the projector reads.

    This is the AUTHORITATIVE pipeline input for S8: the projection consumes declared structured
    handoffs, never re-parses narrative markdown (the Projection Completeness Principle — see
    doc/parkinglot/CONSTRUCTION_DOCTRINE_V0.md). Each `_handoff/<stage>.json` is already
    `{register_id: [row dicts]}`; later stages win on key collision (none expected — emit-fields are
    disjoint across stages). Fidelity of these JSON files against the locked baseline is a separate,
    governed gate (evaluator.projection_fidelity).
    """
    root = Path(handoff_dir)
    up: dict[str, list[dict]] = {}
    for stage in stages:
        path = root / f"{stage}.json"
        if not path.exists():
            raise FileNotFoundError(f"missing governed handoff: {path}")
        data = json.loads(path.read_text())
        for rid, rows in data.items():
            if isinstance(rows, list):
                up[rid] = rows
    return up


def load_entity_fields(workspace: Path | str, *, domain: str | None = None) -> dict[str, list[str]]:
    """Governed field vocabulary per entity, read from the COMPILED entities in the snapshot.

    Returns {ENTITY_CODE: [identity_field, *attribute_names]}. This is the zero-invention grounding
    source for construction: the canonical fields a builder may use come from `pi`-queryable compiled
    entities (e.g. ENTITY_BLOCK_V0 → block_id, height, epoch, …), never invented. Empty when no entity
    snapshot is present (e.g. in unit tests) — grounding then degrades gracefully.
    """
    root = Path(workspace) / "protocol_snapshot" / "artifacts" / "entities"
    out: dict[str, list[str]] = {}
    if not root.exists():
        return out
    for p in sorted(root.glob("*.json")):
        try:
            core = json.loads(p.read_text()).get("frontmatter", {}).get("core", {})
        except Exception:
            continue
        if domain and core.get("domain") not in (None, domain):
            continue
        code = p.stem.split("__")[-1]            # blockchain__ENTITY_BLOCK_V0 → ENTITY_BLOCK_V0
        fields: list[str] = []
        ident = (core.get("identity") or {}).get("field")
        if ident:
            fields.append(ident)
        for a in core.get("attributes") or []:
            if isinstance(a, dict) and a.get("name"):
                fields.append(a["name"])
        out[code] = fields
    return out


# ---- provenance vocabulary ----
PRIMARY_ONLY = "PRIMARY_ONLY"
PRIMARY_PLUS_CORROBORATED = "PRIMARY_PLUS_CORROBORATED"
DERIVED = "DERIVED"
INFERRED = "INFERRED"
UNRESOLVED = "UNRESOLVED"

OK = "OK"
GAP = "GAP"

# ---- readiness ladder (monotonic) ----
DESIGNED = "DESIGNED"
BUILDABLE = "BUILDABLE"
CONSTRUCTION_READY = "CONSTRUCTION_READY"
CONSTRUCTION_CLOSED = "CONSTRUCTION_CLOSED"

# governing constitution per execution concern (authority is derived, not designed)
CONSTITUTION: dict[str, str] = {
    "CC": "CONSTITUTION_CAPABILITY_CONTRACT_V0",
    "CT": "CONSTITUTION_CAPABILITY_TRANSFORM_V0",
    "CS": "CONSTITUTION_CAPABILITY_SIDE_EFFECT_V0",
    "WF": "CONSTITUTION_WORKFLOW_V0",
    "IN": "CONSTITUTION_INTENT_V0",
    "RB": "CONSTITUTION_RUNTIME_BINDING_V0",
    "EV": "CONSTITUTION_EVENT_V0",
    "STRUCTURE": "CONSTITUTION_STRUCTURE_V0",
}

_CODE = re.compile(r"(?:[a-z][a-z0-9_.]*::)?((?:CC|CS|CT|IN|WF|RB|EV|AC|STRUCTURE|TI)_[A-Z0-9_]*_V\d+)")


def code_part(s: Any) -> str | None:
    m = _CODE.search(str(s or ""))
    return m.group(1) if m else None


def _family(code: str | None) -> str | None:
    cp = code_part(code)
    return cp.split("_", 1)[0] if cp else None


# ---------------------------------------------------------------------------
# model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FieldValue:
    """One governed field of a Build Sheet — value + where it came from.

    `sources` are references into the upstream registers (e.g. "S6b.cc_composition#CC_X"). `value`
    is the resolved/derived content (copied from upstream or a controlled token — never Python prose).
    `status` is OK or GAP; a GAP carries its class in `value`.
    """
    sources: tuple[str, ...]
    confidence: str
    status: str = OK
    value: Any = None


@dataclass
class Gap:
    gid: str
    gap_class: str          # GAP_SEED | GAP_DOSSIER | GAP_ARCHITECTURAL_DRIFT | GAP_DECISION | GAP_IMPLEMENTATION | ...
    field: str
    found_by: str
    closed_by: str


@dataclass
class BuildSheetModel:
    code: str
    kind: str
    action: str
    wave: str
    step: str
    subdomain: str
    part_a: dict[str, FieldValue] = field(default_factory=dict)   # Governing Truth
    part_b: dict[str, FieldValue] = field(default_factory=dict)   # Construction Specification
    gaps: list[Gap] = field(default_factory=list)
    readiness: str = DESIGNED
    entity_fields: tuple[str, ...] = ()   # governed field vocabulary grounded from compiled entities

    def all_fields(self) -> dict[str, FieldValue]:
        return {**self.part_a, **self.part_b}


@dataclass
class BuildSheetSetModel:
    domain: str
    subdomain: str
    sheets: list[BuildSheetModel] = field(default_factory=list)
    gap_census: list[Gap] = field(default_factory=list)

    def readiness(self) -> str:
        """Set readiness = the lowest member sheet (monotonic ladder)."""
        order = [DESIGNED, BUILDABLE, CONSTRUCTION_READY, CONSTRUCTION_CLOSED]
        if not self.sheets:
            return DESIGNED
        return min((s.readiness for s in self.sheets), key=order.index)


# ---------------------------------------------------------------------------
# upstream lookup helpers (references, not copies)
# ---------------------------------------------------------------------------

def _rows(up: dict[str, list], rid: str) -> list[dict]:
    return [r for r in (up.get(rid) or []) if isinstance(r, dict)]


def _find(up: dict[str, list], rid: str, *code_cols: str, code: str) -> dict | None:
    """First row in `rid` whose any code column resolves to `code`."""
    for r in _rows(up, rid):
        for c in code_cols:
            if code_part(r.get(c, "")) == code:
                return r
    return None


# ---------------------------------------------------------------------------
# projection
# ---------------------------------------------------------------------------

def project_build_sheets(up: dict[str, list], *, domain: str, subdomain: str,
                         entity_fields: dict[str, list[str]] | None = None) -> BuildSheetSetModel:
    """Derive the Build Sheet Set from the governed upstream registers (no invention).

    `entity_fields` ({ENTITY_CODE: [fields]}, from `load_entity_fields`) grounds the governed field
    vocabulary onto every sheet — the canonical fields a builder may reference (block_id, height, …)
    come from the compiled entities, so construction transcribes governed names instead of inventing
    them. None ⇒ no entity grounding (degrades gracefully).
    """
    model = BuildSheetSetModel(domain=domain, subdomain=subdomain)
    vocab = tuple(sorted({f for fields in (entity_fields or {}).values() for f in fields}))

    for row in _rows(up, "build_order"):
        code = code_part(row.get("code", ""))
        if not code or code in ("EXIT", "EXIT_SUCCESS"):
            continue
        na = _find(up, "new_artifacts", "code", code=code)
        kind = (na.get("family", "").strip() if na else None) or _family(code) or "?"
        sheet = BuildSheetModel(
            code=code, kind=kind,
            action=str(row.get("action", "")).strip(),
            wave=str(row.get("wave", "")).strip(),
            step=str(row.get("step", "")).strip(),
            subdomain=str(row.get("subdomain", "")).strip(),
            entity_fields=vocab,
        )
        _project_part_a(sheet, up, na)
        _project_part_b(sheet, up)
        sheet.readiness = BUILDABLE if not sheet.gaps else DESIGNED
        model.sheets.append(sheet)

    # gap_census = union of per-sheet gaps (structural). Semantic drift recorded upstream (e.g. the
    # deferred genesis-mint GAP_ARCHITECTURAL_DRIFT) is carried as prose in S6b, not auto-detected here.
    for s in model.sheets:
        model.gap_census.extend(s.gaps)
    return model


def _project_part_a(sheet: BuildSheetModel, up: dict[str, list], na: dict | None) -> None:
    code = sheet.code
    # purpose — referenced from S6b new_artifacts capability (corroborated by S5 provisional summary)
    pc = _find(up, "provisional_codes", "provisional_code", "code", code=code)
    purpose_sources: list[str] = []
    purpose_val = None
    if na and na.get("capability"):
        purpose_sources.append(f"S6b.new_artifacts#{code}.capability")
        purpose_val = na.get("capability")
    if pc and pc.get("summary"):
        purpose_sources.append(f"S5.provisional_codes#{code}.summary")
        purpose_val = purpose_val or pc.get("summary")
    if purpose_sources:
        conf = PRIMARY_PLUS_CORROBORATED if len(purpose_sources) > 1 else PRIMARY_ONLY
        sheet.part_a["purpose"] = FieldValue(tuple(purpose_sources), conf, OK, purpose_val)
    else:
        sheet.part_a["purpose"] = FieldValue((), UNRESOLVED, GAP, "GAP_DOSSIER")
        sheet.gaps.append(Gap(f"{code}.purpose", "GAP_DOSSIER", "purpose", "projection", "S5/S6b"))

    # authority — derived from the constitution table
    const = CONSTITUTION.get(sheet.kind)
    sheet.part_a["authority"] = FieldValue(("constitution_table",), DERIVED,
                                           OK if const else GAP, const or "GAP_DECISION")

    # dependencies — from S7 build_order
    deps = str(_find(up, "build_order", "code", code=code).get("depends_on", "")).strip() \
        if _find(up, "build_order", "code", code=code) else "-"
    sheet.part_a["dependencies"] = FieldValue((f"S7.build_order#{code}.depends_on",), PRIMARY_ONLY, OK, deps or "-")

    # invariants — referenced from S5 (governing set; corroboration, not per-row matched here)
    inv = bool(_rows(up, "invariants"))
    sheet.part_a["invariants"] = FieldValue(("S5.invariants",), DERIVED if inv else UNRESOLVED,
                                            OK if inv else GAP, "S5 business invariants" if inv else "GAP_DOSSIER")

    # reuse — existing_inventory artifacts referenced by this artifact's composition/bindings
    sheet.part_a["reuse"] = FieldValue(("S6b.existing_inventory",), DERIVED, OK, "see composition / bindings")


def _project_part_b(sheet: BuildSheetModel, up: dict[str, list]) -> None:
    k = sheet.kind
    if k == "CC":
        _b_cc(sheet, up)
    elif k == "WF":
        _b_wf(sheet, up)
    elif k == "IN":
        _b_in(sheet, up)
    elif k == "RB":
        _b_rb(sheet, up)
    elif k == "CT":
        sheet.part_b["signature"] = FieldValue((f"S6b.new_artifacts#{sheet.code}",), DERIVED, OK,
                                               "pure transform — inputs→outputs; zero side effects; may not call CS")
    elif k == "EV":
        _b_ev(sheet, up)
    elif k == "STRUCTURE":
        _b_structure(sheet, up)
    # compiler/runtime obligations (common)
    sheet.part_b["compiler_mapping"] = FieldValue(("S6b.execution_topology",), DERIVED, OK,
                                                  "compiler accepts the artifact (S4_GOVERN asserts hold)")
    sheet.part_b["verification"] = FieldValue(("derived",), DERIVED, OK,
                                              f"pi artifact source {sheet.code} ; compile --structure …")
    sheet.part_b["runtime_expectations"] = FieldValue(("S6b.execution_topology",), DERIVED, OK,
                                                      "observe declared outcome routing / store writes, or compile-only")


def _fields(cell: Any) -> list[str]:
    """Parse a composition consumes/produces cell into logical field tokens."""
    return [t.strip() for t in str(cell or "").split(",") if t.strip() and t.strip() not in ("—", "-")]


def _b_cc(sheet: BuildSheetModel, up: dict[str, list]) -> None:
    steps = [r for r in _rows(up, "cc_composition") if code_part(r.get("cc_code", "")) == sheet.code]
    if steps:
        steps = sorted(steps, key=lambda r: int(re.sub(r"[^0-9]", "", str(r.get("step", "0"))) or 0))
        sheet.part_b["pipeline"] = FieldValue((f"S6b.cc_composition#{sheet.code}",), PRIMARY_ONLY, OK, steps)
        # inputs/outputs DERIVED from the composition data flow (no design): external inputs = fields
        # a step consumes that no step produces; output = result_status (the routed outcome surface).
        produced = {t for r in steps for t in _fields(r.get("produces", ""))}
        inputs: list[str] = []
        for r in steps:
            for t in _fields(r.get("consumes", "")):
                if t not in produced and t not in inputs:
                    inputs.append(t)
        sheet.part_b["inputs"] = FieldValue((f"S6b.cc_composition#{sheet.code}.consumes",), DERIVED, OK,
                                            inputs or ["—"])
        sheet.part_b["outputs"] = FieldValue((f"S6b.cc_composition#{sheet.code}.produces",), DERIVED, OK,
                                             ["result_status"])
    else:
        sheet.part_b["pipeline"] = FieldValue((), UNRESOLVED, GAP, "GAP_IMPLEMENTATION")
        sheet.gaps.append(Gap(f"{sheet.code}.pipeline", "GAP_IMPLEMENTATION", "pipeline",
                              "projection", "S6b.cc_composition"))
    node = _find(up, "execution_topology", "node", code=sheet.code)
    routing = node.get("routing", "") if node else ""
    sheet.part_b["result_routing"] = FieldValue((f"S6b.execution_topology#{sheet.code}.routing",),
                                                PRIMARY_ONLY if routing else UNRESOLVED,
                                                OK if routing else GAP, routing or "GAP_DOSSIER")
    if not routing:
        sheet.gaps.append(Gap(f"{sheet.code}.result_routing", "GAP_DOSSIER", "result_routing",
                              "projection", "S6b.execution_topology"))


def _b_wf(sheet: BuildSheetModel, up: dict[str, list]) -> None:
    nodes = [r for r in _rows(up, "execution_topology") if code_part(r.get("workflow", "")) == sheet.code]
    sheet.part_b["execution_graph"] = FieldValue((f"S6b.execution_topology#{sheet.code}",),
                                                 PRIMARY_ONLY if nodes else UNRESOLVED,
                                                 OK if nodes else GAP, nodes or "GAP_DOSSIER")
    if not nodes:
        sheet.gaps.append(Gap(f"{sheet.code}.execution_graph", "GAP_DOSSIER", "execution_graph",
                              "projection", "S6b.execution_topology"))
    admission = next((code_part(r.get("node", "")) for r in nodes
                      if str(r.get("node_type", "")).strip() == "IN"), None)
    sheet.part_b["admission"] = FieldValue((f"S6b.execution_topology#{sheet.code}",), DERIVED,
                                           OK if admission else GAP, admission or "GAP_DOSSIER")


def _b_in(sheet: BuildSheetModel, up: dict[str, list]) -> None:
    wf = next((code_part(r.get("workflow", "")) for r in _rows(up, "execution_topology")
               if code_part(r.get("node", "")) == sheet.code), None)
    sheet.part_b["workflow_binding"] = FieldValue(("S6b.execution_topology",), DERIVED,
                                                  OK if wf else GAP, wf or "GAP_DOSSIER")
    node = _find(up, "execution_topology", "node", code=sheet.code)
    sheet.part_b["outcomes"] = FieldValue((f"S6b.execution_topology#{sheet.code}.routing",), DERIVED,
                                          OK, (node or {}).get("routing", "ACK/NACK"))


def _b_rb(sheet: BuildSheetModel, up: dict[str, list]) -> None:
    rb = _find(up, "rb_declarations", "rb_code", code=sheet.code)
    if rb:
        sheet.part_b["bindings"] = FieldValue((f"S6b.rb_declarations#{sheet.code}",), PRIMARY_ONLY, OK, rb)
    else:
        sheet.part_b["bindings"] = FieldValue((), UNRESOLVED, GAP, "GAP_DOSSIER")
        sheet.gaps.append(Gap(f"{sheet.code}.bindings", "GAP_DOSSIER", "bindings",
                              "projection", "S6b.rb_declarations"))


def _b_ev(sheet: BuildSheetModel, up: dict[str, list]) -> None:
    # emitter is not declared in any register (EVs are emitted facts) → an implementation gap
    sheet.part_b["fact"] = FieldValue((f"S6b.new_artifacts#{sheet.code}.capability",), PRIMARY_ONLY, OK,
                                      "the recorded fact")
    sheet.part_b["emitted_by"] = FieldValue((), UNRESOLVED, GAP, "GAP_IMPLEMENTATION")
    sheet.gaps.append(Gap(f"{sheet.code}.emitted_by", "GAP_IMPLEMENTATION", "emitted_by",
                          "projection", "no emitter declared upstream"))


def _b_structure(sheet: BuildSheetModel, up: dict[str, list]) -> None:
    stores = [r for r in _rows(up, "structure_stores")
              if any(code_part(u) == sheet.code for u in str(r.get("used_by", "")).split(","))] \
        or _rows(up, "structure_stores")
    sheet.part_b["entity_stores"] = FieldValue(("S6b.structure_stores",), PRIMARY_ONLY, OK, stores)


# ---------------------------------------------------------------------------
# markdown renderer (one of several future renderers over the model)
# ---------------------------------------------------------------------------

def _fmt(fv: FieldValue) -> str:
    if fv.status == GAP:
        return f"⚠ {fv.value}"
    v = fv.value
    if isinstance(v, list):
        if v and isinstance(v[0], dict) and "step" in v[0]:        # composition steps
            return "; ".join(f"{r.get('step')}.{code_part(r.get('capability'))}({r.get('operation')})" for r in v)
        if v and isinstance(v[0], dict):                            # topology / bindings rows
            return f"{len(v)} row(s)"
        return ", ".join(str(x) for x in v) or "-"
    return str(v) if v is not None else "-"


def _prov(fv: FieldValue) -> str:
    src = " · ".join(fv.sources) if fv.sources else "—"
    return f"`{fv.confidence}` ← {src}"


def render_markdown(model: BuildSheetSetModel) -> str:
    L: list[str] = []
    L.append(f"# Build Sheet Set: {model.domain} / {model.subdomain}")
    L.append(f"**Pipeline Stage:** Stage 8 — Build Sheet Set  ")
    L.append(f"**Set Readiness:** {model.readiness()}  ")
    L.append(f"**Sheets:** {len(model.sheets)} (projected from S2/S5/S6b/S7 — assembled, not authored)")
    L.append("")
    for s in model.sheets:
        L.append(f"## Build Sheet {s.step} — {s.code}   [{s.action} · wave {s.wave} · {s.subdomain}]   "
                 f"Readiness: {s.readiness}")
        L.append("")
        L.append("**Part A — Governing Truth**")
        L.append("")
        L.append("| Field | Value | Provenance |")
        L.append("|-------|-------|------------|")
        for name, fv in s.part_a.items():
            L.append(f"| {name} | {_fmt(fv)} | {_prov(fv)} |")
        L.append("")
        L.append("**Part B — Construction Specification**")
        L.append("")
        L.append("| Field | Value | Provenance |")
        L.append("|-------|-------|------------|")
        for name, fv in s.part_b.items():
            L.append(f"| {name} | {_fmt(fv)} | {_prov(fv)} |")
        if s.gaps:
            L.append("")
            L.append("**Part D — GAPs:** " + " · ".join(f"`{g.gap_class}`[{g.field}]" for g in s.gaps))
        L.append("")
    L.append("## GAP Census")
    L.append("")
    if model.gap_census:
        L.append("| GAP id | Class | Field | Found By | Closed By |")
        L.append("|--------|-------|-------|----------|-----------|")
        for g in model.gap_census:
            L.append(f"| {g.gid} | {g.gap_class} | {g.field} | {g.found_by} | {g.closed_by} |")
    else:
        L.append("NONE IDENTIFIED — every sheet is structurally complete.")
    L.append("")
    return "\n".join(L)
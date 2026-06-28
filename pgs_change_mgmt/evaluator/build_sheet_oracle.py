"""ASSERT_CONSTRUCTION_CLOSED — the static gate over a Build Sheet Set.

Three statically-checkable component asserts raise a sheet from BUILDABLE to CONSTRUCTION_READY:

  ASSERT_STRUCTURE_COMPLETE   — every required Part A + Part B field exists for the sheet's kind
  ASSERT_PROVENANCE_COMPLETE  — every field is sourced (confidence not UNRESOLVED / INFERRED)
  ASSERT_DECISION_COMPLETE    — no GAP of any class remains (no design choice left to the builder)

The fourth assert — ASSERT_ZERO_DESIGN_INVENTION (→ CONSTRUCTION_CLOSED) — is EMPIRICAL: it is
*demonstrated* by construction (independent builders introduce no design / converge), never proven
statically. That separation is deliberate (Phase 5). A set is CONSTRUCTION_READY when every sheet
passes the three static asserts; only a demonstrated build moves it to CONSTRUCTION_CLOSED.
"""

from __future__ import annotations

from ..engine.build_sheet import (
    BuildSheetSetModel, BuildSheetModel, GAP, UNRESOLVED, INFERRED,
    BUILDABLE, CONSTRUCTION_READY,
)

REQUIRED_PART_A: tuple[str, ...] = ("purpose", "authority", "dependencies", "invariants")
REQUIRED_PART_B: dict[str, tuple[str, ...]] = {
    "CC": ("pipeline", "result_routing", "inputs", "outputs"),
    "WF": ("execution_graph", "admission"),
    "IN": ("workflow_binding", "outcomes"),
    "RB": ("bindings",),
    "CT": ("signature",),
    "EV": ("fact", "emitted_by"),
    "STRUCTURE": ("entity_stores",),
}


def assert_structure_complete(s: BuildSheetModel) -> list[str]:
    """Every required Part A + Part B field exists for the sheet's kind."""
    out: list[str] = []
    for f in REQUIRED_PART_A:
        if f not in s.part_a:
            out.append(f"ASSERT_STRUCTURE_COMPLETE: missing Part A field '{f}'")
    for f in REQUIRED_PART_B.get(s.kind, ()):
        if f not in s.part_b:
            out.append(f"ASSERT_STRUCTURE_COMPLETE: missing Part B field '{f}' (kind {s.kind})")
    return out


def assert_provenance_complete(s: BuildSheetModel) -> list[str]:
    """Every field is sourced — confidence is not UNRESOLVED or INFERRED."""
    out: list[str] = []
    for name, fv in s.all_fields().items():
        if fv.confidence in (UNRESOLVED, INFERRED):
            out.append(f"ASSERT_PROVENANCE_COMPLETE: field '{name}' is {fv.confidence} (no governed source)")
    return out


def assert_decision_complete(s: BuildSheetModel) -> list[str]:
    """No GAP remains — no design choice is left to the builder."""
    return [f"ASSERT_DECISION_COMPLETE: open {g.gap_class}[{g.field}]" for g in s.gaps] + \
           [f"ASSERT_DECISION_COMPLETE: field '{n}' is a GAP" for n, fv in s.all_fields().items()
            if fv.status == GAP and not any(g.field == n for g in s.gaps)]


def assert_construction_closed(model: BuildSheetSetModel) -> list[tuple[str, str]]:
    """Run the three static asserts per sheet; raise clean sheets BUILDABLE → CONSTRUCTION_READY.

    Returns (code, message) issues. An empty list means every sheet is CONSTRUCTION_READY (the static
    gate). CONSTRUCTION_CLOSED still requires the empirical zero-design-invention demonstration.
    """
    issues: list[tuple[str, str]] = []
    for s in model.sheets:
        sheet_issues = (assert_structure_complete(s)
                        + assert_provenance_complete(s)
                        + assert_decision_complete(s))
        if sheet_issues:
            issues.extend((s.code, m) for m in sheet_issues)
        elif s.readiness == BUILDABLE:
            s.readiness = CONSTRUCTION_READY
    return issues

"""ASSERT_PROJECTION_FIDELITY proof (Phase 4 — the pipeline-validation gate).

Three things proven, no model invoked:

  1. The one-time migration projects the locked chain markdown into JSON handoffs that are FAITHFUL —
     `assert_projection_fidelity` returns no issues for any migrated stage.
  2. The authoritative JSON path is EQUIVALENT to the old markdown path — `project_build_sheets` over
     `load_registers(_handoff)` yields the same 13 sheets as over `parse_registers(markdown)`.
  3. The gate CATCHES the very bug that motivated it — a handoff that drops a row (the worker
     under-emission discovered in Phase 4) is flagged, not silently accepted. Had this gate existed,
     the lossy baseline would never have been accepted.
"""

from __future__ import annotations

import copy
from pathlib import Path

from ..evaluator.projection_fidelity import assert_projection_fidelity
from .build_sheet import parse_registers, load_registers, project_build_sheets
from ._migrate_handoff_from_baseline import migrate_stage

CHAIN = Path(__file__).resolve().parents[2] / "change_mgmt" / "dossiers" / "blockchain" / "chain"
# the full worker-authored spine S1→S7 (S8/S9 are projector stages — assembled, not migrated). The
# standing gate covers every stage so a stale/lossy handoff at ANY seam is caught, not just S8's inputs.
STAGES = ("1", "2", "3", "4", "5", "6", "6b", "7")


def main() -> int:
    # (1) migration is faithful for every worker-authored stage S1→S7
    for stage in STAGES:
        _, issues = migrate_stage(CHAIN, stage)
        assert not issues, f"migration must be fidelity-clean for S{stage}: {issues}"
    print(f"  migration faithful: {', '.join('S'+s for s in STAGES)} → fidelity-clean handoffs ✓")

    # (2) JSON path ≡ markdown path (the swap is safe)
    md: dict[str, list] = {}
    for stem in ("5_business_intent", "6b_design_intent", "7_authoring_mandate"):
        md.update(parse_registers((CHAIN / f"{stem}_blockchain_chain_v0.md").read_text()))
    md_sheets = [(s.code, s.kind, s.readiness, len(s.gaps))
                 for s in project_build_sheets(md, domain="blockchain", subdomain="chain").sheets]
    js = load_registers(CHAIN / "_handoff")
    js_sheets = [(s.code, s.kind, s.readiness, len(s.gaps))
                 for s in project_build_sheets(js, domain="blockchain", subdomain="chain").sheets]
    assert md_sheets == js_sheets, f"JSON path must equal markdown path:\n md={md_sheets}\n js={js_sheets}"
    assert len(js_sheets) == 13, f"expected 13 chain sheets, got {len(js_sheets)}"
    print(f"  authoritative JSON path ≡ markdown path: {len(js_sheets)} sheets, identical ✓")

    # (3) the gate catches a dropped row (the under-emission bug) and a missing register
    md_text = (CHAIN / "7_authoring_mandate_blockchain_chain_v0.md").read_text()
    full = load_registers(CHAIN / "_handoff", stages=("7",))
    assert assert_projection_fidelity("7", md_text, full) == [], "frozen S7 must be faithful"

    lossy = copy.deepcopy(full)
    lossy["build_order"] = lossy["build_order"][:4]          # the exact shape of the original bug: 4 of 13
    dropped = assert_projection_fidelity("7", md_text, lossy)
    assert any("row count" in i and "build_order" in i for i in dropped), f"must flag dropped rows: {dropped}"

    missing = copy.deepcopy(full)
    del missing["build_order"]                                # build_order is required (not rollout/optional)
    gone = assert_projection_fidelity("7", md_text, missing)
    assert any("present in markdown but absent from JSON" in i for i in gone), f"must flag missing register: {gone}"
    print("  gate catches dropped rows (4/13) and missing required register ✓ — the Phase-4 bug is now gated")

    print("\nPROJECTION FIDELITY PROOF OK ✓ — Projection(markdown) == Projection(JSON) is governed "
          "across S1→S7: migration faithful for every stage, JSON path ≡ markdown path, under-emission caught.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

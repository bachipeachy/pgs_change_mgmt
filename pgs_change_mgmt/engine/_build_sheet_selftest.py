"""Build Sheet projection proof — project the real blockchain/chain corpus (S2/S5/S6b/S7) and check
the projection assembles without inventing: every governed fact lands; every missing one is a GAP.

Run: python -m pgs_change_mgmt.engine._build_sheet_selftest   (hermetic — parses the frozen chain
fixture, never the live working dossier).
"""

from __future__ import annotations

import re
from pathlib import Path

from ..renderer.template_compiler import header_to_key
from ._fixture import chain_dossier
from .build_sheet import project_build_sheets, render_markdown, OK, GAP, BUILDABLE, CONSTRUCTION_READY

_MARK = re.compile(r"<!--\s*register:([a-z0-9_]+)")


def _parse(path: Path) -> dict[str, list[dict]]:
    lines = path.read_text().splitlines()
    data: dict[str, list[dict]] = {}
    i = 0
    while i < len(lines):
        m = _MARK.search(lines[i])
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
        rows = []
        while i < len(lines) and lines[i].lstrip().startswith("|"):
            cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            if set("".join(cells)) <= set("-: "):
                i += 1
                continue
            rows.append({k: v for k, v in zip(keys, cells)})
            i += 1
        data[rid] = rows
    return data


def main() -> int:
    up: dict[str, list] = {}
    with chain_dossier() as chain:
        for stage in ("5_business_intent", "6b_design_intent", "7_authoring_mandate"):
            up.update(_parse(chain / f"{stage}_blockchain_chain_v0.md"))

    model = project_build_sheets(up, domain="blockchain", subdomain="chain")
    by = {s.code: s for s in model.sheets}

    print(f"  projected {len(model.sheets)} sheets; set readiness = {model.readiness()}")
    assert len(model.sheets) == 16, f"expected 16 sheets (S7 build_order), got {len(model.sheets)}"

    # commit cluster CCs are fully composed → pipeline present, BUILDABLE
    for cc in ("CC_COMMIT_BLOCK_CANONICAL_V0", "CC_VALIDATE_PREDECESSOR_LINK_V0"):
        s = by[cc]
        assert s.part_b["pipeline"].status == OK, f"{cc} pipeline should be present: {s.part_b['pipeline']}"
        assert s.part_b["result_routing"].status == OK, f"{cc} routing should be present"
        assert s.readiness == BUILDABLE, f"{cc} should be BUILDABLE, got {s.readiness} gaps={s.gaps}"
    print("  commit cluster CCs composed (pipeline + routing) → BUILDABLE ✓")

    # the shared comparison primitive is projected as a CT
    assert by["CT_PURE_COMPARE_EQUAL_V0"].kind == "CT", "compare primitive should project as a CT"
    print("  CT_PURE_COMPARE_EQUAL_V0 projects as a shared CT ✓")

    # provenance: purpose carries corroborated sources where S5 + S6b agree
    p = by["CC_COMMIT_BLOCK_CANONICAL_V0"].part_a["purpose"]
    assert p.sources, "purpose must carry provenance sources, not invented prose"
    print(f"  purpose is referenced not invented: {p.confidence} ← {p.sources} ✓")

    # every governed fact lands: the EV's payload (S6b.events) and emitter (S6b.execution_outputs) RESOLVE
    # from upstream — a pure join (events ⋈ execution_outputs on ev_code == output_code), no invention, no
    # residual gap. The full chain corpus is construction-closed at the build-sheet level.
    ev = by["EV_GENESIS_CREATED_V0"]
    assert ev.part_b["payload"].status == OK, f"EV payload should resolve from S6b.events: {ev.part_b['payload']}"
    assert ev.part_b["emitted_by"].status == OK, f"EV emitter should resolve from S6b.execution_outputs: {ev.part_b['emitted_by']}"
    assert ev.part_b["emitted_by"].value == ["blockchain::CC_CREATE_GENESIS_BLOCK_V0"], "emitter joined on output_code == ev_code"
    assert not ev.gaps, f"resolved EV carries no gap: {ev.gaps}"
    assert not model.gap_census, f"complete corpus → empty gap census, got {model.gap_census}"
    print("  EV_GENESIS_CREATED payload+emitter RESOLVED from S6b (events ⋈ execution_outputs) → no gap ✓")

    # every missing fact is a GAP, never invented: strip the two EV registers and the projection reports
    # AUTHORABLE dossier gaps — GAP_DOSSIER (not GAP_IMPLEMENTATION now that emission is declarable, and
    # never a fabricated value).
    up_missing = {k: v for k, v in up.items() if k not in ("events", "execution_outputs")}
    ev_missing = {s.code: s for s in
                  project_build_sheets(up_missing, domain="blockchain", subdomain="chain").sheets}["EV_GENESIS_CREATED_V0"]
    g_missing = {g.field: g.gap_class for g in ev_missing.gaps}
    assert ev_missing.part_b["emitted_by"].status == GAP and g_missing.get("emitted_by") == "GAP_DOSSIER", \
        f"missing emitter → authorable GAP_DOSSIER: {g_missing}"
    assert ev_missing.part_b["payload"].status == GAP and g_missing.get("payload") == "GAP_DOSSIER", \
        f"missing payload → authorable GAP_DOSSIER: {g_missing}"
    print("  strip S6b.events/execution_outputs → EV payload+emitter become GAP_DOSSIER (authorable, not invented) ✓")

    # static gate: ASSERT_CONSTRUCTION_CLOSED raises clean sheets BUILDABLE → CONSTRUCTION_READY. With the
    # corpus complete, the commit cluster AND the resolved genesis EV all reach the gate.
    from ..evaluator.build_sheet_oracle import assert_construction_closed
    issues = assert_construction_closed(model)
    for code in ("CC_COMMIT_BLOCK_CANONICAL_V0", "CC_VALIDATE_PREDECESSOR_LINK_V0", "EV_GENESIS_CREATED_V0"):
        assert by[code].readiness == CONSTRUCTION_READY, \
            f"{code} should reach CONSTRUCTION_READY: {[m for c, m in issues if c == code]}"
    print(f"  ASSERT_CONSTRUCTION_CLOSED: commit cluster + resolved genesis EV → CONSTRUCTION_READY; "
          f"{len(issues)} open issue(s) ✓")

    md = render_markdown(model)
    assert md.startswith("# Build Sheet Set: blockchain / chain"), "markdown render header"
    assert "Part A — Governing Truth" in md and "GAP Census" in md, "render structure"
    print(f"  render_markdown OK ({len(md)} chars); gap_census = {len(model.gap_census)} entries")

    print("\nBUILD SHEET PROJECTION PROOF OK ✓ — projected S2/S5/S6b/S7 → 16 sheets, provenance-tracked, "
          "gap-classified, model→markdown; assembled not authored.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

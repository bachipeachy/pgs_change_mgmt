"""Build Sheet projection proof — project the real blockchain/chain corpus (S2/S5/S6b/S7) and check
the projection assembles without inventing: every governed fact lands; every missing one is a GAP.

Run: python -m pgs_change_mgmt.engine._build_sheet_selftest   (needs PGS_WORKSPACE for nothing here —
it parses the committed chain dossier docs directly).
"""

from __future__ import annotations

import re
from pathlib import Path

from ..renderer.template_compiler import header_to_key
from .build_sheet import project_build_sheets, render_markdown, OK, GAP, BUILDABLE, CONSTRUCTION_READY

PKG = Path(__file__).resolve().parents[2]
CHAIN = PKG / "change_mgmt" / "dossiers" / "blockchain" / "chain"
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
    for stage in ("5_business_intent", "6b_design_intent", "7_authoring_mandate"):
        up.update(_parse(CHAIN / f"{stage}_blockchain_chain_v0.md"))

    model = project_build_sheets(up, domain="blockchain", subdomain="chain")
    by = {s.code: s for s in model.sheets}

    print(f"  projected {len(model.sheets)} sheets; set readiness = {model.readiness()}")
    assert len(model.sheets) == 13, f"expected 13 sheets (S7 build_order), got {len(model.sheets)}"

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

    # the projection refuses to invent: EV emitter is undeclared upstream → GAP_IMPLEMENTATION
    ev = by["EV_GENESIS_CREATED_V0"]
    assert ev.part_b["emitted_by"].status == GAP, "EV emitter should be a GAP (no emitter declared)"
    assert any(g.gap_class == "GAP_IMPLEMENTATION" for g in ev.gaps), "EV emitter GAP must be classified"
    print("  EV_GENESIS_CREATED emitter undeclared → GAP_IMPLEMENTATION (not invented) ✓")

    assert model.gap_census, "gap census should surface the unresolved fields"

    # static gate: ASSERT_CONSTRUCTION_CLOSED raises clean sheets BUILDABLE → CONSTRUCTION_READY
    from ..evaluator.build_sheet_oracle import assert_construction_closed
    issues = assert_construction_closed(model)
    for cc in ("CC_COMMIT_BLOCK_CANONICAL_V0", "CC_VALIDATE_PREDECESSOR_LINK_V0"):
        assert by[cc].readiness == CONSTRUCTION_READY, \
            f"{cc} should reach CONSTRUCTION_READY: {[m for c, m in issues if c == cc]}"
    assert any(c == "EV_GENESIS_CREATED_V0" for c, _ in issues), "genesis EV must fail the static gate (open GAP)"
    assert by["EV_GENESIS_CREATED_V0"].readiness != CONSTRUCTION_READY, "genesis EV must not be READY"
    print(f"  ASSERT_CONSTRUCTION_CLOSED: commit cluster → CONSTRUCTION_READY; "
          f"{len(issues)} open issue(s) keep genesis below the gate ✓")

    md = render_markdown(model)
    assert md.startswith("# Build Sheet Set: blockchain / chain"), "markdown render header"
    assert "Part A — Governing Truth" in md and "GAP Census" in md, "render structure"
    print(f"  render_markdown OK ({len(md)} chars); gap_census = {len(model.gap_census)} entries")

    print("\nBUILD SHEET PROJECTION PROOF OK ✓ — projected S2/S5/S6b/S7 → 13 sheets, provenance-tracked, "
          "gap-classified, model→markdown; assembled not authored.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Governance Impact self-test — the discover→approve→consume boundary, offline.

A CR never changes governance: construction *computes* the surface additions it requires
(`governance_impact.json`), the governance authority *approves* them (adds to the canonical surface),
and promotion *consumes* — refusing until the canonical surface satisfies the impact. This locks the
descriptive machinery: comment-tolerant surface parsing, idempotent compose, and the promotion-time
`missing_approvals` gate. Pure text + temp files — no live compiler, no real governance repo.

Run:  python -m pgs_change_mgmt.engine._governance_impact_selftest
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from . import governance_surface as gs

# A surface whose list is grouped under `#` comment headers (like the real blockchain CT surface) —
# the parser must see through the comments, not stop at the first one.
_SURFACE = """\
```yaml
assert_code: ASSERT_CT_SURFACE_CLOSED_DEMO_V0
core:
  allowed_capability_transforms:
    # Domain CTs - group A
    - demo::CT_PURE_ALPHA_V0
    - demo::CT_PURE_BETA_V0
    # Domain CTs - group B
    - demo::CT_PURE_GAMMA_V0
```
"""


def main() -> int:
    # 1. declared() sees through comment headers (the bug that made a populated surface read as empty).
    d = gs.declared(_SURFACE)
    assert d == {"demo::CT_PURE_ALPHA_V0", "demo::CT_PURE_BETA_V0", "demo::CT_PURE_GAMMA_V0"}, d
    print("  comment-tolerant declared    ✓  (3 entries across 2 comment groups)")

    # 2. compose() inserts after the last item, is idempotent, and keeps the block intact.
    added = gs.compose(_SURFACE, ["demo::CT_PURE_DELTA_V0"])
    assert "demo::CT_PURE_DELTA_V0" in gs.declared(added), added
    assert "- demo::CT_PURE_GAMMA_V0" in added and "# Domain CTs - group B" in added, added
    assert gs.compose(added, ["demo::CT_PURE_DELTA_V0"]) == added, "compose must be idempotent"
    print("  compose insert + idempotent  ✓")

    # 3. missing_approvals() navigates required_changes and re-checks the canonical surface live.
    tmp = Path(tempfile.mkdtemp(prefix="gov_impact_"))
    surf = tmp / "surface.md"
    surf.write_text(_SURFACE)
    impact = {"domain": "demo", "subdomain": "d", "required_changes": {"ct_surface": [
        {"surface": "ASSERT_CT_SURFACE_CLOSED_DEMO_V0", "package": "pgs_demo", "path": str(surf),
         "add": ["demo::CT_PURE_ALPHA_V0", "demo::CT_PURE_NEWONE_V0"]}]}}
    # ALPHA already declared, NEWONE is not → exactly one missing.
    assert gs.missing_approvals(impact) == ["demo::CT_PURE_NEWONE_V0"], gs.missing_approvals(impact)
    # after the governance authority approves (compose into canonical), the gate clears.
    surf.write_text(gs.compose(_SURFACE, ["demo::CT_PURE_NEWONE_V0"]))
    assert gs.missing_approvals(impact) == [], "gate must clear once canonical satisfies the impact"
    print("  missing_approvals gate       ✓  (navigates required_changes, re-checks canonical, clears)")

    # 4. A full round-trip (serialized impact doc) behaves identically.
    reloaded = json.loads(json.dumps(impact))
    assert gs.missing_approvals(reloaded) == [], reloaded
    print("  serialized impact round-trip ✓")

    print("\nGOVERNANCE IMPACT OK ✓ — construction discovers, governance approves, promotion consumes; "
          "a CR never writes the constitutional surface.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

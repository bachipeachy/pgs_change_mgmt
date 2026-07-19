"""Placement Manifest self-test — owner-aware promotion routing, offline.

Proves the promotion consumer routes each artifact to the registry the Placement Manifest already
resolved: a cross-repo delta lands in *each owning repo*, an override collapses to one root, and a
missing manifest fails hard. Pure routing — no compiler, no federation, no real writes. Ownership
resolution is computed once upstream (Ownership Resolution / admission); this locks that promotion
*consumes* that decision and never recomputes it.

Run:  python -m pgs_change_mgmt.engine._placement_selftest
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from . import bridge

# A delta that spans two repos: a blockchain CC and the reusable transform it depends on (owned by
# pgs_transforms under pgs_capabilities). Mirrors the blockchain/chain CR that exposed the gap.
_MANIFEST = {
    "domain": "blockchain", "subdomain": "chain",
    "placements": [
        {"code": "CC_VALIDATE_PREDECESSOR_LINK_V0", "fqdn": "blockchain::CC_VALIDATE_PREDECESSOR_LINK_V0",
         "kind": "CC", "owner_layer": "BLOCKCHAIN", "package": "pgs_blockchain",
         "registry_root": "/repos/pgs_blockchain/pgs_blockchain/registry",
         "relative_path": "chain/capability_contracts/CC_VALIDATE_PREDECESSOR_LINK_V0.md"},
        {"code": "CT_PURE_COMPARE_EQUAL_V0", "fqdn": "capability_transforms::CT_PURE_COMPARE_EQUAL_V0",
         "kind": "CT", "owner_layer": "REUSABLE_TRANSFORMS", "package": "pgs_transforms",
         "registry_root": "/repos/pgs_capabilities/pgs_transforms/registry",
         "relative_path": "capability_transforms/CT_PURE_COMPARE_EQUAL_V0.md"},
    ],
}


def _finale(manifest: dict | None) -> Path:
    d = Path(tempfile.mkdtemp(prefix="placement_selftest_"))
    for p in _MANIFEST["placements"]:
        (d / f"{p['code']}.md").write_text(p["code"])
    if manifest is not None:
        (d / bridge.PLACEMENT_MANIFEST).write_text(json.dumps(manifest))
    return d


def main() -> int:
    # 1. Governed ownership (no override): each artifact routes to ITS OWN repo.
    d = _finale(_MANIFEST)
    dests = {p.as_posix() for p, _ in bridge.plan_promotion(_MANIFEST, d)}
    assert "/repos/pgs_blockchain/pgs_blockchain/registry/chain/capability_contracts/" \
           "CC_VALIDATE_PREDECESSOR_LINK_V0.md" in dests, dests
    assert "/repos/pgs_capabilities/pgs_transforms/registry/capability_transforms/" \
           "CT_PURE_COMPARE_EQUAL_V0.md" in dests, dests
    print("  governed multi-repo routing  ✓  (CC → pgs_blockchain, reusable CT → pgs_transforms)")

    # 2. Override collapses both under one throwaway root (dry-run affordance), rel paths preserved.
    ov = sorted(p.as_posix() for p, _ in bridge.plan_promotion(_MANIFEST, d, registry_root=Path("/tmp/dry")))
    assert ov == ["/tmp/dry/capability_transforms/CT_PURE_COMPARE_EQUAL_V0.md",
                  "/tmp/dry/chain/capability_contracts/CC_VALIDATE_PREDECESSOR_LINK_V0.md"], ov
    print("  override single-root routing ✓  (throwaway root, governed rel paths preserved)")

    # 3. A missing manifest fails hard — promotion consumes placement, it never guesses.
    try:
        bridge.load_placement_manifest(_finale(None))
        raise SystemExit("missing manifest should have raised")
    except FileNotFoundError:
        pass
    print("  missing-manifest fail-hard   ✓  (consume, never recompute)")

    # 4. A source .md absent from the finale dir but named in the manifest fails hard.
    d2 = _finale(_MANIFEST)
    (d2 / "CT_PURE_COMPARE_EQUAL_V0.md").unlink()
    try:
        bridge.plan_promotion(_MANIFEST, d2)
        raise SystemExit("missing source .md should have raised")
    except FileNotFoundError:
        pass
    print("  missing-source fail-hard     ✓")

    # 5. Build plan is DECLARED by construction, EXECUTED dumbly by promotion (no scope inference).
    all_plan = {"mode": "all", "structures": [], "reason": "platform-touching"}
    dom_plan = {"mode": "structures", "structures": ["STRUCTURE_BUILD_BLOCKCHAIN_CONFIG_V0"]}
    assert bridge._compile_cmds(all_plan, "X")[0][-1] == "--all-structures", "platform delta → whole platform"
    assert bridge._compile_cmds(dom_plan, "X") == [
        ["python", "-m", "pgs_compiler.cli", "compile", "--structure", "STRUCTURE_BUILD_BLOCKCHAIN_CONFIG_V0"]]
    assert bridge._compile_cmds({}, "STRUCTURE_BUILD_X_V0")[0][-1] == "STRUCTURE_BUILD_X_V0", "fallback"
    print("  declared build-plan          ✓  (platform delta → --all-structures; domain → --structure; dumb execute)")

    print("\nPLACEMENT MANIFEST ROUTING OK ✓ — owner-aware promotion consumes the placement decision "
          "(compute once, persist, consume); a cross-repo delta routes to each owning repo; the "
          "declared build plan sets rebuild scope (platform-wide vs domain).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

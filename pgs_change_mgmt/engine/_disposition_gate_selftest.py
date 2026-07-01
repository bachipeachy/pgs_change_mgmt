"""Disposition-completeness gate wiring proof (SPP · DP4) — hermetic, no workspace.

Builds a tiny Stage Package (projection + response), and asserts the gate: (1) is a no-op when no
projection ships; (2) REJECTS a response that leaves projected elements undisposed; (3) ADMITS a
response that disposes of every element via citations + group rules + GAP; (4) checks completeness
only — a disposition's *content* is never judged (boundary-creep guard).

Run: python -m pgs_change_mgmt.engine._disposition_gate_selftest
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from .disposition_gate import check_disposition

PASS, FAIL = "✅", "❌"

PROJECTION = {
    "projection_identity": {"projection_type": "discovery", "projection_id": "sha256:test"},
    "evidence": {
        "existing": [
            {"fqdn": "blockchain::CC_FORM_BLOCK_V0", "kind": "CC", "included_because": "root"},
            {"fqdn": "blockchain::CC_DERIVE_WALLET_KEYS_V0", "kind": "CC", "included_because": "reference"},
            {"fqdn": "blockchain::WF_CREATE_WALLET_V0", "kind": "WF", "included_because": "reference"},
        ],
        "absent": [{"concept": "GENESIS", "matches": 0}],
    },
}


def _write_pkg(tmp: Path, response_obj: dict | None) -> Path:
    (tmp / "context").mkdir(parents=True, exist_ok=True)
    (tmp / "context" / "discovery_projection.json").write_text(json.dumps(PROJECTION))
    if response_obj is not None:
        (tmp / "response.md").write_text("reasoning\n\n```json\n" + json.dumps(response_obj) + "\n```\n")
    return tmp


def _check(cond: bool, label: str) -> bool:
    print(f"  {PASS if cond else FAIL} {label}")
    return cond


def main() -> int:
    ok = True

    # 1. no projection ⇒ gate is a no-op (applicable False, ok True)
    with tempfile.TemporaryDirectory() as d:
        pkg = Path(d)
        (pkg / "response.md").write_text("```json\n{\"registers\": {}}\n```")
        g = check_disposition(pkg)
        ok &= _check(not g.applicable and g.ok, "no projection ⇒ gate n/a (no-op)")

    # 2. incomplete — cite one node, leave two nodes + the absent concept undisposed ⇒ REJECT
    with tempfile.TemporaryDirectory() as d:
        pkg = _write_pkg(Path(d), {"registers": {
            "entities": [{"entity": "Block", "source_finding": "blockchain::CC_FORM_BLOCK_V0"}]}})
        g = check_disposition(pkg)
        ok &= _check(g.applicable and not g.ok, "undisposed elements ⇒ INCOMPLETE (rejected)")
        ok &= _check("blockchain::CC_DERIVE_WALLET_KEYS_V0" in g.report.undisposed_existing
                     and "GENESIS" in g.report.undisposed_absent,
                     "gate names the undisposed node(s) + absent concept(s)")

    # 3. complete — cite one, group-dispose the wallet set, GAP the absent concept ⇒ ADMIT
    with tempfile.TemporaryDirectory() as d:
        pkg = _write_pkg(Path(d), {
            "registers": {
                "entities": [{"entity": "Block", "source_finding": "blockchain::CC_FORM_BLOCK_V0"}],
                "gaps": [{"gap": "no genesis bootstrap exists", "source_finding": "absent: GENESIS"}],
            },
            "neighbourhood_disposition": [
                {"target": "WALLET", "disposition": "NOT_APPLICABLE", "reason": "wallet internals"},
            ],
        })
        g = check_disposition(pkg)
        ok &= _check(g.ok, "citations + group rule + GAP ⇒ COMPLETE (admitted)")
        ok &= _check(g.report.by_disposition().get("RELEVANT") == 1
                     and g.report.by_disposition().get("NOT_APPLICABLE") == 2
                     and g.report.by_disposition().get("GAP") == 1,
                     "disposition mix recorded (RELEVANT 1 · NOT_APPLICABLE 2 · GAP 1)")

    print(f"\n{'ALL PASS' if ok else 'FAILURES PRESENT'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

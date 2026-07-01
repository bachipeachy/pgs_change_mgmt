"""Belief-Preservation oracle proof (S3 gate) — the invariant is real, not vacuous.

Asserts the gate passes a valid S3 and CATCHES each way S2's Validated Semantic Evidence can fail to
carry forward: a dropped belief, a REUSE with no baseline FQDN, an undecided CRITICAL gap, and a belief
overturned without evidence.

Run: python -m pgs_change_mgmt.evaluator._belief_preservation_selftest
"""

from __future__ import annotations

import sys

from .belief_preservation import check_belief_preservation

PASS, FAIL = "✅", "❌"

_S2 = {
    "belief_verification": [{"belief": f"b{i}"} for i in range(9)],
    "gaps": [{"gap": "no commit capability", "severity": "CRITICAL"}],
    "pps_baseline_fqdns": [{"fqdn": "blockchain::CC_FORM_BLOCK_V0"}],
}
_NINE = [{"item": f"b{i}", "result": "CONFIRMED", "evidence": "x"} for i in range(9)]


def _check(cond: bool, label: str) -> bool:
    print(f"  {PASS if cond else FAIL} {label}")
    return cond


def main() -> int:
    ok = True
    good = {"verification_results": _NINE,
            "authoring_decisions": [{"decision": "AUTHOR_NEW"},
                                    {"decision": "REUSE", "source_finding": "blockchain::CC_FORM_BLOCK_V0"}]}
    ok &= _check(not check_belief_preservation(good, _S2), "valid S3 passes (beliefs preserved)")

    cases = {
        "dropped belief": {"verification_results": _NINE[:1],
                           "authoring_decisions": [{"decision": "AUTHOR_NEW"}]},
        "REUSE without FQDN": {"verification_results": _NINE,
                               "authoring_decisions": [{"decision": "REUSE", "source_finding": "reuse it"}]},
        "critical gap undecided": {"verification_results": _NINE,
                                   "authoring_decisions": [{"decision": "REUSE", "source_finding": "blockchain::CC_FORM_BLOCK_V0"}]},
        "overturned without evidence": {"verification_results": [{"item": "b0", "result": "OVERTURNED"}] + _NINE[1:],
                                        "authoring_decisions": [{"decision": "AUTHOR_NEW"}]},
    }
    for name, s3 in cases.items():
        ok &= _check(bool(check_belief_preservation(s3, _S2)), f"catches: {name}")

    print(f"\n{'ALL PASS' if ok else 'FAILURES PRESENT'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
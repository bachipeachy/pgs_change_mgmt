"""Guided-Mode validation proof (SPP · DP6) — the DP3 measurement, now repeatable + oracle-gated.

Runs `validate_guided_stage` on the real chain S2 (package + response + golden from git + S1 beliefs)
and asserts: completeness and judgment-preservation are GATES that pass; efficiency and coverage are
DIAGNOSTICS that are surfaced but never gate. This encodes the Knowledge Partition Theorem in a metric
— we gate on determinism + the invariant, never on meaning.

Run: python -m pgs_change_mgmt.engine._guided_validation_selftest
"""

from __future__ import annotations

import dataclasses
import json
import subprocess
import sys
from pathlib import Path

from .guided_validation import validate_guided_stage, GuidedValidationReport

PASS, FAIL = "✅", "❌"
CHAIN = Path(__file__).resolve().parents[2] / "change_mgmt" / "dossiers" / "blockchain" / "chain"
PKG = CHAIN / "_packages" / "stage_2"
DOC = CHAIN / "2_domain_model_blockchain_chain_v0.md"
HANDOFF = CHAIN / "cr_ir" / "1.json"


def _check(cond: bool, label: str) -> bool:
    print(f"  {PASS if cond else FAIL} {label}")
    return cond


def main() -> int:
    if not (PKG / "context" / "discovery_projection.json").exists() or not (PKG / "response.md").exists():
        print(f"skip: needs an exported+authored chain stage-2 package at {PKG}")
        return 0
    ok = True
    golden = subprocess.run(
        ["git", "show", "main:change_mgmt/dossiers/blockchain/chain/2_domain_model_blockchain_chain_v0.md"],
        capture_output=True, text=True, cwd=CHAIN).stdout or None
    s1_beliefs = None
    if HANDOFF.exists():
        s1_beliefs = json.loads(HANDOFF.read_text()).get("system_beliefs")
    rendered = DOC.read_text() if DOC.exists() else None

    r = validate_guided_stage(PKG, s1_beliefs=s1_beliefs, golden_text=golden, rendered_doc=rendered)
    print(r.render())

    # gates: completeness + judgment preservation
    ok &= _check(r.completeness_ok and r.completeness == 1.0, "GATE completeness = 100% (DP4)")
    ok &= _check(r.judgment_preserved and r.beliefs_disposed == r.beliefs_total,
                 f"GATE judgment preserved ({r.beliefs_disposed}/{r.beliefs_total} beliefs disposed)")
    ok &= _check(r.ok, "overall PASS (gates: completeness ∧ judgment)")

    # diagnostics: efficiency + coverage are reported, and the gate does NOT depend on them
    ok &= _check(0.0 < r.efficiency < 1.0, f"efficiency reported as a diagnostic ({r.efficiency:.0%})")
    ok &= _check(r.evidence_coverage == 1.0, f"evidence coverage vs golden = {r.evidence_coverage:.0%}")
    ok &= _check(r.depth_coverage is not None and r.depth_coverage >= 0.9,
                 f"depth coverage vs golden ≥ 90% ({r.depth_coverage:.0%})")

    # theorem-in-a-metric: a LOW efficiency must NOT fail the gate (efficiency is not judgment)
    low_eff = dataclasses.replace(r, efficiency=0.05)
    ok &= _check(low_eff.ok, "a low efficiency does NOT fail the gate (efficiency is diagnostic, not judgment)")

    # inverse: dropping judgment preservation MUST fail the gate (the invariant is real)
    broke = dataclasses.replace(r, beliefs_disposed=r.beliefs_total - 1)
    ok &= _check(not broke.ok, "losing one belief disposition DOES fail the gate (judgment is the invariant)")

    print(f"\n{'ALL PASS' if ok else 'FAILURES PRESENT'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

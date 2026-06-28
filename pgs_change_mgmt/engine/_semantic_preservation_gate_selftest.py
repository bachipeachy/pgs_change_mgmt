"""Deterministic proof of the Semantic Preservation Gate (Increment 4 capstone).

Runs the gate against every compiled structure and asserts the gate mechanism — not a hardcoded
finding count, so the proof stays valid after CSI Finding #001 is resolved. Verifies:
  * release_candidate ⇔ the oracle report is clean (full semantic preservation);
  * Semantic Coverage is a well-formed fraction and agrees with the report;
  * at least one structure is a clean Release Candidate (the gate can pass);
  * when a structure is blocked, its findings localize to specific axes (the gate is diagnostic).

Run:  PGS_WORKSPACE=/abs python -m pgs_change_mgmt.engine._semantic_preservation_gate_selftest
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from .semantic_preservation_gate import run_gate, render


def main() -> int:
    ws_str = os.environ.get("PGS_WORKSPACE")
    if not ws_str:
        print("PGS_WORKSPACE required (path to pgs_workspace)")
        return 2
    ws = Path(ws_str)
    structures = sorted(json.loads(
        (ws / "protocol_snapshot" / "artifact_index" / "index.json").read_text()).get("structures", {}))

    clean = 0
    for st in structures:
        result = run_gate(ws, st)
        rep = result.report
        cov = result.coverage
        print(f"  {st:<16} RC={result.release_candidate!s:<5} coverage={cov * 100:5.1f}%  "
              f"axes={sum(1 for r in rep.results if r.ok)}/{len(rep.results)} pass")

        # mechanism invariants
        assert result.release_candidate == rep.ok, "release_candidate must track report.ok"
        assert 0.0 <= cov <= 1.0 and abs(cov - rep.coverage) < 1e-9, "coverage must be a well-formed fraction"
        assert "Semantic Preservation Gate:" in render(result), "render must state the gate verdict"
        if result.release_candidate:
            clean += 1
            assert cov == 1.0, "a Release Candidate must be 100% semantic coverage"
        else:
            # blocked → every failing axis must contribute findings, and coverage must dip below 100%
            failing = [r for r in rep.results if not r.ok]
            assert failing and all(r.issues for r in failing), "a blocked structure must localize findings to axes"
            assert cov < 1.0, "a blocked structure must lose coverage"
            print(f"    findings localize to: {sorted(r.name for r in failing)} "
                  f"({len(rep.issues())} finding(s))")

    assert clean >= 1, "the gate must be able to pass — at least one clean Release Candidate expected"
    print(f"\nSEMANTIC PRESERVATION GATE PROOF OK ✓ — gate verdict tracks semantic preservation across "
          f"{len(structures)} structures; coverage well-formed; {clean}/{len(structures)} clean Release "
          f"Candidate(s); any blocked structure localizes its findings to specific axes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

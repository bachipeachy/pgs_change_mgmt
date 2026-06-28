"""Semantic Preservation Gate — the post-compilation verification stage of the SDLC pipeline.

This is where verification belongs in the protocol lifecycle:

    Seed → S1…S9 (author + construct) → Compiler → Snapshot → [ Semantic Preservation Gate ] → RC

The gate makes Semantic Preservation a *contractual compiler guarantee*, checked automatically after
every construction: it loads the compiled structure's Semantic Substrate, builds the Forward IPM
(declared, from canonical frontmatter) and the Reverse IPM (compiled, from the evidence graph) via the
Compiler Semantic Interface, and runs ASSERT_ROUNDTRIP_EQUIVALENCE across all semantic axes. A clean
run is a Release Candidate; any axis that loses semantic coverage blocks it (or is recorded as a CSI
Finding for a known, accepted gap).

The gate reasons over compiler outputs only — it never reads authoring markdown or CRs — so it is an
independent, reproducible check on whether the compiler preserved protocol semantics end to end.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from pgs_compiler.compiler.projections.ipm import build_forward_ipm
from pgs_compiler.compiler.projections.reverse import SemanticSubstrate, reverse_project

from ..evaluator.roundtrip_equivalence import assert_roundtrip_equivalence, OracleReport


@dataclass
class GateResult:
    structure_id: str
    report: OracleReport

    @property
    def release_candidate(self) -> bool:
        """A Release Candidate iff every semantic axis round-tripped (full Semantic Preservation)."""
        return self.report.ok

    @property
    def coverage(self) -> float:
        return self.report.coverage


def run_gate(workspace: Path | str, structure_id: str) -> GateResult:
    """Build both IPMs from the compiled snapshot and assert semantic equivalence — the gate check."""
    sub = SemanticSubstrate.load(Path(workspace), structure_id)
    forward = build_forward_ipm(structure_id, sub.canonical_artifacts, set(sub.member_fqdns))
    reverse = reverse_project(sub)
    return GateResult(structure_id, assert_roundtrip_equivalence(forward, reverse))


def render(result: GateResult) -> str:
    """The gate's operator-facing surface: the coverage map + the release-candidate verdict."""
    rep = result.report
    verdict = ("RELEASE CANDIDATE — full semantic preservation"
               if result.release_candidate
               else f"BLOCKED — semantic preservation incomplete ({len(rep.issues())} finding(s))")
    lines = [rep.coverage_map(), "", f"Semantic Preservation Gate: {verdict}"]
    if not result.release_candidate:
        lines += ["", "Findings:"] + [f"  • {i}" for i in rep.issues()]
    return "\n".join(lines)


def _structures(ws: Path) -> list[str]:
    index = json.loads((ws / "protocol_snapshot" / "artifact_index" / "index.json").read_text())
    return sorted(index.get("structures", {}))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workspace", default=os.environ.get("PGS_WORKSPACE", ""))
    ap.add_argument("--structure", help="structure short-id (default: all structures in the snapshot)")
    args = ap.parse_args()
    if not args.workspace:
        ap.error("workspace required (--workspace or PGS_WORKSPACE)")
    ws = Path(args.workspace)

    structures = [args.structure] if args.structure else _structures(ws)
    blocked = 0
    for st in structures:
        result = run_gate(ws, st)
        print(render(result))
        print()
        if not result.release_candidate:
            blocked += 1
    # Exit non-zero iff a structure is blocked — the gate is a CI-usable release check.
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())

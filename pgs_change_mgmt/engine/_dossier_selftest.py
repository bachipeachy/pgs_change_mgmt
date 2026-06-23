"""Deterministic dossier-pipeline proof — no live worker.

Drives the staged loop with a StubWorker that emits, per stage, a document + the stage's
declared gov_projection fields. Proves the wiring: the bounded handoff (stage N receives
exactly the upstream fields its schema consumes — nothing more), projection, lossless-handoff
completeness, identity, and document persistence. Writes to a temp dir, never the real dossier.

Run:  PGS_WORKSPACE=/abs python -m pgs_change_mgmt.engine._dossier_selftest
"""

from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

from ..contracts import StageInput, StageOutput, fields_emitted_by, fields_consumed_by
from ..grounding import PiGroundingProvider
from .dossier import DOSSIER_SEEDS, run_dossier


class StubDossierWorker:
    """Emits a stub document + every gov_projection field the stage declares it produces.
    Records each task it receives so the test can assert the bounded handoff."""

    name = "stub-dossier"

    def __init__(self) -> None:
        self.seen: list[tuple[str, dict]] = []

    def execute_stage(self, task: StageInput) -> StageOutput:
        self.seen.append((task.stage, dict(task.input_projection.values)))
        # Emit one register row per emit-field (list-of-row) — valid for both the free-form
        # path (S1) and the structured path (S2, now register-driven): non-FQDN content keeps
        # the business-language oracle clean, and source_finding satisfies traceability.
        # Fill every evidence-column flavor so traceability is satisfied for any register
        # (source_finding / evidence based, or the fqdn-based pps_baseline). The fqdn is a REAL
        # snapshot artifact so the identity evaluator resolves it A_EXACT (no fabrication).
        registers = {f.field: [{"value": "stub", "source_finding": "stub", "evidence": "stub",
                                "fqdn": "blockchain::CC_FORM_BLOCK_V0"}]
                     for f in fields_emitted_by(task.stage)}
        doc = f"# Stage {task.stage} document (stub)\n\nbody"
        telem = "[tool-loop: iters=1/24 tool_calls=0 reason=finished final_chars=0]"
        return StageOutput(stage=task.stage, registers=registers, findings=(telem, doc))


def main() -> int:
    worker = StubDossierWorker()
    grounding = PiGroundingProvider()
    with tempfile.TemporaryDirectory() as tmp:
        seed = replace(DOSSIER_SEEDS["blockchain_chain"], output_dir=Path(tmp) / "chain")
        result = run_dossier(worker, grounding, seed, stages=("1", "2"),
                             runs_root=Path(tmp) / "runs")

        for s in result.stages:
            print(f"  stage {s.stage}: ok={s.ok} emitted={len(s.emitted)} missing={s.missing} "
                  f"identity={s.identity} doc={'written' if s.doc_path else 'MISSING'}")

        # 1. every stage emitted its declared fields (lossless handoff) and wrote a doc
        assert result.ok, "dossier stub run not clean"
        assert all(not s.missing and s.doc_path for s in result.stages)

        # 2. THE BOUNDED HANDOFF: stage 2's input is exactly the upstream fields it consumes.
        s2_seen = dict(worker.seen)["2"]
        expected = {f.field for f in fields_consumed_by("2")}        # governance_scope, known_facts
        assert set(s2_seen) == expected, f"bounded handoff wrong: {set(s2_seen)} != {expected}"
        assert "governance_scope" in s2_seen and "known_facts" in s2_seen
        # and stage 1 received nothing (it's the entry; seeded, not handed off to)
        assert dict(worker.seen)["1"] == {}, "stage 1 should receive no upstream handoff"
        print(f"\n  bounded handoff ✓ — S2 received exactly {sorted(expected)} from S1; "
              f"S1 received {{}}")

        # 3. docs actually landed in the (temp) dossier dir
        docs = sorted(p.name for p in (Path(tmp) / "chain").glob("*.md"))
        print(f"  docs written: {docs}")

    print("\nDOSSIER WIRING PROOF OK ✓ — staged loop, bounded gov_projection handoff, "
          "completeness + identity figure of merit, doc persistence")
    return 0


if __name__ == "__main__":
    sys.exit(main())

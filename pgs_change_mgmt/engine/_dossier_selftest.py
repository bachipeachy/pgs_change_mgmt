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
        # Verification spine (Fix A): a stage emitting `belief_verification` must hand back one
        # valid disposition row per incoming System Belief, else the Tier-1 spine gate halts the
        # pipeline. Emit a structurally complete ledger so this WIRING proof stays admissible.
        if "belief_verification" in registers:
            n = len(task.input_projection.values.get("system_beliefs") or []) or 1
            registers["belief_verification"] = [
                {"belief": f"stub belief {k}", "result": "VERIFIED",
                 "evidence": "blockchain::CC_FORM_BLOCK_V0", "source_finding": "stub"}
                for k in range(n)
            ]
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

    # 4. ADMISSIBILITY GATES — an inadmissible stage must NOT persist a consumable handoff and must
    #    HALT the pipeline (compiler discipline: no object file from a failed compile).
    from .dossier import HALT_EMPTY_EMIT, HALT_SPINE_INVALID

    def _wrap(mutate):
        w = StubDossierWorker()
        orig = w.execute_stage

        def run(task: StageInput) -> StageOutput:
            return mutate(task, orig(task))

        w.execute_stage = run  # type: ignore[method-assign]
        return w

    # 4a. EMPTY_EMIT at S3 — the live blockchain_chain failure: S1/S2 clean, S3 emits nothing.
    with tempfile.TemporaryDirectory() as tmp:
        seed = replace(DOSSIER_SEEDS["blockchain_chain"], output_dir=Path(tmp) / "chain")
        result = run_dossier(
            _wrap(lambda t, o: replace(o, registers={}) if t.stage == "3" else o),
            PiGroundingProvider(), seed, stages=("1", "2", "3", "4"), runs_root=Path(tmp) / "runs")
        s3 = next(s for s in result.stages if s.stage == "3")
        assert s3.halt_reason == HALT_EMPTY_EMIT and not s3.ok, "empty S3 projection must be inadmissible"
        assert not (Path(tmp) / "chain" / "cr_ir" / "3.json").exists(), \
            "empty projection must NOT persist a consumable handoff (the bug)"
        assert [s.stage for s in result.stages] == ["1", "2", "3"], "pipeline must HALT before S4"
        assert not result.ok
        # diagnostics must capture the raw worker output so the failure stays inspectable
        chain = Path(tmp) / "chain"
        diag = json.loads((chain / "3_analysis_loop_blockchain_chain_diagnostics.json").read_text())
        assert diag["raw_register_keys"] == [] and "raw_output_file" in diag, \
            "diagnostics must record the worker's raw register keys + output"
        assert (chain / diag["raw_output_file"]).exists(), "raw worker output must be persisted"
        print(f"\n  empty-projection gate ✓ — S3 emitted {{}} → INADMISSIBLE [{s3.halt_reason}], "
              "no 3.json persisted, halted before S4; raw output captured for diagnosis")

    # 4b. VERIFICATION_SPINE_INVALID at S2 — output produced, belief ledger empty.
    def _empty_spine(t: StageInput, o: StageOutput) -> StageOutput:
        return (replace(o, registers={**o.registers, "belief_verification": []})
                if "belief_verification" in o.registers else o)

    with tempfile.TemporaryDirectory() as tmp:
        seed = replace(DOSSIER_SEEDS["blockchain_chain"], output_dir=Path(tmp) / "chain")
        result = run_dossier(_wrap(_empty_spine), PiGroundingProvider(), seed,
                             stages=("1", "2", "3"), runs_root=Path(tmp) / "runs")
        s2 = next(s for s in result.stages if s.stage == "2")
        assert s2.halt_reason == HALT_SPINE_INVALID and not s2.ok, "incomplete spine must be inadmissible"
        assert not (Path(tmp) / "chain" / "cr_ir" / "2.json").exists()
        assert [s.stage for s in result.stages] == ["1", "2"], "pipeline must HALT before S3"
        print(f"  spine gate ✓ — S2 empty belief ledger → INADMISSIBLE [{s2.halt_reason}], "
              f"no 2.json persisted, halted before S3; defect: {s2.spine_defects[0]}")

    # 5. COMPLETENESS — a required human-authored prose section that ships as an unfilled `[...]`
    #    placeholder is a GAP: it marks the stage not-ok and is reported, but it is NOT a halt
    #    (no resolution path until human injection exists, and it does not propagate downstream).
    from ..renderer.dossier_stage import unfilled_prose_placeholders
    from .dossier import StageResult
    # the gap is NAMED by its nearest heading so the console can say WHICH section is open
    assert unfilled_prose_placeholders("## Purpose\n\n[Purpose paragraph for x.]\n") == \
        ["§Purpose — [Purpose paragraph for x.]"], "must detect + name a standalone placeholder line"
    assert unfilled_prose_placeholders("filled prose, see [ref](u) and range [0,1]") == [], \
        "must NOT false-positive on inline brackets / links"
    sr = StageResult(stage="5", structured=True, incomplete_sections=["[Purpose paragraph for x.]"])
    sr.doc_path = Path("x")
    assert not sr.ok and sr.halt_reason is None, "incomplete required section → not-ok, but NOT a halt"
    assert sr.rating < 5, "an incomplete required section costs a star"
    print("  completeness check ✓ — unfilled required prose section → gap (not-ok, reported, NOT halted)")

    print("\nDOSSIER WIRING PROOF OK ✓ — staged loop, bounded gov_projection handoff, "
          "completeness + identity figure of merit, doc persistence, admissibility gates "
          "(empty-projection + verification spine), required-section completeness")
    return 0


if __name__ == "__main__":
    sys.exit(main())

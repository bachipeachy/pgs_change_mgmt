"""Trifecta integration proof (I3) — deterministic, NO model, NO live grounding.

Three claims that make Guided Authoring Mode a first-class peer of the automated path:

  A. parse_output mode-adapter — automated / interactive / replay extract the SAME registers from
     equivalent inputs (one core + thin per-mode pre-normalizers; no forked parsers).
  B. figure-of-merit parity — the same registers produce the SAME governance verdict whether they
     arrive from a stub automated worker or a guided (interactive) paste; the only rating delta is
     the transport-specific tool-loop-convergence term, which legitimately does not apply to a paste.
  C. Worker Observability — a Guided stage emits a Worker Protocol Trace that renders an HONEST
     interactive view (transport=interactive, HUMAN_BOUNDARY, ingress-gated), not a fabricated
     in-loop grounding failure.

Run: python -m pgs_change_mgmt.engine._trifecta_selftest
"""

from __future__ import annotations

import dataclasses
import json
import sys
import tempfile
from pathlib import Path

from ..contracts import StageInput, StageOutput, GovProjection, fields_emitted_by
from ..evaluator import IdentityEvaluator
from ..worker import parse_output, InteractiveWorker
from ..worker._diagnostics import WorkerProtocolTrace, Termination
from .dossier import DOSSIER_SEEDS, run_dossier, rate_stage
from .stage_package import StagePackageBuilder

PASS, FAIL = "✅", "❌"
_EVIDENCE = {"source_finding", "evidence", "fqdn", "reference", "evidence_status"}


def _check(cond: bool, label: str) -> bool:
    print(f"  {PASS if cond else FAIL} {label}")
    return cond


class _FakeGrounding:
    def query(self, op, /, **kwargs):
        if op == "validate":
            return {"result": {"snapshot_hash": "selftest-snapshot", "status": "VALID"}}
        return {"result": {}}


class _StubAutoWorker:
    """An automated worker that returns fixed registers with natural tool-loop telemetry."""

    name = "stub-auto"

    def __init__(self, registers: dict) -> None:
        self._registers = registers

    def execute_stage(self, task: StageInput) -> StageOutput:
        telem = "[tool-loop: iters=3/24 tool_calls=5 reason=finished final_chars=512]"
        return StageOutput(stage=task.stage, registers=self._registers, findings=(telem,))


def _synth_row(spec: dict) -> dict:
    row = {}
    enums = spec.get("enums", {})
    ev = set(spec.get("evidence_columns", ())) | _EVIDENCE
    for col in spec["columns"]:
        if col in ev:
            row[col] = "seed §1"
        elif col in enums:
            row[col] = enums[col][0]
        else:
            row[col] = "an example business value in plain language"
    return row


def _s1_registers(schema: dict) -> dict:
    emit = {f.field for f in fields_emitted_by("1")}
    return {rid: [_synth_row(spec)] for rid, spec in schema["registers"].items() if rid in emit}


def _gov_tuple(s) -> tuple:
    """The governance-meaningful figure of merit — transport-independent."""
    return (sorted(s.emitted), sorted(s.missing), s.coverage, s.governed_coverage,
            tuple(sorted(s.oracle_issues)), s.inadmissible, s.structured,
            tuple(sorted(s.identity.items())))


def _proof_a() -> bool:
    print("A. parse_output mode-adapter (one core, three transports)")
    payload = {"registers": {"x": [{"a": "1", "b": "2"}]}, "questions": ["q1"]}
    block = json.dumps(payload)
    fenced = f"some reasoning\n```json\n{block}\n```\ntrailing"
    bare_paste = f"Sure — here are the registers:\n{block}\nHope this helps!"   # dropped fence

    ra, qa, _ = parse_output("automated", fenced)
    rr, qr, _ = parse_output("replay", fenced)
    ri, qi, _ = parse_output("interactive", fenced)            # interactive tolerates a fence too
    rb, qb, _ = parse_output("interactive", bare_paste)        # …and a dropped fence

    ok = True
    ok &= _check(ra == rr == ri == rb == {"x": [{"a": "1", "b": "2"}]},
                 "identical registers from automated / replay / interactive(fenced) / interactive(bare)")
    ok &= _check(qa == qr == qi == qb == ("q1",), "identical questions across modes")
    try:
        parse_output("bogus", fenced)
        bad = False
    except ValueError:
        bad = True
    ok &= _check(bad, "unknown mode is a programming error (ValueError)")
    return ok


def _proof_bc(cfg, pkg_root, runs_root) -> bool:
    print("B. figure-of-merit parity (guided == automated, governance verdict)")
    builder = StagePackageBuilder(cfg)
    pkg = builder.build("1", out_root=pkg_root)
    schema = json.loads((pkg / "schema.json").read_text())
    registers = _s1_registers(schema)

    # automated stub
    auto_cfg = dataclasses.replace(cfg, output_dir=cfg.output_dir.parent / "auto")
    res_a = run_dossier(_StubAutoWorker(registers), _FakeGrounding(), auto_cfg, stages=("1",),
                        evaluator=IdentityEvaluator(vocab=()), runs_root=runs_root / "auto")
    s_auto = res_a.stages[0]

    # guided: write the SAME registers as a response.md, import via InteractiveWorker
    (pkg / "response.md").write_text(f"grounded.\n\n```json\n{json.dumps({'registers': registers})}\n```\n")
    res_i = run_dossier(InteractiveWorker(pkg, model_label="parity"), _FakeGrounding(), cfg,
                        stages=("1",), evaluator=IdentityEvaluator(vocab=()), runs_root=runs_root / "int")
    s_int = res_i.stages[0]

    ok = True
    ok &= _check(_gov_tuple(s_auto) == _gov_tuple(s_int),
                 "identical governance figure of merit (emitted/missing/coverage/identity/oracle/admissible)")
    # a CLEAN artifact scores identically across transports: the convergence term fires only on an
    # actual iterative failure (forced/max_iters/stall), a notion a single-shot human paste does not
    # have and is not penalized for (its telemetry carries no `reason=`). Observability lives in the
    # Worker Protocol Trace, not the quality star — so process-convergence never outranks correctness.
    ok &= _check(s_auto.rating == s_int.rating and "reason=finished" in s_auto.telemetry
                 and "reason=" not in s_int.telemetry,
                 f"clean guided scores identically to clean automated (auto={s_auto.rating} guided={s_int.rating})")

    print("C. Worker Observability — Guided emits an honest Worker Protocol Trace")
    trace = WorkerProtocolTrace()
    InteractiveWorker(pkg, model_label="claude-code",
                      on_event=trace.collect).execute_stage(
        StageInput(stage="1", objective="", input_projection=GovProjection("1", {})))
    rendered = trace.render()
    ok &= _check(trace.is_interactive and trace.termination is Termination.HUMAN_BOUNDARY,
                 "trace is interactive · termination = HUMAN_BOUNDARY")
    ok &= _check("transport=interactive" in rendered and "out-of-band" in rendered,
                 "render shows out-of-band grounding at the human boundary")
    ok &= _check("InteractiveIngressValidator" in rendered, "render names the boundary gate")
    ok &= _check("Model emitted tool call:" not in rendered,
                 "render does NOT fabricate an in-loop tool-call failure line")
    ok &= _check("claude-code" in rendered, "render records the model label")
    return ok


def main() -> int:
    ok = _proof_a()
    base = DOSSIER_SEEDS["blockchain_chain"]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cfg = dataclasses.replace(base, output_dir=root / "guided")
        ok &= _proof_bc(cfg, root / "packages", root / "runs")
    print(f"\n{'ALL PASS' if ok else 'FAILURES PRESENT'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

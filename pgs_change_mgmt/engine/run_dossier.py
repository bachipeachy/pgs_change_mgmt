"""Drive the dossier pipeline with a live worker — checkpoint (one-stage) by default.

`--worker` and `--model` are REQUIRED (no silent default) — the model is a conscious choice:

    PGS_WORKSPACE=/abs python -m pgs_change_mgmt.engine.run_dossier --worker qwen --model qwen3.5:latest --stage 1
    python -m pgs_change_mgmt.engine.run_dossier --worker qwen --model qwen2.5-coder:32b --stages 1,2,3
    python -m pgs_change_mgmt.engine.run_dossier --worker claude --model claude-opus-4-8 --stage 6b

Authors ONE stage at a time and STOPS for human disposition: review the document, the
standalone handoff (`chain/_handoff/<stage>.json`), and the verbose grounding log, then
re-run the stage to regenerate or advance to the next. The bounded gov_projection is the
only thing that crosses to the next stage, persisted to disk so stages resume across runs.

Verbose by default: live R/Y/G grounding stream + per-stage figure of merit and 0–5★ rating.
Run on a branch (writes the authored docs into the CR's dossier dir; `git diff` shows changes).
"""

from __future__ import annotations

import argparse
import sys

from ..grounding import PiGroundingProvider, CachingGroundingProvider
from ..worker import OllamaWorker, ClaudeWorker, GeminiWorker
from ..worker._diagnostics import WorkerProtocolTrace
from .dossier import run_dossier, tool_event_printer, color, stars, STAGE_ORDER


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Checkpointed dossier authoring (qwen or claude worker)")
    ap.add_argument("--seed", default="blockchain_chain")
    ap.add_argument("--worker", choices=("ollama", "qwen", "claude", "gemini"), required=True,
                    help="transport that drives authoring: ollama (any local model — qwen, deepseek, …; "
                         "'qwen' is a back-compat alias), claude (Anthropic API), or gemini (Google API)")
    ap.add_argument("--model", required=True,
                    help="model id (explicit, no default) — e.g. qwen3.5:latest, "
                         "qwen2.5-coder:32b, claude-opus-4-8, gemini-flash-latest")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--stage", default=None, help="author a SINGLE stage then stop (e.g. '2')")
    g.add_argument("--stages", default=None, help="explicit comma-separated subset, e.g. '1,2,3'")
    ap.add_argument("--max-iters", type=int, default=24, help="worker tool-loop cap per stage")
    ap.add_argument("--quiet", action="store_true", help="suppress the live grounding stream")
    ap.add_argument("--no-cache", action="store_true",
                    help="disable the pi result cache (default: cache, keyed by snapshot hash)")
    ap.add_argument("--diagnose", action="store_true",
                    help="emit the Worker Protocol Trace (worker-observability evidence) after the stage")
    args = ap.parse_args(argv)

    if args.stage:
        stages = (args.stage,)
    elif args.stages:
        stages = tuple(s.strip() for s in args.stages.split(","))
    else:
        stages = STAGE_ORDER

    verbose = not args.quiet
    g_prov = PiGroundingProvider()
    if not args.no_cache:
        g_prov = CachingGroundingProvider(g_prov)   # JIT disk cache, keyed by snapshot hash
    on_event = tool_event_printer if verbose else None
    trace = WorkerProtocolTrace() if args.diagnose else None
    if trace is not None:
        _base = on_event
        def on_event(kind, **f):                    # compose: live stream (if any) + trace collection
            if _base is not None:
                _base(kind, **f)
            trace.collect(kind, **f)
    model = args.model
    if args.worker == "claude":
        worker = ClaudeWorker(g_prov, model=model, max_iters=args.max_iters, on_event=on_event)
    elif args.worker == "gemini":
        worker = GeminiWorker(g_prov, model=model, max_iters=args.max_iters, on_event=on_event)
    else:
        worker = OllamaWorker(g_prov, model=model, max_iters=args.max_iters, on_event=on_event)
    print(f"worker={args.worker}  seed={args.seed}  model={model}  stages={stages}  "
          f"max_iters={args.max_iters}  cache={'off' if args.no_cache else 'on'}\n")

    result = run_dossier(worker, g_prov, args.seed, stages=stages, verbose=verbose)

    if not args.no_cache:
        print(color("dim", "  " + g_prov.stats))

    print(color("bold", f"\n══ summary ══  run dir: {result.run_dir}"))
    print(color("dim", "  idn(A/B/C/D/E) = grounded / alias / wrong-domain / inferred(class-D) / fabrication"))
    for s in result.stages:
        i = s.identity
        if s.structured and s.governed_coverage is not None:
            gov = color("green" if s.governed_coverage == 1.0 else "red", f"governed={s.governed_coverage:.0%}")
            aud = f"audit={s.audit_coverage:.0%}" if s.audit_coverage is not None else "audit=n/a"
            cov = f"{gov} {aud}"
        else:
            cov = f"cover={s.coverage:.0%}"
        tail = ""
        if s.belief_counts is not None:
            tot = sum(s.belief_counts.values())
            v = s.belief_counts.get("VERIFIED", 0)
            tail = f"  spine={v}/{tot} verified"
        if s.incomplete_sections:
            tail += color("red", f"  gaps={len(s.incomplete_sections)}")
        if s.inadmissible:
            tail = color("red", f"  HALT[{s.halt_reason}]")
        idn = "/".join(str(i.get(k, 0)) for k in
                       ("A_EXACT", "B_TYPO_ALIAS", "C_WRONG_DOMAIN", "D_PROPOSED_NEW", "E_FABRICATION"))
        idn = color("red", idn) if i.get("E_FABRICATION", 0) else idn
        print(f"  S{s.stage:3} {stars(s.rating)} {s.rating}/5  "
              f"fields {len(s.emitted)}/{len(s.emitted)+len(s.missing)}  "
              f"idn {idn}  {cov}{tail}")
    # the governance vs oracle distinction the expert asked to surface
    if result.stages and all(s.governed_coverage == 1.0 for s in result.stages if s.structured):
        print(color("green", "\nGOVERNANCE OUTCOME: PASS (every S4-bound register clean)"))
    halted = next((s for s in result.stages if s.inadmissible), None)
    if halted is not None:
        print(color("red", f"HALTED at S{halted.stage} [{halted.halt_reason}] — "
                           "regenerate that stage before advancing."))
    print(f"DOSSIER RUN OK: {result.ok}")
    if trace is not None:
        print(color("bold", "\n══ Worker Protocol Trace ══"))
        print(trace.render())
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())

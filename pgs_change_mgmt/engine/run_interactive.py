"""Guided Authoring Mode — the two-phase runner (export a Stage Package, import a pasted response).

The third execution mode of the trifecta, driven by a human as the synchronization point. Same
validation / handoff / figure-of-merit as the automated path; only the transport differs.

    # 1. EXPORT — write the governed Stage Package for a stage (stamps the live snapshot hash):
    PGS_WORKSPACE=/abs python -m pgs_change_mgmt.engine.run_interactive --seed blockchain_chain --stage 1 --export

    #    → paste the model's reply into  <dir>/stage_1/response.md  (run `pi …` to ground as you go)

    # 2. IMPORT — ingress-validate the pasted response, then run the engine for that stage:
    PGS_WORKSPACE=/abs python -m pgs_change_mgmt.engine.run_interactive --seed blockchain_chain --stage 1 --import \
        --model-label claude-code

Export is pure governance (no model). Import ingress-validates at the human mutation boundary BEFORE
the engine sees the response, then runs `DossierEngine` for that one stage with `InteractiveWorker` —
producing the SAME document + `_handoff/<stage>.json` + figure-of-merit an automated worker would.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..grounding import PiGroundingProvider, CachingGroundingProvider
from ..worker import InteractiveWorker, InteractiveIngressValidator
from ..worker._diagnostics import WorkerProtocolTrace
from .dossier import run_dossier, tool_event_printer, color, stars, _resolve_seed
from .stage_package import StagePackageBuilder


def _packages_root(cfg, override: str | None) -> Path:
    return Path(override) if override else (cfg.output_dir / "_packages")


def _export(args, cfg) -> int:
    # ── Authoring Completeness gate (pre-stage): human-owned, non-derivable inputs due before this
    #    stage must be supplied by a human first. Symmetric with ingress — AUTHORING_INCOMPLETE :
    #    stage :: NACK : ingress. Structural (present/absent), never judges content. ──────────────
    from .authoring_completeness import check_authoring_completeness
    readiness = check_authoring_completeness(cfg, args.stage)
    if not readiness.ok:
        print(color("red", readiness.render()))
        print(color("red", "\n■ AUTHORING_INCOMPLETE — the Stage Package was NOT exported. Supply the "
                          "human-owned field(s) above, then re-export."))
        return 2

    grounding = PiGroundingProvider()   # ground ONLY to stamp the snapshot hash into the manifest
    builder = StagePackageBuilder(cfg, grounding=grounding)
    root = _packages_root(cfg, args.dir)
    pkg = builder.build(args.stage, out_root=root)
    print(color("bold", f"\n✅ exported Stage Package → {pkg}"))
    print("   files: manifest.json · prompt_bundle.json · system_prompt.md · user_prompt.md ·")
    print("          context/handoff.json · context/grounding_spec.json · expected_output.md · schema.json")
    print(color("bold", "\n next steps (Guided Authoring):"))
    print(f"   1. Open  {pkg / 'system_prompt.md'}  and  {pkg / 'user_prompt.md'}  in a chat LLM")
    print(f"      (Claude Code can ground in-session: run `pi vocab search <TOKEN>` for each token in")
    print(f"       {pkg / 'context' / 'grounding_spec.json'} — confirm before you assert; a 0-result is final).")
    print(f"   2. Paste the model's full reply into  {pkg / 'response.md'}")
    print(f"   3. Import:  PGS_WORKSPACE=$PGS_WORKSPACE python -m pgs_change_mgmt.engine.run_interactive "
          f"--seed {args.seed} --stage {args.stage} --import")
    return 0


def _import(args, cfg) -> int:
    root = _packages_root(cfg, args.dir)
    pkg = root / f"stage_{args.stage}"
    if not pkg.exists():
        print(color("red", f"no package at {pkg} — run --export for stage {args.stage} first"))
        return 2

    # ── human mutation boundary: ingress-validate BEFORE the engine sees the response ──────────
    ingress = InteractiveIngressValidator(pkg)
    verdict, _registers = ingress.validate_response_file()
    print(verdict.render())
    if not verdict.ok:
        print(color("red", "\n■ REJECTED at the human mutation boundary — the engine was NOT run. "
                          "Fix the pasted response.md and re-import."))
        return 1

    # ── DP4 — disposition-completeness gate: enforce that the worker disposed of every element the
    #    platform acquired (only when a Computed Semantic Neighborhood shipped). Completeness only;
    #    the gate never judges disposition content (boundary-creep guard). ────────────────────────
    from .disposition_gate import check_disposition
    gate = check_disposition(pkg)
    print(gate.render())
    if not gate.ok:
        print(color("red", "\n■ REJECTED — judgment incomplete: the platform acquired the semantic "
                          "neighbourhood but the response left elements undisposed. The engine was NOT "
                          "run. Add neighbourhood_disposition rules and re-import."))
        return 1

    # ── identical to automated from here: engine renders, oracles, persists handoff, rates ─────
    g_prov = PiGroundingProvider()
    if not args.no_cache:
        g_prov = CachingGroundingProvider(g_prov)
    verbose = not args.quiet
    on_event = tool_event_printer if verbose else None
    trace = WorkerProtocolTrace() if args.diagnose else None
    if trace is not None:
        _base = on_event
        def on_event(kind, **f):
            if _base is not None:
                _base(kind, **f)
            trace.collect(kind, **f)

    worker = InteractiveWorker(pkg, model_label=args.model_label, on_event=on_event)
    print(color("bold", f"\n▶ importing guided response for stage {args.stage} "
                        f"(model_label={args.model_label})\n"))
    result = run_dossier(worker, g_prov, args.seed, stages=(args.stage,), verbose=verbose)

    print(color("bold", f"\n══ summary ══  run dir: {result.run_dir}"))
    for s in result.stages:
        cov = (f"governed={s.governed_coverage:.0%}" if s.structured and s.governed_coverage is not None
               else f"cover={s.coverage:.0%}")
        tail = color("red", f"  HALT[{s.halt_reason}]") if s.inadmissible else ""
        print(f"  S{s.stage:3} {stars(s.rating)} {s.rating}/5  fields {len(s.emitted)}  {cov}{tail}")
    print(f"GUIDED IMPORT OK: {result.ok}")
    if trace is not None:
        print(color("bold", "\n══ Worker Protocol Trace (Guided) ══"))
        print(trace.render())
    return 0 if result.ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Guided Authoring Mode — export/import a Stage Package")
    ap.add_argument("--seed", default="blockchain_chain")
    ap.add_argument("--stage", required=True, help="the stage to export/import (e.g. '1', '2', '6b')")
    phase = ap.add_mutually_exclusive_group(required=True)
    phase.add_argument("--export", action="store_true", help="write the governed Stage Package")
    phase.add_argument("--import", dest="do_import", action="store_true",
                       help="ingress-validate the pasted response and run the engine for the stage")
    ap.add_argument("--dir", default=None, help="packages root (default: <dossier>/_packages)")
    ap.add_argument("--model-label", default="claude-code",
                    help="provenance label for the model that produced the response (audit trail)")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--diagnose", action="store_true",
                    help="emit the Worker Protocol Trace (Guided) after import")
    args = ap.parse_args(argv)

    cfg = _resolve_seed(args.seed)
    return _export(args, cfg) if args.export else _import(args, cfg)


if __name__ == "__main__":
    sys.exit(main())

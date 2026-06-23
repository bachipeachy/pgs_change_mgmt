"""Phase 4A live equivalence proof — one paste-safe command (no heredoc).

    PGS_WORKSPACE=/abs python -m pgs_change_mgmt.engine.run_proof
    python -m pgs_change_mgmt.engine.run_proof --no-oracle      # skip compile (faster smoke)
    python -m pgs_change_mgmt.engine.run_proof --model qwen3.5:latest --seed blockchain_mempool

Runs the NEW engine with the live qwen worker over the frozen mandate, judged by the compiler
oracle (compile + build + validate strict). PASS = `CLEAN RUN: True`. Run it on a throwaway
branch: it writes artifacts into the domain registry and recompiles protocol_snapshot.
"""

from __future__ import annotations

import argparse
import sys

from ..grounding import PiGroundingProvider
from ..worker import QwenWorker
from .engine import run
from .oracle import compiler_oracle


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Phase 4A equivalence proof (new engine, compiler oracle)")
    ap.add_argument("--seed", default="blockchain_mempool")
    ap.add_argument("--model", default="qwen3.5:latest")
    ap.add_argument("--no-oracle", action="store_true", help="skip the compiler oracle (render only)")
    ap.add_argument("--target", action="append", default=None,
                    help="author only this artifact code (repeatable); default: all seed targets")
    ap.add_argument("--max-iters", type=int, default=24,
                    help="cap the worker's tool-loop iterations (24 = old-harness default; "
                         "query-style CCs can need ~10+ grounding calls before finishing)")
    args = ap.parse_args(argv)

    g = PiGroundingProvider()
    oracle = None if args.no_oracle else compiler_oracle()
    targets = tuple(args.target) if args.target else None
    print(f"seed={args.seed}  model={args.model}  oracle={'off' if args.no_oracle else 'compiler'}"
          f"  targets={targets or 'all'}  max_iters={args.max_iters}\n")

    result = run(QwenWorker(g, model=args.model, max_iters=args.max_iters), g, args.seed,
                 targets=targets, compile_oracle=oracle)

    print(f"\nCLEAN RUN: {result.ok}")
    for t in result.targets:
        status = "rendered" if t.rendered_path else f"CONTRACT_ERROR={t.contract_error}"
        print(f"  {t.code:28} {status:24} verdict_ok={t.verdict_ok} oracle_ok={t.oracle_ok}")
    print(f"\naudit trail: {result.run_dir}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())

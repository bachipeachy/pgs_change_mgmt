"""Phase 5b runner — construct the CONSTRUCTION_READY chain sheets with one or more LOCAL builders
and report structural invention + builder-vs-builder convergence (via the Construction Oracle).

    export PGS_WORKSPACE=/abs/path/to/pgs_workspace
    python -m pgs_change_mgmt.engine.run_construction --models qwen3:14b qwen3.5:latest

Sheets are loaded from the AUTHORITATIVE governed JSON handoffs (no markdown re-parse). Invokes the
local models via ollama (slow). Writes each artifact to engine_runs/construction/ and prints, per
sheet: each builder's structural invention (unauthorised FQDN / field / routing label = ERROR; prose
mentions = text-invention WARN) and the pairwise convergence (same FQDN set ⇒ the sheet DETERMINED the
artifact). Note the field-level dimension: artifacts can converge at FQDN level yet still invent fields.
"""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

from .build_sheet import project_build_sheets, load_registers, load_entity_fields, CONSTRUCTION_READY
from ..evaluator.build_sheet_oracle import assert_construction_closed
from ..evaluator.construction_oracle import evaluate_build
from ..worker.construction import transcribe
from ..worker.ollama_client import OllamaClient

CHAIN = Path(__file__).resolve().parents[2] / "change_mgmt" / "dossiers" / "blockchain" / "chain"
EXEMPLAR_FQDN = "blockchain::CC_PERSIST_MEMPOOL_TX_V0"   # an existing CC — the FORMAT shape to follow


def _exemplar(fqdn: str) -> str:
    ws = os.environ.get("PGS_WORKSPACE", "")
    try:
        r = subprocess.run(["pi", "--workspace", ws, "artifact", "source", fqdn],
                           capture_output=True, text=True, timeout=60)
        return r.stdout if r.returncode == 0 else ""
    except Exception:
        return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=["qwen3:14b", "qwen3.5:latest"])
    ap.add_argument("--kinds", nargs="+", default=["CC"], help="transcribe sheets of these kinds")
    ap.add_argument("--exemplar", default=EXEMPLAR_FQDN, help="existing artifact to use as FORMAT shape")
    ap.add_argument("--timeout", type=float, default=900.0, help="per-call ollama timeout (seconds)")
    args = ap.parse_args()

    # AUTHORITATIVE input: the governed JSON handoffs (S5/S6b/S7). The pipeline never re-parses
    # narrative markdown (Projection Completeness Principle); fidelity of these handoffs against the
    # locked baseline is a separate governed gate (evaluator.projection_fidelity / its selftest).
    up = load_registers(CHAIN / "_handoff")
    # ground the governed field vocabulary from the compiled entities (zero-invention source)
    entity_fields = load_entity_fields(os.environ.get("PGS_WORKSPACE", ""), domain="blockchain")
    model = project_build_sheets(up, domain="blockchain", subdomain="chain", entity_fields=entity_fields)
    if entity_fields:
        print(f"entity-grounded vocabulary: {sum(len(v) for v in entity_fields.values())} fields "
              f"from {len(entity_fields)} entities ({', '.join(entity_fields)})\n")
    assert_construction_closed(model)   # raise clean sheets to CONSTRUCTION_READY

    sheets = [s for s in model.sheets if s.readiness == CONSTRUCTION_READY and s.kind in args.kinds]
    print(f"transcribing {len(sheets)} CONSTRUCTION_READY {args.kinds} sheet(s) with {args.models}\n")

    exemplar = _exemplar(args.exemplar)
    if not exemplar:
        print(f"WARN: no FORMAT exemplar fetched for {args.exemplar} (continuing without)")
    builders = {m: OllamaClient(model=m, timeout=args.timeout) for m in args.models}
    outdir = Path("engine_runs") / "construction"
    outdir.mkdir(parents=True, exist_ok=True)

    def _stopped(art: str) -> bool:
        return art.strip().startswith("STOP:")

    for sh in sheets:
        print(f"=== {sh.code} ({sh.kind}) ===")
        outs: dict[str, str] = {}
        for m, b in builders.items():
            tag = m.replace(":", "_").replace("/", "_")
            try:                                  # a slow local model timing out must not kill the run
                art = transcribe(sh, exemplar, b)
            except Exception as exc:
                print(f"  {m:18}    ERROR: {type(exc).__name__}: {exc} — skipped")
                continue
            outs[m] = art
            (outdir / f"{sh.code}__{tag}.md").write_text(art)
            if _stopped(art):
                print(f"  {m:18} {len(art):5} chars | ABSTAINED — {art.strip()}")
            else:
                ev = evaluate_build(sh, art)
                struct = ev.structural_invention   # ERROR — field/label/FQDN-level design invention
                text = ev.text_invention           # WARN  — prose-only mentions
                msg = "OK ✓" if ev.conformant else f"STRUCTURAL {struct}"
                if text:
                    msg += f"  (text: {text})"
                print(f"  {m:18} {len(art):5} chars | structural_invention: {msg}")
        # convergence compares only BUILT artifacts; a STOP is a located gap (abstention), not a
        # divergent design, and an ERROR is a transport skip — neither is a design disagreement.
        built = {m: o for m, o in outs.items() if not _stopped(o)}
        if len(built) >= 2:
            (ma, oa), (mb, ob) = list(built.items())[:2]
            c = evaluate_build(sh, oa, ob).convergence
            verdict = "CONVERGED ✓" if c["converged"] else f"DIVERGED (only_{ma}={c['only_a']} only_{mb}={c['only_b']})"
            print(f"  convergence: score={c['score']} {verdict}")
        elif any(_stopped(o) for o in outs.values()):
            abst = [m for m, o in outs.items() if _stopped(o)]
            print(f"  convergence: N/A — abstained: {abst} (a STOP is a located gap, not a divergent design)")
        else:
            print(f"  convergence: N/A — fewer than 2 builders produced output")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

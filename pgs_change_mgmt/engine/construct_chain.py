"""Construction phase (S8 → construct → bridge → S9) for the chain subdomain — the SDLC build step.

Produces, in the dossier `change_mgmt/dossiers/blockchain/chain/`:
  * `8_build_sheet_blockchain_chain_v0.md`        — the entity-grounded Build Sheet Set (S8)
  * `constructed/<CODE>.md`                       — each constructed protocol artifact (the build output)
  * `9_construction_record_blockchain_chain_v0.md`— the Construction Record (S9), built from the ACTUAL
                                                    bridge/compiler evidence, not authored

and promotes each compilable artifact into the protocol registry via the bridge (the compiler is the
gate; non-admissible artifacts are rolled back and their diagnostics recorded in S9 for regeneration).

    export PGS_WORKSPACE=/abs/pgs_workspace
    python -m pgs_change_mgmt.engine.construct_chain \
        --registry-root /abs/pgs_blockchain/pgs_blockchain/registry --models qwen3:14b --kinds CC

The worker is pluggable: qwen for the real run, any `Builder` for tests. Construction grounds the
governed field vocabulary from the compiled entities (zero invention) — the whole point of the entity
layer — so the transcribed artifacts use canonical fields and pass the compiler gate.
"""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

from .build_sheet import (load_registers, load_entity_fields, project_build_sheets,
                          render_markdown, CONSTRUCTION_READY)
from ..evaluator.build_sheet_oracle import assert_construction_closed
from ..worker.construction import transcribe
from ..worker.ollama_client import OllamaClient
from .bridge import promote_and_compile, BridgeResult

CHAIN = Path(__file__).resolve().parents[2] / "change_mgmt" / "dossiers" / "blockchain" / "chain"
DOMAIN, SUBDOMAIN = "blockchain", "chain"
BUILD_STRUCTURE = "STRUCTURE_BUILD_BLOCKCHAIN_CONFIG_V0"
EXEMPLAR_FQDN = "blockchain::CC_PERSIST_MEMPOOL_TX_V0"


def _exemplar(workspace: str, fqdn: str) -> str:
    try:
        r = subprocess.run(["pi", "--workspace", workspace, "artifact", "source", fqdn],
                           capture_output=True, text=True, timeout=60)
        return r.stdout if r.returncode == 0 else ""
    except Exception:
        return ""


def render_s9(results: list, *, abstained: list, build_structure: str) -> str:
    """S9 Construction Record — EVIDENCE, not authoring: per artifact, the bridge's compiler verdict."""
    built = [r for r in results if r.ok]
    failed = [r for r in results if not r.ok]
    L = [f"# Construction Record: {DOMAIN} / {SUBDOMAIN}",
         "**Pipeline Stage:** Stage 9 — Construction Record  ",
         f"**Build Structure:** {build_structure}  ",
         f"**Outcome:** {len(built)} compiled · {len(failed)} rejected · {len(abstained)} abstained",
         "", "## §1 Artifacts Built (compiler-validated, promoted to protocol registry)", ""]
    if built:
        L += ["| Artifact | Source | Compiled | Validated |", "|---|---|---|---|"]
        L += [f"| {r.code} | {r.dest} | ✓ | ✓ |" for r in built]
    else:
        L.append("NONE compiled-green this run.")
    L += ["", "## §2 Rejected by the Compiler Gate (rolled back; regenerate from diagnostics)", ""]
    if failed:
        for r in failed:
            L.append(f"- **{r.code}** — compiled={r.compiled} validated={r.validated}")
            L += [f"    - {d}" for d in r.diagnostics[:6]]
    else:
        L.append("NONE.")
    L += ["", "## §3 Abstentions (builder STOPped — a located gap, not invention)", ""]
    L += ([f"- **{code}** — {msg.strip()}" for code, msg in abstained] or ["NONE."])
    L += ["", "## §4 Approved Deviations / Waivers", "", "NONE.", ""]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--registry-root", required=True, help="pgs_blockchain registry root (protocol source)")
    ap.add_argument("--workspace", default=os.environ.get("PGS_WORKSPACE", ""))
    ap.add_argument("--models", nargs="+", default=["qwen3:14b"])
    ap.add_argument("--kinds", nargs="+", default=["CC"])
    ap.add_argument("--timeout", type=float, default=900.0)
    args = ap.parse_args()
    if not args.workspace:
        ap.error("workspace required (--workspace or PGS_WORKSPACE)")
    return run(registry_root=Path(args.registry_root), workspace=Path(args.workspace),
               builder=OllamaClient(model=args.models[0], timeout=args.timeout),
               kinds=tuple(args.kinds))


def run(*, registry_root: Path, workspace: Path, builder, kinds=("CC",)) -> int:
    # ---- S8: entity-grounded Build Sheet Set, persisted to the dossier ----
    up = load_registers(CHAIN / "_handoff")
    entity_fields = load_entity_fields(workspace, domain=DOMAIN)
    model = project_build_sheets(up, domain=DOMAIN, subdomain=SUBDOMAIN, entity_fields=entity_fields)
    assert_construction_closed(model)
    (CHAIN / f"8_build_sheet_{DOMAIN}_{SUBDOMAIN}_v0.md").write_text(render_markdown(model))
    vocab = sorted({f for v in entity_fields.values() for f in v})
    print(f"S8 persisted · entity-grounded vocabulary: {len(vocab)} fields from {len(entity_fields)} entities")

    sheets = [s for s in model.sheets if s.readiness == CONSTRUCTION_READY and s.kind in kinds]
    exemplar = _exemplar(str(workspace), EXEMPLAR_FQDN)
    out_dir = CHAIN / "constructed"
    out_dir.mkdir(parents=True, exist_ok=True)

    results: list[BridgeResult] = []
    abstained: list[tuple[str, str]] = []
    for sh in sheets:
        art = transcribe(sh, exemplar, builder)
        (out_dir / f"{sh.code}.md").write_text(art)            # the build output, kept in the dossier
        if art.strip().startswith("STOP:"):
            abstained.append((sh.code, art))
            print(f"  {sh.code}: ABSTAINED — {art.strip()}")
            continue
        res = promote_and_compile(art, registry_root=registry_root, subdomain=SUBDOMAIN,
                                  workspace=workspace, build_structure=BUILD_STRUCTURE)
        results.append(res)
        print(f"  {sh.code}: compiled={res.compiled} validated={res.validated} "
              f"{'PROMOTED ✓' if res.ok else 'rejected — ' + (res.diagnostics[0][:80] if res.diagnostics else '')}")

    # ---- S9: Construction Record from the actual compiler evidence ----
    (CHAIN / f"9_construction_record_{DOMAIN}_{SUBDOMAIN}_v0.md").write_text(
        render_s9(results, abstained=abstained, build_structure=BUILD_STRUCTURE))
    print(f"S9 persisted · {sum(r.ok for r in results)} compiled, "
          f"{sum(not r.ok for r in results)} rejected, {len(abstained)} abstained")

    # ---- Semantic Preservation Gate: prove the compiler preserved protocol semantics end to end ----
    # The capstone of the pipeline (… → compile → snapshot → THIS). Report-only here: any accepted gap
    # surfaces as a gate finding (a CSI Finding) without aborting an otherwise-good build; the strict
    # release check is the standalone `semantic_preservation_gate` CLI, which exits non-zero if blocked.
    from .semantic_preservation_gate import run_gate, render
    print("\n" + render(run_gate(workspace, DOMAIN)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

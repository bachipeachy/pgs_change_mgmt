"""ONE-TIME MIGRATION — regenerate authoritative JSON handoffs from a locked markdown baseline.

THIS IS NOT A PIPELINE STAGE. It exists only to repair legacy dossiers whose `cr_ir/*.json` was
emitted before Projection Fidelity was a governed property — the chain baseline's JSON carried only
~25–40 % of the rows its own rendered markdown carried (the Phase-4 discovery). No pipeline component
imports this module; per the Projection Completeness Principle no *stage* may ever parse markdown.
This utility parses the locked baseline markdown ONCE, projects each stage's declared emit-fields into
a complete JSON handoff, asserts ASSERT_PROJECTION_FIDELITY, and freezes the result as the new
authoritative handoff. After every baseline dossier has been re-emitted natively under the completed
gov_projection contract, this module is deletable.

    python -m pgs_change_mgmt.engine._migrate_cr_ir_from_baseline \
        --dossier change_mgmt/dossiers/blockchain/chain --stages 5 6b 7
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..contracts.gov_projection import fields_emitted_by
from ..evaluator.projection_fidelity import assert_projection_fidelity
from .build_sheet import parse_registers

# stage → markdown filename stem (the locked baseline doc)
_STEM = {
    "1": "1_change_request", "2": "2_domain_model", "3": "3_analysis_loop",
    "4": "4_business_model", "5": "5_business_intent", "6": "6_governance_intent",
    "6b": "6b_design_intent", "7": "7_authoring_mandate",
}


def _stage_doc(dossier: Path, stage: str) -> Path | None:
    """The locked baseline markdown for a stage, or None if this dossier has no such stage."""
    stem = _STEM[stage]
    p = dossier / f"{stem}_{dossier.parent.name}_{dossier.name}_v0.md"
    if p.exists():
        return p
    hits = sorted(dossier.glob(f"{stem}_*_v0.md"))   # tolerate domain/subdomain naming variation
    return hits[0] if hits else None


def _md_path(dossier: Path, stage: str) -> Path:
    p = _stage_doc(dossier, stage)
    if p is None:
        raise FileNotFoundError(f"no markdown for stage {stage} under {dossier}")
    return p


def available_stages(dossier: Path) -> list[str]:
    """Worker-authored stages (S1→S7) this dossier actually has a baseline doc for (partials allowed)."""
    return [s for s in _STEM if _stage_doc(dossier, s) is not None]


def migrate_stage(dossier: Path, stage: str) -> tuple[Path, list[str]]:
    """Project the stage's declared emit-fields from its markdown into a complete handoff; freeze it.

    Returns (handoff_path, fidelity_issues). The handoff is written only when fidelity holds.
    """
    md_text = _md_path(dossier, stage).read_text()
    registers = parse_registers(md_text)
    emit = [f.field for f in fields_emitted_by(stage)]
    handoff = {field: registers[field] for field in emit if field in registers}

    issues = assert_projection_fidelity(stage, md_text, handoff)
    out = dossier / "cr_ir" / f"{stage}.json"
    # NEVER freeze an empty handoff: a stage that declares emit-fields but parses to zero registers is
    # a legacy pre-register doc (no <!-- register --> markers), not a migration — writing {} would be a
    # vacuously-"faithful" but useless authoritative handoff. Leave it absent and let the caller report.
    if handoff and not issues:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(handoff, indent=2) + "\n")
    return out, issues


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dossier", required=True, help="path to the locked dossier dir (…/blockchain/chain)")
    ap.add_argument("--stages", nargs="+", default=None,
                    help="stages to migrate; default = every S1→S7 stage this dossier has a doc for")
    ap.add_argument("--dry-run", action="store_true", help="report fidelity, do not write")
    args = ap.parse_args()
    dossier = Path(args.dossier).resolve()
    stages = args.stages or available_stages(dossier)

    rc = 0
    for stage in stages:
        md_text = _md_path(dossier, stage).read_text()
        registers = parse_registers(md_text)
        emit = [f.field for f in fields_emitted_by(stage)]
        handoff = {field: registers[field] for field in emit if field in registers}
        if fields_emitted_by(stage) and not handoff:
            rc = 1
            print(f"S{stage}: SKIPPED — legacy pre-register doc (no <!-- register --> markers); nothing to migrate")
            continue
        issues = assert_projection_fidelity(stage, md_text, handoff)
        counts = ", ".join(f"{k}={len(v)}" for k, v in handoff.items())
        if issues:
            rc = 1
            print(f"S{stage}: FIDELITY FAILED — not frozen:")
            for i in issues:
                print(f"   {i}")
            continue
        if not args.dry_run:
            out = dossier / "cr_ir" / f"{stage}.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(handoff, indent=2) + "\n")
        print(f"S{stage}: {'WOULD FREEZE' if args.dry_run else 'FROZEN'} {len(handoff)} register(s) — {counts}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

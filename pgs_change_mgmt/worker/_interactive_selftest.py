"""Guided Authoring Mode proof (I2) — deterministic, NO model, NO live grounding.

Exercises the full Guided round-trip without any LLM: export a Stage Package → stub a VALID
`response.md` → ingress-validate → import through `DossierEngine` → assert the handoff persisted and
a figure of merit was computed; then assert the ingress validator REJECTS malformed responses at the
human mutation boundary, and that the prompt_hash round-trips through the worker's provenance.

Run: python -m pgs_change_mgmt.worker._interactive_selftest
"""

from __future__ import annotations

import dataclasses
import json
import sys
import tempfile
from pathlib import Path

from ..contracts import GovProjection, StageInput, fields_emitted_by
from ..evaluator import IdentityEvaluator
from ..engine.dossier import DOSSIER_SEEDS, run_dossier
from ..engine.stage_package import StagePackageBuilder
from .interactive import InteractiveWorker
from .interactive_ingress import InteractiveIngressValidator

PASS, FAIL = "✅", "❌"
_EVIDENCE = {"source_finding", "evidence", "fqdn", "reference", "evidence_status"}


def _check(cond: bool, label: str) -> bool:
    print(f"  {PASS if cond else FAIL} {label}")
    return cond


class _FakeGrounding:
    """Answers only the engine's run-level `validate` query — S1/S2 need nothing else."""

    def query(self, op, /, **kwargs):
        if op == "validate":
            return {"result": {"snapshot_hash": "selftest-snapshot", "status": "VALID"}}
        return {"result": {}}


def _synth_row(spec: dict) -> dict:
    """One ingress-valid row for a register spec: evidence filled, enums respected, no FQDNs."""
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


def _valid_response(schema: dict) -> str:
    """A VALID guided response.md: reasoning text + a ```json registers block for every S1 emit
    register (so the stage is admissible and persists a handoff)."""
    emit = {f.field for f in fields_emitted_by("1")}
    regs = {rid: [_synth_row(spec)] for rid, spec in schema["registers"].items() if rid in emit}
    block = json.dumps({"registers": regs}, indent=2)
    return ("I grounded the stage and produced the registers below.\n\n"
            f"```json\n{block}\n```\n")


def main() -> int:
    ok = True
    base = DOSSIER_SEEDS["blockchain_chain"]
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        cfg = dataclasses.replace(base, output_dir=tmp_root / "dossier")
        pkg_root = tmp_root / "packages"

        # ---- export (hermetic — no grounding) ----------------------------------------------
        print("export → stub valid response → ingress → import")
        builder = StagePackageBuilder(cfg)
        pkg = builder.build("1", out_root=pkg_root)
        schema = json.loads((pkg / "schema.json").read_text())
        manifest = json.loads((pkg / "manifest.json").read_text())

        # ---- stub a VALID response.md and ingress-validate ---------------------------------
        (pkg / "response.md").write_text(_valid_response(schema))
        ingress = InteractiveIngressValidator(pkg)
        verdict, registers = ingress.validate_response_file()
        ok &= _check(verdict.ok, f"ingress ADMITS a valid response ({len(registers)} registers)")
        ok &= _check(verdict.schema_hash == schema["schema_hash"],
                     "ingress verdict carries the package schema_hash")

        # ---- import through the engine (identical path to automated) ------------------------
        worker = InteractiveWorker(pkg, model_label="selftest-model")
        result = run_dossier(worker, _FakeGrounding(), cfg, stages=("1",),
                             evaluator=IdentityEvaluator(vocab=()), runs_root=tmp_root / "runs")
        s = result.stages[0]
        ok &= _check(not s.inadmissible, f"stage admissible (rating {s.rating}/5)")
        handoff = cfg.output_dir / "_handoff" / "1.json"
        ok &= _check(handoff.exists(), "engine persisted _handoff/1.json (handoff produced)")
        doc = cfg.output_dir / "1_change_request_blockchain_chain_v0.md"
        ok &= _check(doc.exists() and doc.read_text().strip() != "", "engine rendered the S1 document")

        # ---- Human Mutation Boundary provenance + prompt_hash round-trip --------------------
        task = StageInput(stage="1", objective="", input_projection=GovProjection("1", {}))
        out = worker.execute_stage(task)
        prov = dict(out.provenance)
        ok &= _check(prov.get("origin") == "human_guided" and prov.get("mutation_boundary") is True,
                     "StageOutput carries the Human Mutation Boundary provenance (P5)")
        ok &= _check(prov.get("prompt_hash") == manifest["prompt_hash"],
                     "prompt_hash round-trips: worker provenance == package manifest")
        ok &= _check(prov.get("model_label") == "selftest-model", "provenance records the model_label")

        # ---- ingress REJECTS malformed responses at the boundary ---------------------------
        print("ingress rejects malformed responses")
        # (a) undeclared register
        v = ingress.validate({"not_a_real_register": [{}]})
        ok &= _check(not v.ok and any("not declared" in i for i in v.issues),
                     "rejects an undeclared register")
        # (b) FQDN smuggled into a business-language content column
        v = ingress.validate({"business_vocabulary": [
            {"term": "Block", "definition": "produced by blockchain::CC_FORM_BLOCK_V0",
             "source_finding": "seed §2"}]})
        ok &= _check(not v.ok and any("protocol identifier" in i for i in v.issues),
                     "rejects an FQDN in a business-language column")
        # (c) ungrounded row (no traceability) under strict mode
        v = ingress.validate({"business_vocabulary": [{"term": "Block", "definition": "a unit"}]})
        ok &= _check(not v.ok and any("ungrounded" in i for i in v.issues),
                     "rejects an ungrounded row (no traceability) in strict mode")
        # (d) missing response.md
        (pkg / "response.md").unlink()
        v2, _ = ingress.validate_response_file()
        ok &= _check(not v2.ok and any("no response.md" in i for i in v2.issues),
                     "rejects a missing response.md")

        # ---- worker raises a clear error when response.md is absent -------------------------
        try:
            worker.execute_stage(task)
            raised = False
        except FileNotFoundError:
            raised = True
        ok &= _check(raised, "InteractiveWorker raises FileNotFoundError when response.md is absent")

    print(f"\n{'ALL PASS' if ok else 'FAILURES PRESENT'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

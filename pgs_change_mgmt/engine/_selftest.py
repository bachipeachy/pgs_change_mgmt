"""Deterministic engine wiring proof — no live worker required.

Proves the engine coordinates all four seams end-to-end (worker → evaluator → renderer →
artifact) by injecting a StubWorker that returns a known-good mempool CC contract object. The
architecture's promise is exactly that this is all it takes to swap a worker: the live qwen
run is `run(OllamaWorker(grounding), grounding, "blockchain_mempool")` — same call, real worker.

Run:  PGS_WORKSPACE=/abs/path python -m pgs_change_mgmt.engine._selftest
"""

from __future__ import annotations

import re
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

import yaml

from ..contracts import StageInput, StageOutput
from ..grounding import PiGroundingProvider
from .engine import SEEDS, run


class StubWorker:
    """A `contracts.Worker` that returns a fixed, admissible mempool CC contract object.

    Deps are real snapshot FQDNs so the evaluator resolves them as A_EXACT — the same
    grounded outcome a correct qwen run must reach."""

    name = "stub-golden"

    def execute_stage(self, task: StageInput) -> StageOutput:
        contract = {
            "summary": "Write a signed transaction to the MEMPOOL staging buffer.",
            "intent": "Persist a pending tx to MEMPOOL and guard tx_id/tx_hash uniqueness.",
            "rationale": "Mempool staging is scoped to the mempool subdomain.",
            "inputs": [
                {"name": "tx_id", "type": "string", "required": True, "description": "tx id (prefix: TX)"},
                {"name": "amount", "type": "number", "required": True, "description": "amount in BACHI"},
            ],
            "outputs": [{"name": "mempool_key", "type": "string"}],
            "pipeline": [
                {"step": "gen_key", "kind": "CT",
                 "capability": "capability_transforms::CT_PURE_GENERATE_ID_V0", "op": "GENERATE_ID",
                 "inputs": {"seed": "$.inputs.tx_id"}, "outputs": {"mempool_key": "$.capability_result.id"},
                 "on_result": {"SUCCESS": "register_key", "VIOLATION": "exit"}},
                {"step": "register_key", "kind": "CS",
                 "capability": "capability_side_effects::CS_REGISTRY_V0", "store": "MEMPOOL_INDEX",
                 "op": "REGISTER", "inputs": {"key": "$.results.gen_key.mempool_key"}, "outputs": {},
                 "on_result": {"SUCCESS": "write_record", "ALREADY_EXISTS": "exit", "VIOLATION": "exit"}},
                {"step": "write_record", "kind": "CS",
                 "capability": "capability_side_effects::CS_MUTABLE_JSON_V0", "store": "MEMPOOL",
                 "op": "WRITE", "inputs": {"key": "$.inputs.tx_id"}, "outputs": {},
                 "on_result": {"SUCCESS": "exit", "VIOLATION": "exit", "BACKEND_ERROR": "exit"}},
            ],
            "extensions": {"subdomain": "mempool", "notes": ["stub wiring proof"]},
        }
        return StageOutput(stage=task.stage, registers=contract,
                           findings=("stub worker — fixed golden contract object",))


def main() -> int:
    seed = SEEDS["blockchain_mempool"]
    grounding = PiGroundingProvider()
    with tempfile.TemporaryDirectory() as tmp:
        # Write artifacts to a tmp dir — never into pgs_blockchain — and run a single target.
        seed_tmp = replace(seed, dest_root=Path(tmp))
        result = run(StubWorker(), grounding, seed_tmp,
                     targets=("CC_WRITE_MEMPOOL_TX_V0",), runs_root=Path(tmp) / "runs")

        tr = result.targets[0]
        print(f"snapshot_hash = {result.snapshot_hash}")
        print(f"authored      = {tr.authored}")
        print(f"evaluation    = {tr.detail.get('evaluation')}")
        print(f"verdict_ok    = {tr.verdict_ok}")
        print(f"rendered      = {tr.rendered_path}")
        if tr.contract_error:
            print(f"CONTRACT ERROR: {tr.contract_error}")
            return 1

        assert tr.authored, "worker produced no contract"
        assert tr.rendered_path and tr.rendered_path.exists(), "no artifact rendered"
        md = tr.rendered_path.read_text()
        block = re.search(r"```yaml\n(.*?)\n```", md, re.S).group(1)
        doc = yaml.safe_load(block)              # admissible YAML
        assert doc["cc_code"] == "CC_WRITE_MEMPOOL_TX_V0"
        # the three real deps resolved as exact identities (grounded, not invented)
        counts = tr.detail["evaluation"]
        assert counts.get("E_FABRICATION", 0) == 0, f"fabricated FQDN: {counts}"
        assert counts.get("A_EXACT", 0) >= 3, f"deps did not resolve A_EXACT: {counts}"
        assert result.ok, "engine run not clean"

    print("\nENGINE WIRING PROOF OK ✓ — worker→evaluator→renderer→artifact, admissible YAML, "
          "real deps A_EXACT, swap-in worker is the only change for the live qwen run")
    return 0


if __name__ == "__main__":
    sys.exit(main())

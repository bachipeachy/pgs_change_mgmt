"""ChangeEngine — the worker-agnostic process core (Phase 4A: artifact authoring).

The engine coordinates a governed run over the four seams without knowing any concrete
implementation: it hands a `Worker` a bounded `StageInput`, projects the `StageOutput` it gets
back, has the `Evaluator` resolve identity over the result, and the `Renderer` expand it to an
admissible artifact — then hands the artifact to a pluggable compiler oracle. Swapping the
qwen worker for Claude or a human is a constructor argument here, nothing more.

Phase 4A drives the *artifact-authoring* tier proven in the Phase-0 experiment
(`artifact_harness --structured`): a frozen Authoring Mandate (Stage 6b + 7) → structured CC
contract object → `CCRenderer` → compiler. The oracle is the compiler ("does it compile
clean"), so the equivalence proof — old harness == new engine — is objective, not text-diff.

Phase 4B generalizes the renderer beyond CC; Phase 5 drives the full CR → compile pipeline
with gov_projection throughout (the S1–S8 dossier tier). Neither is built here, by design —
the seams are declared so each is an addition, not a refactor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from ..contracts import GovProjection, StageInput, Worker, GroundingProvider, Evaluator
from ..evaluator import IdentityEvaluator
from ..renderer import ContractError, get_renderer
from .run_log import RunLog, now_stamp

# Repo layout (mirrors the Phase-0 harness): package repo = ~/pgs/pgs_change_mgmt.
PKG_REPO = Path(__file__).resolve().parents[2]
PGS = PKG_REPO.parent
DOSSIERS = PKG_REPO / "change_mgmt" / "dossiers"
BLOCKCHAIN_REGISTRY = PGS / "pgs_blockchain" / "pgs_blockchain" / "registry"

# The structured contract-object shape the worker must emit as its `registers` (the renderer
# owns all syntax). This is process knowledge the engine supplies — the worker stays generic.
CONTRACT_OBJECT_SHAPE = """Emit the contract object as your `registers`, with EXACTLY these keys:
  summary:   one line
  intent:    prose paragraph
  rationale: prose paragraph
  inputs:    [ {name, type(string|number|integer|boolean|array|object), required(bool), description} ]
  outputs:   [ {name, type, items_type (only for arrays)} ]
  pipeline:  [ {step, kind("CT"|"CS"), capability("capability_transforms::CT_..._V0" | "capability_side_effects::CS_..._V0"),
               store (CS steps only), op, inputs{<field>: "$.inputs.x"|"$.results.<step>.<f>"|literal},
               outputs{<field>: "$.capability_result.<f>"}, on_result{OUTCOME: "continue"|"exit"|"<step>"}} ]
  error_codes: {OUTCOME: CODE}   (optional)
  extensions:  {subdomain, notes[]}
Routing is OUTCOME-BASED only (on_result) — there is no if/expression routing. Do NOT emit
result_surface or result_status_contract; the renderer DERIVES them from your on_result keys."""

GOVERNANCE_RULES: tuple[str, ...] = (
    "You have NO protocol knowledge of your own — confirm every EXISTING dependency FQDN "
    "(CT_/CS_ capabilities, store names) via a grounding tool call; never invent an FQDN.",
    "Routing is outcome-based (on_result) only; no conditional/if routing.",
    "Follow the mandate's pipeline for this artifact exactly; do not redesign it.",
    "Emit the structured contract object only — no YAML, no Markdown (the renderer owns syntax).",
)


@dataclass(frozen=True)
class SeedConfig:
    """A named authoring seed: what to build, from which mandate, to where."""

    name: str
    kind: str                       # artifact kind (CC today)
    targets: tuple[str, ...]        # artifact codes to author
    mandate_dir: Path               # dir holding the frozen mandate files
    mandate_files: tuple[str, ...]  # Stage 6b + 7 files
    dest_root: Path                 # registry root the artifacts are written under
    dest_subdir: str                # kind subdir under dest_root (e.g. capability_contracts)
    authoring_stage: str = "7"      # evaluator stage: new code is a legit proposal (D), not E


# The proven Phase-0 target: blockchain/mempool, the three NEW CCs the 6b/7 mandate specifies.
SEEDS: dict[str, SeedConfig] = {
    "blockchain_mempool": SeedConfig(
        name="blockchain_mempool",
        kind="CC",
        targets=("CC_WRITE_MEMPOOL_TX_V0", "CC_QUERY_MEMPOOL_TXS_V0", "CC_DRAIN_MEMPOOL_V0"),
        mandate_dir=DOSSIERS / "blockchain" / "mempool",
        mandate_files=("6b_design_intent_mempool_v0.md", "7_authoring_mandate_mempool_v0.md"),
        dest_root=BLOCKCHAIN_REGISTRY / "mempool",
        dest_subdir="capability_contracts",
    ),
}


@dataclass
class TargetResult:
    code: str
    authored: bool = False               # worker produced a contract object
    verdict_ok: bool | None = None       # evaluator identity verdict
    rendered_path: Path | None = None    # admissible artifact written here
    contract_error: str | None = None    # shape/reasoning failure (renderer rejected)
    oracle_ok: bool | None = None         # compiler oracle result, if run
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunResult:
    seed: str
    run_dir: Path
    snapshot_hash: str | None
    targets: list[TargetResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """A run is clean iff every target authored, passed identity, rendered, and (if an
        oracle ran) compiled. This is the engine-level 'successful run' for the proof."""
        return bool(self.targets) and all(
            t.rendered_path is not None
            and t.verdict_ok is not False
            and t.oracle_ok is not False
            for t in self.targets
        )


# Compiler oracle: artifact path -> (ok, detail). Pluggable so the engine stays decoupled
# from the compiler; the CLI / equivalence harness supplies a real `pi validate` / compile.
CompileOracle = Callable[[Path], "tuple[bool, dict[str, Any]]"]


class ChangeEngine:
    """Coordinates one governed authoring run across worker / grounding / evaluator / renderer."""

    def __init__(
        self,
        worker: Worker,
        grounding: GroundingProvider,
        *,
        evaluator: Evaluator | None = None,
        runs_root: Path | None = None,
    ) -> None:
        self.worker = worker
        self.grounding = grounding
        self.evaluator = evaluator if evaluator is not None else IdentityEvaluator()
        self.runs_root = runs_root or (PKG_REPO / "engine_runs")

    # ---- the run ---------------------------------------------------------

    def run(
        self,
        seed: str | SeedConfig,
        *,
        targets: tuple[str, ...] | None = None,
        dest_root: Path | None = None,
        compile_oracle: CompileOracle | None = None,
    ) -> RunResult:
        cfg = seed if isinstance(seed, SeedConfig) else _resolve_seed(seed)
        codes = targets or cfg.targets
        out_root = (dest_root or cfg.dest_root) / cfg.dest_subdir

        # Anchor the run to a snapshot hash via the grounding seam (attestation).
        gate = self.grounding.query("validate")
        snapshot_hash = gate.get("result", {}).get("snapshot_hash")

        run_dir = self.runs_root / f"{cfg.name}_{now_stamp()}"
        log = RunLog(run_dir, {
            "engine": "ChangeEngine", "phase": "4A_artifact_authoring",
            "seed": cfg.name, "kind": cfg.kind, "worker": getattr(self.worker, "name", "?"),
            "targets": list(codes), "snapshot_hash": snapshot_hash,
            "dest_root": str(out_root),
        })

        mandate = self._mandate_text(cfg)
        result = RunResult(seed=cfg.name, run_dir=run_dir, snapshot_hash=snapshot_hash)
        for code in codes:
            result.targets.append(
                self._author_one(cfg, code, mandate, out_root, compile_oracle, log)
            )
        log.finalize(ok=result.ok,
                     authored=sum(t.authored for t in result.targets),
                     rendered=sum(t.rendered_path is not None for t in result.targets))
        return result

    # ---- one artifact ----------------------------------------------------

    def _author_one(self, cfg: SeedConfig, code: str, mandate: str, out_root: Path,
                    compile_oracle: CompileOracle | None, log: RunLog) -> TargetResult:
        tr = TargetResult(code=code)
        task = StageInput(
            stage=cfg.authoring_stage,
            objective=(
                f"Author the {cfg.kind} **{code}** (domain `blockchain`) from the frozen "
                f"Authoring Mandate in your bounded context, following the mandate's pipeline "
                f"specification for it.\n\n{CONTRACT_OBJECT_SHAPE}"
            ),
            input_projection=GovProjection(
                stage=cfg.authoring_stage,
                values={"target_code": code, "mandate": mandate},
            ),
            governance_rules=GOVERNANCE_RULES,
        )
        log.event("stage_input", code=code, objective_chars=len(task.objective))

        output = self.worker.execute_stage(task)
        contract = dict(output.registers)
        tr.authored = bool(contract)
        log.event("worker_output", code=code, register_keys=sorted(contract),
                  questions=list(output.questions))
        if not contract:
            # The worker emitted no parseable structured contract. Persist its raw output so
            # the failure is diagnosable (prose-only? malformed JSON? or a stalled tool-loop
            # that produced empty final content — distinguishable by whether findings is empty).
            raw = "\n\n".join(output.findings)
            (log.run_dir / f"{code}_raw_output.txt").write_text(raw or "(worker produced no content — likely a stalled/empty tool-loop)")
            tr.detail["findings"] = list(output.findings)
            log.event("author_empty", code=code, raw_chars=len(raw),
                      raw_output=f"{code}_raw_output.txt")
            return tr

        # Identity check over the authored contract (deps must resolve; new code is a legit D).
        verdict = self.evaluator.evaluate(output.to_projection(), stage=cfg.authoring_stage)
        tr.verdict_ok = verdict.ok
        tr.detail["evaluation"] = dict(verdict.detail.get("counts", {}))
        log.event("evaluation", code=code, ok=verdict.ok, counts=tr.detail["evaluation"])

        # Render the structured contract → admissible artifact (renderer owns syntax).
        renderer = get_renderer(cfg.kind)
        try:
            rendered = renderer.render({**contract, "code": code})
        except (ContractError, ValueError) as exc:
            tr.contract_error = str(exc)
            (log.run_dir / f"{code}_raw_contract.json").write_text(
                __import__("json").dumps(contract, indent=2, default=str))
            log.event("render", code=code, ok=False, error=str(exc))
            return tr

        out_root.mkdir(parents=True, exist_ok=True)
        dest = out_root / f"{code}.md"
        dest.write_text(rendered)
        tr.rendered_path = dest
        log.event("render", code=code, ok=True, dest=str(dest), chars=len(rendered))

        if compile_oracle is not None:
            ok, detail = compile_oracle(dest)
            tr.oracle_ok = ok
            tr.detail["oracle"] = detail
            log.event("compile_oracle", code=code, ok=ok, detail=detail)
        return tr

    # ---- helpers ---------------------------------------------------------

    @staticmethod
    def _mandate_text(cfg: SeedConfig) -> str:
        chunks = []
        for f in cfg.mandate_files:
            p = cfg.mandate_dir / f
            if not p.exists():
                raise FileNotFoundError(f"mandate file missing (fail hard): {p}")
            chunks.append(f"===== {f} =====\n\n{p.read_text()}")
        return "\n\n".join(chunks)


def _resolve_seed(name: str) -> SeedConfig:
    if name not in SEEDS:
        raise KeyError(f"unknown seed: {name!r} (known: {sorted(SEEDS)})")
    return SEEDS[name]


def run(
    worker: Worker,
    grounding: GroundingProvider,
    seed: str | SeedConfig,
    *,
    targets: tuple[str, ...] | None = None,
    dest_root: Path | None = None,
    runs_root: Path | None = None,
    evaluator: Evaluator | None = None,
    compile_oracle: CompileOracle | None = None,
) -> RunResult:
    """The single durable entry point: drive one governed authoring run.

    Example:
        run(worker=OllamaWorker(grounding), grounding=grounding, seed="blockchain_mempool")
    """
    engine = ChangeEngine(worker, grounding, evaluator=evaluator, runs_root=runs_root)
    return engine.run(seed, targets=targets, dest_root=dest_root, compile_oracle=compile_oracle)

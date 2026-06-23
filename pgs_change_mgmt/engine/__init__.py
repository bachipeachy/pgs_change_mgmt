"""engine — the worker-agnostic process core.

`run(worker, grounding, seed)` is the single durable entry point: it coordinates one governed
authoring run across the four seams (worker → grounding → evaluator → renderer) and a
pluggable compiler oracle, knowing only the *contracts*, never a concrete implementation.
Phase 4A drives the artifact-authoring tier (structured CC contract → compiler-as-oracle).

`RunLog` is the append-only per-run audit trail (promoted from the Phase-0 orchestrator).
"""

from .engine import (
    ChangeEngine,
    RunResult,
    TargetResult,
    SeedConfig,
    SEEDS,
    run,
)
from .dossier import (
    DossierEngine,
    DossierResult,
    StageResult,
    DossierSeedConfig,
    DOSSIER_SEEDS,
    STAGE_ORDER,
    run_dossier,
)
from .run_log import RunLog, now_stamp

__all__ = [
    "run",
    "ChangeEngine",
    "RunResult",
    "TargetResult",
    "SeedConfig",
    "SEEDS",
    "run_dossier",
    "DossierEngine",
    "DossierResult",
    "StageResult",
    "DossierSeedConfig",
    "DOSSIER_SEEDS",
    "STAGE_ORDER",
    "RunLog",
    "now_stamp",
]

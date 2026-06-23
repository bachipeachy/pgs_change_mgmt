"""Worker seam — the bounded task handed to a replaceable worker, and its result.

(change_agent_future.md Plugin #1.) **Process ≠ Worker.** The engine owns this contract;
a concrete worker (qwen today) conforms to it. Swapping one worker for another should have
the architectural impact of swapping a runtime capability handler.

The boundary object that crosses this seam is `gov_projection.GovProjection`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, runtime_checkable

from .gov_projection import GovProjection


@dataclass(frozen=True)
class StageInput:
    """The bounded task handed to a worker: the stage, its objective, the upstream
    `gov_projection` it may read (its *bounded context* — only declared-consumed fields),
    and the governance rules in force. A worker receives nothing else."""

    stage: str
    objective: str
    input_projection: GovProjection
    governance_rules: tuple[str, ...] = ()


@dataclass(frozen=True)
class StageOutput:
    """A worker's structured result — registers / questions / findings only. The engine
    projects it into the stage's emitted `gov_projection`. The worker never emits machine
    syntax (that is the Renderer's job) and never touches storage."""

    stage: str
    registers: Mapping[str, Any]
    questions: tuple[str, ...] = ()
    findings: tuple[str, ...] = ()

    def to_projection(self) -> GovProjection:
        return GovProjection(stage=self.stage, values=dict(self.registers))


@runtime_checkable
class Worker(Protocol):
    """A replaceable worker. Knows only how to execute a bounded stage task; it must never
    know the compiler, the runtime, governance internals, or artifact storage. Swapping one
    worker for another should have the architectural impact of swapping a runtime handler."""

    name: str

    def execute_stage(self, task: StageInput) -> StageOutput: ...

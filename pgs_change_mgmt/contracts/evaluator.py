"""Evaluator seam — identity-aware judgement over authored output or a `gov_projection`.

(change_agent_future.md Plugin #3.) An evaluator resolves identity before classifying
(A–E taxonomy); aggregate counts / regex matches are not an evaluator.
"""

from __future__ import annotations

from dataclasses import dataclass, field as _field
from typing import Any, Mapping, Protocol, runtime_checkable

from .gov_projection import GovProjection


@dataclass(frozen=True)
class Verdict:
    """An evaluator's result over authored output or a `gov_projection`."""

    ok: bool
    detail: Mapping[str, Any] = _field(default_factory=dict)


@runtime_checkable
class Evaluator(Protocol):
    """Identity-aware evaluator. Resolves identity before classifying (A–E taxonomy);
    aggregate counts / regex matches are not an evaluator."""

    def evaluate(self, target: GovProjection | str, *, stage: str | None = None) -> Verdict: ...

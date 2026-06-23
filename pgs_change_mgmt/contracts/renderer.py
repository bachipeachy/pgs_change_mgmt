"""Renderer seam — structured contract → machine artifact, one implementation per kind.

(change_agent_future.md Plugin #4.) The worker emits a structured contract object; a
Renderer deterministically expands it to the machine block. The worker never emits machine
syntax directly.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable


@runtime_checkable
class Renderer(Protocol):
    """Structured contract → machine artifact, one implementation per artifact kind. The
    worker emits a structured contract object; a Renderer deterministically expands it to
    the machine block. The worker never emits machine syntax directly."""

    kind: str  # CC | IN | WF | RB | CT | CS | STRUCTURE

    def render(self, contract: Mapping[str, Any]) -> str: ...

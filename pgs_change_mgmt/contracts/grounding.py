"""Grounding seam — the external evidence authority a stage queries.

(change_agent_future.md Plugin #2.) Today the provider is PI over the compiled snapshot.
A stage asks `query(op, ...)` and receives evidence; it does not care whether the provider
is PI, a document store, a repository, a protocol snapshot, or a human SME.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable


@runtime_checkable
class GroundingProvider(Protocol):
    """External grounding authority (today: PI over the compiled snapshot). A stage asks
    `query(op, ...)` and receives evidence; it does not care whether the provider is PI, a
    document store, a repository, a protocol snapshot, or a human SME."""

    def query(self, op: str, /, **kwargs: Any) -> Mapping[str, Any]: ...

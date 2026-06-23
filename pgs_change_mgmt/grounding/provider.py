"""PiGroundingProvider — PI over the compiled snapshot, conforming to the grounding seam.

This is the single concrete `contracts.GroundingProvider` today. It adapts the read-only
``pi`` query surface (`pi_tools`) to the seam's uniform `query(op, ...)` interface: `op` is a
tool name and the keyword arguments are that tool's parameters.

A stage asks for evidence by *operation name* and receives ``pi``'s stable JSON envelope; it
never learns whether the authority behind the seam is PI, a document store, or a human SME.
Swapping in a second provider is an addition (a new `GroundingProvider`), never a refactor.
"""

from __future__ import annotations

from typing import Any, Mapping

from .pi_tools import PiClient, TOOL_NAMES, dispatch


class PiGroundingProvider:
    """`contracts.GroundingProvider` backed by read-only Protocol Inspection.

    `op` must be one of `available_ops()` (the wrapped `pi` queries); keyword arguments are
    forwarded to the matching query. The returned mapping is `pi`'s verbatim JSON envelope
    (`query` / `result` / `schema_version`).
    """

    #: The operations this provider answers — the wrapped, read-only `pi` queries.
    ops: tuple[str, ...] = TOOL_NAMES

    def __init__(self, client: PiClient | None = None, **client_kwargs: Any) -> None:
        # The PiClient stays accessible (`.client`) for callers that need the
        # verification oracle (`is_indexed`), which is deliberately not a query op.
        self.client = client or PiClient(**client_kwargs)

    def query(self, op: str, /, **kwargs: Any) -> Mapping[str, Any]:
        """Ask the grounding authority for evidence by operation name."""
        if op not in TOOL_NAMES:
            raise KeyError(
                f"unknown grounding op: {op!r} (available: {', '.join(TOOL_NAMES)})"
            )
        return dispatch(self.client, op, kwargs)

    def available_ops(self) -> tuple[str, ...]:
        return TOOL_NAMES

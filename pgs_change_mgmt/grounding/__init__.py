"""grounding — the external grounding authority (PI over the compiled snapshot, today).

A stage asks `query(op, ...)` and receives evidence; it does not care whether the provider
is PI, a document store, a repository, or a human SME. `PiGroundingProvider` is the single
concrete `contracts.GroundingProvider` today.

The lower-level `pi_tools` surface (PiClient + model-facing tool schemas) is re-exported for
callers that drive `pi` directly — the (soon-to-be-`legacy/`) experiment harnesses, and the
evaluator's `is_indexed` verification oracle.
"""

from .provider import PiGroundingProvider
from .cache import CachingGroundingProvider
from .pi_tools import (
    PiClient,
    PiError,
    TOOL_SCHEMAS,
    TOOL_NAMES,
    dispatch,
)

__all__ = [
    "PiGroundingProvider",
    "CachingGroundingProvider",
    "PiClient",
    "PiError",
    "TOOL_SCHEMAS",
    "TOOL_NAMES",
    "dispatch",
]

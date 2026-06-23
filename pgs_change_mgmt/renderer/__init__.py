"""renderer — structured contract → machine artifact, one renderer per artifact kind.

The worker emits a structured contract object; a renderer deterministically expands it to the
machine block (CC | IN | WF | RB | CT | CS | STRUCTURE). The worker never emits machine
syntax. Renderers are dispatched by `kind` through the `registry`. The CR-authoring kinds
(CC, IN, WF, RB) are implemented; CT/CS (capability primitives) and STRUCTURE (storage
topology) are declared addition points (`KINDS`), authored rarely.

`ContractError` is re-exported for callers that validate/shape contract objects.
"""

from .cc import CCRenderer
from .intent import INRenderer
from .runtime_binding import RBRenderer
from .workflow import WFRenderer
from .base import ContractError
from .registry import KINDS, RENDERERS, get_renderer, render

__all__ = [
    "CCRenderer",
    "INRenderer",
    "RBRenderer",
    "WFRenderer",
    "ContractError",
    "KINDS",
    "RENDERERS",
    "get_renderer",
    "render",
]

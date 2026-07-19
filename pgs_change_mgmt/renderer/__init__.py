"""renderer — structured contract → machine artifact, one renderer per artifact kind.

The worker emits a structured contract object; a renderer deterministically expands it to the
machine block (CC | IN | WF | RB | CT | CS | STRUCTURE | EV). The worker never emits machine
syntax. Renderers are dispatched by `kind` through the `registry`. All seven construction
families are implemented (CC, IN, WF, RB, CT, STRUCTURE, EV); only CS (capability side effect)
remains a declared addition point (`KINDS`), authored rarely.

`ContractError` is re-exported for callers that validate/shape contract objects.
"""

from .cc import CCRenderer
from .intent import INRenderer
from .runtime_binding import RBRenderer
from .workflow import WFRenderer
from .transform import CTRenderer
from .structure import StructureRenderer
from .event import EVRenderer
from .base import ContractError
from .registry import KINDS, RENDERERS, get_renderer, render

__all__ = [
    "CCRenderer",
    "INRenderer",
    "RBRenderer",
    "WFRenderer",
    "CTRenderer",
    "StructureRenderer",
    "EVRenderer",
    "ContractError",
    "KINDS",
    "RENDERERS",
    "get_renderer",
    "render",
]

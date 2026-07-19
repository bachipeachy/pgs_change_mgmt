"""Renderer registry — one `contracts.Renderer` per artifact kind, dispatched by `kind`.

The seam is *per kind* by design (`Renderer.kind` ∈ CC | IN | WF | RB | CT | CS | STRUCTURE | EV):
each kind has its own deterministic structured-contract → machine-artifact expansion. Adding
a kind is registering a new conforming `Renderer` here — an addition, never a refactor.

Every family the Construction Compiler renders is registered here: CC, IN, WF, RB (CR-authoring
kinds), CT (capability transform), STRUCTURE (storage topology), and EV (event). Together these
seven cover the full construction delta (e.g. the 16-artifact blockchain/chain CR). Only CS
(capability side effect) remains *declared* (`KINDS`) but unregistered — no CR has yet needed a
newly-authored CS. `get_renderer` for a declared-but-unimplemented kind fails loudly rather than
silently rendering the wrong shape; we never fabricate a renderer ahead of a proven contract
object, which would fossilize unproven syntax.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..contracts import Renderer
from .cc import CCRenderer
from .intent import INRenderer
from .runtime_binding import RBRenderer
from .workflow import WFRenderer
from .transform import CTRenderer
from .structure import StructureRenderer
from .event import EVRenderer

# All artifact kinds the seam will eventually cover (mirrors contracts.Renderer.kind).
KINDS: tuple[str, ...] = ("CC", "IN", "WF", "RB", "CT", "CS", "STRUCTURE", "EV")

# Concrete renderers available today. A new kind is added here, not by changing callers.
# CC/IN/WF/RB are the CR-authoring kinds; CT (capability transform), STRUCTURE (storage
# topology), and EV (event) complete the construction delta. CS (capability side effect)
# remains declared-but-unimplemented until a CR authors a new one.
RENDERERS: dict[str, Renderer] = {
    r.kind: r for r in (
        CCRenderer(), INRenderer(), RBRenderer(), WFRenderer(),
        CTRenderer(), StructureRenderer(), EVRenderer(),
    )
}


def get_renderer(kind: str) -> Renderer:
    """Return the renderer for `kind`, or fail loudly if it is declared-but-unimplemented."""
    if kind in RENDERERS:
        return RENDERERS[kind]
    if kind in KINDS:
        raise NotImplementedError(
            f"renderer for kind {kind!r} is declared but not yet implemented "
            f"(implemented: {sorted(RENDERERS)})"
        )
    raise KeyError(f"unknown artifact kind: {kind!r} (valid kinds: {list(KINDS)})")


def render(kind: str, contract: Mapping[str, Any]) -> str:
    """Dispatch to the renderer for `kind` and expand the structured contract."""
    return get_renderer(kind).render(dict(contract))

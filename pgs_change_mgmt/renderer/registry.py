"""Renderer registry — one `contracts.Renderer` per artifact kind, dispatched by `kind`.

The seam is *per kind* by design (`Renderer.kind` ∈ CC | IN | WF | RB | CT | CS | STRUCTURE):
each kind has its own deterministic structured-contract → machine-artifact expansion. Adding
a kind is registering a new conforming `Renderer` here — an addition, never a refactor.

Today exactly one kind is implemented (CC, the proven Phase-0 renderer). The other kinds are
*declared* (`KINDS`) but unregistered: `get_renderer` for an unimplemented kind fails loudly
rather than silently rendering the wrong shape. We do not fabricate the six remaining
renderers ahead of a proven contract object for each — that would fossilize unproven syntax.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..contracts import Renderer
from .cc import CCRenderer
from .intent import INRenderer
from .runtime_binding import RBRenderer
from .workflow import WFRenderer

# All artifact kinds the seam will eventually cover (mirrors contracts.Renderer.kind).
KINDS: tuple[str, ...] = ("CC", "IN", "WF", "RB", "CT", "CS", "STRUCTURE")

# Concrete renderers available today. A new kind is added here, not by changing callers.
# CC/IN/WF/RB are the CR-authoring kinds; CT/CS (capability primitives) and STRUCTURE
# (storage topology) are authored rarely and remain declared-but-unimplemented for now.
RENDERERS: dict[str, Renderer] = {
    r.kind: r for r in (CCRenderer(), INRenderer(), RBRenderer(), WFRenderer())
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

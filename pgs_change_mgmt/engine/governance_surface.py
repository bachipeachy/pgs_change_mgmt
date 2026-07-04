"""Candidate governance-surface overlays — declaring a construction's new CTs *legal* inside the
Compilation Unit, never in the canonical registry.

When the Construction Compiler emits a new capability transform, that CT does not yet appear in the
governed `allowed_capability_transforms` surface (`INVARIANT_CT_SURFACE_CLOSED`). Admitting it is a
*governance* act — analogous to declaring a new opcode legal in an ISA spec — and it travels with the
candidate set as a **candidate governance artifact**, overlaid onto a read-only copy of the surface's
owning repo. Only Promotion writes the canonical surface.

This module is the governance-aware seam of the admission layer. The **Construction Compiler stays
unaware of it** — the front-end never learns which CTs a surface admits; it only produces contracts.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

# FQDN namespace → the governed CT-surface that must admit it. The surface may live in a *different*
# repo than the CT itself: reusable transforms (`capability_transforms::`) are admitted by the
# PLATFORM surface in `pgs_governance`, not by their own package. Declarative governance routing.
_SURFACE: dict[str, dict[str, str]] = {
    "blockchain": {
        "layer": "BLOCKCHAIN",
        "rel": "registry/assertions/ASSERT_CT_SURFACE_CLOSED_BLOCKCHAIN_V0.md",
    },
    "capability_transforms": {
        "layer": "GOVERNANCE",
        "rel": "registry/FB_TOPOLOGY/assertions/ASSERT_CT_SURFACE_CLOSED_V0.md",
    },
}

_LIST_KEY = "allowed_capability_transforms:"


@dataclass(frozen=True)
class SurfaceOverlay:
    package_dir: Path        # the importable package to mount (copytree) — e.g. …/pgs_governance
    rel: str                 # surface path relative to package_dir
    entries: tuple[str, ...] # candidate CT FQDNs to ensure declared


def is_ct(fqdn: str) -> bool:
    return fqdn.split("::", 1)[-1].startswith("CT_")


def surface_overlays(ct_fqdns: list[str]) -> list[SurfaceOverlay]:
    """Group candidate CTs by their governing surface and resolve that surface's owning package.
    Namespaces with no governed CT-surface are skipped (never guessed)."""
    from .ownership import _layer_resolver
    groups: dict[str, list[str]] = defaultdict(list)
    for fqdn in ct_fqdns:
        ns = fqdn.split("::", 1)[0]
        if ns in _SURFACE:
            groups[ns].append(fqdn)
    out: list[SurfaceOverlay] = []
    for ns, fqdns in groups.items():
        spec = _SURFACE[ns]
        pkg_dir = _layer_resolver().resolve_layer_repo_root(spec["layer"])
        out.append(SurfaceOverlay(pkg_dir, spec["rel"], tuple(sorted(set(fqdns)))))
    return out


def compose(current: str, entries: tuple[str, ...] | list[str]) -> str:
    """Return `current` with each FQDN in `entries` present in the `allowed_capability_transforms:`
    list. Idempotent (already-declared entries are left alone); preserves the block's indentation.
    Operates on the passed text only — the caller applies the result to the overlay copy, never to
    the canonical source."""
    lines = current.splitlines()
    key_ix = next((i for i, ln in enumerate(lines) if ln.strip() == _LIST_KEY), None)
    if key_ix is None:
        raise ValueError(f"surface has no {_LIST_KEY!r} block")
    # the contiguous run of list items directly under the key
    end = key_ix + 1
    indent = None
    while end < len(lines) and lines[end].lstrip().startswith("- "):
        if indent is None:
            indent = lines[end][: len(lines[end]) - len(lines[end].lstrip())]
        end += 1
    indent = indent or "  "
    present = {ln.strip().lstrip("- ").strip() for ln in lines[key_ix + 1 : end]}
    additions = [f"{indent}- {e}" for e in entries if e not in present]
    if not additions:
        return current
    return "\n".join(lines[:end] + additions + lines[end:]) + ("\n" if current.endswith("\n") else "")

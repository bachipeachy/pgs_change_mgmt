"""Artifact Ownership Service — *"where does this artifact belong?"*, resolved through **governance**.

The Compilation Unit asks `ownership.resolve(fqdn)` and never learns *how* ownership is determined. The
implementation uses the FQDN namespace → governed layer → `LayerResolver.resolve_layer_repo_root` today;
tomorrow it may consult a federation manifest or registry metadata — invisible above this seam, so the
ownership algorithm is replaceable without touching the compiler or the Compilation Unit.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

# FQDN namespace → governed layer. The single named place for the namespace→layer convention (mirrors
# governance's `path_registry`). Replace with a governed federation manifest when one exists.
_NAMESPACE_LAYER: dict[str, str] = {
    "blockchain": "BLOCKCHAIN",
    "capability_transforms": "REUSABLE_TRANSFORMS",
    "capability_side_effects": "REUSABLE_SIDE_EFFECTS",
    "ai_governance": "AI_GOVERNANCE",
}


@dataclass(frozen=True)
class Owner:
    namespace: str            # the FQDN namespace (blockchain, capability_transforms, …)
    layer: str                # the governed layer (BLOCKCHAIN, REUSABLE_TRANSFORMS, …)
    repo_root: Path           # mount root — the dir containing the importable package (on PYTHONPATH)
    package: str              # the importable package name (pgs_blockchain, pgs_transforms, …)

    @property
    def registry_root(self) -> Path:
        return self.repo_root / self.package / "registry"


@lru_cache(maxsize=1)
def _layer_resolver():
    from pgs_governance.implementation.structure.resolution.layer_resolver import LayerResolver
    return LayerResolver()


def resolve(fqdn: str) -> Owner:
    """Governed owner of an FQDN. Raises if the namespace has no governed layer (never guesses)."""
    ns = fqdn.split("::", 1)[0]
    layer = _NAMESPACE_LAYER.get(ns)
    if not layer:
        raise KeyError(f"no governed owner for namespace {ns!r} (fqdn {fqdn})")
    pkg_dir = _layer_resolver().resolve_layer_repo_root(layer)     # e.g. …/pgs_blockchain/pgs_blockchain
    return Owner(namespace=ns, layer=layer, repo_root=pkg_dir.parent, package=pkg_dir.name)

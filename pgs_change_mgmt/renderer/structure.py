"""StructureRenderer — structured contract object → admissible storage-topology (STRUCTURE) Markdown.

Grounded in the real authoring schema (e.g. STRUCTURE_BLOCKCHAIN_STORAGE_V0): a STRUCTURE declares a
subdomain's storage topology — one entity store per domain entity type, each mapping a store name to a
relative path under the runtime `{{module_data_root}}`. Storage paths are a governance concern, so a
STRUCTURE names *store → path*; it never encodes a filesystem layout in runtime code.

This is a **template renderer** (per the Construction renderer taxonomy: template / projection / semantic).
The only CR-specific inputs are the store names, storage types, and paths — carried upstream by the
`structure_stores` register. Everything else (the storage-root convention, the resolution / isolation /
migration doctrine) is a deterministic constant owned *here*, not upstream design data. Adding a store is
a CR-IR change; the doctrine boilerplate never is.
"""

from __future__ import annotations

from typing import Any

from .base import ContractError, governed_by, header, machine_block, machine_section, section, assemble

# storage_type → a deterministic human phrase (derivation, not upstream design). The storage type is
# appended verbatim so the CS binding is legible in the store description.
_STORE_DESC: dict[str, str] = {
    "CS_APPENDONLY_JSONL_V0": "Append-only JSONL store",
    "CS_MUTABLE_JSON_V0": "Mutable JSON store",
}


def _describe(storage_type: str) -> str:
    base = _STORE_DESC.get(storage_type, "Entity store")
    return f"{base} ({storage_type})" if storage_type else base


def _relpath(path: str) -> str:
    """Strip the templated storage-root prefix — the STRUCTURE `entity_stores` path is relative to
    `storage_roots.base_path` ({{module_data_root}}), never absolute."""
    p = (path or "").strip()
    for pref in ("{{module_data_root}}/", "{module_data_root}/"):
        if p.startswith(pref):
            return p[len(pref):]
    return p


def _validate(obj: dict[str, Any]) -> None:
    if not obj.get("summary"):
        raise ContractError("STRUCTURE contract missing required field: summary")
    if not obj.get("stores"):
        raise ContractError("STRUCTURE contract missing required field: stores")
    for s in obj["stores"]:
        if not s.get("name"):
            raise ContractError("STRUCTURE store missing 'name'")
        if not s.get("path"):
            raise ContractError(f"STRUCTURE store {s.get('name')!r} missing 'path'")


def _machine(code: str, obj: dict[str, Any]) -> str:
    domain = obj.get("domain") or ""
    subdomain = obj.get("subdomain") or domain
    entity_stores = {
        s["name"]: {"description": _describe(s.get("storage_type", "")), "path": _relpath(s["path"])}
        for s in obj["stores"]
    }
    first_path = next(iter(entity_stores.values()))["path"]
    core = {
        "summary": obj["summary"],
        "description": f"Maps {subdomain} entity stores to storage implementations and paths",
        "layer": "DOMAINS",
        "domain": domain,
        "storage_roots": {
            "base_path": "{{module_data_root}}",
            "description": f"Root path for all {domain} domain storage (resolved at runtime)",
        },
        "entity_stores": entity_stores,
        # --- doctrine boilerplate (renderer-owned constants; never CR-IR design data) ---
        "resolution": {
            "description": "Runtime path resolution strategy",
            "algorithm": "base_path / entity_stores[entity_type].path",
            "example": "{{module_data_root}}/" + first_path,
        },
        "isolation": {
            "description": "Entity storage isolation constraints",
            "rules": [
                "Each entity type has dedicated storage",
                "Cross-entity queries forbidden (no joins)",
                "Entity reads must specify entity type explicitly",
                "Storage paths resolved via STRUCTURE only",
            ],
        },
        "migration": {
            "description": "Storage migration policy",
            "rules": [
                "Path changes are STRUCTURE updates (versioned)",
                "CC artifacts remain unchanged during migration",
                "Runtime resolves paths from active STRUCTURE version",
            ],
        },
    }
    doc = {"structure_code": code, "version": "v0", "governed_by": governed_by("STRUCTURE"), "core": core}
    return machine_block(doc)


class StructureRenderer:
    """`contracts.Renderer` for storage topology (kind="STRUCTURE")."""

    kind = "STRUCTURE"

    def render(self, contract: dict[str, Any]) -> str:
        obj = dict(contract)
        code = obj.pop("code", None) or obj.pop("structure_code", None)
        if not code:
            raise ContractError("STRUCTURE contract is missing 'code'")
        _validate(obj)
        # STRUCTURE header omits the Dependencies line (stores are declared in the machine block).
        parts = header(code, "STRUCTURE", include_deps=False)
        model = "\n".join(
            f"- **{s['name']}** — {_describe(s.get('storage_type', ''))} → `{_relpath(s['path'])}`"
            for s in obj["stores"])
        parts += section("1. Storage Model", model)
        parts += machine_section(_machine(code, obj))
        return assemble(parts)

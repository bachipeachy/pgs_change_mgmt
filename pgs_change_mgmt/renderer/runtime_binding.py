"""RBRenderer — structured contract object → admissible runtime-binding (RB) Markdown.

Grounded in the real authoring schema (e.g. RB_MINT_V0): an RB maps capability side-effect
FQDNs to concrete runtime policies and names the storage structure. An RB carries no prose
sections and no Dependencies header line — it is a pure binding document.
"""

from __future__ import annotations

from typing import Any

from .base import ContractError, governed_by, header, machine_block, machine_section, assemble


def _validate(obj: dict[str, Any]) -> None:
    if not obj.get("summary"):
        raise ContractError("RB contract missing required field: summary")
    bindings = obj.get("bindings")
    if not bindings:
        raise ContractError("RB contract missing required field: bindings")
    for b in bindings:
        if not b.get("capability"):
            raise ContractError("RB binding missing 'capability' FQDN")


def _machine(code: str, obj: dict[str, Any]) -> str:
    core: dict[str, Any] = {"summary": obj["summary"]}
    if obj.get("description"):
        core["description"] = obj["description"]
    if obj.get("storage_structure"):
        core["storage_structure"] = obj["storage_structure"]
    core["bindings"] = {
        b["capability"]: {"policy": b.get("policy", {}) or {}}
        for b in obj.get("bindings", [])
    }
    doc = {"rb_code": code, "version": "v0", "governed_by": governed_by("RB"), "core": core}
    return machine_block(doc)


class RBRenderer:
    """`contracts.Renderer` for runtime bindings (kind="RB")."""

    kind = "RB"

    def render(self, contract: dict[str, Any]) -> str:
        obj = dict(contract)
        code = obj.pop("code", None) or obj.pop("rb_code", None)
        if not code:
            raise ContractError("RB contract is missing 'code'")
        _validate(obj)
        # RB header omits the Dependencies line (bindings are declared in the machine block).
        parts = header(code, "RB", include_deps=False)
        parts += machine_section(_machine(code, obj))
        return assemble(parts)

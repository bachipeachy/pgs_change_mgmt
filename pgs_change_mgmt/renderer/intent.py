"""INRenderer — structured contract object → admissible intent (IN) Markdown.

Grounded in the real authoring schema (e.g. IN_MINT_V0): an intent is a declarative admission
gate that binds to one workflow, declares its inputs, and enumerates ACK/NACK outcomes.
"""

from __future__ import annotations

from typing import Any

from .base import (
    ContractError, governed_by, header, machine_block, machine_section, section, assemble,
)


def _validate(obj: dict[str, Any]) -> None:
    for k in ("summary", "workflow", "inputs", "outcomes"):
        if not obj.get(k):
            raise ContractError(f"IN contract missing required field: {k}")


def _inputs_map(obj: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for f in obj.get("inputs", []) or []:
        spec = {"type": f["type"], "required": bool(f.get("required", False))}
        if f.get("description"):
            spec["description"] = f["description"]
        out[f["name"]] = spec
    return out


def _outcomes_map(obj: dict[str, Any]) -> dict[str, Any]:
    return {o["name"]: {"description": o.get("description", "")} for o in obj.get("outcomes", []) or []}


def _machine(code: str, obj: dict[str, Any]) -> str:
    core = {"summary": obj["summary"], "workflow": obj["workflow"],
            "inputs": _inputs_map(obj), "outcomes": _outcomes_map(obj)}
    ext = obj.get("extensions") or {}
    if obj.get("domain"):
        ext.setdefault("domain", obj["domain"])
    if obj.get("authority"):
        ext.setdefault("authority", obj["authority"])
    doc = {"in_code": code, "version": "v0", "governed_by": governed_by("IN"), "core": core}
    if ext:
        doc["extensions"] = ext
    return machine_block(doc)


class INRenderer:
    """`contracts.Renderer` for intents (kind="IN")."""

    kind = "IN"

    def render(self, contract: dict[str, Any]) -> str:
        obj = dict(contract)
        code = obj.pop("code", None) or obj.pop("in_code", None)
        if not code:
            raise ContractError("IN contract is missing 'code'")
        _validate(obj)

        def _tbl_inputs() -> str:
            rows = ["| Field | Type | Required | Description |", "|---|---|---|---|"]
            for f in obj.get("inputs", []) or []:
                rows.append(f"| {f['name']} | {f['type']} | {str(bool(f.get('required'))).lower()} | {f.get('description','')} |")
            return "\n".join(rows)

        def _tbl_outcomes() -> str:
            rows = ["| Outcome | Description |", "|---|---|"]
            for o in obj.get("outcomes", []) or []:
                rows.append(f"| {o['name']} | {o.get('description','')} |")
            return "\n".join(rows)

        parts = header(code, "IN", deps=[obj["workflow"]])
        parts += section("1. Intent", obj.get("intent", obj["summary"]))
        parts += section("2. Rationale", obj.get("rationale", ""))
        parts += section("3. Workflow Binding",
                         f"| Target | Description |\n|---|---|\n| {obj['workflow']} | Workflow that processes this intent |")
        parts += section("4. Inputs", _tbl_inputs())
        parts += section("5. Outcomes", _tbl_outcomes())
        if obj.get("domain") or obj.get("authority"):
            dom = [f"- **Domain:** {obj.get('domain','')}", f"- **Authority:** {obj.get('authority','')}"]
            parts += section("6. Domain", "\n".join(dom))
        parts += machine_section(_machine(code, obj))
        return assemble(parts)

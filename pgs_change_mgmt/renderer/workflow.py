"""WFRenderer — structured contract object → admissible workflow (WF) Markdown.

Grounded in the real authoring schema (e.g. WF_MINT_V0): a workflow is a governed DAG of
nodes (IN entry, CC steps, EXIT terminals) with outcome-based routing (`next: {OUTCOME:
target}`). Routing is outcome-based only — no conditional/expression edges.

The contract object the worker emits:
    {code, summary, intent, rationale, runtime_binding, subdomain,
     admission: {requires: [], forbids: []},
     start_node: "IN_X_V0",
     nodes: [ {node, type("IN"|"CC"|"EXIT"), code, inputs{}, next{OUTCOME: target}, reason} ],
     dependencies: [...]}   # optional; derived from IN/CC node codes if absent
"""

from __future__ import annotations

from typing import Any

from .base import (
    ContractError, governed_by, header, machine_block, machine_section, section, assemble,
)


def _node_names(obj: dict[str, Any]) -> list[str]:
    return [n["node"] for n in obj.get("nodes", [])]


def _validate(obj: dict[str, Any]) -> None:
    for k in ("summary", "runtime_binding", "start_node", "nodes"):
        if not obj.get(k):
            raise ContractError(f"WF contract missing required field: {k}")
    names = set(_node_names(obj))
    if obj["start_node"] not in names:
        raise ContractError(f"WF start_node {obj['start_node']!r} is not among nodes")
    for n in obj["nodes"]:
        t = n.get("type")
        if t not in ("IN", "CC", "EXIT"):
            raise ContractError(f"node {n.get('node')!r}: type must be IN, CC, or EXIT")
        if t == "EXIT":
            if not n.get("reason"):
                raise ContractError(f"EXIT node {n.get('node')!r}: missing reason")
            continue
        if not n.get("code"):
            raise ContractError(f"{t} node {n.get('node')!r}: missing code")
        nxt = n.get("next") or {}
        if not nxt:
            raise ContractError(f"{t} node {n.get('node')!r}: missing next routing")
        for outcome, target in nxt.items():
            if target not in names:
                raise ContractError(
                    f"node {n.get('node')!r}: next {outcome} → {target!r} is not a known node")


def _derive_deps(obj: dict[str, Any]) -> list[str]:
    seen: list[str] = []
    for n in obj["nodes"]:
        if n.get("type") in ("IN", "CC") and n.get("code") and n["code"] not in seen:
            seen.append(n["code"])
    return seen


def _nodes_machine(obj: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for n in obj["nodes"]:
        if n["type"] == "EXIT":
            out[n["node"]] = {"type": "EXIT", "reason": n["reason"]}
            continue
        d: dict[str, Any] = {"type": n["type"], "code": n["code"]}
        if n.get("inputs"):
            d["inputs"] = n["inputs"]
        d["next"] = n["next"]
        out[n["node"]] = d
    return out


def _machine(code: str, obj: dict[str, Any]) -> str:
    adm = obj.get("admission") or {}
    core = {
        "runtime_binding": obj["runtime_binding"],
        "summary": obj["summary"],
        "admission": {"requires": adm.get("requires", []) or [], "forbids": adm.get("forbids", []) or []},
        "start_node": obj["start_node"],
        "nodes": _nodes_machine(obj),
    }
    doc: dict[str, Any] = {
        "wf_code": code, "version": "v0", "governed_by": governed_by("WF"),
        "runtime_binding": obj["runtime_binding"],
    }
    if obj.get("subdomain"):
        doc["subdomain"] = obj["subdomain"]
    doc["core"] = core
    return machine_block(doc)


class WFRenderer:
    """`contracts.Renderer` for workflows (kind="WF")."""

    kind = "WF"

    def render(self, contract: dict[str, Any]) -> str:
        obj = dict(contract)
        code = obj.pop("code", None) or obj.pop("wf_code", None)
        if not code:
            raise ContractError("WF contract is missing 'code'")
        _validate(obj)
        deps = obj.get("dependencies") or _derive_deps(obj)

        def _graph() -> str:
            lines = [f"start: {obj['start_node']}", ""]
            for n in obj["nodes"]:
                if n["type"] == "EXIT":
                    lines.append(f"{n['node']} [EXIT] reason={n['reason']}")
                else:
                    routes = ", ".join(f"{o} → {t}" for o, t in n["next"].items())
                    lines.append(f"{n['node']} [{n['type']}] {routes}")
            return "```\n" + "\n".join(lines) + "\n```"

        def _tbl_nodes() -> str:
            rows = ["| Node | Type | Code/Reason |", "|---|---|---|"]
            for n in obj["nodes"]:
                rows.append(f"| {n['node']} | {n['type']} | {n.get('code') or n.get('reason','')} |")
            return "\n".join(rows)

        adm = obj.get("admission") or {}
        adm_body = (f"- **Requires:** {adm.get('requires') or 'NONE'}\n"
                    f"- **Forbids:** {adm.get('forbids') or 'NONE'}")

        parts = header(code, "WF", deps=deps)
        parts += section("1. Intent", obj.get("intent", obj["summary"]))
        parts += section("2. Rationale", obj.get("rationale", ""))
        parts += section("3. Execution Graph", _graph())
        parts += section("4. Nodes", _tbl_nodes())
        parts += section("5. Admission", adm_body)
        parts += machine_section(_machine(code, obj))
        return assemble(parts)

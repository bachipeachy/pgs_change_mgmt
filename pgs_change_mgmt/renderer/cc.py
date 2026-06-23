"""Deterministic CC artifact renderer — structured contract object → admissible Markdown.

Option (B): the LLM emits a *structured contract object* (JSON) capturing the semantic
decisions; this renderer owns the syntax. It eliminates the three serialization defect
classes by construction:

  * unquoted-colon YAML errors   → `yaml.safe_dump` always quotes correctly
  * dropped `result_surface` outcome → result_surface is DERIVED from `on_result` keys
  * invented `if:` routing        → the schema has no `if`; routing is `on_result: {OUTCOME: target}`

The LLM provides reasoning (steps, ops, JSONPaths, routing, prose); the renderer provides
serialization, derivation, and prose↔machine consistency. This cleanly separates a
*representation* failure (which this fixes) from a *reasoning* failure (which would remain
as semantically-wrong steps/routing — the real model signal).

Contract object schema (what the LLM emits):
{
  "summary": str,
  "intent": str, "rationale": str,
  "inputs":  [{"name","type","required"(bool),"description"(opt)}],
  "outputs": [{"name","type","items_type"(opt, for arrays)}],
  "pipeline": [{
      "step": str, "kind": "CT"|"CS",
      "capability": "capability_transforms::CT_..."|"capability_side_effects::CS_...",
      "store": str (CS only), "op": str,
      "inputs": {<jsonpath/literal map>}, "outputs": {<map>},
      "on_result": {"SUCCESS":"continue|exit|<step>", ...}     # result_surface DERIVED from keys
  }],
  "error_codes": {OUTCOME: CODE} (opt),
  "extensions": {"subdomain": str, "notes": [str]}
}
"""

from __future__ import annotations

import yaml
from typing import Any

from .base import ContractError  # unified contract-shape error across all kind renderers

GOVERNED_BY = "fb.topology::CONSTITUTION_CAPABILITY_CONTRACT_V0"
# Canonical outcome ordering for derived result_surface / allowed.
CANON = ["SUCCESS", "ALREADY_EXISTS", "NOT_FOUND", "VIOLATION", "BACKEND_ERROR"]


def _ordered(outcomes) -> list[str]:
    s = list(dict.fromkeys(outcomes))
    return [o for o in CANON if o in s] + [o for o in s if o not in CANON]


def _validate(obj: dict[str, Any]) -> None:
    if not isinstance(obj, dict):
        raise ContractError("contract object is not a JSON object")
    for k in ("summary", "pipeline"):
        if not obj.get(k):
            raise ContractError(f"missing required field: {k}")
    step_names = {s.get("step") for s in obj["pipeline"]}
    for st in obj["pipeline"]:
        if st.get("kind") not in ("CT", "CS"):
            raise ContractError(f"step {st.get('step')!r}: kind must be CT or CS")
        if not st.get("capability"):
            raise ContractError(f"step {st.get('step')!r}: missing capability FQDN")
        if st["kind"] == "CS" and not st.get("store"):
            raise ContractError(f"CS step {st.get('step')!r}: missing store")
        on = st.get("on_result") or {}
        if not on:
            raise ContractError(f"step {st.get('step')!r}: missing on_result routing")
        for outcome, target in on.items():
            if target not in ("continue", "exit") and target not in step_names:
                raise ContractError(
                    f"step {st.get('step')!r}: on_result {outcome} → {target!r} is not "
                    f"'continue', 'exit', or a known step")


def _core(obj: dict[str, Any]) -> dict[str, Any]:
    core: dict[str, Any] = {"summary": obj["summary"]}
    # inputs (list → map)
    inputs = {}
    for f in obj.get("inputs", []) or []:
        spec = {"type": f["type"], "required": bool(f.get("required", False))}
        if f.get("description"):
            spec["description"] = f["description"]
        inputs[f["name"]] = spec
    core["inputs"] = inputs
    # outputs (list → map)
    outputs = {}
    for f in obj.get("outputs", []) or []:
        spec: dict[str, Any] = {"type": f["type"]}
        if f["type"] == "array" and f.get("items_type"):
            spec["items"] = {"type": f["items_type"]}
        outputs[f["name"]] = spec
    core["outputs"] = outputs
    # result_status_contract — allowed DERIVED from union of all on_result outcomes
    all_outcomes: list[str] = []
    for st in obj["pipeline"]:
        all_outcomes.extend((st.get("on_result") or {}).keys())
    core["result_status_contract"] = {
        "allowed": _ordered(all_outcomes),
        "on_input_failure": "VIOLATION",
    }
    # pipeline — result_surface DERIVED per step from its on_result keys
    steps = []
    for st in obj["pipeline"]:
        d: dict[str, Any] = {"step": st["step"]}
        if st["kind"] == "CT":
            d["transform"] = st["capability"]
        else:
            d["side_effect"] = st["capability"]
            d["store"] = st["store"]
        d["op"] = st["op"]
        d["inputs"] = st.get("inputs", {}) or {}
        d["outputs"] = st.get("outputs", {}) or {}
        d["result_surface"] = _ordered((st.get("on_result") or {}).keys())
        d["on_result"] = st["on_result"]
        steps.append(d)
    core["pipeline"] = steps
    if obj.get("error_codes"):
        core["error_codes"] = obj["error_codes"]
    return core


def _machine_yaml(code: str, obj: dict[str, Any]) -> str:
    doc = {
        "cc_code": code,
        "version": "v0",
        "governed_by": GOVERNED_BY,
        "core": _core(obj),
        "extensions": obj.get("extensions", {"subdomain": "", "notes": []}),
    }
    # safe_dump guarantees valid YAML: correct quoting of colons, '{{timestamp}}', etc.
    return yaml.safe_dump(doc, sort_keys=False, default_flow_style=False, width=100)


def _deps(obj: dict[str, Any]) -> list[str]:
    seen = []
    for st in obj["pipeline"]:
        code = st["capability"].split("::")[-1]
        if code not in seen:
            seen.append(code)
    return seen


def render(code: str, obj: dict[str, Any]) -> str:
    """Render a structured contract object into an admissible CC artifact Markdown."""
    _validate(obj)
    deps = ", ".join(_deps(obj)) or "NONE"
    allowed = _core(obj)["result_status_contract"]["allowed"]

    def _tbl_inputs() -> str:
        rows = ["| Field | Type | Required | Description |", "|---|---|---|---|"]
        for f in obj.get("inputs", []) or []:
            rows.append(f"| {f['name']} | {f['type']} | {str(bool(f.get('required'))).lower()} | {f.get('description','')} |")
        return "\n".join(rows) if len(rows) > 2 else "(none)"

    def _tbl_pipeline() -> str:
        rows = ["| Step | Capability | Type | Operation |", "|---|---|---|---|"]
        for st in obj["pipeline"]:
            rows.append(f"| {st['step']} | {st['capability'].split('::')[-1]} | {st['kind']} | {st['op']} |")
        return "\n".join(rows)

    parts = [
        f"# {code}",
        "",
        "## Header (Mandatory)",
        "",
        f"- **Artifact Code:** {code}",
        "- **Artifact Kind:** capability_contract",
        f"- **Governed By:** CONSTITUTION_CAPABILITY_CONTRACT_V0",
        "- **Version:** v0",
        "- **Status:** canonical",
        "- **Supersedes:** NONE",
        f"- **Dependencies:** {deps}",
        "",
        "---",
        "",
        "## 1. Intent",
        "",
        obj.get("intent", obj["summary"]),
        "",
        "---",
        "",
        "## 2. Rationale",
        "",
        obj.get("rationale", ""),
        "",
        "---",
        "",
        "## 3. Pipeline",
        "",
        _tbl_pipeline(),
        "",
        "---",
        "",
        "## 4. Inputs",
        "",
        _tbl_inputs(),
        "",
        "---",
        "",
        "## 5. Result Status Contract",
        "",
        f"Allowed outcomes: {', '.join(allowed)}",
        "",
        "---",
        "",
        "## Machine",
        "",
        "```yaml",
        _machine_yaml(code, obj).rstrip(),
        "```",
        "",
    ]
    return "\n".join(parts)


class CCRenderer:
    """`contracts.Renderer` for capability contracts (kind="CC").

    Conforms to the seam's `render(contract)` signature: the structured `contract` mapping
    carries the artifact `code` (or `cc_code`) alongside the contract-object fields; this
    renderer pulls the code out and deterministically expands the rest to admissible CC
    Markdown via the module-level `render`.
    """

    kind = "CC"

    def render(self, contract: dict[str, Any]) -> str:
        obj = dict(contract)
        code = obj.pop("code", None) or obj.pop("cc_code", None)
        if not code:
            raise ContractError("CC contract is missing 'code' (or 'cc_code')")
        return render(code, obj)


if __name__ == "__main__":
    # self-test: a tiny contract object renders to valid YAML with derived fields
    demo = {
        "summary": "demo", "intent": "i", "rationale": "r",
        "inputs": [{"name": "x", "type": "string", "required": True, "description": "an id (prefix: X)"}],
        "outputs": [{"name": "ids", "type": "array", "items_type": "string"}],
        "pipeline": [{"step": "s1", "kind": "CS", "capability": "capability_side_effects::CS_MUTABLE_JSON_V0",
                      "store": "MEMPOOL", "op": "LIST", "inputs": {}, "outputs": {"k": "$.capability_result.keys"},
                      "on_result": {"SUCCESS": "exit", "VIOLATION": "exit", "BACKEND_ERROR": "exit"}}],
        "extensions": {"subdomain": "mempool", "notes": ["n"]},
    }
    md = render("CC_DEMO_V0", demo)
    import re
    block = re.search(r"```yaml\n(.*?)\n```", md, re.S).group(1)
    yaml.safe_load(block)  # must parse
    assert '"an id (prefix: X)"' in block or "an id (prefix: X)" in block
    print("renderer self-test OK — machine block parses, colon auto-quoted")
    print(block)

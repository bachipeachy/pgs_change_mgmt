"""Deterministic CT (capability transform) renderer — contract object → admissible Markdown.

The PAS for the Capability (CT) family: a pure transform is `inputs → outputs`, both typed, zero side
effects. The renderer only formats a complete contract object; it never infers or derives (the types are
already resolved by the Construction Compiler's TYPE_PROPAGATION / declared signatures).
"""
from __future__ import annotations

import yaml
from typing import Any

GOVERNED_BY = "fb.topology::CONSTITUTION_CAPABILITY_TRANSFORMS_V0"


def _typed(d: dict[str, Any], *, required: bool) -> dict[str, Any]:
    return {n: ({"type": t, "required": True} if required else {"type": t}) for n, t in (d or {}).items()}


def render(code: str, obj: dict[str, Any]) -> str:
    inputs = obj.get("inputs", {}) or {}
    outputs = obj.get("outputs", {}) or {}
    doc = {
        "ct_code": code, "version": "v0", "governed_by": GOVERNED_BY,
        "core": {
            "summary": obj.get("summary", code),
            "inputs": _typed(inputs, required=True),
            "outputs": _typed(outputs, required=False),
        },
        # `machine` (kind · purity · operation · implementation binding) is Contract-owned; the renderer
        # only formats it. Governed CT schema requires it.
        "machine": obj.get("machine") or {"ct_kind": "atom", "ct_purity": "ct_pure", "operation": "COMPUTE"},
    }
    machine = yaml.safe_dump(doc, sort_keys=False, default_flow_style=False, width=100)

    def _tbl(d: dict[str, Any]) -> str:
        rows = ["| Field | Type |", "|---|---|"] + [f"| {n} | {t} |" for n, t in d.items()]
        return "\n".join(rows) if d else "(none)"

    parts = [
        f"# {code}", "",
        "## Header (Mandatory)", "",
        f"- **Artifact Code:** {code}",
        "- **Artifact Kind:** capability_transform",
        "- **Governed By:** CONSTITUTION_CAPABILITY_TRANSFORMS_V0",
        "- **Version:** v0",
        "- **Status:** canonical",
        "", "---", "", "## 1. Summary", "", obj.get("summary", code),
        "", "---", "", "## 2. Inputs", "", _tbl(inputs),
        "", "---", "", "## 3. Outputs", "", _tbl(outputs),
        "", "---", "", "## Machine", "", "```yaml", machine.rstrip(), "```", "",
    ]
    return "\n".join(parts)


class CTRenderer:
    """`contracts.Renderer` for capability transforms (kind="CT")."""

    kind = "CT"

    def render(self, contract: dict[str, Any]) -> str:
        obj = dict(contract)
        code = obj.pop("code", None) or obj.pop("ct_code", None)
        if not code:
            raise ValueError("CT contract is missing 'code'")
        return render(code, obj)


if __name__ == "__main__":
    import re
    md = render("CT_DEMO_V0", {"summary": "demo", "inputs": {"x": "object"}, "outputs": {"y": "string"}})
    block = re.search(r"```yaml\n(.*?)\n```", md, re.S).group(1)
    yaml.safe_load(block)
    print("CT renderer self-test OK — machine block parses")

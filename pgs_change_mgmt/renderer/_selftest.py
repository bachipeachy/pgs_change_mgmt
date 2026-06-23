"""Renderer self-test — every implemented kind expands a known-good contract object into an
admissible artifact whose machine block is valid YAML with the kind's required shape.

Run:  python -m pgs_change_mgmt.renderer._selftest
"""

from __future__ import annotations

import re
import sys

import yaml

from .registry import KINDS, RENDERERS, get_renderer


def _machine(md: str) -> dict:
    block = re.search(r"```yaml\n(.*?)\n```", md, re.S)
    assert block, "no ```yaml machine block in rendered artifact"
    return yaml.safe_load(block.group(1))


CONTRACTS = {
    "CC": {
        "code": "CC_DEMO_V0", "summary": "demo cc", "intent": "i", "rationale": "r",
        "inputs": [{"name": "x", "type": "string", "required": True, "description": "id (prefix: X)"}],
        "outputs": [{"name": "ids", "type": "array", "items_type": "string"}],
        "pipeline": [{"step": "s1", "kind": "CS", "capability": "capability_side_effects::CS_MUTABLE_JSON_V0",
                      "store": "MEMPOOL", "op": "WRITE", "inputs": {}, "outputs": {},
                      "on_result": {"SUCCESS": "exit", "VIOLATION": "exit"}}],
        "extensions": {"subdomain": "mempool", "notes": []},
    },
    "IN": {
        "code": "IN_DEMO_V0", "summary": "submit demo", "intent": "i", "rationale": "r",
        "workflow": "WF_DEMO_V0", "domain": "pgs.blockchain.mempool", "authority": "SYSTEM",
        "inputs": [{"name": "amount", "type": "number", "required": True, "description": "amt"}],
        "outcomes": [{"name": "ACK", "description": "accepted"}, {"name": "NACK", "description": "rejected"}],
    },
    "RB": {
        "code": "RB_DEMO_V0", "summary": "rb for demo", "description": "binds CS",
        "storage_structure": "blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0",
        "bindings": [{"capability": "capability_side_effects::CS_MUTABLE_JSON_V0", "policy": {}},
                     {"capability": "capability_side_effects::CS_REGISTRY_V0",
                      "policy": {"path": "{{module_data_root}}/x.json"}}],
    },
    "WF": {
        "code": "WF_DEMO_V0", "summary": "demo wf", "intent": "i", "rationale": "r",
        "runtime_binding": "blockchain::RB_DEMO_V0", "subdomain": "mempool",
        "admission": {"requires": [], "forbids": []},
        "start_node": "IN_DEMO_V0",
        "nodes": [
            {"node": "IN_DEMO_V0", "type": "IN", "code": "IN_DEMO_V0",
             "next": {"ACK": "CC_DO_V0", "NACK": "EXIT"}},
            {"node": "CC_DO_V0", "type": "CC", "code": "CC_DO_V0",
             "inputs": {"amount": "$.payload.amount"},
             "next": {"SUCCESS": "EXIT_OK", "VIOLATION": "EXIT"}},
            {"node": "EXIT_OK", "type": "EXIT", "reason": "COMPLETED"},
            {"node": "EXIT", "type": "EXIT", "reason": "EXITED"},
        ],
    },
}

EXPECT = {
    "CC": ("cc_code", "CC_DEMO_V0"),
    "IN": ("in_code", "IN_DEMO_V0"),
    "RB": ("rb_code", "RB_DEMO_V0"),
    "WF": ("wf_code", "WF_DEMO_V0"),
}


def main() -> int:
    implemented = sorted(RENDERERS)
    print(f"kinds declared : {list(KINDS)}")
    print(f"kinds rendered : {implemented}\n")
    for kind in implemented:
        r = get_renderer(kind)
        md = r.render(CONTRACTS[kind])
        doc = _machine(md)
        key, val = EXPECT[kind]
        assert doc[key] == val, f"{kind}: {key} != {val}"
        assert doc["governed_by"].startswith("fb.topology::"), f"{kind}: governed_by"
        assert "core" in doc, f"{kind}: missing core"
        assert f"# {val}" in md and "## Header (Mandatory)" in md, f"{kind}: header"
        print(f"  {kind}: {val:14} machine OK ({key}, governed_by, core) ✓")

    # WF routing integrity is validated by the renderer; a bad target must be rejected.
    bad = dict(CONTRACTS["WF"]); bad["nodes"] = CONTRACTS["WF"]["nodes"][:1]  # IN points to missing nodes
    try:
        get_renderer("WF").render(bad)
        raise SystemExit("WF should have rejected dangling next target")
    except Exception as exc:
        if "is not a known node" not in str(exc):
            raise
    print("  WF: dangling-route rejected ✓")

    # Unimplemented kinds still fail loudly.
    for k in ("CT", "CS", "STRUCTURE"):
        try:
            get_renderer(k); raise SystemExit(f"{k} should be unimplemented")
        except NotImplementedError:
            pass
    print("\nALL IMPLEMENTED RENDERERS ADMISSIBLE ✓ (CC, IN, RB, WF); CT/CS/STRUCTURE declared")
    return 0


if __name__ == "__main__":
    sys.exit(main())

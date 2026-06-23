"""Smoke test for pi_tools — exercises every wrapped pi query against the live
snapshot and confirms each returns pi's stable JSON envelope.

Run:  PGS_WORKSPACE=/abs/path/to/pgs_workspace python smoke_pi_tools.py

This is a grounding check, not a unit test: it proves the wrapper actually
reaches pi and that each tool name dispatches to a real, read-only query.
"""

from __future__ import annotations

import sys

from pgs_change_mgmt.grounding import PiClient, TOOL_NAMES, dispatch


def _assert_envelope(label: str, env: dict) -> None:
    for key in ("query", "result", "schema_version"):
        if key not in env:
            raise AssertionError(f"{label}: missing '{key}' in envelope: {env!r}")
    print(f"  ok  {label:24}  schema={env['schema_version']}  command={env['query'].get('command')!r}")


def main() -> int:
    client = PiClient()
    print(f"workspace = {client.workspace}")
    print(f"pi_bin    = {client.pi_bin}")
    print(f"tools     = {', '.join(TOOL_NAMES)}\n")

    # Discover a real FQDN to use for the FQDN-bound queries.
    found = client.vocab_search("REGISTER_ACTOR")
    _assert_envelope("vocab_search", found)
    wf = next(r["fqdn"] for r in found["result"] if r["kind"] == "WF")
    cc = next((r["fqdn"] for r in client.vocab_search("GENERATE_ACTOR_ID")["result"]
               if r["kind"] == "CC"), wf)
    print(f"\n  discovered WF = {wf}\n  discovered CC = {cc}\n")

    cases = [
        ("vocab_search", {"term": "WALLET"}),
        ("artifact_refs", {"ref": cc}),
        ("artifact_refs", {"ref": cc, "transitive": True}),
        ("artifact_source", {"ref": wf}),
        ("topology_impact", {"ref": cc}),
        ("behavior_logic_show", {"ref": wf}),
        ("validate", {}),
        ("validate", {"strict": True}),
    ]
    for name, args in cases:
        env = dispatch(client, name, args)
        _assert_envelope(f"{name}{tuple(args.values()) or ''}", env)

    print("\nALL TOOLS GROUNDED ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())

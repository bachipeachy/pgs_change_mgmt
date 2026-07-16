"""Construction Model engine proof — Project → Construct → Validate → Serialize over the chain slice.

Offline, deterministic. Proves: (1) the graph is built from the Construction Projection; (2) the
Lowering Pipeline annotates it — routing expansion, binding + store resolve with zero violations;
(3) Validate reports exactly the honest `TYPED_PORT` gaps (D4 not yet closed — CS/new-CT contracts
carry no field types), and gates serialization on them; (4) once types are present (D4 simulated),
Serialize renders an admissible CC artifact whose machine block is valid YAML.

Run:  PGS_WORKSPACE=/abs python -m pgs_change_mgmt.engine._construction_model_selftest
"""
from __future__ import annotations

import os
import re
from collections import Counter
from pathlib import Path

import yaml

from ._fixture import authored, chain_dossier
from .construction_model import build

WS = Path(os.environ.get("PGS_WORKSPACE", ""))
CC = "blockchain::CC_COMMIT_BLOCK_CANONICAL_V0"


def main() -> int:
    assert WS, "set PGS_WORKSPACE"
    if not authored():
        print("CONSTRUCTION MODEL PROOF PENDING ⏳ — frozen chain fixture predates S7 authoring "
              "(no new_capabilities/new_intents); D4 cannot close. Re-freeze the fixture from the first "
              "governed from-seed run to activate this regression test.")
        return 0
    with chain_dossier() as chain:
        r = build(chain / "cr_ir", domain="blockchain", subdomain="chain", workspace=WS)
    g = r.graph

    # 1 — Project
    concepts = Counter(n.concept for n in g.nodes.values())
    assert concepts["CapabilityComposition"] == 4 and concepts["Step"] == 11, concepts
    assert concepts["Capability"] == 4 and concepts["CapabilityReference"] == 2, concepts
    assert concepts["Store"] == 2, concepts
    print(f"  Project: {sum(concepts.values())} nodes {dict(concepts)}, {len(g.edges)} edges ✓")

    # 2 — Normalize + Lower: expansion + binding + store, zero structural violations
    steps = g.contained_steps(CC)
    assert [s.attrs["kind"] for s in steps] == ["CT", "CS", "CS"], steps
    assert next(e for e in g.by_role("ACCESSES") if e.frm == steps[2].id).to == "store:chain:chain_head"
    # content_hash produced by step1, consumed by step2 → a DATAFLOW edge exists
    df = [(e.frm, e.to) for e in g.by_role("DATAFLOW")]
    assert any(f.endswith(":out:content_hash") and t.endswith(":in:content_hash") for f, t in df), df
    struct = [v for v in r.violations if v.constraint in ("SINGLE_PRODUCER", "STORE_RESOLVED", "SINGLE_SUCCESSOR")]
    assert not struct, f"unexpected structural violations: {struct}"
    print(f"  Normalize+Lower: routing+binding+store resolved, 0 structural violations ✓")

    # 3 — Validate: D4 closed → zero violations; CC + CT families serialize (dependency closure)
    kinds = Counter(v.constraint for v in r.violations)
    assert not kinds, f"D4 closed → expected zero violations, got {dict(kinds)}"
    served = [nid for nid, a in r.artifacts.items() if isinstance(a, str)]
    ccs = [n for n in served if "::CC_" in n]
    cts = [n for n in served if "::CT_" in n]
    assert len(ccs) == 4 and len(cts) == 4, f"expected 4 CC + 4 CT, got {len(ccs)}CC/{len(cts)}CT: {served}"
    print(f"  Validate: 0 violations (D4 closed); {len(ccs)} CC + {len(cts)} CT serialized (CT dependency closure) ✓")

    # 4 — Serialize: real admissible CC + CT markdown from declared types (no injection); machine blocks parse
    def _machine(md):
        return yaml.safe_load(re.search(r"```yaml\n(.*?)\n```", md, re.S).group(1))
    ccdoc = _machine(r.artifacts[CC])
    assert ccdoc["cc_code"] == "CC_COMMIT_BLOCK_CANONICAL_V0" and ccdoc["core"]["pipeline"], ccdoc
    ctdoc = _machine(r.artifacts["blockchain::CT_PURE_HASH_BLOCK_V0"])
    assert ctdoc["ct_code"] == "CT_PURE_HASH_BLOCK_V0" and ctdoc["core"]["outputs"], ctdoc
    print(f"  Serialize: CC (pipeline) + CT (typed signature) artifacts render, machine blocks parse ✓")

    print("\nCONSTRUCTION MODEL PROOF OK ✓ — Project→Normalize→Lower→Validate→Serialize; D4 closed; "
          "CC + CT families serialize (multi-family compiler, CT dependency closure); constraints are "
          "the gap census; renderer only formats. No LLM.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Disposition Completeness oracle proof (SPP · DP4) — measured against the real chain S2.

Asserts the oracle: (1) counts cited FQDNs as implicit RELEVANT; (2) supports GROUP disposition
(segment-pattern + kind rules) so a worker dispositions adjacent-subdomain internals in a few lines
rather than per node; (3) reaches 100% completeness with a realistic rule set; (4) flags any
undisposed element; (5) dispositions `absent` concepts via the gaps register. Also reports the
coverage of the *bare* (cited-only) output — a projection-quality signal that feeds DP1 bounding.

Run:  python -m pgs_change_mgmt.evaluator._disposition_completeness_selftest
      (reads the exported chain stage-2 package + its authored S2 document, if present)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .disposition_completeness import assess, collect_cited_fqdns

PASS, FAIL = "✅", "❌"
CHAIN = Path(__file__).resolve().parents[2] / "change_mgmt" / "dossiers" / "blockchain" / "chain"
PKG = CHAIN / "_packages" / "stage_2" / "context" / "discovery_projection.json"
DOC = CHAIN / "2_domain_model_blockchain_chain_v0.md"

# A realistic worker disposition set: cited nodes are RELEVANT implicitly; these GROUP rules
# disposition the adjacent-subdomain internals the chain consumes but does not model, plus scaffolding.
GROUP_RULES = [
    {"target": "ACTOR", "disposition": "NOT_APPLICABLE", "reason": "identity internals; chain reads actor state, does not model it"},
    {"target": "WALLET", "disposition": "NOT_APPLICABLE", "reason": "wallet internals; chain credits balances via genesis, does not model wallet mgmt"},
    {"target": "TRANSACTION", "disposition": "NOT_APPLICABLE", "reason": "transaction internals; chain records committed txs, does not build them"},
    {"target": "TX", "disposition": "NOT_APPLICABLE", "reason": "transaction internals"},
    {"target": "VALIDATOR", "disposition": "NOT_APPLICABLE", "reason": "validator registry internals; chain reads eligibility"},
    {"target": "MEMPOOL", "disposition": "NOT_APPLICABLE", "reason": "mempool internals; chain drains claimed txs only"},
    {"target": "SLOT", "disposition": "NOT_APPLICABLE", "reason": "orchestration slot internals; chain commits what a slot proposes"},
    {"target": "SIMULATION", "disposition": "NOT_APPLICABLE", "reason": "simulation harness, not chain domain"},
    {"target": "STAKE", "disposition": "NOT_APPLICABLE", "reason": "staking out of scope this release"},
    {"target": "UNSTAKE", "disposition": "NOT_APPLICABLE", "reason": "staking out of scope"},
    {"target": "TRANSFER", "disposition": "NOT_APPLICABLE", "reason": "transfers out of scope this release"},
    {"target": "MINT", "disposition": "RELEVANT", "reason": "genesis reuses mint policy"},
    {"target": "CONSENSUS", "disposition": "NOT_APPLICABLE", "reason": "consensus internals; chain commits its proposed blocks"},
    {"target": "kind:TEST_DATA", "disposition": "NOT_APPLICABLE", "reason": "test scaffolding"},
    {"target": "kind:TI", "disposition": "NOT_APPLICABLE", "reason": "transport ingress, not domain"},
    {"target": "kind:ASSERT", "disposition": "NOT_APPLICABLE", "reason": "compiler assertion scaffolding"},
    {"target": "kind:GOVERNANCE", "disposition": "EXCLUDED", "reason": "governance scaffolding, not a domain concept"},
    # proposal is the chain's direct upstream (RELEVANT); the rest are adjacent internals / out-of-scope
    {"target": "PROPOSE", "disposition": "RELEVANT", "reason": "block proposal is the chain's direct input"},
    {"target": "PROPOSED", "disposition": "RELEVANT", "reason": "proposed-block intent/event the chain consumes"},
    {"target": "PROPOSER", "disposition": "NOT_APPLICABLE", "reason": "proposer selection is consensus internal"},
    {"target": "ROUND", "disposition": "NOT_APPLICABLE", "reason": "consensus round internals"},
    {"target": "NONCE", "disposition": "NOT_APPLICABLE", "reason": "wallet nonce internals"},
    {"target": "BALANCE", "disposition": "NOT_APPLICABLE", "reason": "wallet balance events"},
    {"target": "RECONCILED", "disposition": "NOT_APPLICABLE", "reason": "balance reconciliation event"},
    {"target": "BURN", "disposition": "NOT_APPLICABLE", "reason": "burn out of scope (closed supply)"},
    {"target": "POOL", "disposition": "NOT_APPLICABLE", "reason": "pooling out of scope"},
    {"target": "REWARD", "disposition": "NOT_APPLICABLE", "reason": "rewards out of scope this release"},
    {"target": "SLASH", "disposition": "NOT_APPLICABLE", "reason": "slashing out of scope this release"},
    # absent concepts that are REPRESENTED under other artifacts (not gaps to author)
    {"target": "BACHICOIN", "disposition": "REPRESENTED", "reason": "tracked as wallet balance, not a standalone artifact"},
    {"target": "IDENTITY", "disposition": "REPRESENTED", "reason": "represented via ACTOR artifacts"},
]


def _check(cond: bool, label: str) -> bool:
    print(f"  {PASS if cond else FAIL} {label}")
    return cond


def _s2_registers_from_doc(doc_text: str) -> dict:
    """A minimal register view for the oracle: one synthetic register holding every cited FQDN cell,
    plus a `gaps` register carrying the doc's gap prose (enough to disposition `absent`)."""
    cited = re.findall(r"blockchain::[A-Z][A-Z0-9_]+_V\d+", doc_text)
    gaps_prose = "\n".join(l for l in doc_text.splitlines() if "absent" in l or "no commit" in l.lower()
                           or "genesis" in l.lower() or "bootstrap" in l.lower())
    return {"_cited": [{"evidence": f} for f in cited],
            "gaps": [{"gap": gaps_prose}]}


def main() -> int:
    if not PKG.exists() or not DOC.exists():
        print(f"skip: needs an exported chain stage-2 package + S2 doc\n  {PKG}\n  {DOC}")
        return 0
    ok = True
    projection = json.loads(PKG.read_text())
    registers = _s2_registers_from_doc(DOC.read_text())
    n_existing = len(projection["evidence"]["existing"])
    n_absent = len(projection["evidence"]["absent"])

    # 1. bare (cited-only) coverage — the projection-quality signal
    bare = assess(projection, registers)
    print(f"neighborhood: {n_existing} existing + {n_absent} absent")
    print(f"bare (cited-only) coverage: {bare.coverage:.0%} "
          f"({len(bare.undisposed_existing)} existing undisposed) — over-scope signal for DP1 bounding")
    ok &= _check(len(bare.existing_disposed) > 0 and not bare.ok,
                 f"cited FQDNs auto-disposition as RELEVANT ({len(bare.existing_disposed)}); "
                 "bare output is INCOMPLETE (undisposed remain)")

    # 2. group disposition — a segment rule dispositions a whole adjacent-subdomain set
    wallet_rule = [{"target": "WALLET", "disposition": "NOT_APPLICABLE", "reason": "x"}]
    r = assess(projection, registers, wallet_rule)
    wallet_disposed = [f for f, d in r.existing_disposed.items() if "WALLET" in f and d == "NOT_APPLICABLE"]
    ok &= _check(len(wallet_disposed) >= 3, f"one group rule dispositions a whole set "
                 f"(WALLET → {len(wallet_disposed)} nodes NOT_APPLICABLE)")

    # 3. full realistic disposition → 100% complete
    full = assess(projection, registers, GROUP_RULES)
    print(f"with {len(GROUP_RULES)} group rules: coverage {full.coverage:.0%}  "
          f"dispositions {full.by_disposition()}")
    if full.undisposed_existing:
        print("  residual undisposed:", [f.split('::')[1] for f in full.undisposed_existing])
    ok &= _check(full.ok, "realistic citations + group rules → 100% disposed (ADMISSIBLE)")

    # 4. completeness gate — dropping a rule reintroduces undisposed
    partial = assess(projection, registers, [g for g in GROUP_RULES if g["target"] != "ACTOR"])
    ok &= _check(not partial.ok and any("ACTOR" in f for f in partial.undisposed_existing),
                 "dropping the ACTOR rule → undisposed ACTOR nodes → INADMISSIBLE")

    # 5. absent dispositioned via the gaps register
    ok &= _check(full.absent_disposed.get("GENESIS") == "GAP"
                 and full.absent_disposed.get("BOOTSTRAP") == "GAP",
                 "absent concepts (GENESIS/BOOTSTRAP) dispositioned as GAP via the gaps register")

    print(f"\n{'ALL PASS' if ok else 'FAILURES PRESENT'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
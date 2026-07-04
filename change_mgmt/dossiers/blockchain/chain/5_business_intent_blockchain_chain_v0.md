# Business Intent: blockchain / chain
**Domain:** blockchain  
**Subdomain:** chain  
**Version:** V0  
**Status:** DRAFT  
**Pipeline Stage:** Stage 5 — Business Intent (WHAT)  
**Produced by:** v0.5.0 SDLC authoring pipeline  

---

## Document Contract

**This artifact is a structured register document — not a narrative.** The Business Intent captures
the irreducible WHAT — purpose, scope, invariants, actions, and provisional artifact codes. Purpose
(§1) is short prose (the one irreducible business narrative a compiler can never derive); everything
else — including Identity Semantics (§4) — is registers. The worker emits register ROWS; a
deterministic renderer owns the document. A required cell with no basis in the seed or the snapshot
is declared `UNRESOLVED` (a governed hole), never fabricated and never left blank.

VALID OUTPUT:
- The Purpose prose section (§1) filled for this subdomain
- Populated register tables (every required register below), or `UNRESOLVED` for a genuine hole
- Business-language descriptions in content columns

INVALID OUTPUT:
- Narrative essays replacing the registers
- Implementation bindings, JSONPath, op codes, module paths, or content hashes (those are Stage 6b)

A required register with no rows renders as `| NONE IDENTIFIED |`.

---

### Provisional codes

This is the first stage that assigns **provisional** artifact codes (`provisional_codes`). They are
provisional — Stage 6b assigns the binding domain-qualified FQDNs. Each carries a `_V0` suffix.
Workflow nodes are IN / CC / EXIT only; a sub-workflow call is a gateway CC, never a nested WF. EV
artifacts record facts, never trigger execution.

---

## Stage Inputs — Questions for the Human

| # | Question for the Human | How the Agent Uses the Answer (Intent) |
|---|------------------------|----------------------------------------|
| 1 | In one paragraph: what does this subdomain govern, and why does it exist? | Becomes §1 Purpose — the scope of authority everything hangs from. |
| 2 | For each business record: does history matter, can values be corrected, is deletion allowed? | Selects the Record Model in `business_objects`. |
| 3 | Which field uniquely identifies each record, where does it come from, what does a duplicate mean? | Becomes the `identity_semantics` register (§4). |
| 4 | What is always forbidden or always required, and what is the business reason? | Becomes `invariants`. |
| 5 | What verbs can be performed on these records, and who/what triggers each? | Becomes `actions` — each in-scope action yields one Intent and one Workflow. |

---

## 1. Subdomain Purpose

*One short paragraph: what this subdomain governs, what authority it establishes, what lifecycle it
manages, and the business rationale for its existence. Write for a business stakeholder. No artifact
names.*

The Chain subdomain maintains the official blockchain ledger. It records every block that has been accepted by the network and preserves the complete history of the blockchain from the beginning. Other subdomains decide which blocks should be accepted, but the Chain subdomain is responsible for maintaining the authoritative record once that decision has been made. This authoritative ledger is the foundation that the rest of the blockchain system relies on.

---

## 2. Scope Boundary

*What V0 commits to vs. what is explicitly deferred. A vague scope boundary is a governance defect. Status ∈ IN_SCOPE | DEFERRED.*

<!-- register:scope_boundary business_language=capability,notes -->
| Capability | Status (IN_SCOPE, DEFERRED) | Notes | Source Finding |
|------------|-----------------------------|-------|----------------|
| Commit a proposed block to the canonical chain | IN_SCOPE | the core outcome — proposed blocks become canonical | S4 capability_graph GAP-1 |
| Store the canonical chain ledger and track its head | IN_SCOPE | append-only record of committed blocks | S4 capability_graph GAP-2 |
| Bootstrap the genesis chain and initialise the supply | IN_SCOPE | one-time, before the consensus loop runs | S4 capability_graph GAP-5 |
| Reconcile wallet balances after commit | IN_SCOPE | balances derived from committed transactions | S4 capability_graph GAP-6 |
| Attest proposed blocks | DEFERRED | deferred to a future increment | S1 out_of_scope attest |
| Finalize committed blocks | DEFERRED | deferred; blocks committed directly | S1 out_of_scope finalize |
| Resolve forks and chain reorganizations | DEFERRED | not this release; committed history is immutable | S1 out_of_scope fork/reorg |
| Slash or reward validators | DEFERRED | validator penalties/rewards out of scope | S1 out_of_scope slashing/rewards |

---

## 3. Business Objects

*The business records this subdomain maintains and WHY each takes its form. Record Model ∈ MUTABLE_STATE (current state, correctable) | APPEND_ONLY_JOURNAL (immutable history) | IDENTITY_REGISTRY (stable key→address) | HYBRID. Business language.*

<!-- register:business_objects optional business_language=store_name,business_rationale -->
| Store Name | Record Model (MUTABLE_STATE, APPEND_ONLY_JOURNAL, IDENTITY_REGISTRY, HYBRID) | Business Rationale | Source Finding |
|------------|------------------------------------------------------------------------------|--------------------|----------------|
| The canonical chain ledger | APPEND_ONLY_JOURNAL | Committed history is immutable and ordered; blocks are appended and never altered or removed, so the record is an append-only journal. | S4 constraint_register #2, #6; S1 business_invariants #4, #5 |

---

## 4. Identity Semantics

*Which field uniquely identifies each record, where it comes from, what a duplicate means, and any
cross-subdomain identity relationship. The compiler cannot infer identity semantics from field
names — this is irreducible business knowledge. If a cell is genuinely not derivable from the seed,
declare it `UNRESOLVED` (a governed hole a human will resolve) rather than guessing.*

<!-- register:identity_semantics business_language=identity_field,source,uniqueness_rule,cross_subdomain_relationship -->
| Store Name | Identity Field | Source | Uniqueness Rule | Cross-Subdomain Relationship | Source Finding |
|------------|----------------|--------|-----------------|------------------------------|----------------|
| The canonical chain ledger | The block's content signature | Computed by hashing the committed block's content at commit | Each committed block has a unique content signature; a block cannot be committed twice | The block originates as a proposed block produced by the consensus subdomain | S1 business_vocabulary Commit; S1 business_invariants #6 |

---

## 5. Business Invariants

*Non-negotiable rules with a business reason. A rule without a business reason is a technical constraint and belongs elsewhere.*

<!-- register:invariants business_language=invariant,business_reason -->
| Invariant | Business Reason | Source Finding |
|-----------|-----------------|----------------|
| A committed block is immutable — it never changes or disappears. | Committed history must be a permanent, reliable record other subdomains can trust. | S1 business_invariants #4 |
| Every committed block has exactly one predecessor, except the genesis block. | The chain is a single, ordered history with one origin. | S1 business_invariants #5 |
| A block cannot be committed twice. | Prevents duplication or replay of committed history. | S1 business_invariants #6 |
| Exactly one genesis block exists per chain, and genesis executes exactly once. | The chain has a single, permanent origin and initial state. | S1 business_invariants #1, #2 |
| Total supply is conserved at 1,000,000 BachiCoin after genesis. | The monetary system is closed — no supply enters or leaves except by the system's rules. | S1 business_invariants #3 |
| A proposed block is not authoritative until committed. | The chain is the sole authority for committed history. | S1 business_invariants #7 |
| Wallet balances are derived from committed transactions, not owned by the chain as independent state. | Balances must always be consistent with the canonical committed history. | S1 known_facts #11 (human decision) |

---

## 6. Business Actions

*Every verb performable on this subdomain's objects, in plain business language. Each in-scope action maps to one Intent and one Workflow. Status ∈ IN_SCOPE | DEFERRED.*

<!-- register:actions business_language=object,trigger -->
| Action | Object | Trigger | Status (IN_SCOPE, DEFERRED) | Source Finding |
|--------|--------|---------|-----------------------------|----------------|
| Commit | a proposed block | the consensus loop produces a proposed block | IN_SCOPE | S4 relationships Chain commits Proposed Block |
| Bootstrap | the genesis chain | system initialisation, once, before the consensus loop runs | IN_SCOPE | S4 relationships Bootstrap creates Genesis Block |
| Attest | a proposed block | deferred this increment | DEFERRED | S1 out_of_scope attest |
| Finalize | a committed block | deferred this increment | DEFERRED | S1 out_of_scope finalize |

---

## 7. Provisional Artifact Codes

*Provisional AC / IN / WF / CC codes (Stage 6b assigns binding FQDNs). Each carries `_V0`. `summary` is business language. Family ∈ AC | IN | WF | CC.*

<!-- register:provisional_codes business_language=summary -->
| Provisional Code | Family (AC, IN, WF, CC) | Summary | Source Finding |
|------------------|-------------------------|---------|----------------|
| IN_COMMIT_BLOCK_V0 | IN | Admit a request to commit a proposed block to the canonical chain. | S5 actions Commit |
| WF_COMMIT_BLOCK_V0 | WF | Commit a proposed block: validate its predecessor link, sign it, record it as canonical, and reconcile balances. | S5 actions Commit |
| IN_BOOTSTRAP_GENESIS_CHAIN_V0 | IN | Admit a request to bootstrap the genesis chain and initialise the supply. | S5 actions Bootstrap |
| WF_BOOTSTRAP_GENESIS_CHAIN_V0 | WF | Bootstrap the genesis chain: create the genesis block and initialise the fixed supply before consensus runs. | S5 actions Bootstrap |
| CC_COMMIT_BLOCK_CANONICAL_V0 | CC | Record a validated, signed proposed block as canonical on the chain and announce it committed. | S4 gap_register GAP-1 |
| CC_VALIDATE_PREDECESSOR_LINK_V0 | CC | Check that a proposed block's predecessor link matches the current chain head before commit. | S4 gap_register GAP-3 |
| CC_CREATE_GENESIS_BLOCK_V0 | CC | Create the genesis block containing the initial mint and record it as the first committed block. | S4 gap_register GAP-5 |
| CC_RECONCILE_BALANCES_V0 | CC | Reconcile wallet balances from the committed transactions after a block commits. | S4 gap_register GAP-6 |

---

## 8. Cross-Subdomain References

*Capability Contracts defined in another subdomain and referenced by this subdomain's workflows. `cc_code` is the existing FQDN; do not re-document it here.*

<!-- register:cross_subdomain_refs optional business_language=role -->
| CC Code | Defined In | Role | Source Finding |
|---------|------------|------|----------------|
| NONE IDENTIFIED |  |  |  |

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 4 — Business Model | business_model_chain_v0.md | COMPLETE |
| Stage 5 — Business Intent | This document | COMPLETE |
| Stage 6 — Governance Intent | Pending | — |

---

## gov_projection — Governed Handoff to Stage 6

*The bounded inputs and emit keys mirror the engine's gov_projection schema exactly
(`contracts/gov_projection.py`): S5 consumes the S4 discovery output plus the S1 release boundary
and emits the WHAT. Emit keys match the register ids above exactly (Purpose §1 / Identity Semantics
§4 / Business Objects §3 are this stage's record, not forwarded fields).*

| Direction | Fields |
|-----------|--------|
| **Consumes** ← Stage 1 | out_of_scope |
| **Consumes** ← Stage 4 | actors · bm_entities · events · capability_graph · constraint_register |
| **Emits** → Stage 6 | scope_boundary · invariants · actions · provisional_codes · cross_subdomain_refs |

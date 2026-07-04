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
| commit a proposed block to the canonical chain | IN_SCOPE | the core capability this CR delivers | S4-GAP-1 |
| bootstrap genesis and mint the initial supply once | IN_SCOPE | one-time startup; reuses the existing mint policy | S4-GAP-2 |
| the canonical ledger store for committed blocks | IN_SCOPE | the store the chain owns | S4-GAP-3 |
| attestation and finalization of committed blocks | DEFERRED | excluded by the CR; every committed block is treated as good this increment | S4-design-3 |

---

## 3. Business Objects

*The business records this subdomain maintains and WHY each takes its form. Record Model ∈ MUTABLE_STATE (current state, correctable) | APPEND_ONLY_JOURNAL (immutable history) | IDENTITY_REGISTRY (stable key→address) | HYBRID. Business language.*

<!-- register:business_objects optional business_language=store_name,business_rationale -->
| Store Name | Record Model (MUTABLE_STATE, APPEND_ONLY_JOURNAL, IDENTITY_REGISTRY, HYBRID) | Business Rationale | Source Finding |
|------------|------------------------------------------------------------------------------|--------------------|----------------|
| canonical chain ledger | APPEND_ONLY_JOURNAL | committed history is permanent and ordered; blocks are appended and never rewritten | S4-entity-canonical-chain |

---

## 4. Identity Semantics

*Which field uniquely identifies each record, where it comes from, what a duplicate means, and any
cross-subdomain identity relationship. The compiler cannot infer identity semantics from field
names — this is irreducible business knowledge. If a cell is genuinely not derivable from the seed,
declare it `UNRESOLVED` (a governed hole a human will resolve) rather than guessing.*

<!-- register:identity_semantics business_language=identity_field,source,uniqueness_rule,cross_subdomain_relationship -->
| Store Name | Identity Field | Source | Uniqueness Rule | Cross-Subdomain Relationship | Source Finding |
|------------|----------------|--------|-----------------|------------------------------|----------------|
| canonical chain ledger | block height | assigned at commit as the next position after the current head | exactly one committed block per height; the genesis block is height zero | commits the proposed block produced upstream in consensus_pos | S4-entity-committed-block |

---

## 5. Business Invariants

*Non-negotiable rules with a business reason. A rule without a business reason is a technical constraint and belongs elsewhere.*

<!-- register:invariants business_language=invariant,business_reason -->
| Invariant | Business Reason | Source Finding |
|-----------|-----------------|----------------|
| the canonical chain is append-only and immutable | committed history is the source of truth; rewriting it would destroy the trust the ledger exists to provide | S4-constraint-1 |
| the monetary supply is closed and minted exactly once at genesis | a fixed supply is a monetary guarantee; a second minting path would break it | S4-constraint-2 |
| a block is committed at exactly one height, contiguous with the head | gaps or forks in height would make the ledger ambiguous about which history is canonical | S4-entity-committed-block |
| the committed-block signal is emitted once per committed block | downstream consumers need a single unambiguous signal that a block became permanent | S4-constraint-3 |

---

## 6. Business Actions

*Every verb performable on this subdomain's objects, in plain business language. Each in-scope action maps to one Intent and one Workflow. Status ∈ IN_SCOPE | DEFERRED.*

<!-- register:actions business_language=object,trigger -->
| Action | Object | Trigger | Status (IN_SCOPE, DEFERRED) | Source Finding |
|--------|--------|---------|-----------------------------|----------------|
| commit | proposed block | a consensus round closes and yields a proposed block | IN_SCOPE | S4-cap-commit |
| bootstrap | genesis block | the chain is initialized for the first time | IN_SCOPE | S4-cap-genesis |
| mint | initial supply | genesis bootstrap runs, once | IN_SCOPE | blockchain::WF_MINT_V0 |
| attest | committed block | deferred — no finalization gate this increment | DEFERRED | S4-design-3 |

---

## 7. Provisional Artifact Codes

*Provisional AC / IN / WF / CC codes (Stage 6b assigns binding FQDNs). Each carries `_V0`. `summary` is business language. Family ∈ AC | IN | WF | CC.*

<!-- register:provisional_codes business_language=summary -->
| Provisional Code | Family (AC, IN, WF, CC) | Summary | Source Finding |
|------------------|-------------------------|---------|----------------|
| IN_COMMIT_BLOCK | IN | admit a request to commit a proposed block to the chain | S4-cap-commit |
| WF_COMMIT_BLOCK | WF | the topology that commits a proposed block and emits the committed signal | S4-cap-commit |
| CC_APPEND_BLOCK | CC | append a committed block to the canonical ledger at the next height | S4-GAP-1 |
| WF_BOOTSTRAP_GENESIS | WF | the one-time topology that writes the genesis block and mints the initial supply | S4-cap-genesis |
| CC_WRITE_GENESIS_BLOCK | CC | write the genesis block at height zero | S4-GAP-2 |
| AC_CHAIN | AC | the authority context under which the chain commits blocks to its ledger | S4-actor-chain |

---

## 8. Cross-Subdomain References

*Capability Contracts defined in another subdomain and referenced by this subdomain's workflows. `cc_code` is the existing FQDN; do not re-document it here.*

<!-- register:cross_subdomain_refs optional business_language=role -->
| CC Code | Defined In | Role | Source Finding |
|---------|------------|------|----------------|
| CC_FORM_BLOCK | consensus_pos | forms the proposed block that the chain commits | blockchain::CC_FORM_BLOCK_V0 |
| EV_BLOCK_COMMITTED | consensus_pos | the committed-block signal WF_COMMIT_BLOCK emits | blockchain::EV_BLOCK_COMMITTED_V0 |

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

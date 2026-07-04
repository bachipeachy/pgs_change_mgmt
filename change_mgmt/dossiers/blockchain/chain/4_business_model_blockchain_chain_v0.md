# Business Model: blockchain / chain
**Domain:** blockchain  
**Subdomain:** chain  
**Version:** V0  
**Status:** DRAFT  
**Pipeline Stage:** Stage 4 — Business Model (canonical artifact)  
**Produced by:** v0.5.0 SDLC authoring pipeline  

---

## Document Contract

**This artifact is a structured register document — not a narrative.**

VALID OUTPUT:
- Populated register tables (every required register below)
- Existing artifact references by exact FQDN — only where a column explicitly permits it
- Business-language capability entries

INVALID OUTPUT:
- Narrative summaries
- Reasoning essays
- Executive summaries
- Free-form prose replacing required registers

A required register with no rows MUST be rendered as a single row:

| NONE IDENTIFIED |

Narrative text does NOT satisfy register population requirements. A prose-only or empty
register is a structural defect, not brevity — the renderer rejects the document mechanically
before any human reviews it.

---

### Business-Language Rule

The following registers MUST NOT contain protocol artifact names or FQDNs:

- Discovery Summary (Actors / Entities / Resources / Events / Relationships)
- Capability Graph
- Gap Register

Capabilities are expressed in **business language only**. Naming solution artifacts here is a
design-leakage defect — protocol FQDNs are introduced at Stage 5 (provisional codes) and
Stage 6b (binding FQDNs), never in the Business Model.

VALID:
- Commit a validated block to the canonical chain
- Initialize the chain from a genesis state

INVALID:
- CC_COMMIT_BLOCK_TO_CHAIN_V0
- WF_RUN_GENESIS_BOOTSTRAP_WORKFLOW_V0

(The Dependency Graph and Authoring Scope MAY cite existing PPS artifacts by FQDN; the
Resolution column of the Gap Register names a disposition — NEW | REUSE | REPLACE — not an
artifact.)

**WHERE FQDNs GO.** When a row is grounded in an existing artifact, the FQDN goes ONLY in that
row's **Source Finding** column — NEVER in a content/description cell (Actor, Role, Entity,
Description, Capability, Subject / Verb / Object, Capability Need). Write the *business meaning* in
the content cell and let the FQDN in Source Finding carry the proof.
INVALID: `Capability Need = "block formation (CC_FORM_BLOCK_V0)"`.
VALID: `Capability Need = "form a block from a proposer and pending transactions"` ·
`Source Finding = artifact_source for blockchain::CC_FORM_BLOCK_V0`. The renderer rejects an FQDN
found in a content cell.

---

### Stage 4 execution rules

- This document **consolidates** Stages 1–3 — it does not re-litigate findings or introduce new design.
- **Every row traces to a prior-stage finding** (the Source Finding column). A row with no
  source is inadmissible — `CONCERN_TRACEABILITY_REQUIRED`.
- **Consistency check:** every CRITICAL row in the Capability Graph has a Gap Register entry
  with an owner subdomain; a capability that requires a NEW artifact in a peer subdomain is a
  GAP owned by that peer (dependency gap), never SATISFIED.
- **State-lifecycle completeness:** every state-lifecycle concern surfaced in Stage 3
  (creation, transition, immutability, persistence, cryptographic linkage, …) MUST appear in
  the Constraint Register OR the Design Decisions register before this stage can complete.

---

## 1. Discovery Summary

*Produced by Stages 1–3 (Input Elicitation → Domain Model Discovery → Analysis Loop). This section is the accumulated output of convergence — do not edit it to make it "cleaner." It is a record of what analysis discovered, not a polished narrative.*

<!-- register:actors business_language -->
### Actors (actors)
| Actor | Role | Authority Class | Source Finding |
|-------|------|-----------------|----------------|
| Proposer | Produces a proposed block in a consensus round. | Producer (upstream of the chain) | S1 business_vocabulary Proposer; S3 dependency EXISTING |
| Chain | Records committed blocks and is authoritative for committed history. | Authoritative owner | S1 authority_boundaries Committed History |
| Genesis Actor | Receives the initial minted supply at bootstrap and owns the mint wallet thereafter. | Permanent system actor | S1 business_vocabulary Genesis Actor |
| Consensus | Decides which blocks are proposed; authoritative for a proposed block until commit. | Authoritative owner (proposed block) | S1 authority_boundaries Proposed Block |

<!-- register:bm_entities business_language -->
### Entities (bm_entities)
| Entity | Description | Store Model | Source Finding |
|--------|-------------|-------------|----------------|
| Chain | The authoritative, ordered, append-only ledger of committed blocks. | An append-only record of committed blocks plus a pointer to the most recent committed block (the head). | S2 entities Chain; S3 gaps chain store |
| Block | A committed unit of the ledger carrying the transactions of its round, linked to its predecessor. | An element of the chain; its content is hashed as its signature at commit. | S2 entities Block |
| Genesis Block | The first block, created once at bootstrap, carrying the initial mint transaction. | The single first element of the chain. | S2 entities Genesis Block |

<!-- register:resources optional business_language -->
### Resources
| Resource | Description | Source Finding |
|----------|-------------|----------------|
| BachiCoin | The system's closed-supply unit of value; total supply is fixed after genesis. | S1 business_vocabulary BachiCoin |
| Wallet balance | A derived quantity computed from committed transactions and reconciled on-chain after commit; not owned by the chain as independent state. | S1 known_facts #11 (human decision) |

<!-- register:events business_language -->
### Events (events)
| Event | Trigger | Lifecycle Meaning | Source Finding |
|-------|---------|-------------------|----------------|
| Genesis Created | The one-time bootstrap, before the consensus loop runs. | Establishes the chain and the initial monetary state. | S1 business_events Genesis Created |
| Block Proposed | A proposer produces a block in a round. | A candidate block exists; not yet authoritative. | S1 business_events Block Proposed |
| Block Committed | A proposed block is committed to the canonical chain. | The block and its transactions become authoritative and immutable. | S1 business_events Block Committed; S3 REUSE (blockchain::EV_BLOCK_COMMITTED_V0) |
| Balance Reconciled | After a block is committed, balances are recomputed from the committed transactions. | Wallet balances become consistent with the canonical committed history. | S1 business_events Balance Reconciled; S3 REUSE (blockchain::EV_BALANCE_RECONCILED_V0) |

*A relationship implies a capability. Name that capability as a **business need** in Capability
Need (business language — no artifact names). If an existing or candidate artifact is relevant,
cite its FQDN in **Source Finding** only — never in the Capability Need cell.*

<!-- register:relationships optional business_language -->
### Relationships (Candidate Capabilities)
| Subject | Verb | Object | Capability Need | Source Finding |
|---------|------|--------|-----------------|----------------|
| Chain | commits | Proposed Block | commit a proposed block to the canonical chain | S3 authoring_decisions AUTHOR_NEW commit |
| Bootstrap | creates | Genesis Block | bootstrap the genesis chain and initialise the supply | S3 authoring_decisions AUTHOR_NEW genesis |
| Chain | reconciles | Wallet balance | reconcile wallet balances from committed transactions after commit | S3 authoring_decisions AUTHOR_NEW reconciliation |

---

## 2. Capability Graph (capability_graph)

*Every capability discovered during Analysis Loop. CRITICAL = must author this CR. ADVISORY = should author. SATISFIED = exists in PPS. Capability column is business language — no FQDNs.*

> **Release boundary.** A capability deferred in `out_of_scope` (S1 §12) is NOT part of this CR — do
> not list it here in any status, and never promote it to a CRITICAL gap. The oracle drops governed
> coverage for a capability row that names a deferred item.

<!-- register:capability_graph business_language -->
| Capability | Source Finding | Status | Gap Register Entry | Notes |
|-----------|----------------|--------|--------------------|-------|
| Commit a proposed block to the canonical chain | S3 authoring_decisions AUTHOR_NEW | CRITICAL | GAP-1 | core CR outcome |
| Store the canonical chain ledger and track its head | S3 authoring_decisions AUTHOR_NEW | CRITICAL | GAP-2 | append-only persistence |
| Validate a block's predecessor link before commit | S3 authoring_decisions AUTHOR_NEW | CRITICAL | GAP-3 | single-predecessor invariant |
| Compute a block's content signature | S3 authoring_decisions AUTHOR_NEW | CRITICAL | GAP-4 | reuses the keccak primitive underneath |
| Bootstrap the genesis chain and initialise the supply | S3 authoring_decisions AUTHOR_NEW | CRITICAL | GAP-5 | one-time, before consensus |
| Reconcile wallet balances after commit | S3 authoring_decisions AUTHOR_NEW | CRITICAL | GAP-6 | realises the derived-balance decision |
| Mint the initial genesis supply | S3 authoring_decisions REUSE; blockchain::WF_MINT_V0 | SATISFIED |  | reused as the genesis mint step |
| Announce that a block was committed | S3 authoring_decisions REUSE; blockchain::EV_BLOCK_COMMITTED_V0 | SATISFIED |  | existing event, emitted by the new commit capability |
| Announce that balances were reconciled | S3 authoring_decisions REUSE; blockchain::EV_BALANCE_RECONCILED_V0 | SATISFIED |  | existing event |
| Record a committed block using the existing block schema | S3 authoring_decisions REUSE; blockchain::ENTITY_BLOCK_V0 | SATISFIED |  | block schema fits exactly |

---

## 3. Dependency Graph (dependency_graph)

*Cross-subdomain dependencies discovered. Declared dependencies constrain authoring order. Existing PPS artifacts MAY be cited by FQDN here.*

<!-- register:dependency_graph -->
| From | To | Dependency Type | PPS Status | Source Finding |
|------|----|-----------------|------------|----------------|
| chain | consensus_pos | data read | SATISFIED | S3 dependency EXISTING; blockchain::WF_PROPOSE_BLOCK_V0 produces the proposed block |
| chain | wallet | capability call | SATISFIED | S3 dependency REUSE; blockchain::WF_MINT_V0 mints the genesis supply |
| chain | transaction | data read | SATISFIED | S3 architectural_observations; balances derived from committed transactions (blockchain::ENTITY_TRANSACTION_V0) |

---

## 4. Constraint Register (constraint_register)

*Non-negotiable rules discovered during analysis. Each constraint has a business source.*

<!-- register:constraint_register -->
| # | Constraint | Source Finding | Source |
|---|-----------|----------------|--------|
| 1 | Closed monetary system — no supply enters or leaves except by the system's own rules. | S1 constraints | governance rule |
| 2 | The chain is immutable — a committed block cannot be altered or removed. | S1 constraints; S1 business_invariants #4 | invariant |
| 3 | Genesis supply is fixed at 1,000,000 BachiCoin, minted to the Genesis Actor at bootstrap. | S1 constraints | domain knowledge |
| 4 | Exactly one genesis block exists per chain, and genesis executes exactly once and is never replayed. | S1 business_invariants #1, #2 | invariant |
| 5 | Total supply is conserved and equals 1,000,000 BachiCoin (no minting or burning after genesis). | S1 business_invariants #3 | invariant |
| 6 | Every committed block has exactly one predecessor, except the genesis block; a block cannot be committed twice. | S1 business_invariants #5, #6 | invariant |
| 7 | The canonical chain is authoritative; a proposed block is not authoritative until committed. | S1 business_invariants #7 | invariant |
| 8 | Wallet balances are derived from committed transactions and reconciled on-chain post-commit; the chain does not own balance state independently. | S1 known_facts #11 (human decision) | domain knowledge |

---

## 5. Gap Register (gap_register)

*All CRITICAL gaps. Each gap must be resolved before authoring begins. Capability is business language; Resolution is a disposition, not an artifact name.*

<!-- register:gap_register business_language -->
| Gap Code | Source Finding | Capability | Owner Subdomain | Resolution |
|----------|----------------|-----------|-----------------|------------|
| GAP-1 | S3 authoring_decisions AUTHOR_NEW; S2 gaps #1 | Commit a proposed block to the canonical chain | chain | NEW |
| GAP-2 | S3 authoring_decisions AUTHOR_NEW; S2 gaps #2 | Store the canonical chain ledger and track its head | chain | NEW |
| GAP-3 | S3 authoring_decisions AUTHOR_NEW; S2 gaps #4 | Validate a block's predecessor link before commit | chain | NEW |
| GAP-4 | S3 analysis_findings Q2 | Compute a block's content signature | chain | NEW |
| GAP-5 | S3 authoring_decisions AUTHOR_NEW; S2 gaps #3 | Bootstrap the genesis chain and initialise the supply | chain | NEW |
| GAP-6 | S3 authoring_decisions AUTHOR_NEW; S1 known_facts #11 | Reconcile wallet balances after commit | chain | NEW |

---

## 6. Design Decisions (design_decisions)

*Decisions accumulated during Stages 1–3 that constrain Design Intent. Each decision locks in an architectural choice.*

<!-- register:design_decisions -->
| # | Decision | Source Finding | Rationale | Constraints Imposed |
|---|----------|----------------|-----------|---------------------|
| 1 | The commit path is a new capability that runs downstream of block proposal and records a proposed block as canonical. | S3 authoring_decisions AUTHOR_NEW commit | No commit capability exists; the chain plugs in directly after proposal. | Realises the proposed→committed transition. |
| 2 | The canonical chain is an append-only store with a head pointer; committed blocks are never mutated or removed. | S3 authoring_decisions AUTHOR_NEW chain store | Immutability and single-predecessor invariants require durable, append-only persistence. | Append-only persistence; no in-place mutation. |
| 3 | A block's content signature is computed by a new block-canonical hash transform that reuses the generic keccak primitive. | S3 analysis_findings Q2 | No block hash exists; cryptographic linkage is required at commit. | Signature computed at commit as the block's identity. |
| 4 | The predecessor link is validated against the current chain head before a block is committed. | S3 analysis_findings Q3 | Enforces exactly one predecessor per committed block. | Commit rejects a block whose predecessor does not match the head. |
| 5 | Genesis is a one-time bootstrap that reuses minting to initialise the supply before the consensus loop runs. | S3 authoring_decisions AUTHOR_NEW genesis + REUSE mint | Genesis-once invariant; reuse minting rather than a new monetary mechanism. | Genesis executes once, never replayed. |
| 6 | Wallet balances are derived and reconciled on-chain after commit; the chain does not own balance state. | S1 known_facts #11 (human decision) | The human's authority decision at the S2 design review. | Balances derived from committed transactions; reconciliation is a post-commit process. |
| 7 | Every proposed block is committed directly this increment; attestation and finalization are deferred. | S1 assumptions; S1 out_of_scope | Incremental development decision. | No rejection path; no attest/finalize step. |

---

## 7. Authoring Scope (authoring_scope)

*What is IN this CR vs. FUTURE CR. This is the governance boundary decision that filters the Business Model into the Business Intent.*

<!-- register:authoring_scope -->
### In Scope — This CR
| Capability | Gap Register Ref |
|-----------|-----------------|
| Commit a proposed block to the canonical chain | GAP-1 |
| Store the canonical chain ledger and track its head | GAP-2 |
| Validate a block's predecessor link before commit | GAP-3 |
| Compute a block's content signature | GAP-4 |
| Bootstrap the genesis chain and initialise the supply | GAP-5 |
| Reconcile wallet balances after commit | GAP-6 |

### Deferred — Future CR
| Capability | Deferred Reason |
|-----------|-----------------|

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 1 — Change Request & Input Elicitation | Classification + Problem + Outcome + Known Facts | COMPLETE |
| Stage 2 — Domain Model Discovery | Actors, Entities, Resources, Events, Relationships | COMPLETE |
| Stage 3 — Analysis Loop | Capability Graph, Dependency Graph, Constraints, Gap Register | COMPLETE — SATURATED |
| Stage 4 — Business Model | This document | COMPLETE |
| Stage 4b — Authoring Scope | IN/FUTURE CR boundary | PENDING |

---

## gov_projection — Governed Handoff to Stage 5

*Governed, lossless, identity-preserving (defined in Stage 0 / field manual §4.7). Every identity and concern in a **Consumes** field reappears in the corresponding **Emits** field transform-free, unless explicitly deferred with a recorded reason; no field is dropped silently. Emit keys match the register ids above exactly.*

*S4 is the hub — it consolidates Stages 1–3. The bounded inputs below mirror the engine's
gov_projection schema exactly (`contracts/gov_projection.py`).*

| Direction | Fields |
|-----------|--------|
| **Consumes** ← Stage 1 | cr_type · constraints · business_invariants · authority_boundaries · out_of_scope |
| **Consumes** ← Stage 2 | entities · entity_attributes · business_processes · pps_baseline_fqdns |
| **Consumes** ← Stage 3 | authoring_decisions · dependency_discoveries · placement_decision · saturation |
| **Emits** → Stage 5 | actors · bm_entities · events · capability_graph · dependency_graph · constraint_register · gap_register · design_decisions · authoring_scope |

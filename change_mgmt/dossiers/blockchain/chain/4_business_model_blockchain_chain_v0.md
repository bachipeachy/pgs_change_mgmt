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
| Genesis Actor | Receives the initial minted supply at bootstrap and owns the MINT wallet thereafter. | SYSTEM | S1 vocab; S2 entity Genesis Actor |
| Proposer | Validator selected per round to produce a proposed block that the chain then commits. | SYSTEM | S2 entity Proposer |

<!-- register:bm_entities business_language -->
### Entities (bm_entities)
| Entity | Description | Store Model | Source Finding |
|--------|-------------|-------------|----------------|
| Chain | The authoritative append-only ledger of committed blocks that serves as canonical history. | append-only ledger of committed blocks; lifecycle Uninitialized -> Active | S2 entity: Chain |
| Block | A unit of the ledger produced by a proposer, carrying the transactions of its round. | immutable once committed (append-only canonical record); transient while proposed | S2 entity: Block |
| Proposed Block | A block produced in the consensus loop that is not yet committed and not authoritative. | transient pre-commit candidate (Proposed lifecycle state) | S2 entity: Proposed Block |
| Genesis Block | The chain's first block, containing the initial mint to the Genesis Actor; created once at bootstrap. | first committed block of the canonical ledger (Created Once) | S2 entity: Genesis Block |
| Genesis Actor | The permanent actor receiving the initial minted supply and owning the MINT wallet thereafter. | actor record with permanent minting authority at genesis | S2 entity: Genesis Actor |
| BachiCoin | The system's unit of value; a closed monetary supply conserved at 1,000,000 total. | balance tracked in wallet records | S2 entity: BachiCoin |
| Proposer | The validator selected to produce a block in a given round. | validator record selected per round by eligibility | S2 entity: Proposer |

<!-- register:resources optional business_language -->
### Resources
| Resource | Description | Source Finding |
|----------|-------------|----------------|
| NONE IDENTIFIED |  |  |

<!-- register:events business_language -->
### Events (events)
| Event | Trigger | Lifecycle Meaning | Source Finding |
|-------|---------|-------------------|----------------|
| Genesis Created | Once, at bootstrap, before the consensus loop runs. | Establishes the chain and the initial monetary state. | S1 business_events |
| Block Proposed | A proposer produces a block in a round. | A candidate block exists; not yet authoritative. | S1 business_events |
| Block Committed | A proposed block is committed to the canonical chain. | The block and its transactions become authoritative and immutable. | S1 business_events |

*A relationship implies a capability. Name that capability as a **business need** in Capability
Need (business language — no artifact names). If an existing or candidate artifact is relevant,
cite its FQDN in **Source Finding** only — never in the Capability Need cell.*

<!-- register:relationships optional business_language -->
### Relationships (Candidate Capabilities)
| Subject | Verb | Object | Capability Need | Source Finding |
|---------|------|--------|-----------------|----------------|
| NONE IDENTIFIED |  |  |  |  |

---

## 2. Capability Graph (capability_graph)

*Every capability discovered during Analysis Loop. CRITICAL = must author this CR. ADVISORY = should author. SATISFIED = exists in PPS. Capability column is business language — no FQDNs.*

> **Release boundary.** A capability deferred in `out_of_scope` (S1 §12) is NOT part of this CR — do
> not list it here in any status, and never promote it to a CRITICAL gap. The oracle drops governed
> coverage for a capability row that names a deferred item.

<!-- register:capability_graph business_language -->
| Capability | Source Finding | Status | Gap Register Entry | Notes |
|-----------|----------------|--------|--------------------|-------|
| Commit a proposed block to the canonical chain (immutable, authoritative) | S3 AUTHOR_NEW commit; S2 belief #1 | CRITICAL | GAP-1 | Author the commit operation; it emits the already-existing committed-block event. |
| Bootstrap the chain from a genesis block and mint the initial supply | S3 AUTHOR_NEW genesis; S2 gap genesis | CRITICAL | GAP-2 | Author a one-time bootstrap workflow run before the consensus loop. |
| Append committed blocks to the canonical chain store | S3 EXTEND storage | ADVISORY | GAP-3 | Extend the existing append-only block store with commit semantics; no new store. |
| Record that a block has been committed | S3 REUSE event (blockchain::EV_BLOCK_COMMITTED_V0) | SATISFIED |  | Reuse the existing committed-block event; the commit operation emits it. |
| Run the consensus loop that proposes blocks each round | S3 REUSE consensus (blockchain::RB_RUN_CONSENSUS_LOOP_V0) | SATISFIED |  | Reused unchanged; produces the proposed blocks the chain commits. |
| Produce a proposed block for the round | S3 REUSE proposal (blockchain::CC_INVOKE_BLOCK_PROPOSAL_V0) | SATISFIED |  | Reused unchanged; the input to commit. |
| Select the proposer from eligible validators | S3 REUSE proposer (blockchain::CC_QUERY_ELIGIBLE_VALIDATORS_V0) | SATISFIED |  | Reused unchanged. |
| Mint the initial BachiCoin supply at genesis | S3 REUSE mint (blockchain::RB_MINT_V0) | SATISFIED |  | Reused by the genesis bootstrap to mint the fixed 1,000,000 supply. |
| Create the MINT wallet for the Genesis Actor | S3 REUSE wallet (blockchain::RB_CREATE_WALLET_V0) | SATISFIED |  | Reused at genesis. |
| Register the permanent Genesis Actor | S3 REUSE actor (blockchain::RB_REGISTER_ACTOR_UNVERIFIED_V0) | SATISFIED |  | Reused to establish the Genesis Actor. |

---

## 3. Dependency Graph (dependency_graph)

*Cross-subdomain dependencies discovered. Declared dependencies constrain authoring order. Existing PPS artifacts MAY be cited by FQDN here.*

<!-- register:dependency_graph -->
| From | To | Dependency Type | PPS Status | Source Finding |
|------|----|-----------------|------------|----------------|
| chain | consensus_pos | event | SATISFIED | blockchain::RB_RUN_CONSENSUS_LOOP_V0 produces proposed blocks |
| chain | wallet | capability | SATISFIED | blockchain::RB_CREATE_WALLET_V0 reused for the MINT wallet |
| chain | identity | capability | SATISFIED | blockchain::RB_REGISTER_ACTOR_UNVERIFIED_V0 reused for the Genesis Actor |
| chain | orchestration | control | SATISFIED | consensus loop is driven by orchestration; commit invoked per round |

---

## 4. Constraint Register (constraint_register)

*Non-negotiable rules discovered during analysis. Each constraint has a business source.*

<!-- register:constraint_register -->
| # | Constraint | Source Finding | Source |
|---|-----------|----------------|--------|
| 1 | Closed monetary system — no supply enters or leaves except by the system's own rules. | CR Seed Sec7.1 | Business policy |
| 2 | The chain is immutable — a committed block cannot be altered or removed. | CR Seed Sec7.2 / Sec8.#4 | Business policy |
| 3 | Genesis supply fixed at 1,000,000 BachiCoin, minted to the Genesis Actor at bootstrap. | CR Seed Sec7.3 / Sec4.#3 | Business policy |
| 4 | Exactly one genesis block; genesis executes exactly once and is never replayed. | CR Seed Sec8.#1,#2 | Business invariant |
| 5 | Every committed block has exactly one predecessor, except the genesis block. | CR Seed Sec8.#5 | Business invariant |
| 6 | A block cannot be committed twice. | CR Seed Sec8.#6 | Business invariant |

---

## 5. Gap Register (gap_register)

*All CRITICAL gaps. Each gap must be resolved before authoring begins. Capability is business language; Resolution is a disposition, not an artifact name.*

<!-- register:gap_register business_language -->
| Gap Code | Source Finding | Capability | Owner Subdomain | Resolution |
|----------|----------------|-----------|-----------------|------------|
| GAP-1 | S3 AUTHOR_NEW; S2 gap commit | Commit a proposed block to the canonical chain | chain | NEW |
| GAP-2 | S3 AUTHOR_NEW; S2 gap genesis | Bootstrap the chain from genesis and mint the initial supply | chain | NEW |
| GAP-3 | S3 EXTEND storage | Append committed blocks to the canonical chain store | chain | EXTEND |

---

## 6. Design Decisions (design_decisions)

*Decisions accumulated during Stages 1–3 that constrain Design Intent. Each decision locks in an architectural choice.*

<!-- register:design_decisions -->
| # | Decision | Source Finding | Rationale | Constraints Imposed |
|---|----------|----------------|-----------|---------------------|
| 1 | The commit operation emits the existing committed-block event (blockchain::EV_BLOCK_COMMITTED_V0) rather than a new event. | S2 belief #1 evidence | The event already exists; only the operation is missing. | Commit must populate the existing event contract. |
| 2 | Attest, Finalize, Fork resolution, Chain reorg, Slashing, and Rewards are deferred (out of scope). | S1 out_of_scope; S2 discovery_concerns | Incremental release; every proposed block is committed directly. | No finalization gate; no rejection path; commit every proposed block. |
| 3 | Genesis bootstrap runs exactly once, before the consensus loop, and is never replayed. | S1 invariants Sec8.#1,#2 | Genesis establishes the chain and fixed supply. | Bootstrap is a one-time entry point; not part of the per-round loop. |
| 4 | Reuse the existing append-only chain storage (EXTEND), not a new store. | S2 pps_baseline blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0 | Storage exists but lacks commit semantics. | Commit writes through the existing storage structure. |

---

## 7. Authoring Scope (authoring_scope)

*What is IN this CR vs. FUTURE CR. This is the governance boundary decision that filters the Business Model into the Business Intent.*

<!-- register:authoring_scope -->
### In Scope — This CR
| Capability | Gap Register Ref |
|-----------|-----------------|
| Commit a proposed block to the canonical chain | GAP-1 |
| Bootstrap the chain from genesis and mint the initial supply | GAP-2 |
| Append committed blocks to the canonical chain store | GAP-3 |

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

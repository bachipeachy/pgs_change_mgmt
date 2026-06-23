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
| Genesis Actor | Initial bootstrap authority that receives genesis supply at chain initialization | bootstrap_authority | CR seed §1 CR Type: Genesis creates initial monetary state; blockchain::AC_SYSTEM_V0 for system-level operations |
| Validator | Participates in consensus rounds by proposing and attesting to blocks | consensus_participant | blockchain::RB_REGISTER_VALIDATOR_V0; blockchain::CC_QUERY_ELIGIBLE_VALIDATORS_V0 |
| Enduser | Submits transactions and interacts with the canonical ledger for value transfers | ledger_participant | blockchain::AC_ENDUSER_V0; blockchain::WF_SUBMIT_TRANSACTION_V0 |
| System | Performs system-level operations including block commitment and chain state maintenance | system_operator | blockchain::AC_SYSTEM_V0; blockchain::RB_PROPOSE_BLOCK_V0 |

<!-- register:bm_entities business_language -->
### Entities (bm_entities)
| Entity | Description | Store Model | Source Finding |
|--------|-------------|-------------|----------------|
| Block Record | Immutable record of a committed block containing transactions, proposer information, and cryptographic linkage to predecessor | immutable_store | blockchain::CC_FORM_BLOCK_V0; blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0 |
| Consensus Round History | Historical record of consensus rounds including proposer selections, attestations, and round outcomes | immutable_store | blockchain::CC_RECORD_CONSENSUS_ROUND_V0; blockchain::RB_PROPOSE_BLOCK_V0 |
| Chain State Ledger | Current authoritative state of the canonical ledger including committed block history and wallet balances | immutable_store | blockchain::CC_FORM_BLOCK_V0; blockchain::RB_PROPOSE_BLOCK_V0 |
| Block Events Journal | Append-only journal of block lifecycle events including commitment and finalization records | append_only_store | blockchain::CC_APPENDONLY_JSONL_V0; blockchain::EV_BLOCK_COMMITTED_V0 |

<!-- register:resources optional business_language -->
### Resources
| Resource | Description | Source Finding |
|----------|-------------|----------------|
| Blockchain Storage Structure | Storage infrastructure supporting BLOCKS, BLOCK_EVENTS, and other chain subdomain stores with immutable access patterns | blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0 |
| Mutable JSON Store Access | Capability for writing to mutable blockchain state including block records and ledger entries | CS_MUTABLE_JSON_V0; blockchain::RB_PROPOSE_BLOCK_V0 |
| Append-Only Event Journal | Immutable event logging capability for recording chain lifecycle events without modification or deletion | CS_APPENDONLY_JSONL_V0; blockchain::CC_FORM_BLOCK_V0 |

<!-- register:events business_language -->
### Events (events)
| Event | Trigger | Lifecycle Meaning | Source Finding |
|-------|---------|-------------------|----------------|
| Genesis Completed | Chain bootstrap operation completes genesis block creation and initial state initialization | Marks the single genesis execution that establishes canonical chain, immutability constraints, and fixed supply of 1 million BachiCoin | CR seed §8 Business Invariants #2; blockchain::AC_SYSTEM_V0 |
| Block Committed to Canonical Chain | Consensus round concludes with block attestation and commitment decision | Proposed block becomes immutable history on the canonical ledger, establishing cryptographic linkage to predecessor block | blockchain::EV_BLOCK_COMMITTED_V0; blockchain::CC_FORM_BLOCK_V0 |
| Round Skipped | No eligible proposer or failed proposal in consensus round | Consensus round produces no committed block, advancing to next slot while preserving chain continuity | blockchain::CC_SKIP_ROUND_V0; blockchain::WF_PROPOSE_BLOCK_V0 |

*A relationship implies a capability. Name that capability as a **business need** in Capability
Need (business language — no artifact names). If an existing or candidate artifact is relevant,
cite its FQDN in **Source Finding** only — never in the Capability Need cell.*

<!-- register:relationships optional business_language -->
### Relationships (Candidate Capabilities)
| Subject | Verb | Object | Capability Need | Source Finding |
|---------|------|--------|-----------------|----------------|
| Genesis Actor | receives initial supply from | Chain at bootstrap | create genesis block and initialize canonical ledger state with fixed 1 million BachiCoin supply | CR seed §7 Constraints #3; blockchain::AC_SYSTEM_V0 |
| Validator | participates in consensus rounds to propose and attest blocks for | Chain state maintenance | select proposer, form block from pending transactions, record round outcome including skip or commit decision | blockchain::CC_QUERY_ELIGIBLE_VALIDATORS_V0; blockchain::CC_SELECT_PROPOSER_V0 |
| Enduser | submits transactions to be included in blocks for | Chain state updates via committed block formation | collect pending transactions, form proposed block with transaction set, commit to canonical chain immutably | blockchain::CC_QUERY_PENDING_TRANSACTIONS_V0; blockchain::CC_FORM_BLOCK_V0 |
| System | commits blocks and maintains ledger state for | Canonical chain history | commit proposed block to immutable canonical chain, enforce immutability constraints on committed blocks | blockchain::EV_BLOCK_COMMITTED_V0; blockchain::RB_PROPOSE_BLOCK_V0 |

---

## 2. Capability Graph (capability_graph)

*Every capability discovered during Analysis Loop. CRITICAL = must author this CR. ADVISORY = should author. SATISFIED = exists in PPS. Capability column is business language — no FQDNs.*

<!-- register:capability_graph business_language -->
| Capability | Source Finding | Status | Gap Register Entry | Notes |
|-----------|----------------|--------|--------------------|-------|
| create genesis block at bootstrap | CR seed §8 Business Invariants #1,2,3; authoring_decisions: Genesis creation is distinct one-time operation separate from regular consensus operations | CRITICAL | GAP-001 |  |
| commit block to canonical chain immutably | blockchain::EV_BLOCK_COMMITTED_V0 exists but has zero consumers; CR seed §8 Business Invariants #4,6,7 require actual commit operation for committed blocks | CRITICAL | GAP-002 |  |
| maintain chain state after genesis with supply conservation | blockchain::CC_FORM_BLOCK_V0 handles proposed blocks only; CR seed §7 Constraints #1 and Business Invariants #3 require post-genesis supply conservation enforcement | CRITICAL | GAP-003 |  |
| record consensus round outcome including skip decisions | blockchain::CC_RECORD_CONSENSUS_ROUND_V0; blockchain::CC_SKIP_ROUND_V0 exists for skipping rounds during proposal workflow | SATISFIED |  |  |
| append block lifecycle events to immutable journal | blockchain::CS_APPENDONLY_JSONL_V0 bound via blockchain::RB_PROPOSE_BLOCK_V0; blockchain::CC_FORM_BLOCK_V0 already appends proposed block events | SATISFIED |  |  |
| write committed blocks to immutable BLOCKS store | blockchain::CS_MUTABLE_JSON_V0 available but needs commit-specific binding; blockchain::CC_FORM_BLOCK_V0 writes proposed blocks not commits | CRITICAL | GAP-004 |  |

---

## 3. Dependency Graph (dependency_graph)

*Cross-subdomain dependencies discovered. Declared dependencies constrain authoring order. Existing PPS artifacts MAY be cited by FQDN here.*

<!-- register:dependency_graph -->
| From | To | Dependency Type | PPS Status | Source Finding |
|------|----|-----------------|------------|----------------|
| chain subdomain genesis creation capability | blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0 | storage structure reuse | SATISFIED | upstream handoff: dependency_discoveries storage EXISTING |
| chain subdomain block commitment capability | blockchain::CS_APPENDONLY_JSONL_V0 | capability side effect reuse for event journaling | SATISFIED | upstream handoff: dependency_discoveries append-only REUSE via blockchain::RB_PROPOSE_BLOCK_V0 |
| chain subdomain state maintenance capability | blockchain::CS_MUTABLE_JSON_V0 | capability side effect reuse for mutable store access | SATISFIED | upstream handoff: dependency_discoveries mutable JSON REUSE via blockchain::RB_PROPOSE_BLOCK_V0 |
| chain subdomain block commitment capability | blockchain::EV_BLOCK_COMMITTED_V0 | event emission contract for committed blocks | SATISFIED | upstream handoff: dependency_discoveries event code EV_BLOCK_COMMITTED_V0 |
| chain subdomain genesis creation capability | blockchain::AC_SYSTEM_V0 | actor authority for system-level bootstrap operations | SATISFIED | CR seed §1 CR Type; blockchain::AC_SYSTEM_V0 exists in PPS |

---

## 4. Constraint Register (constraint_register)

*Non-negotiable rules discovered during analysis. Each constraint has a business source.*

<!-- register:constraint_register -->
| # | Constraint | Source Finding | Source |
|---|-----------|----------------|--------|
| 1 | Closed monetary system — no supply enters or leaves except by the system's own rules | CR seed §7 Constraints #1; blockchain::CC_VALIDATE_MINT_POLICY_V0 for mint policy enforcement |  |
| 2 | The chain is immutable — a committed block cannot be altered or removed | CR seed §7 Constraints #2; CR seed §8 Business Invariants #4 on immutability of committed blocks |  |
| 3 | Genesis supply is fixed at 1 million BachiCoin minted to Genesis Actor at bootstrap | CR seed §7 Constraints #3; blockchain::AC_SYSTEM_V0 for system-level genesis operations |  |
| 4 | Exactly one genesis block exists per chain and executes exactly once at bootstrap never replayed | CR seed §8 Business Invariants #1,2; blockchain::AC_SYSTEM_V0 for system-level single-execution semantics |  |
| 5 | Total supply is conserved and equals 1 million BachiCoin with no minting or burning after genesis | CR seed §8 Business Invariants #3; blockchain::CC_VALIDATE_MINT_POLICY_V0 for post-genesis conservation |  |
| 6 | A committed block has exactly one predecessor except the genesis block | CR seed §8 Business Invariants #5; blockchain::CC_FORM_BLOCK_V0 establishes single-predecessor linkage in proposed blocks |  |
| 7 | A committed block cannot be committed twice to the canonical chain | CR seed §8 Business Invariants #6; blockchain::EV_BLOCK_COMMITTED_V0 for commit event uniqueness semantics |  |

---

## 5. Gap Register (gap_register)

*All CRITICAL gaps. Each gap must be resolved before authoring begins. Capability is business language; Resolution is a disposition, not an artifact name.*

<!-- register:gap_register business_language -->
| Gap Code | Source Finding | Capability | Owner Subdomain | Resolution |
|----------|----------------|-----------|-----------------|------------|
| GAP-001 | authoring_decisions: Genesis creation is distinct one-time operation separate from regular consensus operations; CR seed §8 Business Invariants #1,2 require genesis block capability | create genesis block at bootstrap and initialize canonical ledger state with fixed supply | chain | NEW |
| GAP-002 | blockchain::EV_BLOCK_COMMITTED_V0 exists but has zero consumers; CR seed §8 Business Invariants #4,6 require actual commit operation for committed blocks to canonical chain | commit proposed block immutably to canonical chain history with cryptographic linkage enforcement | chain | NEW |
| GAP-003 | blockchain::CC_FORM_BLOCK_V0 handles proposed blocks only; CR seed §7 Constraints #1 and Business Invariants #3 require post-genesis supply conservation enforcement capability | maintain chain state after genesis with closed monetary system constraints including supply conservation validation | chain | NEW |
| GAP-004 | blockchain::CS_MUTABLE_JSON_V0 available but needs commit-specific binding; blockchain::CC_FORM_BLOCK_V0 writes proposed blocks not commits to canonical chain | write committed block records to immutable BLOCKS store with single-predecessor constraint enforcement | chain | NEW |

---

## 6. Design Decisions (design_decisions)

*Decisions accumulated during Stages 1–3 that constrain Design Intent. Each decision locks in an architectural choice.*

<!-- register:design_decisions -->
| # | Decision | Source Finding | Rationale | Constraints Imposed |
|---|----------|----------------|-----------|---------------------|
| 1 | Genesis block creation is a distinct one-time operation separate from regular consensus operations | authoring_decisions: Genesis creates initial monetary state; blockchain::AC_SYSTEM_V0 for system-level bootstrap semantics | No existing artifact handles genesis creation. Genesis establishes canonical chain, immutability constraints, and fixed supply of 1 million BachiCoin at single execution point. | Requires dedicated capability with no replay; enforces exactly-one-execution invariant |
| 2 | Block commitment to canonical chain requires new RB/CC pair in chain subdomain | blockchain::EV_BLOCK_COMMITTED_V0 (exists, zero consumers per topology_impact); blockchain::RB_PROPOSE_BLOCK_V0 handles proposal not commitment; CR seed §8 Business Invariants #4 require actual commit operation | Existing EV_BLOCK_COMMITTED_V0 has no supporting runtime binding or capability contract for actual commit. Need new RB/CC pair to implement immutably committing blocks. | Commit operation must enforce single-predecessor constraint and immutable write semantics |
| 3 | Chain state maintenance after genesis requires dedicated capability for supply conservation | blockchain::CC_FORM_BLOCK_V0 (forms proposed blocks only); blockchain::RB_PROPOSE_BLOCK_V0 handles consensus_pos operations; CR seed §7 Constraints #1 and Business Invariants #3 require post-genesis closed monetary system enforcement | No existing artifacts manage committed block history or enforce post-genesis supply conservation. Need new capability to maintain canonical ledger with immutability constraints. | State maintenance must validate no minting/burning after genesis and preserve total supply invariant |
| 4 | Reuse existing storage structure for chain subdomain stores | upstream handoff: dependency_discoveries blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0 EXISTING; CR seed §1 placement_decision NEW_SUBDOMAIN with shared infrastructure reuse | Blockchain storage structure already provides BLOCKS, BLOCK_EVENTS and other chain subdomain stores. Reuse avoids duplication. | New capabilities must declare store paths resolved from STRUCTURE_BLOCKCHAIN_STORAGE_V0 |
| 5 | Reuse existing append-only event journal capability for block lifecycle events | upstream handoff: dependency_discoveries CS_APPENDONLY_JSONL_V0 REUSE via blockchain::RB_PROPOSE_BLOCK_V0; CR seed §1 placement_decision with common infrastructure reuse | Append-only JSONL store already bound for consensus rounds and block events. Reuse provides immutable event logging without new artifacts. | Block commitment capability must append to BLOCK_EVENTS using existing CS_APPENDONLY_JSONL_V0 binding |
| 6 | Reuse existing mutable JSON store access for chain state writes | upstream handoff: dependency_discoveries CS_MUTABLE_JSON_V0 REUSE via blockchain::RB_PROPOSE_BLOCK_V0; CR seed §1 placement_decision with common infrastructure reuse | Mutable JSON store already bound and available for chain state writes. Reuse provides write capability without new artifacts. | Genesis creation and block commitment capabilities must use CS_MUTABLE_JSON_V0 for BLOCKS store access |

---

## 7. Authoring Scope (authoring_scope)

*What is IN this CR vs. FUTURE CR. This is the governance boundary decision that filters the Business Model into the Business Intent.*

<!-- register:authoring_scope -->
### In Scope — This CR
| Capability | Gap Register Ref |
|-----------|-----------------|
| create genesis block at bootstrap | GAP-001 |
| commit blocks to canonical chain immutably | GAP-002, GAP-004 |
| maintain chain state with supply conservation after genesis | GAP-003 |

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
| **Consumes** ← Stage 1 | cr_type · constraints · business_invariants · authority_boundaries |
| **Consumes** ← Stage 2 | entities · entity_attributes · business_processes · pps_baseline_fqdns |
| **Consumes** ← Stage 3 | authoring_decisions · dependency_discoveries · placement_decision · saturation |
| **Emits** → Stage 5 | actors · bm_entities · events · capability_graph · dependency_graph · constraint_register · gap_register · design_decisions · authoring_scope |

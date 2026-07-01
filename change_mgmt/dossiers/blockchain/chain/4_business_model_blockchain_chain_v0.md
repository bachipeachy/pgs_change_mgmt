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
| Proposer | forms and proposes the next block from mempool transactions | SYSTEM | S2-E-proposer |
| Validator | participates in the consensus round that closes a slot | SYSTEM | S2-belief-4 |
| Genesis Actor | the one-time bootstrap authority that seeds the ledger and initial supply | SYSTEM | S2-E-genesis |
| Chain | owns the canonical ledger and commits proposed blocks to it | SYSTEM | S3-place-1 |

<!-- register:bm_entities business_language -->
### Entities (bm_entities)
| Entity | Description | Store Model | Source Finding |
|--------|-------------|-------------|----------------|
| Canonical Chain | the immutable append-only ledger of committed blocks — the source of truth this subdomain owns | append-only ledger store | S3-dep-5 |
| Committed Block | a proposed block once committed to the canonical chain; permanent and ordered | append-only record in the ledger | S3-C1 |
| Proposed Block | a block formed by the proposer from mempool transactions, awaiting commit — produced upstream, consumed here | consumed record (not owned) | S2-E-proposed-block |
| Genesis Block | the first block, written once at bootstrap to anchor the chain | append-only record in the ledger | S2-E-genesis-block |
| BachiCoin | the fixed initial supply minted once at genesis under the existing mint policy | reused mint policy (not owned) | S2-E-bachicoin |

<!-- register:resources optional business_language -->
### Resources
| Resource | Description | Source Finding |
|----------|-------------|----------------|
| NONE IDENTIFIED |  |  |

<!-- register:events business_language -->
### Events (events)
| Event | Trigger | Lifecycle Meaning | Source Finding |
|-------|---------|-------------------|----------------|
| Block Committed | the chain commits a proposed block to the canonical ledger | the ledger advances by one permanent block | S3-reuse-committed-event |
| Genesis Created | the one-time bootstrap writes the genesis block and mints the initial supply | the chain is anchored and the closed supply established | S2-E-genesis |

*A relationship implies a capability. Name that capability as a **business need** in Capability
Need (business language — no artifact names). If an existing or candidate artifact is relevant,
cite its FQDN in **Source Finding** only — never in the Capability Need cell.*

<!-- register:relationships optional business_language -->
### Relationships (Candidate Capabilities)
| Subject | Verb | Object | Capability Need | Source Finding |
|---------|------|--------|-----------------|----------------|
| Chain | commits | Proposed Block | commit a proposed block to the canonical chain | S3-C1 |
| Genesis Actor | bootstraps | Canonical Chain | bootstrap genesis and mint the initial supply once | S3-C2 |
| Chain | reuses | mint policy | mint supply under policy | S3-reuse-mint |

---

## 2. Capability Graph (capability_graph)

*Every capability discovered during Analysis Loop. CRITICAL = must author this CR. ADVISORY = should author. SATISFIED = exists in PPS. Capability column is business language — no FQDNs.*

> **Release boundary.** A capability deferred in `out_of_scope` (S1 §12) is NOT part of this CR — do
> not list it here in any status, and never promote it to a CRITICAL gap. The oracle drops governed
> coverage for a capability row that names a deferred item.

<!-- register:capability_graph business_language -->
| Capability | Source Finding | Status | Gap Register Entry | Notes |
|-----------|----------------|--------|--------------------|-------|
| commit a proposed block to the canonical chain | S3-C1 | CRITICAL | GAP-1 | the core gap — no capability commits a proposed block to a ledger today |
| bootstrap genesis and mint the initial supply once | S3-C2 | CRITICAL | GAP-2 | one-time startup sequence; invokes the existing mint policy |
| the canonical ledger store for committed blocks | S3-C3 | CRITICAL | GAP-3 | committed history has no authoritative store today |
| form a proposed block from mempool transactions | blockchain::CC_FORM_BLOCK_V0 | REUSE |  | block-proposal already forms blocks; the chain consumes its output |
| mint supply under policy | blockchain::WF_MINT_V0 | REUSE |  | genesis bootstrap invokes the existing mint policy once |
| signal that a block was committed | blockchain::EV_BLOCK_COMMITTED_V0 | REUSE |  | the committed-block event exists; the new commit capability emits it |

---

## 3. Dependency Graph (dependency_graph)

*Cross-subdomain dependencies discovered. Declared dependencies constrain authoring order. Existing PPS artifacts MAY be cited by FQDN here.*

<!-- register:dependency_graph -->
| From | To | Dependency Type | PPS Status | Source Finding |
|------|----|-----------------|------------|----------------|
| chain | consensus_pos | consumes proposed block | SATISFIED | blockchain::WF_PROPOSE_BLOCK_V0 |
| chain | mempool | consumes transactions carried in a block | SATISFIED | blockchain::CC_CLAIM_MEMPOOL_TXS_V0 |
| chain | wallet | invokes mint policy at genesis | SATISFIED | blockchain::WF_MINT_V0 |
| chain | consensus_pos | emits committed-block signal | SATISFIED | blockchain::EV_BLOCK_COMMITTED_V0 |

---

## 4. Constraint Register (constraint_register)

*Non-negotiable rules discovered during analysis. Each constraint has a business source.*

<!-- register:constraint_register -->
| # | Constraint | Source Finding | Source |
|---|-----------|----------------|--------|
| 1 | the canonical chain is immutable and append-only — committed blocks are never rewritten | S1-K-immutable | governance rule |
| 2 | the monetary supply is closed — total supply is fixed and minted only once at genesis | S1-K-closed-supply | governance rule |
| 3 | a single committed-block signal — the commit capability emits the existing event, never a duplicate | S3-reuse-committed-event | analysis decision |

---

## 5. Gap Register (gap_register)

*All CRITICAL gaps. Each gap must be resolved before authoring begins. Capability is business language; Resolution is a disposition, not an artifact name.*

<!-- register:gap_register business_language -->
| Gap Code | Source Finding | Capability | Owner Subdomain | Resolution |
|----------|----------------|-----------|-----------------|------------|
| GAP-1 | S3-C1 | commit a proposed block to the canonical chain | chain | NEW |
| GAP-2 | S3-C2 | bootstrap genesis and mint the initial supply once | chain | NEW |
| GAP-3 | S3-C3 | the canonical ledger store for committed blocks | chain | NEW |

---

## 6. Design Decisions (design_decisions)

*Decisions accumulated during Stages 1–3 that constrain Design Intent. Each decision locks in an architectural choice.*

<!-- register:design_decisions -->
| # | Decision | Source Finding | Rationale | Constraints Imposed |
|---|----------|----------------|-----------|---------------------|
| 1 | the chain is a new subdomain that owns committed history | S3-place-1 | the canonical ledger is a distinct concern from block proposal and is not an extension of an existing subdomain | chain owns the ledger store; proposal stays upstream in consensus |
| 2 | reuse block-proposal, the mint policy and the committed-block event rather than author duplicates | S3-reuse-form-block | these capabilities exist and are verified; duplicating them would fork consensus, break the single-supply invariant, or split the committed signal | chain consumes upstream outputs; single minting path; single committed event |
| 3 | attestation and finalization are out of scope; every committed block is treated as good | S1-out-of-scope | the CR scope excludes a finalization gate for this increment | no finalization or slashing capability is modeled |

---

## 7. Authoring Scope (authoring_scope)

*What is IN this CR vs. FUTURE CR. This is the governance boundary decision that filters the Business Model into the Business Intent.*

<!-- register:authoring_scope -->
### In Scope — This CR
| Capability | Gap Register Ref |
|-----------|-----------------|
| commit a proposed block to the canonical chain | GAP-1 |
| bootstrap genesis and mint the initial supply once | GAP-2 |
| the canonical ledger store for committed blocks | GAP-3 |

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

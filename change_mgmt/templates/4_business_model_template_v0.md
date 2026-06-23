# Business Model: [domain] / [subdomain]
**Domain:** [domain]  
**Subdomain:** [subdomain]  
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

<!-- register:bm_entities business_language -->
### Entities (bm_entities)
| Entity | Description | Store Model | Source Finding |
|--------|-------------|-------------|----------------|

<!-- register:resources optional business_language -->
### Resources
| Resource | Description | Source Finding |
|----------|-------------|----------------|

<!-- register:events business_language -->
### Events (events)
| Event | Trigger | Lifecycle Meaning | Source Finding |
|-------|---------|-------------------|----------------|

*A relationship implies a capability. Name that capability as a **business need** in Capability
Need (business language — no artifact names). If an existing or candidate artifact is relevant,
cite its FQDN in **Source Finding** only — never in the Capability Need cell.*

<!-- register:relationships optional business_language -->
### Relationships (Candidate Capabilities)
| Subject | Verb | Object | Capability Need | Source Finding |
|---------|------|--------|-----------------|----------------|

---

## 2. Capability Graph (capability_graph)

*Every capability discovered during Analysis Loop. CRITICAL = must author this CR. ADVISORY = should author. SATISFIED = exists in PPS. Capability column is business language — no FQDNs.*

<!-- register:capability_graph business_language -->
| Capability | Source Finding | Status | Gap Register Entry | Notes |
|-----------|----------------|--------|--------------------|-------|
| [business-language capability] | [Stage 3 finding ref] | [CRITICAL \| ADVISORY \| SATISFIED] | [gap code if CRITICAL] | |

---

## 3. Dependency Graph (dependency_graph)

*Cross-subdomain dependencies discovered. Declared dependencies constrain authoring order. Existing PPS artifacts MAY be cited by FQDN here.*

<!-- register:dependency_graph -->
| From | To | Dependency Type | PPS Status | Source Finding |
|------|----|-----------------|------------|----------------|
| [subdomain] | [subdomain] | [capability call \| data read \| event] | [SATISFIED \| GAP] | [finding ref] |

---

## 4. Constraint Register (constraint_register)

*Non-negotiable rules discovered during analysis. Each constraint has a business source.*

<!-- register:constraint_register -->
| # | Constraint | Source Finding | Source |
|---|-----------|----------------|--------|
| 1 | [rule] | [finding ref] | [domain knowledge \| invariant \| governance rule] |

---

## 5. Gap Register (gap_register)

*All CRITICAL gaps. Each gap must be resolved before authoring begins. Capability is business language; Resolution is a disposition, not an artifact name.*

<!-- register:gap_register business_language -->
| Gap Code | Source Finding | Capability | Owner Subdomain | Resolution |
|----------|----------------|-----------|-----------------|------------|
| GAP-[n] | [finding ref] | [business-language capability] | [subdomain] | [NEW \| REUSE \| REPLACE] |

---

## 6. Design Decisions (design_decisions)

*Decisions accumulated during Stages 1–3 that constrain Design Intent. Each decision locks in an architectural choice.*

<!-- register:design_decisions -->
| # | Decision | Source Finding | Rationale | Constraints Imposed |
|---|----------|----------------|-----------|---------------------|
| 1 | [decision] | [finding ref] | [why] | [what it rules out] |

---

## 7. Authoring Scope (authoring_scope)

*What is IN this CR vs. FUTURE CR. This is the governance boundary decision that filters the Business Model into the Business Intent.*

<!-- register:authoring_scope -->
### In Scope — This CR
| Capability | Gap Register Ref |
|-----------|-----------------|

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

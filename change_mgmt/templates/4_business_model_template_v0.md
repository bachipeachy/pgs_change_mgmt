# Business Model: [domain] / [subdomain]
**Domain:** [domain]  
**Subdomain:** [subdomain]  
**Version:** V0  
**Status:** DRAFT  
**Pipeline Stage:** Stage 4 — Business Model (canonical artifact)  
**Produced by:** v0.5.0 SDLC authoring pipeline  

---

## Stage Inputs — Questions for the Human

*Stage 4 consolidates Stages 1–3; most content is carried forward, not newly elicited. Ask the human only the boundary questions below.*

| # | Question for the Human | How the Agent Uses the Answer (Intent) |
|---|------------------------|----------------------------------------|
| 1 | Of the capabilities discovered, which are IN this CR and which are deferred (Stage 4b boundary)? | Becomes Section 7 Authoring Scope — the governance filter between the Business Model and the Business Intent. Deferred items become Future CR candidates in the Stage 8 manifest. |
| 2 | Are the constraints in the register complete? Any unstated non-negotiables? | Closes the Constraint Register. Each constraint must carry a business source; constraints added later than this stage force re-approval of the design. |
| 3 | Do you confirm the actor list and each actor's authority class (ENDUSER / SYSTEM)? | Fixes the Actors table, which Stage 6 uses to declare authority and Stage 6b uses for intent admission design. |

**Agent execution rules for this stage:**
- This document consolidates — it does not re-litigate Stage 3 findings or introduce new design.
- Consistency check before completion: every CRITICAL row in the Capability Graph has a Gap Register entry with an owner subdomain; a capability that requires a NEW artifact in a peer subdomain is a GAP owned by that peer (dependency gap), never SATISFIED.
- New capabilities remain in business language. Existing artifacts cited by exact FQDN.

---

## 1. Discovery Summary

*Produced by Stages 1–3 (Input Elicitation → Domain Model Discovery → Analysis Loop). This section is the accumulated output of convergence — do not edit it to make it "cleaner." It is a record of what analysis discovered, not a polished narrative.*

### Actors
| Actor | Role | Authority Class |
|-------|------|-----------------|

### Entities
| Entity | Description | Store Model |
|--------|-------------|-------------|

### Resources
| Resource | Description |
|----------|-------------|

### Events
| Event | Trigger | Lifecycle Meaning |
|-------|---------|-------------------|

### Relationships (Candidate Capabilities)
| Subject | Verb | Object | Capability Candidate |
|---------|------|--------|---------------------|

---

## 2. Capability Graph

*Every capability discovered during Analysis Loop. CRITICAL = must author this CR. ADVISORY = should author. SATISFIED = exists in PPS.*

| Capability | Status | Gap Register Entry | Notes |
|-----------|--------|--------------------|-------|
| [capability] | [CRITICAL | ADVISORY | SATISFIED] | [gap code if CRITICAL] | |

---

## 3. Dependency Graph

*Cross-subdomain dependencies discovered. Declared dependencies constrain authoring order.*

| From | To | Dependency Type | PPS Status |
|------|----|-----------------|------------|
| [subdomain] | [subdomain] | [capability call | data read | event] | [SATISFIED | GAP] |

---

## 4. Constraint Register

*Non-negotiable rules discovered during analysis. Each constraint has a business source.*

| # | Constraint | Source |
|---|-----------|--------|
| 1 | [rule] | [domain knowledge | invariant | governance rule] |

---

## 5. Gap Register

*All CRITICAL gaps. Each gap must be resolved before authoring begins.*

| Gap Code | Capability | Owner Subdomain | Resolution |
|----------|-----------|-----------------|------------|
| GAP-[n] | [capability] | [subdomain] | [NEW artifact | REPLACE existing | REUSE existing] |

---

## 6. Design Decisions Register

*Decisions accumulated during Stages 1–3 that constrain Design Intent. Each decision locks in an architectural choice.*

| # | Decision | Rationale | Constraints Imposed |
|---|----------|-----------|---------------------|
| 1 | [decision] | [why] | [what it rules out] |

---

## 7. Authoring Scope

*What is IN this CR vs. FUTURE CR. This is the governance boundary decision that filters the Business Model into the Business Intent.*

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

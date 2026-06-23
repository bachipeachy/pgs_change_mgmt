# Stage 2 — Domain Model Verification: [domain] / [subdomain]
**Stage:** 2 — Domain Model Verification  
**CR:** change_request_[subdomain]_v0.md  
**Status:** DRAFT  
**Feeds:** Stage 3 — Analysis Loop  

> **S2 verifies the semantic model inherited from S1 — it does not discover the domain from
> scratch.** Stage 1 already established the *meaning* (vocabulary, lifecycle states, events,
> invariants, authority). S2's job is bounded: confirm that model against the compiled snapshot,
> establish what already exists for each Stage-1 **System Belief**, and capture the gaps. It
> **discovers facts**; it does not **decide** (extend-vs-new is Stage 3) and it does not author
> solution artifacts.

---

## Document Contract

**This artifact is a structured register document — not a narrative.**

VALID OUTPUT:
- Populated register tables (every required register below)
- Existing artifacts cited by exact FQDN — only in the PPS Baseline register
- Business-language entity / process / observation / gap descriptions

INVALID OUTPUT:
- Narrative summaries, reasoning essays, executive summaries
- Free-form prose replacing required registers

A required register with no rows MUST be rendered as a single row:

| NONE IDENTIFIED |

A prose-only or empty *required* register is a structural defect — the renderer rejects the
document mechanically before any human reviews it.

---

### A. Semantic Inheritance — start from Stage 1, do not re-derive

The semantic model is **given** by Stage 1; you inherit it, you do not rediscover it:

| Inherited from Stage 1 | How S2 uses it |
|------------------------|----------------|
| **Business Vocabulary** (the objects) | Seed the Business Entities register — confirm and map each object to evidence; do not invent a different object set. |
| **Lifecycle States** | The states each entity moves through — confirm the snapshot supports them; a missing state is a gap. |
| **Business Events** | The moments the domain must recognize — find what (if anything) already emits them. |
| **Business Invariants** | Facts that must hold — note any existing artifact that already enforces (or violates) one. |
| **System Beliefs** (+ Verification Goals) | The **bounded discovery targets** — see §B. |
| **Known Facts · Governance Scope** | Authoritative business truths and the subdomain neighborhood. |

S2 does NOT ask "what is a Chain?" — Stage 1 answered that. S2 asks "given these semantics, what
evidence exists in the snapshot, and what is missing?"

### B. The Spine — Belief Verification drives this stage

**Belief Verification (§3) is the spine of S2 — fill it FIRST, before any other register.** One
row per Stage-1 **System Belief**: ground its Verification Goal and record the result —
`VERIFIED` · `NOT_FOUND` · `INSUFFICIENT_EVIDENCE`. Verification is scoped to the Stage-1 **System
Beliefs** and **Requested Outcomes** — not the domain at large.

**Every other register is a PROJECTION of the verified beliefs.** An entity, process, gap,
observation, concern, or baseline artifact may appear in this stage ONLY because verifying a
belief (or serving a Requested Outcome) surfaced it. A row that traces to no belief and no
requested outcome does not belong here — its `Source Finding` must name the belief or outcome it
serves. The **PPS Baseline** contains ONLY artifacts that verify a belief or directly serve a
requested outcome; an artifact tied to no belief and no outcome — **STOP, do not list it.**

**The belief ledger is the STOP condition: S2 is complete when every System Belief has a result.**
It does NOT continue merely because additional related artifacts exist — a successful grounding is
not a new search frontier. **Absence is a final answer:** if a search returns nothing (e.g.
`GENESIS → 0 results`), record the belief as `NOT_FOUND` and move on. Never re-search variants of a
term that already returned nothing.

### C. Open Questions — a blocker list, not a scratchpad

A row belongs in **Open Questions** ONLY if it BOTH (a) blocks a Stage-3 decision AND (b) cannot
be answered from evidence. It is NOT a list of artifacts you noticed, and NOT an
end-of-budget dump. `open_questions = NONE IDENTIFIED` is a **healthy, successful** outcome.

---

### Business-Language Rule

These registers MUST NOT contain protocol artifact names or FQDNs (express discovery in
**business language**; naming solution artifacts here is premature design — FQDNs are
introduced at Stage 5+):

- Business Entities · Entity Attributes · Business Processes · Process Steps · Gaps ·
  Architectural Observations · Open Questions · Discovery Concerns

VALID: "the canonical chain that commits proposed blocks"  
INVALID: `CC_COMMIT_BLOCK_TO_CHAIN_V0`, `WF_GENESIS_BOOTSTRAP_V0`

**WHERE FQDNs GO.** When an observation, gap, or concern is grounded in an existing artifact, the
FQDN goes ONLY in that row's **Evidence** and/or **Source Finding** column — NEVER in the
content/description cell (Observation, Gap, Impact, Concern, Question, Why It Matters). Write the
*business meaning* in the content cell and let the FQDN in the evidence column carry the proof.
INVALID: `Observation = "a consensus loop workflow exists (WF_RUN_CONSENSUS_LOOP_V0)"`.
VALID: `Observation = "a consensus loop already proposes blocks and drives slot processing"` ·
`Evidence = WF_RUN_CONSENSUS_LOOP_V0`. The renderer rejects an FQDN found in a content cell.

**EXCEPTION — Belief Verification & PPS Baseline.** Those registers cite existing artifacts by
exact FQDN in their `Evidence` / `FQDN` columns — that FQDN is the evidence.

---

### Discovery Classification (DISCOVERY_CLASSIFICATION_REQUIRED)

Every discovered item carries an `Evidence Status`, so a hypothesis is never silently promoted
to a fact:

- **OBSERVED** — supported directly by grounding evidence (confirmed via a tool call).
- **INFERRED** — derived from observed evidence but NOT directly verified (a reasoned suspicion).
- **OPEN** — requires future investigation; not yet established.

**The PPS Baseline is OBSERVED-only** — every row is a grounded, verified existing artifact. A
capability you *suspect* should exist but could not ground is **INFERRED**, and it belongs in
the Gap Register (as an INFERRED gap), NEVER in the Baseline. Do NOT extrapolate an artifact
from a pattern — seeing `APPEND_TX_EVENT` + `APPEND_VALIDATOR_EVENT` does NOT mean an
`APPEND_BLOCK_EVENT` exists. If you did not ground it, it is INFERRED, not OBSERVED.

---

## 1. Business Entities

*Confirm/map the Stage-1 Business Vocabulary against the snapshot — these are the inherited
objects, not a new set. A thing the business talks about, not a data store or artifact.*

<!-- register:entities business_language -->
| Entity | Description | Store Model | Evidence Status | Source Finding |
|--------|-------------|-------------|-----------------|----------------|

### Entity Attributes

*One row per (entity, attribute) — attribute-level, so S5 (identity) and S6b (storage schema) can consume directly.*

<!-- register:entity_attributes business_language -->
| Entity | Attribute | Meaning | Evidence Status | Source Finding |
|--------|-----------|---------|-----------------|----------------|

---

## 2. Business Processes

*Every business process — a sequence of business decisions/actions, implementation-free.*

<!-- register:business_processes business_language -->
| Process | Initiator | Outcome | Evidence Status | Source Finding |
|---------|-----------|---------|-----------------|----------------|

### Process Steps

*One row per step, in order — so S6b workflow authoring can consume the sequence directly.*

<!-- register:process_steps business_language -->
| Process | Step # | Action | Record Produced | Evidence Status | Source Finding |
|---------|--------|--------|-----------------|-----------------|----------------|

---

## 3. Belief Verification — THE SPINE (fill this register FIRST)

*The spine of S2: every other register projects from these rows. One row per Stage-1 System
Belief. Ground its Verification Goal and record the Result. This is the STOP condition: S2 is
complete when every belief has a result. `NOT_FOUND` is a valid, final result — absence is an
answer, not a reason to keep searching.*

<!-- register:belief_verification -->
| Belief | Result (VERIFIED, NOT_FOUND, INSUFFICIENT_EVIDENCE) | Evidence | Source Finding |
|--------|------------------------------------------------------|----------|----------------|

---

## 4. PPS Baseline — What Already Exists

*Read the compiled snapshot directly (grounding tools), not memory. ONLY artifacts that verify a
System Belief or directly serve a Requested Outcome — not the whole domain inventory. One row per
relevant existing capability, cited by exact FQDN. Fit ∈ EXACT | PARTIAL | MISMATCH (an
observation of how well it matches the need — NOT a reuse decision; that is Stage 3).*

<!-- register:pps_baseline_fqdns -->
| Capability | FQDN | What It Does | Fit (EXACT, PARTIAL, MISMATCH) | Cannot Do |
|-----------|------|--------------|--------------------------------|-----------|

---

## 5. Gap Analysis — What Is Missing

*Each gap in business language. Severity ∈ CRITICAL (blocks authoring) | OPEN QUESTION (feeds Stage 3) | MINOR (noted).*

<!-- register:gaps business_language -->
| Gap | Severity | Impact | Evidence Status | Source Finding |
|-----|----------|--------|-----------------|----------------|

---

## 6. Architectural Observations

*Architectural FACTS surfaced WHILE verifying a belief — not decisions, not free discovery. Each
row's `Source Finding` names the belief it came from. Stage 3 argues extend-vs-new from these.
E.g. "a validator lifecycle already exists", "no canonical chain storage was found".*

<!-- register:architectural_observations business_language -->
| Observation | Evidence | Evidence Status | Source Finding |
|-------------|----------|-----------------|----------------|

---

## 7. Discovery Concerns

*Concerns surfaced WHILE verifying a belief — each traces back to one via `Source Finding`. The
primary feed into Stage 3 (operationalizes CONCERN_TRACEABILITY_REQUIRED). Severity ∈ CRITICAL |
MAJOR | MINOR.*

<!-- register:discovery_concerns business_language -->
| Concern | Evidence | Severity | Evidence Status | Source Finding |
|---------|----------|----------|-----------------|----------------|

---

## 8. Open Questions for Stage 3

*A row belongs here ONLY if it blocks a Stage-3 decision AND cannot be answered from evidence (see
§C). NOT an artifact inventory. Empty (`NONE IDENTIFIED`) is a healthy outcome. Category ∈
business | governance | identity | workflow | storage | policy | unknown.*

<!-- register:open_questions business_language optional -->
| Question | Category | Why It Matters | Source Finding |
|----------|----------|----------------|----------------|

---

## gov_projection — Governed Handoff to Stage 3

*Governed, lossless, identity-preserving (Stage 0 / field manual §4.7). Every register is forwarded — Stage 3 never re-discovers what Stage 2 modelled. Emit keys match the register ids above exactly.*

| Direction | Fields |
|-----------|--------|
| **Consumes** ← Stage 1 | business_vocabulary · known_facts · system_beliefs · lifecycle_states · business_events · governance_scope |
| **Emits** → Stage 3 | entities · entity_attributes · business_processes · process_steps · belief_verification · pps_baseline_fqdns · gaps · architectural_observations · discovery_concerns · open_questions |

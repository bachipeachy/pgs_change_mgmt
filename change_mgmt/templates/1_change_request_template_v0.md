# Stage 1 — Change Request: Clarification & Fact Capture: [domain] / [subdomain]
**Stage:** 1 — Change Request (Clarification & Fact Capture)  
**CR:** change_request_[subdomain]_v0.md  
**Status:** DRAFT  
**Feeds:** Stage 2 — Domain Model Discovery  

> **S1 interrogates; it does not author.** It captures *what is requested*, the *business
> semantics* (vocabulary, invariants, lifecycle states, business events, authority boundaries),
> *what the business definitively holds true*, *what the human believes the system already
> provides* (a hypothesis, not a fact), *what is assumed*, *what constrains*, and — most
> importantly — *what must be clarified before proceeding*. S1 is the primary human↔agent
> interaction stage: the agent does not guess, it asks. Implementation is deliberately out of view
> (S1 discovers, S2 models, S3 decides) — no design options, architectures, capability candidates,
> workflows, or artifact names appear here.

---

## Document Contract

**This artifact is a structured register document — not a narrative.** No Problem Statement /
Background / Business Need / Goals prose (those invite speculation). Capture facts and requests
as registers.

VALID OUTPUT:
- Populated register tables (every required register)
- Business-language statements; existing artifacts cited by FQDN ONLY in a Source Finding cell

INVALID OUTPUT:
- Narrative prose replacing registers; design options; recommended architecture; capability /
  workflow / artifact candidates (all premature at S1)

A required register with no rows MUST render as a single `| NONE IDENTIFIED |` row. The renderer
rejects a prose-only or empty register mechanically before any human reviews it.

---

### The three-way split (the heart of S1)

S1's job is to keep three kinds of statement from contaminating one another — the separation
that prevents semantic drift downstream:

- **Business Truth** (§4 Known Facts) — what the business *authoritatively decides or requires*.
  The human owns these. They do not require snapshot inspection. Certainty is HIGH unless the
  human is genuinely unsure. Example: *"initial supply shall be 1,000,000 BachiCoin."*
- **System Belief** (§5 Existing-System Beliefs) — what the human *believes the system already
  provides*. The human is NOT authoritative here; the snapshot is. These are **discovery targets**
  the agent grounds in Stage 2, each with a **Verification Goal** — never asserted as fact at S1.
  Example: *"a consensus loop that proposes blocks may already exist."*
- **Clarification** (§14) — an unresolved question the agent must ask rather than guess, tagged
  with its **Owner** (who can answer: HUMAN, SNAPSHOT, or GOVERNANCE).

A statement about current system state is a **System Belief**, never a Known Fact. A business
decision is a **Known Fact**, never a System Belief. When you would guess either, raise a
**Clarification** instead.

### The business-semantics model (what S3 consumes to eliminate guesswork)

Six registers together form the human-authoritative semantic model so downstream stages discover
topology *in service of* meaning, not the reverse: **Business Vocabulary** (§2, the objects),
**Business Invariants** (§8, what must always hold), **Lifecycle States** (§9, the states an
object moves through), **Business Events** (§10, the moments that matter), and **Authority
Boundaries** (§11, who is authoritative for each object — the transition that drives S3's
REUSE-vs-AUTHOR_NEW calls). A NEW_SUBDOMAIN CR is incomplete without these.

---

### Business-Language Rule

Every CONTENT/DESCRIPTION cell is a business-language statement — NO protocol artifact names,
FQDNs, workflow/capability/intent/event names, or register bindings (those arrive at Stage 5+).
If a fact is supported by an existing artifact, cite that FQDN ONLY in the row's `source_finding`
(evidence) column — never in the statement itself.

VALID: "the running system already registers validators"  
INVALID: "WF_REGISTER_VALIDATOR_V0 exists"

---

### Stage 1 execution rules

- **Vocabulary first.** Every domain term the CR depends on (§2) is defined in business language
  before it is used — definitions are governed evidence, not implicit knowledge.
- **Truths ≠ Beliefs ≠ Requests.** Business Truths (§4) are human-authoritative decisions/
  requirements. System Beliefs (§5) are unverified hypotheses about what exists → discovery
  targets. Requested Outcomes (§3) are what the requester wants. Never merge them.
- **Known Facts are business truths only.** A claim about what the system currently does is a
  System Belief (§5), not a Known Fact — even if the human is confident.
- **Every System Belief carries a Verification Goal** — what Stage 2 must establish to confirm or
  refute it — so grounding is scoped to this CR, not the whole domain inventory.
- **State the business semantics explicitly** (§8–§11): invariants, lifecycle states, events, and
  authority boundaries are human-authoritative business truths, not implementation. S3 uses them
  to eliminate competing designs.
- **Every fact carries a certainty** (HIGH | MEDIUM | LOW). A belief you could not verify is a
  Clarification request — not a HIGH fact.
- **Every clarification carries an Owner.** Do not ask the human what only the snapshot can answer
  (Owner = SNAPSHOT) — route it to discovery instead.
- **Every row carries a `source_finding`** (human statement, seed answer ref, or grounded FQDN).
- **When you would guess, ask instead.** Anything not established becomes a
  `clarification_requests` row, not an assumption silently carried forward.

---

## 1. CR Type

*The classification of this change.*

<!-- register:cr_type business_language -->
| Classification (NEW_SUBDOMAIN, EXTEND_SUBDOMAIN, MODIFY, DEPRECATE) | Rationale | Source Finding |
|----------------|-----------|----------------|

---

## 2. Business Vocabulary

*Every domain term this CR depends on, defined in business language. Governed definitions become
first-class evidence — they prevent every downstream stage from re-inferring what the human
already means. Define the term, not its implementation.*

<!-- register:business_vocabulary business_language -->
| Term | Definition | Source Finding |
|------|------------|----------------|

---

## 3. Requested Outcomes

*What the requester wants to be true at close — business outcomes, not solutions.*

<!-- register:requested_outcomes business_language -->
| Outcome | Source Finding |
|---------|----------------|

---

## 4. Known Facts — Business Truths

*Only statements the human is authoritative about: business decisions and requirements. NOT
statements about what the system currently provides (those are §5 System Beliefs). Certainty
∈ HIGH | MEDIUM | LOW; source is the human (or an explicit human-cited authority).*

<!-- register:known_facts business_language -->
| Fact | Certainty (HIGH, MEDIUM, LOW) | Source Finding |
|------|-----------|----------------|

---

## 5. Existing-System Beliefs — Requiring Verification

*What the human BELIEVES the system already provides — hypotheses, not facts. The human is not
authoritative here; the snapshot is. Each row is a Stage-2 discovery target: `Why It Matters`
scopes the grounding to this CR, and `Verification Goal` states what Stage 2 must establish to
confirm or refute the belief (governing workflow(s), producers, emitted records, ownership).*

<!-- register:system_beliefs business_language -->
| Belief | Why It Matters | Verification Goal | Source Finding |
|--------|----------------|-------------------|----------------|

---

## 6. Assumptions

*Things taken as true WITHOUT full evidence — each with its basis. If an assumption is
load-bearing and unverified, prefer raising a clarification request instead.*

<!-- register:assumptions business_language optional -->
| Assumption | Basis | Source Finding |
|------------|-------|----------------|

---

## 7. Constraints

*Non-negotiable rules the change must honor (monetary, governance, regulatory, immutability, …).*

<!-- register:constraints business_language -->
| Constraint | Source | Source Finding |
|------------|--------|----------------|

---

## 8. Business Invariants

*Properties that must ALWAYS hold true of the domain — business truths stated as invariants, not
implementation rules. S3 uses these to eliminate competing designs (a design that violates an
invariant is inadmissible). Each is a single, testable business statement.*

<!-- register:business_invariants business_language -->
| Invariant | Source Finding |
|-----------|----------------|

---

## 9. Lifecycle States

*The states each core business object moves through, in business language. S3 uses these to scope
the state transitions a design must support (and the ones it must not). One row per object-state.*

<!-- register:lifecycle_states business_language -->
| Object | State | Meaning | Source Finding |
|--------|-------|---------|----------------|

---

## 10. Business Events

*The business moments that matter — the events the domain must recognize. Stated in business
language (not artifact/event-code names). One row per event.*

<!-- register:business_events business_language -->
| Event | When It Occurs | Significance | Source Finding |
|-------|----------------|--------------|----------------|

---

## 11. Authority Boundaries

*Who is authoritative for each core business object — and where authority transitions. S3 uses
these to drive REUSE-vs-AUTHOR_NEW: an authority handoff (e.g. proposed→committed) is exactly the
boundary a design must respect. State the owner in business terms, not artifact names.*

<!-- register:authority_boundaries business_language -->
| Business Object | Authoritative Owner | Source Finding |
|-----------------|---------------------|----------------|

---

## 12. Out of Scope

*Explicitly excluded from this CR — deferred to future CRs. State the release boundary
explicitly so downstream stages do not chase future-state architecture.*

<!-- register:out_of_scope business_language optional -->
| Item | Reason | Source Finding |
|------|--------|----------------|

---

## 13. Governance Scope

*Which governance concerns this CR touches, in business terms (not artifact bindings). Each scope
item declares its `Relationship` to this CR — what the CR does to/with that boundary.*

<!-- register:governance_scope business_language -->
| Scope Item | Relationship (CREATED, ADJACENT) | Source Finding |
|------------|----------------|----------------|

---

## 14. Clarification Requests

*The keystone register: the agent does NOT guess — it asks. Every unresolved uncertainty that
could change the design is a row here. Blocking ∈ YES (cannot proceed until answered) | NO.
Owner ∈ HUMAN (only the requester can answer) | SNAPSHOT (discovery answers it in Stage 2) |
GOVERNANCE (a governance/topology decision). Do not ask the human a SNAPSHOT question.*

<!-- register:clarification_requests business_language optional -->
| Question | Why Needed | Blocking (YES, NO) | Owner (HUMAN, SNAPSHOT, GOVERNANCE) | Source Finding |
|----------|------------|----------|-------|----------------|

---

## 15. Acceptance Criteria

*How the requester will judge the CR satisfied at close — the S8 acceptance boundary. Each
criterion must be business-observable: testable by a business reviewer without inspecting runtime
internals.*

<!-- register:acceptance_criteria business_language -->
| Criterion | Source Finding |
|-----------|----------------|

---

## gov_projection — Governed Handoff to Stage 2

*Governed, lossless, identity-preserving (Stage 0 / field manual §4.7). Emit keys match the
register ids above exactly. Business Vocabulary, Truths, Invariants, Lifecycle States, Events and
Authority Boundaries cross as authoritative business semantics; System Beliefs cross as Stage-2
discovery targets (verified, never trusted). Blocking clarification requests are resolved by the
human at the S1 gate before Stage 2 proceeds.*

| Direction | Fields |
|-----------|--------|
| **Consumes** ← CR seed | human elicitation answers (the seed) |
| **Emits** → Stage 2 | cr_type · business_vocabulary · requested_outcomes · known_facts · system_beliefs · assumptions · constraints · business_invariants · lifecycle_states · business_events · authority_boundaries · out_of_scope · governance_scope · clarification_requests · acceptance_criteria |

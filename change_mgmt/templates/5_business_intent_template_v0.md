# Business Intent: [domain] / [subdomain]
**Domain:** [domain]  
**Subdomain:** [subdomain]  
**Version:** V0  
**Status:** DRAFT  
**Pipeline Stage:** Stage 5 — Business Intent (WHAT)  
**Produced by:** v0.5.0 SDLC authoring pipeline  

---

## Document Contract

**This artifact is a structured register document — not a narrative.** The Business Intent captures
the irreducible WHAT — purpose, scope, invariants, actions, and provisional artifact codes. Purpose
(§1) and Identity Semantics (§4) are short prose (the irreducible business knowledge a compiler can
never derive); everything else is registers. The worker emits register ROWS; a deterministic
renderer owns the document.

VALID OUTPUT:
- The two short prose sections (Purpose, Identity Semantics) filled for this subdomain
- Populated register tables (every required register below)
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
| 3 | Which field uniquely identifies each record, where does it come from, what does a duplicate mean? | Becomes §4 Identity Semantics. |
| 4 | What is always forbidden or always required, and what is the business reason? | Becomes `invariants`. |
| 5 | What verbs can be performed on these records, and who/what triggers each? | Becomes `actions` — each in-scope action yields one Intent and one Workflow. |

---

## 1. Subdomain Purpose

*One short paragraph: what this subdomain governs, what authority it establishes, what lifecycle it
manages, and the business rationale for its existence. Write for a business stakeholder. No artifact
names.*

[Purpose paragraph for [domain]/[subdomain].]

---

## 2. Scope Boundary

*What V0 commits to vs. what is explicitly deferred. A vague scope boundary is a governance defect. Status ∈ IN_SCOPE | DEFERRED.*

<!-- register:scope_boundary business_language=capability,notes -->
| Capability | Status (IN_SCOPE, DEFERRED) | Notes | Source Finding |
|------------|-----------------------------|-------|----------------|

---

## 3. Business Objects

*The business records this subdomain maintains and WHY each takes its form. Record Model ∈ MUTABLE_STATE (current state, correctable) | APPEND_ONLY_JOURNAL (immutable history) | IDENTITY_REGISTRY (stable key→address) | HYBRID. Business language.*

<!-- register:business_objects optional business_language=store_name,business_rationale -->
| Store Name | Record Model (MUTABLE_STATE, APPEND_ONLY_JOURNAL, IDENTITY_REGISTRY, HYBRID) | Business Rationale | Source Finding |
|------------|------------------------------------------------------------------------------|--------------------|----------------|

---

## 4. Identity Semantics

*Short prose. Which field uniquely identifies each record, where it comes from, what a duplicate
means, and any cross-subdomain identity relationship. The compiler cannot infer identity semantics
from field names — this is irreducible business knowledge.*

[Primary identity field, source, uniqueness rule, and cross-subdomain relationship for
[domain]/[subdomain]. If none beyond the primary, say so.]

---

## 5. Business Invariants

*Non-negotiable rules with a business reason. A rule without a business reason is a technical constraint and belongs elsewhere.*

<!-- register:invariants business_language=invariant,business_reason -->
| Invariant | Business Reason | Source Finding |
|-----------|-----------------|----------------|

---

## 6. Business Actions

*Every verb performable on this subdomain's objects, in plain business language. Each in-scope action maps to one Intent and one Workflow. Status ∈ IN_SCOPE | DEFERRED.*

<!-- register:actions business_language=object,trigger -->
| Action | Object | Trigger | Status (IN_SCOPE, DEFERRED) | Source Finding |
|--------|--------|---------|-----------------------------|----------------|

---

## 7. Provisional Artifact Codes

*Provisional AC / IN / WF / CC codes (Stage 6b assigns binding FQDNs). Each carries `_V0`. `summary` is business language. Family ∈ AC | IN | WF | CC.*

<!-- register:provisional_codes business_language=summary -->
| Provisional Code | Family (AC, IN, WF, CC) | Summary | Source Finding |
|------------------|-------------------------|---------|----------------|

---

## 8. Cross-Subdomain References

*Capability Contracts defined in another subdomain and referenced by this subdomain's workflows. `cc_code` is the existing FQDN; do not re-document it here.*

<!-- register:cross_subdomain_refs optional business_language=role -->
| CC Code | Defined In | Role | Source Finding |
|---------|------------|------|----------------|

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 4 — Business Model | business_model_[subdomain]_v0.md | COMPLETE |
| Stage 5 — Business Intent | This document | COMPLETE |
| Stage 6 — Governance Intent | Pending | — |

---

## gov_projection — Governed Handoff to Stage 6

*The bounded inputs and emit keys mirror the engine's gov_projection schema exactly
(`contracts/gov_projection.py`): S5 consumes the S4 discovery output plus the S1 release boundary
and emits the WHAT. Emit keys match the register ids above exactly (Purpose §1 / Identity §4 /
Business Objects §3 are this stage's record, not forwarded fields).*

| Direction | Fields |
|-----------|--------|
| **Consumes** ← Stage 1 | out_of_scope |
| **Consumes** ← Stage 4 | actors · bm_entities · events · capability_graph · constraint_register |
| **Emits** → Stage 6 | scope_boundary · invariants · actions · provisional_codes · cross_subdomain_refs |

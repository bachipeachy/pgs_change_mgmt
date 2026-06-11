# Change Request: [domain] / [subdomain]

**CR Type:** [change_request_bug | change_request_feature | change_request_subdomain | change_request_domain | change_request_other]  
**Domain:** [domain]  
**Primary Subdomain:** [subdomain] — [EXISTING | NEW]  
**Secondary Subdomain:** [if applicable] — [NEW | EXISTING]  
**Version:** V0  
**Status:** DRAFT  
**Pipeline Stage:** Stage 1 — Change Request & Input Elicitation  
**Feeds:** Stage 2 — Domain Model Discovery

> **Before drafting, complete the reading assignment in [`0_agent_context_template_v0.md`](0_agent_context_template_v0.md).** It declares the doctrine, snapshot inventory, and prior dossiers the agent must read before answering. Drafting without it is guessing.

---

## Stage Inputs — Questions for the Human

*Answer each question crisply before the agent drafts this document. The right column states the intent — exactly how the agent will use the answer. An unanswered question is an open gap; the agent must not fill it by assumption.*

| # | Question for the Human | How the Agent Uses the Answer (Intent) |
|---|------------------------|----------------------------------------|
| 1 | What is broken, missing, or ungoverned — in business terms, not artifact terms? | Becomes the Problem Statement verbatim. Determines whether this is a defect, a capability gap, or a new governance concern. |
| 2 | What governed capability must exist when this CR closes? How will you recognize success? | Becomes the Desired Outcome. Sets the acceptance boundary for Stage 8 manifest closure — anything not stated here cannot be claimed as done. |
| 3 | What type of change is this: bug, feature, new subdomain, or new domain? | Selects the analysis path (Section 4) — bug skips to gap analysis; subdomain/domain triggers the full discovery loop through saturation. |
| 4 | Which existing subdomains, workflows, or data flows does this touch or sit next to? | Seeds the Known Facts table and tells Stage 2 which PPS artifacts to read first. The agent verifies every named artifact against `pps_snapshot/index.json` — it does not trust memory. |
| 5 | What is explicitly OUT of scope — deferred to future CRs? | Becomes Section 6. Explicit deferral is a governance decision; silence is ambiguity. The agent will treat anything not deferred and not in scope as an open question, not as in scope. |
| 6 | What business rules are non-negotiable (invariants the change must never violate)? | Carried as candidate invariants into Stages 2–5; each becomes a constraint with a business source in the Business Model Constraint Register. |
| 7 | Are there reference implementations, standards, or seed data the design must follow? | Recorded as Known Facts with source attribution; constrains Stage 6b design choices. |

---

## 1. Problem Statement

*What is the real problem — not the symptom, not the solution. State it in business terms. If you find yourself describing an artifact or a workflow, stop and go one level up. Do not reference WF_, CC_, or any artifact family at this stage.*

*Good: "Autonomous agent authority is exercised operationally rather than through protocol-governed admission."*
*Bad: "We need a new WF_ to govern agent tool requests."*

---

## 2. Desired Outcome

*What governed capability must exist by end of this CR? Describe the operating state, not the implementation. Be specific enough to recognize success, vague enough not to prejudge design.*

*Specify:*
- *What can now happen that could not happen before*
- *What structural property the system gains (traceable, governed, admissible, etc.)*

---

## 3. Known Facts at CR Entry

*What is already known. Organize into named subsections — business labels, not artifact labels. Every claim about what exists in the PPS must be verified against `pps_snapshot/index.json` and cited.*

| Fact | Source |
|------|--------|
| [What existing artifacts or subdomains are relevant] | PPS snapshot (verified) |
| [What reference implementations or domain knowledge is available] | [source] |

### A. [Known Fact Area — e.g., "Existing Data Flow", "Authority Model", "Scope Limits"]

[Describe what is known. Be specific. Include explicit boundaries (what is in scope vs. deferred).]

### B. [Known Fact Area]

[Continue as needed. Each subsection is a distinct known-fact domain.]

---

## 4. CR Type Determination

**Type:** [cr_type]

**Analysis path triggered:**

| CR Type | Analysis Path |
|---------|--------------|
| change_request_bug | Skip to Gap Analysis on existing artifacts |
| change_request_feature | Capability + Gap analysis only |
| change_request_subdomain | Full loop: Domain Model Discovery + Analysis Loop until Discovery Saturation |
| change_request_domain | Full loop + new domain declaration |

**Pipeline entry:** Stage [2 | gap_analysis]

---

## 5. Governance Scope Declared by This CR

| Subdomain | Action | Rationale |
|-----------|--------|-----------|
| [subdomain] | [EXTEND | DECLARE NEW | DEPENDENCY GAP] | [why] |

---

## 6. Out of Scope — Deferred to Future CRs

| Capability | Reason |
|-----------|--------|
| [capability] | [why deferred] |

---

## Analyst Notes — Purity Rules

- **Purity Filter active from this stage forward.** Stages 1–4 use business language only for anything NEW — no artifact family names (CC_, WF_, CS_, CT_, EV_) and no invented artifact codes for capabilities that do not yet exist.
- **Existing PPS artifacts are the one exception:** they may be cited by exact FQDN as evidence, after verification against the snapshot inventory.
- **Provisional artifact codes first appear in Stage 5 (Business Intent); binding FQDNs are assigned only in Stage 6b (Design Intent).**
- **Open question for Stage 2:** [What does Domain Model Discovery need to resolve that this stage left open?]
- **Open question for Stage 3:** [What analysis-loop question cannot be answered without PPS inspection?]

---

## Dossier Status

| Stage | Artifact | Status |
|-------|----------|--------|
| Stage 1 | change_request_[subdomain]_v0.md (classification + input elicitation) | COMPLETE |
| Stage 2 | domain_model_[subdomain]_v0.md | PENDING |
| Stage 3 | analysis_loop_[subdomain]_v0.md | PENDING |
| Stage 4 | business_model_[subdomain]_v0.md | PENDING |
| Stage 4b | Authoring Scope (Section 7 of business model — no separate artifact) | PENDING |
| Stage 5 | business_intent_[subdomain]_v0.md | PENDING |
| Stage 6 | governance_intent_[subdomain]_v0.md | PENDING |
| Stage 6b | design_intent_[subdomain]_v0.md — Gate 1 closes here | PENDING |
| Stage 7 | authoring_mandate_[subdomain]_v0.md — Gate 2 closes here | PENDING |
| Stage 8 | authoring_manifest_[subdomain]_v0.md | PENDING — pre-authoring baseline; populated during/after authoring |
| Stage 9 | (CR Closure — no separate artifact; manifest status → APPROVED) | PENDING |

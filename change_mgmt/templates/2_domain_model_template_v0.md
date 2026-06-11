# Stage 2 — Domain Model Discovery: [domain] / [subdomain]
**Stage:** 2 — Domain Model Discovery
**CR:** change_request_[subdomain]_v0.md
**Status:** DRAFT
**Feeds:** Stage 3 — Analysis Loop

---

## Stage Inputs — Questions for the Human

*Answer crisply before drafting. The right column states how the agent uses each answer.*

| # | Question for the Human | How the Agent Uses the Answer (Intent) |
|---|------------------------|----------------------------------------|
| 1 | What are the business entities this change deals in, and which attributes matter? | Becomes Section 1. Entity attributes drive identity semantics (Stage 5) and store schemas (Stage 6b) — missing attributes here surface as schema gaps later. |
| 2 | For each entity: is it current state, accumulated history, or a stable identity binding? Can records be corrected? Deleted? | Determines the candidate storage model (mutable / append-only / registry). Getting this wrong produces invisible runtime bugs. |
| 3 | Walk through each business process step by step — who initiates it, what decisions occur, what is recorded? | Becomes Section 2. Process steps become workflow nodes in Stage 6b; a step you omit here will be missing from the execution graph. |
| 4 | Which behaviors do you believe already exist in the running system? | Cross-checked against the PPS baseline (Section 3). Mismatches between belief and snapshot are themselves findings. |

**Agent execution rules for this stage:**
- The PPS Baseline (Section 3) MUST come from reading `pps_snapshot/index.json` and the relevant artifacts directly — never from memory or from this conversation. List what was searched, not only what was found: reusable events (EV_), transforms (CT_), and contracts (CC_) frequently already exist under names the human did not mention.
- Do not invent artifact codes for NEW capabilities in this document. New capabilities are named in business language; existing artifacts are cited by exact FQDN.

---

## 1. Business Entities

*Name every domain entity involved in this CR. An entity is a thing the business talks about — not a data store or an artifact.*

### [Entity Name]
*One sentence: what is this entity in business terms.*

| Attribute | Description |
|-----------|-------------|
| [attribute] | [what it represents] |

*Add one subsection per entity. Typical entities: actor types, requests/proposals, decisions, registries, surfaces, records.*

---

## 2. Business Processes

*Name every business process involved. A process is a sequence of decisions or actions the domain performs — not a workflow or CC pipeline.*

### Process 1 — [Process Name]
*Description of what happens, in business steps. Keep implementation-free.*

1. [Step 1]
2. [Step 2]
3. [Step 3]

### Process 2 — [Process Name]
*Continue as needed.*

---

## 3. PPS Baseline — What Already Exists

*Read the PPS snapshot (pps_snapshot/index.json) and relevant registry artifacts directly. Do not rely on memory.*

*For each relevant existing capability, state: what it does, whether its shape matches this CR's needs, and what specifically it cannot do.*

### [Existing Capability Name]

[What the existing artifact does. What fields it operates on. What its governance shape is.]

**Fit for this CR:** [exact match | partial — [what it can and cannot do] | mismatch]

*Add one subsection per relevant existing capability.*

---

## 4. Gap Analysis — What Is Missing

*For each gap: state what is missing, classify its severity, and describe its impact.*

### Gap 1 — [Gap Name] ([CRITICAL | OPEN QUESTION | MINOR])

[What is missing. What artifact or capability does not exist. Why it matters for this CR.]

**Impact:** [what cannot proceed without this]

### Gap 2 — [Gap Name] ([CRITICAL | OPEN QUESTION | MINOR])

[Continue as needed. CRITICAL gaps block authoring. OPEN QUESTION gaps feed into Stage 3. MINOR gaps are noted but do not block.]

---

## 5. Summary: Extend vs. New Subdomain

*State the architectural question explicitly: does this CR extend an existing subdomain or require a new one?*

**The question:** Does [the new capability] belong inside [existing subdomain] or does it require [proposed subdomain]?

**Evidence for extend:** [what argues for putting this inside the existing subdomain]

**Evidence for new subdomain:** [what argues for a separate subdomain — separate governance concern, separate CC configuration, different ownership, etc.]

*Do not decide here. This is the question for Stage 3.*

---

## 6. Open Questions for Stage 3

| # | Question | Why It Matters |
|---|----------|---------------|
| Q1 | [question] | [what the answer determines] |
| Q2 | [question] | [what the answer determines] |

*Each open question becomes a named question in the Stage 3 Analysis Loop. Questions that can be answered by reading PPS artifacts should be resolved there, not deferred.*

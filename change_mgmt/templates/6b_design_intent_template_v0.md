# Design Intent: [domain] / [subdomain]
**Domain:** [domain]  
**Subdomain:** [subdomain]  
**Version:** V0  
**Status:** DRAFT  
**Pipeline Stage:** Stage 6b — Design Intent (HOW)  
**Produced by:** v0.5.0 SDLC authoring pipeline  
**Purity:** HOW only — business facts (Business Model) and placement decisions (Governance Intent) not repeated  

---

## Stage Inputs — Questions for the Human

*Answer crisply before drafting. The right column states how the agent uses each answer.*

| # | Question for the Human | How the Agent Uses the Answer (Intent) |
|---|------------------------|----------------------------------------|
| 1 | For each open design decision carried from Stages 1–4: which concrete resolution do you choose (store shape, schema fields, algorithm, reuse-vs-new)? | Becomes Section 1. Every row must trace back to a Business Model design decision; new decisions invented here must be flagged as such. |
| 2 | Where an existing artifact partially fits: REUSE as-is, EXTEND it, or REPLACE it? | Fixes Section 3 actions. REPLACE/EXTEND of shared artifacts affects other subdomains and needs explicit confirmation. |
| 3 | Do you approve the proposed store names, paths, and key fields? | Locks Section 8 STRUCTURE declarations. Storage topology is a governance concern — paths are declared here, never hardcoded later. |
| 4 | Gate 1: do you approve the full dossier as the design basis? | Gate 1 approval (Section 12) authorizes Stage 7. Without it, no mandate may be drafted. |

**Agent execution rules for this stage (binding FQDNs are assigned here):**
- Every new artifact maps 1:1 to a Governance Intent outcome; every FQDN carries `_V<n>`.
- **Workflow nodes are IN, CC, EXIT/EXIT_SUCCESS only.** Sub-workflow invocation = gateway CC bound to `CS_WORKFLOW_GATEWAY_V0` (precedent: `CC_INVOKE_BLOCK_PROPOSAL_V0`). EV_ artifacts are emitted facts, never triggers.
- A store is written only by CCs of its owning subdomain. Writing CCs for peer stores are declared in the dependency-gap section with peer ownership.
- Before declaring a new CT or EV: list the existing inventory candidates examined and why each does not fit (the transform vocabulary and event set usually already contain the atom).
- Verify field-level facts against the compiled artifacts — e.g., what a producing CC actually outputs — not against assumptions. State the source artifact for every consumed field.
- Artifact Summary counts (Section 11) must equal the rows of Section 4 exactly. Reconcile before completion.

---

## 1. Design Decisions Resolution

*The Design Decisions Register was populated throughout Stages 1–4. These decisions are resolved here.*

| Decision | Business Fact (Business Model) | Design Resolution |
| --- | --- | --- |
| [decision] | "[business fact]" | [concrete design resolution — algorithm, schema field, configuration parameter, etc.] |

---

## 2. [Key Store / Schema Design Decision]

*One section per significant design decision that resolves a Governance Intent storage requirement. Name the section after the decision (e.g., "Enrollment Store Decision", "Round Record Schema Decision").*

**Design resolution:** [State the concrete decision — which existing store is reused, or what new store is created, what schema fields are added/changed.]

| Field | Type | Description |
| --- | --- | --- |
| [field] | [type] | [description] |

**Consequence:** [State what existing artifacts must change as a result of this decision, if any.]

---

## 3. Artifact Inventory — Existing Artifacts

*All existing PPS artifacts touched by this CR. Action = REPLACE, REVIEW, REUSE, or EXTEND.*

| Artifact | Action | Reason |
| --- | --- | --- |
| `[domain]::[ARTIFACT_CODE_V0]` | [REPLACE / REUSE / EXTEND] | [reason] |

---

## 4. Artifact Family Mapping — New Artifacts

*Mapping from Governance Outcome capabilities to artifact families, with FQDN codes assigned. Organized by subdomain ownership as declared in Governance Intent.*

### [domain]::[subdomain] — New Artifacts

#### Workflow: [workflow name]

| Artifact | Family | Code | Status |
| --- | --- | --- | --- |
| [governing workflow] | WF | `[domain]::[WF_CODE_V0]` | NEW |
| [admission intent] | IN | `[domain]::[IN_CODE_V0]` | NEW |
| [runtime binding] | RB | `[domain]::[RB_CODE_V0]` | NEW |

#### Capability Contracts: [pipeline name]

| Capability | Family | Code | Status |
| --- | --- | --- | --- |
| [capability] | CC | `[domain]::[CC_CODE_V0]` | NEW |

#### Capability Transforms: [purpose]

| Capability | Family | Code | Status |
| --- | --- | --- | --- |
| [pure computation] | CT | `[domain]::[CT_CODE_V0]` | NEW |

#### Events: [lifecycle name]

| Event | Family | Code | Status |
| --- | --- | --- | --- |
| [event] | EV | `[domain]::[EV_CODE_V0]` | NEW |

---

### [domain]::[subdomain2] — New Artifacts (New Subdomain Established This CR)

*If this CR establishes a new subdomain, list artifacts that carry that subdomain's ownership here. State why these are authored now despite belonging to the new subdomain.*

| Artifact | Family | Code | Status |
| --- | --- | --- | --- |
| [capability] | CC | `[domain]::[CC_CODE_V0]` | NEW — subdomain: [subdomain2] |
| [event] | EV | `[domain]::[EV_CODE_V0]` | NEW — subdomain: [subdomain2] |

---

### [domain]::[dependency_subdomain] — Dependency Gap (Owned by [dependency_subdomain], Triggered by This CR)

*If a gap in a peer subdomain is triggered by this CR, declare the new artifact here. Ownership stays with the peer subdomain.*

| Capability | Family | Code | Status |
| --- | --- | --- | --- |
| [capability] | CC | `[domain]::[CC_CODE_V0]` | NEW — subdomain: [dependency_subdomain] |

---

## 4b. Module Path Assignments

*Every new artifact family gets a module path in its owning repository. The compiler resolves registry artifacts from these paths — a missing assignment is a build failure.*

| Artifact Family | Module Path |
|----------------|-------------|
| IN | `[repo].registry.[subdomain].intents` |
| WF | `[repo].registry.[subdomain].workflows` |
| CC | `[repo].registry.[subdomain].capability_contracts` |
| CT | `[repo].registry.[subdomain].capability_transforms` |
| RB | `[repo].registry.[subdomain].runtime_bindings` |
| STRUCTURE | `[repo].registry.[subdomain].structures` |
| Implementation | `[repo].implementation.[subdomain]` |

---

## 4c. Runtime Binding (RB) Declarations

*One RB per WF. The RB declares which CS substrates the WF requires and which storage structure resolves store paths. An undeclared CS binding is a runtime failure.*

### `[domain]::[RB_CODE_V0]`

Binds `[WF_CODE_V0]`.

| CS Binding | Role in WF |
|-----------|-----------|
| `capability_side_effects::[CS_CODE_V0]` | [which CC uses it, for what store or gateway call] |

**storage_structure:** `[domain]::[STRUCTURE_ARTIFACT_V0]`

*Repeat per RB.*

---

## 5. Execution Topology — [WF_CODE_V0]

*High-level DAG. JSONPath input bindings are authoring-phase detail.*

```
[IN_CODE_V0]
    ACK  → [CC_CODE_1_V0]
    NACK → EXIT

[CC_CODE_1_V0]                  ← [subdomain]
    SUCCESS       → [CC_CODE_2_V0]
    [outcome]     → EXIT
    VIOLATION     → EXIT
    BACKEND_ERROR → EXIT

[CC_CODE_2_V0]                  ← [subdomain]
    SUCCESS       → [CC_CODE_3_V0]
    [outcome]     → EXIT
    VIOLATION     → EXIT

...

EXIT
```

**Path summary:**
- [path name] path: [condition] → [steps] → EXIT
- [path name] path: [condition] → [steps] → EXIT
- Short-circuit exits: [conditions]

**Cross-subdomain calls in this WF:** [list any cross-subdomain CC calls and ownership statement]

---

## 6. CC Pipeline Declarations (Summary)

*Design-level pipeline intent for each new CC. Full JSONPath bindings are authoring-phase detail. Grouped by subdomain ownership.*

### [subdomain] Pipelines

**[CC_CODE_V0]** *([subdomain])*
- Step 1: [CS or CT code] — [operation] — [store or input] → [output]
- Step 2: [CS or CT code] — [operation] — [store or input] → [output]
- Result statuses: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR` [add domain-specific statuses: NOT_FOUND, EMPTY, ALREADY_EXISTS, etc.]
- *[Any cross-subdomain boundary notes]*

---

### [subdomain2] Pipelines

**[CC_CODE_V0]** *([subdomain2])*
- Step 1: [CS or CT code] — [operation] — [store or input] → [output]
- Result statuses: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`
- *[Boundary note: all writes are within [subdomain2] stores]*

---

## 7. Execution Topology — [WF_CODE_V0] (Re-authored, if applicable)

*If an existing WF is being re-authored (REPLACE), declare its topology here. State what changes from the flawed or prior version.*

```
[IN_CODE_V0]       ← [REPLACE / REUSE]: [reason]
    ACK  → [CC_CODE_V0]
    NACK → EXIT

...

EXIT
```

**Change from existing:** [Describe what topology or schema changes, and what stays the same.]

---

## 8. STRUCTURE Extension — [STRUCTURE_ARTIFACT_V0]

*New entity stores to be added to the existing structure artifact. Organized by subdomain governance.*

**[subdomain] subdomain stores:**

| Store Name | Storage Type | Proposed Path | Used By |
| --- | --- | --- | --- |
| [STORE_NAME] | [CS_APPENDONLY_JSONL_V0 / CS_MUTABLE_JSON_V0] | `[domain]/[subdomain]/[path/file]` | [CC_CODE_V0] |

**[subdomain2] subdomain stores (new subdomain):**

| Store Name | Storage Type | Proposed Path | Used By |
| --- | --- | --- | --- |
| [STORE_NAME] | [CS_APPENDONLY_JSONL_V0 / CS_MUTABLE_JSON_V0] | `[domain]/[subdomain2]/[path/file]` | [CC_CODE_V0] |

*Cross-subdomain write rule: [subdomain] CCs write only to [subdomain] stores. [subdomain2] CCs write only to [subdomain2] stores. No subdomain writes to another's stores.*

---

## 9. [CT_CODE_V0] — New Capability Transform (one section per new CT)

| Field | Value |
| --- | --- |
| Code | `[domain]::[CT_CODE_V0]` |
| Family | CT |
| Purity | ct_pure — no side effects |
| Operation | [OPERATION_NAME] |
| Inputs | `[input_name]` ([type]), `[input_name]` ([type]) |
| Output | `[output_name]` ([type]) |
| Algorithm | [Concrete algorithm description] |
| Failure | VIOLATION if [condition] |

---

## 10. [IN_CODE_V0] — Intent Schema (one section per new IN)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| [field] | [type] | YES / NO | [description] |

Outcomes: `ACK` (payload valid, proceed), `NACK` (payload invalid, reject)

---

## 11. Artifact Summary

*Artifact count by action type, for Stage 7 (Authoring Mandate) input.*

| Action | Count | Notes |
| --- | --- | --- |
| REPLACE | [n] | [artifact list] |
| EXTEND | [n] | [artifact list — e.g., STRUCTURE: adds N new stores] |
| NEW ([subdomain]) | [n] | [WF, IN, RB, CC×n, CT×n, EV×n] |
| NEW ([subdomain2]) | [n] | [CC×n, EV×n] |
| NEW ([dependency_subdomain]) | [n] | [CC×n] |
| **Total** | **[n]** | |

*Build dependency order is the output of Protocol Stage 7 — Authoring Mandate.*

---

## 12. Gate 1 — Design Approval

**Gate 1 closes here.** The full dossier (Stages 0–6b) is presented for review as a body. Any prior-stage artifact that was amended during the Stage 6–6b session is included in this review. This is not a per-stage approval — it is a unified review of the complete design.

**Key design decisions to confirm at Gate 1:**

1. [Key design decision — store/schema choice]
2. [Key design decision — algorithm or topology choice]
3. [Key design decision — cross-subdomain call pattern]
4. [Key design decision — reuse vs. replace artifact decision]
5. [Key design decision — artifact family assignment]
6. [Key design decision — new CT scope]
7. [Summary: N authoring actions total: N REPLACE, N EXTEND, N NEW]

*Gate 1 approval authorizes authoring of Stage 7 — Authoring Mandate. After Gate 1, the dossier (Stages 0–6b) is considered the approved design basis. Gate 2 (Mandate Approval, after Stage 7) locks the full dossier before artifact authoring begins.*

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 1 — Change Request & Input Elicitation | change_request_[subdomain]_v0.md | COMPLETE |
| Stage 2 — Domain Model Discovery | Actors, Entities, Resources, Events, Relationships | COMPLETE |
| Stage 3 — Analysis Loop | Capability Graph, Dependency Graph, Constraints, Gap Register | COMPLETE — SATURATED |
| Stage 4 — Business Model | business_model_[subdomain]_v0.md | COMPLETE |
| Stage 4b — Authoring Scope | IN/FUTURE CR boundary | COMPLETE — APPROVED |
| Stage 5 — Business Intent | business_intent_[subdomain]_v0.md | COMPLETE |
| Stage 6 — Governance Intent | governance_intent_[subdomain]_v0.md | COMPLETE — APPROVED |
| Stage 6b — Design Intent | This document | PENDING GATE 1 APPROVAL |
| Stage 7 — Authoring Mandate | Pending | — |
| Stage 8 — Authoring Manifest | Pending | — |

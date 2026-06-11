# Governance Intent: [domain] / [subdomain]
**Domain:** [domain]  
**Subdomain:** [subdomain]  
**Version:** V0  
**Status:** DRAFT  
**Pipeline Stage:** Stage 6 — Governance Intent (WHERE)  
**Produced by:** v0.5.0 SDLC authoring pipeline  
**Purity:** WHERE only — artifact family mapping, provisional artifact codes, and store declarations excluded  

---

## Stage Inputs — Questions for the Human

*Answer crisply before drafting. The right column states how the agent uses each answer.*

| # | Question for the Human | How the Agent Uses the Answer (Intent) |
|---|------------------------|----------------------------------------|
| 1 | Does this capability stand as its own subdomain, or extend an existing one — and why? | Becomes Section 1 Domain Placement. Subdomain existence is a governance topology declaration; it is never derived from the snapshot. |
| 2 | Under what authority class do these operations execute (existing ENDUSER/SYSTEM, or a new actor type)? | Becomes Section 2. A new actor type expands the CR scope; reuse must be stated explicitly. |
| 3 | For each capability that touches a peer subdomain: who should OWN it? | Drives Section 3 ownership tables. A capability that writes a peer's store MUST be owned by that peer (dependency gap) — the human decides whether to accept that ownership split or redesign the boundary. |
| 4 | Which boundary rules are non-negotiable for this subdomain? | Becomes Section 7 Governance Boundary Rules, the invariants conformance tests will enforce. |

**Agent execution rules for this stage:**
- **Cross-subdomain writes are forbidden — no exceptions.** Never mark one "Permitted". The conformant pattern is a dependency-gap CC owned by the store's subdomain, triggered by this CR (Sections 3/9 have a dedicated subsection for this).
- Cross-subdomain capability calls and data reads are permitted; declare each with explicit direction in Section 6.
- Existing artifacts are cited by exact FQDN (verified against the snapshot). New capabilities remain business-named here — binding codes are assigned in Stage 6b.
- Storage ownership follows the dedicated-STRUCTURE precedent: stores exclusively owned by a new subdomain get their own STRUCTURE artifact (see `STRUCTURE_BLOCKCHAIN_ORCHESTRATION_STORAGE_V0`) rather than extending a shared one — confirm the choice either way in Section 5.

---

## 1. Domain Placement

| Field | Value |
| --- | --- |
| Domain | `[domain]` |
| Primary subdomain | `[subdomain]` |
| Secondary subdomain | `[subdomain2]` — [NEW / EXISTING], [declared by this CR / existing governed namespace] |
| FQDN namespace | `[domain]` |
| [subdomain] status | [EXISTING — declared in PPS namespace topology / NEW — declared by this CR] |
| [subdomain2] status | [NEW — declared by this CR as a governed subdomain / EXISTING] |

*Describe the subdomain placement rationale. If declaring a new subdomain, explain why it stands alone rather than nesting under an existing one. Subdomain existence is a governance topology declaration — not derived from the presence of any artifact in the snapshot.*

---

## 2. Authority and Governance

| Concern | Governing Constitution |
| --- | --- |
| Actor authority | `fb.constitution::CONSTITUTION_GOVERNANCE_V0` |
| Execution topology (WF, IN, CC) | `fb.topology::CONSTITUTION_WORKFLOW_V0`, `fb.topology::CONSTITUTION_INTENT_V0`, `fb.topology::CONSTITUTION_CAPABILITY_CONTRACT_V0` |
| Storage topology | `fb.constitution::CONSTITUTION_STRUCTURE_V0` |
| Domain invariants | `[domain]::[INVARIANT_CODE]` |

*State the authority class under which operations execute. Declare whether a new authority class or actor type is required.*

---

## 3. Subdomain Boundary

### Owned by [subdomain] (this CR)

| Capability | Ownership Decision |
| --- | --- |
| [capability] | OWNED |

### Owned by [subdomain2] (new subdomain, declared this CR)

| Capability | Ownership Decision |
| --- | --- |
| [capability] | OWNED — `[domain]::[subdomain2]` |

*If subdomain2 is NEW: explain why it is not owned by the primary subdomain. State the cross-subdomain dependency direction explicitly.*

### Satisfied by existing subdomains — no ownership transfer

| Capability | Owned By | PPS Status |
| --- | --- | --- |
| [capability] | `[domain]::[existing_subdomain]` | SATISFIED — `[artifact FQDN]` reused |

### Deferred to future CRs — not owned this CR

| Capability | Reason |
| --- | --- |
| [capability] | Future CR — [reason] |

---

## 4. Composition — Extension Pattern

| Composition Decision | Detail |
| --- | --- |
| Domain | [Extend existing / Declare new] `[domain]` domain |
| Subdomain (primary) | [Extend existing / Declare new] `[subdomain]` namespace |
| Subdomain (secondary) | [Declare `[subdomain2]` as new governed namespace — if applicable] |
| Actor types | [Reuse existing / New actor type required: [name]] |
| Execution substrate | [Reuse existing capability substrate] |
| [dependency name] dependency | Cross-subdomain [read / capability call] — [capability]; `[domain]::[subdomain]` owned |
| Storage topology | [Extension required to / No change to] `[STRUCTURE_ARTIFACT_V0]` — see Section 5 |

*Cross-subdomain writes are forbidden — [subdomain] does not write to [other subdomain] stores.*

---

## 5. Storage Governance Requirements

*State what persistent storage is required, organized by subdomain governance. Design Intent (Stage 6b) declares actual store names and paths. This section declares the governance requirement, not the implementation.*

**[subdomain] subdomain storage:**
- [description of storage need] — [purpose]
- [description of storage need] — [purpose]

**[subdomain2] subdomain storage (if applicable):**
- [description of storage need] — [purpose]
- [description of storage need] — [purpose]

---

## 6. Cross-Subdomain Dependency Declaration

| Dependency | Direction | Existing PPS Artifact | Status |
| --- | --- | --- | --- |
| [capability] | [subdomain] → [other_subdomain] | `[FQDN or None]` | [SATISFIED — reuse / GAP — new capability required; owned by `[subdomain]`] |

---

## 7. Governance Boundary Rules

*Non-negotiable boundary rules for this subdomain. Each rule is a governance invariant, not an implementation detail.*

1. **[Rule name]** — [statement]
2. **[Rule name]** — [statement]
3. **[Rule name]** — [statement]

---

## 8. PPS Artifacts Requiring Action

*Existing PPS artifacts that must be reviewed or replaced as part of this CR.*

| Artifact | Current Status | Action |
| --- | --- | --- |
| `[domain]::[ARTIFACT_CODE_V0]` | [EXISTS — description] | [REPLACE / REVIEW / REUSE] — [reason] |

---

## 9. Governance Outcome

*Capabilities that require protocol realization. Design Intent (Stage 6b) determines which artifact family each maps to and assigns FQDN codes. Organized by subdomain ownership.*

**[subdomain] subdomain:**
- [capability]
- [capability]

**[subdomain2] subdomain (if applicable):**
- [capability]
- [capability]

**[other_subdomain] subdomain (dependency gap — new capability owned by [other_subdomain], triggered by this CR):**
- [capability] (cross-subdomain [read/call]; capability owned by [other_subdomain], not [subdomain])

---

## 10. Governance Summary

**Key decisions recorded in this document:**

1. [Decision point — domain/subdomain placement]
2. [Decision point — new subdomain declaration if applicable]
3. [Decision point — cross-subdomain dependency direction]
4. [Decision point — authority class]
5. [Decision point — storage governance]
6. [Decision point — ownership boundary rules]
7. [Decision point — deferred capabilities]

*This document is part of the Stage 1–6b iterative session. No per-stage approval gate. All governance decisions here are eligible for amendment as Design Intent (Stage 6b) develops new knowledge. Gate 1 (Design Approval) closes after Stage 6b — the full dossier is reviewed as a body at that point.*

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
| Stage 6 — Governance Intent | This document | COMPLETE |
| Stage 6b — Design Intent | Pending | — |
| Stage 7 — Authoring Mandate | Pending | — |
| Stage 8 — Authoring Manifest | Pending | — |

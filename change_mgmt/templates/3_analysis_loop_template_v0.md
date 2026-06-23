# Stage 3 — Analysis Loop: [domain] / [subdomain]
**Stage:** 3 — Analysis Loop  
**CR:** change_request_[subdomain]_v0.md  
**Status:** DRAFT  
**Feeds:** Stage 4 — Business Model  

> **S3 decides.** S1 discovers, S2 models, **S3 decides** — given what exists, *what should be
> authored?* Its signature output is the **Decision Classification** (REUSE / EXTEND /
> AUTHOR_NEW) for every capability. S3 resolves the extend-vs-new question S2 deferred, by
> evidence — never by assertion. Every decision traces to a grounded finding.

---

## Document Contract

**This artifact is a structured register document — not a narrative.** No free-form iteration
prose. Capture analysis, verification, and decisions as registers.

VALID OUTPUT:
- Populated register tables (every required register)
- Existing artifacts cited by exact FQDN in dependency / impact / evidence columns
- Business-language capability and rationale descriptions in decision registers

INVALID OUTPUT:
- Narrative summaries / reasoning essays replacing registers
- A decision with no grounded evidence; an assertion the snapshot did not confirm

A required register with no rows MUST render as a single `| NONE IDENTIFIED |` row. The renderer
rejects a prose-only or empty register mechanically before any human reviews it.

---

### Decision Classification (DECISION_CLASSIFICATION_REQUIRED)

S3's central artifact. Every capability the CR needs is classified:

- **REUSE** — an existing artifact satisfies it as-is (cite the FQDN).
- **EXTEND** — an existing artifact nearly satisfies it; a bounded change suffices (cite it).
- **AUTHOR_NEW** — nothing existing fits; a new artifact is required (business-language name only).

A REUSE/EXTEND decision MUST name the existing artifact (in `alternatives_checked`). An
AUTHOR_NEW decision MUST record which existing alternatives were examined and rejected — "I
searched and found nothing" is only credible with the search shown.

### Discovery Classification (carried from S2)

Each analysis finding carries an `evidence_status` and a `confidence`:

- **OBSERVED** — confirmed by a grounding call · **INFERRED** — reasoned, not directly verified ·
  **OPEN** — unresolved.
- Confidence ∈ **HIGH | MEDIUM | LOW** — a reviewer focuses on LOW-confidence findings.

---

### Stage 3 execution rules

- Every finding is answered by reading the snapshot directly (grounding tools) — quote the
  evidence; no assertion without it. `GROUNDING_NOT_INHERITED`: re-verify, never trust prior
  narrative.
- **Impact is mechanically captured, never summarized from memory** — the `impact_analysis`
  register records `pi topology impact` / `artifact_refs` output verbatim (consumer counts are
  evidence, not estimates).
- **Before any AUTHOR_NEW decision**, search the snapshot for an existing artifact that
  satisfies it and record the search in `alternatives_checked`.
- The **Mandatory Verification Pass** re-checks every prior assumption/finding against the
  snapshot (`verification_results`): CONFIRMED with fresh evidence or OVERTURNED.

---

## Stage Inputs — Questions for the Human (reference)

*Reference only — asked only where evidence cannot decide; not filled here.*

| # | Question for the Human | How the Agent Uses the Answer |
|---|------------------------|-------------------------------|
| 1 | Where evidence supports both "extend" and "new subdomain" — which boundary do you intend? | Locks the Placement Decision (a governance topology call only the human makes). |
| 2 | Reuse-with-compromise vs author-new — tolerance for each compromise? | Decides REUSE/EXTEND vs AUTHOR_NEW in the authoring_decisions register. |
| 3 | Any business policies (limits, privileged actors, monetary rules) not yet stated? | Recorded as findings; carried to the S4 Constraint Register. |

---

## 1. Analysis Findings

*One row per analysed question (from S2 open questions / prior iterations). resolution_status ∈ CLOSED | OPEN.*

<!-- register:analysis_findings -->
| Question Id | Finding | Impact | Evidence Status (OBSERVED, INFERRED, OPEN) | Confidence (HIGH, MEDIUM, LOW) | Resolution Status (CLOSED, OPEN) | Evidence |
|-------------|---------|--------|-----------------|------------|-------------------|----------|

---

## 2. Mandatory Verification Pass

*Re-verify every prior assumption/finding against the snapshot directly (grounding not inherited). Result ∈ CONFIRMED | OVERTURNED. An item that cannot be re-confirmed is an open gap, not a finding.*

<!-- register:verification_results -->
| Item | Origin | Result (CONFIRMED, OVERTURNED) | Evidence |
|------|--------|--------|----------|

---

## 3. Dependency Discoveries

*Cross-artifact dependencies surfaced during analysis (feeds S4 dependency graph + authoring order). Disposition ∈ EXISTING | REUSE | AUTHOR_NEW | INVESTIGATE.*

<!-- register:dependency_discoveries -->
| Dependency | Type | Disposition (EXISTING, REUSE, AUTHOR_NEW, INVESTIGATE) | Evidence |
|------------|------|-------------|----------|

---

## 4. Impact Analysis

*Mechanically captured consumer-closure / blast-radius for every artifact this CR touches. Evidence is the verbatim `pi topology impact` / `artifact_refs` output.*

<!-- register:impact_analysis -->
| Artifact | Impact Scope | Consumer Count | Evidence |
|----------|--------------|----------------|----------|

---

## 5. Authoring Decisions

*S3's signature output — the register of **committed** capability decisions. One row per capability: the Decision Classification, the alternatives examined, and the rationale. `capability` is business language (no FQDN — name the need, not the artifact); `decision` is a controlled vocabulary — **exactly one of REUSE / EXTEND / AUTHOR_NEW** (a final, committed call; INVESTIGATE is NOT valid here). `rationale` and `alternatives_checked` may cite existing FQDNs as justification/evidence.*

> **Promotion rule.** This register records only capabilities whose disposition is COMMITTED. A
> capability still under investigation does NOT belong here — it stays in §3 Dependency Discoveries
> with `Disposition = INVESTIGATE` and is promoted to an Authoring Decision only once analysis
> resolves it to REUSE / EXTEND / AUTHOR_NEW. Never carry an unresolved item into both registers.

<!-- register:authoring_decisions business_language=capability -->
| Capability | Decision (REUSE, EXTEND, AUTHOR_NEW) | Rationale | Alternatives Checked | Source Finding |
|------------|----------|-----------|----------------------|----------------|

---

## 6. Subdomain Placement Decision

*The extend-vs-new resolution S2 deferred — a governance topology call. Decision ∈ NEW_SUBDOMAIN | EXTEND.*

<!-- register:placement_decision business_language=subdomain -->
| Decision (NEW_SUBDOMAIN, EXTEND) | Subdomain | Rationale | Source Finding |
|----------|-----------|-----------|----------------|

---

## 7. Saturation Assessment

*Analysis is saturated only when every criterion is SATISFIED. Status ∈ SATISFIED | NOT_SATISFIED.*

<!-- register:saturation business_language=criterion -->
| Criterion | Status (SATISFIED, NOT_SATISFIED) | Evidence |
|-----------|--------|----------|

*Required criteria: (1) no unresolved CRITICAL gaps; (2) no open analyst questions; (3) no dependency expansion in the last pass; (4) verification pass complete, no OVERTURNED item unresolved; (5) every INFERRED finding promoted to OBSERVED, explicitly accepted, or carried forward with a reason.*

---

## gov_projection — Governed Handoff to Stage 4

*Governed, lossless, identity-preserving (Stage 0 / field manual §4.7). The decision registers cross to S4; the analysis/verification/impact registers are S3's audit trail (not re-derived downstream). Emit keys match the register ids above.*

*The bounded inputs and emit keys mirror the engine's gov_projection schema exactly
(`contracts/gov_projection.py`): S3 consumes the S1 framing plus S2's discovery output.*

| Direction | Fields |
|-----------|--------|
| **Consumes** ← Stage 1 | cr_type · assumptions · business_invariants · lifecycle_states · business_events · authority_boundaries |
| **Consumes** ← Stage 2 | belief_verification · pps_baseline_fqdns · gaps · architectural_observations · discovery_concerns · open_questions |
| **Emits** → Stage 4 | authoring_decisions · dependency_discoveries · placement_decision · saturation |

# Authoring Manifest: [domain] / [subdomain]
**Domain:** [domain]  
**Subdomain:** [subdomain]  
**Version:** V0  
**Status:** DRAFT  
**Pipeline Stage:** Stage 8 — Authoring Manifest  
**Produced by:** v0.5.0 SDLC authoring pipeline  
**Produced after:** Created as the pre-authoring baseline at Stage 7 close; populated during/after authoring  

---

## Document Contract

**This artifact is a structured register document — not a narrative.** S8 is the manifest: it
records the as-built reality of the CR (deviations, discoveries, as-designed-vs-as-built, dividend
metrics, future-CR candidates). The worker emits register ROWS; a deterministic renderer owns the
document.

VALID OUTPUT:
- Populated register tables (every required register below)
- Empty `optional` registers render as `| NONE IDENTIFIED |` — a legitimate baseline state

INVALID OUTPUT:
- Narrative summaries / reasoning essays replacing registers
- Grounding searches for not-yet-authored artifacts (see the baseline rule below)

---

### Pre-authoring baseline — do NOT ground the build_order codes

**This stage is created BEFORE artifact authoring.** Artifact authoring, compilation, and runtime
testing happen AFTER Gate 2 — i.e. AFTER this document. The Stage 7 `build_order` codes therefore
do **not** yet exist in the snapshot. **Do NOT ground / verify them** — a grounding search for a
not-yet-authored code returns 0 results BY DESIGN; that is not a discovery to chase or a reason to
keep searching. At baseline:

- `as_designed_vs_built` carries the mandated artifacts from Stage 7 `build_order` (verbatim codes)
  with `as_built` = `PENDING` and `delta` = `PENDING` until real authoring fills them.
- `dividend_metrics` carries the mandated counts from Stage 7 `mandate_artifact_summary`; the
  execution rows (conformance, snapshot status) are `PENDING`.
- `deviations`, `discoveries`, `future_cr_candidates` are typically empty at baseline.

`Status: DRAFT` until the Completion Criterion is met with real execution data — never aspirationally.

---

## Stage Inputs — Questions for the Human

| # | Question for the Human | How the Agent Uses the Answer (Intent) |
|---|------------------------|----------------------------------------|
| 1 | For each deviation from the Design Intent encountered during authoring: approve, or send back for redesign? | Approved deviations are recorded in `deviations` with rationale; rejected ones reopen Stage 6b. Nothing deviates silently. |
| 2 | Which discoveries and lessons should be carried forward (future CR candidates, methodology rules, template fixes)? | Populates `discoveries` / `future_cr_candidates` — the pipeline's feedback loop into the templates. |

---

## 1. Approved Deviations

*Deviations from Design Intent approved during authoring. Each references the DI artifact it departs from and states the governance rationale. Empty at baseline.*

<!-- register:deviations optional -->
| Artifact | DI Reference | Deviation | Rationale |
|----------|--------------|-----------|-----------|

---

## 2. Discoveries

*Findings that emerged during authoring or runtime. `type` ∈ ARCHITECTURAL (architecture needed correction) | IMPLEMENTATION (correct architecture not yet adopted) | CT_VOCABULARY (transform atom missing/mis-used) | SURFACE_ALIGNMENT (declared result surface ≠ CS-produced status). Empty at baseline.*

<!-- register:discoveries optional -->
| Discovery | Type (ARCHITECTURAL, IMPLEMENTATION, CT_VOCABULARY, SURFACE_ALIGNMENT) | Impact | Disposition |
|-----------|------------------------------------------------------------------------|--------|-------------|

---

## 3. Unexpected Constraints

*Constraints encountered during authoring that blocked, redirected, or modified the implementation from what Design Intent specified.*

<!-- register:unexpected_constraints optional -->
| Constraint | Affected Artifacts | Resolution |
|------------|--------------------|------------|

---

## 4. Governance Findings

*New governance knowledge produced by this CR — boundary decisions, ownership clarifications, or protocol rules discovered through implementation.*

<!-- register:governance_findings optional -->
| Finding | Type | Governance Implication |
|---------|------|------------------------|

---

## 5. Amendments to Intent

*Changes required to any prior-stage artifact (BI, GI, DI) based on what was learned during authoring. Recorded here; the prior-stage documents are updated separately if needed.*

<!-- register:amendments optional -->
| Stage Artifact | Amendment | Reason |
|----------------|-----------|--------|

---

## 6. Future CR Candidates

*Capabilities, constraints, or concerns that surfaced during this CR but are explicitly deferred — each a candidate input for a future Change Request.*

<!-- register:future_cr_candidates optional -->
| Concept | Domain / Subdomain | Priority (HIGH, MEDIUM, LOW) | Notes |
|---------|--------------------|------------------------------|-------|

---

## 7. As-Designed vs. As-Built Reconciliation

*Delta between Design Intent (as-designed) and implemented artifacts (as-built). `as_designed` carries the Stage 7 build_order codes verbatim; `as_built` and `delta` are `PENDING` at baseline, filled from real authoring/execution.*

<!-- register:as_designed_vs_built -->
| Concern | As-Designed | As-Built | Delta |
|---------|-------------|----------|-------|

---

## 8. Governed Evolution Metrics

*One row per metric. Mandated counts come from Stage 7 `mandate_artifact_summary`; execution rows (conformance, snapshot status) are `PENDING` at baseline.*

<!-- register:dividend_metrics -->
| Metric | Value |
|--------|-------|

---

## 9. Completion Criterion

This manifest moves `DRAFT → APPROVED` when, with **actual execution data**:

1. All registers are populated (no `PENDING` rows remain)
2. All protocol artifacts are compiled and present in `protocol_snapshot/`
3. All test scenarios execute and produce the expected decision; the S1 `requested_outcomes` / `acceptance_criteria` are met
4. All traces are verified (non-empty, correct decision, correct denial reason where applicable)
5. The determinism invariant holds (primary scenario re-run → same TRACE_ID)
6. No existing artifact outside the declared scope was modified

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 7 — Authoring Mandate | authoring_mandate_[subdomain]_v0.md | COMPLETE |
| Protocol Artifacts | per build_order | PENDING AUTHORING |
| Runtime Execution Testing | scenarios × expected decision × trace verification; determinism re-run | PENDING |
| Stage 8 — Authoring Manifest | This document | DRAFT (baseline) |
| Stage 9 — CR Closure | See Completion Criterion | PENDING |

---

## gov_projection — Governed Handoff to Stage 9 (CR Closure)

*The bounded inputs and emit keys mirror the engine's gov_projection schema exactly
(`contracts/gov_projection.py`). S8 validates the build against the S1 acceptance boundary and
records the as-built reality. Emit fields cross to CR closure (CLOSURE); §3 Unexpected Constraints,
§4 Governance Findings, and §5 Amendments are recorded here but are not forwarded fields. Emit keys
match the register ids above exactly.*

| Direction | Fields |
|-----------|--------|
| **Consumes** ← Stage 1 | requested_outcomes · acceptance_criteria |
| **Consumes** ← Stage 7 | build_order · critical_path · mandate_artifact_summary · field_declarations |
| **Emits** → Stage 9 (closure) | deviations · discoveries · as_designed_vs_built · dividend_metrics · future_cr_candidates |

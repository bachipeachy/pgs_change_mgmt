# Build Sheet Set: [domain] / [subdomain]
**Domain:** [domain]  
**Subdomain:** [subdomain]  
**Version:** V0  
**Status:** DRAFT  
**Pipeline Stage:** Stage 8 — Build Sheet Set  
**Governed By:** CONSTITUTION_BUILD_SHEET_V0  
**Source Mandate:** 7_authoring_mandate_[subdomain]_v0.md (Gate 2: [APPROVED|PENDING])  
**Set Readiness:** DESIGNED | BUILDABLE | CONSTRUCTION-CLOSED  

---

## Document Contract

**This artifact is the construction projection — the final stage that removes every remaining design
degree of freedom.** It is **ASSEMBLED, not authored**: a deterministic assembler copies governed
design from S2/S5/S6b/S7 (per-CC composition comes verbatim from S6b `cc_composition`) and adds
compiler/runtime expectations + verification + acceptance. It contains **no new design**.

VALID OUTPUT:
- One Build Sheet per row of the S7 `build_order`, in `step` order
- Every field traceable to a governed source (S2/S5/S6b/S7); no invented value
- A missing/conflicting fact rendered as a classified GAP (§gap_census) — never invented

INVALID OUTPUT:
- Any design decision left to the builder (= a governance failure → classified GAP)
- A field with no governed source; an inferred decision presented as fact

### Discipline (Phase 4 oracles enforce these)
- No new design. A required decision discovered here is a GAP, resolved upstream (S5–S7).
- Construction is a constrained transformation from governed intent into protocol syntax —
  transcription, not synthesis. The builder (human / LLM / generator) is interchangeable.
- Routing is by OUTCOME only; `if:`/expression routing is unrepresentable.

> **Note:** S8 is produced by the deterministic assembler (not the structured-worker path) and is not
> part of the default S1→S7 dossier run. `build_sheets` below is the assembled body; `gap_census` is
> the machine-forwarded register.

---

## Construction Readiness — oracles + ladder

Ladder (monotonic): `DESIGNED → BUILDABLE → CONSTRUCTION_READY → CONSTRUCTION_CLOSED → IMPLEMENTED → RUNTIME_VALIDATED`.

**Static gate → `CONSTRUCTION_READY`** (everything required exists): three statically-checkable asserts:

| Assert | Holds when |
|--------|-----------|
| ASSERT_STRUCTURE_COMPLETE | every required Part A + Part B field exists for the kind |
| ASSERT_PROVENANCE_COMPLETE | every field is sourced (confidence not UNRESOLVED / INFERRED) |
| ASSERT_DECISION_COMPLETE | no GAP remains — no design choice left to the builder |

**Empirical gate → `CONSTRUCTION_CLOSED`** (construction *demonstrated* zero design invention):

| Assert | Holds when |
|--------|-----------|
| ASSERT_ZERO_DESIGN_INVENTION | a build introduced no design decision (independent builders converge) — DEMONSTRATED, never statically proven |

`CONSTRUCTION_READY` is the static gate the projection + `build_sheet_oracle` reach; only a real build
(Phase 5, e.g. qwen3:14b vs qwen3.5 convergence) moves a set to `CONSTRUCTION_CLOSED`.

---

## Set Reconciliation (vs S7 build_order)

| Check | Expectation |
|-------|-------------|
| Sheet count | == rows in S7 build_order |
| Codes | every sheet `code` verbatim in S7 build_order; no extras/drops |
| Order | by S7 `step`, contiguous from 1 |
| Action counts | NEW/REPLACE/EXTEND == S7 mandate_artifact_summary |

---

## Build Sheets (assembled body — one per S7 build_order row)

*Repeats per artifact. Part A Governing Truth (stable) · Part B Construction Specification
(obligation language, kind-specific) · Part C Admissibility (ASSERT_BUILDABLE) · Part D GAPs. Every
field carries a provenance object {primary · corroborated_by · confidence}.*

### Build Sheet [step] — [code]   [action · wave · subdomain]   Readiness: [state]

**Part A — Governing Truth** *(assembled from S2/S5/S6b)*  
purpose · authority · dependencies · reuse · invariants · acceptance — each with provenance.

**Part B — Construction Specification** *(obligation language; kind-specific protocol_sections)*  
builder shall construct: [pipeline/graph/bindings/schema — from S6b cc_composition + topology + RB]  
builder shall demonstrate: [verification commands]  
builder shall verify: [runtime obligations, or compile-only]  
compiler_mapping: [stage + asserts that must hold]

**Part C — Admissibility** — ASSERT_BUILDABLE preconditions met (purpose/authority/deps/compiler/runtime frozen; no unresolved GAP_IMPLEMENTATION; exactly one valid construction).

**Part D — GAPs** — this sheet's classified gaps (see §gap_census).

---

## GAP Census

*Classified gaps that block CONSTRUCTION-CLOSED — the governance dashboard. Class ∈ GAP_SEED,
GAP_DOSSIER, GAP_ARCHITECTURAL_DRIFT, GAP_DECISION, GAP_IMPLEMENTATION, GAP_POLICY, GAP_REUSE,
GAP_COMPILER, GAP_RUNTIME. Empty (`NONE IDENTIFIED`) is the CONSTRUCTION-CLOSED case.*

<!-- register:gap_census optional -->
| GAP id | Class | Sheet (Code) | Found By | Closed By (upstream) |
|--------|-------|--------------|----------|----------------------|

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 7 — Authoring Mandate | 7_authoring_mandate_[subdomain]_v0.md | GATE 2 [APPROVED|PENDING] |
| Stage 8 — Build Sheet Set | This document | [DESIGNED|BUILDABLE|CONSTRUCTION-CLOSED] |
| Construction | per Build Sheet | PENDING |
| Stage 9 — Construction Record | post-construction | PENDING |

---

## gov_projection — Governed Handoff

*S8 ASSEMBLES (does not author). Consumed inputs come from S2/S5/S6b/S7; it emits the Build Sheet Set
and the GAP census to S9. Emit keys match the schema exactly.*

| Direction | Fields |
|-----------|--------|
| **Consumes** ← Stage 6b | cc_composition · new_artifacts · existing_inventory · rb_declarations · execution_topology |
| **Consumes** ← Stage 7 | build_order · critical_path · field_declarations · mandate_artifact_summary |
| **Consumes** ← Stage 2 / 5 | entity_attributes · invariants · actions (Part A corroboration) |
| **Emits** → Stage 9 | build_sheets · gap_census |

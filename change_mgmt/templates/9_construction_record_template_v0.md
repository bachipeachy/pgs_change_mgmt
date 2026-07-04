# Construction Record: [domain] / [subdomain]
**Domain:** [domain]  
**Subdomain:** [subdomain]  
**Version:** V0  
**Status:** DRAFT  
**Pipeline Stage:** Stage 9 — Construction Record  
**Governed By:** fb.change_mgmt::CONSTITUTION_CONSTRUCTION_V0  
**Source Build Sheet:** 8_build_sheet_[subdomain]_v0.md  

---

## Document Contract

**This artifact records what actually happened during construction — EVIDENCE ONLY. It contains NO
design, NO architecture, NO planning.** Construction performs the work the S8 Build Sheet specified;
S9 records the result. A missing *design* decision discovered during construction is NEVER resolved
here: the build fails, returns upstream (S5–S7), and re-enters through S8. S9 never moves design
authority after implementation.

VALID OUTPUT:
- Built artifacts reconciled against the S8 Build Sheet Set
- Compiler / runtime evidence, with paths
- Approved deviations (explicit, never silent), discoveries, waived issues, future-CR candidates

INVALID OUTPUT:
- Any new artifact design, schema, routing, binding, or composition decision (that belongs upstream)
- A silent deviation (a departure from the Build Sheet with no approval row)

A required register with no rows renders as `| NONE IDENTIFIED |`.

---

## 1. Artifacts Built

*Reconcile against the S8 Build Sheet Set — every CONSTRUCTION-CLOSED sheet should have a built
artifact. `built_by` names the construction mechanism (human / qwen / Claude / generator).*

<!-- register:artifacts_built -->
| Code | Action (REPLACE, EXTEND, NEW) | Built (YES, NO) | Built By | Source Finding |
|------|-------------------------------|-----------------|----------|----------------|

---

## 2. Compiler Result

*The objective oracle. `result` is the compile / `pi validate` verdict; `asserts` names the governing
asserts that held (e.g. S4_GOVERN ASSERT_TOPOLOGY_ROUTING_COMPLETE); `evidence` is a path.*

<!-- register:compiler_result -->
| Code | Result (PASS, FAIL) | Asserts Held | Evidence | Source Finding |
|------|---------------------|--------------|----------|----------------|

---

## 3. Runtime Result

*Observed runtime behavior where exercised, else `COMPILE_ONLY`. `evidence` is a trace path.*

<!-- register:runtime_result -->
| Code or Workflow | Exercised (YES, COMPILE_ONLY) | Outcome / Trace | Evidence | Source Finding |
|------------------|-------------------------------|-----------------|----------|----------------|

---

## 4. Approved Deviations

*Any departure from the S8 Build Sheet — explicit, approved, never silent. Empty is the healthy case.*

<!-- register:approved_deviations optional -->
| Code | Sheet Specified | Built Instead | Approved By | Reason |
|------|-----------------|---------------|-------------|--------|

---

## 5. Discoveries / Unexpected Findings

*Facts surfaced during construction. Not design — observation.*

<!-- register:discoveries optional -->
| Finding | Impact | Disposition |
|---------|--------|-------------|

---

## 6. Waived Issues

*Issues accepted as-is, with rationale and the authority who accepted the risk.*

<!-- register:waived_issues optional -->
| Issue | Why Waived | Risk Accepted By |
|-------|------------|------------------|

---

## 7. Future CR Candidates

*Work spun out, not done here (e.g. a deferred GAP_ARCHITECTURAL_DRIFT).*

<!-- register:future_cr_candidates optional -->
| Candidate | Why Deferred |
|-----------|--------------|

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 7 — Authoring Mandate | 7_authoring_mandate_[subdomain]_v0.md | GATE 2 APPROVED |
| Stage 8 — Build Sheet Set | 8_build_sheet_[subdomain]_v0.md | CONSTRUCTION-CLOSED |
| Construction | per Build Sheet | COMPLETE |
| Stage 9 — Construction Record | This document | COMPLETE |

---

## gov_projection — Governed Handoff (terminal → CR closure)

*S9 is EVIDENCE ONLY. It consumes the Build Sheet Set it reconciles against and emits the
construction record to CR closure. Emit keys match the register ids above exactly.*

| Direction | Fields |
|-----------|--------|
| **Consumes** ← Stage 8 | build_sheets · gap_census |
| **Emits** → CR closure | artifacts_built · compiler_result · runtime_result · approved_deviations · discoveries · waived_issues · future_cr_candidates |

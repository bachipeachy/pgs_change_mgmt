# pgs_change_mgmt

**Governed SDLC change management pipeline for Protocol-Governed Systems.**

The governed change-management subsystem of Protocol-Governed Systems (PGS). Drives every Change Request through a governed, gated pipeline from problem statement to authoring mandate — producing a complete dossier before any protocol artifact is touched.

> *Intent declared. Design approved. Mandate issued. Artifacts authored.*

---

## Status — v0.5.0 (Upcoming)

This repository makes its public debut in **PGS v0.5.0**.

The v0.4.0 release established the full PGS execution backend — governance substrate, compiler, runtime, deterministic traces, and eight governed repos. v0.5.0 adds `pgs_change_mgmt` — the governed authoring layer that closes the loop between human intent and admissible protocol topology.

v0.5.0 will include the complete pipeline implementation and the first end-to-end dossier authoring cycle.

---

## What It Is

`pgs_change_mgmt` governs the **Change Request → Protocol Artifact** lifecycle. Every protocol change begins with a Change Request and must complete a governed stage pipeline before any artifact is authored:

```
Stage 1  — Change Request & Input Elicitation  (classification + problem / outcome / known facts)
Stage 2  — Domain Model Discovery
Stage 3  — Analysis Loop  (Capability, Dependency, Constraint, Gap Register)
Stage 4  — Business Model  (canonical dossier artifact)
Stage 4b — Authoring Scope  (IN / FUTURE CR boundary)
Stage 5  — Business Intent  (projection)
Stage 6  — Governance Intent  (WHERE)
Stage 6b — Design Intent  (HOW)
Stage 7  — Authoring Mandate  (mandated build sequence — topological sort of DI dependency graph)

    ↓  protocol artifact authoring + testing  ↓

Stage 8  — Authoring Manifest  (as-designed vs. as-built reconciliation; pre-authoring baseline populated during execution)
Stage 9  — CR Closure  (populate all PENDING sections with actual data; verify completion criteria; record governance artifacts and methodology lessons; transition manifest status to APPROVED)
```

The pipeline has **two approval gates** — not one per stage. Stages run as a continuous, iterative session between gates; any prior-stage artifact may be amended as new knowledge accumulates before the gate closes.

**Gate 1 — Design Approval (after Stage 6b):** The full dossier (Stages 1–6b) is reviewed as a body. Approval authorizes authoring of the Stage 7 Authoring Mandate.

**Gate 2 — Mandate Approval (after Stage 7):** The Authoring Mandate is reviewed. Approval authorizes protocol artifact authoring to begin. No artifact may be authored before Gate 2 passes. After Gate 2, Stages 1–7 artifacts are locked.

For simple CRs (bug, small feature), Gate 1 and Gate 2 may collapse to a single review session. No stage may be skipped.

**Stage 9 is mandatory.** The Authoring Manifest is generated as a pre-authoring baseline (Stage 8) and must be completed post-execution (Stage 9). A CR is not closed until all PENDING sections carry actual execution data and the manifest status is APPROVED.

---

## Dossier-First Ontology

The primary unit is the **governed change dossier** — not the artifact type. All stage documents for one Change Request live flat inside the dossier directory, each filename prefixed with its pipeline stage number so the directory lists in stage order:

```
change_mgmt/dossiers/[domain]/[subdomain]/
  1_change_request_[subdomain]_v0.md
  1_input_elicitation_[subdomain]_v0.md
  2_domain_model_[subdomain]_v0.md
  3_analysis_loop_[subdomain]_v0.md
  4_business_model_[subdomain]_v0.md
  5_business_intent_[subdomain]_v0.md
  6_governance_intent_[subdomain]_v0.md
  6b_design_intent_[subdomain]_v0.md
  7_authoring_mandate_[subdomain]_v0.md
  8_authoring_manifest_[subdomain]_v0.md   ← produced after authoring closes
```

The stage-template set under `change_mgmt/templates/` uses the same stage-number prefixes (`0_agent_context` … `8_authoring_manifest`).

---

## Where This Fits

| Repo | Role |
|------|------|
| `pgs_governance` | Constitutional governance, invariant enforcement, FB_CHANGE_MGMT constitution |
| `pgs_compiler` | Compiler pipeline; admissibility construction |
| `pgs_transport` | Ingress/egress adapters |
| `pgs_runtime` | Execution engine |
| `pgs_capabilities` | Governed capability substrate |
| `pgs_blockchain` | Blockchain domain |
| `pgs_ai_governance` | AI governance domain |
| **`pgs_change_mgmt` ← here** | **Governed SDLC pipeline — Change Request to Authoring Mandate** |
| `pgs_workspace` | Entry point — snapshot + scripts + runtime execution |

---

## License

Apache-2.0. See LICENSE and NOTICE for details.

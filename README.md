# pgs_change_mgmt

**Governed SDLC change management pipeline for Protocol-Governed Systems.**

The governed change-management subsystem of Protocol-Governed Systems (PGS). Drives every Change Request through a governed, gated pipeline from problem statement to authoring mandate — producing a complete dossier before any protocol artifact is touched.

> *Intent declared. Design approved. Mandate issued. Artifacts authored.*

---

## Status — v0.5.0 (Upcoming)

This repository makes its public debut in **PGS v0.5.0**.

The v0.4.0 release established the full PGS execution backend — governance substrate, compiler, runtime, deterministic traces, and eight governed repos. `pgs_change_mgmt': the governed authoring layer that closes the loop between human intent and admissible protocol topology.

v0.5.0 will include the complete pipeline implementation and the first end-to-end dossier authoring cycle.

---

## What It Is

`pgs_change_mgmt` governs the **Change Request → Protocol Artifact** lifecycle. Every protocol change begins with a Change Request and must complete a governed stage pipeline before any artifact is authored:

```
Stage 0  — Change Request Classification
Stage 1  — Input Elicitation
Stage 2  — Domain Model Discovery
Stage 3  — Analysis Loop  (Capability, Dependency, Constraint, Gap Register)
Stage 4  — Business Model  (canonical dossier artifact)
Stage 4b — Authoring Scope  (IN / FUTURE CR boundary)
Stage 5  — Business Intent  (projection)
Stage 6  — Governance Intent  (WHERE)
Stage 6b — Design Intent  (HOW)
Stage 7  — Authoring Mandate  (mandated build sequence — topological sort of DI dependency graph)

    ↓  protocol artifact authoring + testing  ↓

Stage 8  — Authoring Manifest  (as-designed vs. as-built reconciliation; closes the feedback loop)
```

Each stage is gated by a Governance Decision Gate. No stage may be skipped. No stage may begin before the prior gate is satisfied.

---

## Dossier-First Ontology

The primary unit is the **governed change dossier** — not the artifact type. All stage documents for one Change Request live flat inside:

```
change_mgmt/dossiers/[domain]/[subdomain]/
  change_request_[subdomain]_v0.md
  business_model_[subdomain]_v0.md
  business_intent_[subdomain]_v0.md
  governance_intent_[subdomain]_v0.md
  design_intent_[subdomain]_v0.md
  authoring_mandate_[subdomain]_v0.md
  authoring_manifest_[subdomain]_v0.md   ← produced after authoring closes
```

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

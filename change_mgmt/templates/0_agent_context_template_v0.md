# Agent Context — Reading Assignment for the Change-Management Pipeline

**Version:** V0

**Role:** Loaded FIRST, at CR start, together with `1_change_request_template_v0.md`.

**Purpose:** This is the agent's reading assignment. Before drafting any dossier document, the agent must load and read the context declared here. The human supplies governed knowledge through elicitation; the agent supplies verified knowledge by reading this set. An agent that drafts without completing this assignment is guessing.

---

## How to Use This Document

1. At the start of a Change Request, open this file alongside `1_change_request_template_v0.md`.
2. Read every **required** document below before drafting Stage 1. Read **optional** documents when the CR's scope touches their subject.
3. Re-consult the relevant items at each later stage (the snapshot inventory before authoring; the change-management paper before each gate; sibling dossiers throughout).
4. If a **required** document is missing or unreadable, stop and report it — do not proceed on assumption.

**Path resolution.** Doctrine and snapshot artifacts live in the `pgs_workspace` repository (a sibling of `pgs_change_mgmt`). Templates and dossiers live in this repository under `change_mgmt/`. Paths below are relative to those two roots as noted.

---

## Reading Assignment

| # | Document | Path (root) | Role | Why the Agent Reads It | Required |
|---|----------|-------------|------|------------------------|----------|
| 1 | PGS Field Manual | `doc/pgs_field_manual_v0.md` (workspace) | Primary | Naming conventions, the nine execution concerns, FQDN format, repo ownership, compile-time vs runtime boundary, and §4 the change-management pipeline itself. Read before interpreting any spec or drafting any stage. | **YES** |
| 2 | Closed-Loop Governed Evolution | `doc/pgs_change_management_conceptual_model_v0.md` (workspace) | Doctrine | The conceptual model for this pipeline: stages, purity ladder, gates, Discovery Saturation, the elicitation contract. This is the doctrine the agent is executing. | **YES** |
| 3 | PPS Snapshot Inventory | `pps_snapshot/index.json` (workspace) | Inventory | The full inventory of compiled artifacts — what already exists. The agent MUST check this before proposing any new artifact, to reuse rather than re-author. Load FQDN keys only (`domain::ARTIFACT` entries) to keep context manageable. | **YES** |
| 4 | Prior & Sibling Dossiers | `change_mgmt/dossiers/<domain>/<subdomain>/` (this repo) | Evidence | The evidence chain of completed CRs in the same domain/subdomain. Establishes the governed baseline this CR modifies — nothing is greenfield. Read peers before declaring entities, gaps, or boundaries. | **YES** |
| 5 | PGS Conceptual Model | `doc/pgs_conceptual_model_v0.md` (workspace) | Grounding | How artifacts relate, execution flow, governance-layer relationships. Structural mental model before reading specs. | optional |
| 6 | PGS Tech Paper v2 | `doc/techpaper_protocol-governed_systems_v2.md` (workspace) | Grounding | Why PGS exists; protocol-sovereignty rationale. Context for why invariants are non-negotiable. | optional |
| 7 | Onboarding: First Workflow | `doc/onboarding_build_first_workflow.md` (workspace) | Example | A worked decomposition of a requirement into WF/CC/CT/CS artifacts — what a correct Stage 6b decomposition looks like in practice. | optional |
| 8 | Stage Templates | `change_mgmt/templates/*_template_v0.md` (this repo) | Working | The template for the stage currently being authored, read immediately before drafting that stage. Each opens with its own elicitation contract and execution rules. | per stage |

---

## Per-CR Checklist

Tick before drafting Stage 1:

- [ ] Field manual read (esp. §4 pipeline, naming, FQDN rules)
- [ ] Change-management concept paper read (stages, purity ladder, gates)
- [ ] PPS snapshot inventory loaded (FQDN keys) — baseline of what already exists
- [ ] Sibling/prior dossiers in this `<domain>/<subdomain>` reviewed
- [ ] Optional grounding read as scope requires (conceptual model / tech paper / onboarding)

Carry forward at each stage:

- [ ] Re-check the PPS inventory before naming any NEW artifact (reuse beats re-author)
- [ ] Re-read the change-management paper's gate criteria before Gate 1 (Design Approval) and Gate 2 (Mandate Approval)
- [ ] Open the relevant stage template immediately before drafting that stage

---

## Extending the Assignment

To add a document to the agent's awareness, add a row to the Reading Assignment table — declare its path, role, why it is read, and whether it is required. Awareness is extended by declaration here, never by hardcoding paths into agent logic.

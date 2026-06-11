# Authoring Mandate: [domain] / [subdomain]
**Domain:** [domain]  
**Subdomain:** [subdomain]  
**Version:** V0  
**Status:** DRAFT  
**Pipeline Stage:** Stage 7 — Authoring Mandate  
**Produced by:** v0.5.0 SDLC authoring pipeline  

---

## Stage Inputs — Questions for the Human

| # | Question for the Human | How the Agent Uses the Answer (Intent) |
|---|------------------------|----------------------------------------|
| 1 | Gate 2: do you approve this mandate, locking the dossier before artifact authoring begins? | Gate 2 approval freezes scope. After it, any departure from this mandate is an Approved Deviation recorded in the Stage 8 manifest — not a silent change. |
| 2 | Any sequencing constraints beyond the dependency graph (e.g., author a risky artifact first)? | Adjusts wave ordering without changing the dependency-derived topological order. |

**Agent execution rules for this stage:**
- This stage is mechanical: it re-derives build order from the Stage 6b dependency graph. **No new design decisions, no added or dropped artifacts.** If something looks wrong, fix Stage 6b and re-derive.
- Reconcile before completion: the artifact list here must equal the Stage 6b Artifact Summary exactly — same artifacts, same actions, same counts. Step numbering must be contiguous (a missing step number usually means an artifact was silently dropped).
- Every cross-subdomain note must respect: calls/reads permitted, writes forbidden.

---

## 1. Build Dependency Order

Derived by topological sort of the artifact dependency graph produced in Stage 6b (Design Intent). Parallel work is grouped into waves. The critical path is the longest sequential dependency chain.

### Wave 1 — Parallel (no dependencies)

| Step | Artifact | Action | Subdomain | Depends On |
|------|----------|--------|-----------|------------|

### Wave 2 — Parallel (after Wave 1 prerequisites)

| Step | Artifact | Action | Subdomain | Depends On |
|------|----------|--------|-----------|------------|

*(add waves as needed)*

---

## 2. Critical Path

Steps: [list critical path step numbers in sequence]

---

## 3. Artifact Summary

| Count | Action | Description |
|-------|--------|-------------|
| — | REPLACE | Artifacts authored through prior pipeline that require re-authoring |
| — | EXTEND | Existing artifacts receiving new stores or fields |
| — | NEW | Net-new artifacts |
| **Total** | | |

---

## 4. Subdomain Field Declarations

| Artifact Code | Subdomain Field Value |
|---|---|

*Subdomain field must be declared for every WF, CC, EV, RB artifact. Governs trace routing and data store path resolution.*

---

## 5. Cross-Subdomain Dependency Notes

Document any artifacts that make cross-subdomain calls (permitted) or cross-subdomain writes (forbidden).

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 6b — Design Intent | design_intent_[subdomain]_v0.md | GATE 1 APPROVED |
| Stage 7 — Authoring Mandate | This document | PENDING GATE 2 APPROVAL |
| Stage 8 — Authoring Manifest | Pending | — |

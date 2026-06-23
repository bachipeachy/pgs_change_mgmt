# pgs_change_mgmt

**Governed SDLC change-management pipeline for Protocol-Governed Systems.**

Every change to a Protocol-Governed System (PGS) begins as a **Change Request (CR)** and is driven
through a governed, gated pipeline — from a plain-language problem statement to an **Authoring
Mandate** — producing a complete, reviewable **dossier** *before* any protocol artifact is written.

> *Intent declared. Design approved. Mandate issued. Artifacts authored.*

---

## Status — v0.6.1

Public debut in **PGS v0.5.0**; `pi` Protocol-Inspection surface wired in at **v0.5.1**.

**v0.6.1 — the all-structured pipeline.** Every dossier stage (1 → 7) is now a **structured
register document** — the worker emits register rows, a deterministic renderer owns the document,
and a **structural oracle** mechanically validates it (well-formed FQDNs, controlled vocabularies,
traceability, and cross-stage consistency such as "every mandate code traces to a Design-Intent
register") before a human ever reviews it. The dossier pipeline **ends at Stage 7** (the Authoring
Mandate); protocol-artifact authoring and the Stage 8 manifest happen *after* Gate 2 (see
[After Stage 7](#after-stage-7--author-compile-test-close)).

Repos version independently; the compatible component set is declared in the `pgs_workspace`
manifest (`manifest.json → pgs_release`).

---

## What It Is

`pgs_change_mgmt` governs the **Change Request → Protocol Artifact** lifecycle in two tiers:

```
  ── DOSSIER TIER (this pipeline — `run_change_mgmt_dossier.sh`) ─────────────────────────
  Stage 1   Change Request          classification + problem / outcome / known facts
  Stage 2   Domain Model            confirm the semantic model against the snapshot
  Stage 3   Analysis Loop           REUSE / EXTEND / AUTHOR_NEW decisions, by evidence
  Stage 4   Business Model          the canonical hub — consolidates Stages 1–3
  Stage 5   Business Intent (WHAT)  scope, invariants, actions, provisional codes
  Stage 6   Governance Intent (WHERE)  ownership, storage, cross-subdomain dependencies
  Stage 6b  Design Intent (HOW)     binding FQDNs assigned to every new artifact
  Stage 7   Authoring Mandate       the build sequence (topological sort of the design)
                          │
                          ▼   ══ Gate 2 — Mandate Approval ══
  ── AUTHORING TIER (after Gate 2) ──────────────────────────────────────────────────────
  author the .md protocol artifacts from the mandate  →  compiler governs admissibility
      →  runtime tests + trace verification  →  Stage 8 manifest populated  →  Stage 9 closure
```

**Two approval gates — not one per stage.** Stages run as a continuous, iterative session; any
prior-stage artifact may be amended as knowledge accumulates, until a gate closes.

- **Gate 1 — Design Approval (after Stage 6b):** the full dossier (Stages 1–6b) is reviewed as a
  body. Approval authorizes the Stage 7 Authoring Mandate.
- **Gate 2 — Mandate Approval (after Stage 7):** the mandate is reviewed. Approval authorizes
  protocol-artifact authoring. **No artifact is authored before Gate 2.** After it, Stages 1–7 lock.

No stage may be skipped. For simple CRs the two gates may collapse into one review session.

---

## How to Start: the CR Seed

A CR begins with a **seed** — the frozen human elicitation, stored as the Stage-1 input artifact:

```
change_mgmt/dossiers/[domain]/[subdomain]/1_input_elicitation_[subdomain]_v0.md
```

The seed stands in for the human↔agent conversation that would normally produce it (that
interactive elicitation is a separate concern; the seed is its frozen output). Stage 1 consumes the
seed and projects it into the governed `1_change_request` artifact. **To run a new CR, author a seed
at that path** describing the change in business language: what problem, what outcome, what is in
and out of scope, what is already known, and which CR type it is.

### CR Types — frame the seed

The first thing Stage 1 classifies is the **CR type**. Knowing it up front shapes the whole seed:

| CR Type | Use when… | Example |
|---|---|---|
| `NEW_SUBDOMAIN` | a brand-new capability area needing its own governance boundary | add a canonical `chain` ledger to the blockchain domain |
| `EXTEND_SUBDOMAIN` | adding capabilities to an existing subdomain | add a new workflow to `mempool` |
| `MODIFY` | changing the behavior or shape of existing artifacts | change a validation rule in an existing CC |
| `DEPRECATE` | retiring an artifact or capability | remove a superseded workflow |

A `NEW_SUBDOMAIN` CR carries the most: vocabulary, lifecycle states, events, invariants, and
authority boundaries — the semantic model Stage 2 will verify and the rest of the pipeline projects.

---

## CR Artifact Projection — and why you can start at any stage

Each stage emits a small, governed **projection** of the stages before it — the `gov_projection`
handoff. A downstream stage consumes **only the upstream fields it declares it needs** (its bounded
context), not the full prior documents. The Business Model (Stage 4) is the hub; the later stages
are *projections* of it, not independent re-derivations.

Two consequences make the pipeline pleasant to operate:

1. **Loose coupling.** Stages are joined only by these declared field handoffs, each **persisted to
   disk** (`dossiers/[domain]/[subdomain]/_handoff/<stage>.json`). A stage never re-reads the whole
   history — only its declared upstream projections.
2. **Start (or resume) at any stage.** Because the handoffs are on disk, you can run a single stage
   on its own — `--stage 6b` — as long as its declared upstream handoffs exist. This lets you:
   regenerate one stage after review, resume mid-pipeline, or even **swap the worker model between
   stages**. Authority lives in the *artifact*, not the actor — a different worker can pick up
   mid-pipeline from the governed handoffs.

This is the same governance dividend the compiler gives at the artifact level, one tier up: bounded,
declared context instead of "the whole world."

---

## Running the Pipeline

From the workspace (sets `PGS_WORKSPACE` and the venv for you):

```bash
cd pgs_workspace/scripts

# Full dossier pipeline (Stages 1→7)
./run_change_mgmt_dossier.sh --worker qwen --model qwen3.5:latest

# A single stage (loads its upstream handoffs from disk)
./run_change_mgmt_dossier.sh --worker qwen --model qwen3.5:latest --stage 6b

# An explicit subset
./run_change_mgmt_dossier.sh --worker qwen --model qwen3.5:latest --stages 6b,7

# A stronger / different worker
./run_change_mgmt_dossier.sh --worker qwen   --model qwen2.5-coder:32b
./run_change_mgmt_dossier.sh --worker claude --model claude-opus-4-8     # needs ANTHROPIC_API_KEY
```

`--worker` and `--model` are **required** — the model is always a conscious choice, never a silent
default. Each stage prints a live R/Y/G grounding stream and a per-stage figure of merit:

- **structured stages** report `governed` (the fields that cross to the next stage) and `audit`
  (this stage's own record) coverage — both must be clean for a 5/5;
- a dirty register (malformed FQDN, bad enum, missing traceability, cross-stage mismatch) drops the
  score and is named in the log. **The oracle catches it here, not three stages later.**

---

## After Stage 7 — author, compile, test, close

The dossier pipeline stops at Stage 7 because Stage 7 is the last thing derivable from the dossier
alone. Everything after is **as-built reality**, produced by the authoring tier:

1. **Gate 2** approves the Authoring Mandate.
2. **Author** the protocol-artifact `.md` files (WF / IN / RB / CC / CT / EV / STRUCTURE) from the
   mandate's build order — codes copied verbatim from the Design Intent, never re-minted.
3. **Compile** them with `pgs_compiler` — the compiler governs admissibility (routing, contract
   closure, schema). This is the authoritative gate; a drafted artifact is not admissible until it
   compiles into the snapshot.
4. **Test** at runtime — execute the new workflows, verify the traces (correct decision, determinism).
5. **Stage 8 — Authoring Manifest:** created as a pre-authoring baseline at Stage 7 close, then
   **populated** with the as-built reality — approved deviations, as-designed-vs-as-built deltas,
   conformance results, and governed-evolution metrics. Run it with `--stage 8`.
6. **Stage 9 — CR Closure:** every PENDING section filled with real execution data, completion
   criteria met, manifest status → `APPROVED`. The CR is not closed until then.

So: **the dossier proves the design; the authoring tier proves the build.** The manifest is the
seam between them — which is why it is a *post-authoring* artifact, not a dossier stage.

---

## Dossier-First Ontology

The primary unit is the **governed change dossier**, not the artifact type. All stage documents for
one CR live flat in the dossier directory, each filename prefixed with its stage number so the
directory lists in stage order:

```
change_mgmt/dossiers/[domain]/[subdomain]/
  1_input_elicitation_[subdomain]_v0.md     ← the seed (Stage-1 input)
  1_change_request_[subdomain]_v0.md
  2_domain_model_[subdomain]_v0.md
  3_analysis_loop_[subdomain]_v0.md
  4_business_model_[subdomain]_v0.md
  5_business_intent_[subdomain]_v0.md
  6_governance_intent_[subdomain]_v0.md
  6b_design_intent_[subdomain]_v0.md
  7_authoring_mandate_[subdomain]_v0.md
  8_authoring_manifest_[subdomain]_v0.md    ← produced after authoring closes
  _handoff/<stage>.json                      ← the bounded gov_projection per stage
```

The stage-template set under `change_mgmt/templates/` uses the same stage-number prefixes
(`0_agent_context` … `8_authoring_manifest`).

---

## Where This Fits

| Repo | Role |
|------|------|
| `pgs_governance` | Constitutional governance, invariant enforcement, FB_CHANGE_MGMT constitution |
| `pgs_compiler` | Compiler pipeline; admissibility construction; the `pi` inspection surface |
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

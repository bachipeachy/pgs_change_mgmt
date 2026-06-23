# Design Intent: blockchain / chain
**Domain:** blockchain  
**Subdomain:** chain  
**Version:** V0  
**Status:** DRAFT  
**Pipeline Stage:** Stage 6b — Design Intent (HOW)  
**Produced by:** v0.5.0 SDLC authoring pipeline  
**Purity:** HOW only — business facts (Business Model) and placement decisions (Governance Intent) not repeated  

---

## Document Contract

**This artifact is a structured register document — not a narrative.** 6b assigns the **binding
FQDNs** the rest of the build depends on. The worker emits register ROWS; a deterministic renderer
owns the document and a structural oracle validates the codes BEFORE a human reviews.

VALID OUTPUT:
- Populated register tables (every required register below)
- Binding FQDNs in `code` / `rb_code` / `binds_wf` / `storage_structure` columns, each
  well-formed (`domain::PREFIX_NAME_V<n>`) and assigned EXACTLY ONCE
- Business-language capability descriptions in the `capability` column

INVALID OUTPUT:
- Narrative summaries / reasoning essays replacing registers
- A binding FQDN referenced anywhere (topology, RB) but absent from `new_artifacts`
- Two spellings of the same capability (a typo is a SECOND immutable artifact, not a synonym)

A required register with no rows MUST render as a single `| NONE IDENTIFIED |` row. The renderer
rejects a malformed FQDN, an empty required register, an undeclared reference, or a near-duplicate
code mechanically.

---

### Binding-FQDN discipline (the oracle enforces these)

- **Well-formed:** every assigned code is `domain::PREFIX_NAME_V<n>` (PREFIX ∈ WF/IN/RB/CC/CT/EV/
  STRUCTURE; explicit `_V0`).
- **One canonical FQDN per capability — assign it ONCE, reuse the EXACT string everywhere**
  (topology, pipelines, RB, summary). A binding FQDN is immutable: a spelling/term variant of the
  same concept (e.g. `GENESIS` vs `GENEISIS`) silently creates a SECOND, permanently-misnamed
  artifact. Spell domain terms exactly.
- **Referenced ⇒ declared:** every NEW code that appears in `execution_topology` or
  `rb_declarations` MUST appear as a row in `new_artifacts`. CTs and EVs are first-class new
  artifacts — never implicit.
- **Genuinely new:** an assigned `new_artifacts` code MUST NOT already exist in the snapshot
  (the oracle collision-checks via grounding). Existing artifacts go in `existing_inventory`.
- **Reconciled:** the NEW counts in `artifact_summary` MUST equal the rows of `new_artifacts`.

### Business-Language Rule

Only the `capability` column of `new_artifacts` is business language (name the need, not the
artifact). Every other column legitimately carries FQDNs / controlled tokens — that is where the
binding codes belong. Existing artifacts are cited by their real FQDN in `fqdn` / source columns.

---

## Stage Inputs — Questions for the Human

*Answer crisply before drafting. The right column states how the agent uses each answer.*

| # | Question for the Human | How the Agent Uses the Answer (Intent) |
|---|------------------------|----------------------------------------|
| 1 | For each open design decision carried from Stages 1–4: which concrete resolution (store shape, schema fields, algorithm, reuse-vs-new)? | Becomes `design_resolution`. Every row traces to a Business Model design decision; new decisions invented here are flagged. |
| 2 | Where an existing artifact partially fits: REUSE as-is, EXTEND it, or REPLACE it? | Fixes `existing_inventory` actions. REPLACE/EXTEND of shared artifacts affects other subdomains. |
| 3 | Do you approve the proposed store names, paths, and key fields? | Locks `structure_stores`. Storage topology is a governance concern — paths declared here, never hardcoded later. |
| 4 | Gate 1: do you approve the full dossier as the design basis? | Gate 1 approval authorizes Stage 7. Without it, no mandate may be drafted. |

**Agent execution rules for this stage (binding FQDNs are assigned here):**
- Every new artifact maps 1:1 to a Governance Intent outcome; every FQDN carries `_V<n>`.
- **Workflow nodes are IN, CC, EXIT/EXIT_SUCCESS only.** Sub-workflow invocation = gateway CC bound to `CS_WORKFLOW_GATEWAY_V0` (precedent: `CC_INVOKE_BLOCK_PROPOSAL_V0`). EV_ artifacts are emitted facts, never triggers.
- A store is written only by CCs of its owning subdomain. Writing CCs for peer stores are declared in the dependency-gap section with peer ownership.
- Before declaring a new CT or EV: check the existing inventory (the transform vocabulary and event set usually already contain the atom) — if reused, it belongs in `existing_inventory`, not `new_artifacts`.
- **Module path assignment (reference):** IN→`[repo].registry.chain.intents`, WF→`.workflows`, CC→`.capability_contracts`, CT→`.capability_transforms`, RB→`.runtime_bindings`, STRUCTURE→`.structures`. A missing assignment is a build failure.

---

## 1. Design Decisions Resolution

*The Design Decisions Register populated throughout Stages 1–4 — resolved here. Each row traces to a Business Model design decision (`source_finding`).*

<!-- register:design_resolution optional -->
| Decision | Business Fact | Resolution | Source Finding |
|----------|---------------|------------|----------------|
| Genesis block creation is a distinct one-time operation separate from regular consensus operations | Establish canonical chain, immutability constraints, and fixed supply of one million BachiCoin at single execution point without replay across restarts | NEW capability AC_GENESIS_BOOTSTRAP_AUTHORITY_V0 with system-level bootstrap workflow orchestration for exactly-one-execution invariant | authoring_decisions: Genesis creates initial monetary state; blockchain::AC_SYSTEM_V0 for system-level bootstrap semantics |
| Block commitment to canonical chain requires new RB/CC pair in chain subdomain | Immutably commit proposed blocks after consensus round conclusion with attestation decision and cryptographic linkage enforcement | NEW capability CC_COMMIT_BLOCK_TO_CANONICAL_CHAIN_V0 paired with runtime binding blockchain::RB_COMMIT_BLOCK_TO_CANONICAL_CHAIN_V0 for BLOCKS store writes using CS_MUTABLE_JSON_V0 substrate | blockchain::EV_BLOCK_COMMITTED_V0 (exists, zero consumers per topology_impact); CR seed §8 Business Invariants #4 require actual commit operation |
| Chain state maintenance after genesis requires dedicated capability for supply conservation | Total supply conserved at one million BachiCoin with no minting or burning permitted post-genesis; closed monetary system principle enforced | NEW capability CC_ENFORCE_SUPPLY_CONSERVATION_POST_GENESIS_V0 extending blockchain::CC_VALIDATE_MINT_POLICY_V0 to reject all post-genesis supply creation except protocol-defined mechanisms | blockchain::CC_FORM_BLOCK_V0 (forms proposed blocks only); CR seed §7 Constraints #1 and Business Invariants #3 require closed monetary system enforcement |

---

## 2. Artifact Inventory — Existing Artifacts

*All existing PPS artifacts touched by this CR. Action ∈ REPLACE | REUSE | EXTEND | REVIEW. `fqdn` is the existing artifact, cited by exact FQDN.*

<!-- register:existing_inventory -->
| FQDN | Action (REPLACE, REUSE, EXTEND, REVIEW) | Reason | Source Finding |
|------|------------------------------------------|--------|----------------|
| blockchain::CC_FORM_BLOCK_V0 | REUSE | Canonical capability contract for forming proposed blocks, writing to BLOCKS store and appending lifecycle events; reused from PPS snapshot inventory as shared infrastructure | upstream handoff: pps_artifacts_requiring_action blockchain::CC_FORM_BLOCK_V0 REUSE |
| blockchain::EV_BLOCK_COMMITTED_V0 | REUSE | Event contract for committed blocks to canonical chain history; reused despite zero consumers in PPS inventory, will be consumed by new commit workflow after consensus round conclusion | upstream handoff: pps_artifacts_requiring_action blockchain::EV_BLOCK_COMMITTED_V0 REUSE |
| blockchain::CC_VALIDATE_MINT_POLICY_V0 | REUSE | Policy validation contract for MINT transactions; reused and extended to enforce supply conservation after genesis by rejecting post-genesis minting except through protocol-defined mechanisms | upstream handoff: pps_artifacts_requiring_action blockchain::CC_VALIDATE_MINT_POLICY_V0 REUSE |

---

## 3. Artifact Family Mapping — New Artifacts

*Each Governance Outcome capability mapped to an artifact family with a binding FQDN assigned.
`capability` is business language; `code` is the binding FQDN; `family` is the execution concern;
`owner_subdomain` is the owning subdomain; `source_finding` traces to the S6 ownership / S4 gap.*

<!-- register:new_artifacts business_language=capability -->
| Capability | Family (AC, IN, WF, RB, CC, CT, EV, STRUCTURE) | Code | Owner Subdomain | Status | Source Finding |
|------------|------------------------------------------------|------|-----------------|--------|----------------|
| bootstrap genesis block and initialize canonical chain state with fixed supply | AC | blockchain::AC_GENESIS_BOOTSTRAP_AUTHORITY_V0 | blockchain/chain | NEW | upstream handoff: authoring_scope capability create genesis block at bootstrap; gap_register GAP-001 resolution NEW |
| commit proposed blocks immutably to canonical chain history after consensus round conclusion with attestation decision and cryptographic linkage | CC | blockchain::CC_COMMIT_BLOCK_TO_CANONICAL_CHAIN_V0 | blockchain/chain | NEW | upstream handoff: authoring_scope capability commit blocks to canonical chain immutably; gap_register GAP-002 resolution NEW |
| track proposed blocks awaiting consensus round conclusion and commitment decision for block lifecycle management | IN | blockchain::IN_BLOCK_PROPOSED_TO_CANONICAL_CHAIN_V0 | blockchain/chain | NEW | upstream handoff: provisional_codes IN_BLOCK_PROPOSED_TO_CANONICAL_CHAIN_V0; gap_register GAP-002 input tracking |
| orchestrate block commitment operations following successful consensus round conclusion with attestation from eligible validators | WF | blockchain::WF_COMMIT_BLOCK_AFTER_CONSENSUS_ROUND_V0 | blockchain/chain | NEW | upstream handoff: authoring_scope capability commit blocks to canonical chain immutably; provisional_codes WF_COMMIT_BLOCK_AFTER_CONSENSUS_ROUND_V0 |
| validate mint policy compliance and reject post-genesis supply creation except through protocol-defined mechanisms | CC | blockchain::CC_ENFORCE_SUPPLY_CONSERVATION_POST_GENESIS_V0 | blockchain/chain | NEW | upstream handoff: authoring_scope capability maintain chain state with supply conservation after genesis; gap_register GAP-003 resolution NEW |
| record consensus rounds that advance to next slot without block commitment due to proposer absence or failed proposal | IN | blockchain::IN_ROUND_SKIPPED_NO_ELIGIBLE_PROPOSER_V0 | blockchain/chain | NEW | upstream handoff: provisional_codes IN_ROUND_SKIPPED_NO_ELIGIBLE_PROPOSER_V0; scope_boundary deferred capability fork resolution |

---

## 4. Runtime Binding (RB) Declarations

*One RB per WF. The RB declares which CS substrates the WF requires and which storage structure resolves store paths. An undeclared CS binding is a runtime failure. `cs_bindings` may list several CS FQDNs (comma-separated).*

<!-- register:rb_declarations -->
| RB Code | Binds WF | CS Bindings | Storage Structure | Source Finding |
|---------|----------|-------------|-------------------|----------------|
| blockchain::RB_COMMIT_BLOCK_TO_CANONICAL_CHAIN_V0 | WF_COMMIT_BLOCK_AFTER_CONSENSUS_ROUND_V0 | capability_side_effects::CS_MUTABLE_JSON_V0, capability_side_effects::CS_APPENDONLY_JSONL_V0 | fb.blockchain::STRUCTURE_BUILD_BLOCKCHAIN_V0 | upstream handoff: storage_governance mutable store for committed block records; cross_subdomain_deps fb.blockchain topology establishing storage topology |

---

## 5. Execution Topology

*The DAG flattened to one row per node, in execution order, per workflow. `node` is an IN/CC binding FQDN or a terminal (EXIT / EXIT_SUCCESS); `routing` states the outcome→target edges in business status names (SUCCESS, NOT_FOUND, ALREADY_EXISTS, VIOLATION, BACKEND_ERROR).*

<!-- register:execution_topology -->
| Workflow | Node | Node Type (IN, CC, EXIT, EXIT_SUCCESS) | Routing | Source Finding |
|----------|------|----------------------------------------|---------|----------------|
|  | \| NONE IDENTIFIED \| | None | None | upstream handoff: blockchain/chain is new subdomain; proposed workflops not yet compiled in PPS inventory |

---

## 6. STRUCTURE Stores

*New entity stores. `storage_type` selects the CS substrate; `proposed_path` is the declared store path (governance concern — never hardcoded later); `used_by` names the writing CC (its owning subdomain only).*

<!-- register:structure_stores optional -->
| Store Name | Storage Type (CS_APPENDONLY_JSONL_V0, CS_MUTABLE_JSON_V0) | Proposed Path | Used By | Source Finding |
|------------|-----------------------------------------------------------|---------------|---------|----------------|
| NONE IDENTIFIED |  |  |  |  |

---

## 7. Artifact Summary

*Artifact count by action type, for Stage 7 input. The oracle reconciles: the NEW counts here MUST equal the rows of `new_artifacts`. `artifacts` lists the codes for that action.*

<!-- register:artifact_summary -->
| Action (REPLACE, EXTEND, NEW) | Subdomain | Count | Artifacts |
|-------------------------------|-----------|-------|-----------|
| NEW | blockchain/chain | 6 | ['blockchain::AC_GENESIS_BOOTSTRAP_AUTHORITY_V0', 'blockchain::CC_COMMIT_BLOCK_TO_CANONICAL_CHAIN_V0', 'blockchain::IN_BLOCK_PROPOSED_TO_CANONICAL_CHAIN_V0', 'blockchain::WF_COMMIT_BLOCK_AFTER_CONSENSUS_ROUND_V0', 'blockchain::CC_ENFORCE_SUPPLY_CONSERVATION_POST_GENESIS_V0', 'blockchain::IN_ROUND_SKIPPED_NO_ELIGIBLE_PROPOSER_V0'] |

---

## Gate 1 — Design Approval

**Gate 1 closes here.** The full dossier (Stages 0–6b) is presented for review as a body. Any
prior-stage artifact amended during the Stage 6–6b session is included. This is a unified review of
the complete design, not a per-stage approval. Gate 1 approval authorizes Stage 7 — Authoring
Mandate. Gate 2 (after Stage 7) locks the full dossier before artifact authoring begins.

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 1 — Change Request & Input Elicitation | change_request_chain_v0.md | COMPLETE |
| Stage 2 — Domain Model Discovery | Actors, Entities, Resources, Events, Relationships | COMPLETE |
| Stage 3 — Analysis Loop | Capability Graph, Dependency Graph, Constraints, Gap Register | COMPLETE — SATURATED |
| Stage 4 — Business Model | business_model_chain_v0.md | COMPLETE |
| Stage 5 — Business Intent | business_intent_chain_v0.md | COMPLETE |
| Stage 6 — Governance Intent | governance_intent_chain_v0.md | COMPLETE — APPROVED |
| Stage 6b — Design Intent | This document | PENDING GATE 1 APPROVAL |
| Stage 7 — Authoring Mandate | Pending | — |
| Stage 8 — Authoring Manifest | Pending | — |

---

## gov_projection — Governed Handoff to Stage 7

*The bounded inputs and emit keys mirror the engine's gov_projection schema exactly
(`contracts/gov_projection.py`). 6b is the binding stage — it consumes the full design context
(S2 attribute/step data, S4 gaps/decisions, S5 intent + provisional codes, S6 placement) and emits
the five registers S7 builds from. Emit keys match the register ids above exactly.*

| Direction | Fields |
|-----------|--------|
| **Consumes** ← Stage 2 | entity_attributes · process_steps |
| **Consumes** ← Stage 4 | gap_register · design_decisions · authoring_scope |
| **Consumes** ← Stage 5 | scope_boundary · invariants · actions · provisional_codes |
| **Consumes** ← Stage 6 | ownership · storage_governance · cross_subdomain_deps · pps_artifacts_requiring_action |
| **Emits** → Stage 7 | new_artifacts · existing_inventory · rb_declarations · execution_topology · artifact_summary |

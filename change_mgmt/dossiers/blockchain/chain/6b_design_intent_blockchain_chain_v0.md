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
| Commit emits the existing committed-block event | EV_BLOCK_COMMITTED_V0 already exists | REUSE the event; author only the commit operation | S4 design_decision #1 |
| Genesis runs once before the loop | genesis executes exactly once (S1 invariant) | bootstrap workflow is a one-time entry point | S4 design_decision #3 |

---

## 2. Artifact Inventory — Existing Artifacts

*All existing PPS artifacts touched by this CR. Action ∈ REPLACE | REUSE | EXTEND | REVIEW. `fqdn` is the existing artifact, cited by exact FQDN.*

<!-- register:existing_inventory -->
| FQDN | Action (REPLACE, REUSE, EXTEND, REVIEW) | Reason | Source Finding |
|------|------------------------------------------|--------|----------------|
| blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0 | EXTEND | add commit semantics to the append-only block store | S3 EXTEND |
| blockchain::EV_BLOCK_COMMITTED_V0 | REUSE | emitted by the new commit operation | S3 REUSE event |
| blockchain::RB_RUN_CONSENSUS_LOOP_V0 | REUSE | produces the proposed blocks to commit | S3 REUSE consensus |
| blockchain::CC_INVOKE_BLOCK_PROPOSAL_V0 | REUSE | produces the proposed block | S3 REUSE proposal |
| blockchain::RB_MINT_V0 | REUSE | mints the genesis supply | S3 REUSE mint |
| blockchain::RB_CREATE_WALLET_V0 | REUSE | creates the MINT wallet | S3 REUSE wallet |
| blockchain::RB_REGISTER_ACTOR_UNVERIFIED_V0 | REUSE | registers the Genesis Actor | S3 REUSE actor |

---

## 3. Artifact Family Mapping — New Artifacts

*Each Governance Outcome capability mapped to an artifact family with a binding FQDN assigned.
`capability` is business language; `code` is the binding FQDN; `family` is the execution concern;
`owner_subdomain` is the owning subdomain; `source_finding` traces to the S6 ownership / S4 gap.*

<!-- register:new_artifacts business_language=capability -->
| Capability | Family (AC, IN, WF, RB, CC, CT, EV, STRUCTURE) | Code | Owner Subdomain | Status | Source Finding |
|------------|------------------------------------------------|------|-----------------|--------|----------------|
| admit a commit request | IN | blockchain::IN_COMMIT_BLOCK_V0 | chain | NEW | S4 authoring_scope |
| commit a proposed block to the canonical chain | WF | blockchain::WF_COMMIT_BLOCK_V0 | chain | NEW | S4 authoring_scope |
| bind the commit workflow | RB | blockchain::RB_COMMIT_BLOCK_V0 | chain | NEW | S4 authoring_scope |
| append the validated block to the canonical chain | CC | blockchain::CC_COMMIT_BLOCK_CANONICAL_V0 | chain | NEW | S4 authoring_scope |
| validate the block links to the current chain head | CC | blockchain::CC_VALIDATE_PREDECESSOR_LINK_V0 | chain | NEW | S4 authoring_scope |
| compute the block content hash (signature) | CT | blockchain::CT_PURE_HASH_BLOCK_V0 | chain | NEW | S4 authoring_scope |
| compare two values for equality (generic primitive) | CT | capability_transforms::CT_PURE_COMPARE_EQUAL_V0 | capability_transforms | NEW | S6b composition gap — CC_VALIDATE_PREDECESSOR_LINK; shared reusable CT, not a blockchain rule |
| admit a genesis bootstrap request | IN | blockchain::IN_BOOTSTRAP_GENESIS_CHAIN_V0 | chain | NEW | S4 authoring_scope |
| create the genesis block and mint the initial supply | WF | blockchain::WF_BOOTSTRAP_GENESIS_CHAIN_V0 | chain | NEW | S4 authoring_scope |
| bind the genesis bootstrap workflow | RB | blockchain::RB_BOOTSTRAP_GENESIS_CHAIN_V0 | chain | NEW | S4 authoring_scope |
| create the chain's first block | CC | blockchain::CC_CREATE_GENESIS_BLOCK_V0 | chain | NEW | S4 authoring_scope |
| emit that the genesis block was created | EV | blockchain::EV_GENESIS_CREATED_V0 | chain | NEW | S4 authoring_scope |

---

## 4. Runtime Binding (RB) Declarations

*One RB per WF. The RB declares which CS substrates the WF requires and which storage structure resolves store paths. An undeclared CS binding is a runtime failure. `cs_bindings` may list several CS FQDNs (comma-separated).*

<!-- register:rb_declarations -->
| RB Code | Binds WF | CS Bindings | Storage Structure | Source Finding |
|---------|----------|-------------|-------------------|----------------|
| blockchain::RB_COMMIT_BLOCK_V0 | blockchain::WF_COMMIT_BLOCK_V0 | capability_side_effects::CS_APPENDONLY_JSONL_V0, capability_side_effects::CS_MUTABLE_JSON_V0 | blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0 | S6 storage_governance; CS_MUTABLE_JSON_V0 added — CC_COMMIT writes chain_head (Build Sheet GAP_DOSSIER) |
| blockchain::RB_BOOTSTRAP_GENESIS_CHAIN_V0 | blockchain::WF_BOOTSTRAP_GENESIS_CHAIN_V0 | capability_side_effects::CS_APPENDONLY_JSONL_V0, capability_side_effects::CS_MUTABLE_JSON_V0 | blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0 | S6 storage_governance; CS_MUTABLE_JSON_V0 added — genesis writes chain_head (Build Sheet GAP_DOSSIER) |

---

## 5. Execution Topology

*The DAG flattened to one row per node, in execution order, per workflow. `node` is an IN/CC binding FQDN or a terminal (EXIT / EXIT_SUCCESS); `routing` states the outcome→target edges in business status names (SUCCESS, NOT_FOUND, ALREADY_EXISTS, VIOLATION, BACKEND_ERROR).*

<!-- register:execution_topology -->
| Workflow | Node | Node Type (IN, CC, EXIT, EXIT_SUCCESS) | Routing | Source Finding |
|----------|------|----------------------------------------|---------|----------------|
| blockchain::WF_COMMIT_BLOCK_V0 | blockchain::IN_COMMIT_BLOCK_V0 | IN | ACK -> CC_VALIDATE_PREDECESSOR_LINK_V0, NACK -> EXIT | S6b |
| blockchain::WF_COMMIT_BLOCK_V0 | blockchain::CC_VALIDATE_PREDECESSOR_LINK_V0 | CC | SUCCESS -> CC_COMMIT_BLOCK_CANONICAL_V0, VIOLATION -> EXIT | S6b |
| blockchain::WF_COMMIT_BLOCK_V0 | blockchain::CC_COMMIT_BLOCK_CANONICAL_V0 | CC | SUCCESS -> EXIT_SUCCESS, ALREADY_EXISTS -> EXIT | S6b |
| blockchain::WF_COMMIT_BLOCK_V0 | EXIT_SUCCESS | EXIT_SUCCESS | - | S6b |
| blockchain::WF_BOOTSTRAP_GENESIS_CHAIN_V0 | blockchain::IN_BOOTSTRAP_GENESIS_CHAIN_V0 | IN | ACK -> CC_CREATE_GENESIS_BLOCK_V0, NACK -> EXIT | S6b |
| blockchain::WF_BOOTSTRAP_GENESIS_CHAIN_V0 | blockchain::CC_CREATE_GENESIS_BLOCK_V0 | CC | SUCCESS -> EXIT_SUCCESS, ALREADY_EXISTS -> EXIT | S6b |
| blockchain::WF_BOOTSTRAP_GENESIS_CHAIN_V0 | EXIT_SUCCESS | EXIT_SUCCESS | - | S6b |

---

## 6. Capability Composition

*The inside of each new CC: the ordered CT/CS steps it is composed of and how data flows between
them. Declarative, not procedural. `capability` is a CT/CS binding FQDN (verbatim from
`new_artifacts` or grounded existing); `consumes`/`produces` name logical data fields. The outcomes
the composition can yield must cover the CC's routing surface in §5.*

<!-- register:cc_composition optional -->
| CC Code | Step | Capability | Kind (CT, CS) | Operation | Consumes | Produces |
|---------|------|------------|---------------|-----------|----------|----------|
| blockchain::CC_COMMIT_BLOCK_CANONICAL_V0 | 1 | blockchain::CT_PURE_HASH_BLOCK_V0 | CT | COMPUTE | proposed_block | content_hash |
| blockchain::CC_COMMIT_BLOCK_CANONICAL_V0 | 2 | capability_side_effects::CS_APPENDONLY_JSONL_V0 | CS | APPEND | proposed_block, content_hash | block_record |
| blockchain::CC_COMMIT_BLOCK_CANONICAL_V0 | 3 | capability_side_effects::CS_MUTABLE_JSON_V0 | CS | SET | content_hash | chain_head |
| blockchain::CC_CREATE_GENESIS_BLOCK_V0 | 1 | blockchain::CT_PURE_HASH_BLOCK_V0 | CT | COMPUTE | genesis_block_content | genesis_block_hash |
| blockchain::CC_CREATE_GENESIS_BLOCK_V0 | 2 | capability_side_effects::CS_APPENDONLY_JSONL_V0 | CS | APPEND | genesis_block_content, genesis_block_hash | genesis_block_record |
| blockchain::CC_CREATE_GENESIS_BLOCK_V0 | 3 | capability_side_effects::CS_MUTABLE_JSON_V0 | CS | SET | genesis_block_hash | chain_head |
| blockchain::CC_VALIDATE_PREDECESSOR_LINK_V0 | 1 | capability_side_effects::CS_MUTABLE_JSON_V0 | CS | GET | — | current_head |
| blockchain::CC_VALIDATE_PREDECESSOR_LINK_V0 | 2 | capability_transforms::CT_PURE_COMPARE_EQUAL_V0 | CT | COMPUTE | proposed_block.predecessor_hash, current_head | is_match |

*CC_VALIDATE routing surface (from §5): `is_match=true ⇒ SUCCESS`, `is_match=false ⇒ VIOLATION`. The
equality rule lives in the CC (which two values); `CT_PURE_COMPARE_EQUAL_V0` is a generic primitive.*

**Gaps — disposition (Gate decision 2026-06-25):**

- ✅ RESOLVED — **CC_VALIDATE_PREDECESSOR_LINK_V0** comparison: declared the generic shared primitive
  `capability_transforms::CT_PURE_COMPARE_EQUAL_V0` (new_artifacts) and composed it as step 2. The
  blockchain rule (predecessor==head) stays in the CC; the CT stays reusable. (Was `GAP_DOSSIER`.)
- ⏸ DEFERRED → future CR — **genesis mint chain** (`GAP_ARCHITECTURAL_DRIFT`, not merely a decision:
  S5 governs minting 1,000,000 to the Genesis Actor as in-scope, but S6b failed to preserve it — the
  two stages describe different systems). Per Gate decision this CR delivers **commit + genesis
  block-record** only; wiring the reused mint/wallet/actor workflows (gateway CCs bound to
  `CS_WORKFLOW_GATEWAY_V0`) is an explicit, recorded scope deferral to a follow-up CR. Genesis
  composition therefore stops at the block record (steps 1–3, no mint).

---

## 7. STRUCTURE Stores

*New entity stores. `storage_type` selects the CS substrate; `proposed_path` is the declared store path (governance concern — never hardcoded later); `used_by` names the writing CC (its owning subdomain only).*

<!-- register:structure_stores optional -->
| Store Name | Storage Type (CS_APPENDONLY_JSONL_V0, CS_MUTABLE_JSON_V0) | Proposed Path | Used By | Source Finding |
|------------|-----------------------------------------------------------|---------------|---------|----------------|
| canonical_blocks | CS_APPENDONLY_JSONL_V0 | blockchain/chain/blocks.jsonl | blockchain::CC_COMMIT_BLOCK_CANONICAL_V0, blockchain::CC_CREATE_GENESIS_BLOCK_V0 | S6 storage; genesis writer added (Build Sheet GAP_DOSSIER) |
| chain_head | CS_MUTABLE_JSON_V0 | blockchain/chain/head.json | blockchain::CC_COMMIT_BLOCK_CANONICAL_V0, blockchain::CC_CREATE_GENESIS_BLOCK_V0 | S6 storage; genesis writer added (Build Sheet GAP_DOSSIER) |

---

## 8. Artifact Summary

*Artifact count by action type, for Stage 7 input. The oracle reconciles: the NEW counts here MUST equal the rows of `new_artifacts`. `artifacts` lists the codes for that action.*

<!-- register:artifact_summary -->
| Action (REPLACE, EXTEND, NEW) | Subdomain | Count | Artifacts |
|-------------------------------|-----------|-------|-----------|
| NEW | chain | 11 | IN/WF/RB/CC/CC/CT (commit) + IN/WF/RB/CC/EV (genesis) |
| NEW | capability_transforms | 1 | CT_PURE_COMPARE_EQUAL_V0 (shared comparison primitive) |
| EXTEND | chain | 1 | STRUCTURE_BLOCKCHAIN_STORAGE_V0 |

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

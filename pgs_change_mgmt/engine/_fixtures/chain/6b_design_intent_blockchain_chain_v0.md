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

### Capability Composition discipline (the oracle enforces these)

`cc_composition` declares the second half of Design Intent: WHAT each new CC is composed of. Workflow
topology (§5) says how CCs route to one another; composition says what is *inside* each CC. It is
**declarative, not procedural** — you declare the governed capabilities the CC is built from and how
data flows between them; you never write code, JSON, JSONPath, or an implementation.

- **CT/CS only.** Each composition step is a Capability Transform (`CT`, pure compute, zero side
  effects) or a Capability Side Effect (`CS`, the only place external state changes) — never a CC, WF,
  or IN. A CC composes *capabilities*, not other CCs.
- **Codes verbatim.** Every `Capability` cell is a CT/CS binding FQDN copied verbatim from
  `new_artifacts` (NEW) or a grounded `existing_inventory` artifact (REUSE) — same immutability rule
  as every binding FQDN. A composition code absent from both registers is a defect.
- **Data flow is logical, not wired.** `Consumes` / `Produces` name business/data fields (e.g.
  `proposed_block`, `content_hash`), connecting a CC's inputs to its steps and step-to-step. Concrete
  JSONPath wiring is construction (S8), not design.
- **Outcome coverage.** The outcomes the composition can yield MUST cover the CC's routing surface in
  `execution_topology` (§5): if topology routes the CC on `SUCCESS` and `ALREADY_EXISTS`, the
  composition must be able to produce both. The oracle cross-checks composition ⊇ topology surface.
- **CT purity.** A `CT` step may not appear where a side effect is required, and may never be a CS.

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
- **Compose every new CC.** Each `family = CC` row in `new_artifacts` gets a `cc_composition` (§6): the ordered CT/CS steps it is built from + their data flow. Leaving a CC's composition unstated leaves construction a design decision — exactly the black box this stage exists to close.
- **Module path assignment (reference):** IN→`[repo].registry.chain.intents`, WF→`.workflows`, CC→`.capability_contracts`, CT→`.capability_transforms`, RB→`.runtime_bindings`, STRUCTURE→`.structures`. A missing assignment is a build failure.

---

## 1. Design Decisions Resolution

*The Design Decisions Register populated throughout Stages 1–4 — resolved here. Each row traces to a Business Model design decision (`source_finding`).*

<!-- register:design_resolution optional -->
| Decision | Business Fact | Resolution | Source Finding |
|----------|---------------|------------|----------------|
| How the chain head is tracked for predecessor linkage | Every committed block links to exactly one predecessor (except genesis). | A mutable head-pointer store holds the current head's content signature; predecessor validation READs it and commit WRITEs it, while an append-only store holds the immutable block log. | S5 identity_semantics; S1 business_invariants #5 |
| How genesis establishes the initial supply | The genesis block contains the first mint transaction crediting the Genesis Actor with 1,000,000 BachiCoin. | The existing mint workflow is mempool-based (grounded: writes the mempool) and genesis runs before the mempool/consensus exist; genesis therefore constructs the initial mint transaction directly inside the genesis block content supplied in the bootstrap request. The mempool mint workflow is not reused for genesis (superseding the tentative S3 reuse). | S3 authoring_decisions REUSE mint; grounded blockchain::WF_MINT_V0 internals |
| How balance reconciliation respects the cross-subdomain-write boundary | Balances are derived from committed transactions and reconciled on-chain post-commit. | Reconciliation reads the committed history, derives balances with a pure transform, and announces them via the balance-reconciled event; the wallet subdomain applies balances to its own store. The chain never writes the wallet store. | S6 boundary_rules Chain writes only its own store; S1 known_facts #11 |

---

## 2. Artifact Inventory — Existing Artifacts

*All existing PPS artifacts touched by this CR. Action ∈ REPLACE | REUSE | EXTEND | REVIEW. `fqdn` is the existing artifact, cited by exact FQDN.*

<!-- register:existing_inventory -->
| FQDN | Action (REPLACE, REUSE, EXTEND, REVIEW) | Reason | Source Finding |
|------|------------------------------------------|--------|----------------|
| blockchain::ENTITY_BLOCK_V0 | REUSE | The committed block record schema. | S3 authoring_decisions REUSE |
| blockchain::EV_BLOCK_COMMITTED_V0 | REUSE | Emitted by the commit capability. | S3 authoring_decisions REUSE |
| blockchain::EV_BALANCE_RECONCILED_V0 | REUSE | Emitted by the reconciliation capability. | S3 authoring_decisions REUSE |
| blockchain::WF_PROPOSE_BLOCK_V0 | REUSE | Upstream producer of the proposed block the chain commits. | S3 dependency_discoveries EXISTING |
| capability_transforms::CT_PURE_KECCAK256_HASH_V0 | REUSE | The generic hash primitive reused inside the block-content hash transform. | S3 analysis_findings Q2 |
| capability_side_effects::CS_MUTABLE_JSON_V0 | REUSE | The mutable substrate for the head-pointer store (READ/WRITE). | S4 gap_register GAP-2 |
| capability_side_effects::CS_APPENDONLY_JSONL_V0 | REUSE | The append-only substrate for the committed block log (APPEND/GET_ALL). | S4 gap_register GAP-2 |
| blockchain::CC_VALIDATE_MINT_POLICY_V0 | REVIEW | The genesis mint conforms to the existing mint policy; genesis constructs the mint directly in the block rather than via the mempool mint workflow. | design_resolution genesis mint |
| blockchain::WF_MINT_V0 | REVIEW | Mempool-based mint workflow; not reused for pre-consensus genesis (see design_resolution). | design_resolution genesis mint |

---

## 3. Artifact Family Mapping — New Artifacts

*Each Governance Outcome capability mapped to an artifact family with a binding FQDN assigned.
`capability` is business language; `code` is the binding FQDN; `family` is the execution concern;
`owner_subdomain` is the owning subdomain; `source_finding` traces to the S6 ownership / S4 gap.*

<!-- register:new_artifacts business_language=capability -->
| Capability | Family (AC, IN, WF, RB, CC, CT, EV, STRUCTURE) | Code | Owner Subdomain | Status | Source Finding |
|------------|------------------------------------------------|------|-----------------|--------|----------------|
| Admit a request to commit a proposed block | IN | blockchain::IN_COMMIT_BLOCK_V0 | chain | NEW | S5 provisional_codes; S6 governance_outcome |
| Commit a proposed block to the canonical chain | WF | blockchain::WF_COMMIT_BLOCK_V0 | chain | NEW | S5 actions Commit |
| Validate a block's predecessor link before commit | CC | blockchain::CC_VALIDATE_PREDECESSOR_LINK_V0 | chain | NEW | S4 gap_register GAP-3 |
| Record a validated block as canonical on the chain | CC | blockchain::CC_COMMIT_BLOCK_CANONICAL_V0 | chain | NEW | S4 gap_register GAP-1 |
| Reconcile wallet balances after commit and announce them | CC | blockchain::CC_RECONCILE_BALANCES_V0 | chain | NEW | S4 gap_register GAP-6 |
| Admit a request to bootstrap the genesis chain | IN | blockchain::IN_BOOTSTRAP_GENESIS_CHAIN_V0 | chain | NEW | S5 provisional_codes |
| Bootstrap the genesis chain and initialise the supply | WF | blockchain::WF_BOOTSTRAP_GENESIS_CHAIN_V0 | chain | NEW | S5 actions Bootstrap |
| Create the genesis block and record it as the first committed block | CC | blockchain::CC_CREATE_GENESIS_BLOCK_V0 | chain | NEW | S4 gap_register GAP-5 |
| Compute a block's content signature | CT | blockchain::CT_PURE_HASH_BLOCK_V0 | chain | NEW | S4 gap_register GAP-4 |
| Extract a block's predecessor hash | CT | blockchain::CT_PURE_EXTRACT_PREDECESSOR_HASH_V0 | chain | NEW | S4 gap_register GAP-3 |
| Derive wallet balances from committed transactions | CT | blockchain::CT_PURE_DERIVE_BALANCES_V0 | chain | NEW | S4 gap_register GAP-6 |
| Compare two values for equality | CT | capability_transforms::CT_PURE_COMPARE_EQUAL_V0 | capability_transforms | NEW | S4 gap_register GAP-3 (shared primitive) |
| Announce that the genesis chain was created | EV | blockchain::EV_GENESIS_CREATED_V0 | chain | NEW | S1 business_events Genesis Created |
| Declare the chain storage (block log and head pointer) | STRUCTURE | blockchain::STRUCTURE_CHAIN_STORAGE_V0 | chain | NEW | S4 gap_register GAP-2; S6 storage_governance |
| Bind the commit workflow to its stores | RB | blockchain::RB_COMMIT_BLOCK_V0 | chain | NEW | S6 governance_outcome |
| Bind the genesis workflow to its stores | RB | blockchain::RB_BOOTSTRAP_GENESIS_CHAIN_V0 | chain | NEW | S6 governance_outcome |

---

## 4. Runtime Binding (RB) Declarations

*One RB per WF. The RB declares which CS substrates the WF requires and which storage structure resolves store paths. An undeclared CS binding is a runtime failure. `cs_bindings` may list several CS FQDNs (comma-separated).*

<!-- register:rb_declarations -->
| RB Code | Binds WF | CS Bindings | Storage Structure | Source Finding |
|---------|----------|-------------|-------------------|----------------|
| blockchain::RB_COMMIT_BLOCK_V0 | blockchain::WF_COMMIT_BLOCK_V0 | capability_side_effects::CS_APPENDONLY_JSONL_V0, capability_side_effects::CS_MUTABLE_JSON_V0 | blockchain::STRUCTURE_CHAIN_STORAGE_V0 | S6 governance_outcome |
| blockchain::RB_BOOTSTRAP_GENESIS_CHAIN_V0 | blockchain::WF_BOOTSTRAP_GENESIS_CHAIN_V0 | capability_side_effects::CS_APPENDONLY_JSONL_V0, capability_side_effects::CS_MUTABLE_JSON_V0 | blockchain::STRUCTURE_CHAIN_STORAGE_V0 | S6 governance_outcome |

---

## 5. Execution Topology

*The DAG flattened to one row per node, in execution order, per workflow. `node` is an IN/CC binding FQDN or a terminal (EXIT / EXIT_SUCCESS); `routing` states the outcome→target edges in business status names (SUCCESS, NOT_FOUND, ALREADY_EXISTS, VIOLATION, BACKEND_ERROR).*

<!-- register:execution_topology -->
| Workflow | Node | Node Type (IN, CC, EXIT, EXIT_SUCCESS) | Routing | Source Finding |
|----------|------|----------------------------------------|---------|----------------|
| blockchain::WF_COMMIT_BLOCK_V0 | blockchain::IN_COMMIT_BLOCK_V0 | IN | SUCCESS -> blockchain::CC_VALIDATE_PREDECESSOR_LINK_V0 | S5 actions Commit |
| blockchain::WF_COMMIT_BLOCK_V0 | blockchain::CC_VALIDATE_PREDECESSOR_LINK_V0 | CC | SUCCESS -> blockchain::CC_COMMIT_BLOCK_CANONICAL_V0, VIOLATION -> EXIT | S4 gap_register GAP-3 |
| blockchain::WF_COMMIT_BLOCK_V0 | blockchain::CC_COMMIT_BLOCK_CANONICAL_V0 | CC | SUCCESS -> blockchain::CC_RECONCILE_BALANCES_V0 | S4 gap_register GAP-1 |
| blockchain::WF_COMMIT_BLOCK_V0 | blockchain::CC_RECONCILE_BALANCES_V0 | CC | SUCCESS -> EXIT_SUCCESS | S4 gap_register GAP-6 |
| blockchain::WF_COMMIT_BLOCK_V0 | EXIT_SUCCESS | EXIT_SUCCESS |  | S5 actions Commit |
| blockchain::WF_COMMIT_BLOCK_V0 | EXIT | EXIT |  | S1 business_invariants #5 (predecessor mismatch rejected) |
| blockchain::WF_BOOTSTRAP_GENESIS_CHAIN_V0 | blockchain::IN_BOOTSTRAP_GENESIS_CHAIN_V0 | IN | SUCCESS -> blockchain::CC_CREATE_GENESIS_BLOCK_V0 | S5 actions Bootstrap |
| blockchain::WF_BOOTSTRAP_GENESIS_CHAIN_V0 | blockchain::CC_CREATE_GENESIS_BLOCK_V0 | CC | SUCCESS -> EXIT_SUCCESS | S4 gap_register GAP-5 |
| blockchain::WF_BOOTSTRAP_GENESIS_CHAIN_V0 | EXIT_SUCCESS | EXIT_SUCCESS |  | S5 actions Bootstrap |

---

## 6. Capability Composition

*The inside of each new CC: the ordered CT/CS steps it is composed of and how data flows between
them. Declarative, not procedural — governed capabilities + data flow, never code or JSONPath. One
row per (CC, step), in execution order. `capability` is a CT/CS binding FQDN (verbatim from
`new_artifacts` or `existing_inventory`); `consumes`/`produces` name logical data fields. The
outcomes the composition can yield must cover the CC's routing surface in `execution_topology` (§5).*

<!-- register:cc_composition optional -->
| CC Code | Step | Capability | Kind (CT, CS) | Operation | Consumes | Produces | Interface |
|---------|------|------------|---------------|-----------|----------|---------------------|
| blockchain::CC_VALIDATE_PREDECESSOR_LINK_V0 | 1 | capability_side_effects::CS_MUTABLE_JSON_V0 | CS | READ |  | current_head | in: key="head"; out: value=current_head |
| blockchain::CC_VALIDATE_PREDECESSOR_LINK_V0 | 2 | blockchain::CT_PURE_EXTRACT_PREDECESSOR_HASH_V0 | CT | COMPUTE | proposed_block | predecessor_hash | in: block=proposed_block; out: predecessor_hash=predecessor_hash |
| blockchain::CC_VALIDATE_PREDECESSOR_LINK_V0 | 3 | capability_transforms::CT_PURE_COMPARE_EQUAL_V0 | CT | COMPUTE | predecessor_hash, current_head | is_match | in: left=predecessor_hash, right=current_head; out: is_equal=is_match |
| blockchain::CC_COMMIT_BLOCK_CANONICAL_V0 | 1 | blockchain::CT_PURE_HASH_BLOCK_V0 | CT | COMPUTE | proposed_block | content_hash | in: block=proposed_block; out: content_hash=content_hash |
| blockchain::CC_COMMIT_BLOCK_CANONICAL_V0 | 2 | capability_side_effects::CS_APPENDONLY_JSONL_V0 | CS | APPEND | proposed_block, content_hash | committed_block | in: record=proposed_block; out: record_id=committed_block |
| blockchain::CC_COMMIT_BLOCK_CANONICAL_V0 | 3 | capability_side_effects::CS_MUTABLE_JSON_V0 | CS | WRITE | content_hash |  | in: key="head", value=content_hash |
| blockchain::CC_CREATE_GENESIS_BLOCK_V0 | 1 | blockchain::CT_PURE_HASH_BLOCK_V0 | CT | COMPUTE | genesis_block_content | content_hash | in: block=genesis_block_content; out: content_hash=content_hash |
| blockchain::CC_CREATE_GENESIS_BLOCK_V0 | 2 | capability_side_effects::CS_APPENDONLY_JSONL_V0 | CS | APPEND | genesis_block_content, content_hash | genesis_block | in: record=genesis_block_content; out: record_id=genesis_block |
| blockchain::CC_CREATE_GENESIS_BLOCK_V0 | 3 | capability_side_effects::CS_MUTABLE_JSON_V0 | CS | WRITE | content_hash |  | in: key="head", value=content_hash |
| blockchain::CC_RECONCILE_BALANCES_V0 | 1 | capability_side_effects::CS_APPENDONLY_JSONL_V0 | CS | GET_ALL |  | committed_history | out: entries=committed_history |
| blockchain::CC_RECONCILE_BALANCES_V0 | 2 | blockchain::CT_PURE_DERIVE_BALANCES_V0 | CT | COMPUTE | committed_history | reconciled_balances | in: committed_history=committed_history; out: reconciled_balances=reconciled_balances |
-----------|
--------------|
-----------|
## 7. STRUCTURE Stores

*New entity stores. `storage_type` selects the CS substrate; `proposed_path` is the declared store path (governance concern — never hardcoded later); `used_by` names the writing CC (its owning subdomain only).*

<!-- register:structure_stores optional -->
| Store Name | Storage Type (CS_APPENDONLY_JSONL_V0, CS_MUTABLE_JSON_V0) | Proposed Path | Used By | Source Finding |
|------------|-----------------------------------------------------------|---------------|---------|----------------|
| chain | CS_APPENDONLY_JSONL_V0 | {module_data_root}/blockchain/chain/chain.jsonl | blockchain::CC_COMMIT_BLOCK_CANONICAL_V0, blockchain::CC_CREATE_GENESIS_BLOCK_V0, blockchain::CC_RECONCILE_BALANCES_V0 | S4 gap_register GAP-2 |
| chain_head | CS_MUTABLE_JSON_V0 | {module_data_root}/blockchain/chain/chain_head.json | blockchain::CC_COMMIT_BLOCK_CANONICAL_V0, blockchain::CC_CREATE_GENESIS_BLOCK_V0, blockchain::CC_VALIDATE_PREDECESSOR_LINK_V0 | S5 identity_semantics; S1 business_invariants #5 |

---

## 8. Artifact Summary

*Artifact count by action type, for Stage 7 input. The oracle reconciles: the NEW counts here MUST equal the rows of `new_artifacts`. `artifacts` lists the codes for that action.*

<!-- register:artifact_summary -->
| Action (REPLACE, EXTEND, NEW) | Subdomain | Count | Artifacts |
|-------------------------------|-----------|-------|-----------|
| NEW | chain | 15 | blockchain::IN_COMMIT_BLOCK_V0, blockchain::WF_COMMIT_BLOCK_V0, blockchain::CC_VALIDATE_PREDECESSOR_LINK_V0, blockchain::CC_COMMIT_BLOCK_CANONICAL_V0, blockchain::CC_RECONCILE_BALANCES_V0, blockchain::IN_BOOTSTRAP_GENESIS_CHAIN_V0, blockchain::WF_BOOTSTRAP_GENESIS_CHAIN_V0, blockchain::CC_CREATE_GENESIS_BLOCK_V0, blockchain::CT_PURE_HASH_BLOCK_V0, blockchain::CT_PURE_EXTRACT_PREDECESSOR_HASH_V0, blockchain::CT_PURE_DERIVE_BALANCES_V0, blockchain::EV_GENESIS_CREATED_V0, blockchain::STRUCTURE_CHAIN_STORAGE_V0, blockchain::RB_COMMIT_BLOCK_V0, blockchain::RB_BOOTSTRAP_GENESIS_CHAIN_V0 |
| NEW | capability_transforms | 1 | capability_transforms::CT_PURE_COMPARE_EQUAL_V0 |

---

## 9. Events

*The protocol-design definition of each new event: its payload schema. This is the **protocol
viewpoint** of an event, deliberately kept separate from the **business viewpoint** in S4 (`events`:
why the event exists, its business trigger and meaning). Here the concern is the constructible fact —
the wire payload the EV artifact must carry. One row per payload field. `format` refines a `type`
(e.g. `date-time`, `uuid`); `description` is the field's semantic note (the EV renderer projects it —
it does not invent prose). The emitter is NOT declared here — emission is an execution relationship,
owned by §10 `execution_outputs`, not a property of the event.*

<!-- register:events optional -->
| EV Code | Field | Type | Required | Format | Description |
|---------|-------|------|----------|--------|-------------|
| blockchain::EV_GENESIS_CREATED_V0 | genesis_hash | string | true |  | Genesis block content hash |
| blockchain::EV_GENESIS_CREATED_V0 | height | integer | true |  | Block height (0 for genesis) |
| blockchain::EV_GENESIS_CREATED_V0 | timestamp | string | true | date-time | When genesis was created |

---

## 10. Execution Outputs

*The declared outputs of each execution node — the **execution relationship**: which producer emits
which protocol artifact. The relationship originates at the producer (a CC), exactly as a Capability
consumes a Store; the sink (the event) carries no knowledge of who emits it. This register is
GENERAL: `output_kind ∈ EVENT | STORE | ASSERT | …`, so it scales to future output kinds without
widening `execution_topology` (§5), which stays about ordering and dependencies. `output_code` is a
binding FQDN of the emitted artifact (`new_artifacts` or `existing_inventory`). The EV renderer joins
this register to §9 `events` on `ev_code == output_code` to construct the EV artifact — pure
projection, no inference.*

<!-- register:execution_outputs optional -->
| Producer | Output Kind (EVENT, STORE, ASSERT) | Output Code |
|----------|-----------------------------------|-------------|
| blockchain::CC_CREATE_GENESIS_BLOCK_V0 | EVENT | blockchain::EV_GENESIS_CREATED_V0 |

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
the five registers S7 builds from, plus `cc_composition` which the S8 Build Sheet assembles. Emit
keys match the register ids above exactly.*

| Direction | Fields |
|-----------|--------|
| **Consumes** ← Stage 2 | entity_attributes · process_steps |
| **Consumes** ← Stage 4 | gap_register · design_decisions · authoring_scope |
| **Consumes** ← Stage 5 | scope_boundary · invariants · actions · provisional_codes |
| **Consumes** ← Stage 6 | ownership · storage_governance · cross_subdomain_deps · pps_artifacts_requiring_action |
| **Emits** → Stage 7 | new_artifacts · existing_inventory · rb_declarations · execution_topology · artifact_summary |
| **Emits** → Stage 8 (Build Sheet) | cc_composition · structure_stores · events · execution_outputs |

# Authoring Mandate: blockchain / chain
**Domain:** blockchain  
**Subdomain:** chain  
**Version:** V0  
**Status:** DRAFT  
**Pipeline Stage:** Stage 7 — Authoring Mandate  
**Produced by:** v0.5.0 SDLC authoring pipeline  

---

## Document Contract

**This artifact is a structured register document — not a narrative.** S7 is mechanical: it
re-orders the artifacts Stage 6b already assigned into a build sequence. The worker emits register
ROWS; a deterministic renderer owns the document; a cross-stage oracle checks the codes against the
Stage 6b registers.

VALID OUTPUT:
- Populated register tables (every required register below)
- Every `code` cell a binding FQDN copied VERBATIM from a Stage 6b register

INVALID OUTPUT:
- Narrative summaries replacing registers
- A code not present in the Stage 6b `new_artifacts` / `existing_inventory` registers
- A non-contiguous `step` sequence (a gap means a silently dropped artifact)

---

### Mandate discipline (the oracle enforces these)

- **No design here.** S7 adds nothing and drops nothing — it ORDERS what Stage 6b assigned. No new
  codes, no new actions.
- **Copy every code VERBATIM from the Stage 6b registers** — never re-type, re-spell, or introduce
  a code. A binding FQDN is immutable; re-typing one (even a transposed letter) mints a second,
  permanently-misnamed artifact. Every code in this mandate MUST appear in a Stage 6b register
  (`new_artifacts` for NEW, `existing_inventory` for REPLACE/EXTEND).
- **Reconcile:** the NEW / REPLACE / EXTEND counts in `mandate_artifact_summary` MUST equal Stage
  6b's `artifact_summary`. `step` numbering is contiguous from 1.

---

## Stage Inputs — Questions for the Human

| # | Question for the Human | How the Agent Uses the Answer (Intent) |
|---|------------------------|----------------------------------------|
| 1 | Gate 2: approve this mandate, locking the dossier before authoring begins? | Gate 2 freezes scope. After it, any departure is an Approved Deviation in the Stage 8 manifest — never a silent change. |
| 2 | Any sequencing constraints beyond the dependency graph (e.g., author a risky artifact first)? | Adjusts `wave` ordering without changing the dependency-derived topological order. |

---

## 1. Build Dependency Order

*Topological sort of Stage 6b's `new_artifacts` over the dependencies in `execution_topology` /
`rb_declarations`. ONE row per artifact to AUTHOR — `action` ∈ NEW / REPLACE / EXTEND only. A
REUSE / existing dependency is NOT authored: reference it in `depends_on`, never as its own row.
`step` is the GLOBAL execution order, contiguous from 1 across all waves; `wave` groups parallel
work. `code` is copied verbatim from a Stage 6b register; `depends_on` lists prerequisite codes (or `—`).*

<!-- register:build_order -->
| Wave | Step | Code | Action (REPLACE, EXTEND, NEW) | Subdomain | Depends On |
|------|------|------|-------------------------------|-----------|------------|
| 1 | 1 | blockchain::CT_PURE_HASH_BLOCK_V0 | NEW | chain | capability_transforms::CT_PURE_KECCAK256_HASH_V0 |
| 1 | 2 | blockchain::CT_PURE_EXTRACT_PREDECESSOR_HASH_V0 | NEW | chain | — |
| 1 | 3 | blockchain::CT_PURE_DERIVE_BALANCES_V0 | NEW | chain | — |
| 1 | 4 | capability_transforms::CT_PURE_COMPARE_EQUAL_V0 | NEW | capability_transforms | — |
| 1 | 5 | blockchain::STRUCTURE_CHAIN_STORAGE_V0 | NEW | chain | capability_side_effects::CS_APPENDONLY_JSONL_V0, capability_side_effects::CS_MUTABLE_JSON_V0 |
| 1 | 6 | blockchain::EV_GENESIS_CREATED_V0 | NEW | chain | — |
| 1 | 7 | blockchain::IN_COMMIT_BLOCK_V0 | NEW | chain | — |
| 1 | 8 | blockchain::IN_BOOTSTRAP_GENESIS_CHAIN_V0 | NEW | chain | — |
| 2 | 9 | blockchain::CC_VALIDATE_PREDECESSOR_LINK_V0 | NEW | chain | blockchain::CT_PURE_EXTRACT_PREDECESSOR_HASH_V0, capability_transforms::CT_PURE_COMPARE_EQUAL_V0, blockchain::STRUCTURE_CHAIN_STORAGE_V0 |
| 2 | 10 | blockchain::CC_COMMIT_BLOCK_CANONICAL_V0 | NEW | chain | blockchain::CT_PURE_HASH_BLOCK_V0, blockchain::STRUCTURE_CHAIN_STORAGE_V0 |
| 2 | 11 | blockchain::CC_CREATE_GENESIS_BLOCK_V0 | NEW | chain | blockchain::CT_PURE_HASH_BLOCK_V0, blockchain::STRUCTURE_CHAIN_STORAGE_V0 |
| 2 | 12 | blockchain::CC_RECONCILE_BALANCES_V0 | NEW | chain | blockchain::CT_PURE_DERIVE_BALANCES_V0, blockchain::STRUCTURE_CHAIN_STORAGE_V0 |
| 3 | 13 | blockchain::WF_COMMIT_BLOCK_V0 | NEW | chain | blockchain::IN_COMMIT_BLOCK_V0, blockchain::CC_VALIDATE_PREDECESSOR_LINK_V0, blockchain::CC_COMMIT_BLOCK_CANONICAL_V0, blockchain::CC_RECONCILE_BALANCES_V0 |
| 3 | 14 | blockchain::WF_BOOTSTRAP_GENESIS_CHAIN_V0 | NEW | chain | blockchain::IN_BOOTSTRAP_GENESIS_CHAIN_V0, blockchain::CC_CREATE_GENESIS_BLOCK_V0 |
| 4 | 15 | blockchain::RB_COMMIT_BLOCK_V0 | NEW | chain | blockchain::WF_COMMIT_BLOCK_V0, blockchain::STRUCTURE_CHAIN_STORAGE_V0 |
| 4 | 16 | blockchain::RB_BOOTSTRAP_GENESIS_CHAIN_V0 | NEW | chain | blockchain::WF_BOOTSTRAP_GENESIS_CHAIN_V0, blockchain::STRUCTURE_CHAIN_STORAGE_V0 |

---

## 2. Critical Path

*The longest sequential dependency chain, in order. Each `code` is a build_order step on the
critical path.*

<!-- register:critical_path -->
| Position | Code |
|----------|------|
| 1 | blockchain::CT_PURE_HASH_BLOCK_V0 |
| 2 | blockchain::CC_COMMIT_BLOCK_CANONICAL_V0 |
| 3 | blockchain::WF_COMMIT_BLOCK_V0 |
| 4 | blockchain::RB_COMMIT_BLOCK_V0 |

---

## 3. Artifact Summary

*Authoring action counts, for Stage 8 input. Reconciles against Stage 6b `artifact_summary`.*

<!-- register:mandate_artifact_summary -->
| Action (REPLACE, EXTEND, NEW) | Count | Description |
|-------------------------------|-------|-------------|
| NEW | 16 | 15 new chain artifacts (2 IN, 2 WF, 4 CC, 3 CT, 1 EV, 1 STRUCTURE, 2 RB) + 1 shared capability transform |

---

## 4. Subdomain Field Declarations

*The `subdomain` field for every WF / CC / EV / RB artifact — governs trace routing and data-store path resolution. `code` is copied verbatim from a Stage 6b register.*

<!-- register:field_declarations -->
| Code | Subdomain Field |
|------|-----------------|
| blockchain::WF_COMMIT_BLOCK_V0 | chain |
| blockchain::WF_BOOTSTRAP_GENESIS_CHAIN_V0 | chain |
| blockchain::CC_VALIDATE_PREDECESSOR_LINK_V0 | chain |
| blockchain::CC_COMMIT_BLOCK_CANONICAL_V0 | chain |
| blockchain::CC_CREATE_GENESIS_BLOCK_V0 | chain |
| blockchain::CC_RECONCILE_BALANCES_V0 | chain |
| blockchain::EV_GENESIS_CREATED_V0 | chain |
| blockchain::RB_COMMIT_BLOCK_V0 | chain |
| blockchain::RB_BOOTSTRAP_GENESIS_CHAIN_V0 | chain |

---

## 5. New Capabilities

*New CT/capability declarations — **business intent only**. `Code` is a binding FQDN from a Stage 6b `new_artifacts` row; `Purpose` is business language; `Inputs`/`Outputs` are typed fields written `name:type` (comma-separated, e.g. `block:object`). The Construction Compiler realizes these into candidate CT contracts — it derives ALL protocol realization (purity, governing constitution, machine/implementation binding). You declare only intent. Nothing new → leave empty.*

<!-- register:new_capabilities optional -->
| Code | Purpose | Inputs | Outputs |
|------|---------|--------|---------|
| blockchain::CT_PURE_HASH_BLOCK_V0 | Compute a block's content signature by canonically hashing the block. | block:object | content_hash:string |
| blockchain::CT_PURE_EXTRACT_PREDECESSOR_HASH_V0 | Extract the predecessor hash carried by a proposed block. | block:object | predecessor_hash:string |
| blockchain::CT_PURE_DERIVE_BALANCES_V0 | Derive wallet balances from the committed transaction history. | committed_history:object | reconciled_balances:object |
| capability_transforms::CT_PURE_COMPARE_EQUAL_V0 | Compare two values for equality. | left:string, right:string | is_equal:boolean |

---

## 6. New Intents

*New IN (ingress) declarations — **business intent only**. `Code` is a binding FQDN from `new_artifacts`; `Purpose` is business language; `Workflow` is the WF this intent admits into (a design decision — the FQDN); `Inputs` is the typed payload written `name:type` (comma-separated — only what ARRIVES at the intent boundary). The Construction Compiler realizes these into candidate IN contracts. Nothing new → leave empty.*

<!-- register:new_intents optional -->
| Code | Purpose | Workflow | Inputs |
|------|---------|----------|--------|
| blockchain::IN_COMMIT_BLOCK_V0 | Admit a request to commit a proposed block to the canonical chain. | blockchain::WF_COMMIT_BLOCK_V0 | proposed_block:object |
| blockchain::IN_BOOTSTRAP_GENESIS_CHAIN_V0 | Admit a request to bootstrap the genesis chain and initialise the supply. | blockchain::WF_BOOTSTRAP_GENESIS_CHAIN_V0 | genesis_block_content:object |

---

## 7. Cross-Subdomain Notes

*Artifacts that make cross-subdomain calls (permitted) or would write cross-subdomain (forbidden — must be a peer-owned dependency-gap CC). Audit only.*

<!-- register:cross_subdomain_notes optional -->
| Code | Note |
|------|------|
| blockchain::WF_COMMIT_BLOCK_V0 | Reads the proposed block produced by the consensus subdomain (blockchain::WF_PROPOSE_BLOCK_V0) — a cross-subdomain data read, permitted. |
| blockchain::CC_RECONCILE_BALANCES_V0 | Announces reconciled balances via blockchain::EV_BALANCE_RECONCILED_V0 for the wallet subdomain to apply; the chain never writes the wallet store. |
| capability_transforms::CT_PURE_COMPARE_EQUAL_V0 | A shared primitive authored in the capability_transforms namespace, not the chain subdomain. |

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 6b — Design Intent | design_intent_chain_v0.md | GATE 1 APPROVED |
| Stage 7 — Authoring Mandate | This document | PENDING GATE 2 APPROVAL |
| Artifact Authoring (authoring tier) | per build_order | PENDING |
| Stage 8 — Authoring Manifest | post-authoring | PENDING |

---

## gov_projection — Governed Handoff to Artifact Authoring

*The bounded inputs and emit keys mirror the engine's gov_projection schema exactly
(`contracts/gov_projection.py`). S7 consumes all five Stage 6b registers and emits the four the
authoring step builds from. Emit keys match the register ids above exactly.*

| Direction | Fields |
|-----------|--------|
| **Consumes** ← Stage 6b | new_artifacts · existing_inventory · rb_declarations · execution_topology · artifact_summary |
| **Emits** → artifact authoring | build_order · critical_path · mandate_artifact_summary · field_declarations |

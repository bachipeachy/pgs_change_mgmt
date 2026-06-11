# Governance Intent: blockchain / chain
**Domain:** blockchain  
**Subdomain:** chain  
**Version:** V0  
**Status:** COMPLETE  
**Pipeline Stage:** Stage 6 — Governance Intent (WHERE)  
**Produced by:** v0.5.0 SDLC authoring pipeline  
**Purity:** WHERE only — artifact family mapping, provisional artifact codes, and store declarations excluded  

---

## 1. Domain Placement

| Field | Value |
| --- | --- |
| Domain | `blockchain` |
| Primary subdomain | `chain` |
| Secondary subdomain | `None` |
| FQDN namespace | `blockchain` |
| `chain` status | NEW — declared by this CR |

**Rationale:** The `chain` subdomain is declared as new because it represents a distinct governance concern focused on the canonical, immutable sequence of committed block references and the overall state of the blockchain. This is separate from the `block` subdomain's focus on individual block content and proposal. Establishing `blockchain::chain` as a peer subdomain within the `blockchain` domain ensures clear ownership boundaries and governance policies for these new, fundamental capabilities.

---

## 2. Authority and Governance

| Concern | Governing Constitution |
| --- | --- |
| Actor authority | `fb.constitution::CONSTITUTION_GOVERNANCE_V0` |
| Execution topology (WF, IN, CC) | `fb.topology::CONSTITUTION_WORKFLOW_V0`, `fb.topology::CONSTITUTION_INTENT_V0`, `fb.topology::CONSTITUTION_CAPABILITY_CONTRACT_V0` |
| Storage topology | `fb.constitution::CONSTITUTION_STRUCTURE_V0` |
| Domain invariants | Closed monetary system; canonical chain progression (declared as boundary rules below) |

**Authority Class:** Operations within the `chain` subdomain execute under the existing SYSTEM authority class, for both chain initialization and block commitment, reflecting their foundational and internal nature. No new actor types are required by this CR. `genesis.actor` is an actor instance registered through the existing identity capability, not a new authority class.

---

## 3. Subdomain Boundary

### Owned by `blockchain::chain` (this CR)

| Capability | Ownership Decision |
| --- | --- |
| Chain reference store (append-only) | OWNED |
| Chain state store (mutable, single record) | OWNED |
| Chain event journal (append-only) | OWNED |
| Chain initialization (genesis bootstrap) workflow + admission + binding | OWNED |
| Block commitment workflow + admission + binding | OWNED |
| Single-genesis check | OWNED |
| Gateway invocations of wallet creation, genesis mint, validator registration | OWNED |
| Chain state read/update; append block/genesis reference | OWNED |
| Commit eligibility verification + sequential round transform | OWNED |

### Owned by peer subdomains — dependency gaps declared by this CR

| Capability | Owner | Rationale |
| --- | --- | --- |
| Genesis block formation (writes `BLOCKS[height=0]`) | `blockchain::block` | `BLOCKS` writes must be block-owned; cross-subdomain writes are forbidden. |
| Mark block canonical (updates `status`/`is_canonical` in `BLOCKS`) | `blockchain::block` | Same store-ownership rule. |
| Block commitment invocation gateway + slot workflow extension | `blockchain::orchestration` | Slot coordination is orchestration's concern; commitment is chained into slot processing there. |

*Cross-subdomain dependency directions: chain → block (calls), orchestration → chain (calls). The chain subdomain never writes peer stores; peers never write chain stores.*

### Satisfied by existing subdomains — no ownership transfer

| Capability | Owned By | PPS Status |
| --- | --- | --- |
| Actor registration | `blockchain::identity` | SATISFIED — `blockchain::CC_PERSIST_VERIFIED_ACTOR_V0` reused |
| Wallet creation | `blockchain::wallet` | SATISFIED — `blockchain::WF_CREATE_WALLET_V0` reused via gateway |
| Minting | `blockchain::transaction` | SATISFIED — `blockchain::WF_MINT_V0` reused via gateway |
| Validator registration | `blockchain::consensus_pos` | SATISFIED — `blockchain::WF_REGISTER_VALIDATOR_V0` reused via gateway |
| Block content formation (proposal path) | `blockchain::block` | SATISFIED — `blockchain::CC_FORM_BLOCK_V0` unchanged |
| Block content storage (`BLOCKS` store) | `blockchain::block` | SATISFIED — declared in `STRUCTURE_BLOCKCHAIN_STORAGE_V0` |
| Commitment lifecycle event | `blockchain::block` | SATISFIED — `blockchain::EV_BLOCK_COMMITTED_V0` exists, reserved for this CR; Emitted By updated at authoring |
| Sub-workflow invocation substrate | `capability_side_effects` | SATISFIED — `CS_WORKFLOW_GATEWAY_V0` reused |

### Deferred to future CRs — not owned this CR

| Capability | Reason |
| --- | --- |
| "Attest" block processing step | Future CR — explicitly out of scope for simplicity. |
| "Finalize" block processing step | Future CR — explicitly out of scope for simplicity. |
| Advanced block content validation | Future CR — beyond basic chain integrity. |
| Fork selection / reorganization | Future CR — V0 single canonical chain model. |

---

## 4. Composition — Extension Pattern

| Composition Decision | Detail |
| --- | --- |
| Domain | Extend existing `blockchain` domain |
| Subdomain (primary) | Declare new `chain` namespace |
| Subdomain (secondary) | None |
| Actor types | Reuse existing SYSTEM authority class |
| Execution substrate | Reuse existing capability substrate (gateway, mutable JSON, append-only JSONL) |
| Commitment invocation dependency | Cross-subdomain capability call — `blockchain::orchestration` (slot workflow) invokes `blockchain::chain` (commitment) via workflow gateway |
| Genesis funding dependencies | Cross-subdomain capability calls — chain (genesis WF) → identity (actor), wallet (gateway), transaction (gateway), consensus_pos (gateway) |
| Block content dependencies | Cross-subdomain data read — chain reads `BLOCKS`; all `BLOCKS` writes via block-owned dependency-gap capabilities |
| Storage topology | NEW dedicated chain STRUCTURE artifact — chain stores are exclusively chain-owned (orchestration precedent); `STRUCTURE_BLOCKCHAIN_STORAGE_V0` is NOT extended |

*Cross-subdomain writes are forbidden — chain does not write `BLOCKS` or any peer store; no peer writes chain stores.*

---

## 5. Storage Governance Requirements

**`blockchain::chain` subdomain storage (declared in a dedicated chain STRUCTURE artifact):**
- Chain reference store (append-only) — immutable, ordered record of committed block references.
- Chain state store (mutable) — single, atomically updated record of current head reference and height; the canonical head authority.
- Chain event journal (append-only) — chain lifecycle facts (genesis committed, block committed).

*Store ownership invariant: these stores are exclusively owned by `blockchain::chain`. Cross-subdomain writes to them are a hard governance violation.*

---

## 6. Cross-Subdomain Dependency Declaration

| Dependency | Direction | Existing PPS Artifact | Status |
| --- | --- | --- | --- |
| Commitment invocation from slot processing | `blockchain::orchestration` → `blockchain::chain` | `blockchain::WF_PROCESS_SLOT_V0` (extension point) | GAP — new gateway capability + WF extension; owned by `blockchain::orchestration` |
| Genesis block formation | `blockchain::chain` → `blockchain::block` | None | GAP — new capability; owned by `blockchain::block` |
| Mark block canonical | `blockchain::chain` → `blockchain::block` | None | GAP — new capability; owned by `blockchain::block` |
| Proposed block read | `blockchain::chain` → `blockchain::block` | `STRUCTURE_BLOCKCHAIN_STORAGE_V0` (`BLOCKS`) | SATISFIED — data read permitted |
| Actor registration | `blockchain::chain` → `blockchain::identity` | `blockchain::CC_PERSIST_VERIFIED_ACTOR_V0` | SATISFIED — reuse |
| Wallet creation | `blockchain::chain` → `blockchain::wallet` | `blockchain::WF_CREATE_WALLET_V0` | SATISFIED — reuse via gateway |
| Minting | `blockchain::chain` → `blockchain::transaction` | `blockchain::WF_MINT_V0` | SATISFIED — reuse via gateway |
| Validator registration | `blockchain::chain` → `blockchain::consensus_pos` | `blockchain::WF_REGISTER_VALIDATOR_V0` | SATISFIED — reuse via gateway |
| Commitment lifecycle event | `blockchain::chain` records `blockchain::block`-declared event | `blockchain::EV_BLOCK_COMMITTED_V0` | SATISFIED — reuse; Emitted By updated |

---

## 7. Governance Boundary Rules

1. **Immutability of Chain References** — Once a block reference is added to the chain store, it cannot be altered or removed.
2. **Closed Monetary System** — BachiCoin cannot enter or leave the system from external sources.
3. **Genesis Block Funding** — Genesis establishes the initial supply: 1,000,000 BachiCoin in a "MINT" wallet owned by `genesis.actor`.
4. **Canonical Chain Progression** — A block may be committed only if it exists in `BLOCKS` with status PROPOSED and its `round_id` equals current head height + 1; cryptographic linkage (`previous_block_hash` = current head hash) is constructed at commitment.
5. **Separation of Block Content and Chain Index** — Full block content resides in `BLOCKS` (block-owned); the chain maintains an immutable index of references.
6. **Single Chain State** — Exactly one mutable chain state record, atomically updated; head state is never derived by chain traversal.
7. **Genesis Execution** — Chain initialization may execute exactly once; after initialization, chain governance owns progression, not creation.
8. **Single Canonical Chain Model** — V0 supports a single canonical chain; fork selection, reorganization, attestation, finalization out of scope.
9. **Store Ownership** — A store is written only by capabilities of its owning subdomain. All `BLOCKS` writes are block-owned; all chain-store writes are chain-owned. No exceptions.
10. **Events Are Facts, Not Triggers** — Chain lifecycle events are recorded for observability and audit; no execution is triggered by event consumption. Workflow chaining uses gateway capabilities.

---

## 8. PPS Artifacts Requiring Action

| Artifact | Current Status | Action |
| --- | --- | --- |
| `blockchain::WF_PROCESS_SLOT_V0` | EXISTS — slot processing: read clock → prepare context → invoke proposal → advance clock | EXTEND — insert commitment invocation (orchestration-owned gateway) after successful block proposal, before clock advance |
| `blockchain::EV_BLOCK_COMMITTED_V0` | EXISTS — Emitted By reserved "(consensus finalization CR — next CR)" | UPDATE (metadata) — declare the chain commitment workflow/capability in Emitted By |
| `blockchain::WF_PROPOSE_BLOCK_V0` | EXISTS — produces PROPOSED blocks | NO ACTION — reused unchanged (the event-emission extension proposed in an earlier draft is withdrawn) |
| `blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0` | EXISTS — domain storage topology | NO ACTION — chain stores are declared in a NEW dedicated chain STRUCTURE artifact |

---

## 9. Governance Outcome

**`blockchain::chain` subdomain (capabilities requiring protocol realization; artifact families and codes assigned in Stage 6b):**
- Chain reference store, chain state store, chain event journal (dedicated storage structure)
- Chain initialization workflow, its admission intent, its runtime binding
- Block commitment workflow, its admission intent, its runtime binding
- Single-genesis check
- Gateway invocations: wallet creation, genesis mint, validator registration
- Chain state read; chain state update
- Proposed block read
- Commit eligibility verification; sequential round transform
- Append genesis reference; append block reference

**`blockchain::block` subdomain (dependency gap — owned by block, triggered by this CR):**
- Genesis block formation (writes `BLOCKS[height=0]`)
- Mark block canonical (updates committed block's status/canonical flag)

**`blockchain::orchestration` subdomain (dependency gap — owned by orchestration, triggered by this CR):**
- Block commitment invocation gateway; slot workflow extension

---

## 10. Governance Summary

**Key decisions recorded in this document:**

1. **Placement:** `blockchain::chain` declared as a new peer subdomain, distinct from `blockchain::block` (content vs. canonical ordering).
2. **Authority:** Existing SYSTEM authority class; no new actor types.
3. **Integration pattern:** Commitment is invoked by the orchestration slot workflow via a workflow gateway — events are facts, never triggers. The earlier event-driven design is withdrawn.
4. **Ownership boundaries:** Three dependency gaps declared — genesis block formation and canonical marking owned by `block`; commitment invocation owned by `orchestration`.
5. **Storage:** Three chain-owned stores in a dedicated chain STRUCTURE artifact (orchestration precedent); `STRUCTURE_BLOCKCHAIN_STORAGE_V0` untouched.
6. **Reuse:** `EV_BLOCK_COMMITTED_V0` (reserved for this CR), gateway/storage substrates, hashing and assembly transforms, identity/wallet/transaction/consensus_pos capabilities — all reused, not re-authored.
7. **Boundary rules:** Ten governance invariants declared (Section 7), including store ownership and events-as-facts.
8. **Deferrals:** Attest, Finalize, advanced content validation, fork handling — future CRs.

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 1 — Change Request & Input Elicitation | 1_change_request_blockchain_chain_v0.md | COMPLETE |
| Stage 2 — Domain Model Discovery | 2_domain_model_blockchain_chain_v0.md | COMPLETE |
| Stage 3 — Analysis Loop | 3_analysis_loop_blockchain_chain_v0.md | COMPLETE — SATURATED (2 iterations) |
| Stage 4 — Business Model | 4_business_model_blockchain_chain_v0.md | COMPLETE |
| Stage 4b — Authoring Scope | IN/FUTURE CR boundary | COMPLETE |
| Stage 5 — Business Intent | 5_business_intent_blockchain_chain_v0.md | COMPLETE |
| Stage 6 — Governance Intent | This document | COMPLETE |
| Stage 6b — Design Intent | 6b_design_intent_blockchain_chain_v0.md | PENDING GATE 1 APPROVAL |
| Stage 7 — Authoring Mandate | 7_authoring_mandate_blockchain_chain_v0.md | PENDING GATE 2 APPROVAL |
| Stage 8 — Authoring Manifest | 8_authoring_manifest_blockchain_chain_v0.md | PENDING — baseline created |

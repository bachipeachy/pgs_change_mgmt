# Business Model: blockchain / chain
**Domain:** blockchain  
**Subdomain:** chain  
**Version:** V0  
**Status:** COMPLETE  
**Pipeline Stage:** Stage 4 — Business Model (canonical artifact)  
**Produced by:** v0.5.0 SDLC authoring pipeline  

---

## 1. Discovery Summary

### Actors
| Actor | Role | Authority Class |
|-------|------|-----------------|
| genesis.actor | Privileged actor owning the MINT wallet for initial chain funding; registered during genesis bootstrap | SYSTEM |
| Orchestration (system) | Invokes block commitment per slot after block proposal | SYSTEM |

### Entities
| Entity | Description | Store Model |
|--------|-------------|-------------|
| Block | Fundamental unit containing transactions and metadata; full content lives in the existing `BLOCKS` store (owned by `blockchain::block`); carries no hashes at proposal time | Existing — Mutable State (block-owned) |
| Chain | Ordered, immutable sequence of *references* to committed blocks (`block_id`, `block_hash`, `round_id`, `previous_block_hash`) | NEW — Append-Only Journal |
| Chain State | Single record: current head block reference and height; updated atomically at each commitment | NEW — Mutable State |
| Chain Lifecycle Events | Journal of chain lifecycle facts (genesis committed, block committed) | NEW — Append-Only Journal |
| MINT Wallet | Special wallet holding the initial BachiCoin supply | Existing — WALLET store (wallet-owned) |

### Resources
| Resource | Description |
|----------|-------------|
| BachiCoin initial supply | 1,000,000 BachiCoin minted at genesis into the MINT wallet; fixed total supply of the closed system |

### Events
| Event | Trigger | Lifecycle Meaning |
|-------|---------|-------------------|
| `EV_BLOCK_COMMITTED_V0` (EXISTING — reused) | Successful commitment of a block reference to the chain (including genesis) | Block is canonical; chain head advanced |

### Relationships (Candidate Capabilities)
| Subject | Verb | Object | Capability Candidate |
|---------|------|--------|---------------------|
| Slot processing (orchestration) | invokes | Block commitment | Commitment invocation gateway (orchestration-owned dependency gap) |
| Block commitment | verifies | Proposed block eligibility | Eligibility verification (round sequence + proposed status) |
| Block commitment | marks | Block canonical in `BLOCKS` | Mark-block-canonical (block-owned dependency gap) |
| Block commitment | appends | Block reference to chain | Append block reference (computes hash, links to head) |
| Block commitment | updates | Chain state | Update chain state |
| Genesis bootstrap | orchestrates | Actor, wallet, mint, validator setup + genesis block + initial chain commitment | Chain initialization workflow |
| Genesis bootstrap | uses | Actor registration | Reuse existing identity capability (direct cross-subdomain CC call) |
| Genesis bootstrap | uses | Wallet creation / Minting / Validator registration | Gateway invocations of existing workflows |
| Genesis bootstrap | forms | Genesis block content in `BLOCKS[height=0]` | Genesis block formation (block-owned dependency gap) |

---

## 2. Capability Graph

| Capability | Status | Gap Register Entry | Notes |
|-----------|--------|--------------------|-------|
| Chain reference store (append-only) | CRITICAL | GAP-1 | No existing immutable store of committed block references. |
| Chain state store (mutable, single record) | CRITICAL | GAP-2 | No existing store tracks chain head and height. |
| Chain event journal (append-only) | CRITICAL | GAP-3 | Chain lifecycle facts need a chain-owned journal. |
| Chain initialization (genesis bootstrap) workflow | CRITICAL | GAP-4 | One-time bootstrap; orchestrates reused capabilities plus new chain capabilities. |
| Block commitment workflow | CRITICAL | GAP-5 | No existing capability commits block references to a chain. |
| Commit eligibility verification | CRITICAL | GAP-6 | Sequential round check + proposed-status check before commitment. |
| Genesis block formation (writes `BLOCKS[height=0]`) | CRITICAL | GAP-7 | Block-owned dependency gap — cross-subdomain writes are forbidden. |
| Mark block canonical (updates `BLOCKS` status/is_canonical) | CRITICAL | GAP-8 | Block-owned dependency gap. |
| Block commitment invocation from slot processing | CRITICAL | GAP-9 | Orchestration-owned dependency gap — gateway CC + slot workflow extension. |
| `WF_RUN_CONSENSUS_LOOP_V0` / `WF_PROPOSE_BLOCK_V0` / `CC_FORM_BLOCK_V0` | SATISFIED | — | Reused unchanged. |
| `EV_BLOCK_COMMITTED_V0` | SATISFIED | — | Existing event reserved for this CR; Emitted By table updated at authoring. |
| `CS_WORKFLOW_GATEWAY_V0`, `CS_APPENDONLY_JSONL_V0`, `CS_MUTABLE_JSON_V0` | SATISFIED | — | Existing substrates for gateways and stores. |
| `CT_PURE_KECCAK256_HASH_V0`, `CT_PURE_GENERATE_ID_V0`, `CT_PURE_ASSEMBLE_RECORD_V0` | SATISFIED | — | Existing transforms reused for hashing and genesis record assembly. |
| `CC_PERSIST_VERIFIED_ACTOR_V0`, `WF_CREATE_WALLET_V0`, `WF_MINT_V0`, `WF_REGISTER_VALIDATOR_V0` | SATISFIED | — | Reused for genesis bootstrap (direct CC call / gateway invocations). |

---

## 3. Dependency Graph

| From | To | Dependency Type | PPS Status |
|------|----|-----------------|------------|
| `blockchain::orchestration` (slot processing) | `blockchain::chain` (block commitment) | Capability call (workflow gateway) | GAP — orchestration-owned gateway CC + slot WF extension (GAP-9) |
| `blockchain::chain` (commitment) | `blockchain::block` (`BLOCKS` store) | Data read (proposed block record) | SATISFIED |
| `blockchain::chain` (commitment) | `blockchain::block` (mark canonical) | Capability call | GAP — block-owned (GAP-8) |
| `blockchain::chain` (genesis) | `blockchain::block` (genesis block formation) | Capability call | GAP — block-owned (GAP-7) |
| `blockchain::chain` (genesis) | `blockchain::identity` (actor registration) | Capability call | SATISFIED |
| `blockchain::chain` (genesis) | `blockchain::wallet` (wallet creation) | Capability call (workflow gateway) | SATISFIED |
| `blockchain::chain` (genesis) | `blockchain::transaction` (minting) | Capability call (workflow gateway) | SATISFIED |
| `blockchain::chain` (genesis) | `blockchain::consensus_pos` (validator registration) | Capability call (workflow gateway) | SATISFIED |

---

## 4. Constraint Register

| # | Constraint | Source |
|---|-----------|--------|
| 1 | The chain must be an immutable, ordered sequence of block references. | Domain knowledge, `2_domain_model_blockchain_chain_v0.md` |
| 2 | The blockchain is a closed monetary system; money neither leaves nor enters. | User clarification |
| 3 | Genesis must fund the chain with 1,000,000 BachiCoin in a "MINT" wallet owned by `genesis.actor`. | User clarification |
| 4 | **Canonical Chain Progression** — A block may be committed only if it exists with status `PROPOSED` and its `round_id` equals current head height + 1; its `previous_block_hash` is linked to the current head hash at commitment. | User feedback, CR scope, Iteration 2 verification (proposed blocks carry no hashes) |
| 5 | `BLOCKS` holds full block content (block-owned); the chain stores references only. | User clarification, Analysis Loop |
| 6 | **V0 Chain Model** — Single canonical chain; fork selection, reorganization, attestation, finalization out of scope. | User feedback |
| 7 | Chain capabilities write only chain-owned stores; all `BLOCKS` writes are block-owned capabilities. | Governance rule (cross-subdomain writes forbidden) |
| 8 | Genesis initialization executes exactly once. | User feedback |

---

## 5. Gap Register

| Gap Code | Capability | Owner Subdomain | Resolution |
|----------|-----------|-----------------|------------|
| GAP-1 | Chain reference store (append-only) | `blockchain::chain` | NEW store (dedicated chain STRUCTURE artifact) |
| GAP-2 | Chain state store (mutable) | `blockchain::chain` | NEW store (dedicated chain STRUCTURE artifact) |
| GAP-3 | Chain event journal (append-only) | `blockchain::chain` | NEW store (dedicated chain STRUCTURE artifact) |
| GAP-4 | Chain initialization workflow (+ intent, binding, support capabilities) | `blockchain::chain` | NEW artifacts |
| GAP-5 | Block commitment workflow (+ intent, binding, support capabilities) | `blockchain::chain` | NEW artifacts |
| GAP-6 | Commit eligibility verification (+ sequential round transform) | `blockchain::chain` | NEW artifacts |
| GAP-7 | Genesis block formation | `blockchain::block` | NEW artifact — dependency gap triggered by this CR |
| GAP-8 | Mark block canonical | `blockchain::block` | NEW artifact — dependency gap triggered by this CR |
| GAP-9 | Block commitment invocation from slot processing | `blockchain::orchestration` | NEW gateway CC + EXTEND slot workflow — dependency gap triggered by this CR |

---

## 6. Design Decisions Register

| # | Decision | Rationale | Constraints Imposed |
|---|----------|-----------|---------------------|
| 1 | Chain reference store is an append-only journal of block references. | Immutability and ordering are inherent to the substrate. | Chain store cannot be mutable; full block content never stored in it. |
| 2 | Genesis bootstrap is a dedicated one-time workflow reusing existing actor/wallet/mint/validator capabilities. | Genesis has unique properties (no parent, initial funding); existing capabilities are not re-authored. | Regular commitment cannot handle genesis; single-genesis check gates execution. |
| 3 | Commitment is invoked by the orchestration slot workflow via a gateway CC — not by an event trigger. | EV_ artifacts record facts; the runtime has no event subscription. Gateway invocation is the canonical chaining pattern (`CC_INVOKE_BLOCK_PROPOSAL_V0` precedent). | `WF_PROPOSE_BLOCK_V0` unchanged; slot workflow extended; gateway CC owned by orchestration. |
| 4 | Chain state is a mutable single-record store, updated atomically at each commitment. | Head/height must be readable without chain traversal. | Chain state is the canonical head authority; CCs must not derive head from chain traversal. |
| 5 | Hashes are computed at commitment (reusing `CT_PURE_KECCAK256_HASH_V0`); `previous_block_hash` is linked from the current head. | Proposed blocks carry no hashes (verified against `CC_FORM_BLOCK_V0`). | Eligibility checks reduce to round sequence + proposed status; no hash-comparison transform needed. |
| 6 | `blockchain::chain` is a new subdomain with a dedicated STRUCTURE artifact for its stores. | Distinct governance concern (ordering, immutability, canonical state); exclusive store ownership (orchestration STRUCTURE precedent). | Chain capabilities cannot reside in `blockchain::block`; no extension of `STRUCTURE_BLOCKCHAIN_STORAGE_V0`. |
| 7 | All `BLOCKS` writes (genesis formation, mark canonical) are block-owned dependency-gap capabilities. | Cross-subdomain writes are forbidden — no exceptions. | Chain workflows call these CCs cross-subdomain; ownership stays with `blockchain::block`. |
| 8 | Commitment signaling reuses existing `EV_BLOCK_COMMITTED_V0`. | The event exists and was reserved for this CR; inventory check before authoring new events. | No new event artifact; Emitted By table updated at authoring. |

---

## 7. Authoring Scope

### In Scope — This CR
| Capability | Gap Register Ref |
|-----------|-----------------|
| Chain reference store, chain state store, chain event journal (dedicated STRUCTURE) | GAP-1, GAP-2, GAP-3 |
| Chain initialization workflow + intent + binding + support capabilities | GAP-4 |
| Block commitment workflow + intent + binding + support capabilities | GAP-5 |
| Commit eligibility verification + sequential round transform | GAP-6 |
| Genesis block formation (block-owned) | GAP-7 |
| Mark block canonical (block-owned) | GAP-8 |
| Commitment invocation gateway + slot workflow extension (orchestration-owned) | GAP-9 |

### Deferred — Future CR
| Capability | Deferred Reason |
|-----------|-----------------|
| "Attest" block processing step | Explicitly out of scope for this CR for simplicity. |
| "Finalize" block processing step | Explicitly out of scope for this CR for simplicity. |
| Advanced block content validation (tx re-validation, proposer stake checks at commit) | Beyond basic chain integrity for this CR. |
| Fork selection / reorganization | V0 single canonical chain model. |

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 1 — Change Request & Input Elicitation | 1_change_request_blockchain_chain_v0.md | COMPLETE |
| Stage 2 — Domain Model Discovery | Actors, Entities, Resources, Events, Relationships | COMPLETE |
| Stage 3 — Analysis Loop | Capability Graph, Dependency Graph, Constraints, Gap Register | COMPLETE — SATURATED (2 iterations) |
| Stage 4 — Business Model | This document | COMPLETE |
| Stage 4b — Authoring Scope | IN/FUTURE CR boundary (Section 7) | COMPLETE |

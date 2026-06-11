# Design Intent: blockchain / chain
**Domain:** blockchain  
**Subdomain:** chain  
**Version:** V0  
**Status:** COMPLETE  
**Pipeline Stage:** Stage 6b — Design Intent (HOW)  
**Produced by:** v0.5.0 SDLC authoring pipeline  
**Purity:** HOW only — business facts (Business Model) and placement decisions (Governance Intent) not repeated  

---

## 1. Design Decisions Resolution

| Decision | Business Fact (Business Model) | Design Resolution |
| --- | --- | --- |
| 1 | Chain reference store is an append-only journal of block references. | `CHAIN` store on `CS_APPENDONLY_JSONL_V0`; each entry `{block_id, block_hash, round_id, previous_block_hash, timestamp}`. |
| 2 | Genesis bootstrap is a dedicated one-time workflow reusing existing capabilities. | `WF_INITIALIZE_CHAIN_V0`: single-genesis check → `CC_PERSIST_VERIFIED_ACTOR_V0` (direct cross-subdomain CC call) → gateway CCs for `WF_CREATE_WALLET_V0`, `WF_MINT_V0`, `WF_REGISTER_VALIDATOR_V0` → `CC_FORM_GENESIS_BLOCK_V0` (block-owned) → append genesis ref → init chain state. |
| 3 | Commitment is invoked by the orchestration slot workflow via gateway — not event-driven. | EXTEND `WF_PROCESS_SLOT_V0`: after `CC_INVOKE_BLOCK_PROPOSAL_V0` SUCCESS, insert `CC_INVOKE_BLOCK_COMMITMENT_V0` (orchestration-owned, `CS_WORKFLOW_GATEWAY_V0` → `WF_COMMIT_BLOCK_V0`), then `CC_ADVANCE_SLOT_CLOCK_V0`. `WF_PROPOSE_BLOCK_V0` unchanged. |
| 4 | Chain state is a mutable single-record store, atomically updated. | `CHAIN_STATE` store on `CS_MUTABLE_JSON_V0`, fixed key `canonical_chain_state`, fields `{current_head_block_id, current_head_block_hash, current_block_height}`. |
| 5 | Hashes are computed at commitment; proposed blocks carry none. | `CC_APPEND_BLOCK_REF_V0` / `CC_APPEND_GENESIS_BLOCK_REF_V0` compute `block_hash` via existing `CT_PURE_KECCAK256_HASH_V0`; `previous_block_hash` taken from `CHAIN_STATE` head (genesis: null). No hash-comparison CT needed. |
| 6 | New subdomain with dedicated storage structure. | New registry path `pgs_blockchain.registry.chain.*`; new `STRUCTURE_BLOCKCHAIN_CHAIN_STORAGE_V0`; `STRUCTURE_BLOCKCHAIN_STORAGE_V0` untouched. |
| 7 | All `BLOCKS` writes are block-owned. | `CC_FORM_GENESIS_BLOCK_V0` and `CC_MARK_BLOCK_CANONICAL_V0` authored under `pgs_blockchain.registry.block.*` (dependency gaps); chain WFs call them cross-subdomain. |
| 8 | Commitment signaling reuses the existing event. | `EV_BLOCK_COMMITTED_V0` recorded to `CHAIN_EVENTS`; its Emitted By metadata updated (no schema change). |

---

## 2. Store and Schema Design Decisions

### CHAIN Store

**Design resolution:** New append-only store of immutable block references.

| Field | Type | Description |
| --- | --- | --- |
| block_id | string | Unique identifier of the committed block (B-prefixed). |
| block_hash | string | Keccak256 hash of the block record, computed at commitment. |
| round_id | integer | Block height (consensus round number); genesis = 0. |
| previous_block_hash | string \| null | Hash of the preceding chain entry; null only for genesis. |
| timestamp | string (ISO-8601) | Commitment time. |

### CHAIN_STATE Store

**Design resolution:** New mutable store holding exactly one record under fixed key `canonical_chain_state` — the canonical head authority. CCs must not derive head state from CHAIN traversal.

| Field | Type | Description |
| --- | --- | --- |
| current_head_block_id | string | `block_id` of the most recently committed block. |
| current_head_block_hash | string | `block_hash` of the most recently committed block. |
| current_block_height | integer | `round_id` of the head. |

### CHAIN_EVENTS Store

**Design resolution:** New append-only journal of chain lifecycle facts; records `EV_BLOCK_COMMITTED_V0` payloads `{block_hash, height, is_canonical, timestamp}` per the existing event schema.

**Consequence:** All three stores are declared in the new `STRUCTURE_BLOCKCHAIN_CHAIN_STORAGE_V0` (Section 8). No change to `STRUCTURE_BLOCKCHAIN_STORAGE_V0`.

---

## 3. Artifact Inventory — Existing Artifacts

| Artifact | Action | Reason |
| --- | --- | --- |
| `blockchain::WF_PROCESS_SLOT_V0` | EXTEND | Insert commitment invocation after successful block proposal (Section 7). |
| `blockchain::EV_BLOCK_COMMITTED_V0` | UPDATE (metadata) | Emitted By table gains `WF_COMMIT_BLOCK_V0` / `CC_APPEND_BLOCK_REF_V0` and `WF_INITIALIZE_CHAIN_V0` / `CC_APPEND_GENESIS_BLOCK_REF_V0`. No schema or behavior change. |
| `blockchain::WF_PROPOSE_BLOCK_V0` | REUSE | Unchanged — the earlier event-emission extension is withdrawn. |
| `blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0` | REUSE | Unchanged — chain stores live in the new dedicated structure. |
| `blockchain::CC_PERSIST_VERIFIED_ACTOR_V0`, `blockchain::WF_CREATE_WALLET_V0`, `blockchain::WF_MINT_V0`, `blockchain::WF_REGISTER_VALIDATOR_V0` | REUSE | Genesis bootstrap dependencies. |
| `capability_side_effects::CS_WORKFLOW_GATEWAY_V0`, `CS_MUTABLE_JSON_V0`, `CS_APPENDONLY_JSONL_V0` | REUSE | Substrates for gateways and stores. |
| `capability_transforms::CT_PURE_KECCAK256_HASH_V0`, `CT_PURE_GENERATE_ID_V0`, `CT_PURE_ASSEMBLE_RECORD_V0` | REUSE | Hashing, genesis id generation, record assembly. |

---

## 4. Artifact Family Mapping — New Artifacts

### `blockchain::chain` — New Artifacts

#### Workflow: Chain Initialization

| Artifact | Family | Code | Status |
| --- | --- | --- | --- |
| Chain Initialization Workflow | WF | `blockchain::WF_INITIALIZE_CHAIN_V0` | NEW |
| Chain Initialization Intent | IN | `blockchain::IN_INITIALIZE_CHAIN_V0` | NEW |
| Chain Initialization Runtime Binding | RB | `blockchain::RB_INITIALIZE_CHAIN_V0` | NEW |

#### Workflow: Block Commitment

| Artifact | Family | Code | Status |
| --- | --- | --- | --- |
| Block Commitment Workflow | WF | `blockchain::WF_COMMIT_BLOCK_V0` | NEW |
| Block Commitment Intent | IN | `blockchain::IN_COMMIT_BLOCK_V0` | NEW |
| Block Commitment Runtime Binding | RB | `blockchain::RB_COMMIT_BLOCK_V0` | NEW |

#### Capability Contracts: Chain Management

| Capability | Family | Code | Status |
| --- | --- | --- | --- |
| Check Chain Not Initialized | CC | `blockchain::CC_CHECK_CHAIN_NOT_INITIALIZED_V0` | NEW |
| Invoke Wallet Creation (gateway) | CC | `blockchain::CC_INVOKE_WALLET_CREATION_V0` | NEW |
| Invoke Genesis Mint (gateway) | CC | `blockchain::CC_INVOKE_GENESIS_MINT_V0` | NEW |
| Invoke Validator Registration (gateway) | CC | `blockchain::CC_INVOKE_VALIDATOR_REGISTRATION_V0` | NEW |
| Append Genesis Block Reference | CC | `blockchain::CC_APPEND_GENESIS_BLOCK_REF_V0` | NEW |
| Update Chain State | CC | `blockchain::CC_UPDATE_CHAIN_STATE_V0` | NEW |
| Read Chain State | CC | `blockchain::CC_READ_CHAIN_STATE_V0` | NEW |
| Read Proposed Block | CC | `blockchain::CC_READ_PROPOSED_BLOCK_V0` | NEW |
| Verify Chain Commit Eligibility | CC | `blockchain::CC_VERIFY_CHAIN_COMMIT_ELIGIBILITY_V0` | NEW |
| Append Block Reference | CC | `blockchain::CC_APPEND_BLOCK_REF_V0` | NEW |

#### Capability Transforms: Chain Integrity

| Capability | Family | Code | Status |
| --- | --- | --- | --- |
| Sequential Round Check | CT | `blockchain::CT_PURE_COMPARE_ROUND_IDS_V0` | NEW |

#### Storage Structure

| Artifact | Family | Code | Status |
| --- | --- | --- | --- |
| Chain storage topology | STRUCTURE | `blockchain::STRUCTURE_BLOCKCHAIN_CHAIN_STORAGE_V0` | NEW |

### `blockchain::block` — Dependency Gap (Owned by `block`, Triggered by This CR)

| Capability | Family | Code | Status |
| --- | --- | --- | --- |
| Form Genesis Block (writes `BLOCKS[height=0]`) | CC | `blockchain::CC_FORM_GENESIS_BLOCK_V0` | NEW — subdomain: `block` |
| Mark Block Canonical (updates status/is_canonical in `BLOCKS`) | CC | `blockchain::CC_MARK_BLOCK_CANONICAL_V0` | NEW — subdomain: `block` |

### `blockchain::orchestration` — Dependency Gap (Owned by `orchestration`, Triggered by This CR)

| Capability | Family | Code | Status |
| --- | --- | --- | --- |
| Block Commitment Invocation (gateway) | CC | `blockchain::CC_INVOKE_BLOCK_COMMITMENT_V0` | NEW — subdomain: `orchestration` |

### New Artifacts — Lifecycle Status

All 21 new artifacts are classified `ACTIVE` at authoring time. No new artifact starts in any other lifecycle state.

---

## 4b. Module Path Assignments

### pgs_blockchain — chain subdomain (new registry namespace)

| Artifact Family | Module Path |
|----------------|-------------|
| IN | `pgs_blockchain.registry.chain.intents` |
| WF | `pgs_blockchain.registry.chain.workflows` |
| CC | `pgs_blockchain.registry.chain.capability_contracts` |
| CT | `pgs_blockchain.registry.chain.capability_transforms` |
| RB | `pgs_blockchain.registry.chain.runtime_bindings` |
| STRUCTURE | `pgs_blockchain.registry.chain.structures` |
| Implementation | `pgs_blockchain.implementation.chain` |

### Dependency-gap artifacts (peer-owned paths)

| Artifact | Module Path |
|----------|-------------|
| `CC_FORM_GENESIS_BLOCK_V0`, `CC_MARK_BLOCK_CANONICAL_V0` | `pgs_blockchain.registry.block.capability_contracts` |
| `CC_INVOKE_BLOCK_COMMITMENT_V0` | `pgs_blockchain.registry.orchestration.capability_contracts` |

---

## 4c. Runtime Binding (RB) Declarations

### `blockchain::RB_INITIALIZE_CHAIN_V0`

Binds `WF_INITIALIZE_CHAIN_V0`.

| CS Binding | Role in WF |
|-----------|-----------|
| `capability_side_effects::CS_MUTABLE_JSON_V0` | CHAIN_STATE read (CC_CHECK_CHAIN_NOT_INITIALIZED_V0) + write (CC_UPDATE_CHAIN_STATE_V0); BLOCKS write (CC_FORM_GENESIS_BLOCK_V0, block-owned) |
| `capability_side_effects::CS_APPENDONLY_JSONL_V0` | CHAIN append + CHAIN_EVENTS append (CC_APPEND_GENESIS_BLOCK_REF_V0); BLOCK_EVENTS append (CC_FORM_GENESIS_BLOCK_V0) |
| `capability_side_effects::CS_WORKFLOW_GATEWAY_V0` | Sub-workflow invocation (CC_INVOKE_WALLET_CREATION_V0, CC_INVOKE_GENESIS_MINT_V0, CC_INVOKE_VALIDATOR_REGISTRATION_V0) |
| `capability_side_effects::CS_REGISTRY_V0` | Actor registry write (CC_PERSIST_VERIFIED_ACTOR_V0, identity-owned) |

**storage_structure:** `blockchain::STRUCTURE_BLOCKCHAIN_CHAIN_STORAGE_V0` (chain stores); block- and identity-owned steps resolve their stores via `blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0`.

### `blockchain::RB_COMMIT_BLOCK_V0`

Binds `WF_COMMIT_BLOCK_V0`.

| CS Binding | Role in WF |
|-----------|-----------|
| `capability_side_effects::CS_MUTABLE_JSON_V0` | CHAIN_STATE read/write; BLOCKS read (CC_READ_PROPOSED_BLOCK_V0) and write (CC_MARK_BLOCK_CANONICAL_V0, block-owned) |
| `capability_side_effects::CS_APPENDONLY_JSONL_V0` | CHAIN append + CHAIN_EVENTS append (CC_APPEND_BLOCK_REF_V0) |

**storage_structure:** `blockchain::STRUCTURE_BLOCKCHAIN_CHAIN_STORAGE_V0` (chain stores); block-owned steps resolve `BLOCKS` via `blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0`.

*No gateway binding — `WF_COMMIT_BLOCK_V0` invokes no sub-workflows.*

---

## 5. Execution Topology — `WF_INITIALIZE_CHAIN_V0`

```
IN_INITIALIZE_CHAIN_V0
    ACK  → CC_CHECK_CHAIN_NOT_INITIALIZED_V0
    NACK → EXIT

CC_CHECK_CHAIN_NOT_INITIALIZED_V0              ← blockchain::chain
    SUCCESS        → CC_PERSIST_VERIFIED_ACTOR_V0
    ALREADY_EXISTS → EXIT
    VIOLATION      → EXIT
    BACKEND_ERROR  → EXIT

CC_PERSIST_VERIFIED_ACTOR_V0                   ← blockchain::identity (reused)
    SUCCESS        → CC_INVOKE_WALLET_CREATION_V0
    ALREADY_EXISTS → EXIT
    VIOLATION      → EXIT
    BACKEND_ERROR  → EXIT

CC_INVOKE_WALLET_CREATION_V0                   ← blockchain::chain (gateway → WF_CREATE_WALLET_V0)
    SUCCESS        → CC_INVOKE_GENESIS_MINT_V0
    VIOLATION      → EXIT
    BACKEND_ERROR  → EXIT

CC_INVOKE_GENESIS_MINT_V0                      ← blockchain::chain (gateway → WF_MINT_V0)
    SUCCESS        → CC_INVOKE_VALIDATOR_REGISTRATION_V0
    VIOLATION      → EXIT
    BACKEND_ERROR  → EXIT

CC_INVOKE_VALIDATOR_REGISTRATION_V0            ← blockchain::chain (gateway → WF_REGISTER_VALIDATOR_V0)
    SUCCESS        → CC_FORM_GENESIS_BLOCK_V0
    VIOLATION      → EXIT
    BACKEND_ERROR  → EXIT

CC_FORM_GENESIS_BLOCK_V0                       ← blockchain::block (dependency gap)
    SUCCESS        → CC_APPEND_GENESIS_BLOCK_REF_V0
    VIOLATION      → EXIT
    BACKEND_ERROR  → EXIT

CC_APPEND_GENESIS_BLOCK_REF_V0                 ← blockchain::chain
    SUCCESS        → CC_UPDATE_CHAIN_STATE_V0
    VIOLATION      → EXIT
    BACKEND_ERROR  → EXIT

CC_UPDATE_CHAIN_STATE_V0                       ← blockchain::chain
    SUCCESS        → EXIT_SUCCESS
    VIOLATION      → EXIT
    BACKEND_ERROR  → EXIT

EXIT
EXIT_SUCCESS
```

**Path summary:**
- Happy path: admission → single-genesis check → genesis actor → MINT wallet → initial mint → genesis validator → genesis block → genesis chain entry → chain state → EXIT_SUCCESS
- Short-circuit exits: NACK; ALREADY_EXISTS at the genesis check (exactly-once invariant) or actor registration; VIOLATION/BACKEND_ERROR at any node

**Cross-subdomain calls in this WF:** `CC_PERSIST_VERIFIED_ACTOR_V0` (identity); `WF_CREATE_WALLET_V0`, `WF_MINT_V0`, `WF_REGISTER_VALIDATOR_V0` via chain-owned gateway CCs; `CC_FORM_GENESIS_BLOCK_V0` (block). All workflow nodes are IN/CC/EXIT — no WF appears as a node.

---

## 6. Execution Topology — `WF_COMMIT_BLOCK_V0`

```
IN_COMMIT_BLOCK_V0
    ACK  → CC_READ_CHAIN_STATE_V0
    NACK → EXIT

CC_READ_CHAIN_STATE_V0                         ← blockchain::chain
    SUCCESS       → CC_READ_PROPOSED_BLOCK_V0
    NOT_FOUND     → EXIT        (chain not initialized)
    VIOLATION     → EXIT
    BACKEND_ERROR → EXIT

CC_READ_PROPOSED_BLOCK_V0                      ← blockchain::chain (cross-subdomain READ of BLOCKS)
    SUCCESS       → CC_VERIFY_CHAIN_COMMIT_ELIGIBILITY_V0
    NOT_FOUND     → EXIT        (unknown block)
    VIOLATION     → EXIT
    BACKEND_ERROR → EXIT

CC_VERIFY_CHAIN_COMMIT_ELIGIBILITY_V0          ← blockchain::chain
    SUCCESS       → CC_MARK_BLOCK_CANONICAL_V0
    VIOLATION     → EXIT        (wrong status or non-sequential round)
    BACKEND_ERROR → EXIT

CC_MARK_BLOCK_CANONICAL_V0                     ← blockchain::block (dependency gap)
    SUCCESS       → CC_APPEND_BLOCK_REF_V0
    NOT_FOUND     → EXIT
    VIOLATION     → EXIT
    BACKEND_ERROR → EXIT

CC_APPEND_BLOCK_REF_V0                         ← blockchain::chain
    SUCCESS       → CC_UPDATE_CHAIN_STATE_V0
    VIOLATION     → EXIT
    BACKEND_ERROR → EXIT

CC_UPDATE_CHAIN_STATE_V0                       ← blockchain::chain
    SUCCESS       → EXIT_SUCCESS
    VIOLATION     → EXIT
    BACKEND_ERROR → EXIT

EXIT
EXIT_SUCCESS
```

**Path summary:**
- Happy path: admission → read head → read proposed block → eligibility (status + sequence) → mark canonical → append linked reference + record `EV_BLOCK_COMMITTED_V0` → advance head → EXIT_SUCCESS
- Short-circuit exits: NACK; NOT_FOUND (uninitialized chain, unknown block); VIOLATION (wrong status, non-sequential round); BACKEND_ERROR at any node

**Cross-subdomain calls in this WF:** `CC_MARK_BLOCK_CANONICAL_V0` (block-owned write to `BLOCKS`); `CC_READ_PROPOSED_BLOCK_V0` performs a cross-subdomain read (permitted).

---

## 6b. CC Pipeline Declarations (Summary)

*Design-level pipeline intent. Full JSONPath bindings are authoring-phase detail.*

### `blockchain::chain` Pipelines

**`CC_CHECK_CHAIN_NOT_INITIALIZED_V0`**
- Step 1: `CS_MUTABLE_JSON_V0` — READ — `CHAIN_STATE`, key `canonical_chain_state`
- Result statuses: `SUCCESS` (not initialized — proceed), `ALREADY_EXISTS` (head present — block re-initialization), `VIOLATION`, `BACKEND_ERROR`

**`CC_INVOKE_WALLET_CREATION_V0`** / **`CC_INVOKE_GENESIS_MINT_V0`** / **`CC_INVOKE_VALIDATOR_REGISTRATION_V0`**
- Step 1: `CS_WORKFLOW_GATEWAY_V0` — INVOKE — `WF_CREATE_WALLET_V0` / `WF_MINT_V0` / `WF_REGISTER_VALIDATOR_V0` with payload mapped from intent inputs → invocation result
- Result statuses: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`
- *Pattern precedent: `CC_INVOKE_BLOCK_PROPOSAL_V0`. Each target WF runs under its own admission intent.*

**`CC_APPEND_GENESIS_BLOCK_REF_V0`**
- Step 1: `CT_PURE_KECCAK256_HASH_V0` — HASH — genesis block record → `block_hash`
- Step 2: `CT_PURE_ASSEMBLE_RECORD_V0` — ASSEMBLE — `{block_id, block_hash, round_id: 0, previous_block_hash: null, timestamp}` → chain entry
- Step 3: `CS_APPENDONLY_JSONL_V0` — APPEND — `CHAIN`
- Step 4: `CS_APPENDONLY_JSONL_V0` — APPEND — `CHAIN_EVENTS` (`EV_BLOCK_COMMITTED_V0` payload, height 0)
- Result statuses: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`

**`CC_UPDATE_CHAIN_STATE_V0`**
- Step 1: `CS_MUTABLE_JSON_V0` — WRITE — `CHAIN_STATE`, key `canonical_chain_state`, value `{current_head_block_id, current_head_block_hash, current_block_height}`
- Result statuses: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`

**`CC_READ_CHAIN_STATE_V0`**
- Step 1: `CS_MUTABLE_JSON_V0` — READ — `CHAIN_STATE`, key `canonical_chain_state` → head fields
- Result statuses: `SUCCESS`, `NOT_FOUND` (uninitialized), `VIOLATION`, `BACKEND_ERROR`

**`CC_READ_PROPOSED_BLOCK_V0`**
- Step 1: `CS_MUTABLE_JSON_V0` — READ — `BLOCKS`, key `block_id` → `block_record` *(cross-subdomain read — permitted)*
- Result statuses: `SUCCESS`, `NOT_FOUND`, `VIOLATION`, `BACKEND_ERROR`

**`CC_VERIFY_CHAIN_COMMIT_ELIGIBILITY_V0`**
- Step 1: `CT_PURE_VALIDATE_SET_MEMBERSHIP_V0` (or equivalent status check) — `block_record.status == PROPOSED`
- Step 2: `CT_PURE_COMPARE_ROUND_IDS_V0` — `block_record.round_id == current_block_height + 1`
- Result statuses: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`

**`CC_APPEND_BLOCK_REF_V0`**
- Step 1: `CT_PURE_KECCAK256_HASH_V0` — HASH — `block_record` → `block_hash`
- Step 2: `CT_PURE_ASSEMBLE_RECORD_V0` — ASSEMBLE — `{block_id, block_hash, round_id, previous_block_hash: current_head_block_hash, timestamp}` → chain entry
- Step 3: `CS_APPENDONLY_JSONL_V0` — APPEND — `CHAIN`
- Step 4: `CS_APPENDONLY_JSONL_V0` — APPEND — `CHAIN_EVENTS` (`EV_BLOCK_COMMITTED_V0` payload)
- Result statuses: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`

### `blockchain::block` Pipelines (dependency gap)

**`CC_FORM_GENESIS_BLOCK_V0`**
- Step 1: `CT_PURE_GENERATE_ID_V0` — GENERATE — prefix `B`, data `round_id=0` → `block_id`
- Step 2: `CT_PURE_ASSEMBLE_RECORD_V0` — ASSEMBLE — `{block_id, round_id: 0, slot: 0, epoch: 0, proposer_id: genesis_actor_id, tx_ids: [], initial_state, timestamp, status: PROPOSED, is_canonical: false}` → `genesis_block_record`
- Step 3: `CS_MUTABLE_JSON_V0` — WRITE — `BLOCKS`, key `block_id`
- Step 4: `CS_APPENDONLY_JSONL_V0` — APPEND — `BLOCK_EVENTS`
- Result statuses: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`
- *All writes within block-owned stores.*

**`CC_MARK_BLOCK_CANONICAL_V0`**
- Step 1: `CS_MUTABLE_JSON_V0` — READ — `BLOCKS`, key `block_id` → record
- Step 2: `CS_MUTABLE_JSON_V0` — WRITE — `BLOCKS`, key `block_id`, record updated `{status: COMMITTED, is_canonical: true}`
- Step 3: `CS_APPENDONLY_JSONL_V0` — APPEND — `BLOCK_EVENTS`
- Result statuses: `SUCCESS`, `NOT_FOUND`, `VIOLATION`, `BACKEND_ERROR`
- *All writes within block-owned stores.*

### `blockchain::orchestration` Pipeline (dependency gap)

**`CC_INVOKE_BLOCK_COMMITMENT_V0`**
- Step 1: `CS_WORKFLOW_GATEWAY_V0` — INVOKE — `blockchain::WF_COMMIT_BLOCK_V0` with payload `{block_id, round_id, triggered_by, timestamp}` from slot/proposal context
- Result statuses: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`
- *Mirrors `CC_INVOKE_BLOCK_PROPOSAL_V0` exactly.*

---

## 7. Execution Topology — `WF_PROCESS_SLOT_V0` (EXTEND)

**Change from existing:** one node inserted between block proposal and slot clock advancement. All other nodes and routing unchanged.

```
...
CC_INVOKE_BLOCK_PROPOSAL_V0                    ← blockchain::orchestration (existing)
    SUCCESS       → CC_INVOKE_BLOCK_COMMITMENT_V0   // CHANGED: was → CC_ADVANCE_SLOT_CLOCK_V0
    VIOLATION     → EXIT
    BACKEND_ERROR → EXIT

CC_INVOKE_BLOCK_COMMITMENT_V0                  ← blockchain::orchestration (NEW, gateway → WF_COMMIT_BLOCK_V0)
    SUCCESS       → CC_ADVANCE_SLOT_CLOCK_V0
    VIOLATION     → EXIT
    BACKEND_ERROR → EXIT

CC_ADVANCE_SLOT_CLOCK_V0                       ← blockchain::orchestration (existing, unchanged)
...
```

**Rationale:** the slot is marked complete only after the proposed block is committed to the chain — one slot yields one proposal and one commitment in the V0 single-chain model.

---

## 8. STRUCTURE Artifact — `blockchain::STRUCTURE_BLOCKCHAIN_CHAIN_STORAGE_V0` (NEW)

*Dedicated structure: chain stores are exclusively chain-owned (precedent: `STRUCTURE_BLOCKCHAIN_ORCHESTRATION_STORAGE_V0`).*

| Store Name | Storage Type | Path | Used By |
| --- | --- | --- | --- |
| CHAIN | `CS_APPENDONLY_JSONL_V0` | `blockchain/chain/refs/chain.jsonl` | `CC_APPEND_GENESIS_BLOCK_REF_V0`, `CC_APPEND_BLOCK_REF_V0` |
| CHAIN_STATE | `CS_MUTABLE_JSON_V0` | `blockchain/chain/state/chain_state.json` | `CC_CHECK_CHAIN_NOT_INITIALIZED_V0`, `CC_READ_CHAIN_STATE_V0`, `CC_UPDATE_CHAIN_STATE_V0` |
| CHAIN_EVENTS | `CS_APPENDONLY_JSONL_V0` | `blockchain/chain/events/chain_events.jsonl` | `CC_APPEND_GENESIS_BLOCK_REF_V0`, `CC_APPEND_BLOCK_REF_V0` |

**Store Ownership Invariant:** No non-chain artifact may write these stores. Cross-subdomain writes are a hard governance violation.

---

## 9. New Capability Transform

### `blockchain::CT_PURE_COMPARE_ROUND_IDS_V0`

| Field | Value |
| --- | --- |
| Code | `blockchain::CT_PURE_COMPARE_ROUND_IDS_V0` |
| Family | CT |
| Purity | ct_pure — no side effects; CT never calls CS |
| Operation | Sequential round check |
| Inputs | `proposed_round_id` (integer), `current_block_height` (integer) |
| Output | `sequential` (boolean) |
| Algorithm | `sequential = (proposed_round_id == current_block_height + 1)` — integer arithmetic only; deterministic |
| Failure | VIOLATION if inputs are not valid integers |

*Inventory check performed: no existing CT performs sequence comparison (`CT_PURE_VALIDATE_PARAMETER_RULES_V0` validates static parameter constraints, not relative sequence). Hash computation reuses `CT_PURE_KECCAK256_HASH_V0` — the hash-comparison CT proposed in an earlier draft is withdrawn.*

---

## 10. Intent Schemas

### `IN_INITIALIZE_CHAIN_V0`
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| initial_state | object | YES | Initial configuration embedded in the genesis block. |
| genesis_actor_id | string | YES | Privileged funding actor ("genesis.actor"). |
| mint_wallet_id | string | YES | MINT wallet to create and fund. |
| initial_supply | integer | YES | Genesis mint amount (1,000,000 BachiCoin). |
| validator_actor_id | string | YES | Genesis validator to register. |
| timestamp | string | YES | ISO 8601 genesis creation time. |

Outcomes: `ACK` (payload valid, proceed), `NACK` (payload invalid, reject)

### `IN_COMMIT_BLOCK_V0`
| Field | Type | Required | Description |
| --- | --- | --- | --- |
| block_id | string | YES | Proposed block to commit. |
| round_id | integer | YES | Declared height; checked for sequence in-workflow. |
| triggered_by | string | YES | Actor context of the invoking slot workflow. |
| timestamp | string | YES | ISO 8601 commitment time. |

Outcomes: `ACK` (payload valid, proceed), `NACK` (payload invalid, reject)

*No hash fields — proposed blocks carry no hashes; commitment computes them.*

---

## 11. Artifact Summary

| Action | Count | Notes |
| --- | --- | --- |
| EXTEND | 1 | `blockchain::WF_PROCESS_SLOT_V0` (insert commitment invocation node) |
| UPDATE (metadata) | 1 | `blockchain::EV_BLOCK_COMMITTED_V0` (Emitted By table only) |
| NEW (`blockchain::chain`) | 18 | WF×2, IN×2, RB×2, CC×10, CT×1, STRUCTURE×1 |
| NEW (`blockchain::block`) | 2 | `CC_FORM_GENESIS_BLOCK_V0`, `CC_MARK_BLOCK_CANONICAL_V0` |
| NEW (`blockchain::orchestration`) | 1 | `CC_INVOKE_BLOCK_COMMITMENT_V0` |
| **Total** | **23** | 21 NEW + 1 EXTEND + 1 UPDATE |

*Reconciled against Section 4: 18 + 2 + 1 = 21 NEW rows. Build dependency order is the output of Stage 7.*

---

## 12. Gate 1 — Design Approval

**Gate 1 closes here.** The full dossier (Stages 1–6b) is presented for review as a body. The quality-check pass amended Stages 2–6 (Iteration 2 findings); those amendments are part of this review.

**Key design decisions to confirm at Gate 1:**

1. **Integration pattern:** commitment invoked from `WF_PROCESS_SLOT_V0` via orchestration-owned gateway CC — replaces the withdrawn event-driven design; `WF_PROPOSE_BLOCK_V0` untouched.
2. **Hash-at-commit:** block hashes computed at commitment (keccak256 reuse); linkage constructed from `CHAIN_STATE` head; eligibility = PROPOSED status + sequential round.
3. **Ownership split:** all `BLOCKS` writes via two NEW block-owned CCs (genesis formation, mark canonical); chain writes only chain stores.
4. **Storage:** three chain stores in NEW dedicated `STRUCTURE_BLOCKCHAIN_CHAIN_STORAGE_V0`; existing domain structure untouched.
5. **Event reuse:** existing `EV_BLOCK_COMMITTED_V0` reused; metadata-only update.
6. **Genesis bootstrap:** one-time workflow with single-genesis check; reuses identity/wallet/transaction/consensus_pos capabilities via direct CC call + gateway CCs.
7. **Totals:** 23 authoring actions — 21 NEW (18 chain, 2 block, 1 orchestration), 1 EXTEND, 1 metadata UPDATE.

*Gate 1 approval authorizes Stage 7 — Authoring Mandate. Gate 2 (after Stage 7) locks the dossier before artifact authoring begins.*

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
| Stage 6 — Governance Intent | 6_governance_intent_blockchain_chain_v0.md | COMPLETE |
| Stage 6b — Design Intent | This document | PENDING GATE 1 APPROVAL |
| Stage 7 — Authoring Mandate | 7_authoring_mandate_blockchain_chain_v0.md | PENDING GATE 2 APPROVAL |
| Stage 8 — Authoring Manifest | 8_authoring_manifest_blockchain_chain_v0.md | PENDING — baseline created |

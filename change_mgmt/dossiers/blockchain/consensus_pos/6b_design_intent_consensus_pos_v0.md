# Design Intent: blockchain / consensus_pos
**Domain:** blockchain  
**Subdomain:** consensus_pos  
**Version:** V0  
**Status:** DRAFT  
**Pipeline Stage:** Stage 6b — Design Intent (HOW)  
**Produced by:** v0.5.0 SDLC authoring pipeline  
**Purity:** HOW only — business facts (Business Model) and placement decisions (Governance Intent) not repeated  

---

## 1. Design Decisions Resolution

The Design Decisions Register was populated throughout Stages 1–4. These decisions are resolved here.

| Decision | Business Fact (Business Model) | Design Resolution |
| --- | --- | --- |
| Proposer selection algorithm | "One Validator selected as Proposer per Consensus Round" | Round-robin: `round_number % eligible_pool_size` — deterministic, no randomness required this CR |
| Consensus loop interval (30s) | "Consensus rounds are time-bounded" | External test script concern — not a PGS artifact; runtime stays payload-triggered |
| Transaction submission interval (20s) | "Transactions arrive continuously during test" | External test script concern — not a PGS artifact |
| Pool size limit (10 validators) | "Active participation pool is bounded" | Pool limit is a runtime configuration parameter read by CC_QUERY_ELIGIBLE_VALIDATORS_V0; not hardcoded in any artifact |
| tx_ids[] reference in block | "Block references submitted transactions" | Block record contains `tx_ids` as array field, sourced from CC_QUERY_PENDING_TRANSACTIONS_V0 output |
| Single-node only | "Single-node configuration for this CR" | No multi-node topology artifacts; no peer discovery or network propagation CCs authored |

---

## 2. Enrollment Store Decision

The Governance Intent required persistent storage for "validator enrollment (active participation status + stake credential)."

**Design resolution:** The existing VALIDATOR store serves as the enrollment store. No separate VALIDATOR_ENROLLMENT entity store is created. The validator record is enriched to include:

| Field | Type | Description |
| --- | --- | --- |
| actor_id | string | Identity registry link — primary key |
| stake | string | Declared stake credential (amount or identifier) |
| enrollment_status | string | ACTIVE, INACTIVE, or EXCLUDED |
| registered_at | string | Timestamp of registration |

The VALIDATOR store (CS_MUTABLE_JSON_V0, path: `blockchain/consensus_pos/registry/validators.json`) holds this enriched record. Active participation pool query reads this store filtered by `enrollment_status = ACTIVE` and `stake` present.

**Consequence:** CC_WRITE_VALIDATOR_RECORD_V0 and IN_VALIDATOR_REGISTERED_V0 must be replaced to include `stake` and `enrollment_status` in their schema declarations. The store path and CS type are unchanged.

---

## 3. Artifact Inventory — Existing Artifacts

| Artifact | Action | Reason |
| --- | --- | --- |
| `blockchain::WF_REGISTER_VALIDATOR_V0` | REPLACE | Re-author through correct governed pipeline (GI gate now satisfied); WF topology is sound, pipeline provenance was flawed |
| `blockchain::IN_VALIDATOR_REGISTERED_V0` | REPLACE | Enrich input schema: add `stake` and `enrollment_status` fields |
| `blockchain::CC_WRITE_VALIDATOR_RECORD_V0` | REPLACE | Validator record must include `stake` and `enrollment_status`; re-declare with enriched schema |
| `blockchain::CC_CHECK_ACTOR_EXISTS_V0` | REUSE | Sound — no change |
| `blockchain::CC_CHECK_VALIDATOR_EXISTS_V0` | REUSE | Sound — no change |
| `blockchain::CC_APPEND_VALIDATOR_EVENT_V0` | REUSE | Sound — no change |
| `blockchain::EV_VALIDATOR_REGISTERED_V0` | REUSE | Sound — no change |
| `blockchain::RB_REGISTER_VALIDATOR_V0` | REUSE | No new CCs; runtime binding remains valid |
| `capability_transforms::CT_PURE_ASSEMBLE_RECORD_V0` | REUSE | Generic record assembler — used for block record construction |
| `capability_transforms::CT_PURE_GENERATE_ID_V0` | REUSE | Block ID generation (prefix: BLK) |
| `capability_side_effects::CS_MUTABLE_JSON_V0` | REUSE | Block persistence (BLOCKS store) and validator reads |
| `capability_side_effects::CS_APPENDONLY_JSONL_V0` | REUSE | Event journals and round records |
| `blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0` | EXTEND | Add CONSENSUS_ROUNDS, CONSENSUS_EVENTS (consensus_pos); BLOCKS, BLOCK_EVENTS (blockchain::block) — see Section 8 |

---

## 4. Artifact Family Mapping — New Artifacts

Mapping from Governance Outcome capabilities to artifact families, with FQDN codes assigned. New artifacts are organized by subdomain ownership, as declared in Governance Intent.

### blockchain::consensus_pos — New Artifacts

#### Workflow: Block Proposal Process

| Artifact | Family | Code | Status |
| --- | --- | --- | --- |
| Block proposal governing workflow | WF | `blockchain::WF_PROPOSE_BLOCK_V0` | NEW |
| Block proposal admission intent | IN | `blockchain::IN_BLOCK_PROPOSED_V0` | NEW |
| Block proposal runtime binding | RB | `blockchain::RB_PROPOSE_BLOCK_V0` | NEW |

#### Capability Contracts: Consensus Pipeline

| Capability | Family | Code | Status |
| --- | --- | --- | --- |
| Eligible validator pool query | CC | `blockchain::CC_QUERY_ELIGIBLE_VALIDATORS_V0` | NEW |
| Proposer selection from eligible pool | CC | `blockchain::CC_SELECT_PROPOSER_V0` | NEW |
| Consensus round record (PROPOSED outcome) | CC | `blockchain::CC_RECORD_CONSENSUS_ROUND_V0` | NEW |
| Round skip record and event | CC | `blockchain::CC_SKIP_ROUND_V0` | NEW |

#### Capability Transform: Proposer Selection Algorithm

| Capability | Family | Code | Status |
| --- | --- | --- | --- |
| Deterministic proposer selection | CT | `blockchain::CT_PURE_SELECT_PROPOSER_V0` | NEW |

#### Events: Consensus Lifecycle

| Event | Family | Code | Status |
| --- | --- | --- | --- |
| Round skipped | EV | `blockchain::EV_ROUND_SKIPPED_V0` | NEW |

---

### blockchain::block — New Artifacts (New Subdomain Established This CR)

Block artifacts are authored under `blockchain::block` subdomain governance. This CR establishes `blockchain::block` as a new governed subdomain. These artifacts are authored now because `consensus_pos` cannot function without block formation capability — but ownership is clearly block's, not consensus's. Six months from now: Block ≠ Consensus.

#### Capability Contracts: Block Pipeline

| Capability | Family | Code | Status |
| --- | --- | --- | --- |
| Block formation and persistence | CC | `blockchain::CC_FORM_BLOCK_V0` | NEW — subdomain: block |

*Note: Block record assembly uses the existing `capability_transforms::CT_PURE_ASSEMBLE_RECORD_V0` — no new CT required for that step.*

#### Events: Block Lifecycle

| Event | Family | Code | Status |
| --- | --- | --- | --- |
| Block proposed | EV | `blockchain::EV_BLOCK_PROPOSED_V0` | NEW — subdomain: block |

---

### blockchain::transaction — Dependency Gap (Owned by transaction, Triggered by This CR)

The Governance Intent identified a gap: no existing PPS artifact covers pending transaction query. This capability is owned by `blockchain::transaction` — consensus_pos is its consumer, not its owner. This CR triggers its authoring; the artifact carries `subdomain: transaction`.

| Capability | Family | Code | Status |
| --- | --- | --- | --- |
| Pending transaction query | CC | `blockchain::CC_QUERY_PENDING_TRANSACTIONS_V0` | NEW — subdomain: transaction |

---

## 5. Execution Topology — WF_PROPOSE_BLOCK_V0

High-level DAG. JSONPath input bindings are authoring-phase detail.

```
IN_BLOCK_PROPOSED_V0
    ACK  → CC_QUERY_ELIGIBLE_VALIDATORS_V0
    NACK → EXIT

CC_QUERY_ELIGIBLE_VALIDATORS_V0         ← consensus_pos
    SUCCESS       → CC_SELECT_PROPOSER_V0
    NOT_FOUND     → EXIT                  ← no eligible validators; no block; no skip record
    VIOLATION     → EXIT
    BACKEND_ERROR → EXIT

CC_SELECT_PROPOSER_V0                   ← consensus_pos
    SUCCESS       → CC_QUERY_PENDING_TRANSACTIONS_V0
    VIOLATION     → EXIT

CC_QUERY_PENDING_TRANSACTIONS_V0        ← blockchain::transaction (cross-subdomain call)
    SUCCESS       → CC_FORM_BLOCK_V0     ← pending transactions exist
    EMPTY         → CC_SKIP_ROUND_V0     ← no pending transactions
    VIOLATION     → EXIT
    BACKEND_ERROR → EXIT

[PROPOSE PATH]
CC_FORM_BLOCK_V0                        ← blockchain::block (cross-subdomain call)
    SUCCESS       → CC_RECORD_CONSENSUS_ROUND_V0
    VIOLATION     → EXIT
    BACKEND_ERROR → EXIT

CC_RECORD_CONSENSUS_ROUND_V0            ← consensus_pos
    SUCCESS       → EXIT
    VIOLATION     → EXIT
    BACKEND_ERROR → EXIT

[SKIP PATH]
CC_SKIP_ROUND_V0                        ← consensus_pos
    SUCCESS       → EXIT
    VIOLATION     → EXIT
    BACKEND_ERROR → EXIT

EXIT
```

**Path summary:**
- Propose path: eligible pool found → proposer selected → transactions pending → block formed (blockchain::block) + event → round recorded → EXIT
- Skip path: eligible pool found → proposer selected → no transactions → skip recorded + event → EXIT
- Short-circuit exits: no eligible pool; admission NACK; any VIOLATION or BACKEND_ERROR

**Cross-subdomain calls in this WF:** `CC_QUERY_PENDING_TRANSACTIONS_V0` (transaction-owned) and `CC_FORM_BLOCK_V0` (block-owned) are called from a consensus_pos WF. Cross-subdomain calls are permitted within the `blockchain` domain. The CCs execute writes within their own subdomain stores only.

---

## 6. CC Pipeline Declarations (Summary)

Design-level pipeline intent for each new CC. Full JSONPath bindings are authoring-phase detail. Pipelines are grouped by subdomain ownership.

### consensus_pos Pipelines

**CC_QUERY_ELIGIBLE_VALIDATORS_V0** *(consensus_pos)*
- Step 1: CS_MUTABLE_JSON_V0 — LIST — VALIDATOR store → raw validator list
- Step 2: CT_PURE_EXTRACT_V0 (REUSE) — filter by `enrollment_status=ACTIVE` and `stake` present → eligible list
- Result statuses: `SUCCESS` (eligible list returned), `NOT_FOUND` (no eligible validators), `VIOLATION`, `BACKEND_ERROR`

**CC_SELECT_PROPOSER_V0** *(consensus_pos)*
- Step 1: `blockchain::CT_PURE_SELECT_PROPOSER_V0` — deterministic round-robin: `eligible_list[round_number % len(eligible_list)]` → proposer_id
- Result statuses: `SUCCESS`, `VIOLATION`

**CC_RECORD_CONSENSUS_ROUND_V0** *(consensus_pos)*
- Step 1: CT_PURE_ASSEMBLE_RECORD_V0 (REUSE) — fields: {round_id, proposer_id, block_id, outcome: PROPOSED, timestamp} → round_record
- Step 2: CS_APPENDONLY_JSONL_V0 — APPEND — CONSENSUS_ROUNDS store
- Result statuses: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`

**CC_SKIP_ROUND_V0** *(consensus_pos)*
- Step 1: CT_PURE_ASSEMBLE_RECORD_V0 (REUSE) — fields: {round_id, proposer_id, outcome: SKIPPED, timestamp} → skip_record
- Step 2: CS_APPENDONLY_JSONL_V0 — APPEND — CONSENSUS_ROUNDS store
- Step 3: CS_APPENDONLY_JSONL_V0 — APPEND — CONSENSUS_EVENTS store (event_type: EV_ROUND_SKIPPED_V0)
- Result statuses: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`
- *Note: no write to block stores — all writes remain within consensus_pos subdomain*

---

### blockchain::block Pipelines

**CC_FORM_BLOCK_V0** *(blockchain::block — new subdomain established this CR)*
- Step 1: CT_PURE_GENERATE_ID_V0 (REUSE, prefix: BLK) → block_id
- Step 2: CT_PURE_ASSEMBLE_RECORD_V0 (REUSE) — fields: {block_id, round_id, proposer_id, tx_ids, timestamp} → block_record
- Step 3: CS_MUTABLE_JSON_V0 — WRITE — BLOCKS store (key: block_id) → persist block
- Step 4: CS_APPENDONLY_JSONL_V0 — APPEND — BLOCK_EVENTS store (event_type: EV_BLOCK_PROPOSED_V0)
- Result statuses: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`
- *All writes are within blockchain::block subdomain stores*

---

### blockchain::transaction Pipelines

**CC_QUERY_PENDING_TRANSACTIONS_V0** *(blockchain::transaction — owned by transaction, triggered by this CR)*
- Step 1: CS_MUTABLE_JSON_V0 — LIST — TRANSACTION store (filter: status=pending) → tx_ids list
- Result statuses: `SUCCESS` (pending tx list returned), `EMPTY` (no pending transactions), `VIOLATION`, `BACKEND_ERROR`
- *Cross-subdomain read from consensus_pos WF; no write; store governed by blockchain::transaction*

---

## 7. Execution Topology — WF_REGISTER_VALIDATOR_V0 (Re-authored)

The existing WF topology is sound. Re-authoring corrects the pipeline provenance (GI gate previously skipped) and enriches the validator record with `stake` and `enrollment_status`.

```
IN_VALIDATOR_REGISTERED_V0       ← REPLACE: add stake, enrollment_status fields
    ACK  → CC_CHECK_ACTOR_EXISTS_V0
    NACK → EXIT

CC_CHECK_ACTOR_EXISTS_V0         ← REUSE
    SUCCESS       → CC_CHECK_VALIDATOR_EXISTS_V0
    NOT_FOUND     → EXIT
    VIOLATION     → EXIT
    BACKEND_ERROR → EXIT

CC_CHECK_VALIDATOR_EXISTS_V0     ← REUSE
    NOT_FOUND     → CC_WRITE_VALIDATOR_RECORD_V0
    SUCCESS       → EXIT             ← already registered
    VIOLATION     → EXIT
    BACKEND_ERROR → EXIT

CC_WRITE_VALIDATOR_RECORD_V0     ← REPLACE: validator_record includes stake + enrollment_status
    SUCCESS       → CC_APPEND_VALIDATOR_EVENT_V0
    VIOLATION     → EXIT
    BACKEND_ERROR → EXIT

CC_APPEND_VALIDATOR_EVENT_V0     ← REUSE
    SUCCESS       → EXIT
    VIOLATION     → EXIT
    BACKEND_ERROR → EXIT

EXIT
```

**Change from existing:** The WF topology is identical to the flawed version — the topology was correct. Only the pipeline provenance changes (GI gate now satisfied) and the validator record schema (enriched with stake + enrollment_status). No new CCs required for this WF.

---

## 8. STRUCTURE Extension — STRUCTURE_BLOCKCHAIN_STORAGE_V0

New entity stores to be added to the existing structure artifact, organized by subdomain governance.

**consensus_pos subdomain stores:**

| Store Name | Storage Type | Proposed Path | Used By |
| --- | --- | --- | --- |
| CONSENSUS_ROUNDS | CS_APPENDONLY_JSONL_V0 | `blockchain/consensus_pos/rounds/rounds.jsonl` | CC_RECORD_CONSENSUS_ROUND_V0, CC_SKIP_ROUND_V0 |
| CONSENSUS_EVENTS | CS_APPENDONLY_JSONL_V0 | `blockchain/consensus_pos/events/consensus_events.jsonl` | CC_SKIP_ROUND_V0 (EV_ROUND_SKIPPED_V0) |

**blockchain::block subdomain stores (new subdomain):**

| Store Name | Storage Type | Proposed Path | Used By |
| --- | --- | --- | --- |
| BLOCKS | CS_MUTABLE_JSON_V0 | `blockchain/block/blocks/blocks.json` | CC_FORM_BLOCK_V0 |
| BLOCK_EVENTS | CS_APPENDONLY_JSONL_V0 | `blockchain/block/events/block_events.jsonl` | CC_FORM_BLOCK_V0 (EV_BLOCK_PROPOSED_V0) |

Existing stores: VALIDATOR and VALIDATOR_EVENTS remain at their declared paths under `blockchain/consensus_pos/`. VALIDATOR store absorbs enrollment fields in the written record — no path or CS type change.

Cross-subdomain write rule: CC_SKIP_ROUND_V0 (consensus_pos) writes only to consensus_pos stores. CC_FORM_BLOCK_V0 (blockchain::block) writes only to block stores. No subdomain writes to another's stores.

---

## 9. CT_PURE_SELECT_PROPOSER_V0 — New Capability Transform

| Field | Value |
| --- | --- |
| Code | `blockchain::CT_PURE_SELECT_PROPOSER_V0` |
| Family | CT |
| Purity | ct_pure — no side effects |
| Operation | SELECT_PROPOSER |
| Inputs | `eligible_validators` (array of validator records), `round_number` (integer) |
| Output | `proposer_id` (string) |
| Algorithm | Round-robin: `eligible_validators[round_number % len(eligible_validators)].actor_id` |
| Failure | VIOLATION if `eligible_validators` empty or `round_number` negative |

This CT is the sole artifact carrying the proposer selection algorithm. Changing the algorithm in a future CR requires only a new CT version — all CCs, WFs, and WF topology remain unchanged.

---

## 10. IN_BLOCK_PROPOSED_V0 — Intent Schema

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| round_number | integer | YES | Monotonically increasing round identifier |
| triggered_by | string | NO | External trigger reference (test script or future scheduler) |

Outcomes: `ACK` (payload valid, proceed), `NACK` (payload invalid, reject)

---

## 11. Artifact Summary

Artifact count by action type, for Stage 7 input.

| Action | Count | Notes |
| --- | --- | --- |
| REPLACE | 3 | IN_VALIDATOR_REGISTERED_V0, CC_WRITE_VALIDATOR_RECORD_V0, WF_REGISTER_VALIDATOR_V0 |
| EXTEND | 1 | STRUCTURE_BLOCKCHAIN_STORAGE_V0 — adds 4 new stores across 2 subdomains |
| NEW (consensus_pos) | 9 | WF, IN, RB, 4×CC, CT, EV |
| NEW (blockchain::block) | 2 | CC_FORM_BLOCK_V0, EV_BLOCK_PROPOSED_V0 |
| NEW (blockchain::transaction) | 1 | CC_QUERY_PENDING_TRANSACTIONS_V0 |
| **Total** | **16** | |

Build dependency order is the output of Protocol Stage 7 — Authoring Plan. The artifact inventory, WF topology, CC pipeline declarations, CT specs, and storage design above are the complete output of Stage 6b.

---

## 12. Governance Decision Gate

**Presenting for Analyst approval:**

1. Enrollment store decision: VALIDATOR store enriched with `stake` and `enrollment_status` — no separate enrollment store
2. Proposer selection: round-robin (`round_number % pool_size`) — deterministic, single CT artifact carries the algorithm
3. Consensus loop interval and transaction submission interval: external test script, not PGS artifacts
4. Block record schema: `{block_id, round_id, proposer_id, tx_ids, timestamp}` — TX data not copied, only referenced by ID
5. WF_PROPOSE_BLOCK_V0 topology: two clean paths (PROPOSE / SKIP) — cross-subdomain calls to blockchain::transaction (query) and blockchain::block (form); no convergence, no conditional branching in CCs
6. `CC_QUERY_PENDING_TRANSACTIONS_V0` owned by `blockchain::transaction` — consensus_pos is caller, not owner; authored in this CR as the establishing artifact for that gap
7. `CC_FORM_BLOCK_V0` and block events owned by `blockchain::block` — this CR establishes the block subdomain as a first-class governed boundary
8. `CC_SKIP_ROUND_V0` writes only to consensus_pos stores (CONSENSUS_ROUNDS + CONSENSUS_EVENTS) — no cross-subdomain write
9. `CT_PURE_ASSEMBLE_RECORD_V0` reused for block and round record assembly — no new CT needed for these
10. New CT needed: only `CT_PURE_SELECT_PROPOSER_V0` — algorithm is the only genuinely new pure computation
11. Four new entity stores across two subdomains: consensus_pos (CONSENSUS_ROUNDS, CONSENSUS_EVENTS); blockchain::block (BLOCKS, BLOCK_EVENTS)
12. 16 authoring actions total: 3 REPLACE, 1 EXTEND, 12 NEW (split: 9 consensus_pos, 2 block, 1 transaction)

*Analyst approval of this document gates entry into Protocol Stage 7 — Authoring Plan.*

---

## Pipeline Provenance

| Stage | Output | Status |
| --- | --- | --- |
| Stage 0 — Classification | change_request_subdomain | COMPLETE |
| Stage 1 — Input Elicitation | Problem + Outcome + Known Facts | COMPLETE |
| Stage 2 — Domain Model Discovery | Actors, Entities, Resources, Events, Relationships | COMPLETE |
| Stage 3 — Analysis Loop | Capability Graph, Dependency Graph, Constraints, Gap Register | COMPLETE — SATURATED |
| Stage 4 — Business Model | 4_business_model_consensus_pos_v0.md | COMPLETE |
| Stage 4b — Authoring Scope | IN/FUTURE CR boundary | COMPLETE — APPROVED |
| Stage 5 — Business Intent | 5_business_intent_consensus_pos_v0.md | COMPLETE |
| Stage 6 — Governance Intent | 6_governance_intent_consensus_pos_v0.md | COMPLETE — APPROVED |
| Stage 6b — Design Intent | This document | COMPLETE — APPROVED WITH PATCHES |
| Stage 7 — Authoring Plan | Pending | — |

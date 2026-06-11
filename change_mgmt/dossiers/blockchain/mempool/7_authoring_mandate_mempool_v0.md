# Authoring Mandate: blockchain / mempool
**Domain:** blockchain
**Subdomain:** mempool
**Version:** V0
**Status:** APPROVED
**Pipeline Stage:** Stage 7 — Authoring Mandate
**Produced by:** v0.5.0 SDLC authoring pipeline
**Input:** 6b_design_intent_mempool_v0.md (Stage 6b — APPROVED)

---

## Overview

This CR produces **8 authoring actions** across three subdomains:

| Subdomain | Actions | Breakdown |
|-----------|---------|-----------|
| `blockchain::mempool` | 3 | 3 NEW |
| `blockchain::consensus_pos` | 2 | 2 REPLACE (WF + RB) |
| `blockchain::transaction` | 2 | 2 REPLACE (WF + RB) |
| `blockchain` (cross-subdomain structure) | 1 | 1 EXTEND |
| **Total** | **8** | |

**REUSE artifacts (no changes):** `CC_QUERY_ELIGIBLE_VALIDATORS_V0`, `CC_SELECT_PROPOSER_V0`, `CC_FORM_BLOCK_V0`, `CC_RECORD_CONSENSUS_ROUND_V0`, `CC_SKIP_ROUND_V0`, `IN_BLOCK_PROPOSED_V0`, `IN_TRANSACTION_SUBMITTED_V0`, `CS_MUTABLE_JSON_V0`, `CS_REGISTRY_V0`, `CS_APPENDONLY_JSONL_V0`, `CT_PURE_GENERATE_ID_V0`, `CT_PURE_FILTER_RECORDS_V0`.

---

## Build Dependency Order

### Wave 1 — Foundation (no dependencies)

**Step 1**
```
Artifact:    blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0
Action:      EXTEND
Subdomain:   cross-subdomain
Depends on:  nothing
PPS status:  EXISTS — extend with 2 new store entries
```
Add two new store entries to the existing STRUCTURE artifact:

- `MEMPOOL` — `CS_MUTABLE_JSON_V0`, path: `blockchain/mempool/state/mempool.json`
  Purpose: Ephemeral staging buffer for pending transactions; keyed by tx_id; entries deleted on drain
- `MEMPOOL_INDEX` — `CS_REGISTRY_V0`, path: `blockchain/mempool/registry/mempool_index.json`
  Purpose: Deduplication registry enforcing tx_id and tx_hash uniqueness before write

No existing store entries change. This extension is purely additive.

---

### Wave 2 — New Mempool CCs (parallel, after Step 1)

**Step 2**
```
Artifact:    blockchain::CC_WRITE_MEMPOOL_TX_V0
Action:      NEW
Subdomain:   mempool
Depends on:  Step 1 (STRUCTURE — MEMPOOL + MEMPOOL_INDEX stores)
PPS status:  NOT PRESENT — must author
```
4-step pipeline — all operations within `blockchain::mempool` stores:

| Step | Type | Artifact | Operation | Inputs | Output |
|------|------|----------|-----------|--------|--------|
| generate_mempool_key | CT | CT_PURE_GENERATE_ID_V0 | — | `tx_id` | `mempool_key` |
| check_tx_id_duplicate | CS | CS_REGISTRY_V0 | EXISTS | `mempool_key` → MEMPOOL_INDEX | `tx_id_exists`; route `ALREADY_EXISTS` if true |
| write_pending_tx | CS | CS_MUTABLE_JSON_V0 | WRITE | full input payload + `arrived_at` | — |
| register_tx_hash | CS | CS_REGISTRY_V0 | REGISTER | `tx_hash` → MEMPOOL_INDEX | route `ALREADY_EXISTS` if duplicate hash |

Inputs: `tx_id` (string, required), `tx_hash` (string, required), `tx_type` (string, required), `actor_id` (string, optional), `from_wallet_id` (string, optional), `to_wallet_id` (string, optional), `amount` (number, required), `created_at` (string, required).
Outputs: `result_status` (string).
Routing Outcomes: `SUCCESS`, `ALREADY_EXISTS`, `VIOLATION`, `BACKEND_ERROR`.

---

**Step 3**
```
Artifact:    blockchain::CC_QUERY_MEMPOOL_TXS_V0
Action:      NEW
Subdomain:   mempool
Depends on:  Step 1 (STRUCTURE — MEMPOOL store)
PPS status:  NOT PRESENT — must author
```
2-step pipeline — reads from MEMPOOL store only:

| Step | Type | Artifact | Operation | Inputs | Output |
|------|------|----------|-----------|--------|--------|
| list_mempool_entries | CS | CS_MUTABLE_JSON_V0 | LIST | MEMPOOL store | `entries` (all records) |
| assert_mempool_non_empty | CT | CT_PURE_FILTER_RECORDS_V0 | — | `entries` | `tx_ids` ordered by `created_at`; `VIOLATION` if empty |

Inputs: none.
Outputs: `tx_ids` (array of string).
Routing Outcomes: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`.

Note: `VIOLATION` on empty mempool is the governed signal — calling workflow routes to `CC_SKIP_ROUND_V0`. This replaces the `VIOLATION` that `CC_QUERY_PENDING_TRANSACTIONS_V0` currently returns for this case.

---

**Step 4**
```
Artifact:    blockchain::CC_DRAIN_MEMPOOL_V0
Action:      NEW
Subdomain:   mempool
Depends on:  Step 1 (STRUCTURE — MEMPOOL store)
PPS status:  NOT PRESENT — must author
```
1-step pipeline — DELETE-only from MEMPOOL store:

| Step | Type | Artifact | Operation | Inputs | Output |
|------|------|----------|-----------|--------|--------|
| delete_consumed_txs | CS | CS_MUTABLE_JSON_V0 | DELETE (per tx_id in list) | `tx_ids` list | `drained_count` (integer) |

Idempotent — NOT_FOUND on any tx_id is treated as already drained (not an error).
Inputs: `tx_ids` (array of string, required), `block_id` (string, required).
Outputs: `drained_count` (integer).
Routing Outcomes: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`.

---

### Wave 3 — Updated Workflows (parallel, after respective deps)

**Step 5**
```
Artifact:    blockchain::WF_SUBMIT_TRANSACTION_V0
Action:      REPLACE
Subdomain:   transaction
Depends on:  Step 2 (CC_WRITE_MEMPOOL_TX_V0)
PPS status:  EXISTS — replace; single node substitution
```
One change only: replace the `CC_PERSIST_MEMPOOL_TX_V0` node with `CC_WRITE_MEMPOOL_TX_V0`. All other nodes, routing, input bindings, and admission are unchanged.

| Aspect | Current | Updated |
|--------|---------|---------|
| Persist node code | `CC_PERSIST_MEMPOOL_TX_V0` | `CC_WRITE_MEMPOOL_TX_V0` |
| Persist node fqdn_id | `blockchain::CC_PERSIST_MEMPOOL_TX_V0` | `blockchain::CC_WRITE_MEMPOOL_TX_V0` |
| Routing from persist node | `SUCCESS → CC_APPEND_TX_EVENT_V0`, `ALREADY_EXISTS → EXIT_DUPLICATE`, `VIOLATION → EXIT`, `BACKEND_ERROR → EXIT` | Unchanged |
| All other nodes | Unchanged | Unchanged |

Input fields passed to the persist node: `tx_id`, `tx_hash`, `tx_type`, `actor_id`, `from_wallet_id` (mapped from `from_address`), `to_wallet_id` (mapped from `to_address`), `amount` (mapped from `value`), `created_at` (timestamp). ETH-specific fields (`chain_id`, `gas_limit`, `nonce`, `signature`, etc.) are carried through as metadata on the MEMPOOL record.

Declare `subdomain: transaction` (preserve existing value).

---

**Step 6**
```
Artifact:    blockchain::WF_PROPOSE_BLOCK_V0
Action:      REPLACE
Subdomain:   consensus_pos
Depends on:  Steps 3, 4 (CC_QUERY_MEMPOOL_TXS_V0, CC_DRAIN_MEMPOOL_V0)
PPS status:  EXISTS — replace; two changes: node substitution + drain node insertion
```
Two changes:

**Change 1** — Replace `CC_QUERY_PENDING_TRANSACTIONS_V0` node with `CC_QUERY_MEMPOOL_TXS_V0`:
- Same inputs (`{}`)
- Same routing: `SUCCESS → CC_FORM_BLOCK_V0`, `VIOLATION → CC_SKIP_ROUND_V0`, `BACKEND_ERROR → EXIT`

**Change 2** — Insert `CC_DRAIN_MEMPOOL_V0` between `CC_FORM_BLOCK_V0` and `CC_RECORD_CONSENSUS_ROUND_V0`:
- `CC_FORM_BLOCK_V0` SUCCESS now routes to `CC_DRAIN_MEMPOOL_V0` (was `CC_RECORD_CONSENSUS_ROUND_V0`)
- New `CC_DRAIN_MEMPOOL_V0` node:
  ```
  inputs:
    tx_ids:   $.results.CC_QUERY_MEMPOOL_TXS_V0.tx_ids
    block_id: $.results.CC_FORM_BLOCK_V0.block_id
  next:
    SUCCESS:       CC_RECORD_CONSENSUS_ROUND_V0
    VIOLATION:     EXIT
    BACKEND_ERROR: EXIT
  ```

All other nodes (`IN_BLOCK_PROPOSED_V0`, `CC_QUERY_ELIGIBLE_VALIDATORS_V0`, `CC_SELECT_PROPOSER_V0`, `CC_FORM_BLOCK_V0`, `CC_RECORD_CONSENSUS_ROUND_V0`, `CC_SKIP_ROUND_V0`, `EXIT`) are unchanged. Declare `subdomain: consensus_pos` (preserve existing value).

---

### Wave 4 — Updated Runtime Bindings (parallel, after Wave 3)

**Step 7**
```
Artifact:    blockchain::RB_SUBMIT_TRANSACTION_V0
Action:      REPLACE
Subdomain:   transaction
Depends on:  Step 5 (WF_SUBMIT_TRANSACTION_V0)
PPS status:  EXISTS — replace; update CS_REGISTRY_V0 policy scope
```
`CC_WRITE_MEMPOOL_TX_V0` uses `CS_REGISTRY_V0` against the MEMPOOL_INDEX path (`blockchain/mempool/registry/mempool_index.json`). The current RB declares `CS_REGISTRY_V0` with a single policy path pointing to the identity actor registry. The replacement must support both the identity registry and the mempool index.

Author decision: either declare two `CS_REGISTRY_V0` binding entries (if the runtime supports multiple policy path entries per CS type) or move to a path-agnostic `policy: {}` and rely on STRUCTURE_BLOCKCHAIN_STORAGE_V0 for store resolution. `CS_MUTABLE_JSON_V0` and `CS_APPENDONLY_JSONL_V0` bindings are unchanged.

---

**Step 8**
```
Artifact:    blockchain::RB_PROPOSE_BLOCK_V0
Action:      REPLACE
Subdomain:   consensus_pos
Depends on:  Step 6 (WF_PROPOSE_BLOCK_V0)
PPS status:  EXISTS — replace; update scope description; bindings unchanged
```
`CC_QUERY_MEMPOOL_TXS_V0` and `CC_DRAIN_MEMPOOL_V0` both use only `CS_MUTABLE_JSON_V0` (LIST and DELETE). `CS_MUTABLE_JSON_V0` is already declared in this RB with `policy: {}`. No new CS type binding needed. Update the scope description to include MEMPOOL store as a governed store in this RB's scope. Bindings section is functionally unchanged.

---

## 2. Critical Path

**Steps: 1 → 3/4 → 6 → 8** (4 sequential steps)

Parallel slots available at waves 2 and 3 reduce calendar time. Minimum sequential depth is 4 steps.

---

## 3. Artifact Summary

| Count | Action | Description |
|-------|--------|-------------|
| 3 | NEW | CC_WRITE_MEMPOOL_TX_V0, CC_QUERY_MEMPOOL_TXS_V0, CC_DRAIN_MEMPOOL_V0 |
| 4 | REPLACE | WF_SUBMIT_TRANSACTION_V0, WF_PROPOSE_BLOCK_V0, RB_SUBMIT_TRANSACTION_V0, RB_PROPOSE_BLOCK_V0 |
| 1 | EXTEND | STRUCTURE_BLOCKCHAIN_STORAGE_V0 |
| **8** | **Total** | |

---

## 4. Subdomain Field Declarations

| Artifact Code | Subdomain Field Value | Module Path |
|---------------|-----------------------|-------------|
| CC_WRITE_MEMPOOL_TX_V0 | `mempool` | `pgs_blockchain.registry.mempool.capability_contracts` |
| CC_QUERY_MEMPOOL_TXS_V0 | `mempool` | `pgs_blockchain.registry.mempool.capability_contracts` |
| CC_DRAIN_MEMPOOL_V0 | `mempool` | `pgs_blockchain.registry.mempool.capability_contracts` |
| WF_SUBMIT_TRANSACTION_V0 | `transaction` | `pgs_blockchain.registry.transaction.workflows` (preserve) |
| WF_PROPOSE_BLOCK_V0 | `consensus_pos` | `pgs_blockchain.registry.consensus_pos.workflows` (preserve) |
| RB_SUBMIT_TRANSACTION_V0 | `transaction` | `pgs_blockchain.registry.transaction.runtime_bindings` (preserve) |
| RB_PROPOSE_BLOCK_V0 | `consensus_pos` | `pgs_blockchain.registry.consensus_pos.runtime_bindings` (preserve) |

*Subdomain field governs trace routing and data store path resolution.*

---

## 5. Cross-Subdomain Dependency Notes

| Call | Direction | Permitted | Notes |
|------|-----------|-----------|-------|
| WF_SUBMIT_TRANSACTION_V0 → CC_WRITE_MEMPOOL_TX_V0 | `blockchain::transaction` calls `blockchain::mempool` | YES | Cross-subdomain CC call at WF level; WF does not own MEMPOOL store |
| WF_PROPOSE_BLOCK_V0 → CC_QUERY_MEMPOOL_TXS_V0 | `blockchain::consensus_pos` calls `blockchain::mempool` | YES | Cross-subdomain CC call; WF does not own MEMPOOL store |
| WF_PROPOSE_BLOCK_V0 → CC_DRAIN_MEMPOOL_V0 | `blockchain::consensus_pos` calls `blockchain::mempool` | YES | Cross-subdomain CC call; drain is DELETE from mempool-owned store only |
| CC_DRAIN_MEMPOOL_V0 → TRANSACTION store | Any subdomain | FORBIDDEN | Drain must not write to TRANSACTION store; DELETE-only from MEMPOOL |

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 0 — Classification | 1_change_request_mempool_v0.md | COMPLETE |
| Stage 1 — Input Elicitation | 1_input_elicitation_mempool_v0.md | COMPLETE |
| Stage 2 — Domain Model Discovery | 2_domain_model_mempool_v0.md | COMPLETE |
| Stage 3 — Analysis Loop | 3_analysis_loop_mempool_v0.md | COMPLETE — SATURATED |
| Stage 4 — Business Model | 4_business_model_mempool_v0.md | COMPLETE — APPROVED |
| Stage 5 — Business Intent | 5_business_intent_mempool_v0.md | COMPLETE — APPROVED |
| Stage 6 — Governance Intent | 6_governance_intent_mempool_v0.md | COMPLETE — APPROVED |
| Stage 6b — Design Intent | 6b_design_intent_mempool_v0.md | COMPLETE — APPROVED |
| Stage 7 — Authoring Mandate | This document | APPROVED |
| Stage 8 — Authoring Manifest | 8_authoring_manifest_mempool_v0.md | PENDING |

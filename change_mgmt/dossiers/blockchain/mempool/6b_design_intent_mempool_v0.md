# Design Intent: blockchain / mempool
**Domain:** blockchain
**Subdomain:** mempool
**Version:** V0
**Status:** APPROVED
**Pipeline Stage:** Stage 6b — Design Intent

---

## Section 1 — Store Binding

| Store Code | Path | CS Implementation | Operations Used |
|------------|------|-------------------|-----------------|
| MEMPOOL | `{{module_data_root}}/blockchain/mempool/state/mempool.json` | CS_MUTABLE_JSON_V0 | WRITE, LIST, DELETE |
| MEMPOOL_INDEX | `{{module_data_root}}/blockchain/mempool/registry/mempool_index.json` | CS_REGISTRY_V0 | REGISTER, EXISTS |

---

## Section 2 — CC_WRITE_MEMPOOL_TX_V0 Pipeline

| Step | Type | Artifact | Operation | Inputs | Output |
|------|------|----------|-----------|--------|--------|
| generate_mempool_key | CT | CT_PURE_GENERATE_ID_V0 | — | `tx_id` | `mempool_key` |
| check_tx_id_duplicate | CS | CS_REGISTRY_V0 | EXISTS | `mempool_key` → MEMPOOL_INDEX | `tx_id_exists` → route ALREADY_EXISTS if true |
| write_pending_tx | CS | CS_MUTABLE_JSON_V0 | WRITE | full payload + `arrived_at` | — |
| register_tx_hash | CS | CS_REGISTRY_V0 | REGISTER | `tx_hash` → MEMPOOL_INDEX | route ALREADY_EXISTS if duplicate hash |

**Routing Outcomes:** `SUCCESS`, `ALREADY_EXISTS`, `VIOLATION`, `BACKEND_ERROR`

---

## Section 3 — CC_QUERY_MEMPOOL_TXS_V0 Pipeline

| Step | Type | Artifact | Operation | Inputs | Output |
|------|------|----------|-----------|--------|--------|
| list_mempool_entries | CS | CS_MUTABLE_JSON_V0 | LIST | MEMPOOL store | `entries` (all records) |
| assert_mempool_non_empty | CT | CT_PURE_FILTER_RECORDS_V0 | — | `entries` | `tx_ids` (ordered by `created_at`); VIOLATION if empty |

**Routing Outcomes:** `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`

---

## Section 4 — CC_DRAIN_MEMPOOL_V0 Pipeline

| Step | Type | Artifact | Operation | Inputs | Output |
|------|------|----------|-----------|--------|--------|
| delete_consumed_txs | CS | CS_MUTABLE_JSON_V0 | DELETE (loop) | `tx_ids` list | `drained_count`; NOT_FOUND treated as already drained (idempotent) |

**Routing Outcomes:** `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`

---

## Section 5 — WF_PROPOSE_BLOCK_V0 Updated Topology

| Node | Type | Routing |
|------|------|---------|
| IN_BLOCK_PROPOSED_V0 | IN | ACK → CC_QUERY_ELIGIBLE_VALIDATORS_V0, NACK → EXIT |
| CC_QUERY_ELIGIBLE_VALIDATORS_V0 | CC | SUCCESS → CC_SELECT_PROPOSER_V0, VIOLATION → EXIT, BACKEND_ERROR → EXIT |
| CC_SELECT_PROPOSER_V0 | CC | SUCCESS → CC_QUERY_MEMPOOL_TXS_V0, VIOLATION → EXIT |
| CC_QUERY_MEMPOOL_TXS_V0 | CC | SUCCESS → CC_FORM_BLOCK_V0, VIOLATION → CC_SKIP_ROUND_V0, BACKEND_ERROR → EXIT |
| CC_FORM_BLOCK_V0 | CC | SUCCESS → CC_DRAIN_MEMPOOL_V0, VIOLATION → EXIT, BACKEND_ERROR → EXIT |
| CC_DRAIN_MEMPOOL_V0 | CC | SUCCESS → CC_RECORD_CONSENSUS_ROUND_V0, VIOLATION → EXIT, BACKEND_ERROR → EXIT |
| CC_RECORD_CONSENSUS_ROUND_V0 | CC | SUCCESS → EXIT_SUCCESS, VIOLATION → EXIT, BACKEND_ERROR → EXIT |
| CC_SKIP_ROUND_V0 | CC | SUCCESS → EXIT, VIOLATION → EXIT, BACKEND_ERROR → EXIT |
| EXIT_SUCCESS | EXIT | — |
| EXIT | EXIT | — |

**Change from current:** Single new node `CC_DRAIN_MEMPOOL_V0` inserted between `CC_FORM_BLOCK_V0` and `CC_RECORD_CONSENSUS_ROUND_V0`.

---

## Section 6 — WF_SUBMIT_TRANSACTION_V0 Updated Persist Step

The persist step currently calls `CC_PERSIST_MEMPOOL_TX_V0` which writes to the TRANSACTION store. The updated version replaces that step call with `CC_WRITE_MEMPOOL_TX_V0`.

| Aspect | Current | Updated |
|--------|---------|---------|
| Persist CC called | CC_PERSIST_MEMPOOL_TX_V0 | CC_WRITE_MEMPOOL_TX_V0 |
| Store target | TRANSACTION store (`blockchain/transaction/state/transactions.json`) | MEMPOOL store (`blockchain/mempool/state/mempool.json`) |
| Rest of workflow | Unchanged | Unchanged |

---

## Section 7 — STRUCTURE_BLOCKCHAIN_STORAGE_V0 Addition

New entries to be added to the storage structure manifest:

```
Store Code:     MEMPOOL
Subdomain:      mempool
CS Type:        CS_MUTABLE_JSON_V0
Path:           blockchain/mempool/state/mempool.json
Purpose:        Ephemeral staging buffer for pending transactions; keyed by tx_id; deleted on drain

Store Code:     MEMPOOL_INDEX
Subdomain:      mempool
CS Type:        CS_REGISTRY_V0
Path:           blockchain/mempool/registry/mempool_index.json
Purpose:        Deduplication registry for tx_id and tx_hash uniqueness enforcement
```

---

## Section 8 — Design Intent Gate

| Decision Point | Outcome |
|----------------|---------|
| All CC pipelines are fully wired with CS/CT artifacts | CONFIRMED |
| No new CS or CT primitives required | CONFIRMED |
| Store paths are under `blockchain/mempool/` (subdomain isolation) | CONFIRMED |
| WF topology changes are minimal and localized | CONFIRMED — one new node in WF_PROPOSE_BLOCK_V0; one step re-wire in WF_SUBMIT_TRANSACTION_V0 |
| STRUCTURE additions are additive — no existing entries modified | CONFIRMED |
| Design Intent gate | PASS — proceed to Stage 7 (Authoring Mandate) |

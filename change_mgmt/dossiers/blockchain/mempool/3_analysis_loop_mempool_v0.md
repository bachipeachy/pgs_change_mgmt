# Stage 3 — Analysis Loop: blockchain / mempool
**Stage:** 3 — Analysis Loop
**CR:** 1_change_request_mempool_v0.md
**Iterations:** 1 (saturated)
**Status:** COMPLETE
**Feeds:** Stage 4 — Business Model

---

## Iteration 1

### Q1 — Does drain belong inside CC_FORM_BLOCK_V0 or as a separate CC in WF_PROPOSE_BLOCK_V0?

**Finding:** Drain must be a separate mempool-owned capability called after block formation in WF_PROPOSE_BLOCK_V0.

*CC_FORM_BLOCK_V0 pipeline (confirmed from snapshot): generates block_id, assembles block record, writes to BLOCKS store, appends to BLOCK_EVENTS. It is a block subdomain concern — it has no interaction with any transaction or mempool store. WF_PROPOSE_BLOCK_V0 topology: CC_QUERY_PENDING_TRANSACTIONS_V0 → CC_FORM_BLOCK_V0 → CC_RECORD_CONSENSUS_ROUND_V0. There is no drain step anywhere in this topology.*

**Resolution:** A new drain capability owned by the mempool subdomain must be inserted into WF_PROPOSE_BLOCK_V0 after CC_FORM_BLOCK_V0. CC_FORM_BLOCK_V0 is unchanged — it is a block concern. WF_PROPOSE_BLOCK_V0 must be versioned to add the drain node. This is the `blockchain::consensus_pos` DEPENDENCY GAP already declared in the CR scope.

**Answer:** Drain is a new mempool-owned capability; WF_PROPOSE_BLOCK_V0 calls it after block formation.

---

### Q2 — Does the mempool require its own deduplication registry or can it reuse the transaction registry?

**Finding:** The mempool requires its own store entry in the storage structure; the registry capability itself is reusable.

*STRUCTURE_BLOCKCHAIN_STORAGE_V0 (confirmed from snapshot): defines TRANSACTION store at `blockchain/transaction/state/transactions.json`. No MEMPOOL store entry exists. No MEMPOOL_INDEX registry entry exists. The TRANSACTION store path is under the `transaction` subdomain path — a mempool subdomain cannot share this path without violating subdomain isolation rules declared in the STRUCTURE ("Each entity type has dedicated storage"). CS_REGISTRY_V0 is a generic capability — it is reused across all subdomains (actor registry, wallet registry, etc.) with different path policies.*

**Resolution:** A new MEMPOOL store entry must be added to STRUCTURE_BLOCKCHAIN_STORAGE_V0 at `blockchain/mempool/state/mempool.json`. CS_REGISTRY_V0 is reused as the deduplication mechanism, pointed at the new MEMPOOL key space. No sharing with the transaction registry.

**Answer:** New MEMPOOL store in STRUCTURE required; CS_REGISTRY_V0 reused with new path policy.

---

### Q3 — When drained, does a transaction record move to the TRANSACTION store, or is that a future CR?

**Finding:** Drain is DELETE-only from the MEMPOOL store. Writing committed records to the TRANSACTION store is out of scope for this CR.

*CS_MUTABLE_JSON_V0 (confirmed from snapshot): supports DELETE operation — idempotent, takes `key`, returns SUCCESS / NOT_FOUND / VIOLATION / BACKEND_ERROR. This is sufficient for drain. The CR explicitly deferred TRANSACTION store status update lifecycle (PENDING → COMMITTED, block association) to a future revisit.*

**Resolution:** Drain deletes consumed tx_ids from the MEMPOOL store using CS_MUTABLE_JSON_V0 DELETE. No write to TRANSACTION store in this CR. The TRANSACTION store is untouched by this CR — its purpose as committed transaction record remains for a future CR.

**Answer:** Drain = DELETE from MEMPOOL store only. TRANSACTION store write is a future CR.

---

## Saturation Assessment

| Criterion | Status | Evidence |
|-----------|--------|----------|
| No unresolved CRITICAL gaps | SATISFIED | All 4 CRITICAL gaps from Stage 2 are resolved: MEMPOOL store (new STRUCTURE entry), drain (new CC), query wrong store (new mempool-owned CC), persist wrong store (new mempool-owned CC) |
| No open analyst questions | SATISFIED | Q1, Q2, Q3 resolved. No new questions surfaced. |
| No dependency expansion in last pass | SATISFIED | All cross-subdomain dependencies (consensus_pos, transaction) were already declared in CR scope. No new subdomains discovered. |

**Saturation achieved in 1 iteration.**

---

## Consolidated Findings

### What Already Exists (fully reusable)

| Capability | Status | Reuse |
|------------|--------|-------|
| CS_MUTABLE_JSON_V0 | EXISTS | REUSE — WRITE (mempool entry), LIST (query), DELETE (drain) |
| CS_REGISTRY_V0 | EXISTS | REUSE — deduplication for mempool entries, new path policy |
| CT_PURE_FILTER_RECORDS_V0 | EXISTS | REUSE — filter pending records in mempool query |
| CT_PURE_GENERATE_ID_V0 | EXISTS | REUSE — key generation in mempool persist |
| CS_APPENDONLY_JSONL_V0 | EXISTS | REUSE — transaction event log (TRANSACTION_EVENTS) unchanged |

### What Must Be Authored (new capabilities)

| Capability | Why New |
|------------|---------|
| MEMPOOL store entry in STRUCTURE_BLOCKCHAIN_STORAGE_V0 | No mempool store exists; subdomain isolation rules forbid sharing transaction path |
| Mempool persist capability (mempool-owned) | CC_PERSIST_MEMPOOL_TX_V0 writes to wrong store; mempool subdomain must own its write path |
| Mempool query capability (mempool-owned) | CC_QUERY_PENDING_TRANSACTIONS_V0 reads wrong store; must be re-owned by mempool subdomain |
| Mempool drain capability | No drain exists anywhere in the snapshot; deletes consumed tx_ids from MEMPOOL store |
| Updated WF_PROPOSE_BLOCK_V0 | Add drain node after block formation; current topology has no drain step |
| Updated WF_SUBMIT_TRANSACTION_V0 | Redirect persist step to mempool-owned capability |

### Subdomain Placement Decision

**NEW subdomain — `blockchain::mempool`**

The mempool lifecycle (stage → query → drain) is governed by a separate ownership boundary from the transaction subdomain (which owns submission) and the consensus_pos subdomain (which owns proposer selection and round recording). The MEMPOOL store must live at `blockchain/mempool/` per isolation rules. The drain operation is triggered by consensus but executed against a store owned by mempool — this cross-subdomain call pattern is already established in the PGS architecture (consensus calls block, block calls mempool). A new subdomain is required.

---

## Inputs to Stage 4 — Business Model

1. **New subdomain declared:** `blockchain::mempool` owns the pending transaction lifecycle — staging, query, drain.
2. **New store required:** MEMPOOL store at `blockchain/mempool/state/mempool.json` — mutable, key-addressable, separate from TRANSACTION store.
3. **Drain is part of block formation:** WF_PROPOSE_BLOCK_V0 calls the drain capability after CC_FORM_BLOCK_V0; drain deletes consumed tx_ids from MEMPOOL store only.
4. **Transaction store untouched:** TRANSACTION store purpose and type unchanged; committed record lifecycle is a future CR.
5. **Three cross-subdomain touchpoints:** transaction (persist redirect), consensus_pos (workflow topology update), structure (new store entry).
6. **All required CS/CT capabilities exist:** No new CS or CT primitives needed — CS_MUTABLE_JSON_V0 DELETE covers drain; CS_REGISTRY_V0 covers deduplication.

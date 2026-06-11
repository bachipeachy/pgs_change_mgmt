# Stage 2 — Domain Model Discovery: blockchain / mempool
**Stage:** 2 — Domain Model Discovery
**CR:** 1_change_request_mempool_v0.md
**Status:** COMPLETE
**Feeds:** Stage 3 — Analysis Loop

---

## 1. Business Entities

### Pending Transaction
A transaction that has been submitted and validated but not yet included in a block. Lives in the mempool staging buffer from submission until a proposer drains it.

| Attribute | Description |
|-----------|-------------|
| tx_id | Unique transaction identifier |
| tx_hash | Hash of the signed transaction bytes |
| tx_type | Type of transaction (TRANSFER, MINT, BURN, etc.) |
| actor_id | Submitting actor |
| from_wallet_id | Source wallet (null for MINT, REWARD) |
| to_wallet_id | Destination wallet (null for BURN) |
| amount | Transaction amount |
| status | Always PENDING while in mempool |
| created_at | Submission timestamp — determines arrival order |

### Mempool
The single global staging buffer holding all pending transactions in arrival order. Accepts entries on submission; releases them when a proposer drains.

| Attribute | Description |
|-----------|-------------|
| entries | All pending transactions, ordered by created_at |
| size | Count of pending transactions at any point |

### Transaction Submitter
An actor who submits a transaction for inclusion in a future block. Has no further role after submission.

### Block Proposer
A validator selected by consensus to propose a block for a given slot. Reads pending transactions from the mempool and drains them as part of block formation.

---

## 2. Business Processes

### Process 1 — Transaction Entry
A submitter sends a transaction. The full submission pipeline validates, builds, signs, hashes, and stages it into the mempool.

1. Transaction is received and validated (structure + policy)
2. Transaction is built, signed, and hashed
3. Transaction is written to the mempool staging buffer with status PENDING
4. Transaction submission event is appended to the event log

### Process 2 — Pending Transaction Query
At block proposal time, the proposer reads all pending transactions from the mempool.

1. Proposer is selected for the slot
2. Mempool is read in full (global buffer, arrival order)
3. If no pending transactions exist, the round is skipped
4. If pending transactions exist, they are passed to block formation

### Process 3 — Mempool Drain
After a block is formed, consumed transactions are removed from the mempool. Drain is part of block formation — same operation, not a separate step.

1. Block formation receives the list of included transaction IDs
2. Each included transaction is deleted from the mempool staging buffer
3. Mempool no longer holds those transactions

---

## 3. PPS Baseline — What Already Exists

### CC_PERSIST_MEMPOOL_TX_V0
Persists a signed transaction and registers it in a deduplication index. Currently writes to the TRANSACTION store (wrong store) via a WRITE step. Also appends to TRANSACTION_EVENTS (correct — event log is separate).

**Fit for this CR:** Partial — correct shape and registration logic; store target is wrong. Needs a new version that writes to MEMPOOL store instead of TRANSACTION store.

### CC_QUERY_PENDING_TRANSACTIONS_V0
Lists all records from the TRANSACTION store and filters for status = PENDING. Returns tx_ids for the proposer.

**Fit for this CR:** Partial — correct query shape; wrong store. Needs redirecting to MEMPOOL store. Filter-by-status logic is reusable (PENDING entries in mempool are all entries — no other status exists in the buffer).

### WF_PROPOSE_BLOCK_V0
Governs the full block proposal round: query eligible validators → select proposer → query pending transactions → form block → record round. No drain step exists after block formation.

**Fit for this CR:** Partial — topology is correct but incomplete. Missing a drain step after CC_FORM_BLOCK_V0.

### CC_FORM_BLOCK_V0
Accepts tx_ids, assembles and writes a block record (status PROPOSED) to BLOCKS store, appends to BLOCK_EVENTS. Takes tx_ids as input but performs no drain operation.

**Fit for this CR:** Partial — block assembly is complete; drain is a missing peer step in the workflow, not inside this CC.

### WF_SUBMIT_TRANSACTION_V0
Full ETH transaction submission pipeline. The persist step (CC_PERSIST_MEMPOOL_TX_V0) is wired directly into this workflow. Drain is not in scope here.

**Fit for this CR:** Partial — submission pipeline is complete; persist step needs redirecting to new mempool-owned capability.

---

## 4. Gap Analysis — What Is Missing

### Gap 1 — No MEMPOOL store (CRITICAL)
No governed staging buffer exists separate from the TRANSACTION store. Pending transactions land in the committed record store.

**Impact:** All mempool operations (write, read, drain) have no correct store target.

### Gap 2 — No governed drain operation (CRITICAL)
CC_FORM_BLOCK_V0 accepts tx_ids but never removes them from any store. The mempool accumulates indefinitely after blocks are proposed.

**Impact:** Block proposal workflow cannot complete the mempool lifecycle.

### Gap 3 — CC_QUERY_PENDING_TRANSACTIONS_V0 reads wrong store (CRITICAL)
Current query reads TRANSACTION store and filters by PENDING status. Once the MEMPOOL store is introduced, this query must target the new store.

**Impact:** Proposer would read stale or wrong data without this fix.

### Gap 4 — CC_PERSIST_MEMPOOL_TX_V0 writes to wrong store (CRITICAL)
The persist step writes PENDING transactions into the TRANSACTION store — the committed record store.

**Impact:** TRANSACTION store is contaminated with pending entries that belong in the mempool.

---

## 5. Summary: Extend vs. New Subdomain

**The question:** Does the mempool concern belong inside `blockchain::transaction` or does it require `blockchain::mempool`?

**Evidence for extend (transaction):** Transaction submission already lives in the transaction subdomain; the persist step is already governed there.

**Evidence for new subdomain:** The mempool has an independent lifecycle (submit → stage → drain) with its own store, its own consumer (the block proposer), and its own drain operation that is triggered by consensus — not by the transaction submitter. The transaction subdomain owns submission; the mempool subdomain owns staging and drain. These are separate governance concerns with separate ownership boundaries.

*Decision for Stage 3 to confirm.*

---

## 6. Open Questions for Stage 3

| # | Question | Why It Matters |
|---|----------|----------------|
| Q1 | Does the drain operation belong inside CC_FORM_BLOCK_V0 or as a separate CC called after it in WF_PROPOSE_BLOCK_V0? | Determines whether block subdomain or mempool subdomain owns drain |
| Q2 | Does the mempool require its own deduplication registry or does it reuse the existing transaction registry? | Determines whether a new registry entry point is needed |
| Q3 | When a pending transaction is drained, does its record move to the TRANSACTION store (committed) or is that a separate future CR? | Scopes whether drain is delete-only or delete+write |

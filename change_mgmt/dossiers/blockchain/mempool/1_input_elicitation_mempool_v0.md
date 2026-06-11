# Stage 1 — Input Elicitation: blockchain / mempool
**Stage:** 1 — Input Elicitation
**CR:** 1_change_request_mempool_v0.md
**Status:** COMPLETE
**Feeds:** Stage 2 — Domain Model Discovery

---

## Part 1 — Problem Statement

The blockchain domain has no governed pending transaction buffer. Transactions submitted for inclusion in a future block land directly in the committed transaction record store — a store designed to hold final transaction history with mutable status. The ephemeral staging concern (holding a transaction from submission until a block proposer selects it) is ungoverned and conflated with the committed record concern. There is no governed lifecycle for a pending transaction: no governed point of entry, no governed claim by a proposer, and no governed removal after block commitment.

---

## Part 2 — Business Final Outcome

By end of this CR:
- Pending transactions can be submitted into a governed staging buffer separate from the committed transaction record store
- A block proposer can read pending transactions through a governed access contract owned by the mempool subdomain
- A block proposer can drain consumed transactions from the mempool as part of block formation in the same workflow
- The committed transaction record store remains uncontaminated — it holds only transactions that have been committed to a block

---

## Part 3 — Current Business Knowledge

### A. Existing Transaction Submission Infrastructure

The full transaction submission workflow is governed and deployed. It builds, signs, hashes, and persists a transaction. Currently the persist step writes the pending transaction directly into the committed transaction record store — the wrong staging point. A deduplication registry also exists and is used during submission to prevent duplicate transactions.

### B. Pending Transaction Buffer

The mempool is a single global buffer — all pending transactions regardless of type or submitting actor. A transaction enters the buffer at submission and leaves when a block proposer drains it during block formation. There is no segmentation by transaction type or actor.

### C. Block Proposer Dependency

Consensus selects a proposer each slot. The proposer reads the global pending buffer to include transactions in a block. Drain is part of block formation — consumed transactions are removed from the buffer in the same workflow that forms the block. Currently no governed drain exists; the buffer accumulates indefinitely.

### D. Store Design and Ordering Principles

The committed transaction record store is mutable by design (ETH-like) — transaction records need status updates and future block association. The mempool staging buffer is also mutable — entries are created on submission, read by the proposer, and deleted on drain. These are two separate stores with separate lifecycles and separate owners.

Mempool ordering is sequential by submission time. The proposer picks transactions in arrival order — no priority ordering, no fee-based selection, no per-actor nonce management.

---

## Analyst Notes

- **Purity Filter active.** Business concepts only through Stage 5. No artifact family names until Stage 6b.
- **Nonce management deferred.** Per-actor transaction sequencing and replay protection are out of scope for v0. KISS: sequential arrival order is sufficient.
- **Open question for Stage 2:** What are the distinct actors in the mempool lifecycle? Submitter and proposer are clear — is expiry a system-driven event or a governed actor action?
- **Open question for Stage 3:** What existing submission infrastructure capabilities can be reused for mempool entry? What is the deduplication boundary — does the mempool registry share the existing transaction registry or own a separate one?

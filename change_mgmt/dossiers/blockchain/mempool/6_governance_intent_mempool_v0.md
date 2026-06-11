# Governance Intent: blockchain / mempool
**Domain:** blockchain
**Subdomain:** mempool
**Version:** V0
**Status:** APPROVED
**Pipeline Stage:** Stage 6 — Governance Intent

---

## Section 1 — Domain Placement

| Field | Value |
|-------|-------|
| Domain | `blockchain` |
| Subdomain | `mempool` — NEW |
| Subdomain Action | DECLARE NEW |
| Namespace | `blockchain::mempool` |
| Rationale | The mempool lifecycle (stage → query → drain) is architecturally independent from the transaction subdomain (which owns submission) and the consensus_pos subdomain (which owns proposer selection and round recording). The MEMPOOL store must live at `blockchain/mempool/` per subdomain isolation rules. A new subdomain is required to own the staging buffer lifecycle end-to-end. |

---

## Section 2 — Authority

No new authority class is declared by this subdomain. The Transaction Submitter acts under `AC_ENDUSER_V0` (defined in `blockchain::identity`). The Block Proposer acts under `AC_SYSTEM_V0` (defined in `blockchain::identity`). The mempool subdomain is a governed capability provider — its CCs are invoked from calling workflows; it does not admit execution independently.

---

## Section 3 — Subdomain Boundary

### Owned by `blockchain::mempool`

| Artifact | Type | Action |
|----------|------|--------|
| CC_WRITE_MEMPOOL_TX_V0 | CC | NEW — governs staged write to MEMPOOL store with deduplication |
| CC_QUERY_MEMPOOL_TXS_V0 | CC | NEW — governs read of all pending entries from MEMPOOL store |
| CC_DRAIN_MEMPOOL_V0 | CC | NEW — governs DELETE of consumed tx_ids from MEMPOOL store |
| MEMPOOL store | CS_MUTABLE_JSON_V0 | NEW — governed staging buffer at `blockchain/mempool/state/mempool.json` |

### Dependency Gaps — Other Subdomains

| Subdomain | Artifact | Gap | Action |
|-----------|----------|-----|--------|
| `blockchain::transaction` | CC_PERSIST_MEMPOOL_TX_V0 | Writes pending txs to TRANSACTION store (wrong) | REPLACE — redirect persist step to CC_WRITE_MEMPOOL_TX_V0 |
| `blockchain::transaction` | WF_SUBMIT_TRANSACTION_V0 | Persist step calls wrong CC | REPLACE — updated version wires persist step to CC_WRITE_MEMPOOL_TX_V0 |
| `blockchain::consensus_pos` | CC_QUERY_PENDING_TRANSACTIONS_V0 | Reads TRANSACTION store (wrong) | REPLACE — redirect to CC_QUERY_MEMPOOL_TXS_V0 |
| `blockchain::consensus_pos` | WF_PROPOSE_BLOCK_V0 | Missing drain node after CC_FORM_BLOCK_V0 | REPLACE — updated version inserts CC_DRAIN_MEMPOOL_V0 after CC_FORM_BLOCK_V0 |
| `blockchain` | STRUCTURE_BLOCKCHAIN_STORAGE_V0 | No MEMPOOL store entry | REPLACE — add MEMPOOL store entry at `blockchain/mempool/state/mempool.json` |

### Satisfied — No Action Required

| Artifact | Type | Status |
|----------|------|--------|
| CS_MUTABLE_JSON_V0 | CS | EXISTS — WRITE, LIST, DELETE operations cover all mempool operations |
| CS_REGISTRY_V0 | CS | EXISTS — reused for mempool deduplication; new path policy only |
| CT_PURE_GENERATE_ID_V0 | CT | EXISTS — reused for mempool key generation |
| CT_PURE_FILTER_RECORDS_V0 | CT | EXISTS — reused for pending record filtering in query |

### Explicitly Deferred

| Capability | Deferred To |
|-----------|-------------|
| TRANSACTION store status update (PENDING → COMMITTED) | Future CR |
| Nonce management and per-actor sequencing | Future CR |
| Mempool expiry and eviction | Future CR |
| Priority and fee-based ordering | Future CR |
| Multi-node mempool propagation | Future CR — requires P2P transport |

---

## Section 4 — Composition

| Field | Value |
|-------|-------|
| Extends domain | `blockchain` |
| Declares new namespace | `blockchain::mempool` |
| Peer subdomains affected | `blockchain::transaction`, `blockchain::consensus_pos` |
| Structure artifact affected | `STRUCTURE_BLOCKCHAIN_STORAGE_V0` |

The `blockchain::mempool` subdomain is a governed capability provider. It declares three CCs that are invoked as governed steps within workflows owned by peer subdomains. No standalone WF_ or IN_ is declared by this subdomain in V0.

---

## Section 5 — Storage Governance

| Store | Path | Type | Owner |
|-------|------|------|-------|
| MEMPOOL | `blockchain/mempool/state/mempool.json` | CS_MUTABLE_JSON_V0 | `blockchain::mempool` |

**Governance rule:** The MEMPOOL store and TRANSACTION store are independent stores with independent subdomain paths. No record spans both. The MEMPOOL store is ephemeral by design — entries are created on submission and deleted on drain. No record migration between MEMPOOL and TRANSACTION stores occurs in this CR.

---

## Section 6 — Cross-Subdomain Dependencies

| From | To | Artifact | Dependency Type |
|------|----|----------|-----------------|
| `blockchain::transaction` | `blockchain::mempool` | CC_WRITE_MEMPOOL_TX_V0 | WF_SUBMIT_TRANSACTION_V0 calls mempool-owned persist CC |
| `blockchain::consensus_pos` | `blockchain::mempool` | CC_QUERY_MEMPOOL_TXS_V0 | WF_PROPOSE_BLOCK_V0 calls mempool-owned query CC |
| `blockchain::consensus_pos` | `blockchain::mempool` | CC_DRAIN_MEMPOOL_V0 | WF_PROPOSE_BLOCK_V0 calls mempool-owned drain CC |
| `blockchain::mempool` | `capability_side_effects` | CS_MUTABLE_JSON_V0 | WRITE (persist), LIST (query), DELETE (drain) |
| `blockchain::mempool` | `capability_side_effects` | CS_REGISTRY_V0 | Deduplication — tx_id and tx_hash uniqueness checks |
| `blockchain::mempool` | `capability_transforms` | CT_PURE_GENERATE_ID_V0 | Key generation in persist CC |
| `blockchain::mempool` | `capability_transforms` | CT_PURE_FILTER_RECORDS_V0 | Record filtering in query CC |
| `blockchain` | `blockchain::mempool` | STRUCTURE_BLOCKCHAIN_STORAGE_V0 | New MEMPOOL store entry must be added |

---

## Section 7 — Governance Boundary Rules

| # | Rule | Rationale |
|---|------|-----------|
| 1 | The MEMPOOL store path is exclusively owned by `blockchain::mempool` | Subdomain isolation — no other subdomain may read from or write to `blockchain/mempool/` |
| 2 | `blockchain::transaction` and `blockchain::consensus_pos` call mempool CCs as declared steps — not direct store access | Cross-subdomain access must go through governed CC calls, not store bypass |
| 3 | Drain is always DELETE-only from the MEMPOOL store | TRANSACTION store lifecycle is a separate governed concern; mempool drain must not write to any other store |
| 4 | CC_WRITE_MEMPOOL_TX_V0 enforces deduplication before any WRITE | tx_id uniqueness and tx_hash uniqueness must both be confirmed before the staging write |
| 5 | CC_QUERY_MEMPOOL_TXS_V0 returns VIOLATION when mempool is empty | An empty mempool is a governed state — the calling workflow must route to skip-round, not silently form an empty block |
| 6 | WF_PROPOSE_BLOCK_V0 must call CC_DRAIN_MEMPOOL_V0 after CC_FORM_BLOCK_V0 in every non-skip execution path | Drain is part of block formation — if a block forms, the mempool must be drained in the same workflow execution |

---

## Section 8 — PPS Artifacts Requiring Action

All five artifacts require a REPLACE action (new version or updated content). No existing artifact is preserved without change.

| Artifact | Current State | Required Action | Owner |
|----------|--------------|-----------------|-------|
| CC_PERSIST_MEMPOOL_TX_V0 | Writes pending tx to TRANSACTION store (wrong) | REPLACE — redirect WRITE step to MEMPOOL store | `blockchain::transaction` |
| CC_QUERY_PENDING_TRANSACTIONS_V0 | Reads TRANSACTION store, filters by PENDING status (wrong) | REPLACE — redirect LIST step to MEMPOOL store | `blockchain::consensus_pos` |
| WF_PROPOSE_BLOCK_V0 | Missing drain node after CC_FORM_BLOCK_V0 | REPLACE — insert CC_DRAIN_MEMPOOL_V0 after CC_FORM_BLOCK_V0 | `blockchain::consensus_pos` |
| WF_SUBMIT_TRANSACTION_V0 | Persist step wired to CC_PERSIST_MEMPOOL_TX_V0 (wrong store) | REPLACE — re-wire persist step to CC_WRITE_MEMPOOL_TX_V0 | `blockchain::transaction` |
| STRUCTURE_BLOCKCHAIN_STORAGE_V0 | No MEMPOOL store entry | REPLACE — add MEMPOOL store entry at `blockchain/mempool/state/mempool.json` | `blockchain` |

---

## Section 9 — Governance Outcome

| Subdomain | Outcome |
|-----------|---------|
| `blockchain::mempool` | NEW subdomain declared; three CCs authored; MEMPOOL store registered |
| `blockchain::transaction` | CC_PERSIST_MEMPOOL_TX_V0 replaced (wrong store → MEMPOOL store); WF_SUBMIT_TRANSACTION_V0 updated (persist step re-wired) |
| `blockchain::consensus_pos` | CC_QUERY_PENDING_TRANSACTIONS_V0 replaced (wrong store → MEMPOOL store); WF_PROPOSE_BLOCK_V0 updated (drain node inserted) |
| `blockchain` | STRUCTURE_BLOCKCHAIN_STORAGE_V0 updated (MEMPOOL store entry added) |

---

## Section 10 — Governance Decision Gate

| Decision Point | Outcome |
|----------------|---------|
| New subdomain required — not an extension of `blockchain::transaction` | CONFIRMED — independent lifecycle, independent store, independent ownership |
| No new authority class required | CONFIRMED — existing AC_ENDUSER_V0 and AC_SYSTEM_V0 cover all actors |
| MEMPOOL store is independent of TRANSACTION store | CONFIRMED — separate path, separate ownership, no shared key space |
| Drain is DELETE-only from MEMPOOL store | CONFIRMED — TRANSACTION store untouched by this CR |
| CS/CT capabilities are all satisfied | CONFIRMED — no new CS or CT primitives required |
| All dependency gaps are scoped and owned | CONFIRMED — transaction (GAP-1, GAP-6), consensus_pos (GAP-2, GAP-5), structure (GAP-4) |
| Governance gate | PASS — proceed to Stage 6b (Design Intent) |

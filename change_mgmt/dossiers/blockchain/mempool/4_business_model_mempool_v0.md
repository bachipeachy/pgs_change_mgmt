# Business Model: blockchain / mempool
**Domain:** blockchain
**Subdomain:** mempool
**Version:** V0
**Status:** APPROVED
**Pipeline Stage:** Stage 4 — Business Model (canonical artifact)
**Produced by:** v0.5.0 SDLC authoring pipeline

---

## 1. Discovery Summary

### Actors
| Actor | Role | Authority Class |
|-------|------|-----------------|
| Transaction Submitter | Submits a transaction into the mempool staging buffer | Actor identity (governed by `blockchain::identity`) |
| Block Proposer | Reads pending transactions and drains the mempool as part of block formation | Validator status (governed by `blockchain::consensus_pos`) |

### Entities
| Entity | Description | Store Model |
|--------|-------------|-------------|
| Pending Transaction | A validated transaction staged for block inclusion; lives in the mempool from submission until drain | Mutable key-value (MEMPOOL store) |

### Resources
| Resource | Description |
|----------|-------------|
| MEMPOOL store | Mutable key-value store; holds all pending transactions keyed by tx_id; separate from TRANSACTION store |
| TRANSACTION_EVENTS | Append-only event journal; receives submission events; unchanged by this CR |

### Events
| Event | Trigger | Lifecycle Meaning |
|-------|---------|-------------------|
| Transaction submitted | Pending transaction successfully written to MEMPOOL store | Transaction has entered the governed staging buffer |
| Mempool drained | Consumed tx_ids deleted from MEMPOOL store after block formation | Transactions have left the staging buffer; block formation is complete |

### Relationships (Candidate Capabilities)
| Subject | Verb | Object | Capability Candidate |
|---------|------|--------|---------------------|
| Transaction Submitter | stages | Pending Transaction → MEMPOOL store | Mempool persist |
| Block Proposer | reads | Pending Transactions from MEMPOOL store | Mempool query |
| Block Proposer | drains | Consumed Pending Transactions from MEMPOOL store | Mempool drain |

---

## 2. Capability Graph

| Capability | Status | Gap Register Entry | Notes |
|------------|--------|--------------------|-------|
| Persist pending transaction to MEMPOOL store | CRITICAL | GAP-1 | Replaces write to TRANSACTION store |
| Query pending transactions from MEMPOOL store | CRITICAL | GAP-2 | Replaces query against TRANSACTION store |
| Drain consumed transactions from MEMPOOL store | CRITICAL | GAP-3 | New — no equivalent exists |
| MEMPOOL store entry in STRUCTURE_BLOCKCHAIN_STORAGE_V0 | CRITICAL | GAP-4 | New entity store at `blockchain/mempool/state/mempool.json` |
| Updated WF_PROPOSE_BLOCK_V0 topology (drain node) | CRITICAL | GAP-5 | Drain node inserted after block formation |
| Updated WF_SUBMIT_TRANSACTION_V0 (persist redirect) | CRITICAL | GAP-6 | Persist step redirected to mempool-owned capability |
| CS_MUTABLE_JSON_V0 (WRITE, LIST, DELETE) | SATISFIED | — | Covers all three mempool store operations |
| CS_REGISTRY_V0 | SATISFIED | — | Reused for mempool deduplication; new path policy |
| CT_PURE_FILTER_RECORDS_V0 | SATISFIED | — | Reused for pending record filtering in query |
| CT_PURE_GENERATE_ID_V0 | SATISFIED | — | Reused for key generation in persist |

---

## 3. Dependency Graph

| From | To | Dependency Type | PPS Status |
|------|----|-----------------|------------|
| `blockchain::mempool` | `blockchain::transaction` | Persist step redirect — WF_SUBMIT_TRANSACTION_V0 calls mempool-owned persist CC | GAP |
| `blockchain::mempool` | `blockchain::consensus_pos` | Drain node added to WF_PROPOSE_BLOCK_V0 after CC_FORM_BLOCK_V0 | GAP |
| `blockchain::mempool` | `blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0` | New MEMPOOL store entry required | GAP |
| `blockchain::mempool` | `capability_side_effects` | CS_MUTABLE_JSON_V0, CS_REGISTRY_V0, CS_APPENDONLY_JSONL_V0 | SATISFIED |
| `blockchain::mempool` | `capability_transforms` | CT_PURE_GENERATE_ID_V0, CT_PURE_FILTER_RECORDS_V0 | SATISFIED |

---

## 4. Constraint Register

| # | Constraint | Source |
|---|-----------|--------|
| 1 | MEMPOOL store is separate from TRANSACTION store — different subdomain paths, no shared key space | STRUCTURE isolation rules |
| 2 | Mempool is a single global buffer — no segmentation by actor or transaction type | Design decision (Stage 1) |
| 3 | Mempool ordering is sequential by submission time (created_at) — no priority, no fee-based selection | Design decision (Stage 1, KISS) |
| 4 | Drain is part of block formation — same workflow, not a separate triggered operation | Design decision (Stage 1) |
| 5 | Drain is DELETE-only from MEMPOOL store — TRANSACTION store is untouched by this CR | Scoping decision (Stage 3, Q3) |
| 6 | No nonce management in this CR | Design decision (Stage 1, KISS) |

---

## 5. Gap Register

| Gap Code | Capability | Owner Subdomain | Resolution |
|----------|-----------|-----------------|------------|
| GAP-1 | Persist pending transaction to MEMPOOL store | `blockchain::mempool` | REPLACE — new mempool-owned persist capability replaces TRANSACTION store write |
| GAP-2 | Query pending transactions from MEMPOOL store | `blockchain::mempool` | REPLACE — new mempool-owned query capability replaces TRANSACTION store read |
| GAP-3 | Drain consumed transactions from MEMPOOL store | `blockchain::mempool` | NEW — no equivalent exists in snapshot |
| GAP-4 | MEMPOOL store entry in STRUCTURE_BLOCKCHAIN_STORAGE_V0 | `blockchain` | NEW — new entity store entry at `blockchain/mempool/state/mempool.json` |
| GAP-5 | Updated WF_PROPOSE_BLOCK_V0 topology | `blockchain::consensus_pos` | REPLACE — new version with drain node after CC_FORM_BLOCK_V0 |
| GAP-6 | Updated WF_SUBMIT_TRANSACTION_V0 persist redirect | `blockchain::transaction` | REPLACE — new version redirecting persist step to mempool-owned capability |

---

## 6. Design Decisions Register

| # | Decision | Rationale | Constraints Imposed |
|---|----------|-----------|---------------------|
| 1 | Single global buffer — no segmentation | KISS; per-actor or per-type pools add complexity with no v0 benefit | Query returns all pending txs; no filter by actor or type at read time |
| 2 | Sequential ordering by arrival time | KISS; fee market and priority are future CR concerns | Proposer picks in created_at order; no reordering allowed |
| 3 | Drain is part of block formation | Atomic — block forms and mempool clears in the same workflow execution | Cannot drain without a formed block; drain CC is called from consensus workflow |
| 4 | Drain = DELETE only from MEMPOOL store | TRANSACTION store lifecycle (PENDING→COMMITTED) is a separate future CR | TRANSACTION store is untouched; no committed record written this CR |
| 5 | New subdomain `blockchain::mempool` | Independent lifecycle, independent store, separate ownership boundary from transaction and consensus_pos | Mempool CCs are namespaced under `blockchain::mempool`; consensus_pos calls mempool-owned drain |

---

## 7. Authoring Scope

### In Scope — This CR
| Capability | Gap Register Ref |
|-----------|-----------------|
| MEMPOOL store entry in STRUCTURE_BLOCKCHAIN_STORAGE_V0 | GAP-4 |
| Mempool persist capability | GAP-1 |
| Mempool query capability | GAP-2 |
| Mempool drain capability | GAP-3 |
| Updated WF_PROPOSE_BLOCK_V0 (drain node) | GAP-5 |
| Updated WF_SUBMIT_TRANSACTION_V0 (persist redirect) | GAP-6 |

### Deferred — Future CR
| Capability | Deferred Reason |
|-----------|-----------------|
| TRANSACTION store status update (PENDING → COMMITTED, block association) | Separate lifecycle concern; revisit JIT |
| Nonce management and per-actor sequencing | KISS for v0; future fee/replay-protection CR |
| Mempool expiry and eviction | Future CR |
| Priority and fee-based ordering | Future CR — requires fee model design |
| Multi-node mempool propagation | Future CR — requires P2P transport |

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 1 — Input Elicitation | Problem + Outcome + Known Facts | COMPLETE |
| Stage 2 — Domain Model Discovery | Actors, Entities, Resources, Events, Relationships | COMPLETE |
| Stage 3 — Analysis Loop | Capability Graph, Dependency Graph, Constraints, Gap Register | COMPLETE — SATURATED |
| Stage 4 — Business Model | This document | APPROVED |

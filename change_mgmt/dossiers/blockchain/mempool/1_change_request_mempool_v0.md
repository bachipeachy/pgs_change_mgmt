# Change Request: blockchain / mempool
**CR Type:** change_request_subdomain  
**Domain:** blockchain  
**Primary Subdomain:** mempool — NEW  
**Secondary Subdomain:** transaction — EXISTING (dependency gap)  
**Version:** V0  
**Status:** DRAFT  
**Pipeline Stage:** Stage 0 — Change Request Classification  

---

## 1. Problem Statement

The blockchain domain has no governed mempool subdomain. The pending transaction buffer — the ephemeral staging area between transaction submission and block commitment — is not a governed protocol concern. Currently, `CC_PERSIST_MEMPOOL_TX_V0` writes pending transactions into the TRANSACTION store, conflating two architecturally distinct concerns: the ephemeral staging buffer and the mutable transaction record store. No governed lifecycle exists for the mempool: submission, pending state maintenance, proposer drain, and expiry are uncontrolled.

---

## 2. Desired Outcome

A governed `blockchain::mempool` subdomain that owns the pending transaction lifecycle end-to-end:

- Governed submission of pending transactions into a dedicated mempool store (separate from TRANSACTION store)
- Governed read of pending transactions by consensus at block proposal time
- Governed drain of consumed transactions from the mempool after block commitment
- Governed expiry of stale transactions (timeout-based or slot-based)
- All mempool operations owned by the `mempool` subdomain; `consensus_pos` is a declared consumer, not an owner

---

## 3. Known Facts at CR Entry

| Fact | Source |
|------|--------|
| `blockchain::transaction` subdomain is governed and deployed | PPS snapshot |
| `CC_PERSIST_MEMPOOL_TX_V0` exists but writes pending txs to TRANSACTION store prematurely | PPS snapshot |
| `CC_QUERY_PENDING_TRANSACTIONS_V0` exists — reads pending txs at block proposal time | PPS snapshot |
| TRANSACTION store is `CS_MUTABLE_JSON_V0` — mutable by design; records need status updates and future block association (ETH-like) | Strategic architecture |
| `scripts/test_blockchain_e2e.py` exercises the full Identity→Wallet→Consensus path; will need updating when mempool store changes | Test baseline |

---

## 4. CR Type Determination

**Type:** `change_request_subdomain`

**Analysis path triggered:** Full loop required — Domain Model Discovery + Analysis Loop until Discovery Saturation. Declaring a new subdomain with cross-subdomain ownership corrections (transaction, consensus_pos) and a new dedicated store requires the complete pipeline.

**Pipeline entry:** Stage 1 — Input Elicitation

---

## 5. Governance Scope Declared by This CR

| Subdomain | Action | Rationale |
|-----------|--------|-----------|
| `blockchain::mempool` | DECLARE NEW | Owns pending tx lifecycle — submission, maintenance, drain, expiry |
| `blockchain::transaction` | DEPENDENCY GAP | `CC_PERSIST_MEMPOOL_TX_V0` writes pending txs to wrong store; submission must be re-owned by mempool subdomain |
| `blockchain::consensus_pos` | DEPENDENCY GAP | Reads pending txs at block proposal time — access must be governed through a mempool-owned CC, not direct store access |

---

## 6. Out of Scope — Deferred to Future CRs

| Capability | Reason |
|-----------|--------|
| Transaction fee market and priority ordering | Future CR — requires fee model design |
| Mempool flood protection and rate limiting | Future CR — requires actor reputation or stake constraints |
| Multi-node mempool propagation (gossip) | Future CR — requires P2P transport layer |
| Block commitment writing to TRANSACTION store | Owned by `blockchain::block` or `blockchain::transaction`; out of mempool scope |
| Mempool size limits and eviction policy | Future CR |
| TRANSACTION store status update lifecycle (PENDING → COMMITTED, block association) | Revisit JIT — out of scope for this CR |

---

## Dossier Status

| Stage | Artifact | Status |
|-------|----------|--------|
| Stage 0 | 1_change_request_mempool_v0.md | COMPLETE |
| Stage 1 | 1_input_elicitation_mempool_v0.md | COMPLETE |
| Stage 2 | 2_domain_model_mempool_v0.md | COMPLETE |
| Stage 3 | 3_analysis_loop_mempool_v0.md | COMPLETE |
| Stage 4 | 4_business_model_mempool_v0.md | COMPLETE |
| Stage 5 | 5_business_intent_mempool_v0.md | COMPLETE — APPROVED |
| Stage 6 | 6_governance_intent_mempool_v0.md | COMPLETE — APPROVED |
| Stage 6b | 6b_design_intent_mempool_v0.md | COMPLETE — APPROVED |
| Stage 7 | 7_authoring_mandate_mempool_v0.md | COMPLETE — APPROVED |
| Stage 8 | 8_authoring_manifest_mempool_v0.md | COMPLETE — DRAFT (pre-authoring baseline) |
| Stage 9 | (CR Closure — no separate artifact; manifest status → APPROVED) | PENDING |

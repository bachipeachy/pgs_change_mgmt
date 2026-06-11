# Authoring Mandate: blockchain / chain
**Domain:** blockchain  
**Subdomain:** chain  
**Version:** V0  
**Status:** DRAFT  
**Pipeline Stage:** Stage 7 — Authoring Mandate  
**Produced by:** v0.5.0 SDLC authoring pipeline  

---

## 1. Build Dependency Order

Derived by topological sort of the artifact dependency graph produced in Stage 6b (Design Intent). Parallel work is grouped into waves. The critical path is the longest sequential dependency chain.

### Wave 1 — Foundational Primitives (no new-artifact dependencies)

| Step | Artifact | Action | Subdomain | Depends On |
|------|----------|--------|-----------|------------|
| 1.1 | `blockchain::CT_PURE_COMPARE_ROUND_IDS_V0` | NEW | `chain` | — |
| 1.2 | `blockchain::IN_INITIALIZE_CHAIN_V0` | NEW | `chain` | — |
| 1.3 | `blockchain::IN_COMMIT_BLOCK_V0` | NEW | `chain` | — |
| 1.4 | `blockchain::STRUCTURE_BLOCKCHAIN_CHAIN_STORAGE_V0` | NEW | `chain` | — |
| 1.5 | `blockchain::EV_BLOCK_COMMITTED_V0` | UPDATE (metadata) | `block` | — (Emitted By table only; no schema change) |

### Wave 2 — Capability Contracts (depend on Wave 1 + existing PPS)

| Step | Artifact | Action | Subdomain | Depends On |
|------|----------|--------|-----------|------------|
| 2.1 | `blockchain::CC_CHECK_CHAIN_NOT_INITIALIZED_V0` | NEW | `chain` | `STRUCTURE_BLOCKCHAIN_CHAIN_STORAGE_V0` |
| 2.2 | `blockchain::CC_READ_CHAIN_STATE_V0` | NEW | `chain` | `STRUCTURE_BLOCKCHAIN_CHAIN_STORAGE_V0` |
| 2.3 | `blockchain::CC_READ_PROPOSED_BLOCK_V0` | NEW | `chain` | existing `STRUCTURE_BLOCKCHAIN_STORAGE_V0` (`BLOCKS` read) |
| 2.4 | `blockchain::CC_VERIFY_CHAIN_COMMIT_ELIGIBILITY_V0` | NEW | `chain` | `CT_PURE_COMPARE_ROUND_IDS_V0` |
| 2.5 | `blockchain::CC_UPDATE_CHAIN_STATE_V0` | NEW | `chain` | `STRUCTURE_BLOCKCHAIN_CHAIN_STORAGE_V0` |
| 2.6 | `blockchain::CC_APPEND_GENESIS_BLOCK_REF_V0` | NEW | `chain` | `STRUCTURE_BLOCKCHAIN_CHAIN_STORAGE_V0`, existing `CT_PURE_KECCAK256_HASH_V0` |
| 2.7 | `blockchain::CC_APPEND_BLOCK_REF_V0` | NEW | `chain` | `STRUCTURE_BLOCKCHAIN_CHAIN_STORAGE_V0`, existing `CT_PURE_KECCAK256_HASH_V0` |
| 2.8 | `blockchain::CC_INVOKE_WALLET_CREATION_V0` | NEW | `chain` | existing `CS_WORKFLOW_GATEWAY_V0`, `WF_CREATE_WALLET_V0` |
| 2.9 | `blockchain::CC_INVOKE_GENESIS_MINT_V0` | NEW | `chain` | existing `CS_WORKFLOW_GATEWAY_V0`, `WF_MINT_V0` |
| 2.10 | `blockchain::CC_INVOKE_VALIDATOR_REGISTRATION_V0` | NEW | `chain` | existing `CS_WORKFLOW_GATEWAY_V0`, `WF_REGISTER_VALIDATOR_V0` |
| 2.11 | `blockchain::CC_FORM_GENESIS_BLOCK_V0` | NEW | `block` | existing `STRUCTURE_BLOCKCHAIN_STORAGE_V0` (`BLOCKS`, `BLOCK_EVENTS`), existing CTs |
| 2.12 | `blockchain::CC_MARK_BLOCK_CANONICAL_V0` | NEW | `block` | existing `STRUCTURE_BLOCKCHAIN_STORAGE_V0` (`BLOCKS`, `BLOCK_EVENTS`) |

### Wave 3 — Workflows

| Step | Artifact | Action | Subdomain | Depends On |
|------|----------|--------|-----------|------------|
| 3.1 | `blockchain::WF_INITIALIZE_CHAIN_V0` | NEW | `chain` | 1.2, 2.1, 2.5, 2.6, 2.8, 2.9, 2.10, 2.11; existing `CC_PERSIST_VERIFIED_ACTOR_V0` |
| 3.2 | `blockchain::WF_COMMIT_BLOCK_V0` | NEW | `chain` | 1.3, 2.2, 2.3, 2.4, 2.5, 2.7, 2.12 |

### Wave 4 — Runtime Bindings and Orchestration Gateway

| Step | Artifact | Action | Subdomain | Depends On |
|------|----------|--------|-----------|------------|
| 4.1 | `blockchain::RB_INITIALIZE_CHAIN_V0` | NEW | `chain` | 3.1 |
| 4.2 | `blockchain::RB_COMMIT_BLOCK_V0` | NEW | `chain` | 3.2 |
| 4.3 | `blockchain::CC_INVOKE_BLOCK_COMMITMENT_V0` | NEW | `orchestration` | 3.2; existing `CS_WORKFLOW_GATEWAY_V0` |

### Wave 5 — Slot Workflow Extension

| Step | Artifact | Action | Subdomain | Depends On |
|------|----------|--------|-----------|------------|
| 5.1 | `blockchain::WF_PROCESS_SLOT_V0` | EXTEND | `orchestration` | 4.3 (insert node after `CC_INVOKE_BLOCK_PROPOSAL_V0` SUCCESS, before `CC_ADVANCE_SLOT_CLOCK_V0`) |

---

## 2. Critical Path

`CT_PURE_COMPARE_ROUND_IDS_V0` (1.1) → `CC_VERIFY_CHAIN_COMMIT_ELIGIBILITY_V0` (2.4) → `WF_COMMIT_BLOCK_V0` (3.2) → `CC_INVOKE_BLOCK_COMMITMENT_V0` (4.3) → `WF_PROCESS_SLOT_V0` EXTEND (5.1)

Steps: 1.1, 2.4, 3.2, 4.3, 5.1

---

## 3. Artifact Summary

| Count | Action | Description |
|-------|--------|-------------|
| 0 | REPLACE | — |
| 1 | EXTEND | `blockchain::WF_PROCESS_SLOT_V0` |
| 1 | UPDATE (metadata) | `blockchain::EV_BLOCK_COMMITTED_V0` (Emitted By table only) |
| 21 | NEW | chain (18): `WF_INITIALIZE_CHAIN_V0`, `IN_INITIALIZE_CHAIN_V0`, `RB_INITIALIZE_CHAIN_V0`, `WF_COMMIT_BLOCK_V0`, `IN_COMMIT_BLOCK_V0`, `RB_COMMIT_BLOCK_V0`, `CC_CHECK_CHAIN_NOT_INITIALIZED_V0`, `CC_INVOKE_WALLET_CREATION_V0`, `CC_INVOKE_GENESIS_MINT_V0`, `CC_INVOKE_VALIDATOR_REGISTRATION_V0`, `CC_APPEND_GENESIS_BLOCK_REF_V0`, `CC_UPDATE_CHAIN_STATE_V0`, `CC_READ_CHAIN_STATE_V0`, `CC_READ_PROPOSED_BLOCK_V0`, `CC_VERIFY_CHAIN_COMMIT_ELIGIBILITY_V0`, `CC_APPEND_BLOCK_REF_V0`, `CT_PURE_COMPARE_ROUND_IDS_V0`, `STRUCTURE_BLOCKCHAIN_CHAIN_STORAGE_V0`; block (2): `CC_FORM_GENESIS_BLOCK_V0`, `CC_MARK_BLOCK_CANONICAL_V0`; orchestration (1): `CC_INVOKE_BLOCK_COMMITMENT_V0` |
| **23** | **Total** | Reconciled with Design Intent Section 11 |

---

## 4. Subdomain Field Declarations

| Artifact Code | Subdomain Field Value |
|---|---|
| `WF_INITIALIZE_CHAIN_V0` | `chain` |
| `IN_INITIALIZE_CHAIN_V0` | `chain` |
| `RB_INITIALIZE_CHAIN_V0` | `chain` |
| `WF_COMMIT_BLOCK_V0` | `chain` |
| `IN_COMMIT_BLOCK_V0` | `chain` |
| `RB_COMMIT_BLOCK_V0` | `chain` |
| `CC_CHECK_CHAIN_NOT_INITIALIZED_V0` | `chain` |
| `CC_INVOKE_WALLET_CREATION_V0` | `chain` |
| `CC_INVOKE_GENESIS_MINT_V0` | `chain` |
| `CC_INVOKE_VALIDATOR_REGISTRATION_V0` | `chain` |
| `CC_APPEND_GENESIS_BLOCK_REF_V0` | `chain` |
| `CC_UPDATE_CHAIN_STATE_V0` | `chain` |
| `CC_READ_CHAIN_STATE_V0` | `chain` |
| `CC_READ_PROPOSED_BLOCK_V0` | `chain` |
| `CC_VERIFY_CHAIN_COMMIT_ELIGIBILITY_V0` | `chain` |
| `CC_APPEND_BLOCK_REF_V0` | `chain` |
| `CT_PURE_COMPARE_ROUND_IDS_V0` | `chain` |
| `STRUCTURE_BLOCKCHAIN_CHAIN_STORAGE_V0` | `chain` |
| `CC_FORM_GENESIS_BLOCK_V0` | `block` |
| `CC_MARK_BLOCK_CANONICAL_V0` | `block` |
| `CC_INVOKE_BLOCK_COMMITMENT_V0` | `orchestration` |

---

## 5. Cross-Subdomain Dependency Notes

- `blockchain::orchestration::WF_PROCESS_SLOT_V0` (EXTEND) invokes `blockchain::chain::WF_COMMIT_BLOCK_V0` via `CC_INVOKE_BLOCK_COMMITMENT_V0` (`CS_WORKFLOW_GATEWAY_V0`) — capability call, permitted.
- `blockchain::chain::WF_INITIALIZE_CHAIN_V0` calls `blockchain::identity::CC_PERSIST_VERIFIED_ACTOR_V0` directly, and `WF_CREATE_WALLET_V0` / `WF_MINT_V0` / `WF_REGISTER_VALIDATOR_V0` via chain-owned gateway CCs — capability calls, permitted.
- `blockchain::chain::CC_READ_PROPOSED_BLOCK_V0` reads the `BLOCKS` store — cross-subdomain read, permitted.
- All `BLOCKS` writes are performed by **block-owned** CCs (`CC_FORM_GENESIS_BLOCK_V0`, `CC_MARK_BLOCK_CANONICAL_V0`). **No cross-subdomain writes exist in this CR — they are forbidden, without exception.**
- No event-driven triggers exist: `EV_BLOCK_COMMITTED_V0` is recorded as a fact by chain CCs; nothing consumes events to start execution.

---

## 6. Invariants and Design Clarifications

- **CHAIN_STATE Authority:** `CHAIN_STATE` is the canonical head reference. `CHAIN` is historical lineage; `BLOCKS` holds payloads. CCs must not derive head state from `CHAIN` traversal.
- **Single-Head Invariant:** A candidate block may be committed only if its `round_id` equals the current `CHAIN_STATE` height + 1 and it is in `PROPOSED` status; linkage (`previous_block_hash` = head hash) is constructed at commitment. This is the fundamental V0 chain rule.
- **Exactly-Once Genesis:** `CC_CHECK_CHAIN_NOT_INITIALIZED_V0` gates `WF_INITIALIZE_CHAIN_V0`; `ALREADY_EXISTS` terminates without side effects.

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 6b — Design Intent | 6b_design_intent_blockchain_chain_v0.md | PENDING GATE 1 APPROVAL |
| Stage 7 — Authoring Mandate | This document | PENDING GATE 2 APPROVAL (after Gate 1) |
| Stage 8 — Authoring Manifest | 8_authoring_manifest_blockchain_chain_v0.md | PENDING — baseline created |

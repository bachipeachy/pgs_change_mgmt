# Authoring Mandate: blockchain / data_model
**Domain:** blockchain  
**Primary subdomain:** transaction  
**Additional subdomains:** identity, wallet, consensus_pos, block (updates + new events), chain (declared — no artifacts; boundary established for cross-consensus compatibility)  
**Version:** V0  
**Status:** APPROVED  
**Pipeline Stage:** Stage 7 — Authoring Mandate  
**Produced by:** v0.5.0 SDLC authoring pipeline  
**Input:** 7_authoring_plan_data_model_v0.md (Stage 7 — COMPLETE)

---

## 1. Build Dependency Order

Steps within the same wave have no inter-dependencies and may be authored in parallel.

---

### Wave 1 — Foundation (no dependencies)

| Step | Artifact / File | Action | Subdomain | Depends On |
|------|-----------------|--------|-----------|------------|
| 1 | `seeds/genesis_actor.json` | NEW (seed) | identity | nothing |
| 2 | `seeds/system_wallets.json` | NEW (seed) | wallet | nothing |
| 3 | `seeds/register_validator_payload.json` | UPDATE (seed) | consensus_pos | nothing |
| 4 | `blockchain::WF_SUBMIT_TRANSACTION_V0` | RETIRE | transaction | nothing |
| 5 | `blockchain::IN_TRANSACTION_SUBMITTED_V0` | RETIRE | transaction | nothing |
| 6 | `blockchain::RB_SUBMIT_TRANSACTION_V0` | RETIRE | transaction | nothing |
| 7 | `blockchain::CC_VALIDATE_TX_STRUCTURE_V0` | RETIRE | transaction | nothing |
| 8 | `blockchain::CC_VALIDATE_TX_POLICY_V0` | RETIRE | transaction | nothing |
| 9 | `blockchain::CC_BUILD_ETH_TX_V0` | RETIRE | transaction | nothing |
| 10 | `blockchain::CC_SIGN_TRANSACTION_V0` | RETIRE | transaction | nothing |
| 11 | `blockchain::CC_HASH_TRANSACTION_V0` | RETIRE | transaction | nothing |
| 12 | `blockchain::IN_TRANSFER_V0` | NEW | transaction | nothing |
| 13 | `blockchain::IN_STAKE_V0` | NEW | transaction | nothing |
| 14 | `blockchain::IN_UNSTAKE_V0` | NEW | transaction | nothing |
| 15 | `blockchain::IN_MINT_V0` | NEW | transaction | nothing |
| 16 | `blockchain::IN_BURN_V0` | NEW | transaction | nothing |
| 17 | `blockchain::IN_POOL_V0` | NEW | transaction | nothing |
| 18 | `blockchain::IN_REWARD_V0` | NEW | transaction | nothing |
| 19 | `blockchain::IN_SLASH_V0` | NEW | transaction | nothing |
| 20 | `blockchain::EV_BLOCK_ATTESTED_V0` | NEW | block | nothing |
| 21 | `blockchain::EV_BLOCK_FINALIZED_V0` | NEW | block | nothing |
| 22 | `blockchain::EV_BLOCK_COMMITTED_V0` | NEW | block | nothing |
| 23 | `blockchain::EV_TX_FINALIZED_V0` | NEW | transaction | nothing |
| 24 | `blockchain::EV_BALANCE_RECONCILED_V0` | NEW | wallet | nothing |

---

### Wave 2 — After Retirements (Steps 4–11)

| Step | Artifact | Action | Subdomain | Depends On |
|------|----------|--------|-----------|------------|
| 25 | `blockchain::IN_ACTOR_REGISTERED_V0` | UPDATE | identity | Steps 4–11 (retirements clear) |
| 26 | `blockchain::IN_WALLET_CREATED_V0` | UPDATE | wallet | Steps 4–11 |
| 27 | `blockchain::IN_VALIDATOR_REGISTERED_V0` | UPDATE | consensus_pos | Steps 4–11 |
| 28 | `blockchain::CC_PERSIST_MEMPOOL_TX_V0` | UPDATE | transaction | Step 4 (WF_SUBMIT_TRANSACTION retired) |

---

### Wave 3 — After Wave 2

| Step | Artifact | Action | Subdomain | Depends On |
|------|----------|--------|-----------|------------|
| 29 | `blockchain::CC_WRITE_ACTOR_RECORD_V0` | UPDATE | identity | Step 25 (IN_ACTOR_REGISTERED enriched) |
| 30 | `blockchain::CC_CREATE_WALLET_RECORD_V0` | UPDATE | wallet | Step 26 (IN_WALLET_CREATED enriched) |
| 31 | `blockchain::CC_WRITE_VALIDATOR_RECORD_V0` | UPDATE | consensus_pos | Step 27 (IN_VALIDATOR_REGISTERED enriched) |
| 32 | `blockchain::CC_FORM_BLOCK_V0` | UPDATE | block | Steps 25–27 (enriched field context) |
| 33 | `blockchain::CC_VALIDATE_TRANSFER_POLICY_V0` | NEW | transaction | Step 28 (CC_PERSIST updated) |
| 34 | `blockchain::CC_VALIDATE_STAKE_POLICY_V0` | NEW | transaction | Step 28 |
| 35 | `blockchain::CC_VALIDATE_UNSTAKE_POLICY_V0` | NEW | transaction | Step 28 |
| 36 | `blockchain::CC_VALIDATE_MINT_POLICY_V0` | NEW | transaction | Step 28 |
| 37 | `blockchain::CC_VALIDATE_BURN_POLICY_V0` | NEW | transaction | Step 28 |
| 38 | `blockchain::CC_VALIDATE_POOL_POLICY_V0` | NEW | transaction | Step 28 |
| 39 | `blockchain::CC_VALIDATE_REWARD_POLICY_V0` | NEW | transaction | Step 28 |
| 40 | `blockchain::CC_VALIDATE_SLASH_POLICY_V0` | NEW | transaction | Step 28 |

---

### Wave 4 — After Wave 3

| Step | Artifact | Action | Subdomain | Depends On |
|------|----------|--------|-----------|------------|
| 41 | `blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0` | REVIEW | cross-subdomain | Steps 29–32 (CC updates clarify store schema needs) |
| 42 | `blockchain::RB_TRANSFER_V0` | NEW | transaction | Steps 12, 33 (IN_ + Policy CC ready) |
| 43 | `blockchain::RB_STAKE_V0` | NEW | transaction | Steps 13, 34 |
| 44 | `blockchain::RB_UNSTAKE_V0` | NEW | transaction | Steps 14, 35 |
| 45 | `blockchain::RB_MINT_V0` | NEW | transaction | Steps 15, 36 |
| 46 | `blockchain::RB_BURN_V0` | NEW | transaction | Steps 16, 37 |
| 47 | `blockchain::RB_POOL_V0` | NEW | transaction | Steps 17, 38 |
| 48 | `blockchain::RB_REWARD_V0` | NEW | transaction | Steps 18, 39 |
| 49 | `blockchain::RB_SLASH_V0` | NEW | transaction | Steps 19, 40 |

---

### Wave 5 — After Wave 4 RB_ (Steps 42–49)

| Step | Artifact | Action | Subdomain | Depends On |
|------|----------|--------|-----------|------------|
| 50 | `blockchain::WF_TRANSFER_V0` | NEW | transaction | Steps 12, 42 (IN_ + RB_ ready) |
| 51 | `blockchain::WF_STAKE_V0` | NEW | transaction | Steps 13, 43 |
| 52 | `blockchain::WF_UNSTAKE_V0` | NEW | transaction | Steps 14, 44 |
| 53 | `blockchain::WF_MINT_V0` | NEW | transaction | Steps 15, 45 |
| 54 | `blockchain::WF_BURN_V0` | NEW | transaction | Steps 16, 46 |
| 55 | `blockchain::WF_POOL_V0` | NEW | transaction | Steps 17, 47 |
| 56 | `blockchain::WF_REWARD_V0` | NEW | transaction | Steps 18, 48 |
| 57 | `blockchain::WF_SLASH_V0` | NEW | transaction | Steps 19, 49 |

---

### Wave 6 — Terminal

```bash
# Per-structure compile (blockchain only)
python -m pgs_compiler.cli compile --structure STRUCTURE_BUILD_BLOCKCHAIN_CONFIG_V0

# Cross-structure vocabulary aggregation
python -m pgs_compiler.cli compile --structure STRUCTURE_BUILD_VOCABULARY_AGGREGATE_V0

# Full build: sync artifacts + conformance + mark snapshot valid
python -m pgs_compiler.cli build --workspace /abs/path/to/pgs_workspace
```

**Compiler success criteria:**
- All 8 RETIRED artifacts carry `status: RETIRED` — no active artifact references a RETIRED FQDN
- All 8 typed WFs resolve IN_, RB_, and CC graph without missing artifact errors
- Conformance tests pass for all enriched IN_ schemas (field types, required fields, enum values)
- Vocabulary aggregate includes all 37 new FQDNs

---

## 2. Critical Path

Steps: **4 → 28 → 33 → 42 → 50 → compile**

(Retire WF_SUBMIT_TRANSACTION → Update CC_PERSIST_MEMPOOL_TX → Author first Policy CC → Author first RB_ → Author first WF_ → compile)

Typed IN_ (Steps 12–19) and Events (Steps 20–24) are off the critical path — they can be authored in Wave 1 with retirements.

---

## 3. Artifact Summary

| Count | Action | Description |
|-------|--------|-------------|
| 8 | RETIRE | WF_SUBMIT_TRANSACTION_V0, IN_TRANSACTION_SUBMITTED_V0, RB_SUBMIT_TRANSACTION_V0, CC_VALIDATE_TX_STRUCTURE_V0, CC_VALIDATE_TX_POLICY_V0, CC_BUILD_ETH_TX_V0, CC_SIGN_TRANSACTION_V0, CC_HASH_TRANSACTION_V0 |
| 8 | UPDATE | IN_ACTOR_REGISTERED_V0, IN_WALLET_CREATED_V0, IN_VALIDATOR_REGISTERED_V0, CC_WRITE_ACTOR_RECORD_V0, CC_CREATE_WALLET_RECORD_V0, CC_WRITE_VALIDATOR_RECORD_V0, CC_FORM_BLOCK_V0, CC_PERSIST_MEMPOOL_TX_V0 |
| 1 | REVIEW | STRUCTURE_BLOCKCHAIN_STORAGE_V0 (update only if store schema annotations are absent or mismatched) |
| 8 | NEW (CC) | CC_VALIDATE_TRANSFER/STAKE/UNSTAKE/MINT/BURN/POOL/REWARD/SLASH_POLICY_V0 |
| 8 | NEW (IN_) | IN_TRANSFER/STAKE/UNSTAKE/MINT/BURN/POOL/REWARD/SLASH_V0 |
| 8 | NEW (RB_) | RB_TRANSFER/STAKE/UNSTAKE/MINT/BURN/POOL/REWARD/SLASH_V0 |
| 8 | NEW (WF_) | WF_TRANSFER/STAKE/UNSTAKE/MINT/BURN/POOL/REWARD/SLASH_V0 |
| 5 | NEW (EV_) | EV_BLOCK_ATTESTED/FINALIZED/COMMITTED_V0, EV_TX_FINALIZED_V0, EV_BALANCE_RECONCILED_V0 |
| 3 | SEED | genesis_actor.json (NEW), system_wallets.json (NEW), register_validator_payload.json (UPDATE) |
| **57** | **Total** | **8 retirements + 8 updates + 1 review + 37 new artifacts + 3 seed actions** |

---

## 4. Subdomain Field Declarations

| Artifact Code | Subdomain Field Value |
|---|---|
| IN_ACTOR_REGISTERED_V0 | `identity` |
| CC_WRITE_ACTOR_RECORD_V0 | `identity` |
| IN_WALLET_CREATED_V0 | `wallet` |
| CC_CREATE_WALLET_RECORD_V0 | `wallet` |
| EV_BALANCE_RECONCILED_V0 | `wallet` |
| IN_VALIDATOR_REGISTERED_V0 | `consensus_pos` |
| CC_WRITE_VALIDATOR_RECORD_V0 | `consensus_pos` |
| CC_FORM_BLOCK_V0 | `block` |
| EV_BLOCK_ATTESTED_V0 | `block` |
| EV_BLOCK_FINALIZED_V0 | `block` |
| EV_BLOCK_COMMITTED_V0 | `block` |
| CC_PERSIST_MEMPOOL_TX_V0 | `transaction` |
| CC_VALIDATE_TRANSFER_POLICY_V0 | `transaction` |
| CC_VALIDATE_STAKE_POLICY_V0 | `transaction` |
| CC_VALIDATE_UNSTAKE_POLICY_V0 | `transaction` |
| CC_VALIDATE_MINT_POLICY_V0 | `transaction` |
| CC_VALIDATE_BURN_POLICY_V0 | `transaction` |
| CC_VALIDATE_POOL_POLICY_V0 | `transaction` |
| CC_VALIDATE_REWARD_POLICY_V0 | `transaction` |
| CC_VALIDATE_SLASH_POLICY_V0 | `transaction` |
| IN_TRANSFER_V0 | `transaction` |
| IN_STAKE_V0 | `transaction` |
| IN_UNSTAKE_V0 | `transaction` |
| IN_MINT_V0 | `transaction` |
| IN_BURN_V0 | `transaction` |
| IN_POOL_V0 | `transaction` |
| IN_REWARD_V0 | `transaction` |
| IN_SLASH_V0 | `transaction` |
| RB_TRANSFER_V0 | `transaction` |
| RB_STAKE_V0 | `transaction` |
| RB_UNSTAKE_V0 | `transaction` |
| RB_MINT_V0 | `transaction` |
| RB_BURN_V0 | `transaction` |
| RB_POOL_V0 | `transaction` |
| RB_REWARD_V0 | `transaction` |
| RB_SLASH_V0 | `transaction` |
| WF_TRANSFER_V0 | `transaction` |
| WF_STAKE_V0 | `transaction` |
| WF_UNSTAKE_V0 | `transaction` |
| WF_MINT_V0 | `transaction` |
| WF_BURN_V0 | `transaction` |
| WF_POOL_V0 | `transaction` |
| WF_REWARD_V0 | `transaction` |
| WF_SLASH_V0 | `transaction` |
| EV_TX_FINALIZED_V0 | `transaction` |

*Retired artifacts do not require subdomain declaration — their protocol source receives only `status: RETIRED` and `superseded_by`.*

---

## 5. Cross-Subdomain Dependency Notes

**Permitted: cross-subdomain CC calls within the same domain**

All 8 typed WFs (subdomain: `transaction`) call `CC_WRITE_ACTOR_RECORD_V0` and `CC_RESOLVE_ACTOR_ID_V0` (subdomain: `identity`) and `CC_RESERVE_NONCE_V0` (subdomain: `wallet`). These are cross-subdomain capability calls within `blockchain` — permitted by governance. The WF DAG declares these CCs by FQDN; the runtime resolves them from the snapshot.

**Forbidden: cross-subdomain writes**

No artifact in this CR writes to a store outside its declared subdomain. Policy CCs read from the WALLETS store (wallet subdomain) but do not write to it — they output wallet addresses as CC result fields. The WALLETS read is a CS_MUTABLE_JSON_V0 LIST/READ operation, not a write.

**SYSTEM wallet resolution pattern**

Policy CCs for SYSTEM authority types (MINT, BURN, POOL, REWARD, SLASH) must resolve system wallets by `wallet_type` filter against the WALLETS store — not by hardcoded wallet address. If the wallet is not found → VIOLATION outcome.

**tx_type literal injection**

Each RB_ carries `tx_type` as a `wf_literal` node binding on the CC_PERSIST_MEMPOOL_TX_V0 step. This is the sole mechanism by which the WF identity becomes the transaction type — no payload field, no runtime branching. Values: TRANSFER, STAKE, UNSTAKE, MINT, BURN, POOL, REWARD, SLASH.

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 0 — Classification | 1_change_request_data_model_v0.md | COMPLETE |
| Stage 1 — Input Elicitation | 1_input_elicitation_data_model_v0.md | COMPLETE |
| Stage 2 — Domain Model Discovery | 2_domain_model_data_model_v0.md | COMPLETE |
| Stage 3 — Analysis Loop | 3_analysis_loop_data_model_v0.md | COMPLETE — SATURATED |
| Stage 4 — Business Model | 4_business_model_data_model_v0.md | COMPLETE |
| Stage 5 — Business Intent | 5_business_intent_data_model_v0.md | COMPLETE |
| Stage 6 — Governance Intent | 6_governance_intent_data_model_v0.md | COMPLETE — APPROVED |
| Stage 6b — Design Intent | 6b_design_intent_data_model_v0.md | COMPLETE — APPROVED |
| Stage 7 — Authoring Plan | 7_authoring_plan_data_model_v0.md | COMPLETE |
| Stage 7 — Authoring Mandate | This document | APPROVED |
| Stage 8 — Authoring Manifest | 8_authoring_manifest_data_model_v0.md | COMPLETE |

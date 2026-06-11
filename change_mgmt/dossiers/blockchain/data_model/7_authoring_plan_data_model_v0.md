# Stage 7 — Authoring Plan: blockchain / data_model
**Stage:** 7 — Authoring Plan
**CR:** 1_change_request_data_model_v0.md
**Status:** COMPLETE
**Feeds:** Authoring Mandate / Implementation

---

## Sequencing Principles

1. **Retirements precede successors** — a retired artifact must carry `status: RETIRED` and `superseded_by` in its protocol source before any successor is compiled. The compiler rejects references to RETIRED artifacts.
2. **Seeds are compiler-independent** — seed files are static JSON, not compiled artifacts. They may be authored in any phase. Sequence here places them first as they establish the bootstrap facts that all other work serves.
3. **Shared CCs before typed WFs** — CC_PERSIST_MEMPOOL_TX_V0 is shared across all 8 typed WFs; it must be updated before any WF is compiled.
4. **IN_ before WF** — each typed WF references its IN_ for admission; IN_ must exist before WF is authored.
5. **Events are independent** — EV_ artifacts carry no runtime compilation dependencies; they may be authored in any phase.
6. **Compile once per phase boundary** — intermediate compiles are optional; the mandatory full compile is at the end.

---

## Phase 0 — Seeds (Bootstrap Facts)

*Seed files are static JSON loaded at bootstrap. No compiler dependency. Author first — these are the facts the system starts from.*

| Step | Action | Artifact | Notes |
|------|--------|----------|-------|
| 0.1 | NEW | `seeds/genesis_actor.json` | GENESIS actor record: actor_id (deterministic), user_type: GENESIS, status: ACTIVE, kyc_verified: true, currency_preference: BACHI, language: en. Owns MINT/BURN/POOL wallets by actor_id reference in system_wallets.json |
| 0.2 | NEW | `seeds/system_wallets.json` | Three system wallet records: MINT (balance: 1000000, status: ACTIVE, actor_id = genesis actor_id), BURN (balance: 0), POOL (balance: 0). Each carries wallet_id, wallet_type, EOA address, nonce: 0, currency: BACHI, network: TESTNET |
| 0.3 | UPDATE | `seeds/register_validator_payload.json` | Remove: node_name, stake, enrollment_status. Add: status (ETH2 9-state initial value), slashed: false, effective_balance, balance, activation_eligibility_epoch, activation_epoch, exit_epoch, withdrawable_epoch |

**Verify:** JSON is valid. genesis_actor actor_id matches actor_id referenced in system_wallets. MINT balance = 1000000. All three system wallet wallet_type values are distinct (MINT, BURN, POOL).

---

## Phase 1 — Retirements

*Each retired artifact must have its protocol source updated before Phase 2 begins. Retire in dependency order — WF first (outermost), then IN, RB, then CCs.*

| Step | Action | Artifact FQDN | Add to Protocol Source |
|------|--------|---------------|------------------------|
| 1.1 | RETIRE | `blockchain::WF_SUBMIT_TRANSACTION_V0` | `status: RETIRED`, `superseded_by: [WF_TRANSFER_V0, WF_STAKE_V0, WF_UNSTAKE_V0, WF_MINT_V0, WF_BURN_V0, WF_POOL_V0, WF_REWARD_V0, WF_SLASH_V0]` |
| 1.2 | RETIRE | `blockchain::IN_TRANSACTION_SUBMITTED_V0` | `status: RETIRED`, `superseded_by: [IN_TRANSFER_V0, IN_STAKE_V0, IN_UNSTAKE_V0, IN_MINT_V0, IN_BURN_V0, IN_POOL_V0, IN_REWARD_V0, IN_SLASH_V0]` |
| 1.3 | RETIRE | `blockchain::RB_SUBMIT_TRANSACTION_V0` | `status: RETIRED`, `superseded_by: [RB_TRANSFER_V0, RB_STAKE_V0, RB_UNSTAKE_V0, RB_MINT_V0, RB_BURN_V0, RB_POOL_V0, RB_REWARD_V0, RB_SLASH_V0]` |
| 1.4 | RETIRE | `blockchain::CC_VALIDATE_TX_STRUCTURE_V0` | `status: RETIRED`, `superseded_by: [IN_TRANSFER_V0, IN_STAKE_V0, IN_UNSTAKE_V0, IN_MINT_V0, IN_BURN_V0, IN_POOL_V0, IN_REWARD_V0, IN_SLASH_V0]` — structural validation absorbed into typed IN_ |
| 1.5 | RETIRE | `blockchain::CC_VALIDATE_TX_POLICY_V0` | `status: RETIRED`, `superseded_by: [CC_VALIDATE_TRANSFER_POLICY_V0, CC_VALIDATE_STAKE_POLICY_V0, CC_VALIDATE_UNSTAKE_POLICY_V0, CC_VALIDATE_MINT_POLICY_V0, CC_VALIDATE_BURN_POLICY_V0, CC_VALIDATE_POOL_POLICY_V0, CC_VALIDATE_REWARD_POLICY_V0, CC_VALIDATE_SLASH_POLICY_V0]` |
| 1.6 | RETIRE | `blockchain::CC_BUILD_ETH_TX_V0` | `status: RETIRED`, `superseded_by: [CT_PURE_GENERATE_ID_V0]` — signing removed; tx_hash from deterministic ID |
| 1.7 | RETIRE | `blockchain::CC_SIGN_TRANSACTION_V0` | `status: RETIRED`, `superseded_by: []` — ECDSA signing removed in KISS demo |
| 1.8 | RETIRE | `blockchain::CC_HASH_TRANSACTION_V0` | `status: RETIRED`, `superseded_by: [CT_PURE_GENERATE_ID_V0]` — Keccak-256 replaced by deterministic ID |

**Verify:** All 8 artifacts carry `status: RETIRED` in protocol source. No active WF references any retired FQDN. Compiler will enforce this after full compile in Phase 6.

---

## Phase 2 — Data Model IN_ Updates

*Update three existing admission intents with enriched field sets. No compiler dependency on Phase 1 retirements — these are independent updates.*

| Step | Action | Artifact FQDN | Changes |
|------|--------|---------------|---------|
| 2.1 | UPDATE | `blockchain::IN_ACTOR_REGISTERED_V0` | Add: `user_type` (enum: INDIVIDUAL, BUSINESS, ORGANIZATION, VALIDATOR, DELEGATOR, INSTITUTIONAL, DEVELOPER, TESTNET, GENESIS; required), `kyc_verified` (boolean; required), `currency_preference` (string; default: BACHI), `language` (string; default: en) |
| 2.2 | UPDATE | `blockchain::IN_WALLET_CREATED_V0` | Replace free `wallet_config` object with governed fields: `wallet_type` (enum: DEFAULT, PRIVATE, BUSINESS, SAVINGS, INVESTMENT, MINT, BURN, POOL; required), `opening_balance` (number; default: 0), `currency` (string; default: BACHI), `network` (string; default: TESTNET). Remove: `wallet_config` free object |
| 2.3 | UPDATE | `blockchain::IN_VALIDATOR_REGISTERED_V0` | Remove: `node_name`, `stake`, `enrollment_status`. Add: `status` (enum: PENDING_INITIALIZED, PENDING_QUEUED, ACTIVE_ONGOING, ACTIVE_EXITING, ACTIVE_SLASHED, EXITED_UNSLASHED, EXITED_SLASHED, WITHDRAWAL_POSSIBLE, WITHDRAWAL_DONE; required), `slashed` (boolean; default: false), `effective_balance` (integer; Gwei; required), `balance` (integer; Gwei; required), `activation_eligibility_epoch` (integer; nullable), `activation_epoch` (integer; nullable), `exit_epoch` (integer; nullable), `withdrawable_epoch` (integer; nullable) |

**Verify:** Each IN_ schema passes compiler lint. Required fields are marked required. Enum values match domain model exactly. No removed field still appears as required.

---

## Phase 3 — Data Model CC Updates

*Update four CCs to persist enriched entity schemas. Depends on Phase 2 IN_ updates.*

| Step | Action | Artifact FQDN | Changes |
|------|--------|---------------|---------|
| 3.1 | UPDATE | `blockchain::CC_WRITE_ACTOR_RECORD_V0` | CT_PURE_ASSEMBLE_RECORD_V0 step: add user_type, kyc_verified, currency_preference, language, last_modified (JIT); inject `status: "PENDING"` as literal constant; inject `created_at` (JIT) |
| 3.2 | UPDATE | `blockchain::CC_CREATE_WALLET_RECORD_V0` | CT_PURE_GENERATE_ID_V0 step: prefix WAL → wallet_id. CT_PURE_ASSEMBLE_RECORD_V0 step: add balance (= opening_balance from payload), nonce: 0 (literal), address = `"0x" + wallet_id[:40]` (KISS formula), currency, network, last_tx_at: null, status: "ACTIVE" (literal). CS_MUTABLE_JSON_V0 step: WRITE to WALLETS store keyed by wallet_id |
| 3.3 | UPDATE | `blockchain::CC_WRITE_VALIDATOR_RECORD_V0` | Add CS_MUTABLE_JSON_V0 LIST step to count VALIDATORS store → validator_index = count + 1. CT_PURE_ASSEMBLE_RECORD_V0 step: add validator_index, status (from payload), slashed, effective_balance, balance, epoch fields, created_at/updated_at. Remove: node_name, stake, enrollment_status |
| 3.4 | UPDATE | `blockchain::CC_FORM_BLOCK_V0` | CT_PURE_GENERATE_ID_V0: prefix BLK, hex output → block_hash. CT_PURE_ASSEMBLE_RECORD_V0: compute epoch = height // 32, block_type = GENESIS if height == 0 else REGULAR, base_fee_per_gas = 1000000000 (constant), status: "PROPOSED" (literal); assemble full enriched block entity with all finality fields (justified_epoch: null, finalized_epoch: null, is_canonical: false at proposal) |

**Verify:** Each CC compiles without errors. Assemble steps reference no field that does not exist in the IN_ or a prior CC result. Literal injections are declared in node bindings (not in CT/CS implementations).

---

## Phase 4 — Structure Review

*Review entity store schema annotations. No authoring expected — this is a verification step.*

| Step | Action | Artifact | Check |
|------|--------|----------|-------|
| 4.1 | REVIEW | `blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0` | Verify entity_stores entries cover: ACTORS, WALLETS, VALIDATORS, BLOCKS, MEMPOOL, BLOCK_EVENTS, TRANSACTION_EVENTS, WALLET_EVENTS. Verify store schema annotations match enriched field sets from Phases 2–3. If annotations are absent or mismatched, UPDATE this artifact to add correct schema annotations |

**Verify:** All five subdomain entity stores are declared. No new stores required by this CR.

---

## Phase 5 — Shared Transaction CC Update

*Update CC_PERSIST_MEMPOOL_TX_V0 before any typed WF is authored. All 8 typed WFs share this CC.*

| Step | Action | Artifact FQDN | Changes |
|------|--------|---------------|---------|
| 5.1 | UPDATE | `blockchain::CC_PERSIST_MEMPOOL_TX_V0` | **Remove from node binding inputs:** signature, data, chain_id, value. **Add to node binding inputs:** tx_type (WF-literal — each calling WF injects its own value), amount (BACHI decimal from policy CC result), memo (from payload, nullable). **Step 1:** CT_PURE_GENERATE_ID_V0 (prefix: TX, hex) → tx_hash. **Step 2:** CT_PURE_ASSEMBLE_RECORD_V0 — assemble full transaction record with execution result fields null (base_fee_per_gas, effective_gas_price, gas_used, total_fee, block_number, block_hash — populated by next CR's finalization WFs). **Step 3:** CS_APPENDONLY_JSONL_V0 — APPEND to MEMPOOL store |

**Verify:** CC compiles. tx_type is declared as a `wf_literal` binding type — it has no default value; each WF node binding must supply it. Removal of signature/data/chain_id/value does not break any remaining WF that references this CC (all callers are being replaced by typed WFs in Phase 8).

---

## Phase 6 — New Type-Specific Policy CCs (8)

*All 8 are independent of each other; author in any order within this phase. Each handles wallet resolution, balance gate, address routing, and output of from_address + to_address.*

| Step | Action | Artifact FQDN | Authority Class | Wallet Resolution | Balance Gate | Address Routing |
|------|--------|---------------|-----------------|-------------------|-------------|-----------------|
| 6.1 | NEW | `blockchain::CC_VALIDATE_TRANSFER_POLICY_V0` | ENDUSER | from_wallet belongs to actor | from_wallet.balance ≥ amount | from = from_wallet.address; to = payload.to_address |
| 6.2 | NEW | `blockchain::CC_VALIDATE_STAKE_POLICY_V0` | ENDUSER | from_wallet belongs to actor | from_wallet.balance ≥ amount | from = from_wallet.address; to = POOL wallet (auto by wallet_type lookup) |
| 6.3 | NEW | `blockchain::CC_VALIDATE_UNSTAKE_POLICY_V0` | ENDUSER | validator_index belongs to actor; to_wallet belongs to actor | POOL staked for validator ≥ amount | from = POOL wallet (auto); to = to_wallet.address |
| 6.4 | NEW | `blockchain::CC_VALIDATE_MINT_POLICY_V0` | SYSTEM | MINT wallet exists | MINT.balance ≥ amount | from = MINT wallet (auto); to = to_wallet.address |
| 6.5 | NEW | `blockchain::CC_VALIDATE_BURN_POLICY_V0` | SYSTEM | from_wallet exists | from_wallet.balance ≥ amount | from = from_wallet.address; to = BURN wallet (auto) |
| 6.6 | NEW | `blockchain::CC_VALIDATE_POOL_POLICY_V0` | SYSTEM | MINT + POOL wallets exist | MINT.balance ≥ amount | from = MINT wallet (auto); to = POOL wallet (auto) |
| 6.7 | NEW | `blockchain::CC_VALIDATE_REWARD_POLICY_V0` | SYSTEM | POOL wallet exists; to_wallet exists | POOL.balance ≥ amount | from = POOL wallet (auto); to = to_wallet.address |
| 6.8 | NEW | `blockchain::CC_VALIDATE_SLASH_POLICY_V0` | SYSTEM | from_wallet (validator) exists | from_wallet.balance ≥ amount | from = from_wallet.address; to = BURN wallet (auto) |

**SYSTEM wallet resolution (all SYSTEM CCs):** Read WALLETS store filtered by wallet_type = MINT / BURN / POOL. Do not hardcode wallet addresses. If wallet not found → VIOLATION outcome.

**Outcomes for all policy CCs:** SUCCESS (with from_address, to_address in output), NOT_FOUND, VIOLATION, BACKEND_ERROR.

**Verify:** Each CC compiles. Output schema carries from_address and to_address. SYSTEM wallet lookup uses wallet_type filter, not address literal. Balance gate returns VIOLATION (not NOT_FOUND) when balance is insufficient.

---

## Phase 7 — New Typed IN_ (8)

*Admission intents for the 8 typed WFs. Each IN_ carries the type-specific field schema from Stage 6b Section 5.*

| Step | Action | Artifact FQDN | Authority Class | Key Schema Points |
|------|--------|---------------|-----------------|-------------------|
| 7.1 | NEW | `blockchain::IN_TRANSFER_V0` | ENDUSER | actor_record.email_registration, from_wallet_id, to_address (required), amount, gas params, memo |
| 7.2 | NEW | `blockchain::IN_STAKE_V0` | ENDUSER | actor_record.email_registration, from_wallet_id, amount, gas params. No to_address (auto-resolved) |
| 7.3 | NEW | `blockchain::IN_UNSTAKE_V0` | ENDUSER | actor_record.email_registration, validator_index, amount, to_wallet_id, gas params. No from_address (auto-resolved) |
| 7.4 | NEW | `blockchain::IN_MINT_V0` | SYSTEM | to_wallet_id, amount, triggered_by. No actor_record. No from_address (auto) |
| 7.5 | NEW | `blockchain::IN_BURN_V0` | SYSTEM | from_wallet_id, amount, triggered_by. No to_address (auto) |
| 7.6 | NEW | `blockchain::IN_POOL_V0` | SYSTEM | amount, triggered_by. No from or to (both auto) |
| 7.7 | NEW | `blockchain::IN_REWARD_V0` | SYSTEM | to_wallet_id, amount, block_hash, triggered_by. No from_address (auto) |
| 7.8 | NEW | `blockchain::IN_SLASH_V0` | SYSTEM | from_wallet_id, validator_index, amount, triggered_by. No to_address (auto) |

**Verify:** Each IN_ schema carries no tx_type field. Gas params (gas_limit, max_fee_per_gas, max_priority_fee_per_gas) present with defaults in ENDUSER types; absent in SYSTEM types. SYSTEM IN_ carry no actor_record field.

---

## Phase 8 — New Typed RB_ (8)

*Runtime bindings map each typed WF's CC nodes to their implementations. One RB_ per WF.*

| Step | Action | Artifact FQDN | Binds To |
|------|--------|---------------|----------|
| 8.1 | NEW | `blockchain::RB_TRANSFER_V0` | WF_TRANSFER_V0 → CC_RESOLVE_ACTOR_ID_V0, CC_VALIDATE_TRANSFER_POLICY_V0, CC_RESERVE_NONCE_V0, CC_PERSIST_MEMPOOL_TX_V0 (tx_type literal: "TRANSFER"), CC_APPEND_TX_EVENT_V0 |
| 8.2 | NEW | `blockchain::RB_STAKE_V0` | WF_STAKE_V0 → CC_RESOLVE_ACTOR_ID_V0, CC_VALIDATE_STAKE_POLICY_V0, CC_RESERVE_NONCE_V0, CC_PERSIST_MEMPOOL_TX_V0 (tx_type literal: "STAKE"), CC_APPEND_TX_EVENT_V0 |
| 8.3 | NEW | `blockchain::RB_UNSTAKE_V0` | WF_UNSTAKE_V0 → CC_RESOLVE_ACTOR_ID_V0, CC_VALIDATE_UNSTAKE_POLICY_V0, CC_RESERVE_NONCE_V0, CC_PERSIST_MEMPOOL_TX_V0 (tx_type literal: "UNSTAKE"), CC_APPEND_TX_EVENT_V0 |
| 8.4 | NEW | `blockchain::RB_MINT_V0` | WF_MINT_V0 → CC_VALIDATE_MINT_POLICY_V0, CC_PERSIST_MEMPOOL_TX_V0 (tx_type literal: "MINT"), CC_APPEND_TX_EVENT_V0 |
| 8.5 | NEW | `blockchain::RB_BURN_V0` | WF_BURN_V0 → CC_VALIDATE_BURN_POLICY_V0, CC_PERSIST_MEMPOOL_TX_V0 (tx_type literal: "BURN"), CC_APPEND_TX_EVENT_V0 |
| 8.6 | NEW | `blockchain::RB_POOL_V0` | WF_POOL_V0 → CC_VALIDATE_POOL_POLICY_V0, CC_PERSIST_MEMPOOL_TX_V0 (tx_type literal: "POOL"), CC_APPEND_TX_EVENT_V0 |
| 8.7 | NEW | `blockchain::RB_REWARD_V0` | WF_REWARD_V0 → CC_VALIDATE_REWARD_POLICY_V0, CC_PERSIST_MEMPOOL_TX_V0 (tx_type literal: "REWARD"), CC_APPEND_TX_EVENT_V0 |
| 8.8 | NEW | `blockchain::RB_SLASH_V0` | WF_SLASH_V0 → CC_VALIDATE_SLASH_POLICY_V0, CC_PERSIST_MEMPOOL_TX_V0 (tx_type literal: "SLASH"), CC_APPEND_TX_EVENT_V0 |

**tx_type literal injection:** Each RB_ carries the tx_type value as a node binding literal on the CC_PERSIST_MEMPOOL_TX_V0 step. This is the mechanism by which the WF identity becomes the transaction type — no payload field, no runtime branching.

**Verify:** Each RB_ references only non-RETIRED CC FQDNs. ENDUSER RBs include CC_RESOLVE_ACTOR_ID_V0 and CC_RESERVE_NONCE_V0 nodes. SYSTEM RBs omit both. tx_type literal is present on the CC_PERSIST_MEMPOOL_TX_V0 binding in all 8 RBs.

---

## Phase 9 — New Typed WFs (8)

*Execution topology declarations. Depend on Phase 7 IN_ and Phase 8 RB_. ENDUSER and SYSTEM patterns from Stage 6b Section 6.*

| Step | Action | Artifact FQDN | Pattern | Subdomain |
|------|--------|---------------|---------|-----------|
| 9.1 | NEW | `blockchain::WF_TRANSFER_V0` | ENDUSER | transaction |
| 9.2 | NEW | `blockchain::WF_STAKE_V0` | ENDUSER | transaction |
| 9.3 | NEW | `blockchain::WF_UNSTAKE_V0` | ENDUSER | transaction |
| 9.4 | NEW | `blockchain::WF_MINT_V0` | SYSTEM | transaction |
| 9.5 | NEW | `blockchain::WF_BURN_V0` | SYSTEM | transaction |
| 9.6 | NEW | `blockchain::WF_POOL_V0` | SYSTEM | transaction |
| 9.7 | NEW | `blockchain::WF_REWARD_V0` | SYSTEM | transaction |
| 9.8 | NEW | `blockchain::WF_SLASH_V0` | SYSTEM | transaction |

**ENDUSER topology:** IN → CC_RESOLVE_ACTOR_ID_V0 → CC_VALIDATE_\<TYPE\>_POLICY_V0 → CC_RESERVE_NONCE_V0 → CC_PERSIST_MEMPOOL_TX_V0 → CC_APPEND_TX_EVENT_V0 → EXIT

**SYSTEM topology:** IN → CC_VALIDATE_\<TYPE\>_POLICY_V0 → CC_PERSIST_MEMPOOL_TX_V0 → CC_APPEND_TX_EVENT_V0 → EXIT

**JSONPath input resolution:** each WF node resolves inputs via `$.results.<CC_CODE>.<field>` — no ambient payload access beyond the first CC in each chain.

**Verify:** Each WF references its correct IN_ and RB_. WF subdomain field = "transaction". ENDUSER WFs contain 5 CC nodes. SYSTEM WFs contain 3 CC nodes. No WF references any RETIRED artifact FQDN.

---

## Phase 10 — New Events (5)

*Declared this CR; emitted by next CR's consensus finalization WFs. No runtime compilation dependency — author independently of Phases 1–9.*

| Step | Action | Artifact FQDN | Subdomain | Payload Schema |
|------|--------|---------------|-----------|----------------|
| 10.1 | NEW | `blockchain::EV_BLOCK_ATTESTED_V0` | consensus_pos | block_hash, slot, epoch, attestation_count, timestamp |
| 10.2 | NEW | `blockchain::EV_BLOCK_FINALIZED_V0` | consensus_pos | block_hash, height, slot, epoch, finalized_epoch, transaction_count, timestamp |
| 10.3 | NEW | `blockchain::EV_BLOCK_COMMITTED_V0` | consensus_pos | block_hash, height, is_canonical, timestamp |
| 10.4 | NEW | `blockchain::EV_TX_FINALIZED_V0` | transaction | tx_hash, tx_type, from_address, to_address, amount, total_fee, block_hash, timestamp |
| 10.5 | NEW | `blockchain::EV_BALANCE_RECONCILED_V0` | wallet | wallet_id, actor_id, previous_balance, delta, new_balance, tx_hash, timestamp |

**Verify:** Each EV_ carries a version suffix. Subdomain routing is declared. Payload schema fields match what the next CR's emitting WFs will need — these schemas must be stable before the consensus finalization CR authors its WFs.

---

## Phase 11 — Compile and Verify

*Run after all Phases 0–10 are complete.*

```bash
# Per-structure compile (blockchain only)
python -m pgs_compiler.cli compile --structure STRUCTURE_BUILD_BLOCKCHAIN_CONFIG_V0

# Cross-structure vocabulary aggregation (after blockchain compile passes)
python -m pgs_compiler.cli compile --structure STRUCTURE_BUILD_VOCABULARY_AGGREGATE_V0

# Full build: sync artifacts + conformance tests + mark snapshot valid
python -m pgs_compiler.cli build --workspace /abs/path/to/pgs_workspace
```

**Compiler success criteria:**
- All 8 RETIRED artifacts carry `status: RETIRED` — compiler emits retirement acknowledgment
- No active artifact references a RETIRED FQDN — compiler raises dependency error if violated
- All 8 typed WFs resolve their IN_, RB_, and CC graph without missing artifact errors
- Conformance tests pass for all enriched IN_ schemas (field types, required fields, enum values)
- Vocabulary aggregate includes all new FQDNs

---

## Authoring Checklist Summary

| Phase | Items | Content |
|-------|-------|---------|
| Phase 0 — Seeds | 3 | genesis_actor.json (NEW), system_wallets.json (NEW), register_validator_payload.json (UPDATE) |
| Phase 1 — Retirements | 8 | WF_SUBMIT_TRANSACTION_V0 … CC_HASH_TRANSACTION_V0 |
| Phase 2 — Data Model IN_ | 3 | IN_ACTOR_REGISTERED_V0, IN_WALLET_CREATED_V0, IN_VALIDATOR_REGISTERED_V0 |
| Phase 3 — Data Model CC | 4 | CC_WRITE_ACTOR_RECORD_V0, CC_CREATE_WALLET_RECORD_V0, CC_WRITE_VALIDATOR_RECORD_V0, CC_FORM_BLOCK_V0 |
| Phase 4 — Structure Review | 1 | STRUCTURE_BLOCKCHAIN_STORAGE_V0 |
| Phase 5 — Shared Tx CC | 1 | CC_PERSIST_MEMPOOL_TX_V0 |
| Phase 6 — Policy CCs | 8 | CC_VALIDATE_TRANSFER_POLICY_V0 … CC_VALIDATE_SLASH_POLICY_V0 |
| Phase 7 — Typed IN_ | 8 | IN_TRANSFER_V0 … IN_SLASH_V0 |
| Phase 8 — Typed RB_ | 8 | RB_TRANSFER_V0 … RB_SLASH_V0 |
| Phase 9 — Typed WFs | 8 | WF_TRANSFER_V0 … WF_SLASH_V0 |
| Phase 10 — Events | 5 | EV_BLOCK_ATTESTED_V0 … EV_BALANCE_RECONCILED_V0 |
| Phase 11 — Compile | — | Full compiler build + conformance |
| **Total** | **57** | **8 retirements + 8 updates + 29 new artifacts + 3 seed actions + 1 review** |

---

## Critical Path

```
Phase 0 (Seeds) ──────────────────────────────────────────────→ independent
Phase 1 (Retirements)
    └→ Phase 2 (IN_ updates) ─→ Phase 3 (CC updates) ─→ Phase 4 (Structure Review)
    └→ Phase 5 (CC_PERSIST_MEMPOOL_TX_V0)
          └→ Phase 6 (Policy CCs)
                └→ Phase 7 (Typed IN_)
                      └→ Phase 8 (Typed RB_)
                            └→ Phase 9 (Typed WFs)
Phase 10 (Events) ────────────────────────────────────────────→ independent
All phases complete → Phase 11 (Compile + Verify)
```

Phases 0 and 10 are off the critical path. The critical path runs: Phase 1 → Phase 5 → Phase 6 → Phase 7 → Phase 8 → Phase 9 → Phase 11.

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 0 — Classification | 1_change_request_data_model_v0.md | COMPLETE |
| Stage 1 — Input Elicitation | 1_input_elicitation_data_model_v0.md | COMPLETE |
| Stage 2 — Domain Model Discovery | 2_domain_model_data_model_v0.md | COMPLETE — KISS revision |
| Stage 3 — Analysis Loop | 3_analysis_loop_data_model_v0.md | COMPLETE — SATURATED |
| Stage 4 — Business Model | 4_business_model_data_model_v0.md | COMPLETE |
| Stage 5 — Business Intent | 5_business_intent_data_model_v0.md | COMPLETE |
| Stage 6 — Governance Intent | 6_governance_intent_data_model_v0.md | COMPLETE — APPROVED |
| Stage 6b — Design Intent | 6b_design_intent_data_model_v0.md | COMPLETE — APPROVED |
| Stage 7 — Authoring Plan | This document | COMPLETE |
| Authoring Mandate | Pending | — |

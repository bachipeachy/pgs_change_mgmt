# Stage 5 — Business Intent: blockchain / data_model
**Stage:** 5 — Business Intent
**CR:** 1_change_request_data_model_v0.md
**Status:** COMPLETE
**Feeds:** Stage 6 — Governance Intent

---

## Purpose

Stage 5 translates the 7 business capabilities from Stage 4 into artifact-level obligations. Each obligation names what MUST be authored or updated, states the complete target schema (not just the delta), and identifies which BC it satisfies. This document is the authoritative input to Stage 6 (Governance Intent) and Stage 6b (Design Intent).

**Scope boundary:** This CR authors data model enrichments only — IN_ schema updates, entity store enrichments, new events, seed files, and payload defect fixes. The four missing consensus workflows (WF_ATTEST_BLOCK_V0, WF_FINALIZE_BLOCK_V0, WF_COMMIT_BLOCK_V0, WF_RECONCILE_BALANCES_V0) are deferred to the consensus finalization CR.

---

## Intent 1 — Identity Subdomain (BC-1)

### IN_ACTOR_REGISTERED_V0 — UPDATE

**Satisfies:** BC-1 (Register an Actor with a Governed Role and Status)

**Change type:** UPDATE — add governed fields to existing intent schema

**Current state:** 3 input fields — first_name, last_name, email_registration. No role, no lifecycle status, no KYC tier, no preference fields.

**Target state — Complete input schema after this CR:**

| Field | Type | Required | Constraint | Description |
|-------|------|----------|------------|-------------|
| actor_record | object | YES | — | Proposed actor registration payload |
| └ first_name | string | YES | — | Given name |
| └ last_name | string | YES | — | Family name |
| └ email_registration | string | YES | format: email | Immutable registration email |
| └ user_type | string | YES | enum: INDIVIDUAL, BUSINESS, ORGANIZATION, VALIDATOR, DELEGATOR, INSTITUTIONAL, DEVELOPER, TESTNET, GENESIS | Actor role classification |
| └ kyc_verified | boolean | YES | — | Whether identity has been verified |
| └ currency_preference | string | NO | default: BACHI | Preferred currency denomination |
| └ language | string | NO | default: en | Preferred language |

**Outcomes (unchanged):**

| Outcome | Description |
|---------|-------------|
| ACK | Actor record accepted — all required fields present, user_type valid enum, email format valid |
| NACK | Actor record rejected — missing required fields, invalid user_type, invalid email format |

**Entity store obligation:** CC_WRITE_ACTOR_RECORD_V0 must persist user_type, status (set to PENDING at write time), kyc_verified, currency_preference, language, last_modified in the actor record. status is NOT an intent input — it is assigned by the workflow at write time.

---

## Intent 2 — Wallet Subdomain (BC-2)

### IN_WALLET_CREATED_V0 — UPDATE

**Satisfies:** BC-2 (Create a Wallet with Real Account State)

**Change type:** UPDATE — replace unstructured wallet_config with governed field set; govern wallet_type as controlled enum

**Current state:** actor_record (object), wallet_type (free string, default "standard"), wallet_config (free object — name, currency, metadata). No balance, no nonce, no address, no governed type enum.

**Target state — Complete input schema after this CR:**

| Field | Type | Required | Constraint | Description |
|-------|------|----------|------------|-------------|
| actor_record | object | YES | — | Actor identity data for resolution |
| └ email_registration | string | YES | format: email | Used to resolve actor_id |
| wallet_type | string | YES | enum: DEFAULT, PRIVATE, BUSINESS, SAVINGS, INVESTMENT, MINT, BURN, POOL | Governed wallet classification |
| name | string | NO | — | Human-readable wallet label |
| currency | string | NO | default: BACHI | Currency denomination |
| network | string | NO | default: TESTNET | Network identifier |
| opening_balance | number | NO | default: 0.0, minimum: 0.0 | Initial balance in BACHI (seed-driven for system wallets) |

**Outcomes (unchanged):**

| Outcome | Description |
|---------|-------------|
| ACK | Wallet creation initiated — actor resolved, wallet_type valid |
| NACK | Wallet creation rejected — actor not found, invalid wallet_type |

**Entity store obligation:** CC_CREATE_WALLET_RECORD_V0 must persist wallet_id (JIT), actor_id (resolved), name, wallet_type, status (ACTIVE), network, currency, balance (from opening_balance or 0.0), nonce (0), address (JIT — deterministic EOA string, 0x-prefixed), created_at (JIT), last_modified (JIT), last_tx_at (null at creation).

---

## Intent 3 — Transaction Subdomain (BC-3)

### IN_TRANSACTION_SUBMITTED_V0 — UPDATE (includes defect fix)

**Satisfies:** BC-3 (Submit a Typed Transaction with a Full Gas Model)

**Change type:** UPDATE — add tx_type governed enum; restructure to BACHI/KISS model; remove mnemonic and data fields (not needed for KISS demo); make to_address optional for asymmetric transaction types

**Current state:** 9 fields — actor_record, wallet_id, to_address (required), value (wei string), gas_limit, max_fee_per_gas, max_priority_fee_per_gas, data, mnemonic. No tx_type. Summary hardcodes "ETH transaction."

**Target state — Complete input schema after this CR:**

| Field | Type | Required | Constraint | Description |
|-------|------|----------|------------|-------------|
| actor_record | object | YES | — | Actor identity data for resolution |
| └ email_registration | string | YES | format: email | Used to resolve actor_id |
| tx_type | string | YES | enum: TRANSFER, MINT, BURN, POOL, STAKE, UNSTAKE, REWARD, SLASH | Transaction classification — governs validation rules and routing |
| wallet_id | string | CONDITIONAL | required for TRANSFER, BURN, POOL, STAKE, UNSTAKE; null for MINT, REWARD, SLASH | Source wallet identifier |
| to_address | string | CONDITIONAL | required for TRANSFER, MINT, POOL, STAKE, UNSTAKE, REWARD; null for SLASH, BURN | Destination address (0x-prefixed EOA) |
| amount | number | YES | minimum: 0.0 | Transfer value in BACHI (replaces wei-based "value") |
| currency | string | NO | default: BACHI | Denomination |
| gas_limit | integer | NO | default: 21000 | Gas limit declared by submitter |
| max_fee_per_gas | string | NO | default: "20000000000" | Max fee per gas in wei |
| max_priority_fee_per_gas | string | NO | default: "1000000000" | Tip to block proposer in wei |
| memo | string | NO | — | Optional human note |

**Dropped from current intent:** mnemonic (no signing in KISS demo), data (contract call data — not needed), value (replaced by amount in BACHI decimal).

**Outcomes (unchanged):**

| Outcome | Description |
|---------|-------------|
| ACK | Transaction admitted — tx_type valid, required addresses present for tx_type, amount positive |
| NACK | Transaction rejected — missing required fields, invalid tx_type, missing address for type |

**Entity store obligation:** CC_PERSIST_TRANSACTION_TO_MEMPOOL_V0 must persist tx_hash (JIT), tx_type (from payload — defect fix), from_address (derived from wallet lookup or null for system-sourced), to_address (from payload or null for protocol-routed), amount, currency, network, nonce (reserved atomically or null for system txs), gas_limit, max_fee_per_gas, max_priority_fee_per_gas, status (PENDING), memo, created_at (JIT).

**Execution result fields** (set by execution CCs, not by intent): base_fee_per_gas, effective_gas_price, gas_used, total_fee, block_number, block_hash, final status (SUBMITTED → INCLUDED → FINALIZED).

---

## Intent 4 — Consensus PoS Subdomain: Validator (BC-6)

### IN_VALIDATOR_REGISTERED_V0 — UPDATE (includes defect fix)

**Satisfies:** BC-6 (Observe Validator ETH2 Lifecycle Status)

**Change type:** UPDATE — remove redundant fields (node_name, stake, enrollment_status); add 9-state status enum, epoch fields, slashed flag, balance

**Current state:** 7 fields — actor_id, pubkey, withdrawal_credentials, effective_balance, node_name (redundant), stake (redundant), enrollment_status (3-state: ACTIVE, INACTIVE, EXCLUDED).

**Target state — Complete input schema after this CR:**

| Field | Type | Required | Constraint | Description |
|-------|------|----------|------------|-------------|
| validator_record | object | YES | — | Proposed validator registration payload |
| └ actor_id | string | YES | — | PGS actor ID — must exist in actor registry |
| └ pubkey | string | YES | format: hex, prefix: 0x | BLS12-381 signing public key — immutable |
| └ withdrawal_credentials | string | YES | format: hex, prefix: 0x | Hash of withdrawal destination address |
| └ effective_balance | integer | YES | minimum: 32000000000 | Declared stake in Gwei (32 ETH minimum) |
| └ status | string | YES | enum: PENDING_INITIALIZED, PENDING_QUEUED, ACTIVE_ONGOING, ACTIVE_EXITING, ACTIVE_SLASHED, EXITED_UNSLASHED, EXITED_SLASHED, WITHDRAWAL_POSSIBLE, WITHDRAWAL_DONE | ETH2 lifecycle status — set by payload at registration |
| └ slashed | boolean | NO | default: false | Whether validator has been penalized |
| └ activation_eligibility_epoch | integer | NO | — | Epoch when deposit was processed |
| └ activation_epoch | integer | NO | — | Epoch when validator became active |
| └ exit_epoch | integer | NO | — | Epoch when validator began exiting |
| └ withdrawable_epoch | integer | NO | — | Epoch when funds can be withdrawn |
| └ balance | integer | NO | — | Current balance in Gwei (defaults to effective_balance at registration) |

**Removed from current intent:** node_name (no governance meaning — single node), stake (redundant with effective_balance), enrollment_status (replaced by 9-state status enum).

**Outcomes (unchanged):**

| Outcome | Description |
|---------|-------------|
| ACK | Payload admitted — actor exists, pubkey format valid, effective_balance meets minimum, status valid enum |
| NACK | Payload rejected — missing required fields, invalid pubkey, effective_balance below minimum, invalid status |

**Entity store obligation:** CC_WRITE_VALIDATOR_RECORD_V0 must persist validator_index (JIT — sequential), actor_id, pubkey, withdrawal_credentials, effective_balance, status, slashed, epoch fields, balance, created_at (JIT), updated_at (JIT). validator_index replaces any internal auto-key.

**Seed payload obligation:** seeds/register_validator_payload.json must be updated — remove node_name, stake, enrollment_status; add status (PENDING_INITIALIZED), slashed (false), epoch fields.

---

## Intent 5 — Consensus PoS Subdomain: Block (BC-5)

### IN_BLOCK_PROPOSED_V0 — NO CHANGE

**Satisfies:** BC-5 (Observe Block Finality State)

**Change type:** NO CHANGE to intent schema — IN_BLOCK_PROPOSED_V0 is a consensus round trigger (round_number, triggered_by, timestamp). This is correct and sufficient as a trigger interface.

**Enrichment obligation:** The block ENTITY written by CC_FORM_BLOCK_V0 must carry the full KISS enriched schema. This is a CC-level obligation, not an IN_ obligation.

**Entity store obligation:** CC_FORM_BLOCK_V0 must write a block record carrying: block_hash (JIT), parent_hash, height, slot, epoch (height / 32), block_type (GENESIS for height=0, REGULAR otherwise), proposer_index, gas_limit, gas_used, base_fee_per_gas, total_fees, transaction_count, transactions (list of tx_hash), status (PROPOSED), is_canonical (true), justified_epoch (null), finalized_epoch (null), timestamp, created_at (JIT).

**Dropped from current block entity:** state_root, transactions_root, receipts_root (Merkle/Verkle — too complex for KISS), attestations, randao_reveal, block_size, justified/finalized boolean flags (redundant with status).

---

## Intent 6 — Token Economy Bootstrap (BC-4)

### seeds/genesis_actor.json — NEW

**Satisfies:** BC-4 (Bootstrap the Closed Token Economy)

**Change type:** NEW seed file — GENESIS actor record

**Required content:**

| Field | Value |
|-------|-------|
| actor_id | deterministic (matches system wallet owner) |
| first_name | "Genesis" |
| last_name | "System" |
| email_registration | "genesis@bachicoin.local" |
| user_type | "GENESIS" |
| status | "ACTIVE" |
| kyc_verified | true |
| currency_preference | "BACHI" |
| language | "en" |

**Pattern:** Consistent with seeds/license_facts.json precedent — static seed, loaded by bootstrap, not written by a workflow.

---

### seeds/system_wallets.json — NEW

**Satisfies:** BC-4 (Bootstrap the Closed Token Economy)

**Change type:** NEW seed file — MINT, BURN, POOL system wallet records

**Required content — three wallet records:**

| wallet_type | name | balance | nonce | status | actor_id |
|-------------|------|---------|-------|--------|----------|
| MINT | "Genesis Mint" | 1000000.0 | 0 | ACTIVE | genesis actor_id |
| BURN | "Genesis Burn" | 0.0 | 0 | ACTIVE | genesis actor_id |
| POOL | "Genesis Pool" | 0.0 | 0 | ACTIVE | genesis actor_id |

Each record carries: wallet_id (deterministic), actor_id (GENESIS actor), name, wallet_type, status, network (TESTNET), currency (BACHI), balance, nonce, address (deterministic EOA, 0x-prefixed), created_at, last_modified (null), last_tx_at (null).

**Total supply invariant:** MINT.balance = 1,000,000 BACHI. This is the entire initial supply. Funds move from MINT to user wallets via TRANSFER transactions. BURN is a permanent sink. POOL supports liquidity. Supply is conserved — no creation outside MINT seed.

---

## Intent 7 — New Event Declarations (BC-7)

### Five New Events — NEW

**Satisfies:** BC-7 (Govern State-Change Events for the Token Economy)

**Change type:** NEW — five event artifacts declared. These events are declared in this CR and emitted by the consensus finalization and reconciliation workflows delivered in the next CR.

| Event Code | Subdomain | Trigger | Payload Fields |
|------------|-----------|---------|----------------|
| EV_BLOCK_ATTESTED_V0 | consensus_pos | WF_ATTEST_BLOCK_V0 (next CR) | block_hash, slot, epoch, attestation_count, timestamp |
| EV_BLOCK_FINALIZED_V0 | consensus_pos | WF_FINALIZE_BLOCK_V0 (next CR) | block_hash, height, slot, epoch, finalized_epoch, transaction_count, timestamp |
| EV_BLOCK_COMMITTED_V0 | consensus_pos | WF_COMMIT_BLOCK_V0 (next CR) | block_hash, height, is_canonical, timestamp |
| EV_TX_FINALIZED_V0 | transaction | WF_RECONCILE_BALANCES_V0 (next CR) | tx_hash, tx_type, from_address, to_address, amount, total_fee, block_hash, timestamp |
| EV_BALANCE_RECONCILED_V0 | wallet | WF_RECONCILE_BALANCES_V0 (next CR) | wallet_id, actor_id, previous_balance, delta, new_balance, tx_hash, timestamp |

**Declaration obligation:** Each event must be declared as a governed EV_ artifact with its code, subdomain, summary, and payload schema. Emitter workflows are marked as "next CR" in the event declaration notes.

---

## Payload Defect Fixes

### Defect Fix 1 — CC_VALIDATE_TRANSACTION_POLICY_V0

**Gap reference:** G3 / Finding Set D

**Current defect:** tx_type field is hardcoded as the string "ETH" inside the CC implementation. The field is not read from the payload.

**Required fix:** CC_VALIDATE_TRANSACTION_POLICY_V0 must read tx_type from the transaction payload (`$.tx_record.tx_type` or equivalent JSONPath) and apply type-specific validation rules:
- TRANSFER: requires wallet_id, to_address, amount > 0
- MINT: no wallet_id required (system-sourced); requires to_address
- BURN: requires wallet_id (source); no to_address
- REWARD: no wallet_id required; requires to_address
- SLASH: requires wallet_id (victim); no to_address
- STAKE, UNSTAKE: requires wallet_id, to_address (stake pool wallet)
- POOL: requires wallet_id, to_address

### Defect Fix 2 — CC_PERSIST_TRANSACTION_TO_MEMPOOL_V0

**Gap reference:** G3 / Finding Set D

**Current defect:** tx_type is hardcoded as "ETH" in the transaction record written to the mempool store.

**Required fix:** CC_PERSIST_TRANSACTION_TO_MEMPOOL_V0 must write tx_type from the validated payload (propagated via CC result chain from upstream validation CC) into the persisted transaction record.

### Defect Fix 3 — IN_TRANSACTION_SUBMITTED_V0 summary text

**Current defect:** Summary reads "Submit an ETH transaction from a wallet." This is semantically incorrect — this is a BACHI typed transaction intent.

**Required fix:** Summary updated to "Submit a typed BACHI transaction from a wallet."

---

## Authoring Obligation Summary

| # | Artifact | Action | BC | Subdomain |
|---|----------|--------|----|-----------|
| 1 | IN_ACTOR_REGISTERED_V0 | UPDATE — add user_type, kyc_verified, currency_preference, language | BC-1 | identity |
| 2 | CC_WRITE_ACTOR_RECORD_V0 | UPDATE — persist new fields; assign status=PENDING at write | BC-1 | identity |
| 3 | IN_WALLET_CREATED_V0 | UPDATE — governed wallet_type enum, opening_balance, address, nonce | BC-2 | wallet |
| 4 | CC_CREATE_WALLET_RECORD_V0 | UPDATE — persist full wallet entity (balance, nonce, address, last_tx_at) | BC-2 | wallet |
| 5 | IN_TRANSACTION_SUBMITTED_V0 | UPDATE — add tx_type enum, amount (BACHI), optional to_address; remove mnemonic, data | BC-3 | transaction |
| 6 | CC_VALIDATE_TRANSACTION_POLICY_V0 | FIX — read tx_type from payload; apply type-specific validation rules | BC-3 | transaction |
| 7 | CC_PERSIST_TRANSACTION_TO_MEMPOOL_V0 | FIX — write tx_type from payload (not hardcoded "ETH") | BC-3 | transaction |
| 8 | seeds/genesis_actor.json | NEW — GENESIS actor seed record | BC-4 | identity |
| 9 | seeds/system_wallets.json | NEW — MINT (1,000,000 BACHI), BURN (0), POOL (0) seed records | BC-4 | wallet |
| 10 | CC_FORM_BLOCK_V0 | UPDATE — write enriched block entity (slot, epoch, block_type, proposer_index, finality fields) | BC-5 | consensus_pos |
| 11 | IN_VALIDATOR_REGISTERED_V0 | UPDATE — replace enrollment_status/node_name/stake with 9-state status, epoch fields, slashed, balance | BC-6 | consensus_pos |
| 12 | CC_WRITE_VALIDATOR_RECORD_V0 | UPDATE — persist enriched validator entity | BC-6 | consensus_pos |
| 13 | seeds/register_validator_payload.json | UPDATE — remove node_name, stake, enrollment_status; add status, slashed, epoch fields | BC-6 | consensus_pos |
| 14 | EV_BLOCK_ATTESTED_V0 | NEW — declare event artifact | BC-7 | consensus_pos |
| 15 | EV_BLOCK_FINALIZED_V0 | NEW — declare event artifact | BC-7 | consensus_pos |
| 16 | EV_BLOCK_COMMITTED_V0 | NEW — declare event artifact | BC-7 | consensus_pos |
| 17 | EV_TX_FINALIZED_V0 | NEW — declare event artifact | BC-7 | transaction |
| 18 | EV_BALANCE_RECONCILED_V0 | NEW — declare event artifact | BC-7 | wallet |

**Count:** 5 IN_/CC_ updates, 2 CC defect fixes, 3 seed files (2 new, 1 updated), 5 new events. **Total: 18 authoring obligations.**

---

## Stage 5 Gate

**Gate passed.** All 7 business capabilities translate to named, bounded artifact obligations. Each obligation carries: artifact code, action (NEW / UPDATE / FIX), complete target schema, and BC reference. No obligation is ambiguous about what must be authored.

**Proceed to Stage 6 — Governance Intent.**

---

## Amendments

**Status:** Post-authoring retroactive fix — Option B (amendment section added; approved content above unchanged)
**Source of truth:** 8_authoring_manifest_data_model_v0.md (Sections 1, 2, 7) and 6b_design_intent_data_model_v0.md (Design Pivot Record)

The following items became inaccurate after the Design Pivot was approved during Stage 6b review. All other Business Intent content (identity, wallet, consensus_pos, events, seeds) is unaffected.

---

### Amendment A — Transaction type is WF identity, not a payload field

**BI location:** Intent 3 — `IN_TRANSACTION_SUBMITTED_V0 — UPDATE` — describes a single intent with `tx_type` as an enum field governing which validation rules apply.

**As-built:** `IN_TRANSACTION_SUBMITTED_V0` was RETIRED. The Design Pivot replaced the unified intent + WF approach with **8 typed transaction workflows** — one per transaction type:

| WF | IN_ | Intent |
|----|-----|--------|
| `WF_TRANSFER_V0` | `IN_TRANSFER_V0` | ENDUSER-initiated peer transfer |
| `WF_STAKE_V0` | `IN_STAKE_V0` | ENDUSER stake deposit |
| `WF_UNSTAKE_V0` | `IN_UNSTAKE_V0` | ENDUSER unstake withdrawal |
| `WF_MINT_V0` | `IN_MINT_V0` | SYSTEM mint to user wallet |
| `WF_BURN_V0` | `IN_BURN_V0` | ENDUSER burn (permanent sink) |
| `WF_POOL_V0` | `IN_POOL_V0` | SYSTEM pool liquidity deposit |
| `WF_REWARD_V0` | `IN_REWARD_V0` | SYSTEM validator reward |
| `WF_SLASH_V0` | `IN_SLASH_V0` | SYSTEM validator slash |

**Why:** `tx_type` as a payload field embeds routing intent in data — the WF cannot enforce type-specific topology at compile time without runtime branching. Making each type an explicit WF moves the routing into the governance layer. The WF identity IS the type; no payload field is needed to select the execution path.

**Corrected business intent for BC-3:** Each transaction type MUST be expressed as a separate governed workflow with its own typed intent schema. Type-specific field requirements, address nullability, and policy validation are declared in the typed WF topology, not selected by a payload enum field.

---

### Amendment B — Defect Fix sections name retired artifacts

**BI location:** Section "Payload Defect Fixes" — Defect Fix 1 names `CC_VALIDATE_TRANSACTION_POLICY_V0`; Defect Fix 2 names `CC_PERSIST_TRANSACTION_TO_MEMPOOL_V0`; Defect Fix 3 names `IN_TRANSACTION_SUBMITTED_V0` summary text.

**As-built:**
- `CC_VALIDATE_TRANSACTION_POLICY_V0` — RETIRED; replaced by 8 typed `CC_VALIDATE_<TYPE>_POLICY_V0` CCs
- `CC_PERSIST_TRANSACTION_TO_MEMPOOL_V0` — RETIRED (old name); artifact renamed `CC_PERSIST_MEMPOOL_TX_V0` and updated to be tx_type-aware
- `IN_TRANSACTION_SUBMITTED_V0` — RETIRED; 8 typed INs replace it

**Governance intent preserved:** The defect root causes described in the Defect Fix sections remain correct — hardcoded type strings are governed violations; type must be derived from the governed artifact, not free text. In the as-built system, this constraint is enforced structurally: the WF identity determines the type, so no CC can hardcode or misread it.

---

### Amendment C — Authoring Obligation Summary rows 5–7 are stale

**BI location:** Authoring Obligation Summary — rows 5, 6, 7:
- Row 5: `IN_TRANSACTION_SUBMITTED_V0` UPDATE
- Row 6: `CC_VALIDATE_TRANSACTION_POLICY_V0` FIX
- Row 7: `CC_PERSIST_TRANSACTION_TO_MEMPOOL_V0` FIX

**As-built transaction subdomain obligations (replacing rows 5–7):**

| # | Artifact | Action | BC |
|---|----------|--------|----|
| 5a–5h | `IN_TRANSFER/STAKE/UNSTAKE/MINT/BURN/POOL/REWARD/SLASH_V0` | NEW — 8 typed intents | BC-3 |
| 6a–6h | `CC_VALIDATE_<TYPE>_POLICY_V0` (8 artifacts) | NEW — typed policy CCs | BC-3 |
| 7 | `CC_PERSIST_MEMPOOL_TX_V0` | UPDATE (renamed from CC_PERSIST_TRANSACTION_TO_MEMPOOL_V0) | BC-3 |
| 7b | `CC_GENERATE_TX_ID_V0` | NEW (unplanned) — BACHI-native tx_id/tx_hash generation | BC-3 |
| retired | `IN_TRANSACTION_SUBMITTED_V0`, `CC_VALIDATE_TRANSACTION_POLICY_V0`, `CC_PERSIST_TRANSACTION_TO_MEMPOOL_V0`, `WF_SUBMIT_TRANSACTION_V0`, `RB_SUBMIT_TRANSACTION_V0`, `CC_VALIDATE_TX_STRUCTURE_V0`, `CC_VALIDATE_TX_POLICY_V0`, `CC_BUILD_ETH_TX_V0`, `CC_SIGN_TRANSACTION_V0`, `CC_HASH_TRANSACTION_V0` | RETIRE | BC-3 |

Total transaction subdomain artifact actions: 8 retirements + 17 new/updated (vs. 3 in original summary).

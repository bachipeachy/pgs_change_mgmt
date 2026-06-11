# Stage 2 — Domain Model Discovery: blockchain / data_model
**Stage:** 2 — Domain Model Discovery
**CR:** 1_change_request_data_model_v0.md
**Status:** COMPLETE — revised post-BachiCoin review (KISS)
**Feeds:** Stage 3 — Analysis Loop

---

## 1. Business Entities

### Actor (Identity Subdomain)
A participant in the blockchain system — individual, business, validator, or delegator. An actor has a verified identity, a role classification, and a lifecycle status. An actor is the prerequisite for all other entities — you cannot have a wallet, transaction, or validator record without a registered actor.

| Attribute | Description |
|-----------|-------------|
| actor_id | Deterministic unique identifier (JIT) |
| first_name | Given name |
| last_name | Family name |
| email_registration | Immutable registration email |
| user_type | Role: INDIVIDUAL, BUSINESS, ORGANIZATION, VALIDATOR, DELEGATOR, INSTITUTIONAL, DEVELOPER, TESTNET, GENESIS |
| status | Lifecycle: ACTIVE, INACTIVE, SUSPENDED, PENDING, VERIFIED, DELETED |
| kyc_verified | Boolean — whether identity has been verified |
| currency_preference | Preferred currency denomination (BACHI default) |
| language | Preferred language (en default) |
| created_at | Registration timestamp (JIT) |
| last_modified | Last update timestamp (JIT) |

**Dropped (KISS):** total_balance (computed view), contact fields (phone, country, address — profile CR), auth fields (two_factor_enabled, email_verified), validator stake fields (belong in validator subdomain).

---

### Wallet (Wallet Subdomain)
An account within the system that holds a balance and can send or receive value. Every wallet belongs to one actor. System wallets (MINT, BURN, POOL) belong to the GENESIS actor. A wallet's balance and nonce constitute its full account state.

| Attribute | Description |
|-----------|-------------|
| wallet_id | Deterministic unique identifier (JIT) |
| actor_id | Owning actor reference |
| name | Human-readable wallet label |
| wallet_type | Classification: DEFAULT, PRIVATE, BUSINESS, SAVINGS, INVESTMENT, MINT, BURN, POOL |
| status | Lifecycle: ACTIVE, INACTIVE, SUSPENDED |
| network | Network: TESTNET |
| currency | Denomination: BACHI |
| balance | Current balance in BACHI (updated by reconciliation process) |
| nonce | Transaction count — prevents replay |
| address | Single EOA address (0x-prefixed) |
| created_at | Creation timestamp (JIT) |
| last_modified | Last update timestamp (JIT) |
| last_tx_at | Timestamp of last transaction affecting this wallet |

**Dropped (KISS):** security_type (all HOT on TESTNET), HD address map with derivation paths (deferred), public_key (not needed for demo), metadata.

---

### Transaction (Transaction Subdomain)
A value transfer or system operation. A transaction has a type, a gas fee model, and a lifecycle from submission through mempool persistence to block inclusion and finalization. from_address and to_address are conditionally required — system transactions (REWARD, MINT) have no from; SLASH and BURN have no to (protocol routes to system wallet).

| Attribute | Description |
|-----------|-------------|
| tx_hash | Deterministic hash (JIT) |
| tx_type | Classification: TRANSFER, MINT, BURN, POOL, STAKE, UNSTAKE, REWARD, SLASH |
| from_address | Source address — null for REWARD, MINT (system-sourced) |
| to_address | Destination address — null for SLASH, BURN (protocol-routed) |
| amount | Transfer value in BACHI |
| currency | Denomination: BACHI |
| network | Network: TESTNET |
| nonce | Account nonce — null for system transactions (REWARD, SLASH) |
| gas_limit | Gas declared by submitter |
| max_fee_per_gas | Maximum fee per gas willing to pay |
| max_priority_fee_per_gas | Tip to block proposer |
| base_fee_per_gas | Protocol base fee (JIT — set at execution) |
| effective_gas_price | Actual gas price paid (JIT — computed at execution) |
| gas_used | Gas consumed (JIT — set at execution) |
| total_fee | Total fee paid (JIT — computed at execution) |
| status | Lifecycle: PENDING, SUBMITTED, INCLUDED, FINALIZED, FAILED |
| block_number | Block in which tx was included (JIT) |
| block_hash | Hash of including block (JIT) |
| memo | Optional human note |
| created_at | Submission timestamp (JIT) |

**Dropped (KISS):** signature (trust the nonce for demo), transaction_index, confirmations (status covers it).

---

### Validator (Consensus PoS Subdomain)
A consensus participant who has staked the minimum required balance. Validators are linked to actors via actor_id (direct reference, practical for single-node) and to wallets via withdrawal_credentials. Status is governed by ETH2 9-state vocabulary but set by payload — no workflow-driven transitions in this CR.

| Attribute | Description |
|-----------|-------------|
| validator_index | Sequential consensus index |
| actor_id | Direct actor reference (single-node convenience) |
| pubkey | BLS12-381 signing key (0x-prefixed) — immutable |
| withdrawal_credentials | Hash of withdrawal destination address |
| effective_balance | Staked balance in Gwei |
| slashed | Boolean — whether validator has been penalized |
| status | ETH2 lifecycle: PENDING_INITIALIZED, PENDING_QUEUED, ACTIVE_ONGOING, ACTIVE_EXITING, ACTIVE_SLASHED, EXITED_UNSLASHED, EXITED_SLASHED, WITHDRAWAL_POSSIBLE, WITHDRAWAL_DONE |
| activation_eligibility_epoch | Epoch when deposit was processed |
| activation_epoch | Epoch when validator became active |
| exit_epoch | Epoch when validator began exiting |
| withdrawable_epoch | Epoch when funds can be withdrawn |
| balance | Current balance in Gwei |
| created_at | Registration timestamp |
| updated_at | Last state update |

**Dropped (KISS):** last_attestation_slot (too granular), node_name, stake (redundant with effective_balance and actor_id).

---

### Block (Consensus PoS Subdomain)
A unit of the canonical chain containing a set of transactions. A block progresses from PROPOSED through JUSTIFIED to FINALIZED. Block finalization triggers balance reconciliation across all affected wallets (in the next CR's reconciliation workflow).

| Attribute | Description |
|-----------|-------------|
| block_hash | Deterministic hash of block header (JIT) |
| parent_hash | Hash of preceding block |
| height | Block number in canonical chain |
| slot | Consensus slot |
| epoch | Consensus epoch (slot / 32) |
| block_type | Classification: GENESIS, REGULAR |
| proposer_index | Validator index of block proposer |
| gas_limit | Maximum gas for this block |
| gas_used | Total gas consumed |
| base_fee_per_gas | EIP-1559 base fee for this block |
| total_fees | Sum of all transaction fees |
| transaction_count | Number of included transactions |
| transactions | List of included tx_hash references |
| status | Finality: PROPOSED, JUSTIFIED, FINALIZED, INVALID, ORPHANED |
| is_canonical | Whether block is in the canonical chain |
| justified_epoch | Epoch in which block was justified |
| finalized_epoch | Epoch in which block was finalized |
| timestamp | Block production time |
| created_at | When block record was written |

**Dropped (KISS):** state_root, transactions_root, receipts_root (Merkle/Verkle roots — too complex), justified/finalized boolean flags (redundant with status), attestations, randao_reveal, block_size.

---

## 2. Business Processes

### Process 1 — Actor Registration and Verification
1. Actor submits: first_name, last_name, email_registration, user_type, kyc_verified, currency_preference, language
2. System generates actor_id, sets status = PENDING
3. KYC check — if passes, status → VERIFIED / ACTIVE
4. Actor record persisted

### Process 2 — Wallet Creation
1. Verified actor requests wallet with: wallet_type, name, currency
2. System generates wallet_id, derives EOA address
3. Wallet record created with balance = 0.0, nonce = 0, status = ACTIVE
4. Wallet event appended

### Process 3 — Transaction Submission and Mempool Persistence
1. Actor submits: tx_type, from wallet, to_address, amount, gas parameters
2. System validates structure (field types, address format, gas bounds)
3. System validates policy (sufficient balance, nonce available)
4. Nonce reserved atomically
5. tx_hash computed
6. Transaction persisted to mempool with status = PENDING

### Process 4 — Block Proposal
1. Consensus driver triggers round
2. Eligible validators queried
3. Proposer selected deterministically
4. Pending transactions collected from mempool
5. Block formed with header fields and transaction list
6. Block persisted with status = PROPOSED

### Process 5 — Balance Reconciliation (Batch, Event-Triggered — next CR)
1. Block finalization event received
2. All transactions in finalized block retrieved in order
3. For each transaction: from_wallet.balance -= (amount + total_fee); to_wallet.balance += amount
4. Transaction status → FINALIZED
5. Balance update event appended per affected wallet

---

## 3. PPS Baseline — What Already Exists

### Actor Registration (identity subdomain)
Current intake: first_name, last_name, email_registration — 3 fields. Missing: user_type, status lifecycle, kyc_verified, currency_preference, language, last_modified.
**Fit:** partial.

### Wallet Creation (wallet subdomain)
Current intake: actor_record reference, wallet_type (free string), optional wallet_config. No balance, no nonce, no address, no status. wallet_type is ungoverned.
**Fit:** partial.

### Transaction Submission (transaction subdomain)
Current intake: EIP-1559 gas fields present. Missing: tx_type (hardcoded "ETH" in WF nodes), status lifecycle, execution result fields (base_fee_per_gas, effective_gas_price, gas_used, total_fee, block_number, block_hash).
**Fit:** partial — gas model foundation exists; tx_type is a defect.

### Validator Registration (consensus_pos subdomain)
Current intake: actor_id, pubkey, withdrawal_credentials, effective_balance, node_name, stake, enrollment_status (3-state). Missing: full 9-state status, epoch fields, slashed, balance. node_name and stake are redundant.
**Fit:** partial — best baseline.

### Block Proposal (consensus_pos subdomain)
Current intake: round_number, triggered_by, timestamp — a consensus trigger, not a block entity. Block entity schema with hash, height, slot, epoch, status does not exist as a stored record.
**Fit:** mismatch.

### Events (cross-subdomain)
Existing: EV_BLOCK_PROPOSED_V0, EV_TRANSACTION_SUBMITTED_V0, EV_VALIDATOR_REGISTERED_V0, EV_ACTOR_REGISTERED_UNVERIFIED_V0, EV_ACTOR_VERIFIED_V0, EV_WALLET_CREATION_REQUESTED_V0 (name implies request, not completion — gap), EV_TRANSACTION_REJECTED_V0, EV_ACTOR_REJECTED_V0, EV_ROUND_SKIPPED_V0.
Missing: EV_BLOCK_FINALIZED_V0, EV_BLOCK_COMMITTED_V0, EV_TX_FINALIZED_V0, EV_BALANCE_RECONCILED_V0, EV_BLOCK_ATTESTED_V0.
**Fit:** partial.

---

## 4. Gap Analysis

| # | Gap | Severity |
|---|-----|----------|
| G1 | Actor: missing user_type, status, kyc_verified, currency_preference, language | CRITICAL |
| G2 | Wallet: no real balance, no nonce, no address, wallet_type ungoverned | CRITICAL |
| G3 | Transaction: no tx_type field, status lifecycle absent, tx_type hardcoded as "ETH" in WF | CRITICAL |
| G4 | Validator: enrollment_status 3-state vs 9-state; no epoch fields; node_name/stake redundant | MEDIUM |
| G5 | Block: current record is a round trigger, not a block entity | CRITICAL |
| G6 | EV_BLOCK_FINALIZED_V0 missing — no reconciliation trigger | CRITICAL |
| G7 | EV_TX_FINALIZED_V0, EV_BALANCE_RECONCILED_V0 missing — no observability | MINOR |
| G8-G11 | WF_ATTEST_BLOCK_V0, WF_FINALIZE_BLOCK_V0, WF_COMMIT_BLOCK_V0, WF_RECONCILE_BALANCES_V0 missing | CRITICAL (next CR) |
| G12 | seeds/system_wallets.json, seeds/genesis_actor.json missing | MEDIUM |

---

## 5. Decision: Extend vs. New Subdomain

**Decision:** EXTEND all five existing subdomains. No new runtime subdomain.

Workflow gaps (G8-G11) are deferred to the consensus finalization CR.

---

## 6. Open Questions → Resolved in Stage 3

| Q | Resolution |
|---|-----------|
| Q1 — Reconciliation as new WF or CC sequence? | New WF (WF_RECONCILE_BALANCES_V0) — deferred to next CR |
| Q2 — Full 9-state validator lifecycle or subset? | 9-state enum declared; status set by payload only in this CR |
| Q3 — Event chaining or co-emission? | Sequential chain: each WF emits one event triggering next step |
| Q4 — MINT seeding: WF or seed file? | Seed file (seeds/system_wallets.json) — consistent with license_facts pattern |
| Q5 — node_name/stake removal safe? | Safe — validators.json is empty; seed payload updated in this CR |

---

## Amendments

**Status:** Post-authoring retroactive fix — Option B (amendment section added; approved content above unchanged)
**Source of truth:** 8_authoring_manifest_data_model_v0.md (Sections 1, 2b) and 6b_design_intent_data_model_v0.md (Design Pivot Record)

The business entity schemas and gap findings in this document remain correct. The following amendments record where the realized process mechanism differed from the domain model's description.

---

### Amendment A — Process 3: nonce reservation not implemented; typed WFs replace unified submission

**Domain model location:** Section 2 (Business Processes) — Process 3 (Transaction Submission and Mempool Persistence):
- Step 4: "Nonce reserved atomically"
- The process describes a single unified transaction submission flow with tx_type as a payload field

**As-built:** Two changes:

1. **Nonce reservation dropped.** `CC_RESERVE_NONCE_V0` was not called by any typed transaction WF. The BACHI data model uses content-addressable transaction identity — `tx_id` is derived from payload hash via `CT_PURE_GENERATE_ID_V0`. Sequential nonce counting is not needed in a content-addressable system. Nonce increment remains deferred to a future CR.

2. **8 typed WFs replace one unified submission WF.** The Design Pivot (Stage 6b) replaced the unified `WF_SUBMIT_TRANSACTION_V0` with 8 typed workflows — one per transaction type. The WF identity declares the type; no `tx_type` payload field selects the path.

**Corrected Process 3 steps:**
1. Actor invokes the typed WF for the transaction type (e.g., WF_TRANSFER_V0, WF_STAKE_V0)
2. Typed IN_ validates structure (field types, address format, gas bounds) per type-specific schema
3. Typed CC_VALIDATE_<TYPE>_POLICY_V0 validates policy (balance, address nullability)
4. CC_GENERATE_TX_ID_V0 computes tx_id and tx_hash (content-addressable; BACHI-native)
5. CC_PERSIST_MEMPOOL_TX_V0 persists transaction with status = PENDING

---

### Amendment B — Transaction entity: nonce field present but not incremented in this CR

**Domain model location:** Section 1 (Business Entities) — Transaction entity — "nonce | Account nonce — null for system transactions (REWARD, SLASH)"

**As-built:** The `nonce` field is declared in the transaction entity schema but is never populated during this CR's artifact execution. CC_RESERVE_NONCE_V0 was not called. In the BACHI content-addressable model, replay protection is provided by the deterministic tx_id — submitting identical inputs produces the same tx_id, which can be detected as a duplicate without needing a sequential nonce counter. The nonce field on the transaction entity is effectively vestigial in this CR.

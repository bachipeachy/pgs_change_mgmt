# Stage 4 — Business Model: blockchain / data_model
**Stage:** 4 — Business Model
**CR:** 1_change_request_data_model_v0.md
**Status:** COMPLETE
**Feeds:** Stage 5 — Business Intent

---

## What This CR Delivers

This CR enriches the governed data model across all five blockchain subdomains. It does not deliver workflow logic. After this CR closes, the system carries semantically complete records — actors with roles, wallets with balances, transactions with types, validators with lifecycle status, blocks with finality state. The next CR (consensus finalization workflows) will operate on these records.

---

## Business Capabilities Delivered

### BC-1 — Register an Actor with a Governed Role and Status

**Before:** An actor record carries only name and email. There is no role, no lifecycle status, no KYC tier, no currency preference.

**After:** An actor is registered with a governed user_type (INDIVIDUAL, BUSINESS, ORGANIZATION, VALIDATOR, DELEGATOR, INSTITUTIONAL, DEVELOPER, TESTNET), a lifecycle status (PENDING → VERIFIED / ACTIVE), and a KYC flag. The demo can show an actor admitted as a VALIDATOR role vs. an INDIVIDUAL role — these are now distinguishable records.

**Demo scenario:** Register Gomer Adams as INDIVIDUAL, active, KYC verified. Register a validator actor as VALIDATOR type. Both records carry their role as a governed field.

**Findings satisfied:** G1, Finding Set A (identity row)

---

### BC-2 — Create a Wallet with Real Account State

**Before:** A wallet is created with balance hardcoded to 0.0, no nonce, and wallet_type as a free string ("standard"). No currency is declared on the wallet record.

**After:** A wallet carries a real balance (set at creation or seeded), a nonce (starts at 0, increments per transaction), a governed wallet_type (DEFAULT, PRIVATE, BUSINESS, SAVINGS, INVESTMENT, MINT, BURN, POOL), and a currency denomination (BACHI). Each user wallet starts with a declared opening balance. System wallets (MINT, BURN, POOL) carry their seeded amounts.

**Demo scenario:** Gomer Adams has two wallets — private (opening balance seeded by MINT transfer) and business. Both show a real BACHI balance. The nonce on each wallet prevents replay.

**Findings satisfied:** G2, Finding Set A (wallet row), wallet_type PRIVATE addendum

---

### BC-3 — Submit a Typed Transaction with a Full Gas Model

**Before:** All transactions are treated as type "ETH" regardless of payload. There is no tx_type field. Gas model fields are present but tx_type, status lifecycle, and execution result fields are absent.

**After:** A transaction declares its type (TRANSFER, MINT, BURN, POOL, STAKE, UNSTAKE, REWARD, SLASH), carries a full EIP-1559 gas model (max_fee_per_gas, max_priority_fee_per_gas, base_fee_per_gas at execution), and has a governed status lifecycle (PENDING → SUBMITTED → INCLUDED → FINALIZED). REWARD and SLASH transactions carry only the relevant address (to or from respectively) — the protocol determines the counterparty.

**Demo scenario:** Slot 1 submits a TRANSFER of 6,000 BACHI from MINT to Gomer Adams private wallet. Slot 10 submits a REWARD of 1,000 BACHI to Gomer Adams. Slot 11 submits a SLASH of 1,000 BACHI from Liam Adams. Each has a distinct tx_type and status beginning at PENDING.

**Findings satisfied:** G3, Finding Set A (transaction row), Finding Set D (tx_type defect fixes), asymmetric from/to schema addendum

---

### BC-4 — Bootstrap the Closed Token Economy

**Before:** No GENESIS actor exists as a governed record. No system wallets (MINT, BURN, POOL) exist with seeded balances. The initial 1,000,000 BACHI supply has no governed home.

**After:** A GENESIS actor seed record exists. System wallets (MINT: 1,000,000 BACHI opening balance; BURN: 0 BACHI; POOL: 0 BACHI) exist as governed seed records. All regular user wallets reference real actor_id values. The closed token economy has a declared starting state.

**Demo scenario:** Bootstrap loads system_wallets seed. MINT wallet shows 1,000,000 BACHI. Slots 1–9 transfer funds from MINT to user wallets and POOL. MINT balance decreases; user wallet balances are set (pending reconciliation workflow in next CR).

**Findings satisfied:** Finding Set E (seed gap), G13

---

### BC-5 — Observe Block Finality State

**Before:** A block record carries only hash, parent_hash, height, and timestamp. No slot, epoch, proposer, Merkle/Verkle roots, gas accounting, or finality status exists as a governed field.

**After:** A block record carries slot, epoch, proposer_index, state_root (Verkle), transactions_root and receipts_root (Merkle), gas_limit, gas_used, base_fee_per_gas, total_fees, transaction_count, a governed status lifecycle (PROPOSED → JUSTIFIED → FINALIZED), and canonical chain flag. The block record is a complete governed entity, not a round-trigger payload.

**Demo scenario:** After WF_PROPOSE_BLOCK_V0 runs, the block record shows status = PROPOSED with all header fields populated. When attestation and finalization workflows run (next CR), status advances through JUSTIFIED → FINALIZED.

**Findings satisfied:** G5, Finding Set A (block row)

---

### BC-6 — Observe Validator ETH2 Lifecycle Status

**Before:** A validator carries enrollment_status with 3 values (ACTIVE, INACTIVE, EXCLUDED), plus redundant fields node_name and stake.

**After:** A validator carries status with the full 9-state ETH2 governed vocabulary (PENDING_INITIALIZED, PENDING_QUEUED, ACTIVE_ONGOING, ACTIVE_EXITING, ACTIVE_SLASHED, EXITED_UNSLASHED, EXITED_SLASHED, WITHDRAWAL_POSSIBLE, WITHDRAWAL_DONE), plus epoch fields (activation_eligibility_epoch, activation_epoch, exit_epoch, withdrawable_epoch), slashed flag, balance, and last_attestation_slot. node_name and stake are removed.

**Demo scenario:** Register a validator with status = PENDING_INITIALIZED and effective_balance = 32,000,000,000 Gwei. The governed status field is set at registration by payload. Status transitions are payload-driven in this CR — no workflow-driven lifecycle transitions are in scope.

**Findings satisfied:** G4, Finding Set A (validator row), Q5 resolution

---

### BC-7 — Govern State-Change Events for the Token Economy

**Before:** Events exist for actor registration, transaction submission, validator registration, and block proposal. No events exist for block finalization, transaction finalization, or balance changes.

**After:** Five new governed events are declared: EV_BLOCK_ATTESTED_V0, EV_BLOCK_FINALIZED_V0, EV_BLOCK_COMMITTED_V0, EV_TX_FINALIZED_V0, EV_BALANCE_RECONCILED_V0. These events are declared as governed artifacts in this CR. They are emitted by the consensus finalization and reconciliation workflows delivered in the next CR.

**Demo scenario:** Once the next CR's workflows run, each block finalization emits EV_BLOCK_FINALIZED_V0, each transaction completes with EV_TX_FINALIZED_V0, and each wallet update emits EV_BALANCE_RECONCILED_V0. The event log becomes a readable audit trail of the token economy.

**Findings satisfied:** G6, G7, G8 (partial — event declared; workflow deferred), Finding Set C

---

## What This CR Does NOT Deliver

| Capability | Reason | Next CR |
|-----------|--------|---------|
| Wallet balances actually updated after transactions | Requires WF_RECONCILE_BALANCES_V0 | consensus_finalization CR |
| Block advancing from PROPOSED → JUSTIFIED → FINALIZED | Requires WF_ATTEST_BLOCK_V0, WF_FINALIZE_BLOCK_V0 | consensus_finalization CR |
| Block committed to canonical chain | Requires WF_COMMIT_BLOCK_V0 | consensus_finalization CR |
| Validator status advancing through ETH2 lifecycle via workflow | Explicitly deferred — payload-driven only in this CR | future CR |

---

## Demo Readiness After This CR

The system can demonstrate:
- Actor registration with role and status (BC-1)
- Wallet creation with real account state (BC-2)
- Typed transaction submission through the full EIP-1559 gas model (BC-3)
- Closed token economy with seeded system wallets (BC-4)
- Block entity with full finality state fields (BC-5)
- Validator with ETH2 lifecycle status (BC-6)
- Governed event vocabulary for the full consensus flow (BC-7)

The system cannot yet demonstrate balance movement. Wallet balances are set at seed/creation and remain static until the consensus finalization workflows close. The enriched data model is the prerequisite — the next CR makes it live.

---

## Stage 4 Gate

**Gate passed.** Seven business capabilities named and bounded. Scope split confirmed: this CR = data model enrichment; next CR = consensus finalization workflows.

**Proceed to Stage 5 — Business Intent.**

---

## Amendments

**Status:** Post-authoring retroactive fix — Option B (amendment section added; approved content above unchanged)
**Source of truth:** 8_authoring_manifest_data_model_v0.md (Sections 1, 2b) and 6b_design_intent_data_model_v0.md (Design Pivot Record)

The business capabilities BC-1 through BC-7 are unchanged. The following amendments record where the realization mechanism differed from what the BM implied.

---

### Amendment A — BC-3: transaction type is expressed by WF identity, not a payload field

**BM location:** BC-3 — "A transaction declares its type (TRANSFER, MINT, BURN, POOL, STAKE, UNSTAKE, REWARD, SLASH)"

**Implied mechanism:** A unified transaction submission workflow receives `tx_type` as a payload field. A single WF selects validation rules based on that field.

**As-built:** The Design Pivot (approved Stage 6b) replaced the unified WF with 8 typed transaction workflows — one per type. The transaction type is expressed by which WF the caller invokes (`WF_TRANSFER_V0`, `WF_STAKE_V0`, etc.), not by a payload field. Each typed WF has its own intent schema and policy CC. There is no `tx_type` field routing within a single WF.

**Business capability unchanged:** The business outcome — submitting a typed, governed transaction — is the same. The mechanism that makes each type explicit is WF identity rather than payload content. This is a stronger governance guarantee, not a weaker one.

---

### Amendment B — BC-2: wallet nonce field exists but does not increment in this CR

**BM location:** BC-2 — "a nonce (starts at 0, increments per transaction)"

**As-built:** The wallet entity carries a `nonce` field initialized to 0. However, `CC_RESERVE_NONCE_V0` was not called by any typed transaction WF — the BACHI data model uses content-addressable transaction identity (`tx_id` derived from payload hash) rather than ETH-style sequential nonces. Nonce increment per transaction was not implemented in this CR.

**Business capability partially deferred:** The wallet nonce field is present and initialized. Its increment-per-transaction behavior is deferred to a future CR that implements nonce-based replay protection, if that CR is warranted in the BACHI content-addressable model.

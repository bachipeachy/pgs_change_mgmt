# Stage 1 — Input Elicitation: blockchain / data_model
**Stage:** 1 — Input Elicitation
**CR:** 1_change_request_data_model_v0.md
**Status:** COMPLETE
**Feeds:** Stage 2 — Domain Model Discovery

---

## Part 1 — Problem Statement

The blockchain domain governs real execution paths — actor registration, wallet creation, transaction submission, validator activation, block production — but every payload field that flows through those paths carries only the minimum value needed to satisfy the topology. Balances are zero. Transaction types are unclassified. Validators have no lifecycle. Blocks have no finality state.

The system is structurally governed but semantically hollow. It cannot demonstrate what a blockchain actually does: move value between accounts, fee a transaction, activate a validator through an epoch lifecycle, finalize a block. A governed system with empty data is not demonstrable; it is a skeleton.

---

## Part 2 — Business Final Outcome

By end of this CR, the blockchain domain's five governed subdomains carry the canonical field set required for meaningful operation:

**What can now happen that could not happen before:**
- An actor is registered with a role (individual, validator, delegator, institutional) and a verification status — not just a name and email
- A wallet holds a real account balance and nonce, belongs to a named wallet type (default, savings, business, mint, burn), and is denominated in a specific currency
- A transaction declares its type (transfer, mint, burn, stake, unstake, reward, slash), carries a gas fee model, and has a signing/execution/inclusion lifecycle
- A validator progresses through a governed ETH2 lifecycle: deposit received → activation queued → actively validating → exiting → withdrawn — with epoch markers at each transition
- A block records its finality state (proposed → justified → finalized) alongside slot, epoch, proposer, and Merkle/Verkle roots

**Structural properties the system gains:**
- Every governed field is declared in a protocol artifact — no field exists only in a seed file or test payload
- Enumerated types (actor role, wallet type, transaction type, validator status, block status) are governed controlled vocabularies — not free strings
- State transitions that matter (balance change, validator status change, block finalization) trigger declared events

**Governance independence invariant:**
- identity carries no consensus-layer fields — it remains currency-agnostic and PoS-agnostic
- validator subdomain owns all staking and epoch fields — the only link to identity is through a wallet withdrawal address
- A BTC actor registered in identity is fully valid without ever touching the validator subdomain

---

## Part 3 — Current Business Knowledge

### A. Actor Identity Model

The current identity subdomain registers actors with: actor_id, name, email, kyc_verified, status, created_at. This is sufficient to admit an actor into the system but carries no role classification, no verification tier, no contact or profile data, and no currency preference.

BachiCoin defines 10 actor roles: LEDGER, GENESIS, INDIVIDUAL, BUSINESS, ORGANIZATION, VALIDATOR, DELEGATOR, INSTITUTIONAL, DEVELOPER, TESTNET. Of these, VALIDATOR and DELEGATOR are consensus roles — they classify the actor's participation intent but do not carry staking mechanics (those belong in the validator subdomain). All other roles are identity-layer concepts and belong in this subdomain.

Lifecycle statuses needed: ACTIVE, INACTIVE, SUSPENDED, PENDING, VERIFIED, DELETED, ARCHIVED.

In scope: role, status, KYC tier, contact fields (phone, country, address), currency preference, language. Not in scope: staking fields of any kind.

### B. Wallet and Account State

The current wallet subdomain stores wallet_id, user_id, name, balance (hardcoded 0.0), network. It has no account type, no nonce, no currency denomination, no wallet classification.

ETH account state is: balance + nonce. These two fields together define an account's ability to transact — nonce prevents replay, balance gates transfers. Both are required for any meaningful transaction demo.

Wallet types needed (from BachiCoin): DEFAULT, PRIVATE, BUSINESS, CHARITY, SAVINGS, INVESTMENT, MINT, BURN, POOL. MINT and BURN are system wallets — they represent the token supply endpoints. POOL supports liquidity operations.

Currency denomination: BACHI only in this CR. Multi-currency deferred.

HD multi-address structure (addresses dict): in scope as a field declaration. The derivation path mechanics are out of scope.

### C. Transaction Type and Fee Model

The current transaction subdomain stores: tx_id, from_address, to_address, amount, status. No type classification, no gas model, no lifecycle views.

EIP-1559 Type 2 is the adopted standard (from BachiCoin). This means: max_fee_per_gas + max_priority_fee_per_gas declared at submission; base_fee_per_gas set by protocol at execution; effective_gas_price and total_fee computed as JIT fields.

Transaction types in scope (from BachiCoin, excluding deferred):
- TRANSFER — P2P value transfer (core)
- MINT — create new supply (system)
- BURN — permanently remove supply (system)
- POOL — moves mint funds to pool (system)
- STAKE — lock funds for validator activation
- UNSTAKE — release staked funds
- REWARD — block/staking reward (system-generated)
- SLASH — validator penalty (system-generated)

Deferred: CONTRACT_CALL, CONTRACT_DEPLOY, GOVERNANCE.

JIT fields (populated at execution, not submission): tx_hash, nonce, base_fee_per_gas, effective_gas_price, gas_used, total_fee, block_number, block_hash, transaction_index, confirmations.

### D. Validator Consensus Lifecycle

The current validator subdomain stores: validator_id, pubkey, status. No ETH2 lifecycle, no epoch markers, no balance.

ETH2 validator lifecycle (9 statuses from BachiCoin): PENDING_INITIALIZED → PENDING_QUEUED → ACTIVE_ONGOING → ACTIVE_EXITING / ACTIVE_SLASHED → EXITED_UNSLASHED / EXITED_SLASHED → WITHDRAWAL_POSSIBLE → WITHDRAWAL_DONE.

Fields in scope: validator_index, pubkey (BLS12-381), withdrawal_credentials, effective_balance, slashed, activation_eligibility_epoch, activation_epoch, exit_epoch, withdrawable_epoch, balance, last_attestation_slot.

JIT fields (computed per epoch by consensus layer): committee_assignments, validator_duties, participation_rates, effective_balance updates, attestation_rewards, proposer_rewards, slashing_penalties.

Staking fields (stake_amount, delegation_fee, validator_address) do NOT belong in identity — confirmed ETH2-standard: these are consensus-layer concepts. withdrawal_credentials is the only link from validator back to a wallet/EOA.

### E. Block Finality and Chain State

The current block subdomain stores: block_hash, parent_hash, height, timestamp. No slot/epoch, no finality, no Merkle/Verkle roots, no gas accounting.

Block status lifecycle: PROPOSED → JUSTIFIED → FINALIZED (plus INVALID, ORPHANED).

Fields in scope: block_hash, parent_hash, height, slot, epoch, proposer_index, randao_reveal, state_root (Verkle), transactions_root (Merkle), receipts_root (Merkle), gas_limit, gas_used, base_fee_per_gas, transactions list, transaction_count, attestations, total_fees, block_size, status, is_canonical, justified_epoch, finalized_epoch.

Bitcoin hybrid PoW fields (difficulty, nonce, bits, chainwork) — deferred. Not needed for PoS demo.

### F. Events Triggered by Enriched State

New state transitions that warrant declared events (not currently governed):
- Balance change on wallet (debit/credit)
- Validator status transition (each lifecycle hop)
- Block status change (PROPOSED → JUSTIFIED → FINALIZED)
- Actor status change (ACTIVE → SUSPENDED etc.)

Current event model covers actor registration and transaction submission. These four new event categories are gaps.

---

## Analyst Notes

- **Purity Filter active.** No artifact family names (CC_, WF_, CT_, CS_) through Stage 5.
- **ETH2 separation confirmed:** validator stake fields stay in validator subdomain. identity is consensus-agnostic.
- **BACHI-only currency** in this CR. Multi-currency is a future CR.
- **Open question for Stage 2:** What is the minimal enriched field set per subdomain that enables the demo without over-specifying implementation? BachiCoin schemas are production-grade (40+ fields per entity) — Stage 2 must draw the IN/FUTURE CR line per entity.
- **Open question for Stage 2:** Which new events are strictly required for a functioning governed demo vs. which are observability enhancements that can be deferred?
- **Open question for Stage 3:** Do any of the five enriched subdomains require new workflow topology (new paths, new routing outcomes) or is this purely a payload/store enrichment with no topology change?

---

## Amendments

**Status:** Post-authoring retroactive fix — Option B (amendment section added; approved content above unchanged)
**Source of truth:** 8_authoring_manifest_data_model_v0.md (Sections 1, 2b) and 6b_design_intent_data_model_v0.md (Design Pivot Record)

---

### Amendment A — Transaction type is WF identity, not a payload field

**Input elicitation location:** Part 2 — "A transaction declares its type (transfer, mint, burn, stake, unstake, reward, slash)"
**Input elicitation location:** Part 3C — describes a unified tx submission flow with tx_type as payload content

**As-built:** The Design Pivot (approved Stage 6b) replaced the unified transaction submission approach with 8 typed workflows. The WF identity declares the transaction type — the caller invokes `WF_TRANSFER_V0` or `WF_STAKE_V0`, etc. There is no `tx_type` payload field routing within a unified WF. Each typed WF carries its own intent schema, typed policy CC, and execution topology. The business outcome ("a transaction declares its type") is achieved via a stronger mechanism: type-specific topology expressed at compile time, not selected by a runtime payload value.

---

### Amendment B — Wallet nonce does not increment; transaction nonce not reserved

**Input elicitation location:** Part 3B — "ETH account state is: balance + nonce. These two fields together define an account's ability to transact — nonce prevents replay, balance gates transfers."
**Input elicitation location:** Part 3C — JIT fields include `nonce` for transactions

**As-built:** The BACHI data model uses content-addressable transaction identity (`tx_id` derived from payload hash). `CC_RESERVE_NONCE_V0` was not called by any typed transaction WF in this CR. The wallet `nonce` field exists and is initialized to 0 but is never incremented. The transaction `nonce` field is vestigial in this CR. Replay protection is provided structurally by deterministic tx_id — identical inputs produce the same tx_id, detectable as a duplicate without a sequential nonce counter.

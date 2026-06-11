# Stage 2 — Domain Model Discovery: blockchain / consensus_propose
**Stage:** 2 — Domain Model Discovery
**CR:** 1_change_request_consensus_propose_v0.md
**Status:** COMPLETE
**Feeds:** Stage 3 — Analysis Loop

---

## 1. Business Entities

### Actor
A registered participant in the blockchain system. For this CR, the test population requires at least one INDIVIDUAL actor with a funded wallet to exercise ENDUSER transaction paths. The genesis_actor (GENESIS role) already exists as a seed and owns the system wallets.

| Attribute | Description |
|-----------|-------------|
| actor_id | Deterministic unique identifier |
| user_type | Role: INDIVIDUAL (test actors), GENESIS (system — already seeded) |
| status | ACTIVE |
| kyc_verified | Boolean — must be true for ENDUSER transactions |

---

### Validator
A consensus participant with ACTIVE enrollment status and a declared stake. The block proposal mechanism reads the eligible validator pool from the validator registry. Without at least one active, staked validator, every consensus round is skipped — no block can ever be proposed.

| Attribute | Description |
|-----------|-------------|
| validator_id / validator_index | Unique consensus identifier |
| actor_id | Owning actor reference |
| enrollment_status | Must be ACTIVE to be eligible for proposer selection |
| stake | Must be present (non-null) to pass eligibility filter |
| pubkey | BLS12-381 signing key |

---

### Wallet
An account holding a BACHI balance, owned by an actor. ENDUSER transaction workflows require the submitting actor to have a wallet — admission is gated on wallet existence. System wallets (MINT, BURN, POOL) are already seeded with initial balances.

| Attribute | Description |
|-----------|-------------|
| wallet_id | Deterministic unique identifier |
| actor_id | Owning actor |
| wallet_type | DEFAULT (test actors), MINT / BURN / POOL (system — already seeded) |
| balance | BACHI amount; MINT wallet seeded at 1,000,000 |
| status | ACTIVE |

---

### Transaction (Mempool Entry)
A typed, policy-validated value transfer persisted to the mempool with status PENDING. This CR exercises all eight transaction types — one per typed submission path. Transactions are the input to the block proposal mechanism.

| Attribute | Description |
|-----------|-------------|
| tx_id | Content-addressable deterministic identifier |
| tx_type | TRANSFER, STAKE, UNSTAKE, MINT, BURN, POOL, REWARD, SLASH |
| from_address | Source wallet address (null for MINT, REWARD) |
| to_address | Destination wallet address (null for BURN, SLASH) |
| amount | BACHI value |
| status | PENDING at mempool entry |
| tx_hash | Content-addressable hash |

---

### Block
A unit of the canonical chain containing a set of transactions, produced by a selected proposer for a given consensus slot. For this CR, the block reaches PROPOSED state only — no attestation, finalization, or chain commitment.

| Attribute | Description |
|-----------|-------------|
| block_id | Deterministic identifier (BLK prefix) |
| proposer_id | Validator selected as proposer for this slot |
| round_id | Consensus round number (maps to block height) |
| slot | Slot number within the epoch |
| epoch | Epoch number |
| tx_ids | List of transaction identifiers included in the block |
| timestamp | Block production time |
| is_canonical | false at PROPOSED state |
| status | PROPOSED |

---

### Consensus Round
A record of a single slot execution — either a block was proposed or the round was skipped. Produced regardless of outcome.

| Attribute | Description |
|-----------|-------------|
| round_id | Slot identifier |
| proposer_id | Selected proposer (null if round skipped) |
| block_id | Proposed block reference (null if round skipped) |
| timestamp | Slot execution time |

---

## 2. Business Processes

### Process 1 — Test Data Population
Establish the canonical data set needed to exercise all eight transaction types and propose a block.

1. Register at least two INDIVIDUAL actors through the actor registration path
2. Verify each actor (advance status to ACTIVE/VERIFIED)
3. Create a DEFAULT wallet for each actor
4. Register at least one validator linked to an actor
5. Confirm system wallets (MINT, BURN, POOL) are present and funded — they are seeded; no action required

### Process 2 — Transaction Batch Submission
Exercise all eight typed transaction submission paths to produce PENDING mempool entries.

1. Submit one TRANSFER transaction (actor-to-actor value transfer)
2. Submit one STAKE transaction (actor locks funds for validator activation)
3. Submit one UNSTAKE transaction (actor releases staked funds)
4. Submit one MINT transaction (system creates new supply)
5. Submit one BURN transaction (system permanently removes supply)
6. Submit one POOL transaction (system moves MINT funds to POOL wallet)
7. Submit one REWARD transaction (system issues block/staking reward)
8. Submit one SLASH transaction (system penalizes validator)

Each submission is validated by its typed admission schema and policy. Successful submissions persist to the mempool with status PENDING.

### Process 3 — Consensus Loop Execution
A timed driver triggers consensus rounds on a 30-second slot cycle. Transactions are submitted at 20-second intervals before the slot fires.

1. At each slot boundary, the consensus loop fires with a round_number and timestamp
2. The eligible validator pool is queried — if empty, the round is skipped
3. A proposer is selected deterministically from the active validator pool
4. All pending transactions are read from the mempool
5. A block is formed with the proposer, slot, epoch, and transaction list
6. The block is persisted to the block store with status PROPOSED
7. A consensus round record is written

### Process 4 — Result Verification
Confirm the governed outputs match expectations.

1. Inspect the block store — at least one block record in PROPOSED state with canonical field values
2. Inspect the transaction store — all eight submitted transactions in PENDING state with tx_id and tx_hash
3. Inspect the consensus round record — proposer identified, block_id recorded
4. Examine the execution trace — all eight typed submission paths show SUCCESS routing

---

## 3. PPS Baseline — What Already Exists

### Actor Registration and Verification
Two-step path: register (unverified) → verify. Both workflows exist and have been end-to-end tested. Fit for this CR: **exact match** — no changes needed.

### Wallet Creation
Wallet creation workflow exists and is tested. Requires a verified actor as prerequisite. Produces a wallet with status ACTIVE and balance 0. Fit for this CR: **exact match**.

### Validator Registration
Validator registration workflow exists. Writes a validator record to the VALIDATOR store. Not re-tested since the data_model CR enriched the validator schema. Fit for this CR: **partial** — workflow exists; runtime conformance against enriched schema not yet confirmed.

### Eight Typed Transaction Submission Workflows
All eight workflows (TRANSFER, STAKE, UNSTAKE, MINT, BURN, POOL, REWARD, SLASH) exist, compile, and build. None has ever been invoked at runtime. Fit for this CR: **partial** — governed paths exist; runtime CS wiring not confirmed.

### Block Proposal Workflow
Exists and was tested in the consensus_pos CR. Reads pending transactions, selects a proposer, forms a block, records the consensus round. **Gap discovered:** the workflow payload carries `round_number` and `timestamp` only. The block formation capability requires `slot` and `epoch` as inputs — neither is present in the current payload or resolved by any node in the workflow. This is a structural mismatch that will cause a runtime failure.

Fit for this CR: **mismatch on slot/epoch inputs** — requires correction before block proposal can execute.

### System Wallets Seed
MINT (1,000,000 BACHI), BURN (0), POOL (0) — all owned by genesis_actor. Present and funded. Fit for this CR: **exact match** — SYSTEM authority transaction tests can proceed immediately.

### genesis_actor Seed
GENESIS actor with actor_id ACT_7a77a0461083f938. Present. Fit for this CR: **exact match** for system wallet ownership; does not substitute for INDIVIDUAL test actors.

### Validators Seed
`validators.json` is empty. No validator records exist in the runtime data store. Fit for this CR: **mismatch** — block proposal will always skip (no eligible validators).

---

## 4. Gap Analysis

### Gap 1 — No INDIVIDUAL test actors, wallets, or validators (CRITICAL)
ENDUSER transaction workflows (TRANSFER, STAKE, UNSTAKE) are admission-gated on wallet existence. No INDIVIDUAL actors or their wallets exist. Validator registration requires an actor. Block proposal requires at least one eligible validator.

**Impact:** ENDUSER WFs cannot be invoked; block proposal always skips; the entire test scenario cannot execute without this data.

### Gap 2 — Block proposal payload missing slot and epoch (CRITICAL)
The block formation capability requires `slot` and `epoch` as inputs. The block proposal workflow payload (`round_number`, `timestamp`, `triggered_by`) does not include them, and no node in the workflow resolves them. This is a structural mapping gap.

**Impact:** Every block proposal attempt will fail at the block formation step.

### Gap 3 — Validator registry empty at runtime (CRITICAL)
`validators.json` holds no records. The eligible validator query returns NOT_FOUND → consensus round skipped. No block can be proposed until at least one ACTIVE, staked validator is registered.

**Impact:** Block proposal always skips; no block can be formed.

### Gap 4 — No consensus loop driver (CRITICAL)
The 30-second slot cycle with 20-second transaction feed intervals does not exist as a governed or scripted mechanism. There is no component that triggers `WF_PROPOSE_BLOCK_V0` at slot boundaries.

**Impact:** Block proposal cannot be demonstrated without a slot driver.

### Gap 5 — Typed transaction WF runtime CS wiring unconfirmed (OPEN QUESTION)
All eight typed transaction workflows compile and build but have never been invoked. The CS implementations (mempool persistence, wallet policy reads) may require runtime wiring confirmation before execution succeeds.

**Impact:** Potential runtime failure on first invocation; needs Stage 3 inspection.

---

## 5. Extend vs. New Subdomain

**The question:** Does the consensus loop driver belong inside the protocol as a governed artifact, or outside it as a test script that invokes governed workflows?

**Evidence for inside (governed):** A slot-driven consensus loop is protocol behavior — slot timing, round numbering, and trigger authority are governance concerns. A governed loop would be traceable, auditable, and extensible.

**Evidence for outside (test script):** The loop is a test harness for this CR. Making it a governed workflow adds scope. The governed workflows it calls are already correct — the driver is infrastructure, not protocol.

This question determines whether this CR authors new governed artifacts for the loop or simply scripts invocations of existing ones. Deferred to Stage 3.

---

## 6. Open Questions for Stage 3

| # | Question | Why It Matters |
|---|----------|---------------|
| Q1 | How should `slot` and `epoch` be resolved in the block proposal payload — added to the payload schema, derived from `round_number`, or resolved by a new node? | Determines whether IN_BLOCK_PROPOSED_V0 must be updated and whether a computation step is needed in the WF |
| Q2 | What is the minimum canonical data set for test actors and validators — count, field values, wallet balances? | Determines seed file scope and whether new seeds or governed registration calls are used |
| Q3 | Does the consensus loop driver belong inside the protocol (governed WF) or outside (test script)? | Determines whether this CR authors new governed artifacts for the slot loop |
| Q4 | Are the CS implementations for the eight typed transaction WFs (mempool write, wallet policy read) confirmed wired at runtime? | Determines whether runtime execution will succeed on first invocation or require CS wiring work |
| Q5 | Does the enriched validator schema from the data_model CR conform at runtime with the existing validator registration workflow? | Determines whether validator registration can be used as-is to populate test validators |

# Stage 4 — Business Model: blockchain / consensus_propose
**Domain:** blockchain
**Subdomains:** consensus_pos, transaction, validator
**Version:** V0
**Status:** COMPLETE
**Pipeline Stage:** Stage 4 — Business Model
**Produced by:** v0.5.0 SDLC authoring pipeline

---

## 1. Discovery Summary

*Accumulated output of Stages 1–3. Record of what analysis found — not a polished narrative.*

### Actors

| Actor | Role | Authority Class |
|-------|------|-----------------|
| Genesis Actor | System operator; owns MINT, BURN, POOL wallets | GENESIS — SYSTEM authority |
| Bachi One / Two / Three / Four | Consensus validators; candidates for block proposer selection | VALIDATOR |
| Gomer Adams, Liam Adams, Isha Adams, Sophie Cyber | INDIVIDUAL token holders; exercise ENDUSER transaction paths | INDIVIDUAL — ENDUSER authority |
| Consensus Loop Driver | Initiates slot execution; supplies round_number, slot, epoch, timestamp | SYSTEM (triggered_by actor_id) |

---

### Entities

| Entity | Description | Store Model |
|--------|-------------|-------------|
| Actor | Registered participant; must be ACTIVE + KYC-verified for ENDUSER paths | CS_REGISTRY_V0 → actors.json |
| Wallet | BACHI balance account; PRIVATE, BUSINESS (INDIVIDUAL) or MINT/BURN/POOL (GENESIS) | CS_MUTABLE_JSON_V0 → wallets.json |
| Validator | Consensus participant with status and effective_balance; eligibility filter: status=ACTIVE_ONGOING, effective_balance present | CS_MUTABLE_JSON_V0 → validators.json |
| Transaction (Mempool) | Typed value transfer in PENDING state; content-addressed by tx_id | CS_MUTABLE_JSON_V0 → transactions.json |
| Block | Unit of the canonical chain; status=PROPOSED for this CR; carries proposer_id, slot, epoch, tx_ids | CS_MUTABLE_JSON_V0 → blocks.json |
| Consensus Round | Record of slot execution — proposer selected or round skipped | CS_APPENDONLY_JSONL_V0 → rounds.jsonl |
| Slot Run | Record of a governed finite slot sequence — initiated by WF_RUN_CONSENSUS_SLOTS_V0 | Derived from block + round stores |

---

### Resources

| Resource | Description |
|----------|-------------|
| BACHI supply | Total token supply; created by MINT, destroyed by BURN, moved by TRANSFER/STAKE/UNSTAKE/REWARD/SLASH/POOL |
| Mempool | PENDING transaction queue; input to block proposal at each slot |
| Validator pool | Set of ACTIVE_ONGOING validators with effective_balance present; input to proposer selection |
| Slot schedule | Finite ordered list of slot descriptors (slot number, epoch, timestamp, tx batch); governs the test run |

---

### Events

| Event | Trigger | Lifecycle Meaning |
|-------|---------|-------------------|
| EV_BLOCK_PROPOSED_V0 | CC_FORM_BLOCK_V0 SUCCESS | Block written to BLOCKS store in PROPOSED state |
| EV_ROUND_RECORDED_V0 | CC_RECORD_CONSENSUS_ROUND_V0 | Consensus round complete — proposer and block_id recorded |
| EV_ROUND_SKIPPED_V0 | CC_SKIP_ROUND_V0 | No eligible validators; round skipped with null proposer |
| EV_TX_SUBMITTED_V0 | CC_PERSIST_MEMPOOL_TX_V0 SUCCESS | Transaction persisted to mempool in PENDING state |
| EV_SLOTS_COMPLETE_V0 | CC_VERIFY_SLOT_RESULTS_V0 SUCCESS | Finite slot sequence executed; results verified |

---

### Relationships (Candidate Capabilities)

| Subject | Verb | Object | Capability Candidate |
|---------|------|--------|---------------------|
| Consensus driver | initiates finite run | slot_schedule | CC_EXECUTE_SLOT_SEQUENCE_V0 |
| CC_EXECUTE_SLOT_SEQUENCE_V0 | iterates over | slot_schedule (N slots) | Internal loop — Collatz pattern |
| CC_EXECUTE_SLOT_SEQUENCE_V0 | submits per slot | typed transactions to mempool | Delegates to typed transaction WFs |
| CC_EXECUTE_SLOT_SEQUENCE_V0 | triggers per slot | block proposal | Delegates to WF_PROPOSE_BLOCK_V0 |
| WF_PROPOSE_BLOCK_V0 | queries | eligible validator pool | CC_QUERY_ELIGIBLE_VALIDATORS_V0 |
| WF_PROPOSE_BLOCK_V0 | selects | proposer from eligible validators | CC_SELECT_PROPOSER_V0 |
| WF_PROPOSE_BLOCK_V0 | reads | pending transactions | CC_QUERY_PENDING_TRANSACTIONS_V0 |
| WF_PROPOSE_BLOCK_V0 | forms and writes | block record | CC_FORM_BLOCK_V0 |
| CC_VERIFY_SLOT_RESULTS_V0 | inspects | BLOCKS + TRANSACTION stores | Post-run assertion |
| Actor | submits | typed transaction | 8 typed WFs (TRANSFER, STAKE, UNSTAKE, MINT, BURN, POOL, REWARD, SLASH) |
| Validator | is selected as | proposer for a slot | CC_SELECT_PROPOSER_V0 |

---

## 2. Capability Graph

| Capability | Status | Gap Register Entry | Notes |
|-----------|--------|--------------------|-------|
| Finite consensus slot loop execution | CRITICAL | G4 | New — CC_EXECUTE_SLOT_SEQUENCE_V0; absorbs N-slot iteration using Collatz pattern |
| Post-run result verification | CRITICAL | G4 | New — CC_VERIFY_SLOT_RESULTS_V0; asserts PROPOSED block + 8 PENDING txs |
| Governed slot loop entry point (IN + WF) | CRITICAL | G4 | New — IN_CONSENSUS_SLOTS_V0 + WF_RUN_CONSENSUS_SLOTS_V0 |
| slot + epoch carried to block formation | CRITICAL | G2 | Update — IN_BLOCK_PROPOSED_V0 + WF_PROPOSE_BLOCK_V0 bindings |
| SYSTEM WF tx dedup via CS_REGISTRY_V0 | CRITICAL | G5 | Update — 5 RB artifacts (MINT, BURN, POOL, REWARD, SLASH) |
| Validator eligibility query on canonical fields | CRITICAL | G6 | Update — CC_QUERY_ELIGIBLE_VALIDATORS_V0 filter; IN_VALIDATOR_REGISTERED_V0 schema |
| Test data population (actors, wallets, validators) | CRITICAL | G1/G3 | SATISFIED — existing governed registration WFs reused |
| ENDUSER transaction submission (TRANSFER, STAKE, UNSTAKE) | SATISFIED | — | CS wiring confirmed; RBs correct |
| SYSTEM transaction submission (MINT, BURN, POOL, REWARD, SLASH) | ADVISORY | G5 | SATISFIED after RB update |
| Block proposal for a single slot | SATISFIED | — | WF_PROPOSE_BLOCK_V0 exists; updated for slot/epoch |
| Proposer selection from eligible validators | SATISFIED | — | CC_SELECT_PROPOSER_V0 exists and is correct |
| Block formation and write | SATISFIED | — | CC_FORM_BLOCK_V0 exists and is correct |
| Consensus round recording | SATISFIED | — | CC_RECORD_CONSENSUS_ROUND_V0 exists and is correct |
| Mempool persistence + dedup | SATISFIED | — | CC_PERSIST_MEMPOOL_TX_V0 exists; RB fix required for SYSTEM WFs |

---

## 3. Dependency Graph

| From | To | Dependency Type | PPS Status |
|------|----|-----------------|------------|
| WF_RUN_CONSENSUS_SLOTS_V0 | WF_PROPOSE_BLOCK_V0 | invocation — slot-level block proposal | SATISFIED (after slot/epoch update) |
| CC_EXECUTE_SLOT_SEQUENCE_V0 | Typed transaction WFs (8) | invocation — mempool population per slot | SATISFIED (after RB fix for SYSTEM WFs) |
| CC_QUERY_ELIGIBLE_VALIDATORS_V0 | VALIDATOR store | data read — filters on status + effective_balance | SATISFIED (after CC filter update) |
| WF_REGISTER_VALIDATOR_V0 | ACTOR store | data read — CC_CHECK_ACTOR_EXISTS_V0 | SATISFIED |
| CC_PERSIST_MEMPOOL_TX_V0 | CS_REGISTRY_V0 | capability call — tx dedup | GAP (G5) — RB missing for SYSTEM WFs |
| CC_FORM_BLOCK_V0 | slot, epoch from IN payload | data dependency — inputs not wired | GAP (G2) — IN schema update required |
| test data population | WF_REGISTER_ACTOR_UNVERIFIED_V0, WF_VERIFY_ACTOR_V0, WF_CREATE_WALLET_V0, WF_REGISTER_VALIDATOR_V0 | invocation — governed registration path | SATISFIED |

---

## 4. Constraint Register

| # | Constraint | Source |
|---|-----------|--------|
| 1 | Block status is PROPOSED only in this CR — no attestation, finalization, or chain commitment | CR scope — deferred to consensus_attest, consensus_finalize |
| 2 | Termination of consensus loop is declared in input (finite slot_schedule) — not imposed by external kill signal or runtime flag | PGS doctrine: zero inference, no ambient control |
| 3 | slot = round_number % 32; epoch = round_number // 32 — computed before invoking IN_BLOCK_PROPOSED_V0 | ETH slot/epoch arithmetic; declared in IN payload by caller |
| 4 | Validator eligibility requires status=ACTIVE_ONGOING AND effective_balance present | CC_QUERY_ELIGIBLE_VALIDATORS_V0 filter (after G6 update) |
| 5 | SYSTEM authority transactions (MINT, BURN, POOL, REWARD, SLASH) require no actor wallet — admission gated on triggered_by only | Existing typed IN schema contracts |
| 6 | ENDUSER authority transactions (TRANSFER, STAKE, UNSTAKE) require actor wallet existence | Existing typed IN schema contracts; CS_REGISTRY_V0 checks |
| 7 | tx_id is content-addressed — derived from payload hash via CT_PURE_GENERATE_ID_V0; no nonce reservation | PGS determinism invariant |
| 8 | All CS writes are scoped to the owning subdomain's stores — no cross-subdomain writes in any CC | PGS isolation constraint — STRUCTURE_BLOCKCHAIN_STORAGE_V0 |
| 9 | WF_RUN_CONSENSUS_SLOTS_V0 is reusable for any finite slot sequence — test or live bounded scenario | Design decision (Q3 resolution) |
| 10 | CC_EXECUTE_SLOT_SEQUENCE_V0 must not contain domain logic — it orchestrates governed WF invocations only | PGS runtime dumbness; domain logic belongs in CC/CT artifacts |

---

## 5. Gap Register

| Gap Code | Capability | Owner Subdomain | Resolution |
|----------|-----------|-----------------|------------|
| G1 | Test actor, wallet, validator population | identity / wallet / validator | REUSE existing — WF_REGISTER_ACTOR_UNVERIFIED_V0, WF_VERIFY_ACTOR_V0, WF_CREATE_WALLET_V0, WF_REGISTER_VALIDATOR_V0 |
| G2 | slot and epoch not passed to CC_FORM_BLOCK_V0 | consensus_pos | UPDATE IN_BLOCK_PROPOSED_V0 (add slot, epoch); UPDATE WF_PROPOSE_BLOCK_V0 (add bindings) |
| G3 | Validator registry empty | consensus_pos / validator | RESOLVED by G1 — population via governed path |
| G4 | No governed finite consensus loop | consensus_pos | NEW — IN_CONSENSUS_SLOTS_V0, WF_RUN_CONSENSUS_SLOTS_V0, CC_EXECUTE_SLOT_SEQUENCE_V0, CC_VERIFY_SLOT_RESULTS_V0 |
| G5 | CS_REGISTRY_V0 missing from SYSTEM WF RBs | transaction | UPDATE RB_MINT_V0, RB_BURN_V0, RB_POOL_V0, RB_REWARD_V0, RB_SLASH_V0 |
| G6 | Validator eligibility query / registration schema fragmentation | validator / consensus_pos | UPDATE CC_QUERY_ELIGIBLE_VALIDATORS_V0 (filter fields); UPDATE IN_VALIDATOR_REGISTERED_V0 (schema) |

---

## 6. Design Decisions Register

| # | Decision | Rationale | Constraints Imposed |
|---|----------|-----------|---------------------|
| D1 | WF_RUN_CONSENSUS_SLOTS_V0 governs finite, declared-schedule bounded runs only — it is NOT a live-protocol artifact | Live operation is architecturally distinct: tx submission (8 typed WFs) and block proposal (WF_PROPOSE_BLOCK_V0) are two decoupled perpetual streams; there is no single governing loop and no concept of termination. The WF is the right artifact for any bounded scenario where the slot sequence has a declared end — test runs, replay windows, simulation batches | WF_RUN_CONSENSUS_SLOTS_V0 and CC_EXECUTE_SLOT_SEQUENCE_V0 are bounded-run artifacts; they must not be described as live-compatible |
| D2 | Slot iteration absorbed inside CC_EXECUTE_SLOT_SEQUENCE_V0 (Collatz pattern) | PGS WF is a DAG — no WF-level looping; iteration with side effects must live inside a CC | WF_RUN_CONSENSUS_SLOTS_V0 DAG is linear; loop logic is entirely inside the CC |
| D3 | Termination declared by finite slot_schedule in IN payload | PGS zero-inference: no ambient signals, no runtime kill flags; the bound is in the contract | IN_CONSENSUS_SLOTS_V0 must declare slot_schedule as a required list; CC exits when list is exhausted |
| D4 | Live and test are not different modes of the same WF — they are different operational architectures | Test: CC_EXECUTE_SLOT_SEQUENCE_V0 couples tx submission and block proposal into one governed execution with declared termination — one trace, one IN, one CC exits when the schedule is exhausted. Live: actors submit txs independently at any time via 8 typed WFs; a daemon fires WF_PROPOSE_BLOCK_V0 at each slot boundary; the two streams are decoupled, have no common coordinator, and carry no termination concept. There is no single artifact that bridges them | WF_PROPOSE_BLOCK_V0 single-slot semantics are unchanged; no new artifact is needed for live operation |
| D5 | status / effective_balance are canonical validator fields; enrollment_status / stake are retired | CC_WRITE_VALIDATOR_RECORD_V0 stores status + effective_balance; query filter must match stored fields | CC_QUERY_ELIGIBLE_VALIDATORS_V0 filter uses {status: "ACTIVE_ONGOING", effective_balance: "present"}; enrollment_status / stake eliminated |
| D6 | Validator schema fix included in this CR, not deferred | The registration → eligibility path is a blocker for the test scenario; a workaround payload is not a governed contract | IN_VALIDATOR_REGISTERED_V0 and CC_QUERY_ELIGIBLE_VALIDATORS_V0 must be updated before test execution |
| D7 | Option A for slot/epoch resolution: caller computes and includes in IN payload | Keeps the governed single-slot WF lean; the consensus loop CC is the natural owner of slot arithmetic | IN_BLOCK_PROPOSED_V0 gains slot + epoch; no new CT for arithmetic derivation |

---

## 7. Authoring Scope

### In Scope — This CR

| Capability | Artifact(s) | Gap Ref | Action |
|-----------|-------------|---------|--------|
| Governed finite consensus loop | IN_CONSENSUS_SLOTS_V0, WF_RUN_CONSENSUS_SLOTS_V0 | G4 | NEW |
| Slot loop execution (Collatz pattern) | CC_EXECUTE_SLOT_SEQUENCE_V0 | G4 | NEW |
| Post-run result verification | CC_VERIFY_SLOT_RESULTS_V0 | G4 | NEW |
| slot + epoch in block proposal IN | IN_BLOCK_PROPOSED_V0 | G2 | UPDATE |
| slot + epoch wired in block proposal WF | WF_PROPOSE_BLOCK_V0 | G2 | UPDATE |
| SYSTEM WF tx dedup CS wiring | RB_MINT_V0, RB_BURN_V0, RB_POOL_V0, RB_REWARD_V0, RB_SLASH_V0 | G5 | UPDATE |
| Validator schema alignment | IN_VALIDATOR_REGISTERED_V0, CC_QUERY_ELIGIBLE_VALIDATORS_V0 | G6 | UPDATE |
| Test data population | blockchain_testdata.md (existing) | G1/G3 | REUSE |

### Deferred — Future CR

| Capability | Deferred Reason |
|-----------|-----------------|
| Block attestation | Scope boundary — consensus_attest CR |
| Block finalization + chain commitment + balance reconciliation | Scope boundary — consensus_finalize CR |
| Live unbounded consensus loop (daemon mode) | Not needed for test scenario; daemon pattern (per-slot WF_PROPOSE_BLOCK_V0 invocation) requires no new artifact |
| WF_REGISTER_VALIDATOR_V0 CT assembly step (computed fields) | Optional governed improvement — caller-supplied fields are viable; no runtime blocker |

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 1 — Input Elicitation | Problem + Outcome + Known Facts | COMPLETE |
| Stage 2 — Domain Model Discovery | Entities, Processes, PPS Baseline, Gap Analysis | COMPLETE |
| Stage 3 — Analysis Loop | Q1–Q6 resolved; 2 iterations; 6 gaps registered and resolved | COMPLETE — SATURATED |
| Stage 4 — Business Model | This document | COMPLETE |
| Stage 5 — Business Intent | COMPLETE |
| Stage 6 — Governance Intent | PENDING |
| Stage 6b — Design Intent | PENDING |
| Stage 7 — Authoring Mandate | PENDING |
| Stage 8 — Authoring Manifest | PENDING |

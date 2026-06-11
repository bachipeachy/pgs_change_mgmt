# Stage 2 — Domain Model Discovery: blockchain / orchestration
**Stage:** 2 — Domain Model Discovery  
**CR:** 1_change_request_orchestration_v0.md  
**Status:** COMPLETE  
**Feeds:** Stage 3 — Analysis Loop  

---

## 1. Business Entities

### Simulation Run
A bounded, governed execution of the full blockchain chain simulation — consensus loop and TX workload running concurrently. Declared by a simulation controller invocation with explicit configuration. Has a definite start and a definite end (when both the consensus loop and TX workload have completed their governed termination criteria).

| Attribute | Description |
|-----------|-------------|
| slot_duration_seconds | How long each slot lasts (governs the consensus loop timer cadence) |
| max_slots | Total number of slots to execute before the consensus loop terminates |
| tx_interval_seconds | Interval between consecutive TX submissions in the workload |
| tx_sequence | Ordered list of transaction types to submit (cycles through: MINT, TRANSFER, BURN, STAKE, UNSTAKE, etc.) |
| triggered_by | Actor initiating the simulation |
| status | RUNNING → COMPLETE |

### Slot Clock
Protocol-visible state representing the current position of the simulation in the slot sequence. Owned by the orchestration subdomain. Replaces the external script's sleep-based slot timing.

| Attribute | Description |
|-----------|-------------|
| current_slot | Slot number currently being or about to be executed |
| slot_start_ts | Timestamp at which the current slot began |
| slot_duration_seconds | Configured duration per slot |
| max_slots | Terminal slot number — when current_slot exceeds this, the consensus loop terminates |

### Slot Execution
A single discrete consensus slot execution unit. One slot = one governed invocation = one trace = complete. Receives slot identity fields and triggers block proposal against whatever transactions are pending in the mempool at that moment.

| Attribute | Description |
|-----------|-------------|
| slot_number | Sequential slot identifier |
| epoch | Epoch this slot belongs to |
| timestamp | Governed timestamp of this slot (derived from slot clock, not from external sleep) |
| triggered_by | Actor initiating this slot execution |

### TX Workload
A governed stream of independently submitted transactions running concurrently with the consensus loop. Not bound to any specific slot. Transactions enter the mempool freely; the consensus loop reads whatever is pending at proposal time. Governs its own pace (tx_interval_seconds), sequence (tx_sequence), and termination (max_transactions or simulation end signal).

| Attribute | Description |
|-----------|-------------|
| tx_interval_seconds | Interval between consecutive TX submissions |
| tx_sequence | Ordered list of TX types to cycle through |
| max_transactions | Maximum number of TXs to submit before workload terminates |
| current_index | Position in the tx_sequence cycle |
| status | RUNNING → COMPLETE |

### Simulation Configuration
The declared input parameters that govern a simulation run. Passed at launch; owned by the simulation controller. Replaces the hardcoded values in `scripts/test_blockchain_e2e.py`.

| Attribute | Description |
|-----------|-------------|
| slot_duration_seconds | Consensus loop slot cadence |
| max_slots | Consensus loop termination criterion |
| tx_interval_seconds | TX workload submission pace |
| tx_sequence | TX type rotation sequence |
| max_transactions | TX workload termination criterion |
| triggered_by | Initiating actor |

---

## 2. Business Processes

### Process 1 — Chain Simulation Launch
The simulation controller starts the consensus loop and TX workload as concurrent workers, then waits for both to complete.

1. Simulation configuration is validated and accepted
2. Consensus loop coordinator is started as a concurrent worker (governs slot progression)
3. TX workload coordinator is started as a concurrent worker (governs independent TX submission)
4. Simulation controller waits for both workers to signal completion
5. Simulation controller records the simulation outcome and terminates

### Process 2 — Slot Progression
For each slot in the consensus loop:

1. Slot clock is read — current slot number and timestamp are determined from governed state
2. Slot execution unit is invoked (one discrete governed invocation, one trace)
3. Slot execution triggers block proposal, which reads pending transactions from the mempool and proposes a block
4. Slot clock is advanced from slot N to slot N+1
5. Consensus loop coordinator checks termination criteria (current_slot > max_slots) — if met, worker signals completion

### Process 3 — TX Workload Execution
For each TX submission in the workload:

1. TX workload coordinator determines the next TX type from the tx_sequence (cyclic)
2. TX submission unit is invoked (one discrete governed invocation, one trace)
3. TX is built, signed, validated, and written to the mempool
4. TX workload coordinator waits tx_interval_seconds before the next submission
5. TX workload coordinator checks termination criteria (max_transactions reached or simulation end signal) — if met, worker signals completion

---

## 3. PPS Baseline — What Already Exists

### WF_RUN_CONSENSUS_SLOTS_V0
Governs a finite ordered sequence of consensus slots using the Collatz pattern. The slot loop is absorbed inside CC_EXECUTE_SLOT_SEQUENCE_V0; this WF DAG is linear (3 nodes: IN → execute → verify → EXIT). Currently lives in the `consensus_pos` subdomain.

**Critical shape detail:** Each slot in the `slot_schedule` input carries embedded transactions. CC_EXECUTE_SLOT_SEQUENCE_V0 processes the slot's `transactions` sub-sequence (submitting each via typed TX WFs) BEFORE invoking WF_PROPOSE_BLOCK_V0. TXs are bound to slots at schedule construction time — not floating freely in the mempool.

**Fit for this CR:** Partial — the finite slot sequence structure and Collatz pattern are reusable. The embedded TX dispatch per slot is a mismatch with the orchestration model where TXs flow independently into the mempool from a concurrent workload. This WF would need to be superseded by a slot-only execution unit with no embedded TX dispatch.

### CC_EXECUTE_SLOT_SEQUENCE_V0
The Collatz loop container for the slot sequence. Uses CS_WORKFLOW_LOOP_V0 with a declarative dispatch spec. Processes per-slot TX sub-sequence before invoking WF_PROPOSE_BLOCK_V0.

**Fit for this CR:** Partial — loop container pattern and CS_WORKFLOW_LOOP_V0 dispatch are directly reusable. The `item_sub_sequence` TX dispatch section is a mismatch — it would be removed in the orchestration model. A new version or replacement would contain only the `item_wf` (slot execution unit invocation) with no sub-sequence.

### WF_PROPOSE_BLOCK_V0
Governs a full consensus proposer selection round: query eligible validators → select proposer → read pending transactions from mempool → form block → drain mempool → record round (or skip if no validators or no pending TXs). Already reads from and drains the mempool subdomain.

**Fit for this CR:** Exact match — this is the governed capability that the slot execution unit invokes. No changes required. WF_PROPOSE_BLOCK_V0 already handles the "mempool may be empty" case (skip round).

### WF_SUBMIT_TRANSACTION_V0
Full ETH transaction submission pipeline: validate intent → build → sign → hash → reserve nonce → validate policy → write to mempool → append event. Writes the pending TX to the mempool store.

**Fit for this CR:** Exact match for the TX workload's discrete TX submission unit. The TX workload coordinator governs repeated invocations of WF_SUBMIT_TRANSACTION_V0 (or the appropriate typed TX WF). No changes required.

### Typed Transaction WFs (WF_TRANSFER_V0, WF_MINT_V0, WF_BURN_V0, WF_STAKE_V0, WF_UNSTAKE_V0, etc.)
Type-specific TX submission workflows. Currently dispatched by CC_EXECUTE_SLOT_SEQUENCE_V0's sub-sequence per slot.

**Fit for this CR:** Exact match for the TX workload's dispatch-by-type mechanism. The TX workload coordinator would dispatch to the appropriate typed WF based on the current tx_sequence entry. No changes to these WFs required.

### scripts/test_blockchain_e2e.py — Current Orchestrator
The test script currently owns: slot_schedule construction (from slot_specs.json seed), inter-slot sleep timing (SLOT_DELAY_SECONDS), sequential slot invocation, and all orchestration coordination. It has no concurrency — TX submissions are embedded in each slot's slot_schedule entry.

**Fit for this CR:** To be refactored. Orchestration logic (slot timing, TX dispatch, concurrent coordination) moves into the governed orchestration subdomain. The script becomes a thin config/param entry point (shell or minimal Python) that passes slot_duration_seconds, max_slots, tx_interval_seconds, and tx_sequence to the simulation controller.

---

## 4. Gap Analysis — What Is Missing

### Gap 1 — No Governed Slot Clock (CRITICAL)
No protocol-visible state for slot position exists. Slot timing is managed by `time.sleep(SLOT_DELAY_SECONDS)` in the test script. The current slot number and slot duration are not governed, not auditable, and not inspectable.

**Impact:** The slot execution unit cannot read governed slot state. Slot progression cannot be traced. Temporal drift between the external timer and the protocol state cannot be detected.

### Gap 2 — No Simulation Controller (CRITICAL)
No governed artifact owns: starting concurrent workers, declaring termination criteria, or waiting for both the consensus loop and TX workload to complete. The test script performs this coordination outside the governance boundary.

**Impact:** Concurrent coordination of the consensus loop and TX workload is ungoverned. The boundary between transport-layer concurrency (execution mechanics) and protocol-layer coordination (orchestration intent) cannot be drawn without a governed simulation controller artifact.

### Gap 3 — No TX Workload Coordinator (CRITICAL)
No governed artifact owns: the TX submission sequence, the TX interval, the TX type rotation, or TX workload termination. TXs are currently embedded in the per-slot `slot_schedule` structure — there is no independent TX workload.

**Impact:** TX submissions cannot run concurrently and independently from the consensus loop. Realistic mempool evolution (multiple TXs accumulating before a block is proposed) cannot be tested or governed.

### Gap 4 — WF_RUN_CONSENSUS_SLOTS_V0 Embeds TX Dispatch Per Slot (CRITICAL)
The current slot sequence WF binds TX types to specific slots at schedule construction time (via `slot_schedule[].transactions`). The orchestration model requires slot execution to be TX-agnostic — block proposal reads whatever is pending in the mempool at that moment.

**Impact:** Reusing WF_RUN_CONSENSUS_SLOTS_V0 as-is would perpetuate the per-slot TX binding, preventing independent concurrent TX workload operation. A slot execution unit that does not embed TX dispatch is required.

### Gap 5 — slot_specs.json Seed Drives Per-Slot TX Assignment (OPEN QUESTION)
The current seed data (`seeds/blockchain/consensus_pos/slot_specs.json`) defines TX types per slot. With the orchestration model, TX types are owned by the TX workload configuration — not by a per-slot seed. 

**Impact:** The role of slot_specs.json must be resolved. Does it become a simulation configuration seed (slot_duration, max_slots, tx_interval, tx_sequence)? Or is it removed entirely in favour of governed simulation configuration input?

### Gap 6 — Termination Protocol Between Concurrent Workers (OPEN QUESTION)
When both the consensus loop and TX workload complete, how does the simulation controller detect completion? The transport-layer implementation (asyncio.gather, threading) handles physical termination, but the governed protocol artifact must declare the termination semantics: what signals completion, and what constitutes a successful simulation run vs. a failed one?

**Impact:** Without a declared termination contract, the simulation controller cannot produce a governed outcome (SUCCESS / VIOLATION) with full trace coverage.

---

## 5. Summary: Extend vs. New Subdomain

**The question:** Does orchestration belong inside `blockchain::consensus_pos` (extending the existing slot execution WF) or does it require a new `blockchain::orchestration` subdomain?

**Evidence for extend (consensus_pos):** WF_RUN_CONSENSUS_SLOTS_V0 already governs finite slot sequences. The slot progression logic overlaps with what orchestration needs.

**Evidence for new subdomain:** Orchestration owns concerns that cross multiple subdomains (consensus_pos, transaction, mempool) — it is not a consumer of one subdomain, it is a coordinator across several. The simulation controller, slot clock, and TX workload are governance concerns that do not belong to any existing subdomain. The "when and in what sequence business workflows execute" concern is architecturally separate from "how a slot proposes a block." Extending consensus_pos would conflate coordination with execution.

*The CR already classified this as a new subdomain at Stage 0. Stage 2 evidence confirms that classification.*

---

## 6. Stage 2 Decisions — Open Questions Resolved

All five open questions resolved before Stage 3. Decisions are binding for the Analysis Loop.

| # | Question | Decision | Rationale |
|---|----------|----------|-----------|
| Q1 | Supersede or extend WF_RUN_CONSENSUS_SLOTS_V0? | **Supersede** — create WF_PROCESS_SLOT_V0; leave WF_RUN_CONSENSUS_SLOTS_V0 unchanged as a historical artifact | The existing artifact has two responsibilities: slot execution and simulation sequencing. Stage 3 separates those concerns. New concern = new artifact, not a version bump. WF_RUN_CONSENSUS_SLOTS_V1 would imply the same thing — it is not. |
| Q2 | WF_PROCESS_SLOT_V0 invokes WF_PROPOSE_BLOCK_V0 or consensus CCs directly? | **Invoke WF_PROPOSE_BLOCK_V0** — orchestration orchestrates governed WFs, never reaches into another domain's CCs directly | Cross-domain CC coupling would make orchestration dependent on consensus internals. Clean layering: orchestration → consensus WF → consensus CCs. Orchestration is a coordinator, not a consumer of capability contracts from other domains. |
| Q3 | What replaces slot_specs.json? | **SEED_CHAIN_SIMULATION_CONFIG_V0** — a new seed file at seeds/blockchain/orchestration/ | Simulation config is launch configuration — not runtime state, not mutable during execution. Seed is the correct PGS location. A mutable CS store would be wrong: configuration does not evolve during a simulation run. |
| Q4 | Simulation controller termination contract? | **WF_RUN_CHAIN_SIMULATION_V0 returns SUCCESS / VIOLATION** with output fields: slots_processed, blocks_proposed, transactions_submitted, transactions_confirmed, violations_detected | Simulation controller is analogous to a governed test runner. SUCCESS = all slots executed + workload completed + no invariant violations. VIOLATION = any sub-workflow failure, invariant failure, consensus failure, or unexpected abort. Output is the simulation summary artifact. |
| Q5 | TX workload dispatches to typed WFs or WF_SUBMIT_TRANSACTION_V0? | **Dispatch to WF_SUBMIT_TRANSACTION_V0 with tx_type as payload** — never dispatch to WF_MINT_V0, WF_TRANSFER_V0, etc. from within orchestration | Orchestration knows "submit transaction" — not transaction taxonomy. Dispatching to typed WFs would leak the transaction subdomain's internal type taxonomy into the orchestration layer. TX type is a payload field, not a routing decision owned by orchestration. |

---

## 7. Greenlit Artifact Set for Stage 3

```
blockchain/
├── orchestration/                         ← NEW subdomain
│   ├── WF_RUN_CHAIN_SIMULATION_V0         ← simulation controller (owns: clock, termination, dispatch)
│   ├── WF_RUN_CONSENSUS_LOOP_V0           ← consensus loop coordinator (governs repeated WF_PROCESS_SLOT_V0 invocations)
│   ├── WF_RUN_TX_WORKLOAD_V0              ← TX workload coordinator (governs repeated WF_SUBMIT_TRANSACTION_V0 invocations)
│   ├── WF_PROCESS_SLOT_V0                 ← atomic slot execution unit (one slot = one trace)
│   └── SEED_CHAIN_SIMULATION_CONFIG_V0    ← launch configuration seed
│
├── consensus_pos/
│   └── WF_PROPOSE_BLOCK_V0               ← no change; invoked by WF_PROCESS_SLOT_V0
│
└── transaction/
    └── WF_SUBMIT_TRANSACTION_V0          ← no change; invoked by WF_RUN_TX_WORKLOAD_V0
```

WF_RUN_CONSENSUS_SLOTS_V0 and CC_EXECUTE_SLOT_SEQUENCE_V0 remain in the snapshot unchanged as historical artifacts. No deprecation action required at this stage.

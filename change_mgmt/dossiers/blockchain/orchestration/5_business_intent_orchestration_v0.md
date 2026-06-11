# Business Intent: orchestration
**Domain:** blockchain  
**Subdomain:** orchestration  
**Version:** V0  
**Status:** COMPLETE  

---

## Subdomain Purpose

The orchestration subdomain governs the coordination of concurrent, time-driven blockchain domain workflows. V0 establishes the chain simulation capability: a governed simulation run that starts a consensus loop and a transaction submission workload as concurrent workers, maintains protocol-visible slot clock state, and records a governed simulation summary upon completion. Orchestration owns the scheduling intent (what runs, when, and under what termination criteria), not the execution mechanics (threads, event loops, OS timers). It is the governed entry point that replaces the coordination logic currently embedded in the external test script.

---

## Scope Boundary

### In Scope — V0

| Capability | Notes |
|-----------|-------|
| Chain Simulation Launch | Start consensus loop + TX workload concurrently; wait for both; record outcome |
| Slot Progression | Govern slot-by-slot execution: read clock → derive context → propose block → advance clock |
| TX Workload Execution | Govern independent TX submission workload: dispatch typed TXs at governed interval |
| Slot Clock State | Protocol-visible store for current slot position; owned exclusively by orchestration |
| Simulation Summary Recording | Governed output: slots_processed, blocks_proposed, tx_submitted, tx_confirmed, violations_detected |
| Simulation Configuration Seed | Pre-resolved launch parameters + TX payloads at seeds/blockchain/orchestration/ |
| Lifecycle retirement metadata for WF_RUN_CONSENSUS_SLOTS_V0 | Mark with lifecycle.status = RETIRED + successor artifact references |
| Refactor scripts/test_blockchain_e2e.py | Reduce to thin config/param entry point; move all coordination logic into this subdomain |

### Explicitly Deferred — Not In Scope

| Capability | Deferred To |
|-----------|-------------|
| AR_ governed retirement artifact family | Future pgs_governance CR — requires new PGS artifact type declaration |
| Compiler enforcement for RETIRED artifacts | Future pgs_governance CR — depends on AR_ family definition |
| WF_PROCESS_EPOCH_V0 (epoch-level coordination) | Future CR — epoch is an emergent property of slot progression in V0 |
| Distributed orchestration (lease, lock, leader election) | Future CR — no multi-node model justified yet |
| Generic pgs_orchestration substrate (cross-domain) | Future CR — abstract when second domain triggers same pattern |
| Event subscription / dispatch registry | Future CR — YAGNI for one use case |
| Simulation failure retry and slot expiry governance | Future CR — requires failure model design |

---

## Business Object Semantics

| Store Name | Business Record Model | Business Rationale |
|-----------|----------------------|--------------------|
| SLOT_CLOCK | Mutable State | One current record for the active simulation; updated each slot as the clock advances from N to N+1; single record per active simulation |
| SIMULATION_SUMMARY | Append-Only Journal | Immutable outcome record per simulation run; each run appends one summary; deletion would break audit integrity |

---

## Identity Semantics

### Primary Identity — SLOT_CLOCK

**Field:** `simulation_id`  
**Source:** Declared in SEED_CHAIN_SIMULATION_CONFIG_V0 at simulation launch  
**Role:** Keys the active slot clock record; one clock per active simulation run  
**Uniqueness:** One slot clock record per simulation_id; initialized at launch, advanced per slot, retired at completion

### Primary Identity — SIMULATION_SUMMARY

**Field:** `simulation_id`  
**Source:** Declared in simulation configuration at launch  
**Role:** Cross-references the simulation run in the summary record; links outcome to configuration  
**Uniqueness:** One summary per simulation run; append-only (no correction; violations are recorded, not corrected)

---

## Business Invariants

| # | Invariant | Business Reason |
|---|-----------|-----------------|
| 1 | One slot = one governed invocation = one trace = complete | PGS execution model — perpetual loop WFs violate the single-execution-unit principle; every WF must terminate |
| 2 | TX workload runs independently and concurrently with slot progression | TX submissions are not bound to specific slots; they accumulate freely in the mempool; binding them to slots contradicts the realistic mempool evolution model |
| 3 | Slot state (current slot, start timestamp, duration) is protocol-visible governed state | External sleep-based timing is unauditable; slot position must be inspectable and traceable at any point during simulation |
| 4 | Orchestration invokes governed WFs — never reaches into dependency subdomain CCs directly | Clean cross-domain layering; orchestration cannot call consensus_pos or transaction CCs; all dependency access is via the dependency subdomain's own WF |
| 5 | Bootstrap is a pre-condition for simulation launch | Orchestration does not create actors, wallets, or validators; those must exist before simulation is invoked |
| 6 | Termination criteria are declared at simulation launch | max_slots and max_transactions are configuration inputs, not runtime decisions; they cannot change during a simulation run |
| 7 | TX workload dispatches to typed TX WFs only | IN_TRANSACTION_SUBMITTED_V0 is RETIRED; typed TX schemas (MINT vs. TRANSFER) are structurally incompatible; no generic TX intent exists |

---

## Business Actions

| Business Action | Object Affected | Trigger | V0 Status |
|----------------|-----------------|---------|-----------|
| LAUNCH_SIMULATION | SLOT_CLOCK (init), SIMULATION_SUMMARY (write at end) | Simulation Operator (external trigger — cron, test harness, CLI) | In Scope |
| COORDINATE_CONSENSUS_LOOP | SLOT_CLOCK (advanced per slot) | Simulation Controller (internal — dispatched by LAUNCH_SIMULATION) | In Scope |
| COORDINATE_TX_WORKLOAD | Mempool (via TX submission WFs in dependency subdomains) | Simulation Controller (internal — dispatched by LAUNCH_SIMULATION) | In Scope |
| EXECUTE_SLOT | SLOT_CLOCK (read + advance), Block (via consensus_pos) | Consensus Loop Coordinator (internal — dispatched per slot by COORDINATE_CONSENSUS_LOOP) | In Scope |

---

## Actors

_This subdomain does not define new actors. The Simulation Operator is a transport-layer trigger — it carries no domain authority within the orchestration subdomain. Authority classes are defined in `5_business_intent_identity_v0.md` (AC_ENDUSER_V0, AC_SYSTEM_V0)._

---

## Intents (IN)

### IN_RUN_CHAIN_SIMULATION_V0
**Summary:** Admit a chain simulation launch request with explicit configuration  
**Workflow Binding:** `WF_RUN_CHAIN_SIMULATION_V0`

**Input Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| simulation_id | string | YES | Unique identifier for this simulation run; keys the slot clock and simulation summary records |
| slot_duration_seconds | integer | YES | Duration of each slot in seconds; governs consensus loop cadence |
| max_slots | integer | YES | Total number of slots to execute; consensus loop termination criterion |
| tx_interval_seconds | integer | YES | Interval between consecutive TX submissions; TX workload cadence |
| max_transactions | integer | YES | Maximum number of TXs to submit; TX workload termination criterion |
| tx_sequence | array | YES | Ordered list of TX payload objects to cycle through; each entry contains tx_type + fully resolved payload fields |
| triggered_by | string | YES | Actor initiating the simulation run |

**Outcomes:**

| Outcome | Description |
|---------|-------------|
| ACK | All required configuration fields present and valid; simulation launch admitted |
| NACK | Missing required fields, invalid configuration values (e.g. max_slots < 1), or malformed tx_sequence |

---

### IN_CONSENSUS_LOOP_STARTED_V0
**Summary:** Admit a consensus loop coordination request for a bounded slot sequence  
**Workflow Binding:** `WF_RUN_CONSENSUS_LOOP_V0`

**Input Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| simulation_id | string | YES | Identifies the active simulation; used to read the slot clock |
| slot_schedule | array | YES | Ordered list of slot_number entries from 0 to max_slots-1; governs loop iteration count |
| triggered_by | string | YES | Propagated from simulation launch |

**Outcomes:**

| Outcome | Description |
|---------|-------------|
| ACK | Consensus loop configuration valid; slot sequence admitted |
| NACK | Empty slot schedule, missing simulation_id, or invalid configuration |

---

### IN_TX_WORKLOAD_STARTED_V0
**Summary:** Admit a TX workload coordination request for a bounded TX submission sequence  
**Workflow Binding:** `WF_RUN_TX_WORKLOAD_V0`

**Input Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| tx_interval_seconds | integer | YES | Wait interval between consecutive TX submissions |
| tx_sequence | array | YES | Ordered list of TX payload objects; each entry carries tx_type + fully resolved payload |
| triggered_by | string | YES | Propagated from simulation launch |

**Outcomes:**

| Outcome | Description |
|---------|-------------|
| ACK | TX workload configuration valid; submission sequence admitted |
| NACK | Empty tx_sequence, missing required fields, or invalid interval |

---

### IN_SLOT_EXECUTION_STARTED_V0
**Summary:** Admit a single slot execution request  
**Workflow Binding:** `WF_PROCESS_SLOT_V0`

**Input Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| simulation_id | string | YES | Identifies the active simulation; used to read and advance the slot clock |
| slot_number | integer | YES | The slot number (= round_number) to execute; minimum 0 |
| triggered_by | string | YES | Propagated from consensus loop coordinator |

**Outcomes:**

| Outcome | Description |
|---------|-------------|
| ACK | Slot execution request valid; round number present and non-negative |
| NACK | Missing slot_number, negative value, or missing simulation_id |

---

## Workflows (WF)

### WF_RUN_CHAIN_SIMULATION_V0
**Summary:** Launch a bounded chain simulation — initialize slot clock, dispatch consensus loop and TX workload concurrently, wait for both to complete, record simulation summary  
**Subdomain:** `orchestration`  
**Start Node:** `IN_RUN_CHAIN_SIMULATION_V0`

**Execution Nodes:**

| Node | Type | Routing Outcomes |
|------|------|-----------------|
| IN_RUN_CHAIN_SIMULATION_V0 | IN | ACK → CC_INITIALIZE_SLOT_CLOCK_V0, NACK → EXIT |
| CC_INITIALIZE_SLOT_CLOCK_V0 | CC | SUCCESS → CC_DISPATCH_SIMULATION_WORKERS_V0, VIOLATION → EXIT, BACKEND_ERROR → EXIT |
| CC_DISPATCH_SIMULATION_WORKERS_V0 | CC | SUCCESS → CC_RECORD_SIMULATION_SUMMARY_V0, PARTIAL_FAILURE → CC_RECORD_SIMULATION_SUMMARY_V0, BACKEND_ERROR → EXIT |
| CC_RECORD_SIMULATION_SUMMARY_V0 | CC | SUCCESS → EXIT_SUCCESS, VIOLATION → EXIT, BACKEND_ERROR → EXIT |
| EXIT | EXIT | — |
| EXIT_SUCCESS | EXIT | — |

**CC Dependencies:** `CC_INITIALIZE_SLOT_CLOCK_V0`, `CC_DISPATCH_SIMULATION_WORKERS_V0`, `CC_RECORD_SIMULATION_SUMMARY_V0`

---

### WF_RUN_CONSENSUS_LOOP_V0
**Summary:** Coordinate a bounded sequence of slot executions — invoke WF_PROCESS_SLOT_V0 once per slot in the slot schedule via the Collatz loop pattern  
**Subdomain:** `orchestration`  
**Start Node:** `IN_CONSENSUS_LOOP_STARTED_V0`

**Execution Nodes:**

| Node | Type | Routing Outcomes |
|------|------|-----------------|
| IN_CONSENSUS_LOOP_STARTED_V0 | IN | ACK → CC_RUN_SLOT_SEQUENCE_V0, NACK → EXIT |
| CC_RUN_SLOT_SEQUENCE_V0 | CC | SUCCESS → EXIT_SUCCESS, VIOLATION → EXIT, BACKEND_ERROR → EXIT |
| EXIT | EXIT | — |
| EXIT_SUCCESS | EXIT | — |

**CC Dependencies:** `CC_RUN_SLOT_SEQUENCE_V0`

*Note: CC_RUN_SLOT_SEQUENCE_V0 absorbs the slot iteration loop internally via the Collatz loop substrate. The WF DAG is linear. Each slot execution (WF_PROCESS_SLOT_V0) is dispatched as a distinct governed invocation inside the CC.*

---

### WF_RUN_TX_WORKLOAD_V0
**Summary:** Coordinate a bounded TX submission workload — invoke the appropriate typed TX WF for each entry in the tx_sequence via the Collatz loop pattern with typed dispatch mapping  
**Subdomain:** `orchestration`  
**Start Node:** `IN_TX_WORKLOAD_STARTED_V0`

**Execution Nodes:**

| Node | Type | Routing Outcomes |
|------|------|-----------------|
| IN_TX_WORKLOAD_STARTED_V0 | IN | ACK → CC_RUN_TX_SEQUENCE_V0, NACK → EXIT |
| CC_RUN_TX_SEQUENCE_V0 | CC | SUCCESS → EXIT_SUCCESS, VIOLATION → EXIT, BACKEND_ERROR → EXIT |
| EXIT | EXIT | — |
| EXIT_SUCCESS | EXIT | — |

**CC Dependencies:** `CC_RUN_TX_SEQUENCE_V0`

*Note: CC_RUN_TX_SEQUENCE_V0 absorbs the TX iteration loop internally via the Collatz loop substrate with a tx_type dispatch mapping (MINT → WF_MINT_V0, TRANSFER → WF_TRANSFER_V0, etc.). Each TX submission is a distinct governed invocation. The tx_interval_seconds wait between submissions is handled by the loop substrate's inter-item timing.*

---

### WF_PROCESS_SLOT_V0
**Summary:** Execute a single consensus slot — read slot clock state, derive slot and epoch from round number, invoke block proposal, advance the slot clock  
**Subdomain:** `orchestration`  
**Start Node:** `IN_SLOT_EXECUTION_STARTED_V0`

**Execution Nodes:**

| Node | Type | Routing Outcomes |
|------|------|-----------------|
| IN_SLOT_EXECUTION_STARTED_V0 | IN | ACK → CC_READ_SLOT_CLOCK_V0, NACK → EXIT |
| CC_READ_SLOT_CLOCK_V0 | CC | SUCCESS → CC_PREPARE_SLOT_CONTEXT_V0, NOT_FOUND → EXIT, BACKEND_ERROR → EXIT |
| CC_PREPARE_SLOT_CONTEXT_V0 | CC | SUCCESS → CC_INVOKE_BLOCK_PROPOSAL_V0, VIOLATION → EXIT |
| CC_INVOKE_BLOCK_PROPOSAL_V0 | CC | SUCCESS → CC_ADVANCE_SLOT_CLOCK_V0, VIOLATION → EXIT, BACKEND_ERROR → EXIT |
| CC_ADVANCE_SLOT_CLOCK_V0 | CC | SUCCESS → EXIT_SUCCESS, VIOLATION → EXIT, BACKEND_ERROR → EXIT |
| EXIT | EXIT | — |
| EXIT_SUCCESS | EXIT | — |

**CC Dependencies:** `CC_READ_SLOT_CLOCK_V0`, `CC_PREPARE_SLOT_CONTEXT_V0`, `CC_INVOKE_BLOCK_PROPOSAL_V0`, `CC_ADVANCE_SLOT_CLOCK_V0`

---

## Capability Contracts (CC)

### CC_INITIALIZE_SLOT_CLOCK_V0
**Summary:** Write the initial slot clock record at simulation launch — sets slot=0, start_ts=launch timestamp, duration_seconds=configured slot duration

**Inputs:**

| Field | Type | Required |
|-------|------|----------|
| simulation_id | string | YES |
| slot_duration_seconds | integer | YES |
| triggered_by | string | YES |

**Outputs:**

| Field | Type |
|-------|------|
| result_status | string |

**Result Statuses:** `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`

**Pipeline Steps:**

| Step | Purpose |
|------|---------|
| write_slot_clock_initial | Write slot_number=0, start_ts=now, duration_seconds to the SLOT_CLOCK store keyed by simulation_id; prevents any slot execution before clock is initialized |

---

### CC_DISPATCH_SIMULATION_WORKERS_V0
**Summary:** Declare concurrent worker dispatch intent — invoke WF_RUN_CONSENSUS_LOOP_V0 and WF_RUN_TX_WORKLOAD_V0 concurrently; wait for both to complete; return aggregate result status

**Inputs:**

| Field | Type | Required |
|-------|------|----------|
| simulation_id | string | YES |
| slot_schedule | array | YES |
| slot_duration_seconds | integer | YES |
| tx_interval_seconds | integer | YES |
| tx_sequence | array | YES |
| triggered_by | string | YES |

**Outputs:**

| Field | Type |
|-------|------|
| consensus_result | object |
| tx_workload_result | object |
| all_succeeded | boolean |

**Result Statuses:** `SUCCESS`, `PARTIAL_FAILURE`, `BACKEND_ERROR`

**Pipeline Steps:**

| Step | Purpose |
|------|---------|
| dispatch_concurrent_workers | Invoke WF_RUN_CONSENSUS_LOOP_V0 and WF_RUN_TX_WORKLOAD_V0 concurrently via CS_CONCURRENT_WORKFLOWS_V0; return SUCCESS only when both complete without violation; PARTIAL_FAILURE when either returns a non-SUCCESS result; preserves sub-WF results for summary recording |

---

### CC_RECORD_SIMULATION_SUMMARY_V0
**Summary:** Aggregate sub-workflow results and append a governed simulation summary record — produces SUCCESS or VIOLATION outcome with full output fields

**Inputs:**

| Field | Type | Required |
|-------|------|----------|
| simulation_id | string | YES |
| consensus_result | object | YES |
| tx_workload_result | object | YES |
| all_succeeded | boolean | YES |
| triggered_by | string | YES |

**Outputs:**

| Field | Type |
|-------|------|
| simulation_outcome | string |
| slots_processed | integer |
| blocks_proposed | integer |
| transactions_submitted | integer |
| transactions_confirmed | integer |
| violations_detected | integer |

**Result Statuses:** `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`

**Pipeline Steps:**

| Step | Purpose |
|------|---------|
| aggregate_results | Derive slots_processed, blocks_proposed, tx_submitted, tx_confirmed, violations_detected from sub-WF execution results |
| append_simulation_summary | Append the complete simulation summary record to the SIMULATION_SUMMARY store; records the run outcome permanently |

---

### CC_RUN_SLOT_SEQUENCE_V0
**Summary:** Execute the full slot sequence by iterating over the slot schedule and invoking WF_PROCESS_SLOT_V0 for each slot via the Collatz loop substrate

**Inputs:**

| Field | Type | Required |
|-------|------|----------|
| simulation_id | string | YES |
| slot_schedule | array | YES |
| triggered_by | string | YES |

**Outputs:**

| Field | Type |
|-------|------|
| items_processed | integer |

**Result Statuses:** `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`

**Pipeline Steps:**

| Step | Purpose |
|------|---------|
| execute_slot_sequence | Iterate over slot_schedule via CS_WORKFLOW_LOOP_V0; invoke WF_PROCESS_SLOT_V0 for each slot_number; terminate when all slots are processed or a VIOLATION is returned |

---

### CC_RUN_TX_SEQUENCE_V0
**Summary:** Execute the TX submission workload by iterating over the tx_sequence and invoking the appropriate typed TX WF for each entry via the Collatz loop substrate with typed dispatch mapping

**Inputs:**

| Field | Type | Required |
|-------|------|----------|
| tx_sequence | array | YES |
| tx_interval_seconds | integer | YES |
| triggered_by | string | YES |

**Outputs:**

| Field | Type |
|-------|------|
| items_processed | integer |
| sub_items_processed | integer |

**Result Statuses:** `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`

**Pipeline Steps:**

| Step | Purpose |
|------|---------|
| execute_tx_sequence | Iterate over tx_sequence via CS_WORKFLOW_LOOP_V0 with tx_type dispatch mapping; invoke WF_MINT_V0, WF_TRANSFER_V0, WF_BURN_V0, WF_STAKE_V0, WF_UNSTAKE_V0 etc. per tx_type; apply tx_interval_seconds wait between submissions; terminate at sequence end or VIOLATION |

---

### CC_READ_SLOT_CLOCK_V0
**Summary:** Read the current slot clock state for the active simulation — provides slot_start_ts and slot_duration_seconds to the slot execution pipeline

**Inputs:**

| Field | Type | Required |
|-------|------|----------|
| simulation_id | string | YES |

**Outputs:**

| Field | Type |
|-------|------|
| current_slot | integer |
| slot_start_ts | string |
| slot_duration_seconds | integer |

**Result Statuses:** `SUCCESS`, `NOT_FOUND`, `BACKEND_ERROR`

**Pipeline Steps:**

| Step | Purpose |
|------|---------|
| read_slot_clock | Read the SLOT_CLOCK record for simulation_id; NOT_FOUND means the clock was never initialized — a hard failure, not a graceful skip |

---

### CC_PREPARE_SLOT_CONTEXT_V0
**Summary:** Derive slot and epoch from round_number using pure computation — produces the slot context fields required by WF_PROPOSE_BLOCK_V0

**Inputs:**

| Field | Type | Required |
|-------|------|----------|
| slot_number | integer | YES |
| slot_start_ts | string | YES |
| slots_per_epoch | integer | NO |

**Outputs:**

| Field | Type |
|-------|------|
| round_number | integer |
| slot | integer |
| epoch | integer |
| timestamp | string |

**Result Statuses:** `SUCCESS`, `VIOLATION`

**Pipeline Steps:**

| Step | Purpose |
|------|---------|
| derive_slot_epoch | Invoke CT_PURE_DERIVE_SLOT_EPOCH_V0: slot = slot_number % slots_per_epoch (default 32); epoch = slot_number // slots_per_epoch; pass slot_start_ts as timestamp; these fields satisfy the IN_BLOCK_PROPOSED_V0 required inputs exactly |

---

### CC_INVOKE_BLOCK_PROPOSAL_V0
**Summary:** Invoke WF_PROPOSE_BLOCK_V0 for the current slot — dispatches the slot execution context to the consensus_pos subdomain's block proposal workflow

**Inputs:**

| Field | Type | Required |
|-------|------|----------|
| round_number | integer | YES |
| slot | integer | YES |
| epoch | integer | YES |
| timestamp | string | YES |
| triggered_by | string | YES |

**Outputs:**

| Field | Type |
|-------|------|
| result_status | string |
| execution_result | object |

**Result Statuses:** `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`

**Pipeline Steps:**

| Step | Purpose |
|------|---------|
| invoke_block_proposal | Invoke WF_PROPOSE_BLOCK_V0 via CS_WORKFLOW_GATEWAY_V0 with the prepared slot context fields; clean cross-domain boundary — orchestration submits a fully formed intent payload to the consensus_pos WF and receives the result; never touches consensus_pos CCs directly |

---

### CC_ADVANCE_SLOT_CLOCK_V0
**Summary:** Advance the slot clock from slot N to slot N+1 after slot execution completes — updates current_slot and records the new slot start timestamp

**Inputs:**

| Field | Type | Required |
|-------|------|----------|
| simulation_id | string | YES |
| current_slot | integer | YES |

**Outputs:**

| Field | Type |
|-------|------|
| result_status | string |
| next_slot | integer |

**Result Statuses:** `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`

**Pipeline Steps:**

| Step | Purpose |
|------|---------|
| advance_slot_clock | Write slot_number=current_slot+1 and start_ts=now to the SLOT_CLOCK store; slot advancement is a governed, traceable action — not a sleep call; records that governance has moved from slot N to slot N+1 |

---

## Cross-Subdomain References

The following Capability Contracts and Workflows are defined in other subdomains and invoked by this subdomain's workflows:

| Artifact | Defined In | Role In Orchestration |
|----------|-----------|----------------------|
| WF_PROPOSE_BLOCK_V0 | consensus_pos | Invoked by CC_INVOKE_BLOCK_PROPOSAL_V0 (via CS_WORKFLOW_GATEWAY_V0) for each slot execution |
| WF_MINT_V0, WF_TRANSFER_V0, WF_BURN_V0, WF_STAKE_V0, WF_UNSTAKE_V0, WF_POOL_V0, WF_REWARD_V0, WF_SLASH_V0 | transaction | Invoked by CC_RUN_TX_SEQUENCE_V0 (via CS_WORKFLOW_LOOP_V0 dispatch mapping) for each TX in the workload |
| CT_PURE_DERIVE_SLOT_EPOCH_V0 | orchestration (new) | Called by CC_PREPARE_SLOT_CONTEXT_V0; pure computation — derives slot and epoch from round_number |

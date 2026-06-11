# Authoring Mandate: blockchain / orchestration
**Domain:** blockchain  
**Subdomain:** orchestration  
**Version:** V0  
**Status:** COMPLETE  
**Pipeline Stage:** Stage 7 — Authoring Mandate  
**Produced by:** v0.5.0 SDLC authoring pipeline  
**Input:** 6b_design_intent_orchestration_v0.md (Stage 6b — COMPLETE)

---

## Overview

This CR produces **25 authoring actions** across two repositories:

| Repository | Subdomain | Actions | Breakdown |
|-----------|-----------|---------|-----------|
| `pgs_blockchain` | orchestration (new) | 23 | 1 STRUCTURE + 4 IN + 4 WF + 9 CC + 1 CT + 4 RB |
| `pgs_blockchain` | (cross-subdomain patch) | 1 | 1 LIFECYCLE PATCH (WF_RUN_CONSENSUS_SLOTS_V0) |
| `pgs_capabilities` | capability_side_effects | 1 | 1 CS NEW |
| `pgs_workspace` | seeds | 1 | 1 SEED FILE NEW |
| **Total** | | **26** | |

**REUSE artifacts (no changes):** `CS_MUTABLE_JSON_V0`, `CS_APPENDONLY_JSONL_V0`, `CS_WORKFLOW_LOOP_V0`, `CS_WORKFLOW_GATEWAY_V0`, `WF_PROPOSE_BLOCK_V0`, `WF_MINT_V0`, `WF_TRANSFER_V0`, `WF_BURN_V0`, `WF_STAKE_V0`, `WF_UNSTAKE_V0`, `WF_POOL_V0`, `WF_REWARD_V0`, `WF_SLASH_V0`, `AC_SYSTEM_V0`, `STRUCTURE_BLOCKCHAIN_STORAGE_V0`.

**New module directories required (pgs_blockchain):**
```
pgs_blockchain/registry/orchestration/
pgs_blockchain/registry/orchestration/intents/
pgs_blockchain/registry/orchestration/workflows/
pgs_blockchain/registry/orchestration/capability_contracts/
pgs_blockchain/registry/orchestration/capability_transforms/
pgs_blockchain/registry/orchestration/runtime_bindings/
pgs_blockchain/implementation/orchestration/
```

*Note: STRUCTURE_BLOCKCHAIN_ORCHESTRATION_STORAGE_V0 lives directly at `pgs_blockchain/registry/orchestration/` — no `structures/` subdirectory. Matches the pattern of `STRUCTURE_BLOCKCHAIN_STORAGE_V0` at `pgs_blockchain/registry/`.*

---

## Build Dependency Order

### Wave 1 — Foundation (no dependencies on new artifacts)

**Step 1**
```
Artifact:    blockchain::STRUCTURE_BLOCKCHAIN_ORCHESTRATION_STORAGE_V0
Action:      NEW
Module:      pgs_blockchain.registry.orchestration
Depends on:  nothing
PPS status:  NOT PRESENT — must author
```

Declare storage topology for the orchestration subdomain and register artifact families.

**Entity Stores:**

| Entity Name | Substrate | Path | Semantics |
|-------------|-----------|------|-----------|
| `SLOT_CLOCK` | `CS_MUTABLE_JSON_V0` | `blockchain/orchestration/state/slot_clock.json` | Keyed mutable record; one active record per simulation_id; initialized at launch; advanced per slot |
| `SIMULATION_SUMMARY` | `CS_APPENDONLY_JSONL_V0` | `blockchain/orchestration/events/simulation_summary.jsonl` | Append-only journal; one record per completed simulation run; immutable after write |

**Artifact Families Declared:** IN, WF, CC, CT, RB — all under subdomain `orchestration`.

**Ownership Invariant:** Declare explicitly — no non-orchestration artifact may directly mutate these stores.

**Simulation Isolation:** Declare explicitly — `simulation_id` is the primary isolation boundary; each simulation run owns exactly one SLOT_CLOCK record; concurrent simulation runs do not collide.

---

**Step 2**
```
Artifact:    capability_side_effects::CS_CONCURRENT_WORKFLOWS_V0
Action:      NEW
Module:      pgs_capabilities.registry.capability_side_effects (new file in existing module)
Depends on:  nothing
PPS status:  NOT PRESENT — must author
```

New infrastructure CS. Declare one operation: `EXECUTE_CONCURRENT`.

**Operation: EXECUTE_CONCURRENT**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `workflows` | array | YES | Ordered list of WF invocation specs; each entry: `{code: FQDN, payload: object}`; each `code` must be unique within a single invocation |
| `triggered_by` | string | YES | Actor ID — available for injection into child WF payloads |

**Outputs:**

| Field | Type | Description |
|-------|------|-------------|
| `results` | array | One entry per invoked WF: `{code: FQDN, result_status: string, outputs: object}`; correlated by `code` field, NOT by array position |
| `all_succeeded` | boolean | `true` iff every WF returned `SUCCESS`; `false` if any returned `VIOLATION` or `BACKEND_ERROR` |

**Result Status Values:** `SUCCESS`, `PARTIAL_FAILURE`, `BACKEND_ERROR`

**Contract invariants to declare in the artifact:**
- Workflow completion ordering is not guaranteed
- Results are correlated by `code` (workflow FQDN) — callers must use `code` as the lookup key, not array index
- Implementation uses `asyncio.gather` at the RB layer — the CS declares intent; the RB implements concurrency mechanics

**Idempotent:** false

**Category:** execution_gateway / internal

---

**Step 3**
```
Artifact:    blockchain::CT_PURE_DERIVE_SLOT_EPOCH_V0
Action:      NEW
Module:      pgs_blockchain.registry.orchestration.capability_transforms
Depends on:  nothing
PPS status:  NOT PRESENT — must author
```

Pure computation. Zero side effects. Zero CS calls (CT purity invariant — enforce in artifact declaration).

**Function signature:**

```
CT_PURE_DERIVE_SLOT_EPOCH_V0(
    slot_number: int,
    slot_start_ts: string,
    slots_per_epoch: int = 32
) → {
    round_number: int,
    slot_index: int,
    epoch_number: int,
    timestamp: string
}
```

**Computation:**

| Output | Formula | Semantics |
|--------|---------|-----------|
| `round_number` | `slot_number` | Pass-through; satisfies WF_PROPOSE_BLOCK_V0 payload contract |
| `slot_index` | `slot_number % slots_per_epoch` | Intra-epoch position (0-based); resets to 0 at each epoch boundary |
| `epoch_number` | `slot_number // slots_per_epoch` | Monotonically increasing epoch counter |
| `timestamp` | `slot_start_ts` | Pass-through; carries clock read result forward to block proposal context |

**Naming precision:** `slot_index` is the intra-epoch slot position. `slot_number` is the globally-increasing counter that never resets. These are semantically distinct — use exact field names.

---

### Wave 2 — Intents (parallel, after Step 1)

All four INs depend on the STRUCTURE artifact to validate that their payload fields match the storage key schema. Author all four in parallel.

**Step 4**
```
Artifact:    blockchain::IN_RUN_CHAIN_SIMULATION_V0
Action:      NEW
Module:      pgs_blockchain.registry.orchestration.intents
Depends on:  Step 1 (STRUCTURE)
PPS status:  NOT PRESENT — must author
Workflow:    blockchain::WF_RUN_CHAIN_SIMULATION_V0
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `simulation_id` | string | YES | Non-empty; primary isolation key |
| `slot_duration_seconds` | integer | YES | > 0 |
| `max_slots` | integer | YES | >= 1 |
| `tx_interval_seconds` | integer | YES | > 0 |
| `max_transactions` | integer | YES | >= 1 |
| `tx_sequence` | array | YES | Non-empty; each item must carry `tx_type` and required payload fields for the targeted TX WF |
| `triggered_by` | string | YES | Non-empty |

Outcomes: `ACK` → `WF_RUN_CHAIN_SIMULATION_V0`; `NACK` → `EXIT`

---

**Step 5**
```
Artifact:    blockchain::IN_CONSENSUS_LOOP_STARTED_V0
Action:      NEW
Module:      pgs_blockchain.registry.orchestration.intents
Depends on:  Step 1 (STRUCTURE)
PPS status:  NOT PRESENT — must author
Workflow:    blockchain::WF_RUN_CONSENSUS_LOOP_V0
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `simulation_id` | string | YES | Non-empty |
| `slot_schedule` | array | YES | Non-empty; each item is an integer slot_number >= 0 |
| `triggered_by` | string | YES | Non-empty |

Outcomes: `ACK` → `WF_RUN_CONSENSUS_LOOP_V0`; `NACK` → `EXIT`

---

**Step 6**
```
Artifact:    blockchain::IN_TX_WORKLOAD_STARTED_V0
Action:      NEW
Module:      pgs_blockchain.registry.orchestration.intents
Depends on:  Step 1 (STRUCTURE)
PPS status:  NOT PRESENT — must author
Workflow:    blockchain::WF_RUN_TX_WORKLOAD_V0
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `tx_interval_seconds` | integer | YES | > 0 |
| `tx_sequence` | array | YES | Non-empty; each item carries `tx_type` + all required payload fields for the targeted TX WF |
| `triggered_by` | string | YES | Non-empty |

Outcomes: `ACK` → `WF_RUN_TX_WORKLOAD_V0`; `NACK` → `EXIT`

---

**Step 7**
```
Artifact:    blockchain::IN_SLOT_EXECUTION_STARTED_V0
Action:      NEW
Module:      pgs_blockchain.registry.orchestration.intents
Depends on:  Step 1 (STRUCTURE)
PPS status:  NOT PRESENT — must author
Workflow:    blockchain::WF_PROCESS_SLOT_V0
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `simulation_id` | string | YES | Non-empty |
| `slot_number` | integer | YES | >= 0 |
| `triggered_by` | string | YES | Non-empty |

Outcomes: `ACK` → `WF_PROCESS_SLOT_V0`; `NACK` → `EXIT`

---

### Wave 3 — Capability Contracts (parallel within groups; see dependency notes)

**Step 8 — Slot Clock CCs (parallel; depend on Step 1 only)**

```
Artifact:    blockchain::CC_INITIALIZE_SLOT_CLOCK_V0
Action:      NEW
Module:      pgs_blockchain.registry.orchestration.capability_contracts
Depends on:  Step 1 (STRUCTURE — SLOT_CLOCK store)
PPS status:  NOT PRESENT — must author
```

1-step pipeline:

| Step | Type | Artifact | Operation | Store | Key | Write Fields |
|------|------|----------|-----------|-------|-----|--------------|
| `write_slot_clock_initial` | CS | CS_MUTABLE_JSON_V0 | WRITE | SLOT_CLOCK | `simulation_id` | `current_slot=0`, `slot_start_ts=NOW`, `slot_duration_seconds` |

Inputs: `simulation_id` (string, required), `slot_duration_seconds` (integer, required), `triggered_by` (string, required).  
Outputs: `result_status` (string).  
Routing Outcomes: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`.

---

```
Artifact:    blockchain::CC_READ_SLOT_CLOCK_V0
Action:      NEW
Module:      pgs_blockchain.registry.orchestration.capability_contracts
Depends on:  Step 1 (STRUCTURE — SLOT_CLOCK store)
PPS status:  NOT PRESENT — must author
```

1-step pipeline:

| Step | Type | Artifact | Operation | Store | Key | Read Fields |
|------|------|----------|-----------|-------|-----|-------------|
| `read_slot_clock` | CS | CS_MUTABLE_JSON_V0 | READ | SLOT_CLOCK | `simulation_id` | `current_slot`, `slot_start_ts`, `slot_duration_seconds` |

`NOT_FOUND` is a hard failure — route to EXIT immediately. Clock not initialized before slot execution is a governance violation, not a graceful skip.

Inputs: `simulation_id` (string, required).  
Outputs: `current_slot` (integer), `slot_start_ts` (string), `slot_duration_seconds` (integer).  
Routing Outcomes: `SUCCESS`, `NOT_FOUND`, `BACKEND_ERROR`.

---

```
Artifact:    blockchain::CC_ADVANCE_SLOT_CLOCK_V0
Action:      NEW
Module:      pgs_blockchain.registry.orchestration.capability_contracts
Depends on:  Step 1 (STRUCTURE — SLOT_CLOCK store)
PPS status:  NOT PRESENT — must author
```

1-step pipeline:

| Step | Type | Artifact | Operation | Store | Key | Write Fields |
|------|------|----------|-----------|-------|-----|--------------|
| `advance_slot_clock` | CS | CS_MUTABLE_JSON_V0 | WRITE | SLOT_CLOCK | `simulation_id` | `current_slot=current_slot+1`, `slot_start_ts=NOW` |

`next_slot` is computed as `current_slot + 1` inline before the write. This is CC-implementation-level arithmetic — not a separate CT step.

Inputs: `simulation_id` (string, required), `current_slot` (integer, required).  
Outputs: `result_status` (string), `next_slot` (integer).  
Routing Outcomes: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`.

---

**Step 9**
```
Artifact:    blockchain::CC_RECORD_SIMULATION_SUMMARY_V0
Action:      NEW
Module:      pgs_blockchain.registry.orchestration.capability_contracts
Depends on:  Step 1 (STRUCTURE — SIMULATION_SUMMARY store)
PPS status:  NOT PRESENT — must author
```

2-step pipeline:

| Step | Type | Artifact | Operation | Description |
|------|------|----------|-----------|-------------|
| `aggregate_results` | inline | — | — | Derive aggregate fields from `consensus_result` + `tx_workload_result` sub-objects; compute `simulation_outcome = SUCCESS if all_succeeded else VIOLATION`; extract `slots_processed`, `blocks_proposed`, `transactions_submitted`, `transactions_confirmed`, `violations_detected` from sub-WF outputs |
| `append_simulation_summary` | CS | CS_APPENDONLY_JSONL_V0 | APPEND | SIMULATION_SUMMARY store; write complete summary record |

**Summary Record Schema (fields to append):**

| Field | Source | Type |
|-------|--------|------|
| `simulation_id` | input | string |
| `simulation_outcome` | derived: `SUCCESS` if all_succeeded, `VIOLATION` otherwise | string |
| `slots_processed` | extracted from consensus_result | integer |
| `blocks_proposed` | extracted from consensus_result | integer |
| `transactions_submitted` | extracted from tx_workload_result | integer |
| `transactions_confirmed` | extracted from tx_workload_result | integer |
| `violations_detected` | sum of violations across sub-WFs | integer |
| `timestamp` | NOW at record time | string (ISO-8601) |

Inputs: `simulation_id` (string, required), `consensus_result` (object, required), `tx_workload_result` (object, required), `all_succeeded` (boolean, required), `triggered_by` (string, required).  
Outputs: `simulation_outcome` (string), `slots_processed` (integer), `blocks_proposed` (integer), `transactions_submitted` (integer), `transactions_confirmed` (integer), `violations_detected` (integer).  
Routing Outcomes: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`.

---

**Step 10**
```
Artifact:    blockchain::CC_PREPARE_SLOT_CONTEXT_V0
Action:      NEW
Module:      pgs_blockchain.registry.orchestration.capability_contracts
Depends on:  Step 3 (CT_PURE_DERIVE_SLOT_EPOCH_V0)
PPS status:  NOT PRESENT — must author
```

1-step pipeline:

| Step | Type | Artifact | Operation | Inputs | Outputs |
|------|------|----------|-----------|--------|---------|
| `derive_slot_epoch` | CT | CT_PURE_DERIVE_SLOT_EPOCH_V0 | — | `slot_number`, `slot_start_ts`, `slots_per_epoch` (default 32) | `round_number`, `slot_index`, `epoch_number`, `timestamp` |

Inputs: `slot_number` (integer, required), `slot_start_ts` (string, required), `slots_per_epoch` (integer, optional, default 32).  
Outputs: `round_number` (integer), `slot_index` (integer), `epoch_number` (integer), `timestamp` (string).  
Routing Outcomes: `SUCCESS`, `VIOLATION`.

---

**Step 11**
```
Artifact:    blockchain::CC_INVOKE_BLOCK_PROPOSAL_V0
Action:      NEW
Module:      pgs_blockchain.registry.orchestration.capability_contracts
Depends on:  CS_WORKFLOW_GATEWAY_V0 (existing — no authoring required)
PPS status:  NOT PRESENT — must author
```

1-step pipeline:

| Step | Type | Artifact | Operation | WF Invoked | Payload Fields |
|------|------|----------|-----------|-----------|---------------|
| `invoke_block_proposal` | CS | CS_WORKFLOW_GATEWAY_V0 | EXECUTE | `blockchain::WF_PROPOSE_BLOCK_V0` | `round_number`, `slot=slot_index`, `epoch=epoch_number`, `timestamp`, `triggered_by` |

**Field name mapping:** WF_PROPOSE_BLOCK_V0 expects `slot` and `epoch` in its payload (matching IN_BLOCK_PROPOSED_V0). This CC maps `slot_index` → `slot` and `epoch_number` → `epoch` at the payload construction step.

Inputs: `round_number` (integer, required), `slot_index` (integer, required), `epoch_number` (integer, required), `timestamp` (string, required), `triggered_by` (string, required).  
Outputs: `result_status` (string), `execution_result` (object).  
Routing Outcomes: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`.  
Note: CS_WORKFLOW_GATEWAY_V0 `NOT_FOUND` result (WF code not found in snapshot) routes to `BACKEND_ERROR`.

---

**Step 12**
```
Artifact:    blockchain::CC_RUN_SLOT_SEQUENCE_V0
Action:      NEW
Module:      pgs_blockchain.registry.orchestration.capability_contracts
Depends on:  CS_WORKFLOW_LOOP_V0 (existing), Steps 5+7 (INs define WF_PROCESS_SLOT_V0 expected payload)
PPS status:  NOT PRESENT — must author
```

1-step pipeline:

| Step | Type | Artifact | Operation | Description |
|------|------|----------|-----------|-------------|
| `execute_slot_sequence` | CS | CS_WORKFLOW_LOOP_V0 | EXECUTE_SEQUENCE | Iterate over `slot_schedule`; invoke `WF_PROCESS_SLOT_V0` per slot |

**CS_WORKFLOW_LOOP_V0 dispatch spec:**

```yaml
sequence: slot_schedule  # array of slot_number integers
item_wf:
  code: blockchain::WF_PROCESS_SLOT_V0
  payload_fields:
    slot_number: item  # each slot_schedule entry IS the slot_number value
  inject:
    simulation_id: "$.inputs.simulation_id"
    triggered_by: "$.inputs.triggered_by"
```

On any `VIOLATION` from `WF_PROCESS_SLOT_V0` invocation, the loop terminates and propagates `VIOLATION` out of the CC. Loop does not continue past a slot violation.

Inputs: `simulation_id` (string, required), `slot_schedule` (array of integer, required), `triggered_by` (string, required).  
Outputs: `items_processed` (integer).  
Routing Outcomes: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`.

---

**Step 13**
```
Artifact:    blockchain::CC_RUN_TX_SEQUENCE_V0
Action:      NEW
Module:      pgs_blockchain.registry.orchestration.capability_contracts
Depends on:  CS_WORKFLOW_LOOP_V0 (existing), Steps 6 (IN defines expected tx_sequence schema)
PPS status:  NOT PRESENT — must author
```

1-step pipeline:

| Step | Type | Artifact | Operation | Description |
|------|------|----------|-----------|-------------|
| `execute_tx_sequence` | CS | CS_WORKFLOW_LOOP_V0 | EXECUTE_SEQUENCE | Iterate over `tx_sequence`; dispatch each item to the WF declared by its `tx_type` field |

**CS_WORKFLOW_LOOP_V0 dispatch spec:**

```yaml
sequence: tx_sequence  # array of {tx_type, ...payload fields}
item_sub_sequence:
  field: null  # each item IS the TX payload (no nested sub-array)
  wf_dispatch:
    key_field: tx_type
    mapping:
      MINT:     blockchain::WF_MINT_V0
      TRANSFER: blockchain::WF_TRANSFER_V0
      BURN:     blockchain::WF_BURN_V0
      STAKE:    blockchain::WF_STAKE_V0
      UNSTAKE:  blockchain::WF_UNSTAKE_V0
      POOL:     blockchain::WF_POOL_V0
      REWARD:   blockchain::WF_REWARD_V0
      SLASH:    blockchain::WF_SLASH_V0
  payload_fields: all  # all item fields (except tx_type) forwarded as-is to the resolved WF
  inject:
    triggered_by: "$.inputs.triggered_by"
```

**Implementation note for authoring:** The exact `item_sub_sequence.field` mechanics depend on how CS_WORKFLOW_LOOP_V0's EXECUTE_SEQUENCE handles flat-dispatch (where each item IS the payload). Resolve by inspecting the existing CC_EXECUTE_SLOT_SEQUENCE_V0 implementation and/or the CS_WORKFLOW_LOOP_V0 RB as a reference pattern. The governance intent is clear: `tx_type` is the dispatch key; the full item payload (minus `tx_type`) is forwarded to the dispatched WF.

**TX interval timing:** `tx_interval_seconds` governs the wait between consecutive TX submissions. This timing is declared in the CC dispatch spec as an inter-item delay. Resolve exact field name in CS_WORKFLOW_LOOP_V0's `item_delay_seconds` or equivalent field during authoring.

Inputs: `tx_sequence` (array, required), `tx_interval_seconds` (integer, required), `triggered_by` (string, required).  
Outputs: `items_processed` (integer), `sub_items_processed` (integer).  
Routing Outcomes: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`.

---

**Step 14**
```
Artifact:    blockchain::CC_DISPATCH_SIMULATION_WORKERS_V0
Action:      NEW
Module:      pgs_blockchain.registry.orchestration.capability_contracts
Depends on:  Step 2 (CS_CONCURRENT_WORKFLOWS_V0), Steps 5+6 (INs define WF payload contracts)
PPS status:  NOT PRESENT — must author
```

1-step pipeline:

| Step | Type | Artifact | Operation | Description |
|------|------|----------|-----------|-------------|
| `dispatch_concurrent_workers` | CS | CS_CONCURRENT_WORKFLOWS_V0 | EXECUTE_CONCURRENT | Invoke WF_RUN_CONSENSUS_LOOP_V0 and WF_RUN_TX_WORKLOAD_V0 concurrently; wait for both; return aggregate result |

**CS_CONCURRENT_WORKFLOWS_V0 invocation spec:**

```yaml
workflows:
  - code: blockchain::WF_RUN_CONSENSUS_LOOP_V0
    payload:
      simulation_id: "$.inputs.simulation_id"
      slot_schedule: "$.inputs.slot_schedule"
      triggered_by: "$.inputs.triggered_by"
  - code: blockchain::WF_RUN_TX_WORKLOAD_V0
    payload:
      tx_interval_seconds: "$.inputs.tx_interval_seconds"
      tx_sequence: "$.inputs.tx_sequence"
      triggered_by: "$.inputs.triggered_by"
triggered_by: "$.inputs.triggered_by"
```

**Routing logic:** Derive `all_succeeded` from `results`; expose `consensus_result` and `tx_workload_result` as named outputs by looking up `code = blockchain::WF_RUN_CONSENSUS_LOOP_V0` and `code = blockchain::WF_RUN_TX_WORKLOAD_V0` in the results array (correlated by code, not by position). Route `SUCCESS` if `all_succeeded = true`; route `PARTIAL_FAILURE` if any WF returned non-SUCCESS but execution completed; route `BACKEND_ERROR` on infrastructure failure.

Inputs: `simulation_id` (string, required), `slot_schedule` (array, required), `slot_duration_seconds` (integer, required), `tx_interval_seconds` (integer, required), `tx_sequence` (array, required), `triggered_by` (string, required).  
Outputs: `consensus_result` (object), `tx_workload_result` (object), `all_succeeded` (boolean).  
Routing Outcomes: `SUCCESS`, `PARTIAL_FAILURE`, `BACKEND_ERROR`.

---

### Wave 4 — Workflows (parallel within group; after respective deps)

**Step 15**
```
Artifact:    blockchain::WF_PROCESS_SLOT_V0
Action:      NEW
Module:      pgs_blockchain.registry.orchestration.workflows
Depends on:  Steps 7 (IN), 8 (CC_READ, CC_ADVANCE), 10 (CC_PREPARE), 11 (CC_INVOKE)
Subdomain:   orchestration
Runtime binding: blockchain::RB_PROCESS_SLOT_V0
PPS status:  NOT PRESENT — must author
```

**Execution Topology:**

| Node | Type | next.SUCCESS | next.VIOLATION | next.NOT_FOUND | next.BACKEND_ERROR |
|------|------|-------------|---------------|---------------|-------------------|
| `IN_SLOT_EXECUTION_STARTED_V0` | IN | `CC_READ_SLOT_CLOCK_V0` | `EXIT` | — | — |
| `CC_READ_SLOT_CLOCK_V0` | CC | `CC_PREPARE_SLOT_CONTEXT_V0` | `EXIT` | `EXIT` | `EXIT` |
| `CC_PREPARE_SLOT_CONTEXT_V0` | CC | `CC_INVOKE_BLOCK_PROPOSAL_V0` | `EXIT` | — | — |
| `CC_INVOKE_BLOCK_PROPOSAL_V0` | CC | `CC_ADVANCE_SLOT_CLOCK_V0` | `EXIT` | — | `EXIT` |
| `CC_ADVANCE_SLOT_CLOCK_V0` | CC | `EXIT_SUCCESS` | `EXIT` | — | `EXIT` |

**JSONPath input bindings:**

| CC Node | Input Field | Source |
|---------|------------|--------|
| `CC_READ_SLOT_CLOCK_V0` | `simulation_id` | `$.payload.simulation_id` |
| `CC_PREPARE_SLOT_CONTEXT_V0` | `slot_number` | `$.payload.slot_number` |
| `CC_PREPARE_SLOT_CONTEXT_V0` | `slot_start_ts` | `$.results.CC_READ_SLOT_CLOCK_V0.slot_start_ts` |
| `CC_PREPARE_SLOT_CONTEXT_V0` | `slots_per_epoch` | `$.payload.slots_per_epoch` (optional; default 32) |
| `CC_INVOKE_BLOCK_PROPOSAL_V0` | `round_number` | `$.results.CC_PREPARE_SLOT_CONTEXT_V0.round_number` |
| `CC_INVOKE_BLOCK_PROPOSAL_V0` | `slot_index` | `$.results.CC_PREPARE_SLOT_CONTEXT_V0.slot_index` |
| `CC_INVOKE_BLOCK_PROPOSAL_V0` | `epoch_number` | `$.results.CC_PREPARE_SLOT_CONTEXT_V0.epoch_number` |
| `CC_INVOKE_BLOCK_PROPOSAL_V0` | `timestamp` | `$.results.CC_PREPARE_SLOT_CONTEXT_V0.timestamp` |
| `CC_INVOKE_BLOCK_PROPOSAL_V0` | `triggered_by` | `$.payload.triggered_by` |
| `CC_ADVANCE_SLOT_CLOCK_V0` | `simulation_id` | `$.payload.simulation_id` |
| `CC_ADVANCE_SLOT_CLOCK_V0` | `current_slot` | `$.results.CC_READ_SLOT_CLOCK_V0.current_slot` |

---

**Step 16**
```
Artifact:    blockchain::WF_RUN_CONSENSUS_LOOP_V0
Action:      NEW
Module:      pgs_blockchain.registry.orchestration.workflows
Depends on:  Steps 5 (IN), 12 (CC_RUN_SLOT_SEQUENCE)
Subdomain:   orchestration
Runtime binding: blockchain::RB_RUN_CONSENSUS_LOOP_V0
PPS status:  NOT PRESENT — must author
```

**Execution Topology:**

| Node | Type | next.SUCCESS | next.VIOLATION | next.BACKEND_ERROR |
|------|------|-------------|---------------|-------------------|
| `IN_CONSENSUS_LOOP_STARTED_V0` | IN | `CC_RUN_SLOT_SEQUENCE_V0` | `EXIT` | — |
| `CC_RUN_SLOT_SEQUENCE_V0` | CC | `EXIT_SUCCESS` | `EXIT` | `EXIT` |

**JSONPath input bindings:**

| CC Node | Input Field | Source |
|---------|------------|--------|
| `CC_RUN_SLOT_SEQUENCE_V0` | `simulation_id` | `$.payload.simulation_id` |
| `CC_RUN_SLOT_SEQUENCE_V0` | `slot_schedule` | `$.payload.slot_schedule` |
| `CC_RUN_SLOT_SEQUENCE_V0` | `triggered_by` | `$.payload.triggered_by` |

---

**Step 17**
```
Artifact:    blockchain::WF_RUN_TX_WORKLOAD_V0
Action:      NEW
Module:      pgs_blockchain.registry.orchestration.workflows
Depends on:  Steps 6 (IN), 13 (CC_RUN_TX_SEQUENCE)
Subdomain:   orchestration
Runtime binding: blockchain::RB_RUN_TX_WORKLOAD_V0
PPS status:  NOT PRESENT — must author
```

**Execution Topology:**

| Node | Type | next.SUCCESS | next.VIOLATION | next.BACKEND_ERROR |
|------|------|-------------|---------------|-------------------|
| `IN_TX_WORKLOAD_STARTED_V0` | IN | `CC_RUN_TX_SEQUENCE_V0` | `EXIT` | — |
| `CC_RUN_TX_SEQUENCE_V0` | CC | `EXIT_SUCCESS` | `EXIT` | `EXIT` |

**JSONPath input bindings:**

| CC Node | Input Field | Source |
|---------|------------|--------|
| `CC_RUN_TX_SEQUENCE_V0` | `tx_sequence` | `$.payload.tx_sequence` |
| `CC_RUN_TX_SEQUENCE_V0` | `tx_interval_seconds` | `$.payload.tx_interval_seconds` |
| `CC_RUN_TX_SEQUENCE_V0` | `triggered_by` | `$.payload.triggered_by` |

---

**Step 18**
```
Artifact:    blockchain::WF_RUN_CHAIN_SIMULATION_V0
Action:      NEW
Module:      pgs_blockchain.registry.orchestration.workflows
Depends on:  Steps 4 (IN), 8 (CC_INITIALIZE), 9 (CC_RECORD), 14 (CC_DISPATCH)
Subdomain:   orchestration
Runtime binding: blockchain::RB_RUN_CHAIN_SIMULATION_V0
PPS status:  NOT PRESENT — must author
```

**Execution Topology:**

| Node | Type | next.SUCCESS | next.PARTIAL_FAILURE | next.VIOLATION | next.BACKEND_ERROR |
|------|------|-------------|---------------------|---------------|-------------------|
| `IN_RUN_CHAIN_SIMULATION_V0` | IN | `CC_INITIALIZE_SLOT_CLOCK_V0` | — | `EXIT` | — |
| `CC_INITIALIZE_SLOT_CLOCK_V0` | CC | `CC_DISPATCH_SIMULATION_WORKERS_V0` | — | `EXIT` | `EXIT` |
| `CC_DISPATCH_SIMULATION_WORKERS_V0` | CC | `CC_RECORD_SIMULATION_SUMMARY_V0` | `CC_RECORD_SIMULATION_SUMMARY_V0` | — | `EXIT` |
| `CC_RECORD_SIMULATION_SUMMARY_V0` | CC | `EXIT_SUCCESS` | — | `EXIT` | `EXIT` |

Note: `PARTIAL_FAILURE` from `CC_DISPATCH_SIMULATION_WORKERS_V0` routes to `CC_RECORD_SIMULATION_SUMMARY_V0` — the summary is always recorded, including for partial failures. The `all_succeeded = false` flag drives `simulation_outcome = VIOLATION` in the summary.

**JSONPath input bindings:**

| CC Node | Input Field | Source |
|---------|------------|--------|
| `CC_INITIALIZE_SLOT_CLOCK_V0` | `simulation_id` | `$.payload.simulation_id` |
| `CC_INITIALIZE_SLOT_CLOCK_V0` | `slot_duration_seconds` | `$.payload.slot_duration_seconds` |
| `CC_INITIALIZE_SLOT_CLOCK_V0` | `triggered_by` | `$.payload.triggered_by` |
| `CC_DISPATCH_SIMULATION_WORKERS_V0` | `simulation_id` | `$.payload.simulation_id` |
| `CC_DISPATCH_SIMULATION_WORKERS_V0` | `slot_schedule` | *(derived: array from 0 to max_slots-1; see note below)* |
| `CC_DISPATCH_SIMULATION_WORKERS_V0` | `slot_duration_seconds` | `$.payload.slot_duration_seconds` |
| `CC_DISPATCH_SIMULATION_WORKERS_V0` | `tx_interval_seconds` | `$.payload.tx_interval_seconds` |
| `CC_DISPATCH_SIMULATION_WORKERS_V0` | `tx_sequence` | `$.payload.tx_sequence` |
| `CC_DISPATCH_SIMULATION_WORKERS_V0` | `triggered_by` | `$.payload.triggered_by` |
| `CC_RECORD_SIMULATION_SUMMARY_V0` | `simulation_id` | `$.payload.simulation_id` |
| `CC_RECORD_SIMULATION_SUMMARY_V0` | `consensus_result` | `$.results.CC_DISPATCH_SIMULATION_WORKERS_V0.consensus_result` |
| `CC_RECORD_SIMULATION_SUMMARY_V0` | `tx_workload_result` | `$.results.CC_DISPATCH_SIMULATION_WORKERS_V0.tx_workload_result` |
| `CC_RECORD_SIMULATION_SUMMARY_V0` | `all_succeeded` | `$.results.CC_DISPATCH_SIMULATION_WORKERS_V0.all_succeeded` |
| `CC_RECORD_SIMULATION_SUMMARY_V0` | `triggered_by` | `$.payload.triggered_by` |

**Note on `slot_schedule`:** The `slot_schedule` array (`[0, 1, 2, ..., max_slots-1]`) is not directly available in the payload — the payload carries `max_slots`. Options: (a) derive via a CT before dispatch, (b) include `slot_schedule` directly in the seed payload (pre-expanded), or (c) resolve in the CC dispatch step inline. **Design decision for authoring pass:** Use option (b) — include `slot_schedule` as a pre-expanded array in `IN_RUN_CHAIN_SIMULATION_V0` payload and seed configuration. This keeps CC dispatch spec pure and avoids inline array generation. Add `slot_schedule` as an optional field to `IN_RUN_CHAIN_SIMULATION_V0` (if omitted, CC generates `[0..max_slots-1]` inline as an implementation detail).

---

### Wave 5 — Runtime Bindings (parallel; after respective WFs)

**Step 19**
```
Artifact:    blockchain::RB_PROCESS_SLOT_V0
Action:      NEW
Module:      pgs_blockchain.registry.orchestration.runtime_bindings
Depends on:  Step 15 (WF_PROCESS_SLOT_V0)
PPS status:  NOT PRESENT — must author
```

```yaml
rb_code: RB_PROCESS_SLOT_V0
version: v0
governed_by: fb.topology::CONSTITUTION_RUNTIME_BINDING_V0

core:
  summary: Runtime binding for single slot execution workflow
  storage_structure: blockchain::STRUCTURE_BLOCKCHAIN_ORCHESTRATION_STORAGE_V0

  bindings:
    capability_side_effects::CS_MUTABLE_JSON_V0:
      policy: {}
    capability_side_effects::CS_WORKFLOW_GATEWAY_V0:
      policy: {}
```

Note: `CS_WORKFLOW_GATEWAY_V0` is declared here because `CC_INVOKE_BLOCK_PROPOSAL_V0` uses it as a side effect. This is the first domain-level RB to declare this binding — consistent with the pattern that all used CS substrates are declared in the WF's RB.

---

**Step 20**
```
Artifact:    blockchain::RB_RUN_CONSENSUS_LOOP_V0
Action:      NEW
Module:      pgs_blockchain.registry.orchestration.runtime_bindings
Depends on:  Step 16 (WF_RUN_CONSENSUS_LOOP_V0)
PPS status:  NOT PRESENT — must author
```

```yaml
rb_code: RB_RUN_CONSENSUS_LOOP_V0
version: v0
governed_by: fb.topology::CONSTITUTION_RUNTIME_BINDING_V0

core:
  summary: Runtime binding for consensus loop coordination workflow
  storage_structure: blockchain::STRUCTURE_BLOCKCHAIN_ORCHESTRATION_STORAGE_V0

  bindings:
    capability_side_effects::CS_WORKFLOW_LOOP_V0:
      policy: {}
```

---

**Step 21**
```
Artifact:    blockchain::RB_RUN_TX_WORKLOAD_V0
Action:      NEW
Module:      pgs_blockchain.registry.orchestration.runtime_bindings
Depends on:  Step 17 (WF_RUN_TX_WORKLOAD_V0)
PPS status:  NOT PRESENT — must author
```

```yaml
rb_code: RB_RUN_TX_WORKLOAD_V0
version: v0
governed_by: fb.topology::CONSTITUTION_RUNTIME_BINDING_V0

core:
  summary: Runtime binding for TX workload coordination workflow
  storage_structure: blockchain::STRUCTURE_BLOCKCHAIN_ORCHESTRATION_STORAGE_V0

  bindings:
    capability_side_effects::CS_WORKFLOW_LOOP_V0:
      policy: {}
```

---

**Step 22**
```
Artifact:    blockchain::RB_RUN_CHAIN_SIMULATION_V0
Action:      NEW
Module:      pgs_blockchain.registry.orchestration.runtime_bindings
Depends on:  Step 18 (WF_RUN_CHAIN_SIMULATION_V0)
PPS status:  NOT PRESENT — must author
```

```yaml
rb_code: RB_RUN_CHAIN_SIMULATION_V0
version: v0
governed_by: fb.topology::CONSTITUTION_RUNTIME_BINDING_V0

core:
  summary: Runtime binding for chain simulation coordination workflow
  storage_structure: blockchain::STRUCTURE_BLOCKCHAIN_ORCHESTRATION_STORAGE_V0

  bindings:
    capability_side_effects::CS_MUTABLE_JSON_V0:
      policy: {}
    capability_side_effects::CS_APPENDONLY_JSONL_V0:
      policy: {}
    capability_side_effects::CS_CONCURRENT_WORKFLOWS_V0:
      policy: {}
```

---

### Wave 6 — Lifecycle Patch and Seed (parallel; no interdependency)

**Step 23**
```
Artifact:    blockchain::WF_RUN_CONSENSUS_SLOTS_V0
Action:      LIFECYCLE PATCH (metadata-only; no structural change)
Module:      pgs_blockchain.registry.consensus_pos.workflows (existing)
PPS status:  EXISTS — add lifecycle metadata block to extensions section only
```

Add the following block to the artifact's `extensions` section. **No other field may be modified. Version remains v0. Routing, nodes, and all CC references unchanged.**

```yaml
lifecycle:
  status: RETIRED
  retired_in_cr: blockchain/orchestration/V0
  superseded_by:
    primary: blockchain::WF_RUN_CHAIN_SIMULATION_V0
    note: >
      WF_RUN_CHAIN_SIMULATION_V0 separates slot coordination (WF_RUN_CONSENSUS_LOOP_V0)
      from TX workload coordination (WF_RUN_TX_WORKLOAD_V0) and adds governed slot clock
      state (SLOT_CLOCK store). WF_RUN_CONSENSUS_SLOTS_V0 bundled both concerns in a
      single WF with sleep-based external timing and no governed state.
```

No other consensus_pos artifacts are affected. Verify before committing:
- `WF_PROPOSE_BLOCK_V0` — ACTIVE, unchanged ✓
- `CC_EXECUTE_SLOT_SEQUENCE_V0` — historical; no lifecycle patch in this CR ✓
- All other consensus_pos CCs — ACTIVE, unchanged ✓

---

**Step 24**
```
Action:      NEW SEED FILE
Path:        seeds/blockchain/orchestration/chain_simulation_config.json
Repository:  pgs_workspace
Depends on:  nothing (seed is environment-level data)
```

**Seed schema:**

```json
{
  "simulation_id": "sim_v0_test_001",
  "slot_duration_seconds": 2,
  "max_slots": 5,
  "slot_schedule": [0, 1, 2, 3, 4],
  "tx_interval_seconds": 1,
  "max_transactions": 10,
  "tx_sequence": [
    {"tx_type": "MINT",     "wallet_id": "<seed_wallet_id>", "amount": 100, "triggered_by": "system"},
    {"tx_type": "TRANSFER", "from_wallet_id": "<seed_wallet_id>", "to_wallet_id": "<seed_wallet_id_2>", "amount": 25, "triggered_by": "system"},
    {"tx_type": "MINT",     "wallet_id": "<seed_wallet_id_2>", "amount": 50, "triggered_by": "system"}
  ],
  "triggered_by": "system"
}
```

`<seed_wallet_id>` and `<seed_wallet_id_2>` are resolved from pre-existing wallet seed data in `seeds/blockchain/wallet/`. The orchestration seed depends on bootstrap completing successfully before simulation is invoked.

**`slot_schedule`** is included as a pre-expanded array (design decision from Step 18 note) to keep CC dispatch spec pure. It must equal `[0..max_slots-1]`.

---

### Wave 7 — Compiler Registration

~~**Step 25 — REMOVED**~~

`STRUCTURE_BLOCKCHAIN_ORCHESTRATION_STORAGE_V0` is an entity store STRUCTURE artifact, not a compiler build config. Entity store STRUCTURE artifacts are not registered in `_STRUCTURE_SCOPE_MAP`. The orchestration subdomain is discovered automatically by the existing `STRUCTURE_BUILD_BLOCKCHAIN_CONFIG_V0` (which covers all subdomains under the `BLOCKCHAIN` layer via `artifact_discovery.search_layers: [BLOCKCHAIN]`). No compiler registration step is required.

---

### Wave 8 — scripts/test_blockchain_e2e.py Refactor

**Step 25**
```
Action:      REFACTOR
File:        scripts/test_blockchain_e2e.py (pgs_workspace)
Depends on:  All WF artifacts compiled and available in protocol_snapshot
```

**Before (current state):** script owns slot timing (sleep-based), TX submission sequencing, and consensus loop invocation — all outside the governance boundary.

**After (target state):** Script becomes a thin entry-point — reads seed configuration, constructs the `IN_RUN_CHAIN_SIMULATION_V0` payload, and invokes `WF_RUN_CHAIN_SIMULATION_V0` via `pgs_runtime run`. No coordination logic remains in the script.

**Refactored script responsibilities:**
1. Load `seeds/blockchain/orchestration/chain_simulation_config.json`
2. Construct `IN_RUN_CHAIN_SIMULATION_V0` payload from seed data
3. Write payload to a temp file (following existing script pattern)
4. Invoke: `pgs_runtime run --wf blockchain::WF_RUN_CHAIN_SIMULATION_V0 --payload <path> --data-root <abs-path> --workspace .`
5. Read and display the resulting trace summary

**Remove from script:**
- All `time.sleep()` calls governing slot duration
- All direct invocations of `WF_RUN_CONSENSUS_SLOTS_V0` or `WF_PROPOSE_BLOCK_V0`
- All TX submission loops
- All slot counter logic

---

## Authoring Conformance Checklist

Before marking any artifact as COMPLETE in the authoring manifest, verify:

| Check | Applies To |
|-------|-----------|
| FQDN matches exactly: `blockchain::ARTIFACT_CODE_V0` | All new blockchain artifacts |
| `subdomain: orchestration` declared in frontmatter | All 4 new WF artifacts |
| `runtime_binding` field references correct RB FQDN | All 4 new WF artifacts |
| `slot_index` used (not `slot`) throughout | CT output + CC_PREPARE output + CC_INVOKE input |
| `epoch_number` used (not `epoch`) throughout | CT output + CC_PREPARE output + CC_INVOKE input |
| `slot` and `epoch` used ONLY in CC_INVOKE_BLOCK_PROPOSAL_V0 payload mapping (to match WF_PROPOSE_BLOCK_V0 contract) | CC_INVOKE only |
| Results from CS_CONCURRENT_WORKFLOWS_V0 correlated by `code`, not by array index | CC_DISPATCH implementation |
| SLOT_CLOCK store ownership invariant declared in STRUCTURE artifact | Step 1 |
| `simulation_id` isolation boundary declared in STRUCTURE artifact | Step 1 |
| CT_PURE_DERIVE_SLOT_EPOCH_V0 declares zero CS calls | Step 3 |
| Lifecycle patch touches WF_RUN_CONSENSUS_SLOTS_V0 extensions section only | Step 23 |
| New orchestration artifacts classified `status: ACTIVE` at authoring | Steps 1–22 |
| `slot_schedule` array included in seed and matched to `max_slots` | Step 24 |

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 0 — Classification | 1_change_request_orchestration_v0.md | COMPLETE |
| Stage 1 — Input Elicitation | 1_input_elicitation_orchestration_v0.md | COMPLETE |
| Stage 2 — Domain Model Discovery | 2_domain_model_orchestration_v0.md | COMPLETE |
| Stage 3 — Analysis Loop | 3_analysis_loop_orchestration_v0.md | COMPLETE — SATURATED |
| Stage 4 — Business Model | 4_business_model_orchestration_v0.md | COMPLETE |
| Stage 5 — Business Intent | 5_business_intent_orchestration_v0.md | COMPLETE |
| Stage 6 — Governance Intent | 6_governance_intent_orchestration_v0.md | COMPLETE |
| Stage 6b — Design Intent | 6b_design_intent_orchestration_v0.md | COMPLETE |
| Stage 7 — Authoring Mandate | This document | COMPLETE |
| Stage 8 — Authoring Manifest | 8_authoring_manifest_orchestration_v0.md | PENDING |

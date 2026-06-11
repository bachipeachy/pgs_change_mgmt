# Stage 7 — Authoring Mandate: blockchain / consensus_propose
**Domain:** blockchain
**Subdomains:** consensus_pos, transaction, validator
**Version:** V0
**Status:** DRAFT
**Pipeline Stage:** Stage 7 — Authoring Mandate
**Produced by:** v0.5.0 SDLC authoring pipeline
**Input:** 6b_design_intent_consensus_propose_v0.md (Stage 6b — APPROVED)

---

## Overview

This CR produces 14 authoring actions across three peer subdomains:

| Subdomain | Actions | Breakdown |
|-----------|---------|-----------|
| blockchain::consensus_pos | 9 | 5 NEW + 4 UPDATE |
| blockchain::transaction | 5 | 5 UPDATE |
| blockchain::validator | 1 | 1 UPDATE |
| **Total** | **14** | 5 NEW + 9 UPDATE |

REUSE artifacts (no changes): `CC_FORM_BLOCK_V0`, `CC_SELECT_PROPOSER_V0`, `CC_RECORD_CONSENSUS_ROUND_V0`, `CC_SKIP_ROUND_V0`, `CC_PERSIST_MEMPOOL_TX_V0`, `CT_PURE_EXTRACT_V0`, `CT_PURE_ASSEMBLE_RECORD_V0`, `STRUCTURE_BLOCKCHAIN_STORAGE_V0` — all stores declared in prior CRs; zero new stores; zero new CTs.

Confirmed infrastructure: `CS_WORKFLOW_GATEWAY_V0` (EXECUTE) is the governed side effect for WF invocation from within CC_EXECUTE_SLOT_SEQUENCE_V0. Verified present in PPS snapshot.

---

## Build Dependency Order

Steps within the same wave have no inter-dependencies and may be authored in parallel.

---

### Wave 1 — Foundation: Input Contracts and Atomic Updates (no dependencies)

**Step 1**
```
Artifact:    blockchain::IN_CONSENSUS_SLOTS_V0
Action:      NEW
Subdomain:   consensus_pos
Depends on:  nothing
PPS status:  NOT PRESENT — must author
```
Admission gate for WF_RUN_CONSENSUS_SLOTS_V0. Schema:
- `triggered_by` (string, required) — SYSTEM actor_id initiating the slot run
- `start_timestamp` (string, required) — ISO-8601 start time for the slot run
- `slot_schedule` (array, required, non-empty) — finite ordered list of slot descriptors

Each slot descriptor in `slot_schedule`:
- `round_number` (integer, required) — global round counter
- `slot` (integer, required) — slot within epoch; equals `round_number % 32`
- `epoch` (integer, required) — epoch number; equals `round_number // 32`
- `timestamp` (string, required) — ISO-8601 timestamp for this slot
- `transactions` (array, required) — typed transaction descriptors to submit before block proposal fires for this slot

Outcomes: `ACK` (all required fields present; slot_schedule non-empty), `NACK` (any required field missing or slot_schedule empty).

---

**Step 2**
```
Artifact:    blockchain::IN_BLOCK_PROPOSED_V0
Action:      UPDATE
Subdomain:   consensus_pos
Depends on:  nothing
PPS status:  EXISTS — add slot and epoch as required fields
```
Add two required fields to the existing 3-field schema:
- `slot` (integer, required) — slot within epoch; `round_number % 32`; supplied by caller (CC_EXECUTE_SLOT_SEQUENCE_V0 per D7)
- `epoch` (integer, required) — epoch number; `round_number // 32`; supplied by caller

Updated 5-field schema: `triggered_by`, `round_number`, `slot`, `epoch`, `timestamp`. All fields required.
Outcomes: `ACK` (all five fields present and valid), `NACK` (any required field missing).

No topology change to WF_PROPOSE_BLOCK_V0 is required by this step alone — the WF binding update is Step 12.

---

**Step 3**
```
Artifact:    blockchain::CC_QUERY_ELIGIBLE_VALIDATORS_V0
Action:      UPDATE
Subdomain:   consensus_pos
Depends on:  nothing
PPS status:  EXISTS — replace filter predicate only; pipeline structure unchanged
```
Change the filter predicate in Step 2 of the existing CC pipeline:
- **Remove:** `enrollment_status = ACTIVE` AND `stake` present
- **Add:** `status = ACTIVE_ONGOING` AND `effective_balance` present

No change to pipeline step count, CS types, or result outcomes. `eligible_validators` output field name unchanged.
Outcomes: `SUCCESS` (eligible list returned), `NOT_FOUND` (no eligible validators), `VIOLATION`, `BACKEND_ERROR`.

---

**Step 4**
```
Artifact:    blockchain::IN_VALIDATOR_REGISTERED_V0
Action:      UPDATE
Subdomain:   validator
Depends on:  nothing
PPS status:  EXISTS — extend from 4-field to 8-field canonical schema
```
Extend the existing `validator_record` object schema from 4 fields to 8 canonical fields. Add four required fields:
- `status` (string, required) — enum: `ACTIVE_ONGOING`, `EXITED`, `SLASHED`; canonical lifecycle field
- `effective_balance` (integer, required) — declared stake in BACHI; canonical eligibility field
- `activation_epoch` (integer, required) — epoch at which validator became active
- `exit_epoch` (integer or null, required) — epoch at which validator exits; null if not scheduled

Existing four fields (`actor_id`, `validator_index`, `pubkey`, `withdrawal_credentials`) are unchanged. Outcomes unchanged: `ACK`, `NACK`.

---

**Step 5**
```
Artifact:    blockchain::RB_MINT_V0
Action:      UPDATE
Subdomain:   transaction
Depends on:  nothing
PPS status:  EXISTS — add CS_REGISTRY_V0 binding; correct description
```
Add `capability_side_effects::CS_REGISTRY_V0` to the `bindings` block. Current bindings: `CS_MUTABLE_JSON_V0`, `CS_APPENDONLY_JSONL_V0`. After update: also includes `CS_REGISTRY_V0`.

Also correct the `description` field: remove "No actor registry — system authority only." Correct text: "Binds capability side effects to concrete runtime implementations for MINT (SYSTEM). CS_REGISTRY_V0 provides tx dedup for CC_PERSIST_MEMPOOL_TX_V0."

No change to `storage_structure` reference or any other field.

---

**Step 6**
```
Artifact:    blockchain::RB_BURN_V0
Action:      UPDATE
Subdomain:   transaction
Depends on:  nothing
PPS status:  EXISTS — add CS_REGISTRY_V0 binding; correct description
```
Identical update pattern to Step 5 (RB_MINT_V0). Add `capability_side_effects::CS_REGISTRY_V0` to the `bindings` block. Correct `description` to remove the erroneous "No actor registry" claim and name the registry purpose.

---

**Step 7**
```
Artifact:    blockchain::RB_POOL_V0
Action:      UPDATE
Subdomain:   transaction
Depends on:  nothing
PPS status:  EXISTS — add CS_REGISTRY_V0 binding; correct description
```
Identical update pattern to Steps 5–6. Add `capability_side_effects::CS_REGISTRY_V0`. Correct `description`.

---

**Step 8**
```
Artifact:    blockchain::RB_REWARD_V0
Action:      UPDATE
Subdomain:   transaction
Depends on:  nothing
PPS status:  EXISTS — add CS_REGISTRY_V0 binding; correct description
```
Identical update pattern to Steps 5–7. Add `capability_side_effects::CS_REGISTRY_V0`. Correct `description`.

---

**Step 9**
```
Artifact:    blockchain::RB_SLASH_V0
Action:      UPDATE
Subdomain:   transaction
Depends on:  nothing
PPS status:  EXISTS — add CS_REGISTRY_V0 binding; correct description
```
Identical update pattern to Steps 5–8. Add `capability_side_effects::CS_REGISTRY_V0`. Correct `description`.

---

### Wave 2 — Capability Contracts and Updated WF Wiring (after Wave 1)

*Steps 10–12 may be authored in parallel once their Wave 1 prerequisites are complete.*

**Step 10**
```
Artifact:    blockchain::CC_VERIFY_SLOT_RESULTS_V0
Action:      NEW
Subdomain:   consensus_pos
Depends on:  nothing new — reads existing BLOCKS and TRANSACTION stores (REUSE, declared in prior CRs)
PPS status:  NOT PRESENT — must author
```
Post-run assertion CC. Read-only — no writes to any store.

Pipeline:
- Step 1: `CS_MUTABLE_JSON_V0` — LIST — BLOCKS store → filter `status = PROPOSED` → `proposed_blocks` list
- Step 2: `CT_PURE_EXTRACT_V0` (REUSE) — assert `count(proposed_blocks) ≥ 1` → `VIOLATION` if zero
- Step 3: `CS_MUTABLE_JSON_V0` — LIST — TRANSACTION store → filter `status = PENDING` → extract `tx_type` values → `observed_tx_types` set
- Step 4: `CT_PURE_EXTRACT_V0` (REUSE) — assert all 8 expected tx_types present (`TRANSFER`, `STAKE`, `UNSTAKE`, `MINT`, `BURN`, `POOL`, `REWARD`, `SLASH`) → `VIOLATION` per missing type

Inputs (bound from WF): none required beyond implicit store access context.
Result outputs: `slots_verified` (integer), `missing_tx_types` (array — empty on SUCCESS).
Outcomes: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`.

---

**Step 11**
```
Artifact:    blockchain::CC_EXECUTE_SLOT_SEQUENCE_V0
Action:      NEW
Subdomain:   consensus_pos
Depends on:  Step 1 (IN_CONSENSUS_SLOTS_V0 — schema context for slot_schedule structure)
PPS status:  NOT PRESENT — must author
```
Finite slot loop execution. Collatz pattern — iteration with side effects absorbed entirely inside this CC; WF DAG (Step 13) is linear.

Pipeline (Collatz pattern — loop body):
- Input: `slot_schedule` (array of slot descriptors from IN_CONSENSUS_SLOTS_V0)
- For each slot descriptor in `slot_schedule` (in order):
  - Sub-step A: For each transaction descriptor in `slot.transactions`:
    - `CS_WORKFLOW_GATEWAY_V0` EXECUTE — `workflow_code`: matching typed WF code (e.g., `blockchain::WF_SUBMIT_TRANSFER_V0`); `payload`: transaction descriptor fields
    - Typed WF writes to TRANSACTION store (side effect of invocation)
  - Sub-step B: `CS_WORKFLOW_GATEWAY_V0` EXECUTE — `workflow_code`: `blockchain::WF_PROPOSE_BLOCK_V0`; `payload`: `{triggered_by, round_number, slot, epoch, timestamp}` from slot descriptor
    - WF_PROPOSE_BLOCK_V0 writes BLOCKS and CONSENSUS_ROUNDS (side effects of invocation)
- After slot_schedule exhausted:
  - Assemble counters: `slots_executed`, `blocks_proposed`, `rounds_skipped`, `tx_submitted`
  - Exit with `SUCCESS`

Result outputs: `slots_executed` (integer), `blocks_proposed` (integer), `rounds_skipped` (integer), `tx_submitted` (integer).
Outcomes: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`.

**Collatz constraint:** This CC contains no domain logic. It orchestrates governed WF invocations only. All domain behavior lives in the WFs and CCs it calls. Loop exits when slot_schedule is exhausted — no external kill signal, no polling.

**Cross-subdomain write rule:** This CC does not write to any store directly. All writes (BLOCKS, CONSENSUS_ROUNDS, TRANSACTION) occur through the owned CCs of their respective subdomains, invoked via governed WFs.

---

**Step 12**
```
Artifact:    blockchain::WF_PROPOSE_BLOCK_V0
Action:      UPDATE
Subdomain:   consensus_pos
Depends on:  Step 2 (IN_BLOCK_PROPOSED_V0 updated — slot and epoch now required fields)
             Step 3 (CC_QUERY_ELIGIBLE_VALIDATORS_V0 updated — filter corrected)
PPS status:  EXISTS — update node bindings only; topology unchanged
```
Topology is identical to the existing artifact — no new nodes, no outcome changes. Two changes only:

1. **IN reference:** The WF now references the updated `IN_BLOCK_PROPOSED_V0` (Step 2), which requires slot and epoch. No change to WF admission node declaration — the IN is referenced by FQDN; the schema change is in the IN artifact.

2. **CC_FORM_BLOCK_V0 node input bindings:** Add two JSONPath bindings to the CC_FORM_BLOCK_V0 node:
   - `slot` ← `$.payload.slot`
   - `epoch` ← `$.payload.epoch`

No other bindings change. No node additions. No outcome changes.

Existing bindings retained:
- `CC_SELECT_PROPOSER_V0` receives `eligible_validators` from `$.results.CC_QUERY_ELIGIBLE_VALIDATORS_V0.eligible_validators`
- `CC_SELECT_PROPOSER_V0` receives `round_number` from `$.payload.round_number`
- `CC_FORM_BLOCK_V0` receives `proposer_id` from `$.results.CC_SELECT_PROPOSER_V0.proposer_id`
- `CC_FORM_BLOCK_V0` receives `tx_ids` from `$.results.CC_QUERY_PENDING_TRANSACTIONS_V0.tx_ids`
- `CC_FORM_BLOCK_V0` receives `round_id` from `$.payload.round_number`
- `CC_RECORD_CONSENSUS_ROUND_V0` receives `block_id` from `$.results.CC_FORM_BLOCK_V0.block_id`

---

### Wave 3 — Governing Workflow (after Wave 2)

**Step 13**
```
Artifact:    blockchain::WF_RUN_CONSENSUS_SLOTS_V0
Action:      NEW
Subdomain:   consensus_pos
Depends on:  Step 1 (IN_CONSENSUS_SLOTS_V0), Step 10 (CC_VERIFY_SLOT_RESULTS_V0), Step 11 (CC_EXECUTE_SLOT_SEQUENCE_V0)
PPS status:  NOT PRESENT — must author
```
Governing workflow for the finite consensus slot run. Declare `subdomain: consensus_pos`. Bounded-run artifact only — not live-protocol compatible (D1, D4).

Execution topology (3-node linear DAG):
```
IN_CONSENSUS_SLOTS_V0 (Step 1)
    ACK  → CC_EXECUTE_SLOT_SEQUENCE_V0 (Step 11)
    NACK → EXIT

CC_EXECUTE_SLOT_SEQUENCE_V0
    SUCCESS       → CC_VERIFY_SLOT_RESULTS_V0 (Step 10)
    VIOLATION     → EXIT
    BACKEND_ERROR → EXIT

CC_VERIFY_SLOT_RESULTS_V0
    SUCCESS       → EXIT_SLOTS_COMPLETE
    VIOLATION     → EXIT
    BACKEND_ERROR → EXIT

EXIT_SLOTS_COMPLETE
EXIT
```

JSONPath input bindings:
- `CC_EXECUTE_SLOT_SEQUENCE_V0` receives `slot_schedule` from `$.payload.slot_schedule`
- `CC_EXECUTE_SLOT_SEQUENCE_V0` receives `triggered_by` from `$.payload.triggered_by`
- `CC_VERIFY_SLOT_RESULTS_V0` receives `slots_executed` from `$.results.CC_EXECUTE_SLOT_SEQUENCE_V0.slots_executed`

Emits `EV_SLOTS_COMPLETE_V0` (REUSE) on EXIT_SLOTS_COMPLETE path.

---

### Wave 4 — Terminal Runtime Binding

**Step 14**
```
Artifact:    blockchain::RB_RUN_CONSENSUS_SLOTS_V0
Action:      NEW
Subdomain:   consensus_pos
Depends on:  Step 13 (WF_RUN_CONSENSUS_SLOTS_V0)
PPS status:  NOT PRESENT — must author
```
Runtime binding for WF_RUN_CONSENSUS_SLOTS_V0. Follows the same pattern as existing `blockchain::RB_PROPOSE_BLOCK_V0`.

Bindings required:
- `capability_side_effects::CS_WORKFLOW_GATEWAY_V0` — for WF invocations inside CC_EXECUTE_SLOT_SEQUENCE_V0
- `capability_side_effects::CS_MUTABLE_JSON_V0` — for BLOCKS and TRANSACTION store reads in CC_VERIFY_SLOT_RESULTS_V0
- `capability_side_effects::CS_APPENDONLY_JSONL_V0` — for CONSENSUS_ROUNDS read access if needed by verify step

`storage_structure`: `blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0`

---

## Critical Path

```
Step 1 (IN_CONSENSUS_SLOTS_V0) → Step 11 (CC_EXECUTE_SLOT_SEQUENCE_V0) → Step 13 (WF_RUN_CONSENSUS_SLOTS_V0) → Step 14 (RB_RUN_CONSENSUS_SLOTS_V0)
```
4 sequential steps. All other steps may proceed in parallel at their respective waves.

---

## Dependency Graph Summary

```
Wave 1 (parallel — 9 steps):
    Step 1   IN_CONSENSUS_SLOTS_V0               NEW  — consensus_pos
    Step 2   IN_BLOCK_PROPOSED_V0                UPDATE — consensus_pos
    Step 3   CC_QUERY_ELIGIBLE_VALIDATORS_V0     UPDATE — consensus_pos
    Step 4   IN_VALIDATOR_REGISTERED_V0          UPDATE — validator
    Step 5   RB_MINT_V0                          UPDATE — transaction
    Step 6   RB_BURN_V0                          UPDATE — transaction
    Step 7   RB_POOL_V0                          UPDATE — transaction
    Step 8   RB_REWARD_V0                        UPDATE — transaction
    Step 9   RB_SLASH_V0                         UPDATE — transaction

Wave 2 (parallel — 3 steps, after respective Wave 1 deps):
    Step 10  CC_VERIFY_SLOT_RESULTS_V0           NEW  — consensus_pos (no new deps)
    Step 11  CC_EXECUTE_SLOT_SEQUENCE_V0         NEW  — consensus_pos ← needs Step 1
    Step 12  WF_PROPOSE_BLOCK_V0                 UPDATE — consensus_pos ← needs Steps 2, 3

Wave 3 (after Steps 1, 10, 11):
    Step 13  WF_RUN_CONSENSUS_SLOTS_V0           NEW  — consensus_pos

Wave 4 (after Step 13):
    Step 14  RB_RUN_CONSENSUS_SLOTS_V0           NEW  — consensus_pos
```

---

## Artifact Summary

| Action | Count | Artifacts |
|--------|-------|-----------|
| NEW | 5 | IN_CONSENSUS_SLOTS_V0, CC_EXECUTE_SLOT_SEQUENCE_V0, CC_VERIFY_SLOT_RESULTS_V0, WF_RUN_CONSENSUS_SLOTS_V0, RB_RUN_CONSENSUS_SLOTS_V0 |
| UPDATE | 9 | IN_BLOCK_PROPOSED_V0, WF_PROPOSE_BLOCK_V0, CC_QUERY_ELIGIBLE_VALIDATORS_V0 (consensus_pos); RB_MINT_V0, RB_BURN_V0, RB_POOL_V0, RB_REWARD_V0, RB_SLASH_V0 (transaction); IN_VALIDATOR_REGISTERED_V0 (validator) |
| REUSE | 7 | CC_FORM_BLOCK_V0, CC_SELECT_PROPOSER_V0, CC_RECORD_CONSENSUS_ROUND_V0, CC_SKIP_ROUND_V0, CC_PERSIST_MEMPOOL_TX_V0, CT_PURE_EXTRACT_V0, CT_PURE_ASSEMBLE_RECORD_V0 |
| EXTEND | 0 | No new stores — STRUCTURE_BLOCKCHAIN_STORAGE_V0 untouched |
| **Total authoring actions** | **14** | 5 NEW + 9 UPDATE |

---

## Subdomain Field Declarations

| Artifact Code | Subdomain Field Value | Note |
|---|---|---|
| `IN_CONSENSUS_SLOTS_V0` | `consensus_pos` | NEW |
| `CC_EXECUTE_SLOT_SEQUENCE_V0` | `consensus_pos` | NEW |
| `CC_VERIFY_SLOT_RESULTS_V0` | `consensus_pos` | NEW |
| `WF_RUN_CONSENSUS_SLOTS_V0` | `consensus_pos` | NEW |
| `RB_RUN_CONSENSUS_SLOTS_V0` | `consensus_pos` | NEW |
| `IN_BLOCK_PROPOSED_V0` | `consensus_pos` | UPDATE — subdomain field unchanged |
| `WF_PROPOSE_BLOCK_V0` | `consensus_pos` | UPDATE — subdomain field unchanged |
| `CC_QUERY_ELIGIBLE_VALIDATORS_V0` | `consensus_pos` | UPDATE — subdomain field unchanged |
| `IN_VALIDATOR_REGISTERED_V0` | `validator` | UPDATE — subdomain field unchanged |
| `RB_MINT_V0` | `transaction` | UPDATE — subdomain field unchanged |
| `RB_BURN_V0` | `transaction` | UPDATE — subdomain field unchanged |
| `RB_POOL_V0` | `transaction` | UPDATE — subdomain field unchanged |
| `RB_REWARD_V0` | `transaction` | UPDATE — subdomain field unchanged |
| `RB_SLASH_V0` | `transaction` | UPDATE — subdomain field unchanged |

*Subdomain field governs trace routing and data store path resolution. Must be declared in every WF, CC, IN, RB artifact.*

---

## Cross-Subdomain Dependency Notes

**Permitted — cross-subdomain capability calls:**
- `CC_EXECUTE_SLOT_SEQUENCE_V0` (consensus_pos) invokes typed transaction WFs (transaction subdomain) via `CS_WORKFLOW_GATEWAY_V0` EXECUTE per slot
- `CC_EXECUTE_SLOT_SEQUENCE_V0` (consensus_pos) invokes `WF_PROPOSE_BLOCK_V0` (consensus_pos) via `CS_WORKFLOW_GATEWAY_V0` EXECUTE per slot
- `CC_VERIFY_SLOT_RESULTS_V0` (consensus_pos) reads BLOCKS store (block subdomain) and TRANSACTION store (transaction subdomain) — read-only

**Forbidden — cross-subdomain direct writes:**
- `CC_EXECUTE_SLOT_SEQUENCE_V0` must NOT write to BLOCKS, TRANSACTION, or VALIDATOR stores directly
- All writes occur through the owned CCs of their respective subdomains, invoked via governed WFs
- `CC_VERIFY_SLOT_RESULTS_V0` is read-only — no writes of any kind

**Five SYSTEM WF RB updates (Steps 5–9) — transaction-owned:**
- The CS_REGISTRY_V0 gap is owned by `blockchain::transaction` — the runtime bindings are transaction artifacts
- No consensus_pos artifact has ownership over these bindings
- After update: all 8 typed WFs have complete CS wiring for `CC_PERSIST_MEMPOOL_TX_V0` tx dedup

---

## Authoring Notes

**UPDATE semantics:** UPDATE artifacts retain their FQDN and version (`V0`). The artifact is authored in place — the protocol source file is modified to reflect the change declared in this mandate. No new version number is required for correction-only changes that do not alter the outcome contract.

**Validator schema fix scope:** `IN_VALIDATOR_REGISTERED_V0` is the admission gate — extending it to 8 fields ensures that the payload admitted at registration contains the canonical fields required by `CC_QUERY_ELIGIBLE_VALIDATORS_V0` at block proposal time. The VALIDATOR store path and CS type are unchanged; only the admitted record schema is extended.

**CC_EXECUTE_SLOT_SEQUENCE_V0 is not a WF:** It is a Capability Contract that absorbs an iteration loop internally (Collatz pattern). The WF_RUN_CONSENSUS_SLOTS_V0 DAG has exactly 3 nodes (IN gate + 2 CCs). The loop logic is entirely inside the CC — the WF DAG contains no loops.

**CS_WORKFLOW_GATEWAY_V0 is the governed WF invocation mechanism:** All WF-to-WF invocations from within a CC must use `CS_WORKFLOW_GATEWAY_V0` EXECUTE. This CC does not call WFs by any other mechanism. Confirmed present in PPS snapshot at authoring time.

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 1 — Input Elicitation | Problem + Outcome + Known Facts | COMPLETE |
| Stage 2 — Domain Model Discovery | Entities, Processes, PPS Baseline, Gap Analysis | COMPLETE |
| Stage 3 — Analysis Loop | Q1–Q6 resolved; 2 iterations; 6 gaps registered and resolved | COMPLETE — SATURATED |
| Stage 4 — Business Model | 4_business_model_consensus_propose_v0.md | COMPLETE |
| Stage 5 — Business Intent | 5_business_intent_consensus_propose_v0.md | COMPLETE |
| Stage 6 — Governance Intent | 6_governance_intent_consensus_propose_v0.md | COMPLETE |
| Stage 6b — Design Intent | 6b_design_intent_consensus_propose_v0.md | COMPLETE |
| Stage 7 — Authoring Mandate | This document | PENDING APPROVAL |
| Stage 8 — Authoring Manifest | PENDING |

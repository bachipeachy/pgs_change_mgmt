# Stage 6b — Design Intent: blockchain / consensus_propose
**Domain:** blockchain
**Subdomains:** consensus_pos, transaction, validator
**Version:** V0
**Status:** DRAFT
**Pipeline Stage:** Stage 6b — Design Intent (HOW)
**Produced by:** v0.5.0 SDLC authoring pipeline
**Purity:** HOW only — business facts (Business Model) and placement decisions (Governance Intent) not repeated

---

## 1. Design Decisions Resolution

The Design Decisions Register was populated throughout Stages 1–4. These decisions are resolved here into concrete artifact and schema choices.

| Decision | Business Fact (Business Model) | Design Resolution |
|----------|-------------------------------|-------------------|
| D1 — Bounded loop artifact only | WF_RUN_CONSENSUS_SLOTS_V0 governs finite runs only | WF and its CC are authored as bounded-run artifacts; no live-mode configuration or flag; live daemon calls WF_PROPOSE_BLOCK_V0 directly per slot |
| D2 — Collatz pattern for slot iteration | PGS WF is a DAG — no WF-level looping | CC_EXECUTE_SLOT_SEQUENCE_V0 absorbs the N-slot loop internally; WF DAG is linear (3 nodes); loop lives entirely inside the CC |
| D3 — Termination declared in input | Termination declared by finite slot_schedule | IN_CONSENSUS_SLOTS_V0 requires slot_schedule as a non-empty array; CC exits when list is exhausted — no poll, no flag, no kill signal |
| D4 — Live and test are different architectures | Test: coupled CC loop; Live: decoupled streams | No single artifact bridges the two; WF_RUN_CONSENSUS_SLOTS_V0 and CC_EXECUTE_SLOT_SEQUENCE_V0 are test/bounded-run artifacts; live requires no new artifact |
| D5 — Canonical validator fields | status + effective_balance are canonical; enrollment_status + stake are retired | CC_QUERY_ELIGIBLE_VALIDATORS_V0 filter updated to {status: ACTIVE_ONGOING, effective_balance: present}; IN_VALIDATOR_REGISTERED_V0 schema extended to 8 fields including status and effective_balance |
| D6 — Validator schema fix in this CR | Validator registration → eligibility path is a runtime blocker | IN_VALIDATOR_REGISTERED_V0 and CC_QUERY_ELIGIBLE_VALIDATORS_V0 updated before this CR exits |
| D7 — Caller computes slot + epoch | slot = round_number % 32; epoch = round_number // 32 | IN_BLOCK_PROPOSED_V0 gains slot and epoch as required fields; WF_PROPOSE_BLOCK_V0 wires them to CC_FORM_BLOCK_V0 inputs; no new CT for slot arithmetic |

---

## 2. Canonical Validator Field Decision

The Governance Intent required alignment between the validator registration schema and the eligibility query filter. The consensus_pos CR (predecessor) authored both artifacts with different field names — creating a gap that this CR resolves.

**Design resolution:** `status` and `effective_balance` are the canonical validator fields. `enrollment_status` and `stake` are retired. The VALIDATOR store path and CS type are unchanged.

| Field | Type | Description |
|-------|------|-------------|
| actor_id | string | Identity registry link — primary key |
| validator_index | integer | Consensus-layer numeric index |
| pubkey | string | BLS12-381 signing key |
| withdrawal_credentials | string | Withdrawal destination address |
| status | string | ACTIVE_ONGOING, EXITED, or SLASHED — canonical lifecycle field |
| effective_balance | integer | Declared stake in BACHI — canonical eligibility field |
| activation_epoch | integer | Epoch at which the validator became active |
| exit_epoch | integer | Epoch at which the validator exits; null if not scheduled |

**Consequence:** IN_VALIDATOR_REGISTERED_V0 must be updated to admit all 8 fields. CC_QUERY_ELIGIBLE_VALIDATORS_V0 must be updated to filter on `{status: "ACTIVE_ONGOING", effective_balance: present}`. No change to the VALIDATOR store path or storage type.

---

## 3. Artifact Inventory — Existing Artifacts

All existing PPS artifacts touched by this CR.

| Artifact | Action | Reason |
|----------|--------|--------|
| `blockchain::IN_BLOCK_PROPOSED_V0` | UPDATE | Add `slot` and `epoch` as required fields |
| `blockchain::WF_PROPOSE_BLOCK_V0` | UPDATE | Wire `slot` and `epoch` to CC_FORM_BLOCK_V0 node inputs |
| `blockchain::CC_QUERY_ELIGIBLE_VALIDATORS_V0` | UPDATE | Replace filter fields: `enrollment_status`/`stake` → `status`/`effective_balance` |
| `blockchain::IN_VALIDATOR_REGISTERED_V0` | UPDATE | Extend from 4-field to 8-field canonical schema |
| `blockchain::RB_MINT_V0` | UPDATE | Add CS_REGISTRY_V0 bindings for register_tx_key and register_tx_hash steps |
| `blockchain::RB_BURN_V0` | UPDATE | Add CS_REGISTRY_V0 bindings for register_tx_key and register_tx_hash steps |
| `blockchain::RB_POOL_V0` | UPDATE | Add CS_REGISTRY_V0 bindings for register_tx_key and register_tx_hash steps |
| `blockchain::RB_REWARD_V0` | UPDATE | Add CS_REGISTRY_V0 bindings for register_tx_key and register_tx_hash steps |
| `blockchain::RB_SLASH_V0` | UPDATE | Add CS_REGISTRY_V0 bindings for register_tx_key and register_tx_hash steps |
| `blockchain::CC_FORM_BLOCK_V0` | REUSE | Already requires slot and epoch as inputs; no change to CC itself |
| `blockchain::CC_SELECT_PROPOSER_V0` | REUSE | Sound — no change |
| `blockchain::CC_RECORD_CONSENSUS_ROUND_V0` | REUSE | Sound — no change |
| `blockchain::CC_SKIP_ROUND_V0` | REUSE | Sound — no change |
| `blockchain::CC_PERSIST_MEMPOOL_TX_V0` | REUSE | Sound — invoked by all 8 typed WFs; CS_REGISTRY_V0 fix is in the RBs, not in this CC |
| `blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0` | REUSE | No new stores required — BLOCKS, CONSENSUS_ROUNDS, TRANSACTION, VALIDATOR all declared in prior CRs |

---

## 4. Artifact Family Mapping — New Artifacts

Mapping from Governance Outcome capabilities to artifact families, with FQDN codes assigned. Organized by subdomain ownership as declared in Governance Intent.

### blockchain::consensus_pos — New Artifacts

#### Workflow: Finite Consensus Slot Loop

| Artifact | Family | Code | Status |
|----------|--------|------|--------|
| Finite slot loop governing workflow | WF | `blockchain::WF_RUN_CONSENSUS_SLOTS_V0` | NEW |
| Slot loop admission intent | IN | `blockchain::IN_CONSENSUS_SLOTS_V0` | NEW |
| Slot loop runtime binding | RB | `blockchain::RB_RUN_CONSENSUS_SLOTS_V0` | NEW |

#### Capability Contracts: Slot Loop Pipeline

| Capability | Family | Code | Status |
|------------|--------|------|--------|
| Slot sequence execution (Collatz-pattern loop) | CC | `blockchain::CC_EXECUTE_SLOT_SEQUENCE_V0` | NEW |
| Post-run result verification | CC | `blockchain::CC_VERIFY_SLOT_RESULTS_V0` | NEW |

---

## 5. Execution Topology — WF_RUN_CONSENSUS_SLOTS_V0

High-level DAG. JSONPath input bindings are authoring-phase detail.

```
IN_CONSENSUS_SLOTS_V0
    ACK  → CC_EXECUTE_SLOT_SEQUENCE_V0
    NACK → EXIT

CC_EXECUTE_SLOT_SEQUENCE_V0             ← consensus_pos
    SUCCESS       → CC_VERIFY_SLOT_RESULTS_V0
    VIOLATION     → EXIT
    BACKEND_ERROR → EXIT

CC_VERIFY_SLOT_RESULTS_V0               ← consensus_pos
    SUCCESS       → EXIT_SLOTS_COMPLETE
    VIOLATION     → EXIT

EXIT_SLOTS_COMPLETE
EXIT
```

**Path summary:**
- Happy path: slot schedule admitted → all slots executed → results verified → EXIT_SLOTS_COMPLETE
- Execution failure: any slot produces VIOLATION or BACKEND_ERROR → EXIT
- Verification failure: PROPOSED block or tx type coverage missing → EXIT with VIOLATION
- Short-circuit exits: admission NACK; VIOLATION or BACKEND_ERROR from either CC

**Cross-subdomain calls inside this WF:** None at the WF node level. All cross-subdomain work happens internally inside CC_EXECUTE_SLOT_SEQUENCE_V0, which invokes governed WFs belonging to the transaction and consensus_pos subdomains per slot.

---

## 6. CC Pipeline Declarations (Summary)

Design-level pipeline intent for each new CC. Full JSONPath bindings are authoring-phase detail.

### consensus_pos Pipelines

**CC_EXECUTE_SLOT_SEQUENCE_V0** *(consensus_pos)*
- Step 1: Iterate over slot_schedule — for each slot descriptor in order:
  - Step 1a: For each transaction in the slot's transaction list, invoke the matching typed transaction WF (WF_SUBMIT_TRANSFER_V0, WF_SUBMIT_MINT_V0, etc.) via CS_WORKFLOW_GATEWAY_V0 EXECUTE — mempool write is a side effect of each invocation
  - Step 1b: Invoke WF_PROPOSE_BLOCK_V0 with round_number, slot, epoch, timestamp, triggered_by via CS_WORKFLOW_GATEWAY_V0 EXECUTE — block proposal and round recording are side effects
- Step 2: When slot_schedule is exhausted, assemble counters (slots_executed, blocks_proposed, rounds_skipped, tx_submitted) → SUCCESS
- Result statuses: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`
- *All cross-subdomain writes occur within the owned CCs of their respective subdomains — this CC only invokes WFs; it does not write to any store directly*

**CC_VERIFY_SLOT_RESULTS_V0** *(consensus_pos)*
- Step 1: CS_MUTABLE_JSON_V0 — LIST — BLOCKS store → filter status = PROPOSED → count
- Step 2: CT_PURE_EXTRACT_V0 (REUSE) — assert count ≥ 1 → VIOLATION if zero
- Step 3: CS_MUTABLE_JSON_V0 — LIST — TRANSACTION store → filter status = PENDING → extract tx_type values
- Step 4: CT_PURE_EXTRACT_V0 (REUSE) — assert all 8 expected tx_types present → VIOLATION per missing type
- Result statuses: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`
- *Read-only — no writes; reads from BLOCKS (block-owned) and TRANSACTION (transaction-owned) stores*

---

## 7. Execution Topology — WF_PROPOSE_BLOCK_V0 (Updated)

The existing WF topology is sound. This update adds slot and epoch to the IN schema and wires them through to CC_FORM_BLOCK_V0. No new nodes. No topology change.

```
IN_BLOCK_PROPOSED_V0       ← UPDATE: add slot, epoch as required fields
    ACK  → CC_QUERY_ELIGIBLE_VALIDATORS_V0
    NACK → EXIT

CC_QUERY_ELIGIBLE_VALIDATORS_V0    ← UPDATE: filter on status + effective_balance
    SUCCESS       → CC_SELECT_PROPOSER_V0
    NOT_FOUND     → CC_SKIP_ROUND_V0
    VIOLATION     → EXIT
    BACKEND_ERROR → EXIT

CC_SELECT_PROPOSER_V0              ← REUSE
    SUCCESS       → CC_QUERY_PENDING_TRANSACTIONS_V0
    VIOLATION     → EXIT

CC_QUERY_PENDING_TRANSACTIONS_V0   ← REUSE (transaction-owned)
    SUCCESS       → CC_FORM_BLOCK_V0
    EMPTY         → CC_SKIP_ROUND_V0
    VIOLATION     → EXIT
    BACKEND_ERROR → EXIT

CC_FORM_BLOCK_V0                   ← REUSE (block-owned); now receives slot + epoch via WF binding
    SUCCESS       → CC_RECORD_CONSENSUS_ROUND_V0
    VIOLATION     → EXIT
    BACKEND_ERROR → EXIT

CC_RECORD_CONSENSUS_ROUND_V0       ← REUSE
    SUCCESS       → EXIT_BLOCK_PROPOSED
    VIOLATION     → EXIT
    BACKEND_ERROR → EXIT

CC_SKIP_ROUND_V0                   ← REUSE
    SUCCESS       → EXIT_ROUND_SKIPPED
    VIOLATION     → EXIT
    BACKEND_ERROR → EXIT

EXIT_BLOCK_PROPOSED
EXIT_ROUND_SKIPPED
EXIT
```

**Change from existing:** Topology is identical. Two input fields added to IN_BLOCK_PROPOSED_V0 (`slot`, `epoch`). One node binding updated in WF_PROPOSE_BLOCK_V0 — CC_FORM_BLOCK_V0 node now receives `slot` and `epoch` from `$.payload.slot` and `$.payload.epoch`. No other changes.

---

## 8. STRUCTURE Extension — STRUCTURE_BLOCKCHAIN_STORAGE_V0

No new stores required for this CR. All stores accessed by this CR were declared in prior CRs.

| Store | Subdomain | Declared In | Access By This CR |
|-------|-----------|-------------|-------------------|
| BLOCKS | blockchain::block | consensus_pos CR | Read — CC_VERIFY_SLOT_RESULTS_V0 |
| CONSENSUS_ROUNDS | consensus_pos | consensus_pos CR | Write — CC_RECORD_CONSENSUS_ROUND_V0, CC_SKIP_ROUND_V0 (REUSE) |
| TRANSACTION (mempool) | blockchain::transaction | transaction CR | Read — CC_VERIFY_SLOT_RESULTS_V0; Write — typed WFs invoked per slot |
| VALIDATOR | consensus_pos / validator | consensus_pos CR | Read — CC_QUERY_ELIGIBLE_VALIDATORS_V0; Write — WF_REGISTER_VALIDATOR_V0 (schema fix only) |

Cross-subdomain write rule: CC_VERIFY_SLOT_RESULTS_V0 (consensus_pos) is read-only against BLOCKS and TRANSACTION stores. No consensus_pos artifact writes to block or transaction stores. All writes to BLOCKS occur through CC_FORM_BLOCK_V0 (block-owned). All writes to TRANSACTION occur through CC_PERSIST_MEMPOOL_TX_V0 (transaction-owned).

---

## 9. IN_CONSENSUS_SLOTS_V0 — Intent Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| triggered_by | string | YES | System actor_id initiating the slot sequence |
| start_timestamp | string | YES | ISO-8601 start time for the slot run |
| slot_schedule | array | YES | Finite ordered list of slot descriptors; must be non-empty |
| └ round_number | integer | YES | Global round counter |
| └ slot | integer | YES | Slot within epoch (round_number % 32) |
| └ epoch | integer | YES | Epoch number (round_number // 32) |
| └ timestamp | string | YES | ISO-8601 timestamp for this slot |
| └ transactions | array | YES | Typed transaction descriptors to submit before this slot fires |

Outcomes: `ACK` (payload valid, slot_schedule non-empty, all required fields present), `NACK` (any required field missing or slot_schedule empty)

---

## 10. IN_BLOCK_PROPOSED_V0 — Updated Intent Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| triggered_by | string | YES | Actor_id initiating block proposal |
| round_number | integer | YES | Global round counter |
| slot | integer | YES | **ADDED** — slot within epoch; required by CC_FORM_BLOCK_V0 |
| epoch | integer | YES | **ADDED** — epoch number; required by CC_FORM_BLOCK_V0 |
| timestamp | string | YES | ISO-8601 timestamp for this slot |

Outcomes: `ACK` (all five fields present and valid), `NACK` (any required field missing)

---

## 11. Artifact Summary

Artifact count by action type, for Stage 7 (Authoring Mandate) input.

| Action | Count | Notes |
|--------|-------|-------|
| NEW (consensus_pos) | 5 | WF_RUN_CONSENSUS_SLOTS_V0, IN_CONSENSUS_SLOTS_V0, RB_RUN_CONSENSUS_SLOTS_V0, CC_EXECUTE_SLOT_SEQUENCE_V0, CC_VERIFY_SLOT_RESULTS_V0 |
| UPDATE (consensus_pos) | 3 | IN_BLOCK_PROPOSED_V0, WF_PROPOSE_BLOCK_V0, CC_QUERY_ELIGIBLE_VALIDATORS_V0 |
| UPDATE (transaction) | 5 | RB_MINT_V0, RB_BURN_V0, RB_POOL_V0, RB_REWARD_V0, RB_SLASH_V0 |
| UPDATE (validator) | 1 | IN_VALIDATOR_REGISTERED_V0 |
| REUSE | 7 | CC_FORM_BLOCK_V0, CC_SELECT_PROPOSER_V0, CC_RECORD_CONSENSUS_ROUND_V0, CC_SKIP_ROUND_V0, CC_PERSIST_MEMPOOL_TX_V0, CT_PURE_EXTRACT_V0, CT_PURE_ASSEMBLE_RECORD_V0 |
| EXTEND | 0 | No new stores — all storage declared in prior CRs |
| **Total authoring actions** | **14** | 5 NEW + 9 UPDATE |

Build dependency order is the output of Stage 7 — Authoring Mandate.

---

## 12. Governance Decision Gate

**Presenting for Analyst approval:**

1. No new stores — STRUCTURE_BLOCKCHAIN_STORAGE_V0 is unchanged; all required stores were declared in prior CRs
2. No new CTs — slot arithmetic is caller-supplied (D7); verification and extraction reuse CT_PURE_EXTRACT_V0; no genuinely new pure computation required
3. CC_EXECUTE_SLOT_SEQUENCE_V0 absorbs the N-slot loop via CS_WORKFLOW_GATEWAY_V0 EXECUTE — it invokes governed WFs; it does not write to any store directly; all store writes occur in owned CCs of their respective subdomains
4. WF_PROPOSE_BLOCK_V0 topology is unchanged — only IN schema (2 new fields) and one node binding (slot + epoch wired to CC_FORM_BLOCK_V0) are updated
5. CC_QUERY_ELIGIBLE_VALIDATORS_V0 filter field swap is a one-line update — no topology or pipeline step change; only the filter predicate changes
6. Five SYSTEM WF RB fixes are structurally identical — each RB gains two CS_REGISTRY_V0 step bindings (register_tx_key, register_tx_hash); no CC or WF changes
7. IN_VALIDATOR_REGISTERED_V0 gains 4 fields — status, effective_balance, activation_epoch, exit_epoch; validator_record object schema extended; no WF topology change
8. 14 authoring actions total: 5 NEW (consensus_pos), 9 UPDATE (3 consensus_pos + 5 transaction + 1 validator)

*Analyst approval of this document gates entry into Stage 7 — Authoring Mandate.*

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 1 — Input Elicitation | Problem + Outcome + Known Facts | COMPLETE |
| Stage 2 — Domain Model Discovery | Entities, Processes, PPS Baseline, Gap Analysis | COMPLETE |
| Stage 3 — Analysis Loop | Q1–Q6 resolved; 2 iterations; 6 gaps registered and resolved | COMPLETE — SATURATED |
| Stage 4 — Business Model | Capability graph, dependency graph, constraints, gaps, design decisions, authoring scope | COMPLETE |
| Stage 5 — Business Intent | 5_business_intent_consensus_propose_v0.md | COMPLETE |
| Stage 6 — Governance Intent | 6_governance_intent_consensus_propose_v0.md | COMPLETE |
| Stage 6b — Design Intent | This document | PENDING APPROVAL |
| Stage 7 — Authoring Mandate | 7_authoring_mandate_consensus_propose_v0.md | PENDING APPROVAL |
| Stage 8 — Authoring Manifest | PENDING |

# Stage 3 — Analysis Loop: blockchain / orchestration
**Stage:** 3 — Analysis Loop  
**CR:** 1_change_request_orchestration_v0.md  
**Iterations:** 2 (saturated)  
**Status:** COMPLETE  
**Feeds:** Stage 4 — Business Model  

---

## Iteration 1

*Resolves Stage 2 Q1–Q5 against PPS artifact inspection. Surfaces two new gaps requiring Iteration 2.*

### Q1 — Supersede WF_RUN_CONSENSUS_SLOTS_V0 or extend?

**Finding:** Supersede confirmed. WF_RUN_CONSENSUS_SLOTS_V0 has two bundled responsibilities: TX dispatch per slot (CC_EXECUTE_SLOT_SEQUENCE_V0 item_sub_sequence) + slot execution (WF_PROPOSE_BLOCK_V0 invocation per item_wf). These must be separated.

*PPS evidence: WF_RUN_CONSENSUS_SLOTS_V0 Machine (confirmed from snapshot): CC_EXECUTE_SLOT_SEQUENCE_V0 uses CS_WORKFLOW_LOOP_V0 EXECUTE_SEQUENCE with item_sub_sequence (dispatches TX types to WF_TRANSFER_V0, WF_MINT_V0, etc.) AND item_wf (invokes WF_PROPOSE_BLOCK_V0 per slot). Both concerns are inseparable inside this single artifact.*

**Resolution:** WF_PROCESS_SLOT_V0 is a new artifact that owns only slot execution (one slot = one invocation of WF_PROPOSE_BLOCK_V0). It supersedes the slot execution concern. WF_RUN_CONSENSUS_SLOTS_V0 and CC_EXECUTE_SLOT_SEQUENCE_V0 remain in snapshot unchanged as historical artifacts — no deprecation action required. The Collatz loop pattern (CS_WORKFLOW_LOOP_V0) is reusable for WF_RUN_CONSENSUS_LOOP_V0.

**Answer:** Supersede. WF_PROCESS_SLOT_V0 is the new atomic slot execution unit. CS_WORKFLOW_LOOP_V0 is reused by WF_RUN_CONSENSUS_LOOP_V0 for repeated WF_PROCESS_SLOT_V0 invocations.

---

### Q2 — WF_PROCESS_SLOT_V0 invokes WF_PROPOSE_BLOCK_V0 directly or consensus CCs?

**Finding:** WF_PROPOSE_BLOCK_V0 confirmed as the correct invocation target. CS_WORKFLOW_GATEWAY_V0 is the correct mechanism. IN_BLOCK_PROPOSED_V0 requires exactly 5 fields: `round_number` (int ≥ 0), `slot` (int), `epoch` (int), `timestamp` (ISO 8601), `triggered_by` (string).

*PPS evidence: IN_BLOCK_PROPOSED_V0 Machine (confirmed from snapshot): inputs are round_number (required, integer, minimum 0), slot (required, integer, minimum 0), epoch (required, integer, minimum 0), timestamp (required, string, date-time), triggered_by (required, string). Notes state: "slot = round_number % 32; epoch = round_number // 32 — supplied by CC_EXECUTE_SLOT_SEQUENCE_V0 from slot descriptor." CS_WORKFLOW_GATEWAY_V0 (confirmed from snapshot): EXECUTE operation — takes workflow_code + payload, returns result_status + execution_result. This is the correct single-WF invocation substrate.*

**New gap surfaced:** `slot = round_number % 32` and `epoch = round_number // 32` are currently derived by CC_EXECUTE_SLOT_SEQUENCE_V0 from the slot descriptor. WF_PROCESS_SLOT_V0 must derive these from its input slot_number. No existing CT for slot/epoch derivation found in snapshot — a new CT is needed.

**Resolution:** WF_PROCESS_SLOT_V0 uses CS_WORKFLOW_GATEWAY_V0 to invoke WF_PROPOSE_BLOCK_V0. A new CT (pure computation) derives slot and epoch from round_number before the gateway call. Clean boundary: orchestration invokes the consensus WF; orchestration never touches consensus CCs.

**Answer:** WF_PROCESS_SLOT_V0 → CS_WORKFLOW_GATEWAY_V0 → WF_PROPOSE_BLOCK_V0. New CT required for slot/epoch derivation.

---

### Q3 — What replaces slot_specs.json?

**Finding:** SEED_CHAIN_SIMULATION_CONFIG_V0 is the correct pattern. However, seed content must be significantly richer than initially expected — TX payloads are type-specific and cannot be expressed as bare tx_type strings (see Q5 finding below).

*PPS evidence: seeds/ directory pattern confirmed — seeds/blockchain/consensus_pos/slot_specs.json provides typed slot descriptors with fully resolved TX payloads (from_wallet_id, to_address, amount, actor_record, etc.) pre-populated per slot. This resolution is currently done by resolve_tx() in test_blockchain_e2e.py using actor_lookup and wallet_lookup.*

**Resolution:** SEED_CHAIN_SIMULATION_CONFIG_V0 at seeds/blockchain/orchestration/simulation_config.json. Contains: simulation_id, slot_duration_seconds, max_slots, tx_interval_seconds, tx_sequence (array of fully resolved TX payload objects, not bare type strings — see Q5). The existing slot_specs.json may serve as reference for TX payload structure.

**Answer:** SEED_CHAIN_SIMULATION_CONFIG_V0 confirmed. Design details depend on Q5 resolution (see Iteration 2).

---

### Q4 — Simulation controller termination contract?

**Finding:** SUCCESS / VIOLATION contract is fully viable. Output fields (slots_processed, blocks_proposed, transactions_submitted, transactions_confirmed, violations_detected) can be aggregated from sub-WF execution results.

*PPS evidence: CS_WORKFLOW_GATEWAY_V0 EXECUTE returns result_status + execution_result — the execution_result carries sub-WF output fields. CS_WORKFLOW_LOOP_V0 EXECUTE_SEQUENCE returns items_processed + sub_items_processed. These two aggregation sources are sufficient for the simulation summary output.*

**New gap surfaced (CRITICAL):** No CS exists for concurrent WF dispatch. CS_WORKFLOW_GATEWAY_V0 invokes one WF sequentially. CS_WORKFLOW_LOOP_V0 iterates a sequence sequentially. Neither enables concurrent execution of two independent WFs. WF_RUN_CHAIN_SIMULATION_V0 requires a new CS that declares concurrent WF dispatch intent — the CS substrate implements physical concurrency (asyncio.gather or threading) in its RB, consistent with the architectural principle "PGS governs orchestration intent, not execution mechanics."

**Resolution:** Q4 termination contract confirmed. Concurrent dispatch gap is carried to Iteration 2.

**Answer:** SUCCESS/VIOLATION contract confirmed. New CS_CONCURRENT_WORKFLOWS_V0 required for concurrent WF dispatch — resolved in Iteration 2.

---

### Q5 — TX workload dispatches to WF_SUBMIT_TRANSACTION_V0 or typed WFs?

**Finding (CRITICAL REVISION of Stage 2 Decision):** Q5 Stage 2 decision (dispatch to WF_SUBMIT_TRANSACTION_V0 with tx_type as payload) is NOT viable. Each TX type has a completely incompatible input schema. Dispatch to typed WFs is required.

*PPS evidence:*
- *IN_TRANSACTION_SUBMITTED_V0 Machine (confirmed from snapshot): `status: RETIRED`, `superseded_by: [IN_TRANSFER_V0, IN_STAKE_V0, IN_UNSTAKE_V0, IN_MINT_V0, IN_BURN_V0, IN_POOL_V0, IN_REWARD_V0, IN_SLASH_V0]`*
- *IN_MINT_V0 (confirmed): inputs are to_wallet_id (required), amount (required), triggered_by (required) — no actor_record, no mnemonic, no gas params. Authority: SYSTEM.*
- *IN_TRANSFER_V0 (confirmed): inputs are actor_record (required, object with email), from_wallet_id (required), to_address (required), amount (required) — complex ETH-identity-bound fields.*
- *These schemas are structurally incompatible. A single WF_SUBMIT_TRANSACTION_V0 dispatched with tx_type as payload cannot satisfy both.*

**Resolution:** Q5 Stage 2 decision is revised. TX workload coordinator must dispatch to typed WFs (WF_MINT_V0, WF_TRANSFER_V0, WF_STAKE_V0, etc.) using a dispatch-by-tx_type mapping — exactly the same CS_WORKFLOW_LOOP_V0 dispatch pattern used by CC_EXECUTE_SLOT_SEQUENCE_V0's item_sub_sequence. SEED_CHAIN_SIMULATION_CONFIG_V0 must contain fully resolved TX payload objects per TX type, not bare type strings. The orchestration principle of "knowing submit transaction, not transaction taxonomy" holds for INTENT — but the dispatch mapping and payload resolution are a concrete implementation necessity that must be reflected in the seed design.

**Answer (Revised):** TX workload coordinator dispatches to typed WFs via tx_type dispatch mapping (CS_WORKFLOW_LOOP_V0 pattern). SEED_CHAIN_SIMULATION_CONFIG_V0 contains fully resolved TX payload objects per TX sequence entry. WF_SUBMIT_TRANSACTION_V0 is not used by the orchestration subdomain.

---

## Saturation Assessment — After Iteration 1

| Criterion | Status | Evidence |
|-----------|--------|----------|
| No unresolved CRITICAL gaps | NOT SATISFIED | Two new CRITICAL gaps: (1) no CS for concurrent WF dispatch; (2) Q5 TX dispatch revision requires seed design confirmation |
| No open analyst questions | NOT SATISFIED | Concurrent dispatch CS design not yet specified; SEED_CHAIN_SIMULATION_CONFIG_V0 payload structure not finalized |
| No dependency expansion in last pass | NOT SATISFIED | New dependency: CS_CONCURRENT_WORKFLOWS_V0 (new CS, not in snapshot); new CT for slot/epoch derivation (not in snapshot) |

**NOT SATURATED — proceed to Iteration 2.**

---

## Iteration 2

*Resolves concurrent dispatch CS design, slot/epoch CT gap, and SEED payload structure. No further new dependencies expected.*

### Gap A — No CS for Concurrent WF Dispatch

**Finding:** A new CS_CONCURRENT_WORKFLOWS_V0 is required and fully definable using the established PGS CS pattern.

*Evidence: CS_WORKFLOW_GATEWAY_V0 (sequential, one WF) and CS_WORKFLOW_LOOP_V0 (sequential iteration) are the only WF-execution CS capabilities in the snapshot. Neither supports concurrent execution. The implementation substrate for CS_CONCURRENT_WORKFLOWS_V0 would use asyncio.gather() to launch multiple WF invocations and wait for all to return — consistent with the transport-layer concurrency model established in Stage 1.*

**Resolution:** CS_CONCURRENT_WORKFLOWS_V0 is a new infrastructure-owned CS with operation EXECUTE_CONCURRENT:
- Input: `workflows` (array of {wf_code, payload} objects), `triggered_by` (string)
- Behavior: invokes all declared WFs concurrently; waits for all to complete
- Output: `results` (array of {wf_code, result_status, execution_result}), `all_succeeded` (boolean)
- Result status: SUCCESS (all WFs returned SUCCESS), PARTIAL_FAILURE (any WF returned non-SUCCESS), BACKEND_ERROR

WF_RUN_CHAIN_SIMULATION_V0 uses this CS via a CC (CC_DISPATCH_SIMULATION_WORKERS_V0) that declares the two workers (WF_RUN_CONSENSUS_LOOP_V0 + WF_RUN_TX_WORKLOAD_V0) as concurrent execution targets. The CC owns the dispatch declaration; the CS provides the substrate.

**Answer:** CS_CONCURRENT_WORKFLOWS_V0 must be authored. One new CC (CC_DISPATCH_SIMULATION_WORKERS_V0) declared in the orchestration subdomain.

---

### Gap B — No CT for Slot/Epoch Derivation

**Finding:** A new CT_PURE_DERIVE_SLOT_EPOCH_V0 is required. The computation is pure (zero side effects, deterministic) and trivially simple.

*Evidence: IN_BLOCK_PROPOSED_V0 notes: "slot = round_number % 32; epoch = round_number // 32 — supplied by CC_EXECUTE_SLOT_SEQUENCE_V0 from slot descriptor." In the new model, slot and epoch are no longer in a pre-built slot descriptor — they must be computed from slot_number before WF_PROPOSE_BLOCK_V0 can be invoked. No existing CT in snapshot handles integer modulo/floor-division derivation. CT_PURE_VALIDATE_PARAMETER_RULES_V0 and similar CTs are validation-only, not derivation.*

**Resolution:** CT_PURE_DERIVE_SLOT_EPOCH_V0 — pure computation, zero side effects:
- Input: `round_number` (integer ≥ 0), `slots_per_epoch` (integer, default 32)
- Output: `slot` (integer), `epoch` (integer)
- Logic: slot = round_number % slots_per_epoch; epoch = round_number // slots_per_epoch

WF_PROCESS_SLOT_V0 contains a CC that calls this CT before invoking WF_PROPOSE_BLOCK_V0.

**Answer:** CT_PURE_DERIVE_SLOT_EPOCH_V0 must be authored. One new CC (CC_PREPARE_SLOT_CONTEXT_V0) wraps this CT in the orchestration subdomain's WF_PROCESS_SLOT_V0 pipeline.

---

### Gap C — SEED_CHAIN_SIMULATION_CONFIG_V0 Payload Structure

**Finding:** SEED_CHAIN_SIMULATION_CONFIG_V0 must contain fully resolved TX payload objects per tx_sequence entry. This is structurally analogous to slot_specs.json and can reuse its pattern.

*Evidence: slot_specs.json (from seeds/blockchain/consensus_pos/) contains fully pre-resolved TX payloads per slot (from_wallet_id, to_address, amount, actor_record.email_registration, etc.) alongside slot identity fields. The existing resolve_tx() function in test_blockchain_e2e.py performs actor/wallet lookup to build these fields. SEED_CHAIN_SIMULATION_CONFIG_V0 replaces this by declaring pre-resolved payloads directly in the seed — no runtime resolution required.*

**Resolution:** SEED_CHAIN_SIMULATION_CONFIG_V0 structure:
```
simulation_id: demo_001
slot_duration_seconds: 3
max_slots: 24
tx_interval_seconds: 2
triggered_by: <genesis_actor_id>
tx_sequence:
  - tx_type: MINT
    payload: { to_wallet_id: ..., amount: ..., triggered_by: ... }
  - tx_type: TRANSFER
    payload: { actor_record: {...}, from_wallet_id: ..., to_address: ..., amount: ... }
  - tx_type: BURN
    payload: { ... }
  - tx_type: STAKE
    payload: { ... }
  - tx_type: UNSTAKE
    payload: { ... }
```
The TX workload cycles through tx_sequence entries; each cycle dispatch uses the pre-resolved payload directly. No runtime wallet/actor lookup required.

**Answer:** SEED_CHAIN_SIMULATION_CONFIG_V0 contains fully resolved TX payload objects keyed by tx_type. Existing seeds/blockchain/consensus_pos/ pattern is the direct template.

---

## Saturation Assessment — After Iteration 2

| Criterion | Status | Evidence |
|-----------|--------|----------|
| No unresolved CRITICAL gaps | SATISFIED | All 4 CRITICAL gaps resolved: slot clock (CS_MUTABLE_JSON_V0 + new STRUCTURE entity), concurrent dispatch (CS_CONCURRENT_WORKFLOWS_V0), TX dispatch revision (typed WF dispatch mapping), slot/epoch CT (CT_PURE_DERIVE_SLOT_EPOCH_V0) |
| No open analyst questions | SATISFIED | Q1–Q5 fully resolved; Gaps A, B, C resolved; no new questions surfaced in Iteration 2 |
| No dependency expansion in last pass | SATISFIED | Iteration 2 resolved its own introduced dependencies (CS_CONCURRENT_WORKFLOWS_V0, CT_PURE_DERIVE_SLOT_EPOCH_V0) with no further expansion |

**Saturation achieved in 2 iterations.**

---

## Consolidated Findings

### What Already Exists (fully reusable)

| Artifact | Status | Reuse |
|----------|--------|-------|
| WF_PROPOSE_BLOCK_V0 | EXISTS (canonical) | REUSE — invoked by WF_PROCESS_SLOT_V0 via CS_WORKFLOW_GATEWAY_V0; no changes required |
| WF_MINT_V0, WF_TRANSFER_V0, WF_BURN_V0, WF_STAKE_V0, WF_UNSTAKE_V0, WF_POOL_V0, WF_REWARD_V0, WF_SLASH_V0 | EXISTS (draft) | REUSE — invoked by TX workload coordinator via typed dispatch mapping; no changes required |
| CS_WORKFLOW_GATEWAY_V0 | EXISTS (draft) | REUSE — single WF invocation substrate for WF_PROCESS_SLOT_V0 → WF_PROPOSE_BLOCK_V0 |
| CS_WORKFLOW_LOOP_V0 | EXISTS (draft) | REUSE — loop substrate for WF_RUN_CONSENSUS_LOOP_V0 (slot sequence) and WF_RUN_TX_WORKLOAD_V0 (TX sequence) |
| CS_MUTABLE_JSON_V0 | EXISTS (draft) | REUSE — slot clock store (READ + WRITE operations) |
| WF_RUN_CONSENSUS_SLOTS_V0 | EXISTS (draft) | UNCHANGED — historical artifact; remains in snapshot; no deprecation |
| CC_EXECUTE_SLOT_SEQUENCE_V0 | EXISTS (draft) | UNCHANGED — historical artifact; remains in snapshot; no deprecation |

### What Must Be Authored (new artifacts)

| Artifact | Why New |
|----------|---------|
| CS_CONCURRENT_WORKFLOWS_V0 | No concurrent WF dispatch CS exists; sequential CS substrates (GATEWAY, LOOP) cannot satisfy concurrent execution requirement |
| WF_RUN_CHAIN_SIMULATION_V0 | No simulation controller exists; owns simulation clock, termination criteria, concurrent worker dispatch |
| WF_RUN_CONSENSUS_LOOP_V0 | No governed consensus loop coordinator exists; coordinates repeated WF_PROCESS_SLOT_V0 invocations via CS_WORKFLOW_LOOP_V0 |
| WF_RUN_TX_WORKLOAD_V0 | No governed TX workload coordinator exists; coordinates repeated typed-TX WF invocations via CS_WORKFLOW_LOOP_V0 dispatch mapping |
| WF_PROCESS_SLOT_V0 | No discrete single-slot execution WF exists; new concern separated from WF_RUN_CONSENSUS_SLOTS_V0 |
| CT_PURE_DERIVE_SLOT_EPOCH_V0 | No CT for slot/epoch derivation from round_number; required by WF_PROCESS_SLOT_V0 pipeline before WF_PROPOSE_BLOCK_V0 invocation |
| CC_DISPATCH_SIMULATION_WORKERS_V0 | New CC declaring concurrent worker dispatch intent via CS_CONCURRENT_WORKFLOWS_V0 |
| CC_PREPARE_SLOT_CONTEXT_V0 | New CC wrapping CT_PURE_DERIVE_SLOT_EPOCH_V0; prepares slot/epoch context from slot_number |
| CC_READ_SLOT_CLOCK_V0 | New CC reading current slot clock state from governed store |
| CC_ADVANCE_SLOT_CLOCK_V0 | New CC advancing slot clock from N to N+1 after slot execution |
| CC_RECORD_SIMULATION_SUMMARY_V0 | New CC recording simulation outcome (slots_processed, blocks_proposed, tx_submitted, tx_confirmed, violations_detected) |
| SEED_CHAIN_SIMULATION_CONFIG_V0 | New seed file at seeds/blockchain/orchestration/simulation_config.json; contains fully resolved TX payload objects per tx_sequence entry |
| STRUCTURE_BLOCKCHAIN_ORCHESTRATION_STORAGE_V0 | New compiler structure for orchestration subdomain; declares clock store entity and subdomain artifact families |

### Subdomain Placement Decision

**NEW subdomain — `blockchain::orchestration`**

The orchestration subdomain owns coordination artifacts (simulation controller, loop coordinators, slot clock, concurrent dispatch) that cross the governance boundaries of consensus_pos, transaction, and mempool. The slot clock entity, the simulation summary entity, and the concurrent dispatch CS are all orchestration-owned concerns that do not belong in any existing subdomain. Extending any existing subdomain would conflate coordination with execution. The Stage 0 classification and Stage 2 domain model both confirm this — Stage 3 PPS inspection provides no evidence to reverse that decision.

---

## Inputs to Stage 4 — Business Model

1. **New subdomain declared:** `blockchain::orchestration` — owns simulation coordination, slot clock, concurrent WF dispatch, and simulation outcome recording.
2. **New CS required:** CS_CONCURRENT_WORKFLOWS_V0 — concurrent WF dispatch substrate; implements asyncio.gather at transport layer; declared via CC_DISPATCH_SIMULATION_WORKERS_V0.
3. **New CT required:** CT_PURE_DERIVE_SLOT_EPOCH_V0 — derives slot and epoch from round_number (slot = round_number % slots_per_epoch; epoch = round_number // slots_per_epoch). Pure computation, zero side effects.
4. **Q5 Stage 2 decision revised:** TX workload dispatches to typed WFs (WF_MINT_V0, WF_TRANSFER_V0, etc.) via CS_WORKFLOW_LOOP_V0 dispatch mapping — NOT to WF_SUBMIT_TRANSACTION_V0. IN_TRANSACTION_SUBMITTED_V0 is RETIRED; typed TX schemas are incompatible.
5. **Existing artifacts unchanged:** WF_PROPOSE_BLOCK_V0, all typed TX WFs, WF_RUN_CONSENSUS_SLOTS_V0, CC_EXECUTE_SLOT_SEQUENCE_V0 — all reused or left as historical artifacts without modification.
6. **Seed pattern confirmed:** SEED_CHAIN_SIMULATION_CONFIG_V0 contains fully resolved TX payloads per tx_sequence entry; follows existing slot_specs.json structure pattern.
7. **All required WF execution substrates confirmed:** CS_WORKFLOW_GATEWAY_V0 (single WF call), CS_WORKFLOW_LOOP_V0 (sequential iteration), CS_MUTABLE_JSON_V0 (slot clock store) all exist and are reusable.
8. **Greenlit artifact set confirmed with additions:** 5 WFs + 1 CT + 1 CS + 5 CCs + 1 seed + 1 STRUCTURE for the orchestration subdomain.

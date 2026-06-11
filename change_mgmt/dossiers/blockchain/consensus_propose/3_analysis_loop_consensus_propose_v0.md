# Stage 3 — Analysis Loop: blockchain / consensus_propose
**Stage:** 3 — Analysis Loop
**CR:** 1_change_request_consensus_propose_v0.md
**Iterations:** 2 (saturated)
**Status:** COMPLETE
**Feeds:** Stage 4 — Business Model

---

## Iteration 1

*Each question is resolved by reading PPS snapshot artifacts directly. Findings are evidence-backed — no assertions without a source artifact.*

---

### Q1 — How should slot and epoch be resolved in the block proposal payload?

**Finding:** The gap is structural and confirmed. `slot` and `epoch` are declared required inputs to `CC_FORM_BLOCK_V0` but are not present in `IN_BLOCK_PROPOSED_V0` and are not wired in the `CC_FORM_BLOCK_V0` node of `WF_PROPOSE_BLOCK_V0`.

*Evidence:*
- `CC_FORM_BLOCK_V0` frontmatter declares six required inputs: `round_id`, `slot`, `epoch`, `proposer_id`, `tx_ids`, `timestamp`. Both `slot` and `epoch` are `required: true`.
- `WF_PROPOSE_BLOCK_V0` node inputs for `CC_FORM_BLOCK_V0`: `{proposer_id: $.results.CC_SELECT_PROPOSER_V0.proposer_id, round_id: $.payload.round_number, timestamp: $.payload.timestamp, tx_ids: $.results.CC_QUERY_PENDING_TRANSACTIONS_V0.tx_ids}`. Neither `slot` nor `epoch` is bound.
- `IN_BLOCK_PROPOSED_V0` frontmatter declares three inputs only: `round_number`, `triggered_by`, `timestamp`. No `slot`, no `epoch`.

**Resolution:** Two resolution paths exist:
- **Option A — Extend IN payload:** Add `slot` and `epoch` to `IN_BLOCK_PROPOSED_V0`. The consensus driver computes them from `round_number` (`slot = round_number % 32`, `epoch = round_number // 32`) before invoking the intent. The WF node bindings for `CC_FORM_BLOCK_V0` are updated to pass `$.payload.slot` and `$.payload.epoch`. No new artifact type needed.
- **Option B — Add CT derivation node:** Author a new CT (e.g., `CT_PURE_DERIVE_SLOT_EPOCH_V0`) that computes `slot` and `epoch` from `round_number`. Insert it as a node in `WF_PROPOSE_BLOCK_V0`. More self-contained but adds an artifact and a WF step.

**Answer:** **Option A** — extend IN and WF bindings. The consensus driver (whether a test script or a governed loop) knows the round number and can compute slot and epoch before invoking. This keeps the governed paths lean and avoids a new artifact for arithmetic that the caller already owns. Two artifacts require update: `IN_BLOCK_PROPOSED_V0` (add `slot`, `epoch` fields) and `WF_PROPOSE_BLOCK_V0` (add `slot`/`epoch` bindings to `CC_FORM_BLOCK_V0` node). These are updates to existing artifacts — no new artifact type.

---

### Q2 — What is the minimum canonical data set for test actors and validators?

**Finding:** The minimum data set is defined and documented. `blockchain_testdata.md` (domain-level, reusable across consensus CRs) specifies actors, wallets, validators, and a 24-slot transaction schedule covering all eight tx_types.

*Evidence — `blockchain_testdata.md`:*
- Actors: 4 INDIVIDUAL (Gomer Adams, Liam Adams, Isha Adams, Sophie Cyber) + 4 VALIDATOR (Bachi One–Four). Genesis Actor and Bachi Eight already seeded.
- Wallets: PRIVATE + BUSINESS per INDIVIDUAL actor (8 wallets). System wallets seeded.
- Validators: Bachi One–Four, ACTIVE, 32,000 BACHI effective_balance.
- Transaction schedule: 24 slots; MINT slots 1–8, POOL slot 9, REWARD slot 10, SLASH slot 11, TRANSFER/BURN/STAKE/UNSTAKE slots 12–24. All 8 tx_types exercised.

**Resolution:** Data population follows the existing governed paths in sequence: `WF_REGISTER_ACTOR_UNVERIFIED_V0` → `WF_VERIFY_ACTOR_V0` → `WF_CREATE_WALLET_V0` → `WF_REGISTER_VALIDATOR_V0`. Validator registration conformance has a gap (see Q5/Q6 below) that shapes how payloads must be constructed.

**Answer:** 4 INDIVIDUAL actors, 8 wallets (PRIVATE + BUSINESS each), 4 VALIDATOR actors, 4 validator records. 24-slot transaction schedule. All governed by `blockchain_testdata.md`.

---

### Q3 — Does the consensus loop driver belong inside the protocol or outside as a test script?

**Finding:** No governed artifact exists for the slot cycle driver. The decision is a design choice, not a discovery finding.

*Evidence:* No `WF_*`, `CC_*`, or `IN_*` artifact governs slot timing or round initiation. `WF_PROPOSE_BLOCK_V0` is invoked by an external caller supplying `round_number`, `triggered_by`, and `timestamp` — the intent is designed to be externally triggered.

**Resolution:** The consensus loop driver belongs **inside the protocol as a governed artifact**. Revised rationale: the slot cycle is strategic protocol behavior, not test infrastructure — whether the run is a finite regression test or a live validator daemon, the same governed contract applies. A Python script embedding this logic is a dead end; the governed WF is reusable across test and live contexts.

The apparent DAG constraint ("a DAG cannot loop") is resolved by the **Collatz pattern** established in `ai_governance::WF_DEMO_COLLATZ_CONJECTURE_V0`. In that subdomain, the variable-length Collatz iteration is absorbed entirely inside `CT_PURE_COLLATZ_STEP_V0` — the WF DAG remains a fixed linear graph; the iteration happens inside the transform. The same idiom applies here, with one difference: each consensus slot has side effects (block write, event append, tx persistence), so the iteration cannot be a CT (pure). It must be a CC that orchestrates CS operations internally.

**Collatz-pattern consensus loop design:**

```
WF_RUN_CONSENSUS_SLOTS_V0
  IN_CONSENSUS_SLOTS_V0                  ← admits: slot_schedule, triggered_by, start_timestamp
    ↓ ACK
  CC_EXECUTE_SLOT_SEQUENCE_V0            ← absorbs the N-slot loop (Collatz-style)
    internally iterates over slot_schedule:
      for each slot: submit pending txs (CS writes) → invoke block proposal (CS writes)
    exits when schedule is exhausted → SUCCESS
    ↓ SUCCESS
  CC_VERIFY_SLOT_RESULTS_V0              ← post-run inspection: ≥1 PROPOSED block; all 8 tx_types PENDING
    ↓ SUCCESS / VIOLATION
  EXIT_SLOTS_COMPLETE / EXIT_VIOLATION
```

**Termination nuance:** In a real blockchain, the consensus loop runs indefinitely — there is no natural exit. The PGS governed WF is inherently bounded because the slot_schedule in the IN is a finite list. Termination is declared in the input, not imposed externally. `CC_EXECUTE_SLOT_SEQUENCE_V0` exits when the schedule list is exhausted — clean, deterministic, and inspectable. For live operation, a daemon invokes `WF_PROPOSE_BLOCK_V0` once per slot externally — no change to the single-slot governed path is needed.

**Live vs. test distinction:**
- **Test (this CR):** `WF_RUN_CONSENSUS_SLOTS_V0` with `slot_schedule: [slot_1 … slot_24]` from `blockchain_testdata.md`. One governed execution, one trace, finite and inspectable.
- **Live (future):** External daemon calls `WF_PROPOSE_BLOCK_V0` at each slot boundary. The single-slot governed path is already correct — no new artifact needed for live once this CR closes.

**Answer:** Inside the protocol — four new governed artifacts: `IN_CONSENSUS_SLOTS_V0`, `WF_RUN_CONSENSUS_SLOTS_V0`, `CC_EXECUTE_SLOT_SEQUENCE_V0`, `CC_VERIFY_SLOT_RESULTS_V0`. The WF DAG is linear; the slot iteration is absorbed inside `CC_EXECUTE_SLOT_SEQUENCE_V0` using the Collatz pattern. Termination is declared by the finite slot_schedule in the IN.

---

### Q4 — Are the CS implementations for the eight typed transaction WFs confirmed wired at runtime?

**Finding:** CS wiring is **confirmed for ENDUSER WFs (TRANSFER, STAKE, UNSTAKE)** and **broken for SYSTEM WFs (MINT, BURN, POOL, REWARD, SLASH)** — a new gap not identified in Stage 2.

*Evidence:*
- `CC_PERSIST_MEMPOOL_TX_V0` pipeline uses three CS implementations: `CS_REGISTRY_V0` (two steps: `register_tx_key`, `register_tx_hash` for dedup), `CS_APPENDONLY_JSONL_V0` (TRANSACTION_EVENTS), `CS_MUTABLE_JSON_V0` (TRANSACTION store).
- All eight WFs include `CC_PERSIST_MEMPOOL_TX_V0` as a node — confirmed by inspecting each WF's node list.
- RB inspection for ENDUSER WFs (`RB_TRANSFER_V0`, `RB_STAKE_V0`, `RB_UNSTAKE_V0`): all three bind `CS_APPENDONLY_JSONL_V0`, `CS_MUTABLE_JSON_V0`, and `CS_REGISTRY_V0`. ✓
- RB inspection for SYSTEM WFs (`RB_MINT_V0`, `RB_BURN_V0`, `RB_POOL_V0`, `RB_REWARD_V0`, `RB_SLASH_V0`): all five bind `CS_APPENDONLY_JSONL_V0` and `CS_MUTABLE_JSON_V0` only. **`CS_REGISTRY_V0` is absent from all five SYSTEM WF runtime bindings.** ✗
- CS implementations (`CS_MUTABLE_JSON_V0`, `CS_APPENDONLY_JSONL_V0`) confirmed present in `pgs_capabilities` with test coverage.
- Storage structure `STRUCTURE_BLOCKCHAIN_STORAGE_V0` declares TRANSACTION and TRANSACTION_EVENTS stores at correct paths.

**Resolution:** This is a new critical gap. All five SYSTEM WF invocations will fail at `CC_PERSIST_MEMPOOL_TX_V0` when it attempts to call `CS_REGISTRY_V0` (not bound in their RBs). Five RB artifacts must be updated: `RB_MINT_V0`, `RB_BURN_V0`, `RB_POOL_V0`, `RB_REWARD_V0`, `RB_SLASH_V0` — each needs a `CS_REGISTRY_V0` binding added.

**Answer:** ENDUSER WFs: CS wiring confirmed. SYSTEM WFs: CS wiring broken — `CS_REGISTRY_V0` missing from 5 RBs. **New Gap 5 (CRITICAL)** — see updated gap register.

---

### Q5 — Does the enriched validator schema conform at runtime with the existing validator registration workflow?

**Finding:** There is a multi-layer schema fragmentation. Three artifacts that form the validator registration and eligibility path use incompatible field sets.

*Evidence:*
- `IN_VALIDATOR_REGISTERED_V0` declares 4 required fields in `validator_record`: `actor_id`, `effective_balance`, `pubkey`, `withdrawal_credentials`.
- `CC_WRITE_VALIDATOR_RECORD_V0` requires 8 fields in `validator_record`: adds `balance`, `registered_at`, `slashed`, `status` (enum with lifecycle values `PENDING_INITIALIZED`, `ACTIVE_ONGOING`, etc.).
- `WF_REGISTER_VALIDATOR_V0` passes `$.payload.validator_record` directly to `CC_WRITE_VALIDATOR_RECORD_V0` — no CT step augments the record. The 4 fields missing from IN must come from the caller payload.
- `CC_QUERY_ELIGIBLE_VALIDATORS_V0` filter step uses `CT_PURE_FILTER_RECORDS_V0` with filter `{enrollment_status: "ACTIVE", stake: "present"}`. Neither `enrollment_status` nor `stake` is declared in `CC_WRITE_VALIDATOR_RECORD_V0`'s input schema or in `IN_VALIDATOR_REGISTERED_V0`.

*The gap has two layers:*
1. **Registration gap:** IN declares 4 fields; CC requires 8. The 4 missing fields must be supplied by the caller in the payload object — not documented, not enforced.
2. **Eligibility filter gap:** Query filters on `enrollment_status` + `stake`; registration CC stores `status` + `effective_balance`. Field names are different. Validators registered through the governed path will **never be found** by the eligibility query unless `enrollment_status` and `stake` are also written to the validator record.

**Resolution:** This is a new gap surfaced by cross-artifact inspection. The governed fix is included in this CR — the schema fragmentation is a blocker, not deferred debt. Resolution:

- **Field name alignment:** `CC_QUERY_ELIGIBLE_VALIDATORS_V0` filter is updated from `{enrollment_status: "ACTIVE", stake: "present"}` to `{status: "ACTIVE_ONGOING", effective_balance: "present"}` — matching the field names that `CC_WRITE_VALIDATOR_RECORD_V0` actually stores. `enrollment_status` is retired; `status` with the detailed lifecycle enum is canonical.
- **IN schema extension:** `IN_VALIDATOR_REGISTERED_V0` is updated to declare the full `validator_record` schema — adding `balance`, `registered_at`, `slashed`, and `status` as required fields. Caller supplies all fields; no CT assembly step needed in the WF (the caller is authoritative for registration-time values).
- **No WF topology change:** `WF_REGISTER_VALIDATOR_V0` node structure unchanged — it still passes `$.payload.validator_record` directly to `CC_WRITE_VALIDATOR_RECORD_V0`. The fix is entirely in the IN schema declaration and the query CC filter.

**Answer:** Schema fragmentation resolved in this CR. **Gap 6 (CRITICAL)** — update `IN_VALIDATOR_REGISTERED_V0` (add 4 fields to validator_record schema) and update `CC_QUERY_ELIGIBLE_VALIDATORS_V0` filter (use `status`/`effective_balance`). Two artifacts affected.

---

*Q5 surfaces a dependent question about field pass-through in the IN. Recorded as Q6 and resolved in Iteration 2.*

---

## Iteration 2

### Q6 — What is the correct field alignment between the validator registration write path and the eligibility query filter?

**Finding:** `status` (detailed lifecycle enum) is the canonical field; `enrollment_status` is a stale label from an earlier design. `effective_balance` is the canonical stake field; `stake` is an undeclared alias. The query CC filter must be updated to use the canonical fields.

*Evidence:* `CC_WRITE_VALIDATOR_RECORD_V0` input schema declares `status` (enum: `PENDING_INITIALIZED`, `ACTIVE_ONGOING`, etc.) and `effective_balance` as required fields. Neither `enrollment_status` nor `stake` appears anywhere in the write CC's schema or in `STRUCTURE_BLOCKCHAIN_STORAGE_V0`. The query filter's use of these names is a stale reference — likely authored before the data_model CR enriched the validator schema.

**Resolution:** Update `CC_QUERY_ELIGIBLE_VALIDATORS_V0`'s filter from `{enrollment_status: "ACTIVE", stake: "present"}` to `{status: "ACTIVE_ONGOING", effective_balance: "present"}`. Update `IN_VALIDATOR_REGISTERED_V0` to declare the full `validator_record` schema. Registration payload for all four test validators uses `status: "ACTIVE_ONGOING"` and supplies `effective_balance: 32000000000` (in Gwei-equivalent units per the CC minimum constraint).

**Answer:** Canonical fields confirmed: `status: "ACTIVE_ONGOING"` and `effective_balance`. Query CC filter updated. IN schema extended. No workaround payload required — the governed contract is now self-consistent.

---

## Saturation Assessment

**Three-part saturation criterion:**

| Criterion | Status | Evidence |
|-----------|--------|----------|
| No unresolved CRITICAL gaps in the gap register | SATISFIED | All 6 gaps have a resolution path; new Gaps 5 and 6 are addressed — Gap 5 via RB updates, Gap 6 via test payload construction |
| No open analyst questions | SATISFIED | Q1–Q6 all answered; no new unknowns surfaced in Iteration 2 |
| No dependency expansion in the last review pass | SATISFIED | Iteration 2 confirmed Q6 without surfacing new dependencies |

**Saturation achieved in 2 iterations.**

---

## Consolidated Gap Register

| # | Gap | Severity | Resolution | Artifacts Affected |
|---|-----|----------|------------|--------------------|
| G1 | No INDIVIDUAL test actors, wallets, or validators | CRITICAL | Populate via governed registration path using blockchain_testdata.md | None — existing WFs reused |
| G2 | slot and epoch missing from WF_PROPOSE_BLOCK_V0 | CRITICAL | Extend IN_BLOCK_PROPOSED_V0 (add slot, epoch); update WF bindings | IN_BLOCK_PROPOSED_V0, WF_PROPOSE_BLOCK_V0 |
| G3 | Validator registry empty at runtime | CRITICAL | Resolved by G1 — validator registration populates the store | None additional |
| G4 | No governed consensus loop driver | CRITICAL | Author IN_CONSENSUS_SLOTS_V0, WF_RUN_CONSENSUS_SLOTS_V0, CC_EXECUTE_SLOT_SEQUENCE_V0, CC_VERIFY_SLOT_RESULTS_V0 using Collatz pattern | 4 new artifacts |
| G5 | SYSTEM WF RBs missing CS_REGISTRY_V0 binding | CRITICAL | Add CS_REGISTRY_V0 binding to 5 system WF RBs | RB_MINT_V0, RB_BURN_V0, RB_POOL_V0, RB_REWARD_V0, RB_SLASH_V0 |
| G6 | Validator eligibility query field mismatch (enrollment_status → status, stake → effective_balance) | CRITICAL | Update CC_QUERY_ELIGIBLE_VALIDATORS_V0 filter; extend IN_VALIDATOR_REGISTERED_V0 schema | CC_QUERY_ELIGIBLE_VALIDATORS_V0, IN_VALIDATOR_REGISTERED_V0 |

---

## Consolidated Findings

### What Already Exists (fully reusable)

| Artifact | Status | Reuse |
|----------|--------|-------|
| WF_REGISTER_ACTOR_UNVERIFIED_V0 | EXISTS | REUSE — actor registration path confirmed fit; exact match |
| WF_VERIFY_ACTOR_V0 | EXISTS | REUSE — actor verification path confirmed fit; exact match |
| WF_CREATE_WALLET_V0 | EXISTS | REUSE — wallet creation path confirmed fit; exact match |
| WF_REGISTER_VALIDATOR_V0 | EXISTS | REUSE WITH CAVEATS — validator registration path viable; caller must supply enriched payload (see G6) |
| WF_TRANSFER_V0, WF_STAKE_V0, WF_UNSTAKE_V0 | EXISTS | REUSE — ENDUSER WFs: CS wiring confirmed |
| WF_MINT_V0, WF_BURN_V0, WF_POOL_V0, WF_REWARD_V0, WF_SLASH_V0 | EXISTS | REUSE AFTER RB FIX — CS_REGISTRY_V0 must be added to each RB |
| WF_PROPOSE_BLOCK_V0 | EXISTS | REUSE AFTER IN+WF UPDATE — slot/epoch bindings must be added |
| CC_FORM_BLOCK_V0 | EXISTS | REUSE — artifact is correct; gap was in the WF caller, not the CC |
| CC_QUERY_ELIGIBLE_VALIDATORS_V0 | EXISTS | REUSE — filters on enrollment_status/stake; correct once validator records include these fields |
| CC_PERSIST_MEMPOOL_TX_V0 | EXISTS | REUSE — artifact is correct; gap was in missing RB bindings |
| CS_MUTABLE_JSON_V0, CS_APPENDONLY_JSONL_V0, CS_REGISTRY_V0 | EXISTS | REUSE — all CS implementations confirmed present with test coverage |
| STRUCTURE_BLOCKCHAIN_STORAGE_V0 | EXISTS | REUSE — all required stores declared (TRANSACTION, VALIDATOR, BLOCKS, CONSENSUS_ROUNDS) |

### What Must Be Authored or Updated

| Artifact | Action | Why |
|----------|--------|-----|
| IN_BLOCK_PROPOSED_V0 | UPDATE | Add `slot` (integer, required) and `epoch` (integer, required) to input schema |
| WF_PROPOSE_BLOCK_V0 | UPDATE | Add `slot: $.payload.slot` and `epoch: $.payload.epoch` bindings to CC_FORM_BLOCK_V0 node |
| RB_MINT_V0 | UPDATE | Add `CS_REGISTRY_V0` binding — required by CC_PERSIST_MEMPOOL_TX_V0 for tx dedup |
| RB_BURN_V0 | UPDATE | Add `CS_REGISTRY_V0` binding — same reason |
| RB_POOL_V0 | UPDATE | Add `CS_REGISTRY_V0` binding — same reason |
| RB_REWARD_V0 | UPDATE | Add `CS_REGISTRY_V0` binding — same reason |
| RB_SLASH_V0 | UPDATE | Add `CS_REGISTRY_V0` binding — same reason |
| IN_VALIDATOR_REGISTERED_V0 | UPDATE | Extend validator_record schema to declare all 8 required fields: adds balance, registered_at, slashed, status |
| CC_QUERY_ELIGIBLE_VALIDATORS_V0 | UPDATE | Change filter from {enrollment_status, stake} to {status: "ACTIVE_ONGOING", effective_balance: "present"} |
| IN_CONSENSUS_SLOTS_V0 | NEW | Admits the finite slot schedule to the governed consensus loop |
| WF_RUN_CONSENSUS_SLOTS_V0 | NEW | Governed entry point for a finite consensus run (test or live bounded scenario) |
| CC_EXECUTE_SLOT_SEQUENCE_V0 | NEW | Absorbs the N-slot loop using Collatz pattern; internally iterates over slot_schedule via CS operations |
| CC_VERIFY_SLOT_RESULTS_V0 | NEW | Post-run inspection — confirms ≥1 PROPOSED block and all 8 tx_types PENDING |

### Subdomain Placement Decision

**EXTEND existing subdomains — no new subdomain required.**

Updates touch existing subdomains: `consensus_pos` (IN + WF for block proposal and new consensus loop WF), `transaction` (RBs for SYSTEM WFs), `validator` (IN schema + query CC filter). The four new governed artifacts extend `consensus_pos`. No new governance policy, subdomain boundary, or artifact family is introduced.

---

## Inputs to Stage 4 — Business Model

1. **Slot/epoch fix:** `IN_BLOCK_PROPOSED_V0` extended with `slot` and `epoch` fields. `WF_PROPOSE_BLOCK_V0` wires these to `CC_FORM_BLOCK_V0`. The consensus loop CC computes `slot = round_number % 32`, `epoch = round_number // 32` before invoking the single-slot proposal path.

2. **SYSTEM WF RB fix:** Five runtime binding artifacts (MINT, BURN, POOL, REWARD, SLASH) must add `CS_REGISTRY_V0` binding. Without this, all SYSTEM WF invocations fail at `CC_PERSIST_MEMPOOL_TX_V0`.

3. **Validator schema fix (in this CR):** `IN_VALIDATOR_REGISTERED_V0` extended to declare all 8 required `validator_record` fields. `CC_QUERY_ELIGIBLE_VALIDATORS_V0` filter updated to use `status: "ACTIVE_ONGOING"` and `effective_balance: "present"` — canonical field names matching what `CC_WRITE_VALIDATOR_RECORD_V0` stores.

4. **Governed consensus loop — Collatz pattern:** Four new governed artifacts in `consensus_pos` subdomain: `IN_CONSENSUS_SLOTS_V0`, `WF_RUN_CONSENSUS_SLOTS_V0`, `CC_EXECUTE_SLOT_SEQUENCE_V0`, `CC_VERIFY_SLOT_RESULTS_V0`. The WF DAG is linear; `CC_EXECUTE_SLOT_SEQUENCE_V0` absorbs the N-slot iteration internally (side-effectful Collatz analog). Termination is declared by the finite `slot_schedule` in the IN — no external kill signal, no runtime flag. For live operation, the daemon calls `WF_PROPOSE_BLOCK_V0` per slot — the single-slot path is unchanged.

5. **Canonical data set:** Defined in `blockchain_testdata.md` — 4 INDIVIDUAL actors, 4 VALIDATOR actors, 8 individual wallets, 4 validator records (`status: "ACTIVE_ONGOING"`, `effective_balance: 32000000000`), 24-slot transaction schedule covering all 8 tx_types.

6. **Authoring totals:** 2 existing INs updated, 1 existing WF updated, 5 existing RBs updated, 1 existing CC updated; 4 new governed artifacts (IN + WF + 2 CC). No new subdomain. No new CT.

# Stage 3 — Analysis Loop: blockchain / data_model
**Stage:** 3 — Analysis Loop
**CR:** 1_change_request_data_model_v0.md
**Status:** COMPLETE — Iteration 1 / SATURATED
**Feeds:** Stage 4 — Business Model

---

## Iteration 1

### 1. Open Questions Resolved

#### Q1 — Balance reconciliation: new workflow or embedded CC sequence?

**Evidence:** User declared the full 6-step execution flow:

```
submit_tx → propose_block → attest_block → finalize_block → commit_to_chain → reconcile_update_wallet_user_balances
```

Each step is a named, discrete operation. reconcile is step 6 — it follows commit_to_chain (step 5) as a separate execution unit. It is not embedded inside block finalization.

**Resolution:** Balance reconciliation is a distinct governed workflow, not a CC sequence within an existing workflow. The declared flow implies a chain of 6 separately governable execution units. HOW those are implemented is Stage 6b. WHAT is declared here: `WF_RECONCILE_BALANCES_V0` is a required governed workflow absent from PPS.

---

#### Q2 — Validator lifecycle: full 9-state ETH2 or simplified subset?

**Evidence (PPS):** `IN_VALIDATOR_REGISTERED_V0` carries `enrollment_status` with 3 values: ACTIVE, INACTIVE, EXCLUDED. Confirmed by seed payload at `seeds/register_validator_payload.json` (enrollment_status: "ACTIVE").

**Evidence (user):** "user/validator status static but not changing as part of process, just a payload driven config change."

**Resolution:** The 9-state ETH2 lifecycle is declared as the governed controlled vocabulary for the `status` field on the Validator entity. Status values are enriched from 3 → 9. However, no workflow-driven status transitions are required in this CR — status is set at registration (payload) and updated via direct payload config change. There is no `WF_ACTIVATE_VALIDATOR_V0` or `WF_EXIT_VALIDATOR_V0` in scope. The field enrichment is sufficient for demo fidelity.

**Consequence:** enrollment_status → status (field rename) with 9-value governed enum replaces the current 3-value free string.

---

#### Q3 — Event sequencing: chained triggers or atomic co-emission?

**Evidence:** The declared flow is a sequential chain of 6 steps. Each step is a distinct governed execution unit. If reconciliation follows commit_to_chain as step 6, the trigger is a sequential event — not an atomic batch co-emission.

**Evidence (existing events in PPS):**
- EV_BLOCK_PROPOSED_V0 ✓ (proposed step has event)
- EV_TRANSACTION_SUBMITTED_V0 ✓
- EV_VALIDATOR_REGISTERED_V0 ✓
- EV_ACTOR_REGISTERED_UNVERIFIED_V0 ✓
- EV_ACTOR_VERIFIED_V0 ✓
- EV_WALLET_CREATION_REQUESTED_V0 ✓ (note: "requested" not "created" — a gap)

**Missing events needed for the declared flow:**
| Event | Purpose | Triggered By |
|-------|---------|-------------|
| EV_BLOCK_ATTESTED_V0 | Signals attestation threshold reached | WF_ATTEST_BLOCK_V0 |
| EV_BLOCK_FINALIZED_V0 | Signals finality achieved; triggers commit | WF_FINALIZE_BLOCK_V0 |
| EV_BLOCK_COMMITTED_V0 | Signals block written to canonical chain | WF_COMMIT_BLOCK_V0 |
| EV_BALANCE_RECONCILED_V0 | Signals per-wallet balance update completed | WF_RECONCILE_BALANCES_V0 |
| EV_TX_FINALIZED_V0 | Signals individual transaction status → FINALIZED | WF_RECONCILE_BALANCES_V0 |

**Resolution:** Events are sequential triggers — each workflow in the chain emits one event that signals the next step is ready. No atomic co-emission. Event chain: EV_BLOCK_FINALIZED_V0 → triggers commit → EV_BLOCK_COMMITTED_V0 → triggers reconcile → EV_BALANCE_RECONCILED_V0 (per wallet) + EV_TX_FINALIZED_V0 (per transaction).

---

#### Q4 — MINT wallet seeding: dedicated workflow or bootstrap seed file?

**Evidence (PPS):** Seeds directory contains: `seeds/license_facts.json`, `seeds/register_actor_unverified_payload.json`, `seeds/validators.json` (empty `{}`), `seeds/register_validator_payload.json`. No wallet seed file exists. The bootstrap pattern for static reference data is a seed file (license_facts.json precedent).

**Evidence (domain model):** MINT wallet belongs to the GENESIS system actor. It holds the initial 1,000,000 BACHI supply. It is not a user-created wallet — it is a system bootstrap artifact.

**Resolution:** MINT wallet (and BURN, POOL system wallets) are bootstrapped via seed file, not a governed workflow. A `seeds/system_wallets.json` seed is the correct pattern — consistent with how license_facts are handled. `WF_SEED_SUPPLY_V0` is NOT in scope for this CR.

**Action required:** `seeds/system_wallets.json` must be declared as a required seed artifact for this CR. The GENESIS actor record seed must also exist (a prerequisite for the MINT wallet's `user_id` reference).

---

#### Q5 — node_name and stake removal safety from validator intake?

**Evidence (PPS seed payload):** `seeds/register_validator_payload.json` currently contains:
```json
{
  "validator_record": {
    "actor_id": "AC_dc6e2a7ae93b8bae",
    "pubkey": "0xb301803f8b5ac4a1...",
    "withdrawal_credentials": "0x00fc3109a5e43640...",
    "effective_balance": 32000000000,
    "node_name": "bachi8-validator-node-01",
    "stake": "32000000000",
    "enrollment_status": "ACTIVE"
  }
}
```

**Evidence (PPS data store):** `seeds/validators.json` is empty `{}`. No validator record has been persisted to the data store. The seed payload is the submission payload, not stored data.

**Resolution:** node_name and stake removal is safe for this CR. The only artifact carrying these fields is the seed submission payload, which must be updated as part of this CR's authoring scope. The data store is empty — no migration required. The update to `seeds/register_validator_payload.json` is in-scope cleanup.

**Note:** `stake` duplicates `effective_balance` (both are 32000000000). `node_name` carries no governed meaning — it is an informal label with no routing or policy impact.

---

### 2. Critical Scope Finding — Workflow Gap

**The declared 6-step flow mapped against PPS:**

| Step | Declared Name | Governed Workflow | Status |
|------|--------------|-------------------|--------|
| 1 | submit_tx | WF_SUBMIT_TRANSACTION_V0 | EXISTS (partial — tx_type hardcoded as "ETH") |
| 2 | propose_block | WF_PROPOSE_BLOCK_V0 | EXISTS (partial — proposes only; no attest/finalize/commit) |
| 3 | attest_block | WF_ATTEST_BLOCK_V0 | MISSING |
| 4 | finalize_block | WF_FINALIZE_BLOCK_V0 | MISSING |
| 5 | commit_to_chain | WF_COMMIT_BLOCK_V0 | MISSING |
| 6 | reconcile_update_wallet_user_balances | WF_RECONCILE_BALANCES_V0 | MISSING |

**4 of 6 required workflows are absent from PPS.**

**Why this matters for the data model CR:** The enriched data model (balance fields, tx lifecycle, block finality state) is only observable through execution. A wallet balance field means nothing if the process that updates it (reconciliation) has no governed workflow. The data model enrichment is semantically complete only when the processes that produce enriched state are governed.

**Scope assessment:** The declared flow is part of the same business goal stated in the CR: "The demo workflow can show meaningful end-to-end behavior: submit transfer transaction with gas, observe validator activation, see block finalized." Without these 4 workflows, the enriched data model is still hollow — fields exist but no governed process updates them.

**Decision required at Stage 4:** Expand this CR's scope to include the 4 missing workflows as new governed artifacts, OR split into two CRs: (a) data model enrichment only, (b) consensus finalization and reconciliation workflows.

**Recommendation for Stage 4:** Expand scope. The data model enrichment and the consensus flow are tightly coupled — the enriched fields (block status FINALIZED, tx status FINALIZED, wallet balance updated) only become meaningful when the processes that set them are governed. Splitting risks delivering a still-hollow system.

---

### 3. Payload Defect — tx_type Hardcoded

**Evidence (PPS):** WF_SUBMIT_TRANSACTION_V0 sets `tx_type: "ETH"` as a hardcoded literal in two CC nodes:
- CC_VALIDATE_TRANSACTION_POLICY_V0 (`tx_type: "ETH"`)
- CC_PERSIST_TRANSACTION_TO_MEMPOOL_V0 (`tx_type: "ETH"`)

This predates the tx_type enum declared in Stage 2. The current implementation treats all transactions as type "ETH" regardless of submitted payload.

**Resolution required:** CC_VALIDATE_TRANSACTION_POLICY_V0 and CC_PERSIST_TRANSACTION_TO_MEMPOOL_V0 must read tx_type from the payload (`$.payload.tx_record.tx_type`) rather than hardcode it. This is a defect fix, not a new feature — IN_TRANSACTION_SUBMITTED_V0 must be updated to declare tx_type as a required governed field.

---

### 4. Event Vocabulary Gap — Existing Events vs. Required Events

**Full event inventory from PPS (blockchain domain):**

| Event | Exists | Notes |
|-------|--------|-------|
| EV_ACTOR_REGISTERED_UNVERIFIED_V0 | ✓ | |
| EV_ACTOR_VERIFIED_V0 | ✓ | |
| EV_ACTOR_REJECTED_V0 | ✓ | |
| EV_WALLET_CREATION_REQUESTED_V0 | ✓ | Name implies request, not completion — possible gap |
| EV_TRANSACTION_SUBMITTED_V0 | ✓ | |
| EV_TRANSACTION_REJECTED_V0 | ✓ | |
| EV_VALIDATOR_REGISTERED_V0 | ✓ | |
| EV_BLOCK_PROPOSED_V0 | ✓ | |
| EV_ROUND_SKIPPED_V0 | ✓ | |
| EV_BLOCK_ATTESTED_V0 | ✗ | **MISSING** |
| EV_BLOCK_FINALIZED_V0 | ✗ | **MISSING — keystone trigger** |
| EV_BLOCK_COMMITTED_V0 | ✗ | **MISSING** |
| EV_TX_FINALIZED_V0 | ✗ | **MISSING** |
| EV_BALANCE_RECONCILED_V0 | ✗ | **MISSING** |

**Note on EV_WALLET_CREATION_REQUESTED_V0:** The name "requested" suggests it fires at intent submission, not at wallet creation completion. If there is no EV_WALLET_CREATED_V0, the wallet creation confirmation event is missing. This is a naming/completeness issue to resolve in authoring scope.

---

### 5. Full Gap Register (Consolidated)

| # | Gap | Severity | Origin |
|---|-----|----------|--------|
| G1 | Actor field set: missing user_type, status lifecycle, kyc_verified, currency_preference, language | CRITICAL | Stage 2 |
| G2 | Wallet: no balance, no nonce, wallet_type is free string, no currency, no status | CRITICAL | Stage 2 |
| G3 | Transaction: no tx_type field, no status lifecycle, tx_type hardcoded as "ETH" in WF | CRITICAL | Stage 2 + this stage |
| G4 | Validator: enrollment_status is 3-state; ETH2 requires 9-state; no epoch fields; node_name and stake are redundant | MEDIUM | Stage 2 |
| G5 | Block: current block intent is a round trigger, not a block entity schema | CRITICAL | Stage 2 |
| G6 | EV_BLOCK_FINALIZED_V0 does not exist — no trigger for reconciliation | CRITICAL | Stage 2 |
| G7 | EV_TX_FINALIZED_V0 and EV_BALANCE_RECONCILED_V0 do not exist | MINOR | Stage 2 |
| G8 | WF_ATTEST_BLOCK_V0 does not exist | CRITICAL | This stage |
| G9 | WF_FINALIZE_BLOCK_V0 does not exist | CRITICAL | This stage |
| G10 | WF_COMMIT_BLOCK_V0 does not exist | CRITICAL | This stage |
| G11 | WF_RECONCILE_BALANCES_V0 does not exist — balance updates have no governed process | CRITICAL | This stage |
| G12 | EV_BLOCK_ATTESTED_V0 and EV_BLOCK_COMMITTED_V0 do not exist | MINOR | This stage |
| G13 | seeds/system_wallets.json does not exist — GENESIS actor and system wallet bootstrap missing | MEDIUM | This stage |

---

### 6. Saturation Declaration

**Iteration 1 is saturated.**

All five open questions from Stage 2 are resolved. The declared 6-step flow has been fully mapped against PPS. No new subdomains were discovered. No contradictions between Stage 2 domain model and PPS evidence remain unresolved.

**What is now fully known:**
- Data model enrichment scope: complete (5 subdomains, field sets defined, event vocabulary defined)
- Workflow gap scope: complete (4 missing workflows fully identified)
- Seed gap scope: complete (system_wallets.json and GENESIS actor seed required)
- Payload defect: complete (tx_type hardcoded in 2 CC nodes)
- Validator intake cleanup: complete (node_name, stake removal is safe)

**No Iteration 2 required.** All gaps are classified. Proceed to Stage 4.

---

## Consolidated Findings → Stage 4

### Finding Set A — Data Model Enrichment (5 Subdomains)

All five existing subdomains require field enrichment. No new runtime subdomain. Extension only.

| Subdomain | Field Additions | Enum Additions | Lifecycle |
|-----------|----------------|----------------|-----------|
| identity | user_type, status, kyc_verified, currency_preference, language, last_modified | user_type (8 values), status (6 values) | PENDING → VERIFIED / ACTIVE |
| wallet | balance (real), nonce, wallet_type (enum), currency (enum), network (enum), status, last_tx_at | wallet_type (7 values), status (3 values) | ACTIVE / INACTIVE / SUSPENDED |
| transaction | tx_type (enum), status lifecycle, base_fee_per_gas, effective_gas_price, gas_used, total_fee, block_number, block_hash, memo | tx_type (8 values), status (5 values) | PENDING → SUBMITTED → INCLUDED → FINALIZED |
| validator | status (9-state enum, renamed from enrollment_status), slashed, epoch fields (4), balance, last_attestation_slot; remove node_name and stake | status (9 values) | Payload-driven; no WF transitions in this CR |
| block | slot, epoch, proposer_index, state_root, transactions_root, receipts_root, gas_limit, gas_used, base_fee_per_gas, total_fees, transaction_count, status, is_canonical, justified_epoch, finalized_epoch | status (5 values) | PROPOSED → JUSTIFIED → FINALIZED |

### Finding Set B — Workflow Gap (New Governed Workflows Required)

| Workflow | Subdomain | Purpose |
|----------|-----------|---------|
| WF_ATTEST_BLOCK_V0 | consensus_pos | Collect validator attestations; advance block from PROPOSED → JUSTIFIED |
| WF_FINALIZE_BLOCK_V0 | consensus_pos | Advance block from JUSTIFIED → FINALIZED; emit EV_BLOCK_FINALIZED_V0 |
| WF_COMMIT_BLOCK_V0 | consensus_pos | Write finalized block to canonical chain; emit EV_BLOCK_COMMITTED_V0 |
| WF_RECONCILE_BALANCES_V0 | transaction (or consensus_pos) | Apply all finalized transactions to wallet balances; emit EV_BALANCE_RECONCILED_V0 per wallet and EV_TX_FINALIZED_V0 per transaction |

### Finding Set C — Event Gap (New Governed Events Required)

| Event | Purpose | Priority |
|-------|---------|---------|
| EV_BLOCK_ATTESTED_V0 | Marks attestation threshold reached | MINOR |
| EV_BLOCK_FINALIZED_V0 | Keystone trigger for commit step | CRITICAL |
| EV_BLOCK_COMMITTED_V0 | Signals canonical chain updated; triggers reconcile | CRITICAL |
| EV_TX_FINALIZED_V0 | Per-transaction confirmation of finalization | MINOR |
| EV_BALANCE_RECONCILED_V0 | Per-wallet balance update confirmation | MINOR |

### Finding Set D — Payload Defects (Fix Required in Existing Artifacts)

| Artifact | Defect | Fix |
|----------|--------|-----|
| WF_SUBMIT_TRANSACTION_V0 (via CC_VALIDATE_TRANSACTION_POLICY_V0) | tx_type hardcoded as "ETH" | Read from `$.payload.tx_record.tx_type` |
| WF_SUBMIT_TRANSACTION_V0 (via CC_PERSIST_TRANSACTION_TO_MEMPOOL_V0) | tx_type hardcoded as "ETH" | Read from `$.payload.tx_record.tx_type` |
| IN_TRANSACTION_SUBMITTED_V0 | tx_type field absent | Add tx_type as required governed field with enum constraint |
| IN_VALIDATOR_REGISTERED_V0 | enrollment_status (3-state), node_name, stake present | Rename enrollment_status → status; update to 9-state enum; remove node_name and stake |
| seeds/register_validator_payload.json | node_name, stake, enrollment_status (outdated) | Update to match new IN_ schema |

### Finding Set E — Seed Gap

| Seed Artifact | Status | Required |
|---------------|--------|---------|
| seeds/system_wallets.json | MISSING | GENESIS actor + MINT/BURN/POOL system wallets with opening balances |
| seeds/genesis_actor.json | MISSING (inferred) | GENESIS actor record — prerequisite for system wallet user_id reference |

### Scope Decision for Stage 4

**Recommended scope:** Include Findings B, C, D, and E in this CR alongside Finding A. Rationale: the data model enrichment (A) is observable only through governed processes (B). The tx_type defect (D) must be fixed to make tx_type a payload discriminator. Seeds (E) are bootstrap prerequisites for system wallets. Events (C) are the governance signal layer for the new processes. These are not separable without delivering a still-hollow system.

**If scope is split:** the data model CR delivers enriched field definitions with no observable outcome. A second CR delivers the workflows. This is a viable phasing strategy but risks the CR being undemonstrable until the second CR closes.

---

## Stage 3 Gate

**Gate passed.** Discovery is saturated. All gaps classified. Consolidated findings ready for Stage 4.

**Proceed to Stage 4 — Business Model.**

---

## Amendments

**Status:** Post-authoring retroactive fix — Option B (amendment section added; approved content above unchanged)
**Source of truth:** 6b_design_intent_data_model_v0.md (Design Pivot Record) and 8_authoring_manifest_data_model_v0.md (Sections 1, 2, 7)

The gap findings in this document remain correct — the gaps existed and were critical inputs to the governed pipeline. The following amendments record where the resolution mechanism differed from what the analysis loop anticipated.

---

### Amendment A — WF_SUBMIT_TRANSACTION_V0 was retired, not patched

**Analysis loop location:** Section 2 (Workflow Gap) — Step 1: "WF_SUBMIT_TRANSACTION_V0 | EXISTS (partial — tx_type hardcoded as 'ETH')"

**Anticipated resolution:** Fix the existing WF by patching CC_VALIDATE_TRANSACTION_POLICY_V0 and CC_PERSIST_TRANSACTION_TO_MEMPOOL_V0 to read tx_type from payload.

**As-built:** `WF_SUBMIT_TRANSACTION_V0` was RETIRED. The Design Pivot (approved Stage 6b) determined that patching a unified WF cannot resolve the architecture defect: a unified WF with a tx_type payload field cannot express type-specific topology at compile time without runtime branching — itself a governance violation. The resolution was **8 typed transaction workflows** (WF_TRANSFER_V0 through WF_SLASH_V0), one per transaction type. Each typed WF carries its own IN_, RB_, and CC_VALIDATE_<TYPE>_POLICY_V0.

**Gap finding G3 remains valid:** The tx_type problem was correctly identified. The resolution was a topology redesign, not a CC-level patch.

---

### Amendment B — Finding Set D artifacts were retired, not fixed

**Analysis loop location:** Finding Set D (Payload Defects) — lists `WF_SUBMIT_TRANSACTION_V0`, `CC_VALIDATE_TRANSACTION_POLICY_V0`, `CC_PERSIST_TRANSACTION_TO_MEMPOOL_V0`, and `IN_TRANSACTION_SUBMITTED_V0` as fix targets.

**As-built:** All four artifacts were RETIRED. No CC-level payload fix was applied because the unified WF topology was replaced entirely.

| Finding Set D Entry | Anticipated Fix | As-Built Disposition |
|---------------------|-----------------|----------------------|
| `WF_SUBMIT_TRANSACTION_V0` (via CC_VALIDATE) | Read tx_type from payload | RETIRED — replaced by 8 typed WFs |
| `WF_SUBMIT_TRANSACTION_V0` (via CC_PERSIST) | Read tx_type from payload | RETIRED — replaced by 8 typed WFs |
| `IN_TRANSACTION_SUBMITTED_V0` | Add tx_type required field | RETIRED — replaced by 8 typed IN_ |
| `IN_VALIDATOR_REGISTERED_V0` | Rename status, 9-state enum | UPDATED as planned — not retired |
| `seeds/register_validator_payload.json` | Update to match new IN_ schema | UPDATED as planned |

**Finding Set D root cause was correct.** The resolution mechanism was more radical than anticipated: retire-and-replace rather than patch-in-place.

---

### Amendment C — Scope Decision tx_type mechanism clarification

**Analysis loop location:** Scope Decision for Stage 4 — "The tx_type defect (D) must be fixed to make tx_type a payload discriminator."

**As-built:** tx_type is NOT a payload discriminator — it is expressed by WF identity. The WF the caller invokes (WF_TRANSFER_V0, WF_STAKE_V0, etc.) IS the type. No payload field selects the execution path. The scope decision recommendation (keep transaction artifacts in this CR) was correct; the mechanism description was not.

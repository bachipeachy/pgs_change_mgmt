# Stage 6 — Governance Intent: blockchain / data_model
**Domain:** blockchain
**CR:** 1_change_request_data_model_v0.md
**Version:** V0
**Status:** DRAFT
**Pipeline Stage:** Stage 6 — Governance Intent (WHERE)
**Produced by:** v0.5.0 SDLC authoring pipeline
**Purity:** WHERE only — artifact family mapping, provisional artifact codes, and store path declarations excluded

---

## 1. Domain Placement

| Field | Value |
|-------|-------|
| Domain | `blockchain` |
| FQDN namespace | `blockchain` |
| Subdomains touched | identity, wallet, transaction, consensus_pos |
| All subdomain status | EXISTING — all declared in PPS namespace topology |
| New subdomains | NONE — this CR extends only; no new governed namespace is declared |

This CR is a pure enrichment CR. It enriches the field sets, enums, and events of five existing governed entity types across four existing subdomains. It does not introduce new workflows, new topology paths, or new subdomains. The governed data model becomes semantically complete; the execution topology is unchanged.

---

## 2. Authority and Governance

| Concern | Governing Constitution |
|---------|----------------------|
| Actor authority | `fb.constitution::CONSTITUTION_GOVERNANCE_V0` |
| Execution topology (WF, IN, CC) | `fb.topology::CONSTITUTION_WORKFLOW_V0`, `fb.topology::CONSTITUTION_INTENT_V0`, `fb.topology::CONSTITUTION_CAPABILITY_CONTRACT_V0` |
| Storage topology | `fb.constitution::CONSTITUTION_STRUCTURE_V0` |
| Domain invariants | `blockchain::INVARIANT_CT_SURFACE_CLOSED_BLOCKCHAIN_V0` |

**Authority classes in scope:**
- `ENDUSER` — actor-initiated intents (actor registration, wallet creation, transaction submission, validator registration)
- `SYSTEM` — consensus-driver-initiated intents (block proposal); protocol-generated transactions (MINT, REWARD, SLASH, BURN)

No new authority class is required. No new actor type is introduced. GENESIS is a governed `user_type` enum value on the Actor entity — it is not a new authority class.

---

## 3. Subdomain Boundary

### identity subdomain — EXTEND

| Capability | Ownership Decision |
|------------|-------------------|
| Actor registration with governed role (user_type enum) | OWNED — identity |
| Actor lifecycle status (PENDING → VERIFIED / ACTIVE) | OWNED — identity |
| KYC verification flag | OWNED — identity |
| Currency preference and language preference | OWNED — identity |
| GENESIS actor seed record | OWNED — identity (bootstrap; not workflow-registered) |

**Governance note:** GENESIS is a `user_type` enum value, not an authority class. The GENESIS actor record is loaded from a seed file at bootstrap time. It is never submitted through `IN_ACTOR_REGISTERED_V0`. The seed record bypasses the workflow registration path — this is consistent with the license_facts.json seed precedent and is explicitly permitted for bootstrap records.

### wallet subdomain — EXTEND

| Capability | Ownership Decision |
|------------|-------------------|
| Wallet creation with governed type (wallet_type enum) | OWNED — wallet |
| Real account state (balance, nonce, EOA address) | OWNED — wallet |
| Currency denomination (BACHI) | OWNED — wallet |
| System wallet seed records (MINT, BURN, POOL) | OWNED — wallet (bootstrap; not workflow-created) |
| Opening balance at wallet creation | OWNED — wallet |

**Governance note:** System wallets (MINT, BURN, POOL) belong to the GENESIS actor and are loaded from seeds/system_wallets.json at bootstrap. They are never submitted through `IN_WALLET_CREATED_V0`. The 1,000,000 BACHI initial supply is a bootstrap invariant — not a transaction-generated balance.

**Token economy invariant:** MINT.balance at bootstrap = total initial supply. Funds flow from MINT to user wallets via governed transactions. BURN is a permanent sink. Supply is conserved. This invariant is a governance boundary rule (see Section 7).

### transaction subdomain — EXTEND (includes defect fixes)

| Capability | Ownership Decision |
|------------|-------------------|
| Typed transaction submission (tx_type enum) | OWNED — transaction |
| EIP-1559 gas model (simplified BACHI amounts) | OWNED — transaction |
| Transaction lifecycle (PENDING → SUBMITTED → INCLUDED → FINALIZED) | OWNED — transaction |
| Asymmetric address schema (nullable from_address / to_address by tx_type) | OWNED — transaction |
| Mempool persistence with governed tx_type | OWNED — transaction (defect fix) |
| tx_type policy validation by transaction type | OWNED — transaction (defect fix) |

**Governance note on defects:** The tx_type defect is classified as a CC-level payload defect, not a topology defect. The WF topology (WF_SUBMIT_TRANSACTION_V0) is correct. Two CC implementations hardcode "ETH" instead of reading tx_type from payload — these are implementation defects in CC_VALIDATE_TRANSACTION_POLICY_V0 and CC_PERSIST_TRANSACTION_TO_MEMPOOL_V0. No topology change is required; only CC-level payload handling must be corrected.

### consensus_pos subdomain — EXTEND

| Capability | Ownership Decision |
|------------|-------------------|
| Validator registration with 9-state ETH2 lifecycle (status enum) | OWNED — consensus_pos |
| Validator epoch fields (activation, exit, withdrawable epochs) | OWNED — consensus_pos |
| Validator slashed flag and Gwei balance | OWNED — consensus_pos |
| Block entity enrichment (slot, epoch, block_type, finality fields) | OWNED — consensus_pos |
| Block status lifecycle (PROPOSED → JUSTIFIED → FINALIZED) | OWNED — consensus_pos |

**Governance note on validator status:** Status transitions are payload-driven only in this CR. The full ETH2 9-state lifecycle is declared as a governed enum; however, no workflow-driven lifecycle transitions are in scope. Status is set at registration by payload. Workflow-driven transitions are deferred to a future CR.

**Governance note on block enrichment:** `IN_BLOCK_PROPOSED_V0` is unchanged — it is a correct round trigger (round_number, triggered_by, timestamp). Block entity enrichment is a CC-level obligation on `CC_FORM_BLOCK_V0`, which now MUST write the full enriched block record. The intent surface is not the appropriate layer for block header field submission.

### Capabilities deferred to next CR — not owned this CR

| Capability | Reason |
|------------|--------|
| WF_ATTEST_BLOCK_V0 | Consensus finalization CR |
| WF_FINALIZE_BLOCK_V0 | Consensus finalization CR |
| WF_COMMIT_BLOCK_V0 | Consensus finalization CR |
| WF_RECONCILE_BALANCES_V0 | Consensus finalization CR |
| Balance updates on wallet records after finalization | Requires reconciliation workflow — next CR |
| Block status advancing past PROPOSED | Requires attestation and finalization workflows — next CR |
| Validator status transitions via workflow | Future CR — payload-driven only in this CR |
| Event emission for EV_BLOCK_FINALIZED_V0 and siblings | Emitter workflows are next CR; event declarations are this CR |

---

## 4. Composition — Extension Pattern

| Composition Decision | Detail |
|---------------------|--------|
| Domain | Extend existing `blockchain` domain — no new domain |
| Subdomains | Extend all 4 existing subdomains — no new subdomain declared |
| Actor types | Reuse existing — no new actor type. GENESIS = user_type enum value |
| Execution substrate | Reuse existing — no new WF topology |
| Authority classes | Reuse ENDUSER + SYSTEM — no new authority class |
| Identity dependency | wallet → identity (actor_id resolution); validator → identity (actor existence check) — cross-subdomain reads, both EXISTING |
| Bootstrap dependency | system_wallets seed DEPENDS ON genesis_actor seed (wallet references actor_id) — load order: genesis_actor first |
| Storage topology | Enrichment of existing entity stores — no new stores required; see Section 5 |

**Cross-subdomain writes are forbidden.** identity does not write to wallet; wallet does not write to transaction; consensus_pos does not write to wallet. The reconciliation workflow (next CR) will update wallet balances — that capability is owned by the wallet subdomain and invoked by the consensus orchestration WF.

---

## 5. Storage Governance Requirements

The existing `STRUCTURE_BLOCKCHAIN_STORAGE_V0` declares entity stores for all four subdomains. No new stores are required by this CR — all changes are enrichments to the entity schemas of existing stores.

**Storage obligations by subdomain:**

| Store | Subdomain | Change |
|-------|-----------|--------|
| identity/registry/actors.json | identity | Schema enrichment — add user_type, status, kyc_verified, currency_preference, language, last_modified fields |
| wallet/state/wallets.json | wallet | Schema enrichment — add wallet_type (enum), balance, nonce, address, currency, network, last_tx_at |
| transaction/mempool/*.json | transaction | Schema enrichment — add tx_type, from_address (nullable), to_address (nullable), amount (replaces value), currency; remove mnemonic, data |
| consensus_pos/validators.json | consensus_pos | Schema enrichment — add status (9-state enum), epoch fields, slashed, balance, actor_id; remove node_name, stake, enrollment_status |
| consensus_pos/blocks.json | consensus_pos | Schema enrichment — add slot, epoch, block_type, proposer_index, base_fee_per_gas, total_fees, transaction_count, transactions, status, is_canonical, justified_epoch, finalized_epoch |

**New seed files (not entity stores — bootstrap-only):**

| File | Subdomain | Purpose |
|------|-----------|---------|
| seeds/genesis_actor.json | identity | GENESIS actor bootstrap record |
| seeds/system_wallets.json | wallet | MINT (1,000,000 BACHI), BURN (0), POOL (0) bootstrap records |

Seed files are read-only bootstrap inputs. They are loaded into entity stores at bootstrap time. They are not written by any workflow and are not governed as runtime data.

---

## 6. Cross-Subdomain Dependency Declaration

| Dependency | Direction | Existing PPS Artifact | Status |
|------------|-----------|----------------------|--------|
| Actor existence check (validator registration) | consensus_pos → identity | `blockchain::CC_CHECK_ACTOR_EXISTS_V0` | SATISFIED — reuse |
| Actor identity resolution (wallet creation) | wallet → identity | `blockchain::CC_RESOLVE_ACTOR_ID_V0` | SATISFIED — verify available |
| Wallet lookup for from_address derivation (transaction submission) | transaction → wallet | Existing CC in transaction WF | SATISFIED — verify tx WF resolves from_address from wallet_id |
| genesis_actor seed → system_wallets seed | identity → wallet (bootstrap order) | N/A — seed load order | DECLARED — genesis_actor.json must load before system_wallets.json |

No new cross-subdomain dependencies are introduced by this CR. All dependencies are existing reuse patterns.

---

## 7. Governance Boundary Rules

1. **Enum purity** — wallet_type, user_type, tx_type, validator status, block status are governed controlled vocabularies. Free string values (e.g., "standard", "ETH", "ACTIVE"/"INACTIVE"/"EXCLUDED") are governed defects. No field governed by enum may accept values outside its declared enum.

2. **GENESIS seed bypass** — The GENESIS actor and system wallets are not registered through governed workflows. They are bootstrap seed records. This bypass is explicitly permitted for bootstrap records only. No other entity class may use this bypass.

3. **Total supply conservation** — MINT.balance at bootstrap = 1,000,000 BACHI. All user wallet balances are funded by transfer from MINT. BURN absorbs permanently removed supply. POOL holds liquidity. The sum of all wallet balances = initial supply at all times. Violations of this invariant are governance violations.

4. **Validator status payload-driven only** — Status transitions for the ETH2 validator lifecycle are payload-driven in this CR. The governance layer does not enforce ETH2 lifecycle ordering (e.g., cannot transition from PENDING_INITIALIZED to ACTIVE_ONGOING without passing through PENDING_QUEUED). Lifecycle enforcement is deferred to a future CR.

5. **Block entity write is CC-owned** — `CC_FORM_BLOCK_V0` is the sole authority for writing block records. No other CC may write a block record. The block entity schema declared in this CR is the complete and authoritative schema for all block records.

6. **No tx_type free string** — CC_VALIDATE_TRANSACTION_POLICY_V0 and CC_PERSIST_TRANSACTION_TO_MEMPOOL_V0 must read tx_type from payload. Hardcoded type values are a governed defect. After this CR, any CC that hardcodes a transaction type is a governance violation.

7. **Asymmetric address nullability** — from_address and to_address nullability is governed by tx_type. The governance table is authoritative:

   | tx_type | from_address | to_address |
   |---------|-------------|------------|
   | TRANSFER | REQUIRED | REQUIRED |
   | MINT | NULL (system) | REQUIRED |
   | BURN | REQUIRED | NULL (protocol) |
   | POOL | REQUIRED | REQUIRED |
   | STAKE | REQUIRED | REQUIRED |
   | UNSTAKE | REQUIRED | REQUIRED |
   | REWARD | NULL (system) | REQUIRED |
   | SLASH | REQUIRED | NULL (protocol) |

8. **Append-only event journal** — All 5 new events (EV_BLOCK_ATTESTED_V0, EV_BLOCK_FINALIZED_V0, EV_BLOCK_COMMITTED_V0, EV_TX_FINALIZED_V0, EV_BALANCE_RECONCILED_V0) are governed artifacts. When emitted by next CR's workflows, they append to the relevant subdomain event journal. Events are never modified or deleted.

9. **No ambient actor_id** — actor_id on the validator record (direct reference) is a convenience for single-node lookup. It does not grant identity authority to consensus_pos. consensus_pos does not own or modify identity records.

---

## 8. PPS Artifacts Requiring Action

| Artifact | Current Status | Action |
|----------|---------------|--------|
| `blockchain::IN_ACTOR_REGISTERED_V0` | EXISTS — 3 fields | UPDATE — add user_type, kyc_verified, currency_preference, language |
| `blockchain::CC_WRITE_ACTOR_RECORD_V0` | EXISTS | UPDATE — persist new fields; assign status=PENDING at write time |
| `blockchain::IN_WALLET_CREATED_V0` | EXISTS — unstructured wallet_config | UPDATE — governed wallet_type enum; add opening_balance, currency, network; restructure |
| `blockchain::CC_CREATE_WALLET_RECORD_V0` | EXISTS | UPDATE — persist full enriched entity (balance, nonce, address, last_tx_at) |
| `blockchain::IN_TRANSACTION_SUBMITTED_V0` | EXISTS — no tx_type, mnemonic present | UPDATE — add tx_type enum, amount (BACHI), optional to_address; remove mnemonic, data; fix summary |
| `blockchain::CC_VALIDATE_TRANSACTION_POLICY_V0` | EXISTS — tx_type hardcoded "ETH" | FIX — read tx_type from payload; enforce type-specific address nullability rules |
| `blockchain::CC_PERSIST_TRANSACTION_TO_MEMPOOL_V0` | EXISTS — tx_type hardcoded "ETH" | FIX — write tx_type from payload into persisted record |
| `blockchain::IN_VALIDATOR_REGISTERED_V0` | EXISTS — 3-state enrollment_status, node_name, stake | UPDATE — 9-state status enum; add epoch fields, slashed, balance; remove node_name, stake, enrollment_status |
| `blockchain::CC_WRITE_VALIDATOR_RECORD_V0` | EXISTS | UPDATE — persist enriched entity with validator_index (JIT sequential), new fields |
| `blockchain::CC_FORM_BLOCK_V0` | EXISTS — minimal block record | UPDATE — write full enriched block entity (slot, epoch, block_type, proposer_index, finality fields, status=PROPOSED) |
| `seeds/register_validator_payload.json` | EXISTS — node_name, stake, enrollment_status | UPDATE — remove redundant fields; add status (PENDING_INITIALIZED), slashed (false), epoch fields |
| `seeds/genesis_actor.json` | MISSING | NEW — GENESIS actor seed record |
| `seeds/system_wallets.json` | MISSING | NEW — MINT/BURN/POOL seed records |
| `blockchain::EV_BLOCK_ATTESTED_V0` | MISSING | NEW — declare event artifact |
| `blockchain::EV_BLOCK_FINALIZED_V0` | MISSING | NEW — declare event artifact |
| `blockchain::EV_BLOCK_COMMITTED_V0` | MISSING | NEW — declare event artifact |
| `blockchain::EV_TX_FINALIZED_V0` | MISSING | NEW — declare event artifact |
| `blockchain::EV_BALANCE_RECONCILED_V0` | MISSING | NEW — declare event artifact |
| `blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0` | EXISTS | REVIEW — verify entity_store schema annotations cover enriched field sets; no new stores expected |

**Count:** 8 UPDATE, 2 FIX, 3 seed actions (2 NEW + 1 UPDATE), 5 NEW events, 1 REVIEW. **Total: 19 artifact actions.**

---

## 9. Governance Outcome

The following capabilities require protocol realization. Design Intent (Stage 6b) determines which artifact family each maps to, assigns FQDN codes, and specifies implementation contracts.

**identity subdomain:**
- IN_ACTOR_REGISTERED_V0 — enriched schema (user_type, kyc_verified, currency_preference, language)
- CC_WRITE_ACTOR_RECORD_V0 — persist enriched actor entity with PENDING status at write

**wallet subdomain:**
- IN_WALLET_CREATED_V0 — governed wallet_type enum; opening_balance; currency; network
- CC_CREATE_WALLET_RECORD_V0 — persist enriched wallet entity (balance, nonce, address, last_tx_at)

**transaction subdomain:**
- IN_TRANSACTION_SUBMITTED_V0 — tx_type enum; amount (BACHI); conditional to_address
- CC_VALIDATE_TRANSACTION_POLICY_V0 — payload-driven tx_type; type-specific validation rules
- CC_PERSIST_TRANSACTION_TO_MEMPOOL_V0 — payload-driven tx_type written to mempool record

**consensus_pos subdomain:**
- IN_VALIDATOR_REGISTERED_V0 — 9-state status enum; epoch fields; slashed; balance; remove redundant fields
- CC_WRITE_VALIDATOR_RECORD_V0 — persist enriched validator entity with validator_index (JIT)
- CC_FORM_BLOCK_V0 — write full enriched block entity

**events (cross-subdomain declarations):**
- EV_BLOCK_ATTESTED_V0, EV_BLOCK_FINALIZED_V0, EV_BLOCK_COMMITTED_V0 — consensus_pos ownership
- EV_TX_FINALIZED_V0 — transaction subdomain ownership
- EV_BALANCE_RECONCILED_V0 — wallet subdomain ownership

**seeds (bootstrap — not protocol artifacts):**
- seeds/genesis_actor.json — identity bootstrap
- seeds/system_wallets.json — wallet bootstrap
- seeds/register_validator_payload.json — updated test seed

---

## 10. Governance Decision Gate

**Presenting for Analyst approval:**

1. Domain `blockchain` — all 4 subdomains extended; no new subdomain declared
2. GENESIS is a `user_type` enum value (9th value), not a new authority class or actor type
3. GENESIS actor and system wallets are seed bootstrap records, not workflow-registered entities — bootstrap bypass is explicitly permitted for this purpose only
4. 1,000,000 BACHI initial supply is a bootstrap invariant; total supply conservation is a governance boundary rule
5. tx_type defect in CC_VALIDATE_TRANSACTION_POLICY_V0 and CC_PERSIST_TRANSACTION_TO_MEMPOOL_V0 is a CC-level payload defect — topology is correct; no WF change required
6. IN_BLOCK_PROPOSED_V0 is unchanged — it is a correct round trigger; block entity enrichment is a CC_FORM_BLOCK_V0 obligation
7. Validator status transitions are payload-driven only in this CR — 9-state enum declared; no lifecycle enforcement workflow in scope
8. Asymmetric from/to address nullability on Transaction is governed by tx_type — governance table in Section 7 is authoritative
9. 5 new events declared in this CR; emission infrastructure (emitter workflows) deferred to consensus finalization CR
10. Cross-subdomain writes are forbidden — no subdomain writes to another subdomain's stores
11. 4 missing consensus finalization workflows (WF_ATTEST_BLOCK_V0, WF_FINALIZE_BLOCK_V0, WF_COMMIT_BLOCK_V0, WF_RECONCILE_BALANCES_V0) are explicitly deferred to next CR
12. No new actor types, no new authority classes, no new domain topology

*Analyst approval of this document gates entry into Stage 6b — Design Intent.*

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 0 — Classification | 1_change_request_data_model_v0.md | COMPLETE |
| Stage 1 — Input Elicitation | 1_input_elicitation_data_model_v0.md | COMPLETE |
| Stage 2 — Domain Model Discovery | 2_domain_model_data_model_v0.md | COMPLETE — KISS revision |
| Stage 3 — Analysis Loop | 3_analysis_loop_data_model_v0.md | COMPLETE — SATURATED |
| Stage 4 — Business Model | 4_business_model_data_model_v0.md | COMPLETE |
| Stage 5 — Business Intent | 5_business_intent_data_model_v0.md | COMPLETE |
| Stage 6 — Governance Intent | This document | PENDING APPROVAL |
| Stage 6b — Design Intent | Pending | — |
| Stage 7 — Authoring Plan | Pending | — |

---

## Amendments

**Status:** Post-authoring retroactive fix — Option B (amendment section added; approved content above unchanged)
**Source of truth:** 8_authoring_manifest_data_model_v0.md (Sections 1, 2, 7) and 6b_design_intent_data_model_v0.md (Design Pivot Record)

The following items became inaccurate after the Design Pivot was approved during Stage 6b review. The GI was approved before the pivot; the governance boundary decisions (subdomain placement, authority classes, cross-subdomain write rules, token economy invariant) remain correct and are not amended.

---

### Amendment A — WF_SUBMIT_TRANSACTION_V0 was retired, not preserved

**GI location:** Section 3 (transaction subdomain defect note) — "The WF topology (WF_SUBMIT_TRANSACTION_V0) is correct. Two CC implementations hardcode 'ETH' instead of reading tx_type from payload — these are implementation defects in CC_VALIDATE_TRANSACTION_POLICY_V0 and CC_PERSIST_TRANSACTION_TO_MEMPOOL_V0. No topology change is required."
**GI location:** Section 10 (Governance Decision Gate item 5) — "tx_type defect in CC_VALIDATE_TRANSACTION_POLICY_V0 and CC_PERSIST_TRANSACTION_TO_MEMPOOL_V0 is a CC-level payload defect — topology is correct; no WF change required"

**As-built:** `WF_SUBMIT_TRANSACTION_V0` was RETIRED. The unified topology was replaced by 8 typed transaction workflows (WF_TRANSFER_V0, WF_STAKE_V0, WF_UNSTAKE_V0, WF_MINT_V0, WF_BURN_V0, WF_POOL_V0, WF_REWARD_V0, WF_SLASH_V0).

**Why:** The Design Pivot approved during Stage 6b determined that a unified transaction WF cannot express type-specific policy gates at compile time without runtime branching — a topology violation. The tx_type defect diagnosis was correct, but the repair required a topology redesign, not just CC-level patching.

**Governance impact:** The governance boundary decisions (transaction subdomain ownership, ENDUSER + SYSTEM authority classes, cross-subdomain write prohibition) are unchanged. The architectural realization changed: 8 typed WFs replaced 1 unified WF. This is a topology decision, not a governance boundary decision.

---

### Amendment B — Transaction artifact scope was much larger than Section 8 declared

**GI location:** Section 8 (PPS Artifacts Requiring Action) — transaction domain rows:
- `IN_TRANSACTION_SUBMITTED_V0` — UPDATE
- `CC_VALIDATE_TRANSACTION_POLICY_V0` — FIX
- `CC_PERSIST_TRANSACTION_TO_MEMPOOL_V0` — FIX

**As-built (from Authoring Mandate and Manifest):**

| Artifact | Action | Note |
|----------|--------|------|
| `WF_SUBMIT_TRANSACTION_V0` | RETIRE | replaced by 8 typed WFs |
| `IN_TRANSACTION_SUBMITTED_V0` | RETIRE | replaced by 8 typed INs |
| `RB_SUBMIT_TRANSACTION_V0` | RETIRE | replaced by 8 typed RBs |
| `CC_VALIDATE_TX_STRUCTURE_V0` | RETIRE | structural validation absorbed into typed INs |
| `CC_VALIDATE_TX_POLICY_V0` | RETIRE | replaced by 8 typed policy CCs |
| `CC_BUILD_ETH_TX_V0` | RETIRE | ETH pipeline — replaced by BACHI-native |
| `CC_SIGN_TRANSACTION_V0` | RETIRE | ETH pipeline |
| `CC_HASH_TRANSACTION_V0` | RETIRE | ETH pipeline — replaced by CC_GENERATE_TX_ID_V0 |
| `CC_PERSIST_MEMPOOL_TX_V0` | UPDATE | renamed; now tx_type-aware |
| 8 × `IN_TRANSFER/STAKE/UNSTAKE/MINT/BURN/POOL/REWARD/SLASH_V0` | NEW | typed intent per tx_type |
| 8 × `RB_TRANSFER/STAKE/.../SLASH_V0` | NEW | typed runtime bindings |
| 8 × `CC_VALIDATE_<TYPE>_POLICY_V0` | NEW | typed policy CCs |
| 8 × `WF_TRANSFER/STAKE/.../SLASH_V0` | NEW | typed transaction workflows |
| `CC_GENERATE_TX_ID_V0` | NEW (unplanned) | BACHI-native tx_id/tx_hash generation |

**Total transaction subdomain artifact actions: 8 retirements + 1 update + 33 new.** Section 8 declared 3 actions (1 update + 2 fix).

---

### Amendment C — Governance boundary rule #6 names retired artifacts

**GI location:** Section 7 (Governance Boundary Rules) — Rule #6: "CC_VALIDATE_TRANSACTION_POLICY_V0 and CC_PERSIST_TRANSACTION_TO_MEMPOOL_V0 must read tx_type from payload. Hardcoded type values are a governed defect."

**As-built:** Both artifacts named in rule #6 were RETIRED. The governance rule itself is correct and carries forward — but it now applies to the 8 typed `CC_VALIDATE_<TYPE>_POLICY_V0` artifacts and the updated `CC_PERSIST_MEMPOOL_TX_V0`.

**Corrected rule (intent preserved, artifact names updated):** All capability contracts in the transaction subdomain that read or write transaction type must derive `tx_type` from the governed typed intent payload, not from hardcoded constants. No CC may assume a transaction type by name.

---

### Amendment D — Section 9 transaction outcome lists stale artifacts

**GI location:** Section 9 (Governance Outcome — transaction subdomain) — lists:
- `IN_TRANSACTION_SUBMITTED_V0` — tx_type enum; amount (BACHI); conditional to_address
- `CC_VALIDATE_TRANSACTION_POLICY_V0` — payload-driven tx_type; type-specific validation rules
- `CC_PERSIST_TRANSACTION_TO_MEMPOOL_V0` — payload-driven tx_type written to mempool record

**As-built:** All three are RETIRED. The transaction subdomain governance outcome is realized by 8 typed WF families (see Amendment B table). Each typed WF carries: typed IN_ (admission) + typed policy CC (validation) + CC_GENERATE_TX_ID_V0 (BACHI-native identity) + CC_PERSIST_MEMPOOL_TX_V0 (updated, reused) + CC_APPEND_TX_EVENT_V0 (event emission).

# Authoring Manifest: blockchain / consensus_pos
**Domain:** blockchain  
**Subdomain:** consensus_pos  
**Version:** V0  
**Status:** APPROVED  
**Pipeline Stage:** Stage 8 — Authoring Manifest  
**Produced by:** v0.5.0 SDLC authoring pipeline  
**Produced after:** Protocol artifact authoring and testing complete  

> **Wave structure:** This manifest covers two authoring waves within the same CR.  
> Wave 1 — WF_PROPOSE_BLOCK_V0 and all 16 mandated steps (approved prior session).  
> Wave 2 — WF_RUN_CONSENSUS_SLOTS_V0 consensus orchestration layer (approved this session).

---

## 1. Approved Deviations

Deviations from Design Intent that were approved during artifact authoring. Each deviation must reference the DI artifact it departs from and state the governance rationale.

| Artifact | DI Reference | Deviation | Rationale |
|----------|-------------|-----------|-----------|
| WF_PROPOSE_BLOCK_V0 | Authoring Mandate Wave 1 deferred IN_BLOCK_PROPOSED_V0 | IN_BLOCK_PROPOSED_V0 authored in Wave 5 alongside WF — not Wave 1 | ASSERT_IN_WORKFLOW_BINDING_V0 hard-fails if WF referenced by IN does not exist; IN must be authored after WF |
| RB_PROPOSE_BLOCK_V0 | Authoring Mandate Wave 6 | RB authored in Wave 5 alongside WF — not Wave 6 | S2_CANONICALIZE resolves WF→RB FQDN references; RB must exist before WF can pass compilation; Wave 6 collapsed into Wave 5 |
| IN_BLOCK_PROPOSED_V0 | Authoring Mandate — timestamp not listed as required input | `timestamp` field added to intent inputs | CC_FORM_BLOCK_V0, CC_SKIP_ROUND_V0, and CC_RECORD_CONSENSUS_ROUND_V0 all require a consistent round timestamp; sourcing it once at intent admission eliminates per-CC clock skew |
| WF_RUN_CONSENSUS_SLOTS_V0, CC_EXECUTE_SLOT_SEQUENCE_V0, CC_VERIFY_SLOT_RESULTS_V0, IN_CONSENSUS_SLOTS_V0, RB_RUN_CONSENSUS_SLOTS_V0 | Authoring Mandate — 16 steps ending at WF_PROPOSE_BLOCK_V0 | Five additional artifacts authored beyond mandate scope (Wave 2) | WF_PROPOSE_BLOCK_V0 is a sub-WF invoked per slot; a governing orchestration layer is required to drive the slot schedule, dispatch typed transactions, and assert post-slot correctness. Without this layer the CR has no executable entry point for consensus. Wave 2 extends the mandate in-authoring — no new CR required as all artifacts are within the consensus_pos governance boundary |

---

## 2. Architectural Discoveries

Findings that emerged during artifact authoring revealing that the architecture itself needed correction or was incomplete.

| Discovery | Impact | Disposition |
|-----------|--------|-------------|
| CS_APPENDONLY_JSONL_V0 was path-centric (config["path"]) while the rest of the architecture had migrated to entity-based store resolution via __pgs_store_entity__ + storage_structure_artifact | WF_PROPOSE_BLOCK_V0 is the first WF requiring CS_APPENDONLY_JSONL_V0 across multiple stores (CONSENSUS_ROUNDS, CONSENSUS_EVENTS, BLOCK_EVENTS); the single-path pattern cannot serve multi-store workflows | Full capability migration: executor.py rewritten to entity-based resolution (mirrors CS_MUTABLE_JSON_V0); all RBs updated to `policy: {}`; all affected CCs given `store:` declarations; STRUCTURE artifacts updated with new entity stores; assertion handler updated to exclude CS_APPENDONLY_JSONL_V0 from file-path policy check |
| CC_FORM_BLOCK_V0 (Wave 1) assembled block records without a `status` field; CC_VERIFY_SLOT_RESULTS_V0 (Wave 2) filters the BLOCKS store by `status: PROPOSED` using CT_PURE_FILTER_RECORDS_V0 — the filter returned nothing → VIOLATION on every consensus run | WF_RUN_CONSENSUS_SLOTS_V0 could not reach SUCCESS; CC_VERIFY_SLOT_RESULTS_V0 always violated | `status: PROPOSED` added to CC_FORM_BLOCK_V0 `assemble_block_record` fields map; block records now carry explicit status at write time; CC_VERIFY_SLOT_RESULTS_V0 filter succeeds |

---

## 2b. Implementation Discoveries

Findings that emerged during artifact authoring or runtime execution revealing that an existing, correct architecture had not yet been fully adopted or implemented by all consumers.

| Discovery | Impact | Disposition |
|-----------|--------|-------------|
| ai_governance domain had not yet migrated CS_APPENDONLY_JSONL_V0 CC steps to entity-based resolution — the architecture was correct, but adoption was incomplete | CC_RECORD_GOVERNED_ACTION_V0, CC_RECORD_DENIED_ACTION_V0 (agent_governance), and CC_APPEND_AUDIT_EVENT_V0 (ai_licensing) lacked `store:` declarations; STRUCTURE_AGENT_GOVERNANCE_STORAGE_V0 lacked GOVERNANCE_AUDIT and LICENSE_AUDIT entity stores | ai_governance artifacts updated in the same migration pass; no separate CR required as the fix is a capability alignment, not a protocol change |
| CS_MUTABLE_JSON_V0 `LIST` op was declared by the dispatcher contract but not implemented in the engine — `getattr(engine, "list", None)` returned None → BACKEND_ERROR | WF_PROPOSE_BLOCK_V0 could not pass CC_QUERY_ELIGIBLE_VALIDATORS_V0 (first query-oriented workflow in the domain); blocked end-to-end execution | Added `list()` method to `MutableJsonEngine` returning both `records` (full values) and `keys` (store keys) with `NOT_FOUND` on empty store; dispatcher contract now fulfilled |
| CC_VALIDATE_POOL_POLICY_V0 dispatch binding uses literal key `"POOL"` to look up the pool wallet (not the wallet_id `WAL_c97b4e66dc1d4a16`) — the WALLET store had no `"POOL"` alias entry | WF_RUN_CONSENSUS_SLOTS_V0 POOL transaction always raised BACKEND_ERROR (key not found); pool policy validation was unreachable | `"POOL"` alias entry added to seeds/wallets.json pointing to the pool wallet record; seeds/wallets.json wired into clean_outputs_dir.sh as a restored seed alongside validators.json |
| System wallets (MINT, BURN, POOL) were not restored on workspace clean — clean_outputs_dir.sh only restored license_facts.json and validators.json | Any clean run of consensus WFs would fail immediately: MINT wallet not found → BACKEND_ERROR on first tx | seeds/wallets.json created (CS_MUTABLE_JSON_V0 dict format; includes MINT, BURN, POOL system wallets + POOL alias + genesis test wallet); wired into clean_outputs_dir.sh restore sequence |

---

## 2c. CT Vocabulary Discoveries

Findings that emerged during runtime execution revealing that the transform vocabulary lacked an atom needed for a declared CC pipeline step.

| Discovery | Impact | Disposition |
|-----------|--------|-------------|
| `CT_PURE_EXTRACT_V0` was used in CC_QUERY_ELIGIBLE_VALIDATORS_V0 as a filter step (array records → filtered subset by field criteria), but CT_PURE_EXTRACT_V0 is a scalar path extractor (from/path/type) — semantically wrong CT for the declared pipeline intent | CC filter_eligible step always raised VIOLATION regardless of validator data; no eligible validator set could be produced | New atom CT_PURE_FILTER_RECORDS_V0 authored and registered: accepts `source` (array) + `filter` (field criteria dict, supporting exact-value and `present` existence checks), returns `extracted` array; ASSERT_CT_SURFACE_CLOSED_V0 updated; CC updated to reference the correct CT |

---

## 2d. Surface Alignment Discoveries

Findings that emerged during runtime execution revealing that a CC's declared result surface did not match the result status actually produced by its CS step — a class of gap not yet detected by the compiler.

| Discovery | Impact | Disposition |
|-----------|--------|-------------|
| CC_QUERY_PENDING_TRANSACTIONS_V0 declared `EMPTY` as its no-transactions result status, but CS_MUTABLE_JSON_V0 `LIST` returns `NOT_FOUND` when the store is empty — the WF routed `EMPTY → CC_SKIP_ROUND_V0`, which was unreachable; `NOT_FOUND` had no routing rule and caused WF exit without round record | WF_PROPOSE_BLOCK_V0 exited with unrouted NOT_FOUND instead of executing CC_SKIP_ROUND_V0; round skip path was dead | CC_QUERY_PENDING_TRANSACTIONS_V0 updated: EMPTY → NOT_FOUND throughout result_surface, allowed list, and on_result; WF_PROPOSE_BLOCK_V0 routing updated: `EMPTY: CC_SKIP_ROUND_V0 → NOT_FOUND: CC_SKIP_ROUND_V0`; compiler opportunity identified (see Section 6) |
| Trace directory path for WF_RUN_CONSENSUS_SLOTS_V0 was written to `traces/blockchain/WF_RUN_CONSENSUS_SLOTS_V0/` rather than `traces/blockchain/consensus_pos/` — the runtime resolves subdomain from WF artifact name, not from the `subdomain:` field | Traces for consensus WFs land in a non-canonical directory; CLAUDE.md declares the canonical path as `traces/<domain>/<subdomain>/` | Cosmetic only — no data loss, no execution impact. Logged as Future CR candidate for runtime trace routing fix (see Section 6) |

---

## 3. Unexpected Constraints

Constraints encountered during authoring that blocked, redirected, or modified the implementation from what Design Intent specified.

| Constraint | Affected Artifacts | Resolution |
|------------|-------------------|------------|
| ASSERT_IN_WORKFLOW_BINDING_V0 requires referenced WF to exist at compile time | IN_BLOCK_PROPOSED_V0 could not be authored before WF_PROPOSE_BLOCK_V0 was compiled | Wave ordering adjusted: WF authored and compiled first; IN authored immediately after in same wave |
| S2_CANONICALIZE resolves WF→RB FQDN at compile time (not a forward-reference-tolerant phase) | WF_PROPOSE_BLOCK_V0 failed S2 with E104_INVALID_FQDN until RB_PROPOSE_BLOCK_V0 was authored | RB authored and compiled before WF recompile; Wave 6 collapsed into Wave 5 |
| CS_WORKFLOW_LOOP_V0 EXECUTE_SEQUENCE dispatch is not idempotent — same payload produces same deterministic TX hashes → ALREADY_EXISTS on repeat run | WF_RUN_CONSENSUS_SLOTS_V0 Phase 3 returns VIOLATION on repeat execution without workspace clean | By design: consensus requires clean state between slot runs. E2E orchestrator uses `--clean` flag as standard entry point; idempotency is scoped to Identity (Phase 1) and Wallet (Phase 2) phases only |

---

## 4. Governance Findings

New governance knowledge produced by this CR — boundary decisions, ownership clarifications, or protocol rules discovered through implementation.

| Finding | Type | Governance Implication |
|---------|------|----------------------|
| CC_SELECT_PROPOSER_V0 (NOT_FOUND path from CC_QUERY_ELIGIBLE_VALIDATORS_V0) must route to EXIT, not to CC_SKIP_ROUND_V0 — no eligible validators is a distinct condition from no pending transactions | Protocol routing rule | When no eligible validators exist, no proposer was selected, so CC_SKIP_ROUND_V0 (which requires a valid proposer_id) must not be invoked; the WF exits without writing a round record |
| CS_APPENDONLY_JSONL_V0 is now a fully entity-based capability (identical resolution pattern to CS_MUTABLE_JSON_V0); it no longer uses policy.path | Capability governance | ASSERT_RB_BINDING_POLICY_CONFORMANCE_V0 updated to reflect this; all future RBs using CS_APPENDONLY_JSONL_V0 declare `policy: {}` |
| System wallets (MINT, BURN, POOL) are genesis-level protocol entities — they must be seeded before any consensus WF can execute and must be restored on every workspace clean | Operational governance | seeds/wallets.json is the canonical source of system wallet state; restoration is part of workspace bootstrap; system wallet IDs are stable protocol constants (WAL_67ac742cc0930491 MINT, WAL_28344959edf3c402 BURN, WAL_c97b4e66dc1d4a16 POOL) |
| `status` is a required field on block records — CC_FORM_BLOCK_V0 must write it; CC_VERIFY_SLOT_RESULTS_V0 asserts it; the field value at formation time is always `PROPOSED` | Block record schema governance | All future CCs that read or write BLOCKS store must treat `status` as a required field; block finalization (future CR) transitions status from PROPOSED to a canonical final state |
| Transactions in the PENDING state represent mempool submissions — balance settlement, nonce finalization, and status transition to CONFIRMED are finalization concerns explicitly deferred to the block finalization CR | Protocol boundary | No CC within the consensus_propose scope modifies wallet balances or marks transactions CONFIRMED; this is not an omission but a declared protocol boundary |

---

## 5. Amendments to Intent

Changes required to any prior stage artifact (BI, GI, DI) based on what was learned during authoring. These amendments are recorded here; the prior stage documents are updated separately if needed.

| Stage Artifact | Amendment | Reason |
|----------------|-----------|--------|
| Authoring Mandate — Wave ordering | Wave 6 (RB) collapsed into Wave 5 | S2_CANONICALIZE constraint requires RB to exist before WF compilation can succeed |
| Authoring Mandate — Wave 1 | IN_BLOCK_PROPOSED_V0 deferred to Wave 5 | ASSERT_IN_WORKFLOW_BINDING_V0 constraint; IN cannot precede its WF |
| Authoring Mandate — Scope | Wave 2 (5 artifacts) added beyond mandated 16 steps | Consensus orchestration layer required for CR to have an executable entry point; WF_PROPOSE_BLOCK_V0 alone is a sub-WF invoked by a higher orchestrator |
| CC_FORM_BLOCK_V0 — Step 9 field list | `status: PROPOSED` added to assemble_block_record | Required by CC_VERIFY_SLOT_RESULTS_V0 filter; block records must carry explicit status at formation time |

---

## 6. Future CR Candidates

Capabilities, constraints, or concerns that surfaced during this CR but are explicitly deferred. Each entry is a candidate input for a future Change Request.

| Concept | Domain / Subdomain | Priority | Notes |
|---------|-------------------|----------|-------|
| Authoring Mandate wave ordering rules should explicitly document the IN→WF and WF→RB compile-time sequencing constraints to prevent future wave deferral surprises | pgs_change_mgmt / methodology | MEDIUM | Would eliminate per-CR authoring manifest deviation entries for known structural constraints |
| Compiler surface alignment check: an assertion phase should verify that each CC's declared result_surface entries are producible by its CS step (e.g., CS_MUTABLE_JSON_V0 LIST returns NOT_FOUND on empty — any CC declaring EMPTY as a list-empty result status is a static gap detectable at compile time) | pgs_compiler / assertions | HIGH | Surface Alignment Discovery 2d was only detectable at runtime; this class of gap should be compiler-caught. Precedent: CC_QUERY_PENDING_TRANSACTIONS_V0 EMPTY vs NOT_FOUND routing mismatch caused dead WF path that executed silently until end-to-end test |
| Block finalization: WF_FINALIZE_BLOCK_V0 — settle wallet balances, transition transactions from PENDING → CONFIRMED, mark block is_canonical=True | blockchain / block | HIGH | Currently all transactions remain PENDING and all wallet balances are unchanged after consensus; finalization is a declared protocol boundary of this CR, not an omission |
| Runtime trace subdomain routing: traces should be written to `traces/<domain>/<subdomain>/` using the `subdomain:` field declared in the WF artifact JSON, not derived from the WF code | pgs_runtime | LOW | Current behavior uses WF name as subdomain folder (e.g., `blockchain/WF_RUN_CONSENSUS_SLOTS_V0/`); correct canonical path is `blockchain/consensus_pos/`; cosmetic but inconsistent with CLAUDE.md declared structure |
| Wallet balance settlement: CS_MUTABLE_JSON_V0 UPDATE op for atomic balance mutation | blockchain / wallet | HIGH | Prerequisite for WF_FINALIZE_BLOCK_V0; CS_MUTABLE_JSON_V0 currently supports READ/WRITE/LIST; UPDATE (delta mutation without full record overwrite) needed for safe balance operations |

---

## 7. As-Designed vs. As-Built Reconciliation

Summary delta between Design Intent (as-designed) and implemented artifacts (as-built).

| Concern | As-Designed | As-Built | Delta |
|---------|-------------|----------|-------|
| Wave sequencing | WF (Wave 5), IN (Wave 1), RB (Wave 6) | WF + IN + RB all in Wave 5 | Compile-time FQDN resolution forces WF→RB and WF→IN ordering constraints |
| timestamp in IN_BLOCK_PROPOSED_V0 | Not specified in mandate inputs | Required field (ISO 8601) | Downstream CCs require consistent round timestamp; sourced at admission |
| CS_APPENDONLY_JSONL_V0 policy | Not specified in mandate | `policy: {}` with entity-based store resolution | Capability migration from path-centric to entity-based pattern |
| CR scope | 16 steps (Steps 1–16, ending at RB_PROPOSE_BLOCK_V0) | 21 steps (Steps 1–16 + Wave 2: WF_RUN_CONSENSUS_SLOTS_V0, CC_EXECUTE_SLOT_SEQUENCE_V0, CC_VERIFY_SLOT_RESULTS_V0, IN_CONSENSUS_SLOTS_V0, RB_RUN_CONSENSUS_SLOTS_V0) | Consensus orchestration layer required; all artifacts within governance boundary |
| CC_FORM_BLOCK_V0 block record fields | `{block_id, round_id, proposer_id, tx_ids, timestamp}` (mandate Step 9) | `{block_id, round_id, proposer_id, tx_ids, is_canonical, status, timestamp}` | `is_canonical` (pre-existing); `status: PROPOSED` added (required by CC_VERIFY_SLOT_RESULTS_V0 filter) |
| Wallet state post-consensus | Not specified | All wallets at seed balance (PENDING transactions; no settlement) | Balance settlement deferred to block finalization CR; PENDING is correct mempool state |
| System wallet seeding | Not in mandate | seeds/wallets.json (MINT/BURN/POOL + POOL alias + genesis test wallet) restored by clean_outputs_dir.sh | Genesis-level protocol entities must be pre-seeded; now governed via workspace bootstrap |

---

## 8. Governed Evolution Metrics

Cumulative metrics for the full consensus_pos CR (Wave 1 + Wave 2).

| Metric | Wave 1 | Wave 2 | Total |
|--------|--------|--------|-------|
| Mandated authoring actions | 16 | 5 (scope extension) | 21 |
| Completed authoring actions | 16 | 5 | 21 |
| Snapshot growth | +4 artifacts (70 → 74) | +5 artifacts (74 → 79) | +9 artifacts (70 → 79) |
| Architectural discoveries | 1 | 1 | 2 |
| Implementation discoveries | 2 | 2 | 4 |
| CT vocabulary discoveries | 1 | 0 | 1 |
| Surface alignment discoveries | 1 | 1 | 2 |
| Governance findings | 2 | 3 | 5 |
| Approved deviations | 3 | 1 | 4 |
| Conformance status | 73 / 73 PASS | 77 / 77 PASS | 77 / 77 PASS |
| Snapshot status | VALID | VALID | VALID |
| E2E test baseline | — | ALL PASSED (scripts/test_blockchain_e2e.py --clean) | ESTABLISHED |

**Discovery category note:** Implementation discoveries (2b) and Architectural discoveries (2) were identified during artifact authoring. CT Vocabulary discoveries (2c) and Surface Alignment discoveries (2d) are new categories surfaced by runtime execution — both classes were invisible to the compiler and only detectable through end-to-end WF execution. CT Vocabulary discoveries indicate vocabulary gaps (wrong semantic fit for declared pipeline intent); Surface Alignment discoveries indicate CS/CC contract mismatches (what a CS op actually returns vs. what a CC declares it returns).

---

## 9. Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 7 — Authoring Mandate | 7_authoring_mandate_consensus_pos_v0.md | COMPLETE |
| Wave 1 Protocol Artifacts | WF_PROPOSE_BLOCK_V0, IN_BLOCK_PROPOSED_V0, RB_PROPOSE_BLOCK_V0 | COMPLETE |
| Wave 1 Capability Migration | CS_APPENDONLY_JSONL_V0 executor, 7 RBs, 3 CCs, 1 STRUCTURE, 1 assertion handler | COMPLETE |
| Wave 1 CT Vocabulary | CT_PURE_FILTER_RECORDS_V0 authored, admitted, 4 conformance cases authored and passing | COMPLETE |
| Wave 1 Runtime Execution Testing | WF_PROPOSE_BLOCK_V0 end-to-end; skip-round path (NOT_FOUND → CC_SKIP_ROUND_V0 → SUCCESS) and block formation path (SUCCESS → CC_FORM_BLOCK_V0 → CC_RECORD_CONSENSUS_ROUND_V0 → SUCCESS, block BLK_48208f9428d64634 PROPOSED) both confirmed | COMPLETE |
| Wave 2 Protocol Artifacts | WF_RUN_CONSENSUS_SLOTS_V0, CC_EXECUTE_SLOT_SEQUENCE_V0, CC_VERIFY_SLOT_RESULTS_V0, IN_CONSENSUS_SLOTS_V0, RB_RUN_CONSENSUS_SLOTS_V0 | COMPLETE |
| Wave 2 Infrastructure | seeds/wallets.json (system wallet seed), clean_outputs_dir.sh (wallet restore wired), CC_FORM_BLOCK_V0 (status: PROPOSED field added) | COMPLETE |
| Wave 2 Runtime Execution Testing | WF_RUN_CONSENSUS_SLOTS_V0 end-to-end: 1 slot, 8 tx_types (MINT POOL REWARD TRANSFER STAKE UNSTAKE BURN SLASH), WF_PROPOSE_BLOCK_V0 invoked, CC_VERIFY_SLOT_RESULTS_V0 passes; 205 trace events, all 42 CCs completed; E2E orchestrator (scripts/test_blockchain_e2e.py) ALL PASSED — Identity → Wallet → Consensus; idempotency confirmed (Phase 1+2 no-op on repeat, Phase 3 VIOLATION on repeat by design) | COMPLETE |
| Stage 8 — Authoring Manifest | This document | APPROVED |
| Stage 9 — CR Closure | See Section 10 | COMPLETE |

---

## 10. CR Closure

**Closed by:** v0.5.0 SDLC authoring pipeline  
**Closed on:** 2026-06-05  
**Final snapshot:** 79 blockchain artifacts, 77/77 conformance PASS, VALID  

### Governance Artifacts Produced by This CR

| Artifact | Type | Scope |
|----------|------|-------|
| CT_PURE_FILTER_RECORDS_V0 | CT — new capability transform atom | capability_transforms domain; general-purpose filtered array extraction |
| CT_PURE_SELECT_PROPOSER_V0 | CT — new capability transform | blockchain::consensus_pos; deterministic proposer selection by modulo |
| CC_QUERY_ELIGIBLE_VALIDATORS_V0 | CC — new | blockchain::consensus_pos; validator eligibility query |
| CC_SELECT_PROPOSER_V0 | CC — new | blockchain::consensus_pos; proposer selection pipeline |
| CC_QUERY_PENDING_TRANSACTIONS_V0 | CC — new (cross-subdomain) | blockchain::transaction; mempool query owned by transaction subdomain |
| CC_FORM_BLOCK_V0 | CC — new | blockchain::block; block record formation + BLOCK_EVENTS append |
| CC_SKIP_ROUND_V0 | CC — new | blockchain::consensus_pos; round skip record + CONSENSUS_EVENTS append |
| CC_RECORD_CONSENSUS_ROUND_V0 | CC — new | blockchain::consensus_pos; PROPOSED round record write |
| CC_EXECUTE_SLOT_SEQUENCE_V0 | CC — new | blockchain::consensus_pos; CS_WORKFLOW_LOOP_V0 slot dispatch orchestrator |
| CC_VERIFY_SLOT_RESULTS_V0 | CC — new | blockchain::consensus_pos; post-slot block + tx assertion |
| WF_PROPOSE_BLOCK_V0 | WF — new | blockchain::consensus_pos; single-round block proposal governance workflow |
| WF_RUN_CONSENSUS_SLOTS_V0 | WF — new | blockchain::consensus_pos; top-level slot schedule orchestration workflow |
| IN_BLOCK_PROPOSED_V0 | IN — new | blockchain::consensus_pos; admission gate for WF_PROPOSE_BLOCK_V0 |
| IN_CONSENSUS_SLOTS_V0 | IN — new | blockchain::consensus_pos; admission gate for WF_RUN_CONSENSUS_SLOTS_V0 |
| RB_PROPOSE_BLOCK_V0 | RB — new | blockchain::consensus_pos; runtime binding for WF_PROPOSE_BLOCK_V0 |
| RB_RUN_CONSENSUS_SLOTS_V0 | RB — new | blockchain::consensus_pos; runtime binding for WF_RUN_CONSENSUS_SLOTS_V0 |
| STRUCTURE_BLOCKCHAIN_STORAGE_V0 | STRUCTURE — extended | Added CONSENSUS_ROUNDS, CONSENSUS_EVENTS, BLOCKS, BLOCK_EVENTS stores |
| seeds/wallets.json | Operational seed | System wallet genesis state (MINT, BURN, POOL + alias); workspace bootstrap |

### Methodology Lessons Carried Forward

| Lesson | Origin | Action |
|--------|--------|--------|
| CT vocabulary should be audited against CC pipeline intent before authoring — using the wrong CT (CT_PURE_EXTRACT_V0 for array filtering) only fails at runtime, not compile time | CT Vocabulary Discovery 2c | Add CT selection audit to Stage 7 authoring mandate checklist: for each CC step, confirm CT semantics match the declared pipeline intent |
| CS op result status must match CC declared result_surface — e.g., CS_MUTABLE_JSON_V0 LIST returns NOT_FOUND on empty, not EMPTY | Surface Alignment Discovery 2d | Add CS/CC surface alignment check to Stage 7 authoring mandate checklist: for each CC step using LIST/READ, verify the CC's result_surface matches what the CS op actually returns |
| System wallets and other genesis-level entities must be seeded before any dependent WF can execute; seeding belongs in workspace bootstrap, not in test setup | Implementation Discovery 2b (wallet seeding gap) | Any future CR that introduces new genesis-level entities (validators, wallets, actors) must declare a corresponding seeds/ entry and wire it into clean_outputs_dir.sh as part of the authoring mandate |
| Scope extension beyond mandate is legitimate when the extension is within the same governance boundary and required for the CR to have an executable entry point | Wave 2 scope extension | Authoring mandate template should include an explicit "scope extension gate" — if authoring reveals that the mandated artifacts are sub-WFs of an unspecified orchestrator, the orchestrator is in-scope for the same CR without a new CR |
| E2E regression baseline should be established at CR closure — a passing orchestrator run is the authoritative proof of correctness | Wave 2 E2E testing | scripts/test_blockchain_e2e.py --clean is the canonical regression command for the consensus_pos CR scope; future CRs that touch consensus_pos artifacts must re-run this baseline |

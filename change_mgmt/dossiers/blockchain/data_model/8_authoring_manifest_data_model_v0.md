# Authoring Manifest: blockchain / data_model
**Domain:** blockchain  
**Primary subdomain:** transaction  
**Additional subdomains:** identity, wallet, consensus_pos, block  
**Version:** V0  
**Status:** APPROVED  
**Pipeline Stage:** Stage 8 — Authoring Manifest  
**Produced by:** v0.5.0 SDLC authoring pipeline  
**Produced after:** Protocol artifact authoring and testing complete  

---

## 1. Approved Deviations

Deviations from Design Intent that were approved during artifact authoring. Each deviation must reference the DI artifact it departs from and state the governance rationale.

| Artifact | DI Reference | Deviation | Rationale |
|----------|-------------|-----------|-----------|
| WF_TRANSFER_V0, WF_STAKE_V0, WF_UNSTAKE_V0 (ENDUSER WFs) | Authoring Mandate Section 5 — cross-subdomain dependency notes | CC_RESERVE_NONCE_V0 absent from all ENDUSER WF pipelines | BACHI data model removes ETH-style nonce reservation entirely; no sequential nonce counter is needed in a content-addressable ID system; the mandate's cross-subdomain note was authored before the full BACHI simplification was resolved |
| WF_TRANSFER_V0, WF_STAKE_V0, WF_UNSTAKE_V0 (ENDUSER WFs) | Authoring Mandate Section 5 — cross-subdomain dependency notes | CC_WRITE_ACTOR_RECORD_V0 absent from all transaction WF pipelines | CC_WRITE_ACTOR_RECORD_V0 belongs to the actor registration WF (WF_REGISTER_ACTOR_UNVERIFIED_V0), not transaction WFs; transaction WFs call CC_RESOLVE_ACTOR_ID_V0 (read-only ownership check) — writing actor records during transaction submission would be a boundary violation |
| All 8 WF_*_V0 (initial authoring) | Authoring Mandate Wave 5 | EXIT_DUPLICATE node initially authored with `reason: DUPLICATE_TX`; corrected to `reason: DUPLICATE_NONCE` before final compile | WF schema ASSERT_SCHEMA_CONFORMANCE_V0 enforces reason enum `['EXITED', 'COMPLETED', 'FAILED', 'HALTED', 'DUPLICATE_NONCE']`; `DUPLICATE_TX` is not a valid enum member; the original WF_SUBMIT_TRANSACTION_V0 (now RETIRED) used `DUPLICATE_NONCE` — that pattern should have been followed |

---

## 2. Architectural Discoveries

Findings that emerged during artifact authoring revealing that the architecture itself needed correction or was incomplete.

| Discovery | Impact | Disposition |
|-----------|--------|-------------|
| CC_BUILD_ETH_TX_V0 and CC_HASH_TRANSACTION_V0 were RETIRED (ETH-specific), leaving no tx_id/tx_hash generation mechanism in the BACHI-native pipeline | All 8 typed WFs require a deterministic tx_id and tx_hash; without a generation CC, no WF DAG could complete to CC_PERSIST_MEMPOOL_TX_V0 | New CC_GENERATE_TX_ID_V0 authored: wraps CT_PURE_GENERATE_ID_V0 twice (TX prefix for tx_id, TXHASH prefix for tx_hash); content-addressable, no cryptographic signing; replaces the ETH pipeline with a single deterministic CC; unplanned addition to the 57-action mandate |

---

## 2b. Implementation Discoveries

Findings that emerged during artifact authoring revealing that an existing, correct architecture had not yet been fully adopted or implemented by all consumers.

| Discovery | Impact | Disposition |
|-----------|--------|-------------|
| Authoring Mandate Section 5 declared "Each RB_ carries `tx_type` as a `wf_literal` node binding on the CC_PERSIST_MEMPOOL_TX_V0 step" — no `wf_literal` mechanism was found implemented in the compiler | `tx_type` could not be injected via RB; the WF graph has no mechanism to read literal values declared in an RB binding | `tx_type` declared as a YAML literal value directly in each WF's `inputs` block for the relevant CC nodes (e.g., `tx_type: TRANSFER`); semantically equivalent — each WF is typed and carries its own tx_type literal; `wf_literal` deferred to a future CR as a potential compiler feature |

---

## 3. Unexpected Constraints

Constraints encountered during authoring that blocked, redirected, or modified the implementation from what Design Intent specified.

| Constraint | Affected Artifacts | Resolution |
|------------|-------------------|------------|
| SYSTEM WFs (MINT, BURN, POOL, REWARD, SLASH) have no actor payload — CC_APPEND_TX_EVENT_V0 requires an `actor_id` input field | CC_APPEND_TX_EVENT_V0 must receive a non-null actor_id; SYSTEM transactions have no actor submitting them | `actor_id: SYSTEM` declared as a YAML literal value in each SYSTEM WF's CC_APPEND_TX_EVENT_V0 node inputs; consistent with the SYSTEM authority pattern already used in identity and wallet domains |
| WF_POOL_V0: IN_POOL_V0 payload supplies only `amount` and `triggered_by` — no pool_wallet_id field; CC_VALIDATE_POOL_POLICY_V0 requires a pool_wallet_id to resolve the POOL system wallet | CC_VALIDATE_POOL_POLICY_V0 node could not receive pool_wallet_id from payload | `pool_wallet_id: POOL` declared as a YAML literal value in the CC_VALIDATE_POOL_POLICY_V0 node inputs; CC resolves the POOL system wallet by this identifier against the WALLETS store |

---

## 4. Governance Findings

New governance knowledge produced by this CR — boundary decisions, ownership clarifications, or protocol rules discovered through implementation.

| Finding | Type | Governance Implication |
|---------|------|----------------------|
| BACHI transaction identity (tx_id, tx_hash) is content-addressable via CT_PURE_GENERATE_ID_V0 — not derived from ECDSA signing or keccak-256 hashing | Protocol data model rule | All future transaction CRs must use CC_GENERATE_TX_ID_V0 for tx_id/tx_hash generation; no CC that uses ETH signing primitives (CC_BUILD_ETH_TX_V0, CC_HASH_TRANSACTION_V0, CC_SIGN_TRANSACTION_V0) may be referenced from an active WF — all three are RETIRED |
| `block` and `chain` are cross-consensus subdomains — they cannot be owned by `consensus_pos` because both PoS and future consensus algorithms (e.g., PoW) depend on block structure and chain topology | Subdomain boundary rule | `block` is an established first-class subdomain of `blockchain` (CC_FORM_BLOCK_V0 and WF_PROPOSE_BLOCK_V0 were built and tested under `consensus_pos` CR; CC_FORM_BLOCK_V0 is updated in this CR under subdomain: `block`). `chain` is declared as a peer subdomain — no artifacts authored in this CR, boundary established for future CRs. Neither `block` nor `chain` may be nested under `consensus_pos` — consensus depends on block/chain, not the reverse. Governing block or chain under `consensus_pos` would invert the dependency. This boundary is recorded here to prevent re-litigation when PoW or other consensus algorithms are introduced. |
| SYSTEM authority transaction WFs carry actor_id as a literal constant (`SYSTEM`), not from payload or actor context | Protocol authority rule | WFs with `admission: requires: []` and `actor_id: SYSTEM` are the canonical SYSTEM authority pattern; any WF requiring actor resolution must declare `requires: [EV_WALLET_CREATED_V0]` or equivalent actor binding in admission |
| tx_type literal must be declared in the WF node inputs, not in RB bindings | WF authoring convention | Each typed WF carries its tx_type as a YAML literal in the CC_GENERATE_TX_ID_V0 and CC_PERSIST_MEMPOOL_TX_V0 node inputs; the `wf_literal` RB binding pattern described in the mandate is not yet implemented and should be treated as a future compiler feature candidate |

---

## 5. Amendments to Intent

Changes required to any prior stage artifact (BI, GI, DI) based on what was learned during authoring. These amendments are recorded here; the prior stage documents are updated separately if needed.

| Stage Artifact | Amendment | Reason |
|----------------|-----------|--------|
| Authoring Mandate Section 5 — cross-subdomain dependency notes | CC_RESERVE_NONCE_V0 and CC_WRITE_ACTOR_RECORD_V0 removed from transaction WF pipeline dependencies | BACHI model has no nonce reservation; CC_WRITE_ACTOR_RECORD_V0 is actor registration scope, not transaction scope |
| Authoring Mandate Section 5 — `wf_literal` binding pattern | `wf_literal` pattern is not yet implemented; tx_type injected as YAML literal in WF nodes instead | No compiler implementation found; pattern deferred to future CR |
| Authoring Mandate Wave 1–5 action count (57) | Actual count is 58 (57 mandated + 1 unplanned CC_GENERATE_TX_ID_V0) | ETH pipeline retirement created a tx_id generation gap requiring a new BACHI-native CC |

---

## 6. Future CR Candidates

Capabilities, constraints, or concerns that surfaced during this CR but are explicitly deferred.

| Concept | Domain / Subdomain | Priority | Notes |
|---------|-------------------|----------|-------|
| Consensus finalization CR: author WF_ATTEST_BLOCK_V0, WF_FINALIZE_BLOCK_V0, WF_COMMIT_BLOCK_V0, WF_RECONCILE_BALANCES_V0 under the `consensus_pos` subdomain track — this is the primary realization dependency for the data_model CR; without block finalization and balance reconciliation, typed transaction WFs produce PENDING transactions that are never finalized and wallet balances are never updated | pgs_blockchain / consensus_pos | CRITICAL | WF_PROPOSE_BLOCK_V0 already exists and was built and tested in the consensus_pos CR; the follow-on CR completes the remaining steps: attest → finalize → commit → reconcile. The data_model CR delivers compiler-validated typed transaction artifacts; they cannot demonstrate end-to-end execution until the full block lifecycle (propose → attest → finalize → commit → reconcile) is governed. This follow-on CR completes the token economy loop. |
| `wf_literal` compiler feature: allow RB_ artifacts to declare literal value bindings that override WF node inputs, enabling the RB to carry the tx_type constant rather than each WF duplicating it | pgs_compiler / runtime_bindings | LOW | Authoring convenience only — current YAML literal pattern is functionally equivalent; each typed WF is self-contained and the duplication is minimal |
| End-to-end runtime execution test for all 8 typed WFs (TRANSFER, STAKE, UNSTAKE, MINT, BURN, POOL, REWARD, SLASH) | pgs_blockchain / transaction | HIGH | This CR delivered compiler-validated artifacts; no e2e runtime execution has been performed for the 8 typed transaction WFs; missing runtime implementations (CC_VALIDATE_*_POLICY_V0) will need CS wiring before execution succeeds |
| CC_VALIDATE_*_POLICY_V0 CS wiring: all 8 policy CCs validate wallet existence against the WALLETS store but the CS_MUTABLE_JSON_V0 READ/LIST implementation must be confirmed to resolve system wallets by wallet_type | pgs_blockchain / transaction | HIGH | SYSTEM wallet resolution (POOL, BURN, MINT wallets) uses `wallet_type` filter — the CS LIST op returning `records` must support this filter pattern at runtime |

---

## 7. As-Designed vs. As-Built Reconciliation

Summary delta between Design Intent (as-designed) and implemented artifacts (as-built).

| Concern | As-Designed | As-Built | Delta |
|---------|-------------|----------|-------|
| tx_id/tx_hash generation | CC_BUILD_ETH_TX_V0 + CC_HASH_TRANSACTION_V0 (RETIRED) | CC_GENERATE_TX_ID_V0 (new, BACHI-native) | ETH pipeline retired; content-addressable ID generation replaces cryptographic derivation |
| tx_type injection into CC_PERSIST_MEMPOOL_TX_V0 | `wf_literal` binding declared in RB_ | YAML literal value in WF node inputs block | `wf_literal` not compiler-implemented; pattern moved to WF |
| ENDUSER WF pipeline | CC_RESOLVE_ACTOR_ID + CC_RESERVE_NONCE + CC_VALIDATE_POLICY + CC_GENERATE_TX_ID + CC_PERSIST + CC_APPEND_EVENT | CC_RESOLVE_ACTOR_ID + CC_VALIDATE_POLICY + CC_GENERATE_TX_ID + CC_PERSIST + CC_APPEND_EVENT | CC_RESERVE_NONCE_V0 removed — BACHI has no nonce; CC_WRITE_ACTOR_RECORD_V0 removed — wrong scope |
| Total mandated authoring actions | 57 | 58 (57 + CC_GENERATE_TX_ID_V0) | 1 unplanned addition to cover ETH pipeline retirement gap |

---

## 8. Governed Evolution Metrics

| Metric | Value |
|--------|-------|
| Mandated authoring actions | 57 |
| Completed authoring actions | 58 (57 mandated + 1 unplanned) |
| Snapshot growth | +38 artifacts (22 WF, 19 RB, 22 IN, 25 EV across all types) |
| Architectural discoveries | 1 (CC_GENERATE_TX_ID_V0 gap) |
| Implementation discoveries | 1 (wf_literal not implemented) |
| Schema violations encountered and fixed | 8 (DUPLICATE_TX → DUPLICATE_NONCE, all 8 WFs) |
| Governance findings | 3 |
| Approved deviations | 3 |
| Conformance status | 77 / 77 PASS |
| Snapshot status | VALID |

---

## 9. Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 7 — Authoring Mandate | 7_authoring_mandate_data_model_v0.md | COMPLETE |
| Wave 1 | 8 RETIRE (ETH pipeline artifacts), 8 IN_ (typed transaction intents), 5 EV_ (block + transaction events), 3 seeds | COMPLETE |
| Wave 2 | 3 IN_ UPDATE (IN_ACTOR_REGISTERED, IN_WALLET_CREATED, IN_VALIDATOR_REGISTERED), CC_PERSIST_MEMPOOL_TX_V0 UPDATE | COMPLETE |
| Wave 3 | 4 CC_ UPDATE (CC_WRITE_ACTOR_RECORD, CC_CREATE_WALLET_RECORD, CC_WRITE_VALIDATOR_RECORD, CC_FORM_BLOCK), 8 CC_ NEW (CC_VALIDATE_*_POLICY_V0) | COMPLETE |
| Wave 4 | STRUCTURE_BLOCKCHAIN_STORAGE_V0 REVIEW (no changes required), 8 RB_ NEW (typed transaction runtime bindings), 1 CC_ NEW (CC_GENERATE_TX_ID_V0, unplanned) | COMPLETE |
| Wave 5 | 8 WF_ NEW (typed transaction workflows, ENDUSER + SYSTEM patterns) | COMPLETE |
| Wave 6 | blockchain structure compile: 376 artifacts, Verified: True, Attested: True; 8 schema violations (DUPLICATE_TX) detected and fixed; recompile: 0 violations; full build: 77/77 conformance PASS, snapshot VALID | COMPLETE |
| Stage 8 — Authoring Manifest | This document | APPROVED |

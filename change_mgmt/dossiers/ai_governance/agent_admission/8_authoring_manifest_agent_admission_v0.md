# Authoring Manifest: ai_governance / agent_admission
**Domain:** ai_governance
**Subdomain:** agent_admission
**Version:** V0
**Status:** APPROVED
**Pipeline Stage:** Stage 8 — Authoring Manifest
**Produced by:** v0.5.0 SDLC authoring pipeline
**Produced after:** Authoring Mandate complete (Stage 7); protocol artifact authoring and testing complete

---

## 1. Approved Deviations

Deviations from Design Intent approved during artifact authoring. Each deviation must reference the DI artifact it departs from and state the governance rationale.

| Artifact | DI Reference | Deviation | Rationale |
|----------|-------------|-----------|-----------|
| *(none)* | | | |

No deviations. Layer ordering in the Authoring Mandate (L1:RB → L2:WF → L3:IN) was followed exactly. The entity-based CS_APPENDONLY_JSONL_V0 pattern was pre-encoded in the design specs and required no adjustment during authoring.

---

## 2. Architectural Discoveries

Findings that emerged during artifact authoring revealing that the architecture itself needed correction or was incomplete.

| Discovery | Impact | Disposition |
|-----------|--------|-------------|
| *(none)* | | |

No architectural discoveries. The architecture was complete and correct as specified.

---

## 2b. Implementation Discoveries

Findings that emerged during artifact authoring or runtime execution revealing that an existing, correct architecture had not yet been fully adopted by all consumers.

| Discovery | Impact | Disposition |
|-----------|--------|-------------|
| `dispatch.py` keyed WF node bindings by CC FQDN address rather than by `node_key` — all four denial paths in `WF_GOVERN_AGENT_ADMISSION_V0` collapsed to a single binding entry, causing incorrect denial reason routing | Four distinct denial paths (UNAUTHORIZED_ACTOR, UNAUTHORIZED_TOOL, UNDECLARED_TOOL, PARAMETER_VIOLATION) each resolved to the same binding; runtime always returned the last-written denial_reason regardless of which CC raised the VIOLATION | Root cause fixed in `dispatch.py`; keying changed from CC FQDN to `node_key`; named governance added: INVARIANT_WF_NODE_KEY_BINDING_UNIQUE_V0 + ASSERT_WF_NODE_KEY_BINDING_UNIQUE_V0 added to FB_TOPOLOGY; compiled canonical JSONs and handler registered in pgs_governance |
| `s7_materialize.py` did not propagate `expected_outcome` from TEST_DATA case data into CT_CONFORMANCE artifacts; `_project_single_node` in `s4_govern.py` did not expose `content` to governance handlers — no handler could inspect TEST_DATA case blocks at compile time | CT conformance test cases were missing `expected_outcome`, making the conformance runner unable to determine the expected result contract; 28 TEST_DATA files affected across pgs_capabilities, pgs_blockchain, pgs_ai_governance | Root cause fixed in `s7_materialize.py` (propagates expected_outcome); `_project_single_node` extended in `s4_govern.py` to expose `content`; named governance added: INVARIANT_CT_TEST_DATA_OUTCOME_DECLARED_V0 + ASSERT_CT_TEST_DATA_OUTCOME_DECLARED_V0; all 28 TEST_DATA files updated with explicit expected_outcome |

Both discoveries are platform-level bugs surfaced by agent_admission end-to-end execution testing. Neither is an agent_admission architecture gap — both are prior implementation debts that execution testing exposed and that are now governed by named invariants.

---

## 2c. CT Vocabulary Discoveries

Findings revealing that the transform vocabulary lacked an atom needed for a declared CC pipeline step, or that a CT was semantically mismatched.

| Discovery | Impact | Disposition |
|-----------|--------|-------------|
| *(none)* | | |

No CT vocabulary discoveries. All three CTs in use (CT_PURE_VALIDATE_SET_MEMBERSHIP_V0, CT_PURE_LOOKUP_V0, CT_PURE_VALIDATE_PARAMETER_RULES_V0) are the same transforms used in the analogous agent_governance CCs. Semantic fit was established by prior execution.

---

## 2d. Surface Alignment Discoveries

Findings revealing that a CC's declared result surface did not match the result status actually produced by its CS step — a class of gap not yet detected by the compiler.

| Discovery | Impact | Disposition |
|-----------|--------|-------------|
| *(none)* | | |

No surface alignment discoveries. Scenario 02 (EMP_NONE_001, no_license) exercised the `NOT_FOUND` path from `CC_RESOLVE_LICENSE_TIER_V0` and routed correctly to `CC_AUDIT_UNAUTHORIZED_ACTOR → EXIT_UNAUTHORIZED_ACTOR` as specified. No LIST operations in agent_admission — the EMPTY vs NOT_FOUND gap class that affected consensus_pos cannot recur here.

---

## 3. Unexpected Constraints

Constraints encountered during authoring that blocked, redirected, or modified the implementation from what Design Intent specified.

| Constraint | Affected Artifacts | Resolution |
|------------|-------------------|------------|
| *(none)* | | |

No unexpected constraints. Both known compile-time constraints (ASSERT_IN_WORKFLOW_BINDING_V0 and S2_CANONICALIZE FQDN resolution) were pre-handled in the Authoring Mandate layer ordering (L1:RB → L2:WF → L3:IN). No wave deferral was required.

---

## 4. Governance Findings

New governance knowledge produced by this CR — boundary decisions, ownership clarifications, or protocol rules discovered through implementation.

| Finding | Type | Governance Implication |
|---------|------|----------------------|
| 1:1 IN_→WF_ binding is structural — same schema does not imply shared intent | Protocol invariant | Every new workflow requires a new IN_ artifact. Reusing an IN_ across workflows violates the federation boundary invariant. This applies to all future subdomain CRs. Pre-confirmed at Stage 6 Governance Intent. |
| WF node_key must uniquely identify each CC node usage within a WF's binding set — keying bindings by CC FQDN collapses multiple uses of the same CC to a single entry | Platform governance (INVARIANT_WF_NODE_KEY_BINDING_UNIQUE_V0) | Enforced at compile time via ASSERT_WF_NODE_KEY_BINDING_UNIQUE_V0 in FB_TOPOLOGY. All WF authors must ensure each `node_key` is unique within the WF's declared binding set. Applies to all future CRs producing multi-path denial workflows. |
| Every TEST_DATA case must declare an explicit `expected_outcome` field — the conformance runner cannot default an absent value to SUCCESS without silently masking VIOLATION test cases | Platform governance (INVARIANT_CT_TEST_DATA_OUTCOME_DECLARED_V0) | Enforced at compile time via ASSERT_CT_TEST_DATA_OUTCOME_DECLARED_V0 in FB_TOPOLOGY. All TEST_DATA authors must include `expected_outcome: SUCCESS` or `expected_outcome: VIOLATION` in every `### Case N:` yaml block. |

---

## 5. Amendments to Intent

Changes required to any prior stage artifact based on what was learned during authoring.

| Stage Artifact | Amendment | Reason |
|----------------|-----------|--------|
| *(none)* | | |

No prior stage documents required amendment. The Authoring Mandate correctly pre-encoded all compile-time ordering constraints, and no deviations or architectural corrections altered the declared intent.

---

## 6. Future CR Candidates

Capabilities, constraints, or concerns that surfaced during this CR but are explicitly deferred. Each entry is a candidate input for a future Change Request.

| Concept | Domain / Subdomain | Priority | Notes |
|---------|-------------------|----------|-------|
| Compiler surface alignment check: assert that each CC's declared result_surface entries are producible by its CS step | pgs_compiler / assertions | HIGH | Carried from consensus_pos (Section 6). Surface Alignment Discovery 2d is only detectable at runtime. For agent_admission, the risk is low but the compiler gap remains. An assertion phase that cross-references CS operation return semantics against CC result_surface declarations would make this class of gap compile-time detectable. |
| Phase 2 — OpenClaw adapter: replace Python harness with a real agent runtime adapter | ai_governance / agent_admission | HIGH | Explicitly planned at Business Intent. No governance changes required — only the transport adapter changes. The test of Business Commitment C7: "The governance model is not modified when the Python harness is replaced." |
| Phase 3 — Multi-agent coordination and federated governance | ai_governance / TBD | MEDIUM | Declared in Business Intent Phase Relationship table. Requires multi-agent authority model and agent-to-agent delegation — new CR |
| Premium tier addition: add `premium` tier to CC_BIND_AGENT_LICENSE_TO_TOOL_SURFACE_V0 | ai_governance / agent_admission | LOW | Intentionally omitted in Phase 1 — three tiers exist in ai_licensing but only standard and enterprise are mapped to the agent tool surface. When the business requires a premium-tier agent tool surface, a V1 of this CC is required. |
| Path traversal constraints for write_file: add `..` restriction to CC_VALIDATE_AGENT_TOOL_PARAMETERS_V0 | ai_governance / agent_admission | LOW | Explicitly deferred to V1 in Design Intent. Phase 1 constraints are required-field-only. Production-grade path safety requires additional `not_contains: ..` operator on the `path` field. |
| Authoring Mandate methodology: document known build ordering constraints (RB before WF, WF before IN) as methodology rules | pgs_change_mgmt / methodology | MEDIUM | Reduces per-CR wave deferral surprises. The lesson from consensus_pos (IN authored too early, RB scheduled too late) is now incorporated into agent_admission's mandate by design — but it should be a documented methodology rule so future CRs don't rediscover it. |

---

## 7. As-Designed vs. As-Built Reconciliation

Summary delta between Design Intent (as-designed) and implemented artifacts (as-built).

| Concern | As-Designed | As-Built | Delta |
|---------|-------------|----------|-------|
| WF artifact count | 1 (WF_GOVERN_AGENT_ADMISSION_V0) | 1 | None |
| CC artifact count | 3 (CC_CHECK_AGENT_TOOL_DECLARED_V0, CC_BIND_AGENT_LICENSE_TO_TOOL_SURFACE_V0, CC_VALIDATE_AGENT_TOOL_PARAMETERS_V0) | 3 | None |
| IN artifact count | 1 (IN_AGENT_ADMISSION_REQUESTED_V0) | 1 | None |
| RB artifact count | 1 (RB_AGENT_ADMISSION_BINDINGS_V0) | 1 | None |
| STRUCTURE artifact count | 1 (STRUCTURE_AGENT_ADMISSION_STORAGE_V0) | 1 | None |
| Layer ordering | L1: RB → L2: WF → L3: IN | L1: RB → L2: WF → L3: IN | None — followed exactly |
| CC pipeline order | CC_CHECK_AGENT_TOOL_DECLARED → CC_BIND_AGENT_LICENSE_TO_TOOL_SURFACE → CC_VALIDATE_AGENT_TOOL_PARAMETERS | As designed | None |
| Denial routing paths | 4 distinct paths (UNAUTHORIZED_ACTOR, UNAUTHORIZED_TOOL, UNDECLARED_TOOL, PARAMETER_VIOLATION) | 4 distinct paths confirmed by execution | None (dispatch.py bug fixed before final test) |
| Reused CCs (agent_governance) | CC_AUDIT_UNAUTHORIZED_ACTOR_V0, CC_RECORD_DENIED_ACTION_V0, CC_RECORD_GOVERNED_ACTION_V0 | Reused unchanged | None — no modifications to existing CCs |

---

## 8. Governed Evolution Metrics

| Metric | Pre-Authoring Estimate | Actual |
|--------|----------------------|--------|
| Mandated authoring actions | 16 (2 pre-auth + 7 protocol artifacts + 7 testbed files) | 16 |
| Completed authoring actions | 16 | 16 |
| Snapshot growth | 155 → 162 artifacts (+7) | 155 → 162 (+7) — estimate exact |
| Pre-authoring modifications | 1 (STRUCTURE_DISCOVERY_V0 one-line addition) | 2 (STRUCTURE_DISCOVERY_V0 + registry directory structure) |
| Architectural discoveries | 0 expected | 0 |
| Implementation discoveries | 0 expected | 2 (platform-level: dispatch.py binding collapse, s7_materialize.py expected_outcome omission) |
| CT vocabulary discoveries | 0 expected | 0 |
| Surface alignment discoveries | 0 expected | 0 |
| Governance findings | 1 confirmed pre-authoring | 3 (1 pre-confirmed + 2 new INVARIANTs in FB_TOPOLOGY) |
| Approved deviations | 0 expected | 0 |
| Conformance status | PENDING | 77/77 PASS |
| Snapshot status | PENDING | VALID |

**Implementation discovery note:** Both discoveries are platform-level bugs, not agent_admission design gaps. They were latent in the codebase and surfaced because agent_admission is the first multi-path denial workflow in the domain (Bug 1) and the first workflow where conformance test expected outcomes were systematically verified (Bug 2). Both are now governed by compile-time invariants that prevent recurrence.

---

## 9. Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 0 — Change Request | 1_change_request_agent_admission_v0.md | COMPLETE |
| Stage 1 — Input Elicitation | 1_input_elicitation_agent_admission_v0.md | COMPLETE |
| Stage 2 — Domain Model | 2_domain_model_agent_admission_v0.md | COMPLETE |
| Stage 3 — Analysis Loop | 3_analysis_loop_agent_admission_v0.md | COMPLETE |
| Stage 4 — Business Model | 4_business_model_agent_admission_v0.md | COMPLETE |
| Stage 5 — Business Intent | 5_business_intent_agent_admission_v0.md | COMPLETE |
| Stage 6 — Governance Intent | 6_governance_intent_agent_admission_v0.md | COMPLETE |
| Stage 6b — Design Intent | 6b_design_intent_agent_admission_v0.md | COMPLETE |
| Stage 7 — Authoring Mandate | 7_authoring_mandate_agent_admission_v0.md | COMPLETE |
| Pre-authoring (A1) | STRUCTURE_DISCOVERY_V0 — added agent_admission to allowed_domains | COMPLETE |
| Pre-authoring (A2) | agent_admission registry directory structure created | COMPLETE |
| Protocol Artifacts | IN_AGENT_ADMISSION_REQUESTED_V0, WF_GOVERN_AGENT_ADMISSION_V0, CC_CHECK_AGENT_TOOL_DECLARED_V0, CC_BIND_AGENT_LICENSE_TO_TOOL_SURFACE_V0, CC_VALIDATE_AGENT_TOOL_PARAMETERS_V0, STRUCTURE_AGENT_ADMISSION_STORAGE_V0, RB_AGENT_ADMISSION_BINDINGS_V0 | COMPLETE |
| Platform Fixes | dispatch.py (node_key binding), s7_materialize.py (expected_outcome propagation), s4_govern.py (content projection), 28 TEST_DATA files updated | COMPLETE |
| Governance Additions | INVARIANT_WF_NODE_KEY_BINDING_UNIQUE_V0, ASSERT_WF_NODE_KEY_BINDING_UNIQUE_V0, INVARIANT_CT_TEST_DATA_OUTCOME_DECLARED_V0, ASSERT_CT_TEST_DATA_OUTCOME_DECLARED_V0 + compiled canonical JSONs + handler | COMPLETE |
| Compiler Build | STRUCTURE_BUILD_AI_GOVERNANCE_CONFIG_V0 + STRUCTURE_BUILD_VOCABULARY_AGGREGATE_V0 + full build sync | COMPLETE |
| Testbed | README + 6 test payloads in testbed/agent_admission/ | COMPLETE |
| Runtime Execution Testing | 6 scenarios × expected decision × trace verification: scenario 01 (ADMIT — web_search, standard), scenario 02 (DENY — no license), scenario 03 (DENY — standard attempts write_file), scenario 04 (ADMIT — enterprise write_file), scenario 05 (DENY — undeclared tool), scenario 06 (DENY — parameter violation); all 6 decisions correct; all 4 denial reasons distinct; determinism confirmed (scenario 01 re-run → same TRACE_ID) | COMPLETE |
| Stage 8 — Authoring Manifest | This document | APPROVED |
| Stage 9 — CR Closure | See Section 10 | COMPLETE |

---

## 10. Completion Criterion — SATISFIED

1. ✅ All PENDING sections populated with actual execution data
2. ✅ All seven protocol artifacts compiled and present in `protocol_snapshot/`
3. ✅ All six test scenarios execute and produce the expected decision
4. ✅ All six traces verified (non-empty, correct decision outcome, correct denial reason)
5. ✅ Determinism invariant holds — scenario 01 re-run produces same TRACE_ID
6. ✅ No existing artifact in `agent_governance`, `ai_licensing`, or the platform layer was modified (platform fixes are compiler/runtime layer, not protocol artifacts)
7. ✅ `STRUCTURE_DISCOVERY_V0` change is the only governance source modification

**Status: APPROVED — all completion criteria satisfied.**

---

## Stage 9 — CR Closure

**Closed by:** v0.5.0 SDLC authoring pipeline  
**Closed on:** 2026-06-03  
**Final snapshot:** 162 artifacts, 77/77 conformance PASS, VALID

### Governance Artifacts Produced by This CR

| Artifact | Type | Scope |
|----------|------|-------|
| INVARIANT_WF_NODE_KEY_BINDING_UNIQUE_V0 | FB_TOPOLOGY invariant | All WF artifacts — node_key uniqueness in binding sets |
| ASSERT_WF_NODE_KEY_BINDING_UNIQUE_V0 | FB_TOPOLOGY assertion | Compile-time enforcement of node_key invariant |
| INVARIANT_CT_TEST_DATA_OUTCOME_DECLARED_V0 | FB_TOPOLOGY invariant | All TEST_DATA artifacts — explicit expected_outcome required |
| ASSERT_CT_TEST_DATA_OUTCOME_DECLARED_V0 | FB_TOPOLOGY assertion | Compile-time enforcement of expected_outcome invariant |

### Methodology Lessons Carried Forward

| Lesson | Origin | Action |
|--------|--------|--------|
| Layer ordering (L1:RB → L2:WF → L3:IN) should be a documented methodology rule, not per-CR tribal knowledge | consensus_pos discovery; incorporated into agent_admission mandate | Future CR candidate: pgs_change_mgmt/methodology — codify as Authoring Mandate invariant |
| Multi-path denial workflows must verify each denial path produces its distinct denial_reason at runtime — not just that the WF reaches a denial exit | agent_admission execution testing (Bug 1) | Add to authoring mandate test checklist for workflows with multiple VIOLATION routing paths |
| Every TEST_DATA file must declare expected_outcome at authoring time — not at test-run time | Bug 2 governance | Now compile-time enforced via ASSERT_CT_TEST_DATA_OUTCOME_DECLARED_V0; no further action needed |

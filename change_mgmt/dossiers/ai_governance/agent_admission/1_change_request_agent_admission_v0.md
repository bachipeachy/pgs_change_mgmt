# Change Request: ai_governance / agent_admission
**CR Type:** change_request_subdomain (provisional — analysis loop will confirm)
**Domain:** ai_governance
**Subdomain:** UNDETERMINED — pipeline will discover whether this extends `agent_governance` or declares a new governed namespace (`agent_admission`)
**Version:** V0
**Status:** OPEN — Stage 0 complete; entering Stage 1
**Pipeline Stage:** Stage 0 — Change Request Classification

---

## 1. Problem Statement

Autonomous AI agents act on external systems — files, browsers, APIs, messaging, databases — without structural governance. Current mitigation strategies are operational: system prompts the agent may ignore, middleware filters that catch known-bad patterns, and monitoring dashboards that detect violations after they happen.

None of these are structural. The agent can still attempt any action the runtime allows. Governance is advisory, not architecturally enforced.

PGS governs execution by declaring what is admissible before execution begins. Whether that structural governance model extends to autonomous AI agents — agents that propose actions against external systems — is an open architectural question this CR exists to answer.

---

## 2. Business Question

**Can autonomous agent actions be structurally governed by protocol rather than operationally supervised by middleware?**

This is the central question. The CR does not assume the answer. The analysis loop will determine what governance capabilities are required, what already exists in PPS, and whether the problem surface fits within existing `agent_governance` or requires a new subdomain.

---

## 3. Desired Outcome

A governed execution envelope for a single autonomous agent operating against a single external runtime. By end of this CR:

- Agent action proposals must pass protocol admission before any tool executes
- Tool surfaces are explicitly declared — undeclared tools are structurally absent, not filtered
- Authority is governed — the agent holds a declared authority scope; actions outside it are inadmissible
- Every admission decision produces a deterministic trace
- The governance model is runtime-agnostic — it must survive replacement of the external runtime without protocol changes

---

## 4. Known Facts at CR Entry

| Fact | Source |
|------|--------|
| `ai_governance::agent_governance` subdomain exists with `WF_GOVERN_AGENT_ACTION_V0` | PPS snapshot |
| `ai_governance::ai_licensing` subdomain exists with license tier concepts (STANDARD, PREMIUM, ENTERPRISE) | PPS snapshot |
| Actor identity and enrollment is governed under `blockchain::identity` | PPS snapshot |
| No governed artifact exists for autonomous agent tool surface declaration | PPS snapshot |
| No governed artifact exists for runtime-agnostic external tool execution | PPS snapshot |
| Authority governance is a declared governance concern (CONSTITUTION_AUTHORITY_GOVERNANCE_V0) | pgs_governance registry |
| External runtimes that may serve as the first integration target include OpenClaw, Claude Code, LangGraph, CrewAI, AutoGen | Domain knowledge — runtime choice is implementation detail, not CR scope |

---

## 5. CR Type Determination

**Provisional Type:** `change_request_subdomain`

**Analysis path triggered:** Full loop required. The subdomain placement question — whether this extends `agent_governance` or declares a new governed namespace — cannot be resolved before Domain Model Discovery and PPS baseline comparison. The full pipeline is required.

**Note on subdomain naming:** The provisional dossier folder `agent_admission` reflects the governance mechanism (admission control for agent actions), not a technology product. The governance topology discovery in Stage 6 will determine the canonical subdomain name. Any runtime-named subdomain is explicitly excluded as a governance namespace — the external runtime is implementation, not topology.

**Pipeline entry:** Stage 1 — Input Elicitation

---

## 6. Scope — Phase 1 Only

This CR is formally restricted to:

| In Scope | Description |
|----------|-------------|
| Single autonomous agent | One agent actor with a declared authority scope |
| Single governance envelope | One admission workflow governing the agent's tool surface |
| Single runtime integration | One external runtime used to prove the governance model |
| Tool surface declaration | Governed declaration of what tools are admissible |
| Authority validation | Does this agent hold authority to invoke this tool? |
| Admission and denial | Approve or deny tool execution before it occurs |
| Deterministic trace | Every governance decision produces an execution trace |

---

## 7. Out of Scope — Deferred to Future CRs

| Capability | Reason |
|-----------|--------|
| Agent-to-agent delegation | Requires multi-agent authority model — future CR |
| Escalation chains | Requires mid-execution suspension mechanism — not yet a PGS capability |
| Multi-agent coordination | Federated agent topology — Phase 3 of challenge project |
| Federated governance boundaries per agent | Future CR |
| LLM reasoning or planning governance | Out of scope by design — PGS governs actions, not reasoning |
| Modifying the external agent runtime | Not a PGS concern — governance wraps the runtime, never enters it |

---

## 8. Open Architectural Question — Let the Pipeline Decide

The most important output of this CR is not the artifacts. It is whether the analysis loop discovers that:

- `ai_governance::agent_governance` already owns the autonomous agent concern (EXTEND), or
- Autonomous agent governance requires a new subdomain declaration (NEW — candidate name: `agent_admission`), or
- A different name better captures the business concept

This must not be pre-decided. Stage 6 (Governance Intent) is where the subdomain question is resolved — after Domain Model Discovery and PPS baseline comparison have produced the evidence.

---

## 9. Strategic Context

consensus_pos proved PGS can evolve a blockchain domain under the governed pipeline.

This CR tests PGS against a fundamentally different governance surface:

| Dimension | consensus_pos | This CR |
|-----------|--------------|---------|
| Domain | Blockchain | AI Governance |
| Actor model | Validators (native PGS actors) | Autonomous agents (external runtime actors) |
| Authority model | Participation eligibility | Tool execution authority |
| Side-effect model | PGS-native storage | External runtime execution |
| Governance surface | PGS governing PGS | PGS governing a foreign runtime |

If this CR completes cleanly, FB_CHANGE_MGMT is validated across two fundamentally different problem domains.

---

## Dossier Status

| Stage | Artifact | Status |
|-------|----------|--------|
| Stage 0 | 1_change_request_agent_admission_v0.md | COMPLETE |
| Stage 1 | 1_input_elicitation_agent_admission_v0.md | COMPLETE |
| Stage 2 | 2_domain_model_agent_admission_v0.md | COMPLETE |
| Stage 3 | 3_analysis_loop_agent_admission_v0.md | COMPLETE |
| Stage 4 | 4_business_model_agent_admission_v0.md | COMPLETE |
| Stage 5 | 5_business_intent_agent_admission_v0.md | COMPLETE |
| Stage 6 | 6_governance_intent_agent_admission_v0.md | COMPLETE |
| Stage 6b | 6b_design_intent_agent_admission_v0.md | COMPLETE |
| Stage 7 | 7_authoring_mandate_agent_admission_v0.md | COMPLETE |
| Stage 8 | 8_authoring_manifest_agent_admission_v0.md | COMPLETE |

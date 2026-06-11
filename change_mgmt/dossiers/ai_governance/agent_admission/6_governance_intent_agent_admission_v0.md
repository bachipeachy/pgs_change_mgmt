# Stage 6 — Governance Intent: ai_governance / agent_admission
**Stage:** 6 — Governance Intent
**CR:** 1_change_request_agent_admission_v0.md
**Status:** COMPLETE
**Feeds:** Stage 6b — Design Intent

---

## 1. Subdomain Placement — Confirmed

**New subdomain:** `ai_governance::agent_admission`

Evidence basis (from Stage 3 analysis):
- The agent tool surface (registry, tier mapping, parameter constraints) is governance policy
- Governance policy lives in CC_ artifacts
- New governance policy = new CC_ artifacts
- New CC_ artifacts require a governing subdomain
- `agent_governance` owns licensing operation governance — distinct concern, untouched
- `agent_admission` owns autonomous agent tool admission governance

This subdomain owns exactly one governance concern: the declaration of what tools an autonomous agent may propose, under what authority conditions, and with what parameter constraints.

---

## 2. Governance Topology

### Entry Point

| Artifact | Family | Decision | Rationale |
|----------|--------|----------|-----------|
| `ai_governance::IN_AGENT_ADMISSION_REQUESTED_V0` | IN_ | NEW | Same payload schema as `IN_AGENT_ACTION_REQUESTED_V0` but bound exclusively to `WF_GOVERN_AGENT_ADMISSION_V0`. IN_→WF_ binding is 1:1 by constitution — a new workflow requires a new intent. |

### Admission Workflow

| Artifact | Family | Decision | Rationale |
|----------|--------|----------|-----------|
| `ai_governance::WF_GOVERN_AGENT_ADMISSION_V0` | WF_ | NEW | Same DAG topology as `WF_GOVERN_AGENT_ACTION_V0`. References agent_admission CCs instead of agent_governance CCs. Subdomain: `agent_admission`. |

### Capability Contracts — Governance Gates

| Artifact | Family | Decision | Rationale |
|----------|--------|----------|-----------|
| `ai_governance::CC_NORMALIZE_AGENT_REQUEST_V0` | CC_ | REUSE | Normalization (deterministic intent hash) is domain-agnostic. Tool name, user ID, context hash the same way regardless of tool surface. |
| `ai_governance::CC_CHECK_AGENT_TOOL_DECLARED_V0` | CC_ | NEW | Must contain `web_search`, `read_file`, `write_file` as the closed registry. Cannot reuse `CC_CHECK_TOOL_DECLARED_V0` — it contains licensing operations. |
| `ai_governance::CC_RESOLVE_LICENSE_TIER_V0` | CC_ | REUSE | License tier resolution from user ID is domain-agnostic. Same user, same license facts, same tier regardless of which tool is being requested. |
| `ai_governance::CC_BIND_AGENT_LICENSE_TO_TOOL_SURFACE_V0` | CC_ | NEW | Must map tiers to agent tools (`web_search`, `read_file`, `write_file`). Cannot reuse `CC_BIND_LICENSE_TO_TOOL_SURFACE_V0` — it maps tiers to licensing operations. |
| `ai_governance::CC_VALIDATE_AGENT_TOOL_PARAMETERS_V0` | CC_ | NEW | Must declare parameter constraints for agent tools. Cannot reuse `CC_VALIDATE_TOOL_PARAMETERS_V0` — it declares constraints for licensing fields. |
| `ai_governance::CC_RECORD_GOVERNED_ACTION_V0` | CC_ | REUSE | Authorized action recording is domain-agnostic. Same fields, same audit structure, same storage side effect regardless of which tool was authorized. |
| `ai_governance::CC_RECORD_DENIED_ACTION_V0` | CC_ | REUSE | Denied action recording is domain-agnostic. Same denial reasons, same audit structure, same storage side effect regardless of which tool was denied. |

### Events

| Artifact | Family | Decision | Rationale |
|----------|--------|----------|-----------|
| `ai_governance::EV_AGENT_ACTION_AUTHORIZED_V0` | EV_ | REUSE | Authorization event is domain-agnostic. The event signals the outcome; it does not encode the tool surface. |
| `ai_governance::EV_AGENT_ACTION_DENIED_V0` | EV_ | REUSE | Denial event is domain-agnostic. Same reasoning as above. |

### Actor

| Artifact | Family | Decision | Rationale |
|----------|--------|----------|-----------|
| `ai_governance::AC_AGENT_V0` | AC_ | REUSE | Agent actor definition (agent_id + requesting_user_id) is unchanged. Phase 1 does not introduce a new actor type. |

### Storage and Runtime Binding

| Artifact | Family | Decision | Rationale |
|----------|--------|----------|-----------|
| `ai_governance::STRUCTURE_AGENT_ADMISSION_STORAGE_V0` | STRUCTURE | NEW | `agent_admission` needs its own governance audit trail path (`ai_governance/agent_admission/governance_audit.jsonl`). Shares LICENSE_FACTS (read-only) with agent_governance. Storage topology is a governance concern — each subdomain declares its own. |
| `ai_governance::RB_AGENT_ADMISSION_BINDINGS_V0` | RB_ | NEW | New runtime binding for `WF_GOVERN_AGENT_ADMISSION_V0`. Same CS_ host classes as agent_governance. Different storage paths (agent_admission subdirectory). |

---

## 3. Governance Execution Flow

```
Python Harness (action proposal)
  → IN_AGENT_ADMISSION_REQUESTED_V0           [NEW — entry gate, agent_admission]
      ACK ↓
  → WF_GOVERN_AGENT_ADMISSION_V0              [NEW — admission DAG, agent_admission]
      ↓
  → CC_NORMALIZE_AGENT_REQUEST_V0             [REUSE — deterministic hash]
      SUCCESS ↓
  → CC_CHECK_AGENT_TOOL_DECLARED_V0           [NEW — agent tool registry]
      SUCCESS ↓              VIOLATION → CC_RECORD_DENIED_ACTION_V0 → EXIT_UNDECLARED_TOOL
  → CC_RESOLVE_LICENSE_TIER_V0                [REUSE — user license lookup]
      SUCCESS ↓              NOT_FOUND/VIOLATION → CC_RECORD_DENIED_ACTION_V0 → EXIT_UNAUTHORIZED_ACTOR
  → CC_BIND_AGENT_LICENSE_TO_TOOL_SURFACE_V0  [NEW — agent tier → tool surface]
      SUCCESS ↓              VIOLATION → CC_RECORD_DENIED_ACTION_V0 → EXIT_UNAUTHORIZED_TOOL
  → CC_VALIDATE_AGENT_TOOL_PARAMETERS_V0      [NEW — agent tool parameter constraints]
      SUCCESS ↓              VIOLATION → CC_RECORD_DENIED_ACTION_V0 → EXIT_PARAMETER_VIOLATION
  → CC_RECORD_GOVERNED_ACTION_V0              [REUSE — authorized action audit]
      SUCCESS ↓
  → EXIT_SUCCESS → EV_AGENT_ACTION_AUTHORIZED_V0   [REUSE]

All denial paths:
  → CC_RECORD_DENIED_ACTION_V0 → EXIT_* → EV_AGENT_ACTION_DENIED_V0   [REUSE]
```

---

## 4. Artifact Inventory

### New Artifacts (to be authored)

| FQDN | Family | Subdomain | Purpose |
|------|--------|-----------|---------|
| `ai_governance::IN_AGENT_ADMISSION_REQUESTED_V0` | IN_ | agent_admission | Entry intent bound to agent_admission workflow |
| `ai_governance::WF_GOVERN_AGENT_ADMISSION_V0` | WF_ | agent_admission | Admission DAG — same topology as WF_GOVERN_AGENT_ACTION_V0 |
| `ai_governance::CC_CHECK_AGENT_TOOL_DECLARED_V0` | CC_ | agent_admission | Agent tool registry (web_search, read_file, write_file) |
| `ai_governance::CC_BIND_AGENT_LICENSE_TO_TOOL_SURFACE_V0` | CC_ | agent_admission | Tier-to-agent-tool surface mapping |
| `ai_governance::CC_VALIDATE_AGENT_TOOL_PARAMETERS_V0` | CC_ | agent_admission | Parameter constraints for agent tools |
| `ai_governance::STRUCTURE_AGENT_ADMISSION_STORAGE_V0` | STRUCTURE | agent_admission | Storage topology for agent_admission subdomain |
| `ai_governance::RB_AGENT_ADMISSION_BINDINGS_V0` | RB_ | agent_admission | Runtime bindings for agent_admission workflow |

**Non-artifact deliverables:**
- Python harness (`AgentHarness`) — submits scripted tool proposals to `IN_AGENT_ADMISSION_REQUESTED_V0`
- Seed data — license_facts.json entries for Phase 1 test actors (standard-tier, enterprise-tier, no-license)
- Test payloads — one per test scenario (C1–C5 from Business Intent)

### Reused Artifacts (no modification)

| FQDN | Family | Owner Subdomain |
|------|--------|-----------------|
| `ai_governance::CC_NORMALIZE_AGENT_REQUEST_V0` | CC_ | agent_governance |
| `ai_governance::CC_RESOLVE_LICENSE_TIER_V0` | CC_ | agent_governance |
| `ai_governance::CC_RECORD_GOVERNED_ACTION_V0` | CC_ | agent_governance |
| `ai_governance::CC_RECORD_DENIED_ACTION_V0` | CC_ | agent_governance |
| `ai_governance::EV_AGENT_ACTION_AUTHORIZED_V0` | EV_ | agent_governance |
| `ai_governance::EV_AGENT_ACTION_DENIED_V0` | EV_ | agent_governance |
| `ai_governance::AC_AGENT_V0` | AC_ | agent_governance |

---

## 5. Governance Boundary Assertions

**`agent_governance` is not modified.** All seven CC_ artifacts in agent_governance remain unchanged. The WF_, IN_, and EV_ artifacts in agent_governance remain unchanged. No existing test scenarios or traces are affected.

**`ai_licensing` is not modified.** The license tier model (STANDARD, PREMIUM, ENTERPRISE) and license_facts.json seed data are read-only inputs to agent_admission — not owned by it.

**`blockchain::identity` is not modified.** Identity infrastructure is a dependency, not a deliverable.

**CT_ functions are not modified.** `CT_PURE_VALIDATE_SET_MEMBERSHIP_V0`, `CT_PURE_LOOKUP_V0`, and `CT_PURE_VALIDATE_PARAMETER_RULES_V0` are reused as-is. No new CT_ functions are required.

---

## 6. Open Design Questions for Stage 6b

| # | Question | Scope |
|---|----------|-------|
| D1 | What is the tier-to-tool mapping? Which tiers permit `web_search`, `read_file`, `write_file`? | CC_BIND_AGENT_LICENSE_TO_TOOL_SURFACE_V0 pipeline |
| D2 | What parameter constraints apply per tool? (field names, types, operators, values) | CC_VALIDATE_AGENT_TOOL_PARAMETERS_V0 pipeline |
| D3 | What are the exact field definitions for `IN_AGENT_ADMISSION_REQUESTED_V0`? (same as existing IN_ or extended?) | IN_ schema |
| D4 | What storage paths does `STRUCTURE_AGENT_ADMISSION_STORAGE_V0` declare? | STRUCTURE artifact |
| D5 | How does the Python harness submit proposals — CLI payload, HTTP, or direct runtime call? | Transport adapter implementation |
| D6 | What seed data entries (user IDs, license tiers) are required for the five test scenarios? | Seed data |

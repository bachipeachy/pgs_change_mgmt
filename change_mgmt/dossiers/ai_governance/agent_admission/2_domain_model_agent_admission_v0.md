# Stage 2 — Domain Model Discovery: ai_governance / agent_admission
**Stage:** 2 — Domain Model Discovery
**CR:** 1_change_request_agent_admission_v0.md
**Status:** COMPLETE
**Feeds:** Stage 3 — Analysis Loop

---

## 1. Business Entities

### Agent
An autonomous actor that proposes actions against external systems. The agent does not execute tools directly — it submits proposals for governance evaluation.

| Attribute | Description |
|-----------|-------------|
| Identity | Who the agent is (or acts on behalf of) |
| Authority Scope | What tools the agent is permitted to request |
| Runtime | The execution environment from which proposals originate (implementation detail — not a governance entity) |

### Tool Request
The agent's proposal to invoke a specific capability. The governance model evaluates this proposal before any execution occurs.

| Attribute | Description |
|-----------|-------------|
| Tool Name | The capability being requested (from the closed tool registry) |
| Parameters | Tool-specific inputs |
| Requesting Actor | The identity submitting the request |
| Context | Domain context for the request |

### Tool Registry (Closed)
The declared set of tools that may be requested. A tool outside this registry is not filtered — it is structurally absent. The registry is the first admission gate.

Phase 1 registry:
- `web_search`
- `read_file`
- `write_file`

### Authority Surface
The mapping from an actor's authority scope (e.g., license tier) to the tools they are permitted to request. A tool may be declared in the registry but not authorized for a given authority scope.

### Admission Decision
The governance output for a tool request. Binary: **AUTHORIZED** or **DENIED**.

| Outcome | Meaning |
|---------|---------|
| AUTHORIZED | Tool is declared, actor has authority, parameters are valid — execution is permitted |
| DENIED | One or more governance gates rejected the request — execution is blocked |

Denial carries a structured reason:
- `UNDECLARED_TOOL` — tool not in closed registry
- `UNAUTHORIZED_ACTOR` — actor has no valid authority scope
- `UNAUTHORIZED_TOOL` — tool exists but not permitted for this authority scope
- `PARAMETER_VIOLATION` — tool is authorized but parameters fail constraints

### Governance Trace
The deterministic, append-only record of each admission decision. Includes both authorized and denied paths. Carries: tool requested, actor, decision, reason, trace ID.

---

## 2. Business Processes

### Process 1 — Tool Surface Declaration
Before any agent acts, the governed tool surface must be declared:
- Which tools exist (closed registry)
- Which authority scopes may access which tools (authority surface mapping)

This is a configuration-time process, not a runtime process.

### Process 2 — Admission Evaluation
For each agent tool request:
1. Normalize the request (deterministic intent hash)
2. Check: is the tool declared in the closed registry?
3. Check: does the actor have a valid authority scope?
4. Check: does the actor's authority scope permit this tool?
5. Check: do the parameters satisfy declared constraints?
6. Record the decision (authorized or denied) in the governance trace

### Process 3 — Authorized Execution
After a successful admission decision, the agent's runtime executes the tool. **Execution is in the runtime, not in the governance layer.** The governance layer produces an authorized signal; the runtime acts on it.

### Process 4 — Denial Response
After a denied admission decision, the governance layer returns a structured denial to the runtime. The runtime receives: tool requested, denial reason, trace ID.

---

## 3. PPS Baseline — What Already Exists

### Existing Governance Pipeline (agent_governance subdomain)

`WF_GOVERN_AGENT_ACTION_V0` implements exactly the 5-gate admission process described above:

```
Normalize → Check Declared → Resolve Authority → Bind Surface → Validate Parameters
    ↓               ↓                ↓                 ↓                ↓
  hash          registry          tier lookup       tier→tools       param check
    ↓               ↓                ↓                 ↓                ↓
              UNDECLARED_TOOL  UNAUTHORIZED_ACTOR  UNAUTHORIZED_TOOL  PARAMETER_VIOLATION
```

All four denial paths route through `CC_RECORD_DENIED_ACTION_V0` before producing a governed exit. Both `EV_AGENT_ACTION_AUTHORIZED_V0` and `EV_AGENT_ACTION_DENIED_V0` exist.

**The governance pipeline shape is correct and complete for this CR.**

### Existing Intent

`IN_AGENT_ACTION_REQUESTED_V0` declares the full input surface:
- `tool_name` (required)
- `parameters` (required, object)
- `requesting_user_id` (required)
- `domain_context` (required)
- `request_id` (optional)

**The intent schema maps directly to the Tool Request entity.**

### Existing Authority Model

`CC_RESOLVE_LICENSE_TIER_V0` + `CC_BIND_LICENSE_TO_TOOL_SURFACE_V0` implement license-tier authority binding. The tier-to-tool surface mapping exists as a governed lookup.

---

## 4. Gap Analysis — What Is Missing

### Gap 1 — Tool Registry Contains Wrong Tools (CRITICAL)

`CC_CHECK_TOOL_DECLARED_V0` has its closed tool registry hardcoded in the CC pipeline configuration:

```
allowed_set: [READ_RECORD, PROVISION_STANDARD_LICENSE, PROVISION_PREMIUM_LICENSE]
```

These are licensing workflow operations — not agent tools. The Phase 1 tool surface (`web_search`, `read_file`, `write_file`) is not declared anywhere in PPS.

**Impact:** The existing CC cannot govern the agent_admission tool surface without modification.

### Gap 2 — License-to-Tool Surface Maps Wrong Tools (CRITICAL)

`CC_BIND_LICENSE_TO_TOOL_SURFACE_V0` maps license tiers to licensing operations:

```
none:       [READ_RECORD]
standard:   [READ_RECORD, PROVISION_STANDARD_LICENSE]
enterprise: [READ_RECORD, PROVISION_STANDARD_LICENSE, PROVISION_PREMIUM_LICENSE]
```

No mapping exists for `web_search`, `read_file`, `write_file` at any tier.

**Impact:** Even if an agent has a valid license, `CC_BIND_LICENSE_TO_TOOL_SURFACE_V0` will always deny agent tool requests because they are absent from all tier mappings.

### Gap 3 — Actor Identity Semantic (OPEN QUESTION)

The existing model uses `requesting_user_id` — it assumes a human user with a license. For an autonomous agent:

- Option A: The agent *is* the actor — `requesting_user_id` is the agent's identity, and the agent holds its own license tier.
- Option B: The agent acts *on behalf of* a user — `requesting_user_id` is the user's identity, and the license tier belongs to the user.

Phase 1 must choose one. This choice determines whether the authority model requires a new actor type or reuses the existing user-license model.

### Gap 4 — No Transport Adapter (IMPLEMENTATION — NOT DOMAIN)

Nothing exists to route a Python harness action proposal to `IN_AGENT_ACTION_REQUESTED_V0`. This is a transport/integration concern (TI_ layer), not a domain model gap. Noted here for completeness; it does not affect the domain model.

### Gap 5 — Parameter Constraints for Agent Tools (MINOR)

`CC_VALIDATE_TOOL_PARAMETERS_V0` validates parameters against declared constraints. No parameter schemas exist for `web_search`, `read_file`, or `write_file`. Phase 1 needs at minimum a minimal constraint declaration per tool.

---

## 5. Summary: Extend vs. New Subdomain

The governance pipeline architecture — the admission process shape — is **fully present** in `agent_governance`. It was designed for exactly this kind of structural admission control.

What is missing is **domain-specific configuration**: the tool registry, the tier-to-tool surface mapping, and the parameter constraints for agent tools. These configurations are currently baked into CCs that serve the licensing domain.

**Architectural question for Stage 3:**

Does the agent tool surface configuration belong:
- Inside `agent_governance` (same subdomain, new configuration) — makes the existing WF runtime-agnostic by externalizing the tool surface, or
- Inside `agent_admission` (new subdomain, owns the agent-specific tool surface) — clean separation from the licensing-domain CC configurations

This is the subdomain placement question. The answer depends on whether `CC_CHECK_TOOL_DECLARED_V0` and `CC_BIND_LICENSE_TO_TOOL_SURFACE_V0` are designed to be reused with different configurations (generic CCs) or are coupling the tool surface to the licensing domain (domain-specific CCs).

---

## 6. Open Questions for Stage 3

| # | Question | Why It Matters |
|---|----------|---------------|
| Q1 | Are `CC_CHECK_TOOL_DECLARED_V0` and `CC_BIND_LICENSE_TO_TOOL_SURFACE_V0` intended to be generic (reusable with different tool sets) or licensing-specific? | Determines whether new CCs are needed or existing CCs can be reconfigured |
| Q2 | Does the agent actor hold its own authority scope, or does it inherit the user's? | Determines whether a new actor enrollment model is needed |
| Q3 | Can `WF_GOVERN_AGENT_ACTION_V0` be reused as-is (with new CC configurations), or does agent_admission require a new workflow version? | Determines authoring scope |
| Q4 | What parameter constraints are appropriate for Phase 1 tools (`web_search` query length? `read_file` path restrictions? `write_file` path restrictions)? | Required for `CC_VALIDATE_TOOL_PARAMETERS_V0` |

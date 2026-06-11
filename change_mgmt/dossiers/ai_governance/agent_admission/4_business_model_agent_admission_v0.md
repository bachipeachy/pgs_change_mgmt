# Stage 4 — Business Model: ai_governance / agent_admission
**Stage:** 4 — Business Model
**CR:** 1_change_request_agent_admission_v0.md
**Status:** COMPLETE
**Feeds:** Stage 5 — Business Intent

---

## 1. Business Context

Autonomous agents act on behalf of users against external systems. Without structural governance, an agent's authority is implicit — bounded only by what the runtime permits and what operational controls happen to catch. This is supervision, not governance.

The business model for `agent_admission` establishes a different architecture: the agent proposes, governance decides, the runtime executes only what governance admits.

---

## 2. Business Actors

### Autonomous Agent
An actor that proposes tool requests on behalf of a user. The agent does not execute tools directly — it submits proposals through the governance layer and acts on the outcome.

The agent has its own identity. It carries the identity of the user on whose behalf it acts.

### User
The human principal whose authority scope governs what the agent may request. The user's authority tier determines which tools the agent may propose on their behalf.

The user does not need to be present at execution time. Their authority scope is evaluated at proposal time through the governance layer.

### Governance Authority
The structural decision-maker. Evaluates every agent tool proposal against declared policy before execution occurs. Produces a decision — authorized or denied — with a traceable record.

The governance authority does not execute tools. It decides.

### Agent Runtime (Phase 1: Python Harness)
The execution environment. Submits tool proposals to the governance authority. Executes tools only when authorized. Receives and acts on structured denial responses.

The runtime is replaceable. The governance model does not change when the runtime changes.

---

## 3. Business Rules

**Rule 1 — No tool executes without prior admission.**
Every tool invocation must pass through governance before execution. There is no bypass, no ambient permission, no implicit grant.

**Rule 2 — The tool surface is closed.**
Only declared tools may be proposed. A tool not in the governed registry is not filtered — it is structurally absent. The agent cannot reference it.

**Rule 3 — Authority is user-bound.**
Tool access is determined by the user's license tier. The agent inherits the user's authority — it cannot exceed it. An agent acting on behalf of a standard-tier user has standard-tier tool access.

**Rule 4 — Every decision is traceable.**
Both authorized and denied decisions produce a governed record. Governance without a trace is not governance — it is a claim.

**Rule 5 — Denial is structured.**
When admission is denied, the agent receives a structured response: what was denied, why it was denied, and the identifier of the governance decision. The agent can reason about the outcome.

**Rule 6 — Governance is runtime-agnostic.**
The governance model is defined independently of any specific agent runtime. Replacing the runtime does not change the governance policy, the tool surface, the authority model, or the trace structure.

---

## 4. Business Processes

### Process A — Tool Surface Declaration (configuration-time)

Before any agent acts, the governed tool surface must be established:

1. Declare what tools exist (the closed registry)
2. Declare which authority tiers may access which tools (the authority surface)
3. Declare what parameter constraints apply to each tool (the safety boundary)

This is a governance authoring process, not a runtime process. The tool surface does not change at runtime.

**Phase 1 tool surface:**

| Tool | Description | Available To |
|------|-------------|-------------|
| `web_search` | Search the web for information | Standard, Premium, Enterprise |
| `read_file` | Read a file from the filesystem | Standard, Premium, Enterprise |
| `write_file` | Write a file to the filesystem | Premium, Enterprise |

*Note: Exact tier assignments are a governance policy decision confirmed at Design Intent. The above is illustrative.*

### Process B — Admission Evaluation (runtime)

For each agent tool proposal, in sequence:

1. **Normalize** — establish a deterministic identity for the proposal
2. **Registry check** — is the requested tool in the closed registry? If not: denied (undeclared tool)
3. **Authority check** — does the requesting user have an active authority scope? If not: denied (unauthorized actor)
4. **Surface check** — does the user's authority tier permit this tool? If not: denied (unauthorized tool)
5. **Parameter check** — do the proposal's parameters satisfy declared constraints? If not: denied (parameter violation)
6. **Record** — write the governance decision to the trace

If all five checks pass: the proposal is authorized.

### Process C — Authorized Execution (runtime)

After authorization, the agent runtime executes the tool. The governance layer produced the authorization signal; the runtime acts on it. Execution is in the runtime, not in governance.

### Process D — Denial Response (runtime)

After denial, the agent runtime receives a structured denial: tool name, denial reason, decision trace ID. The runtime presents this to the agent, which may retry, escalate, or halt.

---

## 5. Business Outcomes

| Outcome | Trigger | What the Agent Receives |
|---------|---------|-------------------------|
| Authorized | All five admission checks pass | Permission to execute; governance trace ID |
| Denied — Undeclared Tool | Requested tool not in registry | Denial: tool not recognized |
| Denied — Unauthorized Actor | User has no active authority scope | Denial: no authority |
| Denied — Unauthorized Tool | Tool exists but not permitted for this tier | Denial: tool not authorized for authority level |
| Denied — Parameter Violation | Parameters fail declared constraints | Denial: parameter constraint failed |

---

## 6. Business Value

**Structural over operational.** Governance enforces admissibility before execution. It does not monitor after the fact. The agent cannot execute what governance has not admitted.

**Auditability.** Every admission decision — authorized and denied — produces a traceable record. The record is not a log that may be searched; it is a governed artifact produced by the same governance pipeline that made the decision.

**Runtime independence.** The governance model is defined once and applies to any runtime that submits proposals through the governance interface. Phase 1 proves this with a Python harness; Phase 2 demonstrates it with a real agent framework (OpenClaw or equivalent) by replacing the harness without touching governance.

**Authority clarity.** An agent's authority is not implicit in what the runtime allows. It is explicit in the user's governed authority scope. The boundary is declared, not inferred.

---

## 7. What This Model Does Not Cover (Phase 1 Boundary)

| Excluded | Reason |
|----------|--------|
| Agent-to-agent delegation | Multi-agent authority model — future CR |
| Mid-execution suspension or escalation | Requires suspension mechanism — not yet available |
| Multi-agent coordination | Future CR |
| LLM reasoning or planning | PGS governs actions, not reasoning |
| Modifying the agent runtime | Governance wraps the runtime; never enters it |
| Tool execution within the governance layer | Execution is in the runtime; governance decides, not executes |

---

## 8. Authoring Scope Summary

*Preliminary authoring scope — confirmed at Governance Intent and Design Intent stages.*

**New governance concern (new subdomain):** `ai_governance::agent_admission`

The agent tool surface — what tools exist, what authority tiers permit them, what parameters are valid — is governance policy. Governance policy must be declared as governed artifacts. These artifacts need a governing subdomain. `agent_governance` is not the right home (it governs licensing operations). `agent_admission` is the declared subdomain for autonomous agent tool admission governance.

**Reuses without modification:**
- Existing admission workflow topology
- Existing intent schema for tool requests
- Existing events (authorized, denied)
- Existing actor definition (agent, user relationship)
- Existing recording and audit mechanisms
- Existing authority resolution (user license tier)
- Existing pure computation functions
- Existing storage infrastructure

**Authors new:**
- Tool registry for agent tools (3 tools: web_search, read_file, write_file)
- Authority surface mapping (tier → permitted agent tools)
- Parameter constraints for agent tools
- Admission workflow for agent_admission subdomain
- Transport adapter (Python harness → governance intent)
- Seed data for test actors (2 actors: standard-tier user, enterprise-tier user)

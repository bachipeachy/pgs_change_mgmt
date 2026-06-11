# Stage 5 — Business Intent: ai_governance / agent_admission
**Stage:** 5 — Business Intent
**CR:** 1_change_request_agent_admission_v0.md
**Status:** COMPLETE
**Feeds:** Stage 6 — Governance Intent

---

## 1. Intent Statement

Establish a structural governance envelope for autonomous agent tool execution within the `ai_governance` domain, implemented as the new `agent_admission` subdomain.

The governance envelope ensures that every agent tool proposal passes protocol-governed admission before execution occurs, that the tool surface is explicitly declared and closed, that authority is user-bound and license-tier governed, and that every admission decision — authorized or denied — produces a deterministic, traceable record.

---

## 2. Governance Principles This CR Embodies

### Principle 1 — Admissibility Before Execution
An agent may not execute a tool it has not been admitted to use. Governance evaluates admissibility at proposal time, not at execution time. This is structural, not supervisory.

### Principle 2 — Closed Surface, Not Open Filter
The tool surface is declared. Tools outside the declaration are not filtered — they are structurally absent. The agent cannot reference them. This is a stronger guarantee than filtering: there is nothing to bypass.

### Principle 3 — Authority Is Declared, Not Assumed
The agent's authority to invoke a tool derives from the user's governed license tier. Authority is not ambient. It is not inferred from context. It is evaluated explicitly against a declared authority scope at every proposal.

### Principle 4 — Symmetric Traceability
Every governance decision — authorized and denied — produces a traceable record through the same governance mechanism. Governance that only records denials is incomplete. Governance that only records authorizations is unauditable. Both paths produce a trace.

### Principle 5 — Runtime Independence
The governance model is defined independently of any specific agent runtime. The governance envelope does not know or care which runtime is executing. This is the architectural claim this CR proves: PGS can govern a foreign runtime without coupling to it.

---

## 3. Business Commitments

This CR commits to delivering a governance envelope that satisfies all of the following:

| Commitment | Description | Verification |
|------------|-------------|--------------|
| C1 | An agent tool request that is not in the declared registry is denied before execution | Test: undeclared tool → denial with reason UNDECLARED_TOOL |
| C2 | An agent tool request from an actor with no authority scope is denied | Test: no-license actor → denial with reason UNAUTHORIZED_ACTOR |
| C3 | An agent tool request for a tool not permitted by the actor's authority tier is denied | Test: standard-tier actor requests write_file → denial with reason UNAUTHORIZED_TOOL |
| C4 | An agent tool request with parameters that violate declared constraints is denied | Test: parameter violation → denial with reason PARAMETER_VIOLATION |
| C5 | A valid agent tool request — declared tool, active authority, tier-permitted, valid parameters — is authorized | Test: valid standard-tier request → authorization |
| C6 | Every decision (C1–C5) produces a traceable record | Test: all scenario traces are non-empty and contain the decision outcome |
| C7 | The governance model is not modified when the Python harness is replaced by a real agent runtime | Architectural assertion: Phase 2 replacement changes only the transport adapter |

---

## 4. Success Criteria

This CR is complete when:

1. All five test scenarios (C1–C5) execute and produce the expected admission decision
2. All five scenarios produce a deterministic governance trace
3. The same inputs produce the same trace on repeated execution (determinism invariant)
4. The governance model artifacts are independent of the Python harness — replacing the harness changes nothing in the governance layer
5. A future OpenClaw adapter can be added without modifying the governance policy, tool surface, authority model, or trace structure

---

## 5. What This CR Does Not Commit To

| Not Committed | Reason |
|---------------|--------|
| Governing what the LLM reasons | PGS governs actions, not reasoning |
| Governing the runtime's internal behavior | Governance wraps the runtime; it does not enter it |
| Multi-agent authority delegation | Future CR |
| Mid-execution escalation or suspension | Future CR |
| A second tool surface | Phase 1 is intentionally minimal — three tools only |
| Production-grade hardening | This CR proves the architectural model; production hardening is a future concern |

---

## 6. Relationship to Existing Governance

This CR does not replace or modify any existing governance capability.

`agent_governance` continues to govern licensing workflow operations unchanged. The admission workflow it contains is the architectural template that `agent_admission` follows — it is not extended, modified, or shared.

`ai_licensing` continues to govern license provisioning. The authority model it defines (STANDARD, PREMIUM, ENTERPRISE tiers) is the authority model `agent_admission` uses to evaluate tool requests — reused without modification.

`blockchain::identity` continues to govern actor enrollment. The identity infrastructure it provides is what `agent_admission` uses to resolve actor identity — reused without modification.

`agent_admission` owns one new governance concern: the declaration of what tools an autonomous agent may propose, under what authority conditions, and with what parameter constraints.

---

## 7. Phase Relationship

This CR is Phase 1 of a multi-phase capability:

| Phase | Scope | Status |
|-------|-------|--------|
| Phase 1 (this CR) | Single agent, single governance envelope, Python harness runtime, three tools | IN PROGRESS |
| Phase 2 | Replace Python harness with real agent runtime (e.g., OpenClaw adapter) | Future CR — no governance changes required |
| Phase 3 | Multi-agent coordination and federated governance | Future CR |

Phase 2 is explicitly designed to require no governance changes. If Phase 2 requires modifying the governance policy, the tool surface, or the authority model, Phase 1 has failed its architectural claim.

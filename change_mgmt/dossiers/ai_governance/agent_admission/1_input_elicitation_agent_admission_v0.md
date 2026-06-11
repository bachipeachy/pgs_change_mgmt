# Stage 1 — Input Elicitation: ai_governance / agent_admission
**Stage:** 1 — Input Elicitation
**CR:** 1_change_request_agent_admission_v0.md
**Status:** COMPLETE
**Feeds:** Stage 2 — Domain Model Discovery

---

## Part 1 — Problem Statement

The core problem is not unsafe tools.

The core problem is that autonomous agent authority is exercised operationally rather than through protocol-governed admission. Existing approaches supervise behavior after capability has been granted; they do not govern admissibility before execution.

Operational mitigations — system prompts, middleware filters, monitoring dashboards — are structurally insufficient. The agent retains the capability to attempt any action the runtime allows. Governance is advisory. Admissibility is never structurally declared.

PGS governs execution by declaring what is admissible before execution begins. The question this CR answers is whether that structural governance model extends to autonomous agents that propose actions against external systems.

---

## Part 2 — Business Final Outcome

A governed execution envelope in which:

- Agent actions are **proposed**, not executed directly
- **Admissibility** is evaluated through protocol governance before any tool executes
- Agent **authority** is explicit and governed — the agent holds a declared scope; actions outside it are inadmissible
- Every **execution decision** is traceable — both authorized and denied paths produce a governed trace
- **Governance is independent** of any specific agent runtime — the model survives runtime replacement without protocol changes

---

## Part 3 — Current Business Knowledge

### A. Tool Surface (Phase 1)

Three tools. Intentionally small — the objective is to prove protocol-governed admission, not maximize coverage.

| Tool | Description |
|------|-------------|
| `web_search` | Search the web for information |
| `read_file` | Read a file from the filesystem |
| `write_file` | Write a file to the filesystem |

Additional tools (api_call, execute_shell, messaging, browser automation) are explicitly deferred to future CRs.

### B. Authority Model

No new authority model is asserted by this CR.

The analysis loop (Stage 3) will evaluate whether existing authority constructs — including the license tier model in `ai_governance::ai_licensing` (STANDARD, PREMIUM, ENTERPRISE) — are sufficient for tool surface governance. If gaps exist, they surface through Business Model and Governance Intent stages, not by assumption here.

### C. Agent Identity

Assume existing identity infrastructure (`blockchain::identity`) unless Domain Model Discovery or the analysis loop proves otherwise.

This CR governs agent actions, not agent enrollment. Identity is a dependency, not a deliverable.

### D. Phase 1 Runtime

**Minimal Python agent harness.**

A lightweight Python harness that:
- Accepts a script of planned agent actions (simulates agent intent deterministically)
- For each action: routes the tool request through PGS admission
- Executes the tool only if admitted; receives a structured denial if denied
- Produces a deterministic, repeatable governance trace

This runtime choice is implementation detail only. It does not influence governance topology, subdomain placement, or protocol artifact design.

**Planned extension:** After Phase 1 succeeds with the Python harness, an OpenClaw adapter will replace the harness as the action source. The governance layer remains unchanged — this is the proof of runtime-agnosticism.

### E. Denial Behavior

The agent receives a **structured denial response**.

The denial is part of the governed execution trace. It allows the agent runtime to reason about the outcome (retry with different parameters, escalate, halt). Silent blocking provides less governance value and less auditability.

Denial responses must include:
- The tool that was requested
- The reason admission was denied
- The trace ID for the execution decision

---

## Analyst Notes

- **Purity Filter active from this stage forward.** Business concepts only through Stage 5. No artifact family names (CC_, WF_, CS_, CT_) until Stage 6b.
- **Open question for Stage 2:** Does `WF_GOVERN_AGENT_ACTION_V0` already cover the admission concern, or does the Phase 1 scope require capabilities not present in the existing workflow?
- **Open question for Stage 2:** What is the data model for a "tool request" — what fields does the agent submit for admission evaluation?
- **Open question for Stage 3:** Is authority model gap real or is `ai_licensing` sufficient for Phase 1 tool surface governance?

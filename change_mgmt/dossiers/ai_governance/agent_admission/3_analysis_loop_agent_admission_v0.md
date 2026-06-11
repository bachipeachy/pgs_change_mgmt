# Stage 3 — Analysis Loop: ai_governance / agent_admission
**Stage:** 3 — Analysis Loop
**CR:** 1_change_request_agent_admission_v0.md
**Iterations:** 1 (saturated)
**Status:** COMPLETE — saturation achieved
**Feeds:** Stage 4 — Business Model

---

## Iteration 1

### Q1 — Are CC_CHECK_TOOL_DECLARED_V0 and CC_BIND_LICENSE_TO_TOOL_SURFACE_V0 generic or domain-specific?

**Finding: Architecturally generic; data-specifically coupled to the licensing domain.**

Reading the source artifacts directly:

`CC_CHECK_TOOL_DECLARED_V0` — the CC shape is generic (validate set membership). The closed tool set is embedded inline in the CC pipeline declaration:
```
allowed_set: [READ_RECORD, PROVISION_STANDARD_LICENSE, PROVISION_PREMIUM_LICENSE]
```

`CC_BIND_LICENSE_TO_TOOL_SURFACE_V0` — the CC shape is generic (lookup tier → tools, validate membership). The tier-to-tool map is embedded inline:
```
none:       [READ_RECORD]
standard:   [READ_RECORD, PROVISION_STANDARD_LICENSE]
enterprise: [READ_RECORD, PROVISION_STANDARD_LICENSE, PROVISION_PREMIUM_LICENSE]
```

`CC_VALIDATE_TOOL_PARAMETERS_V0` — same pattern. Parameter constraint rules per tool are embedded inline (record_type, id, tier, quantity — all licensing fields).

**PGS doctrine implication:** Governance data lives in governance artifacts, not in external configuration. The tool registry, tier mapping, and parameter constraints embedded in these CCs ARE the governance policy for the licensing domain. They are not configurable at runtime — they are compiled into the snapshot.

**Resolution:** To govern `web_search`, `read_file`, `write_file`, new CC artifacts are required. These new CCs will contain the agent tool surface as their embedded governance policy. They cannot be the same artifacts with different configuration.

**Answer:** New CCs required. The existing CCs must not be modified — they govern the licensing domain. New CCs govern the agent tool surface.

---

### Q2 — Does the agent actor hold its own authority scope, or does it inherit the user's?

**Finding: The existing model is hybrid — agent has identity, user supplies authority.**

`AC_AGENT_V0` (source read):
```yaml
attributes:
  agent_id:     string, required  ← the agent's own identity
  requesting_user_id: string, required  ← the user the agent acts on behalf of
```

`IN_AGENT_ACTION_REQUESTED_V0` uses `requesting_user_id` as the authority lookup key. `CC_RESOLVE_LICENSE_TIER_V0` reads the license tier from the user's license record using that ID.

**Interpretation:** Authority is resolved through the USER's license tier. The agent proposes; the user's authority governs. The agent's own identity (`agent_id`) identifies the proposer but does not independently hold a license.

**Resolution:** No new authority model needed for Phase 1. The existing user-license authority model is sufficient. The Python harness will submit a `requesting_user_id` that maps to an existing licensed user in the seed data.

**Answer:** Agent inherits user's authority. Existing `blockchain::identity` + `ai_licensing` infrastructure serves Phase 1 without modification.

---

### Q3 — Can WF_GOVERN_AGENT_ACTION_V0 be reused as-is, or does agent_admission require a new workflow?

**Finding: New workflow required — because new CCs are required (Q1 resolution).**

`WF_GOVERN_AGENT_ACTION_V0` references the three domain-coupled CCs by FQDN:
- `ai_governance::CC_CHECK_TOOL_DECLARED_V0`
- `ai_governance::CC_BIND_LICENSE_TO_TOOL_SURFACE_V0`
- `ai_governance::CC_VALIDATE_TOOL_PARAMETERS_V0`

Since these CCs contain licensing-domain tool surface data, a new workflow must reference the new agent_admission CCs. The workflow DAG topology is identical — only the CC references change.

**Resolution:** New workflow `WF_GOVERN_AGENT_ADMISSION_V0` referencing new agent_admission CCs. The governance DAG shape is preserved — five gates, four denial paths, symmetric audit trail.

**Answer:** New workflow required. Topology reused; CC references replaced.

---

### Q4 — Parameter constraints for Phase 1 tools

**Finding: Design decision, not a discovery gap. Deferred to Stage 6b.**

The parameter constraint mechanism is proven (`CC_VALIDATE_TOOL_PARAMETERS_V0` with `CT_PURE_VALIDATE_PARAMETER_RULES_V0`). What constraints apply to `web_search`, `read_file`, `write_file` is a governance policy choice, not a structural unknown.

Reasonable defaults for Design Intent (Stage 6b):
- `web_search`: `query` field, string, not_null
- `read_file`: `path` field, string, not_null; no `..` traversal sequences
- `write_file`: `path` field, string, not_null; `content` field, string, not_null; no `..` traversal sequences

These are carried as **design inputs to Stage 6b**, not open discovery questions.

**Answer:** Not a blocker for saturation. Constraints are defined at Design Intent.

---

## Saturation Assessment

**Three-part saturation criterion:**

| Criterion | Status | Evidence |
|-----------|--------|----------|
| No unresolved CRITICALs | SATISFIED | Gap 1 (tool registry) and Gap 2 (tier mapping) both have clear resolution paths: new CCs in new subdomain |
| No open analyst questions | SATISFIED | Q1–Q3 resolved; Q4 deferred to design as a policy choice, not a discovery gap |
| No dependency expansion in last pass | SATISFIED | No new unknowns surfaced; all discovered dependencies already exist in PPS |

**Saturation achieved in 1 iteration.**

---

## Consolidated Findings

### What Already Exists (fully reusable)

| Artifact | Status | Reuse |
|----------|--------|-------|
| Governance pipeline topology (5-gate admission) | EXISTS | REUSE — shape is correct |
| `WF_GOVERN_AGENT_ACTION_V0` | EXISTS | REFERENCE — DAG topology template |
| `IN_AGENT_ACTION_REQUESTED_V0` | EXISTS | REUSE — intent schema fits agent tool requests exactly |
| `EV_AGENT_ACTION_AUTHORIZED_V0` | EXISTS | REUSE |
| `EV_AGENT_ACTION_DENIED_V0` | EXISTS | REUSE |
| `CC_NORMALIZE_AGENT_REQUEST_V0` | EXISTS | REUSE — normalization is domain-agnostic |
| `CC_RESOLVE_LICENSE_TIER_V0` | EXISTS | REUSE — user license resolution is domain-agnostic |
| `CC_RECORD_GOVERNED_ACTION_V0` | EXISTS | REUSE — audit recording is domain-agnostic |
| `CC_RECORD_DENIED_ACTION_V0` | EXISTS | REUSE — denial recording is domain-agnostic |
| `AC_AGENT_V0` | EXISTS | REUSE |
| User license infrastructure (`ai_licensing`) | EXISTS | REUSE — authority model unchanged |
| Identity infrastructure (`blockchain::identity`) | EXISTS | REUSE |
| CT functions (VALIDATE_SET_MEMBERSHIP, LOOKUP, VALIDATE_PARAMETER_RULES) | EXISTS | REUSE |

### What Must Be Authored (new artifacts)

| Artifact | Why New |
|----------|---------|
| `CC_CHECK_AGENT_TOOL_DECLARED_V0` | Tool registry must contain `web_search`, `read_file`, `write_file` — not licensing operations |
| `CC_BIND_AGENT_LICENSE_TO_TOOL_SURFACE_V0` | Tier-to-tool map must reference agent tools — not licensing operations |
| `CC_VALIDATE_AGENT_TOOL_PARAMETERS_V0` | Parameter constraints for agent tools — not licensing fields |
| `WF_GOVERN_AGENT_ADMISSION_V0` | References new agent_admission CCs; topology identical to existing WF |
| Transport adapter (Python harness → `IN_AGENT_ACTION_REQUESTED_V0`) | No integration path exists yet |
| Seed data: agent license facts for test actors | Python harness needs valid `requesting_user_id` entries in license_facts.json |

### Subdomain Placement Decision

**The agent tool surface (what tools exist, what tiers permit them, what parameters are valid) is governance policy. In PGS, governance policy lives in CC artifacts. New governance policy = new CC artifacts. New CC artifacts need a governing subdomain.**

The licensing domain's CC artifacts encode licensing operation policy. The agent admission CC artifacts encode agent tool admission policy. These are distinct governance concerns.

**Decision: NEW subdomain — `ai_governance::agent_admission`**

`agent_governance` continues to own: governance of licensing workflow operations.
`agent_admission` owns: governance of autonomous agent tool requests.

The workflow (`WF_GOVERN_AGENT_ACTION_V0`) and intent (`IN_AGENT_ACTION_REQUESTED_V0`) live in `agent_governance` and are **reused** by the agent_admission execution path through the same intent — no duplication.

---

## Inputs to Stage 4 — Business Model

1. **Governance pipeline shape:** proven, existing, reusable
2. **Authority model:** user license tier, no new model
3. **Tool surface (Phase 1):** `web_search`, `read_file`, `write_file`
4. **Subdomain decision:** `agent_admission` (new) — carries agent tool surface CCs
5. **New artifacts required:** 3 new CCs + 1 new WF + transport adapter + seed data
6. **Existing artifacts reused:** IN, EV, 4 existing CCs, AC, all CT functions, full storage infrastructure
7. **Parameter constraints:** policy decision for Stage 6b

# Stage 7 — Authoring Mandate: ai_governance / agent_admission
**Stage:** 7 — Authoring Mandate
**CR:** 1_change_request_agent_admission_v0.md
**Status:** COMPLETE
**Feeds:** Stage 8 — Authoring Manifest

---

## 1. Mandate Statement

This mandate defines the complete, ordered build sequence for the `ai_governance::agent_admission` subdomain. It is derived directly from the dependency graph in the Design Intent (Stage 6b). Every task listed is mandatory. No task may be deferred or reordered without a CR amendment.

The mandate is structured as three phases: Pre-Authoring, Authoring, and Post-Authoring.

---

## 2. Dependency Graph

### New Artifact Dependencies

| Artifact | Depends On (new artifacts only) |
|----------|--------------------------------|
| `STRUCTURE_AGENT_ADMISSION_STORAGE_V0` | *(none)* |
| `CC_CHECK_AGENT_TOOL_DECLARED_V0` | *(none)* |
| `CC_BIND_AGENT_LICENSE_TO_TOOL_SURFACE_V0` | *(none)* |
| `CC_VALIDATE_AGENT_TOOL_PARAMETERS_V0` | *(none)* |
| `RB_AGENT_ADMISSION_BINDINGS_V0` | `STRUCTURE_AGENT_ADMISSION_STORAGE_V0` |
| `WF_GOVERN_AGENT_ADMISSION_V0` | `CC_CHECK_AGENT_TOOL_DECLARED_V0`, `CC_BIND_AGENT_LICENSE_TO_TOOL_SURFACE_V0`, `CC_VALIDATE_AGENT_TOOL_PARAMETERS_V0`, `RB_AGENT_ADMISSION_BINDINGS_V0` |
| `IN_AGENT_ADMISSION_REQUESTED_V0` | `WF_GOVERN_AGENT_ADMISSION_V0` |

### External Dependencies (existing — no modification required)

| Artifact | FQDN | Owner Subdomain |
|----------|------|-----------------|
| Set membership check | `capability_transforms::CT_PURE_VALIDATE_SET_MEMBERSHIP_V0` | platform |
| Lookup | `capability_transforms::CT_PURE_LOOKUP_V0` | platform |
| Parameter rules | `capability_transforms::CT_PURE_VALIDATE_PARAMETER_RULES_V0` | platform |
| Mutable JSON | `capability_side_effects::CS_MUTABLE_JSON_V0` | platform |
| Registry | `capability_side_effects::CS_REGISTRY_V0` | platform |
| Append-only JSONL | `capability_side_effects::CS_APPENDONLY_JSONL_V0` | platform |
| Normalize | `ai_governance::CC_NORMALIZE_AGENT_REQUEST_V0` | agent_governance |
| License tier resolve | `ai_governance::CC_RESOLVE_LICENSE_TIER_V0` | agent_governance |
| Record authorized | `ai_governance::CC_RECORD_GOVERNED_ACTION_V0` | agent_governance |
| Record denied | `ai_governance::CC_RECORD_DENIED_ACTION_V0` | agent_governance |
| Authorized event | `ai_governance::EV_AGENT_ACTION_AUTHORIZED_V0` | agent_governance |
| Denied event | `ai_governance::EV_AGENT_ACTION_DENIED_V0` | agent_governance |
| Agent actor | `ai_governance::AC_AGENT_V0` | agent_governance |

---

## 3. Topological Build Layers

| Layer | Artifacts | Parallelizable |
|-------|-----------|---------------|
| L0 | `STRUCTURE_AGENT_ADMISSION_STORAGE_V0`, `CC_CHECK_AGENT_TOOL_DECLARED_V0`, `CC_BIND_AGENT_LICENSE_TO_TOOL_SURFACE_V0`, `CC_VALIDATE_AGENT_TOOL_PARAMETERS_V0` | Yes — all four have no new-artifact deps |
| L1 | `RB_AGENT_ADMISSION_BINDINGS_V0` | After L0 (depends on STRUCTURE_) |
| L2 | `WF_GOVERN_AGENT_ADMISSION_V0` | After L1 (depends on all 3 CCs + RB_) |
| L3 | `IN_AGENT_ADMISSION_REQUESTED_V0` | After L2 (binds to WF_) |

---

## 4. Phase A — Pre-Authoring

These steps MUST be completed before any new protocol artifact is authored. The compiler cannot discover `agent_admission` until step A1 is complete.

### A1 — Register agent_admission in the Constitutional Discovery Layer

**File:** `pgs_governance/registry/FB_CONSTITUTION/structures/STRUCTURE_DISCOVERY_V0.md`

**Change:** Add `agent_admission` to the `AI_GOVERNANCE.allowed_domains` list.

**Current state:**
```yaml
AI_GOVERNANCE:
  registry_module: pgs_ai_governance.registry
  module_path_pattern: "{registry_module}.{domain}"
  layer_category: domain
  allowed_domains:
    - ai_licensing
    - agent_governance
```

**Required state:**
```yaml
AI_GOVERNANCE:
  registry_module: pgs_ai_governance.registry
  module_path_pattern: "{registry_module}.{domain}"
  layer_category: domain
  allowed_domains:
    - ai_licensing
    - agent_governance
    - agent_admission
```

**Why this is the prerequisite:** `STRUCTURE_DISCOVERY_V0` is the constitutional declaration of which subdomains exist in the `AI_GOVERNANCE` layer. The compiler resolves artifact paths via `{registry_module}.{domain}` — which produces `pgs_ai_governance.registry.agent_admission`. Without this entry, the compiler cannot discover any artifact in the new subdomain. This change must precede all authoring.

**Note:** This modifies a constitutional governance artifact in `pgs_governance`. It is a one-line addition to the `allowed_domains` list — minimal, bounded, non-breaking.

### A2 — Create registry directory structure

**Location:** `pgs_ai_governance/pgs_ai_governance/registry/agent_admission/`

Create the following subdirectories (mirrors `agent_governance` layout):
```
registry/agent_admission/
  capability_contracts/
  intents/
  layers/
  runtime_bindings/
  workflows/
```

No `actors/` or `events/` directories required — agent_admission reuses these from agent_governance without modification.

---

## 5. Phase B — Authoring (Mandated Sequence)

All artifact locations are relative to `pgs_ai_governance/pgs_ai_governance/`.

### B1 — Layer 0: Author in any order (no inter-dependencies)

#### B1.1 — STRUCTURE_AGENT_ADMISSION_STORAGE_V0

**File:** `registry/agent_admission/layers/STRUCTURE_AGENT_ADMISSION_STORAGE_V0.md`

**Specification source:** Design Intent §6 — Artifact Specifications, item 6

**Constraint:** Must declare three entity stores:
- `LICENSE_FACTS` — read-only, path `ai_governance/ai_licensing/license_facts.json`
- `GOVERNANCE_ACTIONS` — read-write, path `ai_governance/agent_admission/governance_actions.json`
- `GOVERNANCE_AUDIT` — append-only, path `ai_governance/agent_admission/governance_audit.jsonl`

**Isolation rules to encode:**
- `LICENSE_FACTS` is read-only — agent_admission may not mutate license facts
- `GOVERNANCE_AUDIT` is append-only — admission audit records are immutable
- `GOVERNANCE_ACTIONS` is scoped to agent_admission — no cross-subdomain writes

#### B1.2 — CC_CHECK_AGENT_TOOL_DECLARED_V0

**File:** `registry/agent_admission/capability_contracts/CC_CHECK_AGENT_TOOL_DECLARED_V0.md`

**Specification source:** Design Intent §6, item 3

**Constraint:** `allowed_set` MUST contain exactly `[web_search, read_file, write_file]`. Any other value is a governance policy violation.

**Transform reference:** `capability_transforms::CT_PURE_VALIDATE_SET_MEMBERSHIP_V0` (existing — no modification)

#### B1.3 — CC_BIND_AGENT_LICENSE_TO_TOOL_SURFACE_V0

**File:** `registry/agent_admission/capability_contracts/CC_BIND_AGENT_LICENSE_TO_TOOL_SURFACE_V0.md`

**Specification source:** Design Intent §6, item 4

**Constraint:** Tier mapping MUST be:
- `standard` → `[web_search, read_file]`
- `enterprise` → `[web_search, read_file, write_file]`

No `premium` tier entry — Phase 1 tool surface does not include premium. Any actor with a `premium` tier that arrives at this CC will receive VIOLATION (tier not in map → unauthorized).

**Transform references:** `CT_PURE_LOOKUP_V0`, `CT_PURE_VALIDATE_SET_MEMBERSHIP_V0` (both existing)

#### B1.4 — CC_VALIDATE_AGENT_TOOL_PARAMETERS_V0

**File:** `registry/agent_admission/capability_contracts/CC_VALIDATE_AGENT_TOOL_PARAMETERS_V0.md`

**Specification source:** Design Intent §6, item 5

**Constraint:** Parameter rule map MUST be:
- `web_search` → `[{field: query, op: not_null}]`
- `read_file` → `[{field: path, op: not_null}]`
- `write_file` → `[{field: path, op: not_null}, {field: content, op: not_null}]`

**Transform references:** `CT_PURE_LOOKUP_V0`, `CT_PURE_VALIDATE_PARAMETER_RULES_V0` (both existing)

---

### B2 — Layer 1: After B1 complete

#### B2.1 — RB_AGENT_ADMISSION_BINDINGS_V0

**File:** `registry/agent_admission/runtime_bindings/RB_AGENT_ADMISSION_BINDINGS_V0.md`

**Specification source:** Design Intent §6, item 7

**Prerequisite:** `STRUCTURE_AGENT_ADMISSION_STORAGE_V0` (B1.1) must be authored first — this artifact references it by FQDN.

**Constraint:** Storage paths MUST match STRUCTURE declarations exactly:
- Registry path: `{{module_data_root}}/ai_governance/agent_admission/governance_actions.json`
- CS_MUTABLE_JSON_V0 serves LICENSE_FACTS in read-only mode
- CS_APPENDONLY_JSONL_V0 serves GOVERNANCE_AUDIT

---

### B3 — Layer 2: After B2 complete

#### B3.1 — WF_GOVERN_AGENT_ADMISSION_V0

**File:** `registry/agent_admission/workflows/WF_GOVERN_AGENT_ADMISSION_V0.md`

**Specification source:** Design Intent §6, item 2

**Prerequisites:** B1.2, B1.3, B1.4 (all three new CCs), B2.1 (RB_) must be authored first.

**Constraint:** DAG topology must be identical to `WF_GOVERN_AGENT_ACTION_V0` — 5 gate nodes, 4 denial audit paths, 1 authorized path. Any structural deviation is a governance invariant violation.

**Subdomain field:** MUST declare `subdomain: agent_admission` — this governs trace directory routing.

**Runtime binding field:** MUST reference `ai_governance::RB_AGENT_ADMISSION_BINDINGS_V0`.

**CC references:** All three new CCs (check, bind, validate) plus four reused CCs (normalize, resolve, record_governed, record_denied) from agent_governance.

---

### B4 — Layer 3: After B3 complete

#### B4.1 — IN_AGENT_ADMISSION_REQUESTED_V0

**File:** `registry/agent_admission/intents/IN_AGENT_ADMISSION_REQUESTED_V0.md`

**Specification source:** Design Intent §6, item 1

**Prerequisite:** `WF_GOVERN_AGENT_ADMISSION_V0` (B3.1) must be authored first — this artifact binds to it.

**Constraint:** Schema fields MUST be identical to `IN_AGENT_ACTION_REQUESTED_V0`:
- `tool_name`: string, required
- `parameters`: object, required
- `requesting_user_id`: string, required
- `domain_context`: string, required
- `request_id`: string, optional

The ONLY difference from the existing IN_ artifact is the workflow binding: `WF_GOVERN_AGENT_ADMISSION_V0`.

**Domain extension:** `pgs.governance.agent.admission`

---

## 6. Phase C — Post-Authoring

These steps execute after all seven protocol artifacts are authored and committed to `pgs_ai_governance`.

### C1 — Compile AI Governance domain (Phase A)

```bash
cd ~/pgs/pgs_compiler
python -m pgs_compiler.cli compile --structure STRUCTURE_BUILD_AI_GOVERNANCE_CONFIG_V0
```

Expected outcome: all seven new artifacts discover, validate, and materialize without error. Compiler output confirms `agent_admission` subdomain artifacts in canonical output.

### C2 — Compile vocabulary aggregate (Phase B)

```bash
python -m pgs_compiler.cli compile --structure STRUCTURE_BUILD_VOCABULARY_AGGREGATE_V0
```

Expected outcome: `agent_admission` vocabulary entries present in aggregate.

### C3 — Full build sync to workspace

```bash
python -m pgs_compiler.cli build --workspace /abs/path/to/pgs_workspace
```

Expected outcome: `protocol_snapshot/` updated with all seven new artifacts. `protocol_snapshot/artifacts/workflows/ai_governance__WF_GOVERN_AGENT_ADMISSION_V0.json` exists.

### C4 — Author testbed

**Location:** `pgs_ai_governance/pgs_ai_governance/testbed/agent_admission/`

Create the following structure:
```
testbed/agent_admission/
  README.md
  test_payloads/
    01_web_search_authorized.json
    02_no_license.json
    03_standard_requests_write.json
    04_enterprise_write_authorized.json
    05_undeclared_tool.json
    06_parameter_violation.json
```

**Seed data:** No new seed_data directory. Reuse `testbed/agent_governance/seed_data/license_facts.json` — existing entries `EMP_STD_001`, `EMP_ENT_001`, `EMP_NONE_001` provide all required test actor profiles.

**Payload specifications:** All six payloads are fully specified in Design Intent §Test Scenario Specifications.

**README content:** Run instructions following the `agent_governance` README pattern — `pgs_runtime run` invocation per scenario, trace examine command, expected outcome per scenario.

### C5 — Execute all six test scenarios

Run each payload in sequence:

```bash
source .venv/bin/activate

# Scenario 01 — authorized: standard user, web_search
pgs_runtime run \
  --wf ai_governance::WF_GOVERN_AGENT_ADMISSION_V0 \
  --payload testbed/agent_admission/test_payloads/01_web_search_authorized.json \
  --data-root $PGS_DATA_ROOT \
  --workspace $PGS_WORKSPACE

# Scenario 02 — denied: no license
# Scenario 03 — denied: standard requests write_file
# Scenario 04 — authorized: enterprise user, write_file
# Scenario 05 — denied: undeclared tool
# Scenario 06 — denied: parameter violation (write_file, missing content)
```

### C6 — Verify all six traces

For each scenario, verify:
1. Trace file exists at `traces/ai_governance/agent_admission/<TRACE_ID>/`
2. Trace contains the expected decision (AUTHORIZED or DENIED)
3. Denial traces contain the correct `denial_reason` field
4. `data/ai_governance/agent_admission/governance_audit.jsonl` contains an entry for each execution
5. Scenarios 01 and 04 produce entries in `governance_actions.json`

### C7 — Verify determinism

Re-run scenario 01 with the same payload. Verify:
- Same `TRACE_ID` produced (identical inputs → identical trace)
- Runtime exits with `ALREADY_EXISTS` (idempotency guard in CC_RECORD_GOVERNED_ACTION_V0)
- No duplicate entry in `governance_audit.jsonl`

---

## 7. Governance Boundary Assertions (Mandatory Verification)

After Phase C, verify these negative assertions hold:

| Assertion | Verification |
|-----------|-------------|
| `agent_governance` artifacts unmodified | `git diff pgs_ai_governance/pgs_ai_governance/registry/agent_governance/` → empty |
| `ai_licensing` artifacts unmodified | `git diff pgs_ai_governance/pgs_ai_governance/registry/ai_licensing/` → empty |
| `license_facts.json` unmodified | seed data unchanged; no new entries added |
| No new CT_ or CS_ artifacts authored | Platform capability layer untouched |
| STRUCTURE_DISCOVERY_V0 change is the only `pgs_governance` modification | `git diff pgs_governance/` → only the one-line `allowed_domains` addition |

---

## 8. Build Sequence Summary

```
A1  Add agent_admission to STRUCTURE_DISCOVERY_V0 (pgs_governance)
A2  Create agent_admission registry directory structure (pgs_ai_governance)
    │
    ├── B1.1  STRUCTURE_AGENT_ADMISSION_STORAGE_V0
    ├── B1.2  CC_CHECK_AGENT_TOOL_DECLARED_V0          ← parallelizable with B1.1, B1.3, B1.4
    ├── B1.3  CC_BIND_AGENT_LICENSE_TO_TOOL_SURFACE_V0 ← parallelizable
    ├── B1.4  CC_VALIDATE_AGENT_TOOL_PARAMETERS_V0     ← parallelizable
    │
    └── B2.1  RB_AGENT_ADMISSION_BINDINGS_V0           ← after B1.1
              │
              └── B3.1  WF_GOVERN_AGENT_ADMISSION_V0   ← after B1.2, B1.3, B1.4, B2.1
                        │
                        └── B4.1  IN_AGENT_ADMISSION_REQUESTED_V0  ← after B3.1
    │
    ├── C1    Compile STRUCTURE_BUILD_AI_GOVERNANCE_CONFIG_V0
    ├── C2    Compile STRUCTURE_BUILD_VOCABULARY_AGGREGATE_V0
    ├── C3    Full build sync to pgs_workspace
    ├── C4    Author testbed (README + 6 payloads)
    ├── C5    Execute 6 test scenarios
    ├── C6    Verify 6 traces + governance_audit.jsonl
    └── C7    Verify determinism (scenario 01 re-run)
```

---

## 9. Completion Criterion

This mandate is satisfied when:

1. All seven protocol artifacts are authored, compiled, and present in `protocol_snapshot/`
2. All six test scenarios execute and produce the expected admission decision
3. All six traces are non-empty and contain the correct decision outcome
4. The determinism invariant holds (scenario 01 re-run → same TRACE_ID)
5. No existing artifact in `agent_governance`, `ai_licensing`, or the platform capability layer was modified

At that point, Business Commitment C7 is also satisfied by construction: the governance model was not modified to accommodate the Python harness — the harness adapted to the governance interface.

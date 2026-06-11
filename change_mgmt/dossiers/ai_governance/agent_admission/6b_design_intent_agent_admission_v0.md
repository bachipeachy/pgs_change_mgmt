# Stage 6b — Design Intent: ai_governance / agent_admission
**Stage:** 6b — Design Intent
**CR:** 1_change_request_agent_admission_v0.md
**Status:** COMPLETE
**Feeds:** Stage 7 — Authoring Mandate

---

## Design Question Resolutions

### D1 — Tier-to-Tool Mapping

| License Tier | Permitted Agent Tools |
|---|---|
| `none` (absent from license_facts) | (no tools — UNAUTHORIZED_ACTOR) |
| `standard` | `web_search`, `read_file` |
| `enterprise` | `web_search`, `read_file`, `write_file` |

Rationale: `write_file` requires enterprise tier — it is a higher-trust operation (mutates the filesystem). `web_search` and `read_file` are read-oriented and appropriate for standard tier. This creates a clean UNAUTHORIZED_TOOL proof path: a standard-tier agent requesting `write_file` is denied.

### D2 — Parameter Constraints Per Tool

| Tool | Field | Op | Value |
|---|---|---|---|
| `web_search` | `query` | `not_null` | — |
| `read_file` | `path` | `not_null` | — |
| `write_file` | `path` | `not_null` | — |
| `write_file` | `content` | `not_null` | — |

Violation test: submit `write_file` with `content` field absent → PARAMETER_VIOLATION.

Rationale: Constraints are minimal for Phase 1 — the goal is to prove the governance mechanism, not to build production parameter policy. Path traversal constraints (`..` restriction) are a V1 concern.

### D3 — IN_ Schema

`IN_AGENT_ADMISSION_REQUESTED_V0` uses the identical schema as `IN_AGENT_ACTION_REQUESTED_V0`:
- `tool_name`: string, required
- `parameters`: object, required
- `requesting_user_id`: string, required
- `domain_context`: string, required
- `request_id`: string, optional

The only difference is the workflow binding: `WF_GOVERN_AGENT_ADMISSION_V0`.
Domain extension: `pgs.governance.agent.admission`

### D4 — Storage Paths

| Entity | Path | Access |
|---|---|---|
| LICENSE_FACTS | `ai_governance/ai_licensing/license_facts.json` | READ-ONLY (shared with agent_governance) |
| GOVERNANCE_ACTIONS | `ai_governance/agent_admission/governance_actions.json` | READ-WRITE |
| GOVERNANCE_AUDIT | `ai_governance/agent_admission/governance_audit.jsonl` | APPEND-ONLY |

### D5 — Python Harness Integration

The Python harness follows the existing agent_governance testbed pattern exactly:
- CLI invocation: `pgs_runtime run --wf ai_governance::WF_GOVERN_AGENT_ADMISSION_V0 --payload <file> --data-root $PGS_DATA_ROOT --workspace $PGS_WORKSPACE`
- No custom transport adapter — payload JSON submitted directly to pgs_runtime CLI
- One JSON payload file per test scenario
- Post-run: examine trace + inspect `governance_audit.jsonl`

The harness is a testbed README + payload files, not a new Python class. This follows the existing proven pattern.

### D6 — Seed Data

Reuse existing `agent_governance` seed users — no new entries needed:

| User ID | License Status | Tier |
|---|---|---|
| `EMP_STD_001` | active | standard |
| `EMP_ENT_001` | active | enterprise |
| `EMP_NONE_001` | *(absent from license_facts)* | none |

The existing `license_facts.json` (already in `pgs_workspace/seeds/`) provides all three test actor profiles.

---

## Artifact Specifications

### 1. IN_AGENT_ADMISSION_REQUESTED_V0

**Location:** `pgs_ai_governance/registry/agent_admission/intents/IN_AGENT_ADMISSION_REQUESTED_V0.md`

```yaml
in_code: IN_AGENT_ADMISSION_REQUESTED_V0
version: v0
governed_by: fb.topology::CONSTITUTION_INTENT_V0

core:
  summary: Request governance admission of an autonomous agent tool proposal
  workflow: WF_GOVERN_AGENT_ADMISSION_V0

  inputs:
    tool_name:
      type: string
      required: true
      description: Requested tool identifier from closed agent tool registry
    parameters:
      type: object
      required: true
      description: Tool-specific parameter key-value map
    requesting_user_id:
      type: string
      required: true
      description: Identity of the user on whose behalf the agent acts
    domain_context:
      type: string
      required: true
      description: Domain context for the request
    request_id:
      type: string
      required: false
      description: Client-provided request correlation ID

  outcomes:
    ACK:
      description: Admission request accepted for governance evaluation
    NACK:
      description: Admission request rejected at intent gate

extensions:
  domain: pgs.governance.agent.admission
```

---

### 2. WF_GOVERN_AGENT_ADMISSION_V0

**Location:** `pgs_ai_governance/registry/agent_admission/workflows/WF_GOVERN_AGENT_ADMISSION_V0.md`

DAG topology: identical to `WF_GOVERN_AGENT_ACTION_V0`. CC references replaced with agent_admission variants.

```yaml
wf_code: WF_GOVERN_AGENT_ADMISSION_V0
version: v0
governed_by: fb.topology::CONSTITUTION_WORKFLOW_V0
runtime_binding: ai_governance::RB_AGENT_ADMISSION_BINDINGS_V0
subdomain: agent_admission

core:
  summary: Protocol-governed admission of autonomous agent tool proposals
  start_node: IN_AGENT_ADMISSION_REQUESTED_V0

  nodes:
    IN_AGENT_ADMISSION_REQUESTED_V0:
      type: IN
      code: IN_AGENT_ADMISSION_REQUESTED_V0
      next:
        ACK: CC_NORMALIZE_AGENT_REQUEST_V0
        NACK: EXIT_REJECTED

    CC_NORMALIZE_AGENT_REQUEST_V0:
      type: CC
      code: CC_NORMALIZE_AGENT_REQUEST_V0
      inputs:
        tool_name: $.payload.tool_name
        requesting_user_id: $.payload.requesting_user_id
        domain_context: $.payload.domain_context
      next:
        SUCCESS: CC_CHECK_AGENT_TOOL_DECLARED_V0
        VIOLATION: EXIT_ERROR

    CC_CHECK_AGENT_TOOL_DECLARED_V0:
      type: CC
      code: CC_CHECK_AGENT_TOOL_DECLARED_V0
      inputs:
        tool_name: $.payload.tool_name
      next:
        SUCCESS: CC_RESOLVE_LICENSE_TIER_V0
        VIOLATION: CC_AUDIT_UNDECLARED_TOOL

    CC_RESOLVE_LICENSE_TIER_V0:
      type: CC
      code: CC_RESOLVE_LICENSE_TIER_V0
      inputs:
        requesting_user_id: $.payload.requesting_user_id
      next:
        SUCCESS: CC_BIND_AGENT_LICENSE_TO_TOOL_SURFACE_V0
        NOT_FOUND: CC_AUDIT_UNAUTHORIZED_ACTOR
        VIOLATION: CC_AUDIT_UNAUTHORIZED_ACTOR
        BACKEND_ERROR: EXIT_ERROR

    CC_BIND_AGENT_LICENSE_TO_TOOL_SURFACE_V0:
      type: CC
      code: CC_BIND_AGENT_LICENSE_TO_TOOL_SURFACE_V0
      inputs:
        tool_name: $.payload.tool_name
        license_tier: $.results.CC_RESOLVE_LICENSE_TIER_V0.license_tier
      next:
        SUCCESS: CC_VALIDATE_AGENT_TOOL_PARAMETERS_V0
        VIOLATION: CC_AUDIT_UNAUTHORIZED_TOOL

    CC_VALIDATE_AGENT_TOOL_PARAMETERS_V0:
      type: CC
      code: CC_VALIDATE_AGENT_TOOL_PARAMETERS_V0
      inputs:
        tool_name: $.payload.tool_name
        parameters: $.payload.parameters
      next:
        SUCCESS: CC_RECORD_GOVERNED_ACTION_V0
        VIOLATION: CC_AUDIT_PARAMETER_VIOLATION

    CC_RECORD_GOVERNED_ACTION_V0:
      type: CC
      code: CC_RECORD_GOVERNED_ACTION_V0
      inputs:
        tool_name: $.payload.tool_name
        parameters: $.payload.parameters
        requesting_user_id: $.payload.requesting_user_id
        license_tier: $.results.CC_RESOLVE_LICENSE_TIER_V0.license_tier
        domain_context: $.payload.domain_context
        intent_hash: $.results.CC_NORMALIZE_AGENT_REQUEST_V0.intent_hash
      next:
        SUCCESS: EXIT_SUCCESS
        ALREADY_EXISTS: EXIT_SUCCESS
        VIOLATION: EXIT_ERROR
        BACKEND_ERROR: EXIT_ERROR

    CC_AUDIT_UNDECLARED_TOOL:
      type: CC
      code: CC_RECORD_DENIED_ACTION_V0
      inputs:
        tool_name: $.payload.tool_name
        requesting_user_id: $.payload.requesting_user_id
        domain_context: $.payload.domain_context
        denial_reason: UNDECLARED_TOOL
      next:
        SUCCESS: EXIT_UNDECLARED_TOOL
        VIOLATION: EXIT_ERROR
        BACKEND_ERROR: EXIT_ERROR

    CC_AUDIT_UNAUTHORIZED_ACTOR:
      type: CC
      code: CC_RECORD_DENIED_ACTION_V0
      inputs:
        tool_name: $.payload.tool_name
        requesting_user_id: $.payload.requesting_user_id
        domain_context: $.payload.domain_context
        denial_reason: UNAUTHORIZED_ACTOR
      next:
        SUCCESS: EXIT_UNAUTHORIZED_ACTOR
        VIOLATION: EXIT_ERROR
        BACKEND_ERROR: EXIT_ERROR

    CC_AUDIT_UNAUTHORIZED_TOOL:
      type: CC
      code: CC_RECORD_DENIED_ACTION_V0
      inputs:
        tool_name: $.payload.tool_name
        requesting_user_id: $.payload.requesting_user_id
        domain_context: $.payload.domain_context
        denial_reason: UNAUTHORIZED_TOOL
      next:
        SUCCESS: EXIT_UNAUTHORIZED_TOOL
        VIOLATION: EXIT_ERROR
        BACKEND_ERROR: EXIT_ERROR

    CC_AUDIT_PARAMETER_VIOLATION:
      type: CC
      code: CC_RECORD_DENIED_ACTION_V0
      inputs:
        tool_name: $.payload.tool_name
        requesting_user_id: $.payload.requesting_user_id
        domain_context: $.payload.domain_context
        denial_reason: PARAMETER_VIOLATION
      next:
        SUCCESS: EXIT_PARAMETER_VIOLATION
        VIOLATION: EXIT_ERROR
        BACKEND_ERROR: EXIT_ERROR

    EXIT_SUCCESS:
      type: EXIT
      reason: COMPLETED
      emit: EV_AGENT_ACTION_AUTHORIZED_V0

    EXIT_UNDECLARED_TOOL:
      type: EXIT
      reason: COMPLETED
      emit: EV_AGENT_ACTION_DENIED_V0

    EXIT_UNAUTHORIZED_ACTOR:
      type: EXIT
      reason: COMPLETED
      emit: EV_AGENT_ACTION_DENIED_V0

    EXIT_UNAUTHORIZED_TOOL:
      type: EXIT
      reason: COMPLETED
      emit: EV_AGENT_ACTION_DENIED_V0

    EXIT_PARAMETER_VIOLATION:
      type: EXIT
      reason: COMPLETED
      emit: EV_AGENT_ACTION_DENIED_V0

    EXIT_ERROR:
      type: EXIT
      reason: FAILED

    EXIT_REJECTED:
      type: EXIT
      reason: EXITED
```

---

### 3. CC_CHECK_AGENT_TOOL_DECLARED_V0

**Location:** `pgs_ai_governance/registry/agent_admission/capability_contracts/CC_CHECK_AGENT_TOOL_DECLARED_V0.md`

```yaml
cc_code: CC_CHECK_AGENT_TOOL_DECLARED_V0
version: v0
governed_by: fb.topology::CONSTITUTION_CAPABILITY_CONTRACT_V0

core:
  summary: Verify requested tool exists in the closed autonomous agent tool registry

  inputs:
    tool_name:
      type: string
      required: true

  outputs:
    is_declared:
      type: boolean

  result_status_contract:
    allowed: [SUCCESS, VIOLATION]
    on_input_failure: VIOLATION

  pipeline:
    - step: check_agent_tool_declared
      transform: capability_transforms::CT_PURE_VALIDATE_SET_MEMBERSHIP_V0
      inputs:
        value: $.inputs.tool_name
        allowed_set:
          - web_search
          - read_file
          - write_file
      outputs:
        is_declared: $.capability_result.is_member
      result_surface: [SUCCESS, VIOLATION]
      on_result:
        SUCCESS: continue
        VIOLATION: exit

extensions:
  description: Phase 1 agent tool surface — web_search, read_file, write_file
```

---

### 4. CC_BIND_AGENT_LICENSE_TO_TOOL_SURFACE_V0

**Location:** `pgs_ai_governance/registry/agent_admission/capability_contracts/CC_BIND_AGENT_LICENSE_TO_TOOL_SURFACE_V0.md`

```yaml
cc_code: CC_BIND_AGENT_LICENSE_TO_TOOL_SURFACE_V0
version: v0
governed_by: fb.topology::CONSTITUTION_CAPABILITY_CONTRACT_V0

core:
  summary: Map user license tier to permitted agent tool surface

  inputs:
    tool_name:
      type: string
      required: true
    license_tier:
      type: string
      required: true

  outputs:
    allowed_tools:
      type: array
    is_authorized:
      type: boolean

  result_status_contract:
    allowed: [SUCCESS, VIOLATION]
    on_input_failure: VIOLATION

  pipeline:
    - step: lookup_tier_tools
      transform: capability_transforms::CT_PURE_LOOKUP_V0
      inputs:
        key: $.inputs.license_tier
        map:
          standard:
            - web_search
            - read_file
          enterprise:
            - web_search
            - read_file
            - write_file
      outputs:
        allowed_tools: $.capability_result.result
      result_surface: [SUCCESS, VIOLATION]
      on_result:
        SUCCESS: continue
        VIOLATION: exit

    - step: validate_tool_membership
      transform: capability_transforms::CT_PURE_VALIDATE_SET_MEMBERSHIP_V0
      inputs:
        value: $.inputs.tool_name
        allowed_set: $.results.lookup_tier_tools.allowed_tools
      outputs:
        is_authorized: $.capability_result.is_member
        allowed_tools: $.results.lookup_tier_tools.allowed_tools
      result_surface: [SUCCESS, VIOLATION]
      on_result:
        SUCCESS: continue
        VIOLATION: exit

extensions:
  description: standard → web_search + read_file; enterprise → web_search + read_file + write_file
```

---

### 5. CC_VALIDATE_AGENT_TOOL_PARAMETERS_V0

**Location:** `pgs_ai_governance/registry/agent_admission/capability_contracts/CC_VALIDATE_AGENT_TOOL_PARAMETERS_V0.md`

```yaml
cc_code: CC_VALIDATE_AGENT_TOOL_PARAMETERS_V0
version: v0
governed_by: fb.topology::CONSTITUTION_CAPABILITY_CONTRACT_V0

core:
  summary: Enforce declared parameter constraints for authorized agent tools

  inputs:
    tool_name:
      type: string
      required: true
    parameters:
      type: object
      required: true

  outputs:
    rules:
      type: array
    validation_result:
      type: object

  result_status_contract:
    allowed: [SUCCESS, VIOLATION]
    on_input_failure: VIOLATION

  pipeline:
    - step: lookup_parameter_rules
      transform: capability_transforms::CT_PURE_LOOKUP_V0
      inputs:
        key: $.inputs.tool_name
        map:
          web_search:
            - field: query
              op: not_null
          read_file:
            - field: path
              op: not_null
          write_file:
            - field: path
              op: not_null
            - field: content
              op: not_null
      outputs:
        rules: $.capability_result.result
      result_surface: [SUCCESS, VIOLATION]
      on_result:
        SUCCESS: continue
        VIOLATION: exit

    - step: validate_parameters
      transform: capability_transforms::CT_PURE_VALIDATE_PARAMETER_RULES_V0
      inputs:
        parameters: $.inputs.parameters
        rules: $.results.lookup_parameter_rules.rules
      outputs:
        validation_result: $.capability_result.value
        rules: $.results.lookup_parameter_rules.rules
      result_surface: [SUCCESS, VIOLATION]
      on_result:
        SUCCESS: continue
        VIOLATION: exit

extensions:
  description: Phase 1 constraints — required fields only; path traversal constraints deferred to V1
```

---

### 6. STRUCTURE_AGENT_ADMISSION_STORAGE_V0

**Location:** `pgs_ai_governance/registry/agent_admission/layers/STRUCTURE_AGENT_ADMISSION_STORAGE_V0.md`

```yaml
structure_code: STRUCTURE_AGENT_ADMISSION_STORAGE_V0
version: v0
governed_by: fb.constitution::CONSTITUTION_STRUCTURE_V0

core:
  summary: Agent admission subdomain storage topology
  layer: DOMAINS
  domain: ai_governance

  storage_roots:
    base_path: "{{module_data_root}}"

  entity_stores:
    LICENSE_FACTS:
      description: "Read-only license tier and status fact feed (shared with agent_governance)"
      path: "ai_governance/ai_licensing/license_facts.json"
    GOVERNANCE_ACTIONS:
      description: "Registry of authorized agent admission actions (idempotency tracking)"
      path: "ai_governance/agent_admission/governance_actions.json"
    GOVERNANCE_AUDIT:
      description: "Append-only audit trail for agent admission authorization and denial decisions"
      path: "ai_governance/agent_admission/governance_audit.jsonl"

  isolation:
    rules:
      - "LICENSE_FACTS is read-only — agent_admission may not mutate license facts"
      - "GOVERNANCE_AUDIT is append-only — admission audit records are immutable"
      - "GOVERNANCE_ACTIONS is scoped to agent_admission — no cross-subdomain writes"
```

---

### 7. RB_AGENT_ADMISSION_BINDINGS_V0

**Location:** `pgs_ai_governance/registry/agent_admission/runtime_bindings/RB_AGENT_ADMISSION_BINDINGS_V0.md`

```yaml
rb_code: RB_AGENT_ADMISSION_BINDINGS_V0
version: v0
governed_by: fb.topology::CONSTITUTION_RUNTIME_BINDING_V0

parameters:
  - module_data_root

core:
  summary: Runtime bindings for agent admission workflow
  storage_structure: ai_governance::STRUCTURE_AGENT_ADMISSION_STORAGE_V0

  bindings:
    capability_side_effects::CS_MUTABLE_JSON_V0:
      type: CS
      host: MutableJsonRuntime
      operation: READ_WRITE
      policy: {}

    capability_side_effects::CS_REGISTRY_V0:
      type: CS
      host: RegistryRuntime
      operation: READ_WRITE
      policy:
        path: "{{module_data_root}}/ai_governance/agent_admission/governance_actions.json"
        strict: true

    capability_side_effects::CS_APPENDONLY_JSONL_V0:
      policy: {}

extensions:
  notes:
    - CS_MUTABLE_JSON_V0 (license_facts.json) is READ-ONLY — agent_admission may not mutate license facts
    - GOVERNANCE_ACTIONS path is scoped to agent_admission — separate from agent_governance
```

---

## Test Scenario Specifications

**Payload field: `domain_context`** — use `"agent_admission"` for all scenarios.

| # | Scenario | User | Tool | Parameters | Expected Decision | Denial Reason |
|---|---|---|---|---|---|---|
| 01 | Valid: standard user, read-only tool | `EMP_STD_001` | `web_search` | `{"query": "PGS governance"}` | AUTHORIZED | — |
| 02 | Denied: no license record | `EMP_NONE_001` | `web_search` | `{"query": "test"}` | DENIED | UNAUTHORIZED_ACTOR |
| 03 | Denied: standard user requests write | `EMP_STD_001` | `write_file` | `{"path": "out.txt", "content": "hello"}` | DENIED | UNAUTHORIZED_TOOL |
| 04 | Valid: enterprise user, write tool | `EMP_ENT_001` | `write_file` | `{"path": "out.txt", "content": "hello"}` | AUTHORIZED | — |
| 05 | Denied: undeclared tool | `EMP_STD_001` | `execute_shell` | `{"command": "ls"}` | DENIED | UNDECLARED_TOOL |
| 06 | Denied: parameter violation | `EMP_ENT_001` | `write_file` | `{"path": "out.txt"}` | DENIED | PARAMETER_VIOLATION |

*Scenario 06 submits `write_file` without the required `content` field — content is `not_null` in the constraint map.*

---

## Compiler Build Configuration

The agent_admission subdomain must be registered in the STRUCTURE build config for `pgs_ai_governance`.

The existing build structure (`STRUCTURE_BUILD_AI_GOVERNANCE_CONFIG_V0`) will need to include the new `agent_admission` registry path so the compiler discovers the new artifacts.

This is an authoring task, not a new artifact — the build config update is a modification to an existing STRUCTURE artifact. It is noted here as a prerequisite for Stage 7 build ordering.

---

## Testbed Location

`pgs_ai_governance/pgs_ai_governance/testbed/agent_admission/`

Structure mirrors the existing `agent_governance` testbed:
```
testbed/agent_admission/
  README.md          ← run instructions + scenario descriptions
  test_payloads/
    01_web_search_authorized.json
    02_no_license.json
    03_standard_requests_write.json
    04_enterprise_write_authorized.json
    05_undeclared_tool.json
    06_parameter_violation.json
```

No new seed_data directory needed — reuses `agent_governance/seed_data/license_facts.json`.

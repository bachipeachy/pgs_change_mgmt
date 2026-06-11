# Business Intent Authoring Guide — V0

**Status:** CANONICAL
**Supersedes:** All prior versions
**Informed By:** validator subdomain exercise (2026-05-29)

---

## What Is This Document?

A Business Intent is the **authoritative governance record** for a subdomain — written by someone who
understands the business process, not by a compiler. It captures what no algorithm can ever derive:
purpose, boundaries, identity meaning, and deferred concerns.

**What belongs here:** WHY this subdomain exists. What it governs. What it does NOT govern. What
business records it maintains and why those records take the form they do. What rules are
non-negotiable and why. What business actions are possible.

**What does NOT belong here:** Implementation bindings, JSONPath expressions, operation codes,
module paths, content hashes, or any field a compiler can determine mechanically. Those details live
in the Governance Intent. If you find yourself writing something that looks like a file path or a
code reference — stop. It belongs elsewhere.

**The key test:** If a developer deleted this file and tried to reconstruct it purely from the
compiled protocol artifacts, what would they be unable to recover? That irreducible content is what
belongs in this document. Everything else is a projection.

---

---

## Stage Inputs — Questions for the Human

*Answer crisply before drafting. The right column states how the agent uses each answer.*

| # | Question for the Human | How the Agent Uses the Answer (Intent) |
|---|------------------------|----------------------------------------|
| 1 | In one paragraph: what does this subdomain govern, and why does it exist? | Becomes Section 1 Purpose — the scope of authority everything else hangs from. |
| 2 | For each business record: does history matter, can values be corrected, is deletion ever allowed? | Selects the Business Record Model per store (Section 3). This is a business decision the compiler cannot infer. |
| 3 | Which field uniquely identifies each record, where does that field come from, and what does a duplicate mean? | Becomes Section 4 Identity Semantics — drives duplicate checks and cross-subdomain resolution. |
| 4 | What is always forbidden or always required, and what is the business reason? | Becomes Section 5 Invariants. Rules without a business reason are technical constraints and belong elsewhere. |
| 5 | What verbs can be performed on these records, and who/what triggers each? | Becomes Section 6 Business Actions. Each in-scope action mechanically yields one Intent and one Workflow — an action missed here is a workflow missing at runtime. |

**Agent execution rules for this stage (provisional codes are now permitted):**
- Every artifact code carries an explicit version suffix (`_V0`) — including provisional codes. Unversioned codes are a defect.
- Workflow execution nodes are **IN, CC, and EXIT/EXIT_SUCCESS only**. A workflow NEVER appears as a node inside another workflow. Sub-workflow invocation is expressed as a CC (e.g., `CC_INVOKE_<TARGET>_V0`) whose implementation binds to the workflow-gateway side effect — see `blockchain::CC_INVOKE_BLOCK_PROPOSAL_V0` for the canonical precedent.
- **EV_ artifacts record facts; they never trigger execution.** There is no event subscription in the runtime. If one workflow must cause another to run, declare a gateway CC in the calling workflow — do not design an event-driven trigger.
- Cross-subdomain CC calls are permitted (list them in Section 11). Cross-subdomain **writes** are forbidden: a store is written only by CCs of its owning subdomain. If this subdomain's process requires a write to a peer's store, the writing CC must be owned by the peer (a dependency gap declared in Stage 6).
- Before declaring any new event or transform: check the snapshot inventory for an existing one (lifecycle events such as EV_*_COMMITTED/FINALIZED and generic transforms such as hash/assemble/generate-id frequently already exist).

---

## Document Header

```
# Business Intent: {{subdomain_name}}
**Domain:** {{domain_name}}
**Subdomain:** {{subdomain_name}}
**Version:** V0
**Status:** DRAFT
```

> **The Business Intent is intentionally lossy.** It captures business governance intent, not
> realization topology. Any field, step, binding, or reference derivable by deterministic compiler
> logic must not appear here. The Governance Intent is where realization topology lives; the
> Business Intent is where governance intent is declared.

---

---

## Business Intent Assembly Flow

*Author this document in the order shown below. Each step feeds the next. The workflow and
capability structure will emerge naturally — you do not need to design them upfront.*

```
  ┌─────────────────────────────────────────────────────────┐
  │  1. Purpose          What does this subdomain govern?   │
  │         │                                               │
  │         ▼                                               │
  │  2. Scope Boundary   What is in V0? What is deferred?  │
  │         │                                               │
  │         ▼                                               │
  │  3. Business Objects What records exist? What shape?    │
  │         │                                               │
  │         ▼                                               │
  │  4. Identity         Which fields are the keys? Why?    │
  │         │                                               │
  │         ▼                                               │
  │  5. Invariants       What is always forbidden or req'd? │
  │         │                                               │
  │         ▼                                               │
  │  6. Business Actions What can happen to these objects?  │
  │         │                                               │
  │         ▼                                               │
  │  7. Actors           Who is authorized to act?          │
  │         │                                               │
  │         ▼                                               │
  │  8. Intents          What does each action require?     │
  │         │                                               │
  │         ▼                                               │
  │  9. Workflow         In what order do checks execute?   │
  │         │                                               │
  │         ▼                                               │
  │ 10. Capability       What does each step do and why?    │
  │     Contracts                                           │
  └─────────────────────────────────────────────────────────┘
```

**Key insight:** Most authors instinctively start with the workflow. Resist that instinct.
Workflow is an *outcome* of the earlier thinking, not a starting point. If you author in the order
above, the workflow graph will typically write itself.

---

---

## Authoring Strategy

*Read this before opening Section 1.*

This guide is organized as a **discovery process**, not a documentation checklist. Each section
answers one question about your business domain. By the time you reach Section 8 (Workflow), you
will have accumulated everything needed to describe the execution graph — the nodes, the routing,
and the terminal conditions — without needing to design it from scratch.

**The discovery sequence:**

| Step | Question | Why This Order |
| --- | --- | --- |
| 1. Purpose | What does this subdomain govern? | Establishes scope of authority before anything else |
| 2. Scope Boundary | What does V0 commit to? | Prevents scope creep; makes deferrals explicit |
| 3. Business Objects | What records exist? | Establishes what the domain *has* before asking what it *does* |
| 4. Identity | Which fields key those records? | Can only be answered after records are declared |
| 5. Invariants | What is always forbidden or required? | Rules apply to records and identities already declared |
| 6. Business Actions | What verbs apply to these objects? | Actions drive Intents; Intents drive Workflows |
| 7. Actors | Who is authorized to act? | Authority is declared after actions are known |
| 8. Intents | What must a caller provide per action? | Input shape follows from action semantics |
| 9. Workflow | In what order do checks execute? | Workflow topology follows from action + invariant + CC dependencies |
| 10. Capability Contracts | What does each workflow step do? | CCs are leaf implementations; authored last |

**Do not start with Workflow.** It is the last thing that becomes clear, not the first.

---

---

## Section 1 — Subdomain Purpose

*Write one paragraph answering: what does this subdomain govern? What authority does it establish?
What lifecycle does it manage? Write for a business stakeholder, not a developer.*

*Good example (validator):*
> The consensus_pos subdomain governs the Proof-of-Stake consensus layer within the blockchain domain.
> V0 covers validator registration — the authoritative validator registry and the validator lifecycle
> event log. A validator is an actor already registered in the identity registry who signs up to
> participate in block production and attestation.

*Anti-pattern:*
> This subdomain executes WF_REGISTER_VALIDATOR_V0 which calls CC_CHECK_ACTOR_EXISTS_V0 via the
> identity layer's CS_REGISTRY_V0 binding.
> *(That is realization topology. It belongs in the Governance Intent, not here.)*

**Template:**

{{One paragraph: what does this subdomain govern, what authority does it establish, what lifecycle
does it manage, and what is the business rationale for its existence.}}

---

---

## Section 2 — Scope Boundary  ✦ MANDATORY — Do Not Skip

*This is the most important section a business analyst authors. It tells architects, developers,
and future maintainers exactly what V0 commits to and what is explicitly deferred. It prevents
scope creep and documents governance decisions that no compiler can infer.*

*A missing or vague scope boundary is a governance defect. Be explicit — if something is not listed
as in scope, someone will assume it should be.*

**Template:**

### In Scope — V0

| Capability | Notes |
| --- | --- |
| {{capability}} | {{why it is in scope, any constraints}} |

*Example (validator):*
| Capability | Notes |
| --- | --- |
| Validator registration | One record per actor; actor prerequisite enforced |
| Validator existence check | Gates write to prevent duplicate registration |
| Validator lifecycle event logging | Append-only; immutable after write |

### Explicitly Deferred — Not In Scope

| Capability | Deferred To |
| --- | --- |
| {{capability}} | {{future version, future sub-module, or TBD}} |

*Example (validator):*
| Capability | Deferred To |
| --- | --- |
| Block proposal | Future sub-module: proposer |
| Attestation | Future sub-module: attestor |
| Finalization | Future sub-module: finalizer |
| Slashing | Future version |
| Rewards and penalties | Future version |
| Epoch-triggered transitions | Future version |

*Authoring note: When in doubt, list it as deferred. Explicit deferral is a governance decision.
Silence is ambiguity.*

---

---

## Section 3 — Business Object Semantics  ✦ MANDATORY — Do Not Skip

*Start here before thinking about identity or workflows. Declare what business records this
subdomain maintains and WHY those records take the form they do.*

*The storage model (mutable vs. append-only vs. registry) is a business decision — it reflects
whether history matters, whether values can change, and whether deletion is allowed. Getting the
storage model wrong produces bugs that are invisible until runtime.*

*Ask yourself: does this record represent current state, or accumulated history? Can it be
corrected? Does deletion break anything? The answers determine the model.*

**Template:**

| Store Name | Business Record Model | Business Rationale |
| --- | --- | --- |
| {{STORE_NAME}} | {{Mutable State \| Append-Only Journal \| Identity Registry \| Hybrid}} | {{WHY this model — e.g. "each actor has exactly one current validator record; it may need correction after write, so mutable state is appropriate"}} |

**Business Record Model definitions:**

| Model | Meaning | Use When |
| --- | --- | --- |
| **Mutable State** | One current record per key; can be updated; history not preserved | Current status, latest snapshot, idempotent state |
| **Append-Only Journal** | Records accumulate; never modified or deleted after write | Audit log, lifecycle events, immutable history |
| **Identity Registry** | Stable key-to-address bindings; append-only; no rebinding | Cross-subdomain resolution, name service, stable references |
| **Hybrid** | Multiple stores serving different roles | When both current state and history are required |

*Example (validator):*
| Store Name | Business Record Model | Business Rationale |
| --- | --- | --- |
| VALIDATOR | Mutable State | Authoritative validator registry; one record per actor; corrections must be possible; duplicate check enforced before first write |
| VALIDATOR_EVENTS | Append-Only Journal | Immutable lifecycle event log; every state change is recorded permanently; deletion would break audit integrity |

---

---

## Section 4 — Identity Semantics  ✦ MANDATORY — Do Not Skip

*Now that records are declared, declare which fields carry identity meaning and why. The compiler
cannot infer identity semantics from field names alone — this is irreducible business knowledge.*

*Identity semantics determine how records are keyed, how duplicates are detected, and how this
subdomain connects to others. Getting this wrong cascades into storage model errors.*

**Template:**

### Primary Identity

**Field:** `{{field_name}}`
**Source:** {{Where this comes from — e.g. "generated by identity subdomain at actor registration"}}
**Role:** {{What this field anchors — e.g. "cross-subdomain identity key; ties this record to the actor in the identity registry"}}
**Uniqueness:** {{One record per X — e.g. "one validator record per actor_id; enforced by duplicate check before write"}}

### Secondary Identity (if applicable)

**Field:** `{{field_name}}`
**Role:** {{What this field represents in the business context — e.g. "BLS12-381 public key — consensus-layer cryptographic identity, distinct from the PGS actor identity"}}
**Uniqueness:** {{Whether secondary identity must also be unique, or is informational}}

*If this subdomain has no secondary identity, write:*
_No secondary identity fields. Primary identity is sufficient._

### Cross-Subdomain Identity Usage

{{Explain if and how this subdomain's identity fields relate to another subdomain's records.
Example: "actor_id is the identity anchor shared with the identity subdomain. A validator record
cannot exist without a corresponding actor record — actor existence is enforced as a hard
prerequisite before any write."}}

*If this subdomain defines its own actors, write:*
_This subdomain defines its own actor identity. See Actors section below._

---

---

## Section 5 — Business Invariants

*Invariants are the non-negotiable rules of this subdomain. They exist because the business process
requires them, not because a compiler enforces them. List only rules that have a business reason —
not technical constraints.*

*Format each invariant as: what is forbidden or required, and WHY the business requires it.*

**Template:**

| # | Invariant | Business Reason |
| --- | --- | --- |
| 1 | {{State the rule plainly — e.g. "An actor must exist in the identity registry before registering as a validator"}} | {{The business reason — e.g. "Validators are a privileged role; only verified participants may assume it; orphaned validator records would break cross-subdomain resolution"}} |
| 2 | {{...}} | {{...}} |

*If no invariants apply, write:*
_No subdomain-level invariants declared in V0._

---

---

## Section 6 — Business Actions  ✦ MANDATORY — Do Not Skip

*List every verb that can be performed on this subdomain's objects. Do not jump to intent codes or
workflow names yet — state the business action in plain English first.*

*This is the bridge between your static model (objects, identity, invariants) and the dynamic
model (intents, workflows, capability contracts). Each business action maps to exactly one Intent,
which maps to exactly one Workflow.*

*Common action verbs:* REGISTER, CREATE, VERIFY, APPROVE, REJECT, ACTIVATE, DEACTIVATE, REVOKE,
UPDATE, TRANSFER, CLOSE, ARCHIVE, QUERY, COUNT.

**Template:**

| Business Action | Object Affected | Trigger | V0 Status |
| --- | --- | --- | --- |
| {{VERB}} | {{Store Name}} | {{Who or what initiates this action}} | {{In Scope \| Deferred}} |

*Example (validator):*
| Business Action | Object Affected | Trigger | V0 Status |
| --- | --- | --- | --- |
| REGISTER_VALIDATOR | VALIDATOR, VALIDATOR_EVENTS | An actor submits a registration request | In Scope |
| DEACTIVATE_VALIDATOR | VALIDATOR, VALIDATOR_EVENTS | Governance event or slashing condition | Deferred |
| REACTIVATE_VALIDATOR | VALIDATOR, VALIDATOR_EVENTS | Validator re-enters active set | Deferred |

*Authoring note: Once this table is complete, each In Scope row becomes one Intent and one
Workflow. The derivation is mechanical — the business decision happened here.*

**How Business Actions propagate:**

```
Business Action:  REGISTER_VALIDATOR
      ↓
Intent:           IN_REGISTER_VALIDATOR_V0   (admission gate — what must the caller provide?)
      ↓
Workflow:         WF_REGISTER_VALIDATOR_V0   (execution graph — in what order do checks run?)
      ↓
Capability CCs:   CC_CHECK_ACTOR_EXISTS_V0   (does the prerequisite hold?)
                  CC_CHECK_VALIDATOR_EXISTS_V0 (is this a duplicate?)
                  CC_WRITE_VALIDATOR_RECORD_V0 (write the record)
                  CC_APPEND_VALIDATOR_EVENT_V0 (log the lifecycle event)
```

---

---

## Section 7 — Actors (AC)

<!-- OPTION A: This subdomain defines new actors -->

### {{AC_CODE_V0}}
**Summary:** {{Short role summary}}
**Description:** {{What entity does this actor represent and what authority does it carry?}}
**Authority Class:** {{ENDUSER | SYSTEM}}

| Field | Type | Required |
| --- | --- | --- |
| {{field_name}} | {{type}} | {{YES | NO}} |

<!-- OPTION B: This subdomain does not define new actors
     Replace the entire section body with:

_This subdomain does not define new actors. Actor authority classes are defined in
`business_intent_identity_v0.md` (AC_ENDUSER_V0, AC_SYSTEM_V0)._
-->

---

---

## Section 8 — Intents (IN)

*An Intent is the admission gate for a workflow — it declares what a caller must provide and
whether the system will accept or reject the request. Write input field descriptions to explain
WHY the field is required, not just what type it is.*

*One Intent per Business Action (Section 6). Outcomes are always ACK (accepted) or NACK (rejected).*

### {{IN_CODE_V0}}
**Summary:** {{What does this intent admit? One sentence.}}
**Workflow Binding:** `{{WF_CODE_V0}}`

**Input Fields:**

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| {{field_name}} | {{type}} | {{YES | NO}} | {{WHY this field is required — what business validation does it enable?}} |
| └ {{nested_field}} | {{type}} | {{YES | NO}} | {{Description or "—"}} |

*Use └ prefix for nested fields within an object-type parent. Include nested fields only when they
carry independent validation meaning.*

**Outcomes:**

| Outcome | Description |
| --- | --- |
| ACK | {{What does acceptance mean for this intent? What has been confirmed?}} |
| NACK | {{What triggers rejection? What business rules failed?}} |

---

---

## Section 9 — Workflows (WF)

*A Workflow is the ordered execution graph for a business process. Declare the nodes and routing
in business terms — which step leads to which, and what outcome drives each route.*

*One Workflow per Business Action (Section 6). If you have authored Sections 3–6 carefully, the
node sequence here should follow directly from the invariants and business actions you declared.*

*Routing outcomes use the business status name (SUCCESS, NOT_FOUND, ALREADY_EXISTS, etc.).
Terminal nodes are EXIT (failure or early exit) and EXIT_SUCCESS (happy path completion).*

### {{WF_CODE_V0}}
**Summary:** {{What does this workflow accomplish? One sentence covering the full business process.}}
**Subdomain:** `{{subdomain_name}}`
**Start Node:** `{{IN_CODE_V0}}`

**Execution Nodes:**

| Node | Type | Routing Outcomes |
| --- | --- | --- |
| {{IN_CODE_V0}} | IN | ACK → {{FIRST_CC}}, NACK → EXIT |
| {{CC_CODE_V0}} | CC | SUCCESS → {{NEXT}}, {{OTHER_OUTCOME}} → EXIT |
| EXIT | EXIT | — |
| EXIT_SUCCESS | EXIT | — |

*List nodes in execution order from start to terminal. Include EXIT_SUCCESS when the workflow has a
distinct happy-path terminal. Use EXIT for all failure and early-exit terminals.*

**CC Dependencies:** `{{CC_1}}`, `{{CC_2}}`

*List all CC nodes in execution order. Include cross-subdomain CCs — they are referenced here even
though they are documented in another subdomain's Business Intent.*

---

---

## Section 10 — Capability Contracts (CC)

*A Capability Contract is a named step in the workflow graph. Document only the CCs owned by THIS
subdomain. Cross-subdomain CCs (from another subdomain's workflow) go in Section 11.*

*For each CC, describe what it does in business terms, what it needs as input, what it produces as
output, and what outcomes it can return. Do not include implementation bindings, file paths, or
op codes — those are derived by the compiler.*

### {{CC_CODE_V0}}
**Summary:** {{What does this CC do, and why does it exist in this workflow?}}

**Inputs:**

| Field | Type | Required |
| --- | --- | --- |
| {{field_name}} | {{type}} | {{YES | NO}} |

*If no inputs: "_No inputs declared._"*

**Outputs:**

| Field | Type |
| --- | --- |
| {{field_name}} | {{type}} |

*If no outputs: "_No outputs declared._"*

**Result Statuses:** `{{STATUS_1}}`, `{{STATUS_2}}`

*Declare only statuses this CC can actually return. Common sets:*
- *Pure computation: `SUCCESS`, `VIOLATION`*
- *Registry read: `SUCCESS`, `NOT_FOUND`, `VIOLATION`, `BACKEND_ERROR`*
- *Registry write: `SUCCESS`, `ALREADY_EXISTS`, `VIOLATION`, `BACKEND_ERROR`*
- *Event append: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`*

**Pipeline Steps:**

| Step | Purpose |
| --- | --- |
| {{step_name}} | {{Plain English: what does this step do and why? Include the business outcome it guards against.}} |

---

---

## Section 11 — Cross-Subdomain References

*Include this section only if this subdomain's workflow references CCs owned by another subdomain.
Do not re-document the CC here — its authoritative definition is in the source subdomain's
Business Intent.*

The following Capability Contracts are defined in another subdomain and referenced in this
subdomain's workflow execution graph:

| CC Code | Defined In | Role In This Workflow |
| --- | --- | --- |
| {{CC_CODE_V0}} | {{business_intent_subdomain_v0.md}} | {{What business gate does this CC serve here?}} |

*If this subdomain owns all CCs in its workflows, omit this section entirely.*

---

---

## Authoring Checklist

Before submitting, confirm:

- [ ] **Authored in discovery order** — Purpose → Scope → Objects → Identity → Invariants → Actions → Actors → Intents → Workflow → CCs
- [ ] **Scope Boundary is complete** — both in-scope capabilities AND explicitly deferred items listed
- [ ] **Business Objects are declared** — every store named, model chosen, business rationale given
- [ ] **Identity Semantics is complete** — primary identity field named, role explained, uniqueness stated
- [ ] **Business Actions are declared** — every in-scope action listed; each maps to one IN and one WF
- [ ] **No implementation details leaked** — no file paths, no op codes, no module names, no FQDNs
- [ ] **Invariants are stated in business language** — each invariant has a business reason, not just a technical constraint
- [ ] **CC pipeline step purposes explain WHY** — not just "read the store" but "check X exists before Y to prevent Z"
- [ ] **Cross-subdomain CCs are listed** — all CCs from other subdomains appear in Section 11
- [ ] **EXIT_SUCCESS declared** if the workflow has a distinct happy-path terminal

# Business Intent: consensus_pos
**Domain:** blockchain  
**Subdomain:** consensus_pos  
**Version:** V0  
**Status:** DRAFT  

---

## Subdomain Purpose

The consensus_pos subdomain governs the Proof-of-Stake consensus layer within the blockchain domain. V0 covers validator registration: enforcing the actor prerequisite, preventing duplicate registration, persisting the validator record to the VALIDATOR store, and appending a validator lifecycle event to the append-only event journal.

---

## Actors (AC)

_This subdomain does not define new actors. Actor authority classes are defined in `5_business_intent_identity_v0.md` (AC_ENDUSER_V0, AC_SYSTEM_V0)._

---

## Intents (IN)

### IN_VALIDATOR_REGISTERED_V0
**Summary:** Register an existing actor as a validator node  
**Workflow Binding:** `WF_REGISTER_VALIDATOR_V0`  

**Input Fields:**

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| validator_record | object | YES | Proposed validator registration payload |
| └ actor_id | string | YES | — |
| └ effective_balance | integer | YES | — |
| └ node_name | string | YES | — |
| └ pubkey | string | YES | — |
| └ withdrawal_credentials | string | YES | — |

**Outcomes:**

| Outcome | Description |
| --- | --- |
| ACK | Payload admitted — all required fields present, pubkey format valid, effective_balance meets minimum |
| NACK | Payload rejected — missing required fields, invalid pubkey format, or effective_balance below minimum |

---

## Workflows (WF)

### WF_REGISTER_VALIDATOR_V0
**Summary:** Register an actor as a validator node  
**Subdomain:** `consensus_pos`  
**Start Node:** `IN_VALIDATOR_REGISTERED_V0`  

**Execution Nodes:**

| Node | Type | Routing Outcomes |
| --- | --- | --- |
| IN_VALIDATOR_REGISTERED_V0 | IN | ACK → CC_CHECK_ACTOR_EXISTS_V0, NACK → EXIT |
| CC_CHECK_ACTOR_EXISTS_V0 | CC | BACKEND_ERROR → EXIT, NOT_FOUND → EXIT, SUCCESS → CC_CHECK_VALIDATOR_EXISTS_V0, VIOLATION → EXIT |
| EXIT | EXIT | — |
| CC_CHECK_VALIDATOR_EXISTS_V0 | CC | BACKEND_ERROR → EXIT, NOT_FOUND → CC_WRITE_VALIDATOR_RECORD_V0, SUCCESS → EXIT, VIOLATION → EXIT |
| CC_WRITE_VALIDATOR_RECORD_V0 | CC | BACKEND_ERROR → EXIT, SUCCESS → CC_APPEND_VALIDATOR_EVENT_V0, VIOLATION → EXIT |
| CC_APPEND_VALIDATOR_EVENT_V0 | CC | BACKEND_ERROR → EXIT, SUCCESS → EXIT, VIOLATION → EXIT |

**CC Dependencies:** `CC_CHECK_ACTOR_EXISTS_V0`, `CC_CHECK_VALIDATOR_EXISTS_V0`, `CC_WRITE_VALIDATOR_RECORD_V0`, `CC_APPEND_VALIDATOR_EVENT_V0`

---

## Capability Contracts (CC)

### CC_APPEND_VALIDATOR_EVENT_V0
**Summary:** Append a validator lifecycle event to the append-only event journal  

**Inputs:**

| Field | Type | Required |
| --- | --- | --- |
| actor_id | string | YES |
| data | object | YES |
| event_type | string | YES |

**Outputs:**

| Field | Type |
| --- | --- |
| result_status | string |

**Result Statuses:** `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`

**Pipeline Steps:**

| Step | Purpose |
| --- | --- |
| append_validator_event | Append validator event |

### CC_CHECK_VALIDATOR_EXISTS_V0
**Summary:** Check if actor already has a validator record in the VALIDATOR store  

**Inputs:**

| Field | Type | Required |
| --- | --- | --- |
| actor_id | string | YES |

**Outputs:**

| Field | Type |
| --- | --- |
| result_status | string |

**Result Statuses:** `NOT_FOUND`, `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`

**Pipeline Steps:**

| Step | Purpose |
| --- | --- |
| check_validator_exists | Check validator exists |

### CC_WRITE_VALIDATOR_RECORD_V0
**Summary:** Write the validator record to the VALIDATOR store keyed by actor_id  

**Inputs:**

| Field | Type | Required |
| --- | --- | --- |
| validator_record | object | YES |

**Outputs:**

_No outputs declared._

**Result Statuses:** `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`

**Pipeline Steps:**

| Step | Purpose |
| --- | --- |
| write_validator_record | Write validator record |

---

## Cross-Subdomain References

The following Capability Contracts are defined in another subdomain and referenced here in the workflow execution topology. They are not re-documented — see the authoritative Business Intent for the subdomain listed.

| CC Code | Defined In |
| --- | --- |
| CC_CHECK_ACTOR_EXISTS_V0 | 5_business_intent_identity_v0.md |

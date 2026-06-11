# Authoring Plan: blockchain / consensus_pos
**Domain:** blockchain  
**Primary subdomain:** consensus_pos  
**Additional subdomains:** blockchain::block (new), blockchain::transaction (dependency gap)  
**Version:** V0  
**Status:** READY FOR AUTHORING  
**Pipeline Stage:** Stage 7 — Authoring Plan  
**Produced by:** v0.5.0 SDLC authoring pipeline  
**Input:** 6b_design_intent_consensus_pos_v0.md (Stage 6b — APPROVED)  

---

## Overview

This CR produces 16 authoring actions across three subdomains:

| Subdomain | Actions | Breakdown |
| --- | --- | --- |
| blockchain::consensus_pos | 12 | 3 REPLACE, 9 NEW |
| blockchain::block | 2 | 2 NEW (new subdomain established) |
| blockchain::transaction | 1 | 1 NEW (dependency gap, owned by transaction) |
| STRUCTURE (cross-subdomain) | 1 | 1 EXTEND (4 new stores across 2 subdomains) |
| **Total** | **16** | |

REUSE artifacts (10 existing, no changes): `CC_CHECK_ACTOR_EXISTS_V0`, `CC_CHECK_VALIDATOR_EXISTS_V0`, `CC_APPEND_VALIDATOR_EVENT_V0`, `EV_VALIDATOR_REGISTERED_V0`, `RB_REGISTER_VALIDATOR_V0`, `CT_PURE_ASSEMBLE_RECORD_V0`, `CT_PURE_GENERATE_ID_V0`, `CS_MUTABLE_JSON_V0`, `CS_APPENDONLY_JSONL_V0`, `CT_PURE_EXTRACT_V0`.

---

## Build Dependency Order

Steps within the same wave have no inter-dependencies and may be authored in parallel.

---

### Wave 1 — Foundation (no dependencies)

**Step 1**
```
Artifact:    blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0
Action:      EXTEND
Subdomain:   cross-subdomain (adds stores to consensus_pos and blockchain::block)
Depends on:  nothing
PPS status:  EXISTS — extend with 4 new stores
```
Add four new entity stores to the existing structure artifact:
- `CONSENSUS_ROUNDS` — `CS_APPENDONLY_JSONL_V0`, path: `blockchain/consensus_pos/rounds/rounds.jsonl`
- `CONSENSUS_EVENTS` — `CS_APPENDONLY_JSONL_V0`, path: `blockchain/consensus_pos/events/consensus_events.jsonl`
- `BLOCKS` — `CS_MUTABLE_JSON_V0`, path: `blockchain/block/blocks/blocks.json`
- `BLOCK_EVENTS` — `CS_APPENDONLY_JSONL_V0`, path: `blockchain/block/events/block_events.jsonl`

Existing stores `VALIDATOR` and `VALIDATOR_EVENTS` are unchanged — the VALIDATOR record schema is enriched at write time by CC_WRITE_VALIDATOR_RECORD_V0 (Step 7); no store path or CS type change.

---

**Step 2**
```
Artifact:    blockchain::CT_PURE_SELECT_PROPOSER_V0
Action:      NEW
Subdomain:   consensus_pos
Depends on:  nothing
PPS status:  NOT PRESENT — must author
```
Pure capability transform. No side effects.
- Inputs: `eligible_validators` (array of validator records), `round_number` (integer)
- Output: `proposer_id` (string)
- Algorithm: `eligible_validators[round_number % len(eligible_validators)].actor_id`
- Failure: `VIOLATION` if `eligible_validators` empty or `round_number` negative
- This CT is the sole artifact carrying the proposer selection algorithm — future algorithm changes require only a new CT version.

---

**Step 3**
```
Artifact:    blockchain::IN_VALIDATOR_REGISTERED_V0
Action:      REPLACE
Subdomain:   consensus_pos
Depends on:  nothing
PPS status:  EXISTS — replace; enrich input schema
```
Admission gate for WF_REGISTER_VALIDATOR_V0. Add `stake` (string, required) and `enrollment_status` (string, required, enum: ACTIVE/INACTIVE/EXCLUDED) to the payload schema. Outcomes: `ACK`, `NACK`.

---

**Step 4**
```
Artifact:    blockchain::IN_BLOCK_PROPOSED_V0
Action:      NEW
Subdomain:   consensus_pos
Depends on:  nothing
PPS status:  NOT PRESENT — must author
```
Admission gate for WF_PROPOSE_BLOCK_V0. Schema:
- `round_number` (integer, required) — monotonically increasing round identifier
- `triggered_by` (string, optional) — external trigger reference

Outcomes: `ACK`, `NACK`.

---

**Step 5**
```
Artifact:    blockchain::EV_BLOCK_PROPOSED_V0
Action:      NEW
Subdomain:   block
Depends on:  nothing
PPS status:  NOT PRESENT — must author
```
Block lifecycle event. Emitted by CC_FORM_BLOCK_V0 (Step 9) to the BLOCK_EVENTS store. Payload fields: `block_id`, `round_id`, `proposer_id`, `tx_ids`, `timestamp`.

---

**Step 6**
```
Artifact:    blockchain::EV_ROUND_SKIPPED_V0
Action:      NEW
Subdomain:   consensus_pos
Depends on:  nothing
PPS status:  NOT PRESENT — must author
```
Consensus lifecycle event. Emitted by CC_SKIP_ROUND_V0 (Step 10) to the CONSENSUS_EVENTS store. Payload fields: `round_id`, `proposer_id`, `outcome: SKIPPED`, `timestamp`.

---

### Wave 2 — Depends on STRUCTURE (Step 1)

*Steps 7–11 may be authored in parallel with each other once Step 1 is complete.*

**Step 7**
```
Artifact:    blockchain::CC_WRITE_VALIDATOR_RECORD_V0
Action:      REPLACE
Subdomain:   consensus_pos
Depends on:  Step 1 (STRUCTURE extension — VALIDATOR store schema context)
PPS status:  EXISTS — replace; enriched validator record schema
```
Single-step pipeline: `CS_MUTABLE_JSON_V0` WRITE to VALIDATOR store (key: `actor_id`). The `validator_record` object must include: `actor_id`, `stake`, `enrollment_status`, `registered_at`. Outcomes: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`.

---

**Step 8**
```
Artifact:    blockchain::CC_QUERY_PENDING_TRANSACTIONS_V0
Action:      NEW
Subdomain:   transaction  ← owned by blockchain::transaction; triggered by this CR
Depends on:  Step 1 (STRUCTURE extension — TRANSACTION store exists)
PPS status:  NOT PRESENT — must author; fills identified dependency gap
```
Cross-subdomain dependency gap. This CC is called by WF_PROPOSE_BLOCK_V0 (consensus_pos) but owned and governed by `blockchain::transaction`.
- Step 1: `CS_MUTABLE_JSON_V0` — LIST — TRANSACTION store (filter: `status=pending`) → `tx_ids` list
- Outcomes: `SUCCESS` (list returned), `EMPTY` (no pending transactions), `VIOLATION`, `BACKEND_ERROR`

---

**Step 9**
```
Artifact:    blockchain::CC_FORM_BLOCK_V0
Action:      NEW
Subdomain:   block  ← owned by blockchain::block; new subdomain established this CR
Depends on:  Step 1 (STRUCTURE — BLOCKS + BLOCK_EVENTS stores), Step 5 (EV_BLOCK_PROPOSED_V0)
PPS status:  NOT PRESENT — must author
```
Block formation pipeline — all writes within blockchain::block stores:
- Step 1: `CT_PURE_GENERATE_ID_V0` (REUSE, prefix: `BLK`) → `block_id`
- Step 2: `CT_PURE_ASSEMBLE_RECORD_V0` (REUSE) — fields: `{block_id, round_id, proposer_id, tx_ids, timestamp}` → `block_record`
- Step 3: `CS_MUTABLE_JSON_V0` — WRITE — BLOCKS store (key: `block_id`)
- Step 4: `CS_APPENDONLY_JSONL_V0` — APPEND — BLOCK_EVENTS store (event_type: `EV_BLOCK_PROPOSED_V0`)
- Outcomes: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`

---

**Step 10**
```
Artifact:    blockchain::CC_SKIP_ROUND_V0
Action:      NEW
Subdomain:   consensus_pos
Depends on:  Step 1 (STRUCTURE — CONSENSUS_ROUNDS + CONSENSUS_EVENTS stores), Step 6 (EV_ROUND_SKIPPED_V0)
PPS status:  NOT PRESENT — must author
```
All writes within consensus_pos stores only — no cross-subdomain write:
- Step 1: `CT_PURE_ASSEMBLE_RECORD_V0` (REUSE) — fields: `{round_id, proposer_id, outcome: SKIPPED, timestamp}` → `skip_record`
- Step 2: `CS_APPENDONLY_JSONL_V0` — APPEND — CONSENSUS_ROUNDS store
- Step 3: `CS_APPENDONLY_JSONL_V0` — APPEND — CONSENSUS_EVENTS store (event_type: `EV_ROUND_SKIPPED_V0`)
- Outcomes: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`

---

**Step 11**
```
Artifact:    blockchain::CC_RECORD_CONSENSUS_ROUND_V0
Action:      NEW
Subdomain:   consensus_pos
Depends on:  Step 1 (STRUCTURE — CONSENSUS_ROUNDS store)
PPS status:  NOT PRESENT — must author
```
Records the PROPOSED outcome after a block is formed:
- Step 1: `CT_PURE_ASSEMBLE_RECORD_V0` (REUSE) — fields: `{round_id, proposer_id, block_id, outcome: PROPOSED, timestamp}` → `round_record`
- Step 2: `CS_APPENDONLY_JSONL_V0` — APPEND — CONSENSUS_ROUNDS store
- Outcomes: `SUCCESS`, `VIOLATION`, `BACKEND_ERROR`

---

### Wave 3 — Depends on Wave 1/2 results

**Step 12**
```
Artifact:    blockchain::WF_REGISTER_VALIDATOR_V0
Action:      REPLACE
Subdomain:   consensus_pos
Depends on:  Step 3 (IN_VALIDATOR_REGISTERED_V0), Step 7 (CC_WRITE_VALIDATOR_RECORD_V0)
Reuses:      CC_CHECK_ACTOR_EXISTS_V0, CC_CHECK_VALIDATOR_EXISTS_V0, CC_APPEND_VALIDATOR_EVENT_V0
PPS status:  EXISTS — replace; correct pipeline provenance (GI gate now satisfied) + enriched schema
```
WF topology is unchanged from the existing artifact — only the pipeline provenance and validator record schema change. Declare `subdomain: consensus_pos`. The WF must reference the REPLACE versions of IN and CC.

Execution topology (for reference):
```
IN_VALIDATOR_REGISTERED_V0 (REPLACE)
    ACK  → CC_CHECK_ACTOR_EXISTS_V0 (REUSE)
    NACK → EXIT

CC_CHECK_ACTOR_EXISTS_V0
    SUCCESS       → CC_CHECK_VALIDATOR_EXISTS_V0 (REUSE)
    NOT_FOUND/VIOLATION/BACKEND_ERROR → EXIT

CC_CHECK_VALIDATOR_EXISTS_V0
    NOT_FOUND     → CC_WRITE_VALIDATOR_RECORD_V0 (REPLACE)
    SUCCESS       → EXIT  ← already registered
    VIOLATION/BACKEND_ERROR → EXIT

CC_WRITE_VALIDATOR_RECORD_V0
    SUCCESS       → CC_APPEND_VALIDATOR_EVENT_V0 (REUSE)
    VIOLATION/BACKEND_ERROR → EXIT

CC_APPEND_VALIDATOR_EVENT_V0
    SUCCESS/VIOLATION/BACKEND_ERROR → EXIT
```

---

**Step 13**
```
Artifact:    blockchain::CC_SELECT_PROPOSER_V0
Action:      NEW
Subdomain:   consensus_pos
Depends on:  Step 2 (CT_PURE_SELECT_PROPOSER_V0)
PPS status:  NOT PRESENT — must author
```
Single-step pipeline:
- Step 1: `blockchain::CT_PURE_SELECT_PROPOSER_V0` — inputs: `eligible_validators`, `round_number` → output: `proposer_id`
- Outcomes: `SUCCESS`, `VIOLATION`

---

### Wave 4 — Depends on Wave 3

**Step 14**
```
Artifact:    blockchain::CC_QUERY_ELIGIBLE_VALIDATORS_V0
Action:      NEW
Subdomain:   consensus_pos
Depends on:  Step 1 (STRUCTURE — VALIDATOR store), Step 12 (WF_REGISTER_VALIDATOR_V0 functional — validators can be enrolled)
PPS status:  NOT PRESENT — must author
```
- Step 1: `CS_MUTABLE_JSON_V0` — LIST — VALIDATOR store → raw validator list
- Step 2: `CT_PURE_EXTRACT_V0` (REUSE) — filter: `enrollment_status=ACTIVE` AND `stake` present → `eligible_validators` list
- Outcomes: `SUCCESS` (eligible list returned), `NOT_FOUND` (no eligible validators), `VIOLATION`, `BACKEND_ERROR`

Note: functional dependency on Step 12 means the enrollment workflow must be operational before block proposal execution can succeed. Both artifacts can be authored independently; the dependency is runtime (an empty pool is a valid operational state at authoring time).

---

### Wave 5 — All CCs Ready

**Step 15**
```
Artifact:    blockchain::WF_PROPOSE_BLOCK_V0
Action:      NEW
Subdomain:   consensus_pos
Depends on:  Steps 4, 8, 9, 10, 11, 13, 14  (all CCs + IN + EVs)
PPS status:  NOT PRESENT — must author
```
Governing workflow for the block proposal process. Declare `subdomain: consensus_pos`.

Execution topology:
```
IN_BLOCK_PROPOSED_V0 (Step 4)
    ACK  → CC_QUERY_ELIGIBLE_VALIDATORS_V0 (Step 14)
    NACK → EXIT

CC_QUERY_ELIGIBLE_VALIDATORS_V0
    SUCCESS       → CC_SELECT_PROPOSER_V0 (Step 13)
    NOT_FOUND     → EXIT
    VIOLATION/BACKEND_ERROR → EXIT

CC_SELECT_PROPOSER_V0
    SUCCESS       → CC_QUERY_PENDING_TRANSACTIONS_V0 (Step 8)
    VIOLATION     → EXIT

CC_QUERY_PENDING_TRANSACTIONS_V0  ← cross-subdomain: blockchain::transaction
    SUCCESS       → CC_FORM_BLOCK_V0 (Step 9)
    EMPTY         → CC_SKIP_ROUND_V0 (Step 10)
    VIOLATION/BACKEND_ERROR → EXIT

[PROPOSE PATH]
CC_FORM_BLOCK_V0                  ← cross-subdomain: blockchain::block
    SUCCESS       → CC_RECORD_CONSENSUS_ROUND_V0 (Step 11)
    VIOLATION/BACKEND_ERROR → EXIT

CC_RECORD_CONSENSUS_ROUND_V0
    SUCCESS/VIOLATION/BACKEND_ERROR → EXIT

[SKIP PATH]
CC_SKIP_ROUND_V0
    SUCCESS/VIOLATION/BACKEND_ERROR → EXIT
```

JSONPath input bindings (authoring-phase detail — resolved when authoring each CC step):
- `CC_SELECT_PROPOSER_V0` receives `eligible_validators` from `$.results.CC_QUERY_ELIGIBLE_VALIDATORS_V0.eligible_validators`
- `CC_SELECT_PROPOSER_V0` receives `round_number` from `$.payload.round_number`
- `CC_FORM_BLOCK_V0` receives `proposer_id` from `$.results.CC_SELECT_PROPOSER_V0.proposer_id`
- `CC_FORM_BLOCK_V0` receives `tx_ids` from `$.results.CC_QUERY_PENDING_TRANSACTIONS_V0.tx_ids`
- `CC_FORM_BLOCK_V0` receives `round_id` from `$.payload.round_number`
- `CC_RECORD_CONSENSUS_ROUND_V0` receives `block_id` from `$.results.CC_FORM_BLOCK_V0.block_id`

---

### Wave 6 — Terminal

**Step 16**
```
Artifact:    blockchain::RB_PROPOSE_BLOCK_V0
Action:      NEW
Subdomain:   consensus_pos
Depends on:  Step 15 (WF_PROPOSE_BLOCK_V0)
PPS status:  NOT PRESENT — must author
```
Runtime binding for WF_PROPOSE_BLOCK_V0. Maps CC implementations to their concrete runtime handlers. Follows the same pattern as existing `blockchain::RB_REGISTER_VALIDATOR_V0`. Binds: all 6 new CCs (Steps 8–11, 13, 14) to their runtime implementations.

---

## Dependency Graph Summary

```
Wave 1 (parallel):
    Step 1  STRUCTURE extend
    Step 2  CT_PURE_SELECT_PROPOSER_V0
    Step 3  IN_VALIDATOR_REGISTERED_V0
    Step 4  IN_BLOCK_PROPOSED_V0
    Step 5  EV_BLOCK_PROPOSED_V0
    Step 6  EV_ROUND_SKIPPED_V0

Wave 2 (parallel, after Step 1):
    Step 7   CC_WRITE_VALIDATOR_RECORD_V0          ← needs Step 1
    Step 8   CC_QUERY_PENDING_TRANSACTIONS_V0       ← needs Step 1
    Step 9   CC_FORM_BLOCK_V0                       ← needs Steps 1, 5
    Step 10  CC_SKIP_ROUND_V0                       ← needs Steps 1, 6
    Step 11  CC_RECORD_CONSENSUS_ROUND_V0           ← needs Step 1

Wave 3 (parallel, after respective deps):
    Step 12  WF_REGISTER_VALIDATOR_V0               ← needs Steps 3, 7
    Step 13  CC_SELECT_PROPOSER_V0                  ← needs Step 2

Wave 4 (after Step 12):
    Step 14  CC_QUERY_ELIGIBLE_VALIDATORS_V0        ← needs Steps 1, 12

Wave 5 (after Steps 4, 8–11, 13, 14):
    Step 15  WF_PROPOSE_BLOCK_V0

Wave 6 (after Step 15):
    Step 16  RB_PROPOSE_BLOCK_V0
```

Minimum critical path: 1 → 7 → 12 → 14 → 15 → 16 (6 sequential steps with parallel work available at each wave).

---

## Authoring Notes

**Subdomain field in JSON:** Each artifact's JSON must declare its subdomain explicitly. This CR authors artifacts under three subdomain values:
- `subdomain: "consensus_pos"` — Steps 2–4, 6, 10–15 (all consensus_pos artifacts)
- `subdomain: "block"` — Steps 5, 9 (blockchain::block artifacts: EV_BLOCK_PROPOSED_V0, CC_FORM_BLOCK_V0)
- `subdomain: "transaction"` — Step 8 (CC_QUERY_PENDING_TRANSACTIONS_V0 — transaction-owned)

**Cross-subdomain calls in WF_PROPOSE_BLOCK_V0:** The WF references CCs from different subdomains (transaction, block). This is a cross-subdomain capability call within the `blockchain` domain — permitted. The WF DAG declares these CCs by FQDN; the runtime resolves them from the snapshot regardless of subdomain.

**REPLACE semantics:** REPLACE means the existing artifact is superseded by a new version at the same FQDN. The new artifact carries the same code (V0) but correct pipeline provenance. In PGS, versioning is immutable — a REPLACE that changes behavior must increment the version. For WF_REGISTER_VALIDATOR_V0: the topology is unchanged; provenance and schema are corrected. Whether this warrants V1 is an authoring-phase decision deferred to the author.

**blockchain::block is a new subdomain:** CC_FORM_BLOCK_V0 and EV_BLOCK_PROPOSED_V0 are the establishing artifacts of a new governed subdomain. STRUCTURE_BLOCKCHAIN_STORAGE_V0 already registers their stores. Future CRs against `blockchain::block` (attestation, finalization) extend this subdomain.

---

## Pipeline Provenance

| Stage | Output | Status |
| --- | --- | --- |
| Stage 0 — Classification | change_request_subdomain | COMPLETE |
| Stage 1 — Input Elicitation | Problem + Outcome + Known Facts | COMPLETE |
| Stage 2 — Domain Model Discovery | Actors, Entities, Resources, Events, Relationships | COMPLETE |
| Stage 3 — Analysis Loop | Capability Graph, Dependency Graph, Constraints, Gap Register | COMPLETE — SATURATED |
| Stage 4 — Business Model | 4_business_model_consensus_pos_v0.md | COMPLETE |
| Stage 4b — Authoring Scope | IN/FUTURE CR boundary | COMPLETE — APPROVED |
| Stage 5 — Business Intent | 5_business_intent_consensus_pos_v0.md | COMPLETE |
| Stage 6 — Governance Intent | 6_governance_intent_consensus_pos_v0.md | COMPLETE — APPROVED |
| Stage 6b — Design Intent | 6b_design_intent_consensus_pos_v0.md | COMPLETE — APPROVED |
| Stage 7 — Authoring Plan | This document | COMPLETE |

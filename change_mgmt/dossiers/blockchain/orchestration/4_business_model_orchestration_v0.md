# Business Model: blockchain / orchestration
**Domain:** blockchain  
**Subdomain:** orchestration  
**Version:** V0  
**Status:** COMPLETE  
**Pipeline Stage:** Stage 4 — Business Model (canonical artifact)  
**Produced by:** v0.5.0 SDLC authoring pipeline  
**change_request type:** change_request_subdomain  
**Discovery Saturation:** REACHED (2 iterations)  
**Purity Filter:** APPLIED — design decisions and reference models separated  

---

## 1. Domain Ontology (Stages 1–3 accumulated output)

### Actors

| Actor | Description |
|-------|-------------|
| Simulation Operator | The actor (system or human) that initiates a chain simulation run by supplying configuration parameters. Carries no domain semantics beyond triggering the governed entry point — analogous to an HTTP caller or cron trigger. |

*Note: The Simulation Operator is a transport-layer concept — it fires the entry point. All business coordination after invocation is owned by the orchestration subdomain.*

### Entities

| Entity | Scope | Description |
|--------|-------|-------------|
| Simulation Run | IN SCOPE | A bounded, governed execution of the full chain simulation — consensus loop and TX workload running concurrently. Has a definite start and a definite end. Terminal states: COMPLETE or FAILED. |
| Slot Clock | IN SCOPE | Protocol-visible state representing the current position of the simulation in the slot sequence. Owned by orchestration. Replaces the external script's sleep-based timing. |
| Simulation Configuration | IN SCOPE | The declared input parameters governing a simulation run: slot_duration_seconds, max_slots, tx_interval_seconds, tx_sequence (with pre-resolved payloads), triggered_by. Passed at launch; not mutable during execution. |
| Simulation Summary | IN SCOPE | The governed output artifact recording the simulation outcome: slots_processed, blocks_proposed, transactions_submitted, transactions_confirmed, violations_detected. Produced at simulation completion. |

*Entities owned by dependency subdomains (not re-declared here):*
- *Block, Consensus Round — consensus_pos subdomain*
- *Transaction, Mempool — transaction and mempool subdomains*

### Resources

| Resource | Description |
|----------|-------------|
| Mempool (read/drain) | Owned by the mempool subdomain. Consumed by slot execution during block proposal. Read and drained by WF_PROPOSE_BLOCK_V0. |
| Validator pool | Owned by the consensus_pos subdomain. Consumed by slot execution during proposer selection. |
| Actor and wallet records | Owned by identity and wallet subdomains. Consumed by TX workload (pre-resolved into seed payloads at simulation configuration time). |

### Events

| Event | Scope | Description |
|-------|-------|-------------|
| SimulationStarted | IN SCOPE | Emitted when simulation controller begins concurrent worker dispatch. |
| SlotExecuted | IN SCOPE | Emitted once per slot after WF_PROPOSE_BLOCK_V0 completes (block proposed or round skipped). |
| TransactionSubmitted | SATISFIED | Emitted by the transaction subdomain for each TX submitted by the workload. |
| SimulationCompleted | IN SCOPE | Emitted when both concurrent workers have completed and the simulation summary is recorded. |

### Relationships

```
Simulation Operator   --initiates-->           Simulation Run
Simulation Run        --governed_by-->          Simulation Configuration
Simulation Run        --produces-->             Simulation Summary
Simulation Run        --coordinates-->          Consensus Loop + TX Workload (concurrent)
Consensus Loop        --advances-->             Slot Clock (N → N+1 each slot)
Consensus Loop        --invokes_per_slot-->      Block Proposal (via consensus_pos)
TX Workload           --submits_per_interval-->  Transaction (via transaction subdomain)
Slot Clock            --supplies_context_to-->   Block Proposal (round_number, slot, epoch, timestamp)
Block Proposal        --reads_from-->            Mempool (pending TXs at proposal time)
Block Proposal        --drains-->               Mempool (after block formation)
```

---

## 2. Business Capability Graph

```
orchestration
├── Chain Simulation Launch
│       Start the consensus loop and TX workload as concurrent workers under
│       governed coordination, declare termination criteria, wait for both to complete.
│       (CRITICAL — no governed simulation controller exists)
│
├── Slot Progression
│       Govern slot-by-slot execution of the consensus loop. Each slot is a discrete
│       governed execution unit: read slot clock → derive slot context → execute
│       block proposal → advance slot clock → check termination.
│       (CRITICAL — no slot execution unit separated from TX dispatch exists)
│
├── TX Workload Execution
│       Govern independent TX submission workload running concurrently with slot
│       progression. Determine next TX type from sequence → submit TX → wait
│       interval → check termination.
│       (CRITICAL — no governed TX workload coordinator exists)
│
└── Simulation Recording
        Aggregate sub-workflow results and record a governed simulation summary
        artifact. Produce SUCCESS or VIOLATION outcome with full output fields.
        (CRITICAL — no governed simulation summary recording exists)
```

*Implementation candidates (Design Decisions Register — not Business Model):*
- *asyncio.gather / threading model → transport-layer implementation detail*
- *CS substrate for concurrent dispatch → Design Intent (Stage 6b)*
- *Slot clock storage format → Design Intent (Stage 6b)*
- *TX payload resolution strategy → resolved in seed (Stage 3 decision, confirmed)*

---

## 3. Business Dependency Graph

```
Chain Simulation Launch
    ↓ coordinates concurrently
Slot Progression + TX Workload Execution

Slot Progression
    ↓ requires
Block Proposal capability            ← SATISFIED — consensus_pos::WF_PROPOSE_BLOCK_V0

TX Workload Execution
    ↓ requires
TX Submission capability             ← SATISFIED — typed TX WFs (WF_MINT_V0, WF_TRANSFER_V0, etc.)
    ↓ requires
Mempool Write capability             ← SATISFIED — consumed by WF_SUBMIT_TRANSACTION_V0 → WF_PROPOSE_BLOCK_V0

All Simulation Work
    ↓ requires (pre-condition)
Environment Preparation              ← BOOTSTRAP PRE-CONDITION — actors, wallets, validators seeded
                                       before simulation start; not owned by orchestration
```

Topological build order (dependency-driven):
1. Simulation Configuration Seed (provides pre-resolved payloads + launch params)
2. Slot Clock Store entity (governed state substrate for slot position)
3. Slot Execution Unit (depends on: Slot Clock + Block Proposal capability)
4. Consensus Loop Coordinator (depends on: Slot Execution Unit + Slot Clock)
5. TX Workload Coordinator (depends on: TX Submission capabilities)
6. Concurrent Worker Dispatch (depends on: Consensus Loop + TX Workload)
7. Simulation Controller (depends on: Concurrent Worker Dispatch + Simulation Recording)
8. Simulation Summary Recording (depends on: sub-WF execution results aggregation)

---

## 4. Constraint Register

```
1. One slot = one governed invocation = one trace = complete
   No perpetual loop WFs; every WF must terminate.
   Source: PGS Core Doctrine (loop workflows violate execution model)

2. TX workload runs independently and concurrently with slot progression
   TXs are not bound to specific slots; they enter the mempool freely.
   Source: Stage 1 — Part 3C (TX Workload Model)

3. Slot state is protocol-visible governed state
   slot_number, slot_start_ts, slot_duration_seconds are owned by orchestration — not
   by an external timer or script variable.
   Source: Stage 1 — Part 3B (Slot Execution Model)

4. PGS governs orchestration intent, not execution mechanics
   PGS declares what runs, when, and under what conditions. Threads, asyncio, and OS
   timers are transport-layer implementation details that the protocol does not govern.
   Source: Stage 1 — Part 3D (Concurrency Principle)

5. Bootstrap is a pre-condition for orchestration
   Orchestration does not create actors, wallets, or validators. That work must be
   complete before orchestration is invoked.
   Source: Stage 1 — Part 3A (Bootstrap vs. Orchestration Boundary)

6. Termination criteria are declared at simulation launch
   max_slots and max_transactions are configuration inputs — not runtime decisions.
   Source: Stage 2 — Simulation Configuration entity

7. TX types are parametric, not hardcoded in orchestration logic
   Orchestration knows "submit transaction"; TX taxonomy (MINT, TRANSFER, etc.) is
   carried in the simulation configuration seed as pre-resolved payload objects.
   Source: Stage 3 — Q5 revision (IN_TRANSACTION_SUBMITTED_V0 RETIRED; typed schemas incompatible)

8. Simulation outcome is SUCCESS or VIOLATION with full output fields
   SUCCESS = all slots executed + workload completed + no invariant violations.
   VIOLATION = any sub-workflow failure or invariant breach.
   Source: Stage 2 — Q4 (termination contract)

9. Orchestration invokes governed WFs — never reaches into dependency subdomain CCs
   Cross-domain boundary: orchestration → consensus_pos WF → consensus_pos CCs.
   Source: Stage 2 — Q2 decision (clean layering)

10. WF_RUN_CONSENSUS_SLOTS_V0 is a historical artifact — not deprecated, not reused
    It remains in snapshot unchanged. Its two bundled responsibilities are separated into
    WF_PROCESS_SLOT_V0 and WF_RUN_CONSENSUS_LOOP_V0. No versioning of the old artifact.
    Source: Stage 2 — Q1 decision; Stage 3 — confirmed
```

---

## 5. PPS Baseline Comparison

| Concept | PPS Status | Analysis Result |
|---------|------------|-----------------|
| Block proposal (select proposer, form block, drain mempool) | WF_PROPOSE_BLOCK_V0 | SATISFIED — exact match; invoked by WF_PROCESS_SLOT_V0 |
| Typed TX submission (MINT, TRANSFER, BURN, STAKE, UNSTAKE, POOL, REWARD, SLASH) | WF_MINT_V0 etc. | SATISFIED — invoked by TX workload coordinator via dispatch mapping |
| Single WF invocation substrate | CS_WORKFLOW_GATEWAY_V0 | SATISFIED — reused by WF_PROCESS_SLOT_V0 |
| Sequential loop substrate | CS_WORKFLOW_LOOP_V0 | SATISFIED — reused by WF_RUN_CONSENSUS_LOOP_V0 and WF_RUN_TX_WORKLOAD_V0 |
| Mutable JSON store substrate | CS_MUTABLE_JSON_V0 | SATISFIED — reused for Slot Clock store (READ + WRITE operations) |
| Slot clock (protocol-visible slot state) | — | CRITICAL gap — no governed slot state store exists |
| Concurrent WF dispatch | — | CRITICAL gap — no CS for concurrent execution exists |
| Simulation controller | — | CRITICAL gap — no governed simulation launcher/terminator exists |
| Consensus loop coordinator | — | CRITICAL gap — no governed coordinator for repeated slot execution exists |
| TX workload coordinator | — | CRITICAL gap — no governed coordinator for repeated TX submission exists |
| Discrete slot execution unit (TX-agnostic) | — | CRITICAL gap — WF_RUN_CONSENSUS_SLOTS_V0 bundles TX dispatch (incompatible) |
| Slot/epoch derivation from round_number | — | CRITICAL gap — no CT for slot = round_number % 32; epoch = round_number // 32 |
| Simulation configuration seed | — | CRITICAL gap — slot_specs.json carries per-slot TX binding (incompatible) |
| Simulation summary recording | — | CRITICAL gap — no governed artifact records simulation outcome |
| Orchestration compiler structure | — | CRITICAL gap — no STRUCTURE_BUILD for orchestration subdomain exists |
| WF_SUBMIT_TRANSACTION_V0 | IN_TRANSACTION_SUBMITTED_V0 RETIRED | NOT USED — IN_TRANSACTION_SUBMITTED_V0 is RETIRED; typed TX schemas are incompatible |
| WF_RUN_CONSENSUS_SLOTS_V0 | EXISTS (consensus_pos) | HISTORICAL — bundles TX dispatch + slot execution; superseded by new artifacts; not deprecated |

---

## 6. Gap Register

**Primary output. Drives Authoring Scope and Stage 5.**

```
Desired State − Current PPS = What to Build

CRITICAL: Concurrent Workflow Dispatch capability
              No governed artifact declares concurrent WF execution intent.
              CS_WORKFLOW_GATEWAY_V0 and CS_WORKFLOW_LOOP_V0 are both sequential.
              Required by: Simulation Controller (concurrent worker launch).

CRITICAL: Simulation Controller
              No governed artifact owns: starting concurrent workers, declaring
              termination criteria, or waiting for both workers to complete.
              Required by: Chain Simulation Launch business capability.

CRITICAL: Consensus Loop Coordinator
              No governed coordinator for repeated slot execution exists.
              Must use Collatz loop pattern (CS_WORKFLOW_LOOP_V0); terminates at max_slots.
              Required by: Slot Progression business capability.

CRITICAL: TX Workload Coordinator
              No governed coordinator for repeated TX submission exists.
              Must use Collatz loop pattern (CS_WORKFLOW_LOOP_V0) with typed WF dispatch mapping;
              terminates at max_transactions.
              Required by: TX Workload Execution business capability.

CRITICAL: Discrete Slot Execution Unit
              No single-slot execution WF exists that is TX-agnostic.
              WF_RUN_CONSENSUS_SLOTS_V0 bundles TX dispatch — incompatible with concurrent
              independent TX workload model.
              Required by: Slot Progression, Consensus Loop Coordinator.

CRITICAL: Slot/Epoch Derivation (pure computation)
              No CT for slot = round_number % slots_per_epoch; epoch = round_number // slots_per_epoch.
              Required by: Discrete Slot Execution Unit (before WF_PROPOSE_BLOCK_V0 invocation).
              IN_BLOCK_PROPOSED_V0 requires slot and epoch fields explicitly.

CRITICAL: Slot Clock Store
              No protocol-visible state for slot position exists.
              CS_MUTABLE_JSON_V0 is the correct substrate; a new STRUCTURE entity and
              governing CCs are required to declare and operate the clock.
              Required by: Slot Progression (read before execution, advance after execution).

CRITICAL: Simulation Configuration Seed
              slot_specs.json carries per-slot TX binding — incompatible with independent
              concurrent TX workload model.
              New seed at seeds/blockchain/orchestration/ with: slot_duration_seconds,
              max_slots, tx_interval_seconds, max_transactions, tx_sequence (fully resolved
              TX payload objects per tx_type).
              Required by: Simulation Controller, TX Workload Coordinator.

CRITICAL: Simulation Summary Recording
              No governed artifact records simulation outcome (slots_processed,
              blocks_proposed, transactions_submitted, transactions_confirmed,
              violations_detected).
              Required by: Chain Simulation Launch (SUCCESS/VIOLATION contract).

CRITICAL: Orchestration Compiler Structure
              No STRUCTURE_BUILD artifact declares the orchestration subdomain,
              its clock store entity, and its artifact families.
              Required by: compiler (Phase A build for orchestration subdomain).

SATISFIED: Block proposal — WF_PROPOSE_BLOCK_V0 (consensus_pos)
SATISFIED: Typed TX submission — WF_MINT_V0, WF_TRANSFER_V0, WF_BURN_V0, WF_STAKE_V0,
           WF_UNSTAKE_V0, WF_POOL_V0, WF_REWARD_V0, WF_SLASH_V0
SATISFIED: Single WF invocation — CS_WORKFLOW_GATEWAY_V0
SATISFIED: Sequential loop — CS_WORKFLOW_LOOP_V0
SATISFIED: Mutable JSON store — CS_MUTABLE_JSON_V0
```

**Discovery Saturation conditions met (Stage 3, Iteration 2):**
1. No unresolved CRITICAL gaps — all 9 CRITICAL items explicitly identified and bounded
2. No open analyst questions — Q1–Q5 fully resolved; Q5 revision confirmed
3. No dependency expansion in last iteration — Iteration 2 resolved its own introduced dependencies

---

## 7. Design Decisions Register

*Decisions from Stages 1–3 that constrain Design Intent. Each locks in an architectural choice.*

| # | Decision | Rationale | Constraints Imposed |
|---|----------|-----------|---------------------|
| D1 | Transport-layer concurrency model (Model A): asyncio.gather at transport layer; PGS runtime remains single-WF-invocation | PGS governs orchestration intent, not execution mechanics; no WF spawning/lifecycle/sync primitives; determinism preserved | No Temporal/Airflow-style WF lifecycle management; physical concurrency is RB implementation detail only |
| D2 | Supersede WF_RUN_CONSENSUS_SLOTS_V0 — new concern = new artifact; historical preservation | WF has two bundled concerns (TX dispatch + slot execution) that must be separated; versioning would imply same thing | WF_RUN_CONSENSUS_SLOTS_V0 and CC_EXECUTE_SLOT_SEQUENCE_V0 stay in snapshot unchanged; no deprecation action this CR |
| D3 | WF_PROCESS_SLOT_V0 → WF_PROPOSE_BLOCK_V0 (not consensus CCs) | Clean cross-domain layering; orchestration orchestrates WFs, never reaches into another domain's CCs | Orchestration cannot call consensus_pos CCs directly; all consensus_pos access via its own WF |
| D4 | SEED_CHAIN_SIMULATION_CONFIG_V0 — seed, not mutable CS | Configuration is launch-time input, not mutable runtime state; seed is the correct PGS location | Configuration is fixed at simulation start; no runtime config mutation during simulation |
| D5 | SUCCESS/VIOLATION contract with 5 output fields | Simulation controller is analogous to a governed test runner; full outcome auditability required | WF_RUN_CHAIN_SIMULATION_V0 must aggregate sub-WF results into simulation summary |
| D6 | TX workload dispatches to typed WFs via dispatch mapping (NOT WF_SUBMIT_TRANSACTION_V0) | IN_TRANSACTION_SUBMITTED_V0 is RETIRED; typed TX schemas are structurally incompatible; one general intent cannot satisfy MINT vs. TRANSFER field requirements | Seed must contain fully resolved TX payload objects per tx_type; orchestration cannot use generic TX submission |
| D7 | Slot clock as protocol-visible governed state (owned by orchestration) | External sleep-based timing is unauditable, ungoverned, undetectable drift; clock must be inspectable | All slot timing logic migrates from test script into orchestration; test script becomes thin config entry point |
| D8 | WF_RUN_CONSENSUS_SLOTS_V0 to receive lifecycle retirement metadata | Retirement should be discoverable in artifact header; successor artifacts must be referenced | lifecycle.status = RETIRED + replacement list added during authoring pass; full AR_ retirement framework is a future governance CR |

---

## 8. Authoring Scope

### In Scope — This CR

| Capability / Artifact | Gap Register Ref |
|-----------------------|-----------------|
| Concurrent Workflow Dispatch (new CS) | GAP: Concurrent Workflow Dispatch |
| Simulation Controller WF | GAP: Simulation Controller |
| Consensus Loop Coordinator WF | GAP: Consensus Loop Coordinator |
| TX Workload Coordinator WF | GAP: TX Workload Coordinator |
| Discrete Slot Execution Unit WF | GAP: Discrete Slot Execution Unit |
| Slot/Epoch Derivation CT (pure) | GAP: Slot/Epoch Derivation |
| Slot Clock Store (STRUCTURE entity + governing CCs) | GAP: Slot Clock Store |
| Simulation Configuration Seed | GAP: Simulation Configuration Seed |
| Simulation Summary Recording CC | GAP: Simulation Summary Recording |
| Orchestration Compiler Structure | GAP: Orchestration Compiler Structure |
| Refactor scripts/test_blockchain_e2e.py → thin config entry point | Stage 1 — Part 2 (desired outcome) |
| WF_RUN_CONSENSUS_SLOTS_V0 lifecycle retirement metadata | D8 design decision |

### Deferred — Future CRs

| Capability | Deferred Reason |
|-----------|-----------------|
| AR_ governed retirement artifact family | Requires new PGS artifact type declaration (pgs_governance CR); one use case does not justify the machinery |
| Compiler enforcement for RETIRED artifacts | Depends on AR_ family definition; future governance CR |
| WF_PROCESS_EPOCH_V0 (epoch-level coordination) | Not confirmed as distinct business concern in V0; epoch is an emergent property of slot progression |
| Distributed orchestration (lease, lock, leader election) | No multi-node model justified yet; second use case required before abstracting |
| Generic pgs_orchestration substrate | No second domain use case yet; abstract when pattern repeats independently |
| Event subscription / dispatch registry | YAGNI — one use case does not justify dispatch machinery |
| Simulation failure retry and slot expiry governance | Requires failure model design; future CR |

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 0 — Classification | 1_change_request_orchestration_v0.md | COMPLETE |
| Stage 1 — Input Elicitation | 1_input_elicitation_orchestration_v0.md | COMPLETE |
| Stage 2 — Domain Model Discovery | 2_domain_model_orchestration_v0.md | COMPLETE |
| Stage 3 — Analysis Loop | 3_analysis_loop_orchestration_v0.md | COMPLETE — SATURATED (2 iterations) |
| Stage 4 — Business Model | This document | PENDING APPROVAL |
| Stage 5 — Business Intent | 5_business_intent_orchestration_v0.md | PENDING |
| Stage 6 — Governance Intent | 6_governance_intent_orchestration_v0.md | PENDING |
| Stage 6b — Design Intent | 6b_design_intent_orchestration_v0.md | PENDING |
| Stage 7 — Authoring Mandate | 7_authoring_mandate_orchestration_v0.md | PENDING |
| Stage 8 — Authoring Manifest | 8_authoring_manifest_orchestration_v0.md | PENDING |

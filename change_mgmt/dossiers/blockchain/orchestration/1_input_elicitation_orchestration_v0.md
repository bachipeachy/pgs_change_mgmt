# Stage 1 — Input Elicitation: blockchain / orchestration
**Stage:** 1 — Input Elicitation  
**CR:** 1_change_request_orchestration_v0.md  
**Status:** COMPLETE  
**Feeds:** Stage 2 — Domain Model Discovery  

---

## Part 1 — Problem Statement

The blockchain domain has no governed mechanism for coordinating the concurrent, time-driven execution of long-running domain behaviors. Scheduling, slot progression, timing, and work distribution are performed outside the governance boundary by an external test script that acts as the de facto orchestrator. The result is:

- Slot state (which slot is current, when it started, how long it runs) is external, invisible, and unauditable — it lives as a sleep interval in a script, not as governed protocol state
- The concurrent execution of the consensus loop and the transaction submission workload is coordinated by imperative script logic, not by a governed protocol artifact
- There is no declared boundary between environment preparation (creating actors, wallets, validators before operation begins) and operational coordination (governing what runs, when, and in what sequence once the system is operating)
- All business-level coordination rules — slot count, slot duration, TX interval, TX sequence, termination criteria — are hardcoded in the test script outside the governance boundary

This is not a concurrency problem. PGS already models logically concurrent actors (users, wallets, validators, API callers). What is missing is governed orchestration: a protocol-owned declaration of what long-running domain behaviors run, under what conditions, and in what coordination relationship.

---

## Part 2 — Business Final Outcome

By end of this CR:

- A governed `blockchain::orchestration` subdomain exists, owning the coordination of long-running blockchain domain behaviors after environment preparation is complete
- Slot state is protocol-visible, auditable, governed state — every slot advancement is a governed, traceable action, not a sleep call in a script
- The consensus loop and TX submission workload run concurrently under governed coordination — their schedules, termination criteria, and dispatch decisions are protocol artifacts, not script logic
- One governed action equals one workflow execution equals one trace — no internal iteration, no perpetual loop workflows
- The external entry point (test harness, cron, timer) becomes a thin transport-layer signal carrying only configuration parameters; all business coordination logic after invocation is governed
- Scheduling (when something runs) and physical concurrency (how it runs) are formally separated — PGS governs orchestration intent; the runtime/transport layer owns execution mechanics
- `scripts/test_blockchain_e2e.py` is reduced to a thin config/param entry point; all orchestration logic it currently owns is moved into the governed subdomain

The system gains the following structural properties:
- **Traceable:** every slot, every coordinated TX submission, every termination decision produces a trace
- **Governed:** all coordination rules (slot duration, TX interval, max slots, TX sequence, stop condition) are declared protocol artifacts, not implementation choices
- **Auditable:** slot clock state can be inspected at any point; the current slot is protocol-visible state
- **Extensible:** the orchestration boundary is stable — future domains (ai_governance, change_mgmt) can declare their own orchestration subdomains using the same pattern without structural rework

---

## Part 3 — Current Business Knowledge

### A. Bootstrap vs. Orchestration Boundary

Environment preparation and operational coordination are two distinct concerns with a stable boundary:

- **Bootstrap** owns: creating actors, wallets, and validators — all preparation that must complete before the system begins operating. Bootstrap is a pre-condition for orchestration, not a part of it.
- **Orchestration** owns: governing when and in what sequence business workflows execute after the system begins operating — slot progression, concurrent TX submission, termination, dispatch decisions.

Orchestration does not become a dumping ground for setup logic. The boundary is: operation begins → orchestration takes over.

### B. Slot Execution Model

Each slot is a discrete governed execution unit:
- One slot = one governed invocation = one trace = complete
- Slot state (current slot number, slot start timestamp, slot duration in seconds) is protocol-visible state owned by the orchestration subdomain, not an external timer variable
- Slot progression — advancing from slot N to slot N+1 — is itself a governed, traceable action
- The external timer (or test harness) is a dumb firing mechanism, analogous to an HTTP request: it carries no domain semantics; it triggers a governed execution and then gets out of the way
- A workflow that never terminates naturally violates the PGS execution model. There are no perpetual loop workflows. Every execution has a declared entry, deterministic behavior, and a complete outcome.

### C. TX Workload Model

Transaction submission is a separate concurrent workload with its own governed configuration:
- TX workload is governed by: TX interval (seconds between submissions), TX sequence (ordered list of transaction types), and max transaction count
- TX types are parametric (MINT, TRANSFER, BURN, STAKE, UNSTAKE) — not hardcoded in orchestration logic
- Each individual TX submission is a discrete governed execution unit: one TX submission = one governed invocation = one trace = complete
- The TX workload coordinator governs repeated invocations of the discrete TX submission unit; it does not iterate internally

### D. Concurrency Principle — PGS Governs Intent, Not Mechanics

This CR establishes a foundational architectural principle:

**PGS governs orchestration intent, not execution mechanics.**

| PGS governs | PGS does NOT govern |
|-------------|---------------------|
| What work may run | Threads |
| When work may run | asyncio / event loops |
| Under what conditions it may run | CPU scheduling |
| How often it may run | OS timers |
| How slot progression advances | Process scheduling |
| Termination criteria | Physical concurrency primitives |

Scheduling ("run consensus every 3 seconds") and concurrency ("consensus and TX generation progress simultaneously") are distinct concerns. Scheduling is a governed timing rule — it belongs in a protocol artifact. Physical concurrency is an execution mechanic — it belongs in the transport layer or runtime implementation.

For V0: the simulation controller declares the intent ("start consensus loop, start TX workload, wait for both to complete"). How that is physically executed (asyncio.gather, threading.Thread, multiprocessing) is a transport-layer implementation detail that the protocol does not govern and does not need to know.

This keeps the runtime:
- Deterministic
- Single-WF-invocation semantics
- Trace-producing
- Protocol-governed

With no internal scheduler, no WF spawning/lifecycle/joins, no WF synchronization primitives — and no scope expansion into Temporal/Airflow territory.

### E. Simulation Controller Hierarchy

The orchestration subdomain contains a four-level execution hierarchy (illustrative — final names resolved in later stages):

```
Simulation Controller
    owns: simulation clock, termination criteria, dispatch decisions
    starts: consensus loop coordinator + TX workload coordinator concurrently
    waits for: both coordinators to complete

Consensus Loop Coordinator
    owns: slot count, slot duration configuration
    governs: repeated invocations of the slot execution unit
    does NOT internally iterate — each slot is a separate governed invocation

TX Workload Coordinator
    owns: TX interval, TX sequence, max TX count
    governs: repeated invocations of the TX submission unit
    does NOT internally iterate — each TX submission is a separate governed invocation

Slot Execution Unit
    one slot = one governed invocation = one trace = complete

TX Submission Unit
    one TX = one governed invocation = one trace = complete
```

### F. Existing Infrastructure Available for Reuse

The following governed capabilities are already deployed and available for reuse — no rewrite required:

- Consensus slot processing capability (propose block, select proposer, form block, record consensus round) — governed and tested
- Transaction submission capability (build, sign, hash, validate, persist) — governed and tested
- Mempool read and drain capability (query pending transactions, drain after block formation) — governed and tested
- All existing e2e test coverage (24/24 consensus slots, 8 TX types) remains valid as regression baseline

---

## Analyst Notes

- **Purity Filter active from this stage forward.** Business concepts only through Stage 5. No artifact family names (CC_, WF_, CS_, CT_) until Stage 6b.
- **No event subscription model in V0.** Event registry, subscription dispatch, and routing rules are explicitly deferred. YAGNI — one use case does not justify dispatch machinery.
- **Distributed orchestration deferred.** Lease, distributed lock, leader election, and cross-node coordination are future CR territory. No second use case yet; abstraction would be premature.
- **WF_PROCESS_EPOCH_V0 scope:** not confirmed for V0. Deferred to Stage 2 domain modeling — confirm whether epoch-level coordination is a distinct business concern or an emergent property of slot progression.
- **Open question for Stage 2:** What are the distinct actors in the orchestration lifecycle? The simulation controller, slot executor, and workload runner — are these distinct protocol actors or all subsumed under the orchestration subdomain as governed execution roles?
- **Open question for Stage 2:** What events does orchestration emit? Slot completed, TX submitted, simulation started, simulation completed — which are governed observability signals vs. internal coordination state?
- **Open question for Stage 3:** How does the simulation controller learn that both the consensus loop and TX workload have completed? What is the governed termination protocol between concurrent coordinators? Does the PPS have any existing termination or completion signaling pattern to reuse?
- **Open question for Stage 3:** Does the slot execution unit directly invoke existing consensus capabilities (propose block, finalize block) or does it coordinate through the mempool read/drain interface only? Clarify ownership of the slot execution chain.

# Stage 1 — Input Elicitation: blockchain / consensus_propose
**Stage:** 1 — Input Elicitation
**CR:** 1_change_request_consensus_propose_v0.md
**Status:** COMPLETE
**Feeds:** Stage 2 — Domain Model Discovery

---

## Problem

The blockchain domain has a governed block proposal path and eight governed typed transaction submission paths. All artifacts compile and build successfully but have never been invoked or tested against real data. Entities carry no canonical data — balances are seeded at zero, transactions are unexercised, and no block has ever been proposed with realistic field values.

The governed data model is complete — entities have the right fields, typed transaction workflows are compiler-validated, events are declared, and the token economy has its initial supply. What is absent is any exercise of the consensus lifecycle that feeds canonical data through the governed paths and produces a verifiable, persisted result.

Without this CR, the system can govern the submission of value but cannot demonstrate it.

---

## Outcome

End-to-end invocation of all eight typed transaction workflows against canonical domain data — actors, wallets, and validators populated with realistic values — culminating in at least one persisted block in PROPOSED state with realistic field values. The result must be demonstrable and verifiable.

The test harness built for this CR is designed for extension: as attestation, finalization, and chain commitment are governed in sister CRs, the same test script grows to cover them without a rewrite.

Attestation, finalization, and chain commitment are explicitly deferred to sister CRs (`consensus_attest`, `consensus_finalize`).

---

## Known Facts

| Fact | Source |
|------|--------|
| All workflows and artifact concerns added in the data_model CR compile and build successfully | PPS snapshot — data_model CR |
| None of the eight typed transaction workflows have ever been invoked at runtime | Runtime test record (none exists) |
| The regression test strategy feeds a batch of transactions at 20-second intervals to a consensus loop running on a 30-second slot cycle — matching ETH slot timing. The loop reads from the mempool and proposes a block. For this CR, the block is persisted in PROPOSED state only. | Test plan — JIT |
| `genesis_actor` exists as a seeded system actor | seeds/genesis_actor.json |

---

## Analyst Notes

- **Purity filter active.** No artifact family names through Stage 5.
- The genesis_actor bootstrapping the first block is a design question, not a known fact — deferred to Stage 2.
- **Open question for Stage 2:** What canonical data set is needed per entity type (actors, validators, wallets) to make the demo meaningful? Minimum cardinality per type?
- **Open question for Stage 2:** Does the test harness belong inside the governed protocol (a governed seed or test workflow) or outside it (a script that invokes governed workflows)? Governance implications differ.
- **Open question for Stage 3:** Do the eight typed transaction workflows require any new capability wiring (CS implementations) before they can execute at runtime, or are all CS paths already wired in the current baseline?

# Business Model: consensus_pos
**Domain:** blockchain  
**Subdomain:** consensus_pos  
**Version:** V0  
**Status:** DRAFT  
**Pipeline Stage:** Stage 4 — Business Model (canonical artifact)  
**Produced by:** v0.5.0 SDLC analysis pipeline  
**change_request type:** change_request_subdomain  
**Discovery Saturation:** REACHED  
**Purity Filter:** APPLIED — design decisions and reference models separated  

---

## Domain Ontology (Stage 2 — Domain Model Discovery)

### Actors

| Actor | Description |
| --- | --- |
| Validator | A governed actor enrolled in consensus participation; must meet qualification criteria and hold active status to participate in block proposal |

### Entities

| Entity | Scope | Description |
| --- | --- | --- |
| Block | IN SCOPE | The unit of state proposed by a selected Validator each consensus round; contains references to submitted transactions |
| Consensus Round | IN SCOPE | The atomic time unit of consensus: one proposer is selected, one block is proposed (or the round is skipped) |
| Chain | PRE-WIRED | The ordered record of agreed blocks; structural placeholder; populated by attestation and finalization (future scope) |

*Note: Consensus Round maps to "Slot" in ETH PoS vocabulary — see Reference Models.*

### Roles (transient assignments on Validator — not separate actor types)

| Role | Scope |
| --- | --- |
| Proposer | IN SCOPE — one Validator assigned per Consensus Round |
| Attestor | FUTURE |
| Finalizer | FUTURE |

### Resources

| Resource | Description |
| --- | --- |
| Stake | Qualification credential held by Validator; signals commitment and accountability |

### Events

| Event | Scope | Description |
| --- | --- | --- |
| BlockProposed | IN SCOPE | A Validator has proposed a block for the current consensus round |
| RoundSkipped | ADVISORY | A consensus round completed with no block proposed (no pending transactions) |

### Relationships

```
Validator  --qualifies_through-->  Stake               (credential establishing participation right)
Validator  --enrolled_in-->        ValidatorRegistry    (active participation record)
Validator  --selected_as-->        Proposer             (per Consensus Round)
Validator  --proposes-->           Block                (as assigned Proposer)
Block      --references-->         Transactions         (submitted transactions pending inclusion)
Block      --belongs_to-->         Chain                (upon attestation — future scope)
Consensus Round --produces-->      Block or RoundSkipped
```

---

## Business Capability Graph (Stage 3a — business level)

```
consensus_pos
├── Validator Participation
│       Who may participate in consensus and under what conditions
│       (qualification, enrollment, active status, exclusion)
│
├── Consensus Coordination
│       How agreement on the next block producer is reached each round
│       (selection from eligible pool; one producer per round)
│
├── Block Formation
│       How a block is assembled from pending transactions and recorded
│       (collect pending transactions; construct block; persist; emit event)
│       (skip round and record when no transactions are pending)
│
└── Chain Advancement
        How agreed blocks become part of the permanent ordered record
        (pre-wired structural placeholder; populated by attestation — future scope)
```

*Implementation candidates (Design Decisions Register — not Business Model):*
- *Selection algorithm (rotation, random, weighted) → underneath Consensus Coordination*
- *Transaction collection mechanism → underneath Block Formation*
- *Pool size limit → underneath Validator Participation*
- *Consensus loop interval → test configuration*

---

## Business Dependency Graph (Stage 3b)

```
Block Formation
    ↓ requires
Consensus Coordination (proposer must be selected before block is formed)
    ↓ requires
Validator Participation (active pool must exist before selection)
    ↓ requires
Actor Identity                    ← SATISFIED — identity subdomain (PPS)

Block Formation
    ↓ requires
Submitted Transactions            ← SATISFIED — transaction subdomain (PPS)
```

Topological build order (dependency-driven):
1. Validator Participation (depends on identity — SATISFIED)
2. Consensus Coordination (depends on Validator Participation)
3. Block Formation (depends on Consensus Coordination + Submitted Transactions)
4. Chain Advancement (structural placeholder; no execution dependency this CR)

---

## Constraint Discovery (Stage 3c — business requirements only)

```
- Only validators meeting qualification criteria may be selected as Proposer
- Only one Proposer is selected per Consensus Round
- A Consensus Round with no pending transactions produces no block
- The ledger is append-only — blocks are not removed or modified once proposed
- Single chain — no competing forks resolved in this CR
- Qualification requires active enrollment status and a declared stake credential
- System-designated actors may be excluded from participation (inactive status)
- Stake is a declaration of commitment — enforcement mechanisms (slashing) are future scope
```

---

## PPS Baseline Comparison (Stage 3d)

| Concept | PPS Status | Oracle Result |
| --- | --- | --- |
| Actor registry | WF_REGISTER_ACTOR_UNVERIFIED_V0, WF_VERIFY_ACTOR_V0 | SATISFIED |
| Actor resolution | CC_RESOLVE_ACTOR_ID_V0 | SATISFIED |
| Transaction submission | WF_SUBMIT_TRANSACTION_V0 | SATISFIED |
| Submitted transaction persistence | CC_PERSIST_MEMPOOL_TX_V0 | SATISFIED |
| Validator registration | WF_REGISTER_VALIDATOR_V0 | REPLACE — produced through flawed pipeline; GI gate skipped; semantic alignment unverified |
| Validator enrollment store | — | CRITICAL gap |
| Active participation pool | — | CRITICAL gap |
| Consensus Coordination capability | — | CRITICAL gap |
| Block entity + formation capability | — | CRITICAL gap |
| Block Proposal workflow | — | CRITICAL gap |
| Consensus Round entity | — | CRITICAL gap |
| Chain entity placeholder | — | ADVISORY (pre-wire only) |
| Stake as qualification field | — | ADVISORY (field only, no enforcement workflow) |
| RoundSkipped event | — | ADVISORY |

---

## Gap Register (Stage 3e — at Discovery Saturation)

**Primary output. Drives Authoring Plan.**

```
Desired State − Current PPS = What to Build

REPLACE:   WF_REGISTER_VALIDATOR_V0
               Flawed Goal 1 pipeline; GI gate skipped; semantic alignment unverified.
               Must be re-authored through correct governed pipeline.

CRITICAL:  Validator Enrollment Store
               The data store recording active participation status and qualification.
               Required by: Consensus Coordination.

CRITICAL:  Active Participation Pool
               The governed record of which validators are eligible each round.
               Required by: Consensus Coordination.

CRITICAL:  Consensus Coordination capability
               How one Validator is selected as Proposer each Consensus Round.
               Required by: Block Formation.

CRITICAL:  Consensus Round entity
               The atomic unit of consensus (one selection, one block or skip).
               Required by: Block Formation workflow.

CRITICAL:  Block entity + formation capability
               Construction, persistence, and event emission for a proposed block.
               Required by: Block Proposal workflow.

CRITICAL:  WF_PROPOSE_BLOCK_V0
               New governed workflow: select proposer → collect transactions →
               form block → persist → emit event (or skip round).

ADVISORY:  Chain entity placeholder
               Structural pre-wire for future attestation and finalization.

ADVISORY:  Stake as qualification field
               Declared on Validator enrollment record; no deposit/withdrawal this CR.

ADVISORY:  RoundSkipped event
               Emitted when no transactions are pending; useful for test validation.

SATISFIED: Actor Identity — identity subdomain (PPS)
SATISFIED: Transaction submission — transaction subdomain (PPS)
SATISFIED: Submitted transaction persistence — CC_PERSIST_MEMPOOL_TX_V0 (PPS)
```

**Discovery Saturation conditions met:**
1. No unresolved CRITICAL gaps — all six CRITICAL items explicitly identified and bounded
2. No unresolved analyst questions — scope confirmed (attestation/finalization/slashing deferred)
3. No dependency expansion in last review — Consensus Round surfaced and resolved; no further expansion

*ETH concepts confirmed during saturation probe: Slot → Consensus Round (in scope), Epoch → future scope, Checkpoint → future scope.*

---

## Authoring Scope Decision (Stage 4b)

Approved by Business Analyst.

**IN THIS CR:**
- WF_REGISTER_VALIDATOR_V0 (re-author correctly through governed pipeline)
- Validator Enrollment Store
- Active Participation Pool management
- Consensus Coordination (Proposer selection)
- Consensus Round
- Block Formation (build, persist, emit event, skip round)
- WF_PROPOSE_BLOCK_V0
- Chain entity placeholder (pre-wire only)
- Test script (consensus loop driver + transaction submission driver)

**FUTURE CRs:**
- Block attestation
- Block finalization and chain population
- Slashing (stake enforcement)
- Rewards
- Epoch / Checkpoint concepts
- Multi-node configuration
- Live validator enrollment sync from identity

---

## Design Decisions Register (deferred to Protocol Intent — Stage 6b)

*These entered the analysis as implementation terms. Business facts substituted above.*

| Decision | Business Fact (in model) | Deferred to |
| --- | --- | --- |
| Round-robin rotation | "One Validator selected as Proposer per Consensus Round" | Protocol Intent |
| 30s consensus loop interval | "Consensus rounds are time-bounded" | Test configuration |
| 20s transaction submission interval | "Transactions arrive continuously during test" | Test configuration |
| Pool size limit (10 validators) | "Active participation pool is bounded" | Protocol Intent |
| tx_ids[] reference in block | "Block references submitted transactions" | Protocol Intent |
| Single-node only | "Single-node configuration for this CR" | Authoring constraint |

---

## Reference Models Register (inform Protocol Intent and authoring — not business analysis)

| Source | Cited for | Business Fact Extracted | Detail Deferred |
| --- | --- | --- | --- |
| ETH PoS | Proposer selection mechanism | "One Validator selected per Consensus Round" | RANDAO algorithm → Protocol Intent |
| ETH PoS | Slot / Epoch / Checkpoint terminology | Consensus Round (Slot) in scope; Epoch / Checkpoint future | ETH epoch = 32 slots → future CR |
| ETH PoS | Stake as accountability mechanism | "Stake is a qualification credential" | Slashing → future CR |
| BachiCoin `/Users/bp/BachiCoin/` | Reference implementation | — | Use at authoring phase only |

---

## Assumptions (Explicit)

```
1. Single-node configuration only — no peer discovery or network propagation this CR
2. External driver provides timing for consensus loop and transaction submission
3. Validator enrollment seeded at bootstrap — not live-synced from identity this CR
4. Block references transactions by identifier — no transaction data copied into block
5. Proposer selection mechanism is deterministic within a round — implementation TBD in Protocol Intent
6. Single chain — no fork choice algorithm this CR
7. Stake is a declared field — enforcement (slashing) is future scope
8. Test window is bounded — mempool drains within test duration
```

---

## Pipeline Provenance

| Stage | Output | Status |
| --- | --- | --- |
| Stage 0 — Classification | change_request_subdomain | COMPLETE |
| Stage 1 — Input Elicitation | Problem + Outcome + Known Facts | COMPLETE |
| Stage 2 — Domain Model Discovery | Actors, Entities, Resources, Events, Relationships | COMPLETE |
| Stage 3 — Analysis Loop | Capability Graph, Dependency Graph, Constraints, Gap Register | COMPLETE — SATURATED |
| Stage 4 — Business Model | This document | COMPLETE |
| Stage 4b — Authoring Scope | IN/FUTURE CR boundary | COMPLETE — APPROVED |
| Stage 5 — Business Intent | 5_business_intent_consensus_pos_v0.md | PENDING REWRITE |
| Stage 6 — Governance Intent (WHERE) | Pending | — |
| Stage 6b — Protocol Intent (HOW) | Pending | — |
| Stage 7 — Authoring Plan | Pending | — |

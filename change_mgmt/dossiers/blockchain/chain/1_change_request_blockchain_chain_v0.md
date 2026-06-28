# Stage 1 — Change Request: Clarification & Fact Capture: blockchain / chain
**Stage:** 1 — Change Request (Clarification & Fact Capture)  
**CR:** change_request_chain_v0.md  
**Status:** DRAFT  
**Feeds:** Stage 2 — Domain Model Discovery  

> **S1 interrogates; it does not author.** It captures *what is requested*, the *business
> semantics* (vocabulary, invariants, lifecycle states, business events, authority boundaries),
> *what the business definitively holds true*, *what the human believes the system already
> provides* (a hypothesis, not a fact), *what is assumed*, *what constrains*, and — most
> importantly — *what must be clarified before proceeding*. S1 is the primary human↔agent
> interaction stage: the agent does not guess, it asks. Implementation is deliberately out of view
> (S1 discovers, S2 models, S3 decides) — no design options, architectures, capability candidates,
> workflows, or artifact names appear here.

---

## Document Contract

**This artifact is a structured register document — not a narrative.** No Problem Statement /
Background / Business Need / Goals prose (those invite speculation). Capture facts and requests
as registers.

VALID OUTPUT:
- Populated register tables (every required register)
- Business-language statements; existing artifacts cited by FQDN ONLY in a Source Finding cell

INVALID OUTPUT:
- Narrative prose replacing registers; design options; recommended architecture; capability /
  workflow / artifact candidates (all premature at S1)

A required register with no rows MUST render as a single `| NONE IDENTIFIED |` row. The renderer
rejects a prose-only or empty register mechanically before any human reviews it.

---

### The three-way split (the heart of S1)

S1's job is to keep three kinds of statement from contaminating one another — the separation
that prevents semantic drift downstream:

- **Business Truth** (§4 Known Facts) — what the business *authoritatively decides or requires*.
  The human owns these. They do not require snapshot inspection. Certainty is HIGH unless the
  human is genuinely unsure. Example: *"initial supply shall be 1,000,000 BachiCoin."*
- **System Belief** (§5 Existing-System Beliefs) — what the human *believes the system already
  provides*. The human is NOT authoritative here; the snapshot is. These are **discovery targets**
  the agent grounds in Stage 2, each with a **Verification Goal** — never asserted as fact at S1.
  Example: *"a consensus loop that proposes blocks may already exist."*
- **Clarification** (§14) — an unresolved question the agent must ask rather than guess, tagged
  with its **Owner** (who can answer: HUMAN, SNAPSHOT, or GOVERNANCE).

A statement about current system state is a **System Belief**, never a Known Fact. A business
decision is a **Known Fact**, never a System Belief. When you would guess either, raise a
**Clarification** instead.

### The business-semantics model (what S3 consumes to eliminate guesswork)

Six registers together form the human-authoritative semantic model so downstream stages discover
topology *in service of* meaning, not the reverse: **Business Vocabulary** (§2, the objects),
**Business Invariants** (§8, what must always hold), **Lifecycle States** (§9, the states an
object moves through), **Business Events** (§10, the moments that matter), and **Authority
Boundaries** (§11, who is authoritative for each object — the transition that drives S3's
REUSE-vs-AUTHOR_NEW calls). A NEW_SUBDOMAIN CR is incomplete without these.

---

### Business-Language Rule

Every CONTENT/DESCRIPTION cell is a business-language statement — NO protocol artifact names,
FQDNs, workflow/capability/intent/event names, or register bindings (those arrive at Stage 5+).
If a fact is supported by an existing artifact, cite that FQDN ONLY in the row's `source_finding`
(evidence) column — never in the statement itself.

VALID: "the running system already registers validators"  
INVALID: "WF_REGISTER_VALIDATOR_V0 exists"

---

### Stage 1 execution rules

- **Vocabulary first.** Every domain term the CR depends on (§2) is defined in business language
  before it is used — definitions are governed evidence, not implicit knowledge.
- **Truths ≠ Beliefs ≠ Requests.** Business Truths (§4) are human-authoritative decisions/
  requirements. System Beliefs (§5) are unverified hypotheses about what exists → discovery
  targets. Requested Outcomes (§3) are what the requester wants. Never merge them.
- **Known Facts are business truths only.** A claim about what the system currently does is a
  System Belief (§5), not a Known Fact — even if the human is confident.
- **Every System Belief carries a Verification Goal** — what Stage 2 must establish to confirm or
  refute it — so grounding is scoped to this CR, not the whole domain inventory.
- **State the business semantics explicitly** (§8–§11): invariants, lifecycle states, events, and
  authority boundaries are human-authoritative business truths, not implementation. S3 uses them
  to eliminate competing designs.
- **Every fact carries a certainty** (HIGH | MEDIUM | LOW). A belief you could not verify is a
  Clarification request — not a HIGH fact.
- **Every clarification carries an Owner.** Do not ask the human what only the snapshot can answer
  (Owner = SNAPSHOT) — route it to discovery instead.
- **Every row carries a `source_finding`** (human statement, seed answer ref, or grounded FQDN).
- **When you would guess, ask instead.** Anything not established becomes a
  `clarification_requests` row, not an assumption silently carried forward.

---

## 1. CR Type

*The classification of this change.*

<!-- register:cr_type business_language -->
| Classification (NEW_SUBDOMAIN, EXTEND_SUBDOMAIN, MODIFY, DEPRECATE) | Rationale | Source Finding |
|----------------|-----------|----------------|
| NEW_SUBDOMAIN | The canonical ledger (chain) is a distinct concern from block proposal and needs its own governance boundary; it is not an extension of an existing subdomain. | CR Seed §1 |

---

## 2. Business Vocabulary

*Every domain term this CR depends on, defined in business language. Governed definitions become
first-class evidence — they prevent every downstream stage from re-inferring what the human
already means. Define the term, not its implementation.*

<!-- register:business_vocabulary business_language -->
| Term | Definition | Source Finding |
|------|------------|----------------|
| Chain | The authoritative, ordered, append-only ledger of committed blocks. (Canonical chain or canonical ledger are synonyms.) | CR Seed §2 |
| Block | A unit of the ledger produced by a proposer and recorded on the chain; carries the transactions of its round. | CR Seed §2 |
| Proposed Block | A block produced by a proposer in the consensus loop, not yet committed and not yet authoritative. | CR Seed §2 |
| Commit | To make a proposed block part of the canonical chain: its content is hashed as its signature, it is linked to its predecessor, and it is recorded as canonical. Commit is irreversible; on commit the block and its contained transactions become immutable and authoritative. | CR Seed §2 |
| Genesis Block | The chain's first block. It has the same form as any block and contains the first system transaction — a mint crediting the MINT wallet — performed by the Genesis Actor. | CR Seed §2 |
| Bootstrap | The one-time genesis sequence that establishes the initial chain and supply, before the consensus loop runs. | CR Seed §2 |
| Genesis Actor | The special, permanent actor that receives the initial minted supply at bootstrap and owns the MINT wallet thereafter. | CR Seed §2 |
| Proposer | The validator selected to produce a block in a given round. | CR Seed §2 |
| BachiCoin | The system's unit of value; the supply is a closed monetary system. | CR Seed §2 |

---

## 3. Requested Outcomes

*What the requester wants to be true at close — business outcomes, not solutions.*

<!-- register:requested_outcomes business_language -->
| Outcome | Source Finding |
|---------|----------------|
| Establish a closed, canonical chain (ledger) that commits proposer-produced blocks to an authoritative, append-only record. | CR Seed §3.1 |
| Bootstrap the chain from a genesis block that mints the initial supply to a Genesis Actor before the consensus loop runs. | CR Seed §3.2 |
| Commit all proposed blocks directly to the chain — emulating the ETH proof-of-stake model validators → proposers, with attestors and finalizers deferred to future iterations. | CR Seed §3.3 |

---

## 4. Known Facts — Business Truths

*Only statements the human is authoritative about: business decisions and requirements. NOT
statements about what the system currently provides (those are §5 System Beliefs). Certainty
∈ HIGH | MEDIUM | LOW; source is the human (or an explicit human-cited authority).*

<!-- register:known_facts business_language -->
| Fact | Certainty (HIGH, MEDIUM, LOW) | Source Finding |
|------|-----------|----------------|
| A canonical chain (ledger) is required as the authoritative record of committed blocks. | HIGH | CR Seed §4.#1 |
| A genesis bootstrap is required, and must occur before consensus execution begins. | HIGH | CR Seed §4.#2 |
| The genesis block shall mint an initial supply of 1,000,000 BachiCoin. | HIGH | CR Seed §4.#3 |
| The initial supply shall be assigned to a Genesis Actor, which is permanent and owns the MINT wallet. | HIGH | CR Seed §4.#4 |
| Minting occurs only during genesis bootstrap; no minting and no burning occur in this release. | HIGH | CR Seed §4.#5 |
| For this development increment, all proposer-produced blocks are committed to the chain. | HIGH | CR Seed §4.#6 |
| Attestation and finalization are intentionally deferred to a future iteration. | HIGH | CR Seed §4.#7 |
| Consensus proposes; the chain records and is the authoritative source of committed history. | HIGH | CR Seed §4.#8 |
| In this release, the chain commits every proposed block without additional validation. | HIGH | CR Seed §4.#9 |
| On commit, a block and its contained transactions become authoritative and immutable. | HIGH | CR Seed §4.#10 |

---

## 5. Existing-System Beliefs — Requiring Verification

*What the human BELIEVES the system already provides — hypotheses, not facts. The human is not
authoritative here; the snapshot is. Each row is a Stage-2 discovery target: `Why It Matters`
scopes the grounding to this CR, and `Verification Goal` states what Stage 2 must establish to
confirm or refute the belief (governing workflow(s), producers, emitted records, ownership).*

<!-- register:system_beliefs business_language -->
| Belief | Why It Matters | Verification Goal | Source Finding |
|--------|----------------|-------------------|----------------|
| The current implementation does NOT yet provide a chain that commits proposed blocks. | This CR exists to fill that gap; if a commit capability already exists, the CR scope changes. | Confirm no existing capability commits proposed blocks to a ledger. | CR Seed §5.#1 |
| A consensus loop already exists that proposes blocks and drives slot processing. | The chain commits exactly the blocks this loop proposes — its upstream producer. | Identify the governing workflow(s), their producers, the records emitted, and the owning subdomain. | CR Seed §5.#2 |
| A block-proposal capability already exists. | Defines the input the chain commit consumes. | Identify the capability that produces a proposed block and the record/shape it emits. | CR Seed §5.#3 |
| A validator registry already exists. | Validators feed proposer selection upstream of the chain. | Identify where validators are registered and how proposer selection reads it. | CR Seed §5.#4 |
| A wallet capability already exists. | Genesis mints the initial supply to the MINT wallet held by the Genesis Actor. | Identify the wallet capability and how a balance/mint is recorded. | CR Seed §5.#5 |
| A transaction capability already exists. | Part of the pipeline actor → wallet → transaction → mempool. | Identify the transaction capability and its place in that pipeline. | CR Seed §5.#6 |
| A mempool already exists. | Transactions queue there before block formation. | Identify the mempool store and how transactions queue before a block is formed. | CR Seed §5.#7 |
| An orchestration subdomain already exists. | Drives slot processing / the consensus loop. | Identify the orchestration/slot-processing driver and what it invokes. | CR Seed §5.#8 |
| Adjacent subdomains exist: identity, wallet, transaction, mempool, consensus_pos, orchestration. | Establishes the neighborhood the new chain subdomain plugs into. | Confirm each named subdomain exists and note its owning boundary. | CR Seed §5.#9 |

---

## 6. Assumptions

*Things taken as true WITHOUT full evidence — each with its basis. If an assumption is
load-bearing and unverified, prefer raising a clarification request instead.*

<!-- register:assumptions business_language optional -->
| Assumption | Basis | Source Finding |
|------------|-------|----------------|
| All proposed blocks are good and are committed as finalized (no rejection path this increment). | Incremental-development decision; attest/finalize deferred. | CR Seed §6 |

---

## 7. Constraints

*Non-negotiable rules the change must honor (monetary, governance, regulatory, immutability, …).*

<!-- register:constraints business_language -->
| Constraint | Source | Source Finding |
|------------|--------|----------------|
| Closed monetary system — no supply enters or leaves except by the system's own rules. | Business policy | CR Seed §7.1 |
| The chain is immutable — a committed block cannot be altered or removed. | Business policy | CR Seed §7.2 |
| Genesis supply is fixed at 1,000,000 BachiCoin, minted to the Genesis Actor at bootstrap. | Business policy | CR Seed §7.3 |

---

## 8. Business Invariants

*Properties that must ALWAYS hold true of the domain — business truths stated as invariants, not
implementation rules. S3 uses these to eliminate competing designs (a design that violates an
invariant is inadmissible). Each is a single, testable business statement.*

<!-- register:business_invariants business_language -->
| Invariant | Source Finding |
|-----------|----------------|
| Exactly one genesis block exists per chain. | CR Seed §8.#1 |
| Genesis executes exactly once at bootstrap and is never replayed. | CR Seed §8.#2 |
| Total supply is conserved and equals 1,000,000 BachiCoin (no minting or burning after genesis). | CR Seed §8.#3 |
| A committed block is immutable — it never changes or disappears. | CR Seed §8.#4 |
| Every committed block has exactly one predecessor, except the genesis block. | CR Seed §8.#5 |
| A block cannot be committed twice. | CR Seed §8.#6 |
| The canonical chain is the authoritative source of committed history; a proposed block is not authoritative until committed. | CR Seed §8.#7 |

---

## 9. Lifecycle States

*The states each core business object moves through, in business language. S3 uses these to scope
the state transitions a design must support (and the ones it must not). One row per object-state.*

<!-- register:lifecycle_states business_language -->
| Object | State | Meaning | Source Finding |
|--------|-------|---------|----------------|
| Chain | Uninitialized | No genesis block yet; the chain is not established. | CR Seed §9.Chain.Uninitialized |
| Chain | Active | Genesis created; the chain accepts and commits blocks. | CR Seed §9.Chain.Active |
| Block | Proposed | Produced by a proposer; not yet committed and not authoritative. | CR Seed §9.Block.Proposed |
| Block | Committed | Recorded in the canonical chain; immutable and authoritative. | CR Seed §9.Block.Committed |
| Genesis Block | Created Once | The single first block, established at bootstrap; permanent. | CR Seed §9.Genesis.CreatedOnce |

---

## 10. Business Events

*The business moments that matter — the events the domain must recognize. Stated in business
language (not artifact/event-code names). One row per event.*

<!-- register:business_events business_language -->
| Event | When It Occurs | Significance | Source Finding |
|-------|----------------|--------------|----------------|
| Genesis Created | Once, at bootstrap, before the consensus loop runs. | Establishes the chain and the initial monetary state. | CR Seed §10.Genesis.Created |
| Block Proposed | When a proposer produces a block in a round. | A candidate block exists; not yet authoritative. | CR Seed §10.Block.Proposed |
| Block Committed | When a proposed block is committed to the canonical chain. | The block and its contained transactions become authoritative and immutable. | CR Seed §10.Block.Committed |

---

## 11. Authority Boundaries

*Who is authoritative for each core business object — and where authority transitions. S3 uses
these to drive REUSE-vs-AUTHOR_NEW: an authority handoff (e.g. proposed→committed) is exactly the
boundary a design must respect. State the owner in business terms, not artifact names.*

<!-- register:authority_boundaries business_language -->
| Business Object | Authoritative Owner | Source Finding |
|-----------------|---------------------|----------------|
| Proposed Block | Consensus | CR Seed §11.ProposedBlock→Consensus |
| Committed Block | Chain | CR Seed §11.CommittedBlock→Chain |
| Committed History | Chain | CR Seed §11.History→Chain |
| Monetary Supply | Genesis at bootstrap, then Chain | CR Seed §11.Supply→Genesis/Chain |
| Wallet Balance | Chain | CR Seed §11.Balance→Chain |

---

## 12. Out of Scope

*Explicitly excluded from this CR — deferred to future CRs. State the release boundary
explicitly so downstream stages do not chase future-state architecture.*

<!-- register:out_of_scope business_language optional -->
| Item | Reason | Source Finding |
|------|--------|----------------|
| The Attest step of the PoS progression. | Deferred to a future iteration; all proposed blocks treated as good this increment. | CR Seed §12.Attest |
| The Finalize step of the PoS progression. | Deferred to a future iteration; proposed blocks committed directly. | CR Seed §12.Finalize |
| Fork resolution. | Not part of this release; the chain commits every proposed block. | CR Seed §12.ForkResolution |
| Chain reorganization (reorg). | Not part of this release; committed history is immutable. | CR Seed §12.Reorg |
| Slashing. | Validator penalties are out of scope this release. | CR Seed §12.Slashing |
| Rewards. | Validator/proposer rewards are out of scope this release. | CR Seed §12.Rewards |

---

## 13. Governance Scope

*Which governance concerns this CR touches, in business terms (not artifact bindings). Each scope
item declares its `Relationship` to this CR — what the CR does to/with that boundary.*

<!-- register:governance_scope business_language -->
| Scope Item | Relationship (CREATED, ADJACENT) | Source Finding |
|------------|----------------|----------------|
| chain | CREATED | CR Seed §13.chain.CREATED |
| consensus_pos | ADJACENT | CR Seed §13.consensus_pos.ADJACENT |
| orchestration | ADJACENT | CR Seed §13.orchestration.ADJACENT |
| wallet | ADJACENT | CR Seed §13.wallet.ADJACENT |
| transaction | ADJACENT | CR Seed §13.transaction.ADJACENT |
| mempool | ADJACENT | CR Seed §13.mempool.ADJACENT |
| identity | ADJACENT | CR Seed §13.identity.ADJACENT |

---

## 14. Clarification Requests

*The keystone register: the agent does NOT guess — it asks. Every unresolved uncertainty that
could change the design is a row here. Blocking ∈ YES (cannot proceed until answered) | NO.
Owner ∈ HUMAN (only the requester can answer) | SNAPSHOT (discovery answers it in Stage 2) |
GOVERNANCE (a governance/topology decision). Do not ask the human a SNAPSHOT question.*

<!-- register:clarification_requests business_language optional -->
| Question | Why Needed | Blocking (YES, NO) | Owner (HUMAN, SNAPSHOT, GOVERNANCE) | Source Finding |
|----------|------------|----------|-------|----------------|
| NONE IDENTIFIED |  |  |  |  |

---

## 15. Acceptance Criteria

*How the requester will judge the CR satisfied at close — the S8 acceptance boundary. Each
criterion must be business-observable: testable by a business reviewer without inspecting runtime
internals.*

<!-- register:acceptance_criteria business_language -->
| Criterion | Source Finding |
|-----------|----------------|
| The chain begins with a genesis block that records the assignment of the initial 1,000,000 BachiCoin supply to the Genesis Actor. | CR Seed §15.1 |
| Blocks accepted by the chain appear in the authoritative ledger in proposal order. | CR Seed §15.2 |
| A block recorded in the ledger never changes or disappears. | CR Seed §15.3 |
| The total recorded supply on the ledger is 1,000,000 BachiCoin, held initially by the Genesis Actor. | CR Seed §15.4 |
| Once committed, a block and its contained transactions are treated as authoritative. | CR Seed §15.5 |

---

## gov_projection — Governed Handoff to Stage 2

*Governed, lossless, identity-preserving (Stage 0 / field manual §4.7). Emit keys match the
register ids above exactly. Business Vocabulary, Truths, Invariants, Lifecycle States, Events and
Authority Boundaries cross as authoritative business semantics; System Beliefs cross as Stage-2
discovery targets (verified, never trusted). Blocking clarification requests are resolved by the
human at the S1 gate before Stage 2 proceeds.*

| Direction | Fields |
|-----------|--------|
| **Consumes** ← CR seed | human elicitation answers (the seed) |
| **Emits** → Stage 2 | cr_type · business_vocabulary · requested_outcomes · known_facts · system_beliefs · assumptions · constraints · business_invariants · lifecycle_states · business_events · authority_boundaries · out_of_scope · governance_scope · clarification_requests · acceptance_criteria |

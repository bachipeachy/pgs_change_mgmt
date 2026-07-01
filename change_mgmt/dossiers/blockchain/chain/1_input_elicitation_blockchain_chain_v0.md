# CR Seed — blockchain / chain

The **human-provided elicitation** that S1 (Clarification & Fact Capture) consumes. Human input
only — no agent-derived content. Organized one section per S1 register so the agent maps each
section directly, with the **three-way split** kept clean:

- **Business Truths** (§4) — what the business authoritatively decides/requires. Human-authoritative.
- **System Beliefs** (§5) — what the human *believes* already exists. NOT facts — Stage-2 discovery
  targets the agent must verify against the snapshot, each with a Verification Goal.
- **Clarifications** (§14) — open questions the agent must ask, never guess.

The agent must not promote a System Belief to a Known Fact, and must not invent design. The
business semantics (§2 vocabulary, §8 invariants, §9 lifecycle states, §10 events, §11 authority
boundaries) are human-authoritative and let Stage 2 discover topology in service of meaning.

- **Domain:** blockchain
- **Primary subdomain:** chain — NEW
- **Secondary subdomain:** none
- **CR version:** V0

---

## Subdomain Purpose (foundational business context — human, non-derivable)

*The one irreducible business narrative no compiled artifact can derive: what this subdomain
governs and why it exists. Stated once here, at the source; consumed downstream (e.g. S5 §1),
never rediscovered.*

The Chain subdomain maintains the official blockchain ledger. It records every block that has been
accepted by the network and preserves the complete history of the blockchain from the beginning.
Other subdomains decide which blocks should be accepted, but the Chain subdomain is responsible for
maintaining the authoritative record once that decision has been made. This authoritative ledger is
the foundation that the rest of the blockchain system relies on.

---

## 1. CR Type

**NEW_SUBDOMAIN** — `blockchain/chain`.
Rationale: the canonical ledger ("chain") is a distinct concern from block *proposal* and needs
its own governance boundary; it is not an extension of an existing subdomain.

## 2. Business Vocabulary (governed definitions — business language, not implementation)

| Term | Definition |
|------|------------|
| Chain | The authoritative, ordered, append-only ledger of committed blocks. ("Canonical chain"/"canonical ledger" are synonyms.) |
| Block | A unit of the ledger produced by a proposer and recorded on the chain; carries the transactions of its round. |
| Proposed Block | A block produced by a proposer in the consensus loop, not yet committed and not yet authoritative. |
| Commit | To make a proposed block part of the canonical chain: its content is hashed as its signature, it is linked to its predecessor, and it is recorded as canonical. Commit is irreversible; on commit the block and its contained transactions become immutable and authoritative. |
| Genesis Block | The chain's first block. It has the same form as any block and contains the first system transaction — a mint crediting the MINT wallet — performed by the Genesis Actor. |
| Bootstrap | The one-time genesis sequence that establishes the initial chain and supply, before the consensus loop runs. |
| Genesis Actor | The special, permanent actor that receives the initial minted supply at bootstrap and owns the MINT wallet thereafter. |
| Proposer | The validator selected to produce a block in a given round. |
| BachiCoin | The system's unit of value; the supply is a closed monetary system. |

## 3. Requested Outcomes (business outcomes the human wants at close)

1. Establish a closed, canonical **chain (ledger)** that commits proposer-produced blocks to an
   authoritative, append-only record.
2. **Bootstrap** the chain from a **genesis block** that mints the initial supply to a Genesis
   Actor *before* the consensus loop runs.
3. *(Interim, this increment)* Commit **all proposed blocks directly** to the chain — emulating
   the ETH proof-of-stake model validators → proposers → ~~attestors → finalizers~~, the last two
   steps deferred to future iterations.

## 4. Known Facts — Business Truths (human-authoritative; agent assigns certainty)

| # | Fact | Certainty |
|---|------|-----------|
| 1 | A canonical chain (ledger) is required as the authoritative record of committed blocks. | HIGH |
| 2 | A genesis bootstrap is required, and must occur before consensus execution begins. | HIGH |
| 3 | The genesis block shall mint an initial supply of 1,000,000 BachiCoin. | HIGH |
| 4 | The initial supply shall be assigned to a Genesis Actor, which is permanent and owns the MINT wallet. | HIGH |
| 5 | Minting occurs only during genesis bootstrap; no minting and no burning occur in this release. | HIGH |
| 6 | For this development increment, all proposer-produced blocks are committed to the chain. | HIGH |
| 7 | Attestation and finalization are intentionally deferred to a future iteration. | HIGH |
| 8 | Consensus proposes; the chain records and is the authoritative source of committed history. | HIGH |
| 9 | In this release, the chain commits every proposed block without additional validation. | HIGH |
| 10 | On commit, a block and its contained transactions become authoritative and immutable. | HIGH |

## 5. Existing-System Beliefs — Requiring Verification (discovery targets, NOT facts)

*The human believes these already exist; the agent must verify each against the snapshot in
Stage 2. `Why it matters` scopes the grounding to this CR; `Verification Goal` states what Stage 2
must establish.*

| # | Belief (suspected) | Why it matters | Verification Goal |
|---|---------------------|----------------|-------------------|
| 1 | The current implementation does NOT yet provide a chain that commits proposed blocks. | This CR exists to fill that gap; if a commit capability already exists, the CR scope changes. | Confirm no existing capability commits proposed blocks to a ledger. |
| 2 | A consensus loop already exists that proposes blocks and drives slot processing. | The chain commits exactly the blocks this loop proposes — its upstream producer. | Identify the governing workflow(s), their producers, the records emitted, and the owning subdomain. |
| 3 | A block-proposal capability already exists. | Defines the input the chain commit consumes. | Identify the capability that produces a proposed block and the record/shape it emits. |
| 4 | A validator registry already exists. | Validators feed proposer selection upstream of the chain. | Identify where validators are registered and how proposer selection reads it. |
| 5 | A wallet capability already exists. | Genesis mints the initial supply to the MINT wallet held by the Genesis Actor. | Identify the wallet capability and how a balance/mint is recorded. |
| 6 | A transaction capability already exists. | Part of the pipeline actor → wallet → transaction → mempool. | Identify the transaction capability and its place in that pipeline. |
| 7 | A mempool already exists. | Transactions queue there before block formation. | Identify the mempool store and how transactions queue before a block is formed. |
| 8 | An orchestration subdomain already exists. | Drives slot processing / the consensus loop. | Identify the orchestration/slot-processing driver and what it invokes. |
| 9 | Adjacent subdomains exist: identity, wallet, transaction, mempool, consensus_pos, orchestration. | Establishes the neighborhood the new `chain` subdomain plugs into. | Confirm each named subdomain exists and note its owning boundary. |

## 6. Assumptions

| Assumption | Basis |
|------------|-------|
| All proposed blocks are good and are committed as finalized (no rejection path this increment). | Incremental-development decision; attest/finalize deferred (see §4.6, §4.7, §12). |

## 7. Constraints (non-negotiable, human)

| Constraint | Source |
|------------|--------|
| Closed monetary system — no supply enters or leaves except by the system's own rules. | Business policy |
| The chain is immutable — a committed block cannot be altered or removed. | Business policy |
| Genesis supply is fixed at 1,000,000 BachiCoin, minted to the Genesis Actor at bootstrap. | Business policy |

## 8. Business Invariants (always-true business truths)

| # | Invariant |
|---|-----------|
| 1 | Exactly one genesis block exists per chain. |
| 2 | Genesis executes exactly once at bootstrap and is never replayed. |
| 3 | Total supply is conserved and equals 1,000,000 BachiCoin (no minting or burning after genesis). |
| 4 | A committed block is immutable — it never changes or disappears. |
| 5 | Every committed block has exactly one predecessor, except the genesis block. |
| 6 | A block cannot be committed twice. |
| 7 | The canonical chain is the authoritative source of committed history; a proposed block is not authoritative until committed. |

## 9. Lifecycle States (states each core object moves through)

| Object | State | Meaning |
|--------|-------|---------|
| Chain | Uninitialized | No genesis block yet; the chain is not established. |
| Chain | Active | Genesis created; the chain accepts and commits blocks. |
| Block | Proposed | Produced by a proposer; not yet committed and not authoritative. |
| Block | Committed | Recorded in the canonical chain; immutable and authoritative. |
| Genesis Block | Created Once | The single first block, established at bootstrap; permanent. |

## 10. Business Events (the moments the domain must recognize)

| Event | When It Occurs | Significance |
|-------|----------------|--------------|
| Genesis Created | Once, at bootstrap, before the consensus loop runs. | Establishes the chain and the initial monetary state. |
| Block Proposed | When a proposer produces a block in a round. | A candidate block exists; not yet authoritative. |
| Block Committed | When a proposed block is committed to the canonical chain. | The block and its contained transactions become authoritative and immutable. |

## 11. Authority Boundaries (who is authoritative for each object)

| Business Object | Authoritative Owner |
|-----------------|---------------------|
| Proposed Block | Consensus |
| Committed Block | Chain |
| Committed History | Chain |
| Monetary Supply | Genesis at bootstrap, then Chain |
| Wallet Balance | Chain |

## 12. Out of Scope (human — explicit release boundary)

| Item | Reason |
|------|--------|
| The **Attest** step of the PoS progression. | Deferred to a future iteration; all proposed blocks treated as good this increment. |
| The **Finalize** step of the PoS progression. | Deferred to a future iteration; proposed blocks committed directly. |
| **Fork resolution.** | Not part of this release; the chain commits every proposed block. |
| **Chain reorganization (reorg).** | Not part of this release; committed history is immutable. |
| **Slashing.** | Validator penalties are out of scope this release. |
| **Rewards.** | Validator/proposer rewards are out of scope this release. |

## 13. Governance Scope (human, business terms)

| Scope Item | Relationship |
|------------|--------------|
| chain | CREATED |
| consensus_pos | ADJACENT |
| orchestration | ADJACENT |
| wallet | ADJACENT |
| transaction | ADJACENT |
| mempool | ADJACENT |
| identity | ADJACENT |

## 14. Clarification Requests

*The two prior blocking clarifications (what genesis produces; how commit differs from proposal)
have been answered by the human and folded into §2 Vocabulary and §4 Known Facts. No open blocking
questions remain.*

(none)

## 15. Acceptance Criteria (business-observable — testable without runtime internals)

1. The chain begins with a genesis block that records the assignment of the initial 1,000,000 BachiCoin supply to the Genesis Actor.
2. Blocks accepted by the chain appear in the authoritative ledger in proposal order.
3. A block recorded in the ledger never changes or disappears.
4. The total recorded supply on the ledger is 1,000,000 BachiCoin, held initially by the Genesis Actor.
5. Once committed, a block and its contained transactions are treated as authoritative.

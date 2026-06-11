# Stage 2 — Domain Model Discovery: blockchain / chain
**Stage:** 2 — Domain Model Discovery
**CR:** 1_change_request_blockchain_chain_v0.md
**Status:** DRAFT
**Feeds:** Stage 3 — Analysis Loop

---

## 1. Business Entities

### Block
A fundamental unit of the blockchain, containing a set of transactions, a header with metadata (e.g., timestamp, previous block hash), and a unique identifier. Blocks are proposed by validators and, once committed, form an immutable sequence. The full content of a block is stored separately from the chain itself.

| Attribute | Description |
|-----------|-------------|
| block_id | Unique identifier for the block (B-prefixed) |
| round_id | Consensus round number (block height) |
| slot | Slot number within the epoch |
| epoch | Epoch number |
| proposer_id | Actor ID of the validator who proposed the block |
| tx_ids | Ordered list of transaction IDs included in the block |
| timestamp | ISO 8601 timestamp of block formation |
| previous_block_hash | Cryptographic hash of the preceding block — NOT present on PROPOSED records; established at commitment |
| block_hash | Cryptographic hash of the block's content — NOT present on PROPOSED records; computed at commitment |
| is_canonical | Boolean indicating if this block is part of the canonical chain (false at proposal) |
| status | Current status of the block (PROPOSED at formation; COMMITTED at commitment) |

*Verified against PPS: the existing block formation capability assembles `block_id`, `round_id`, `slot`, `epoch`, `proposer_id`, `tx_ids`, `timestamp`, `status: PROPOSED`, `is_canonical: false`. It does NOT compute hashes. Cryptographic linkage is therefore a commitment-time concern owned by this CR.*

### Chain
The ordered, immutable sequence of *references* to committed blocks (e.g., `block_id`s or `block_hash`es), starting from a genesis block reference. It represents the authoritative history of all transactions and state changes in the blockchain. The chain itself does not store the full block contents, but rather pointers to them.

| Attribute | Description |
|-----------|-------------|
| current_head_block_id | The `block_id` of the most recently committed block reference in the chain |
| current_head_block_hash | The hash of the most recently committed block reference in the chain |
| current_block_height | The total number of blocks referenced in the chain (round_id of the head block) |
| genesis_block_id | The `block_id` of the first block referenced in the chain |
| genesis_block_hash | The hash of the first block referenced in the chain |

---

## 2. Business Processes

### Process 1 — Block Proposal
Validators propose blocks containing transactions from the mempool during a consensus round. This process results in a `PROPOSED` block, whose full content is stored in the `BLOCKS` store.

1. Eligible validators are queried.
2. A proposer is selected deterministically.
3. Pending transactions are claimed from the mempool.
4. A block is formed with these transactions and marked `PROPOSED`.
5. The mempool is drained of the claimed transactions.
6. The consensus round is recorded.

### Process 2 — Chain Initialization
The very first block, the genesis block (`BLOCKS[height=0]`), is created and its *reference* is committed to establish the beginning of the blockchain.

1. A genesis block record is defined with initial state and its full content is stored in the `BLOCKS` store.
2. The *reference* (e.g., `block_id` and `block_hash`) of the genesis block is added to the `CHAIN` store.
3. The `Chain` state is initialized with the genesis block reference as its head.

### Process 3 — Block Commitment
A `PROPOSED` block's *reference* is validated and added to the canonical chain, extending the blockchain's history. The full block content remains in its existing persistent location.

1. A `PROPOSED` block is identified for commitment.
2. The block's integrity (e.g., cryptographic linkage to the previous block) is verified.
3. The *reference* (e.g., `block_id` and `block_hash`) of the block is marked as `COMMITTED` and added to the `CHAIN` store.
4. The `Chain` state is updated to reflect the new head block reference.
5. An event is recorded for the block commitment.

---

## 3. PPS Baseline — What Already Exists

### WF_RUN_CONSENSUS_LOOP_V0
Orchestrates the execution of ordered slot sequences, which in turn process individual slots.
**Fit for this CR:** Partial — This workflow drives the overall consensus process, leading to block proposals. The new `chain` subdomain will be the ultimate destination for the *references* to blocks produced by this loop.

### WF_PROCESS_SLOT_V0
Processes a single blockchain slot, including reading the slot clock, preparing context, invoking block proposal, and advancing the slot clock. It calls `CC_INVOKE_BLOCK_PROPOSAL_V0`.
**Fit for this CR:** Partial — This workflow directly leads to the proposal of a block. The output of its `CC_INVOKE_BLOCK_PROPOSAL_V0` step (which calls `WF_PROPOSE_BLOCK_V0`) is a `PROPOSED` block whose *reference* the `chain` subdomain needs to commit.

### WF_PROPOSE_BLOCK_V0
Executes a consensus proposer selection round, claims transactions, forms a block (`CC_FORM_BLOCK_V0`), drains the mempool, and records the round. It produces a `PROPOSED` block.
**Fit for this CR:** Partial — This workflow is the direct source of `PROPOSED` blocks. The `chain` subdomain needs to consume the *reference* of the output of this workflow (the `PROPOSED` block) and commit it. It currently writes the full block content to the `BLOCKS` store.

### CC_FORM_BLOCK_V0
Forms a new block from selected transactions and round context, writes its full content to the `BLOCKS` store, and appends an event to `BLOCK_EVENTS`. It sets the block status to `PROPOSED`.
**Fit for this CR:** Partial — This CC creates the `PROPOSED` block record (full content). The `chain` subdomain needs a mechanism to transition this `PROPOSED` block's *reference* to a `COMMITTED` state and integrate it into the chain.

### STRUCTURE_BLOCKCHAIN_STORAGE_V0
Declares storage topology for blockchain domain entities, including `BLOCKS` (`blockchain/block/blocks/blocks.json`) and `BLOCK_EVENTS` (`blockchain/block/events/block_events.jsonl`).
**Fit for this CR:** Partial — It defines where `PROPOSED` blocks (full content) are stored. However, it does not define a dedicated `CHAIN` store for the ordered, canonical sequence of *references* to committed blocks, nor a `GENESIS_BLOCK` store. The `BLOCKS` store is currently mutable, which is suitable for `PROPOSED` blocks but not for the immutable `CHAIN` references. The `BLOCKS` store is owned by `blockchain::block` — any write to it must be performed by a `block`-owned capability.

### Existing Block Lifecycle Events (EV_BLOCK_*)
The PPS already declares the block lifecycle event vocabulary: `blockchain::EV_BLOCK_PROPOSED_V0` (canonical; emitted by `CC_FORM_BLOCK_V0`), `blockchain::EV_BLOCK_COMMITTED_V0`, `blockchain::EV_BLOCK_ATTESTED_V0`, and `blockchain::EV_BLOCK_FINALIZED_V0`. Notably, `EV_BLOCK_COMMITTED_V0` exists with its "Emitted By" declared as "(consensus finalization CR — next CR)" — it was reserved for exactly this CR.
**Fit for this CR:** Exact match for commitment signaling — `EV_BLOCK_COMMITTED_V0` is REUSED by this CR (its Emitted By table is updated to name the new commitment capability). No new block lifecycle event is required.

### WF_PROCESS_SLOT_V0 / CC_INVOKE_BLOCK_PROPOSAL_V0 (orchestration invocation pattern)
`WF_PROCESS_SLOT_V0` (orchestration) processes one slot: read slot clock → prepare context → invoke block proposal → advance slot clock. Sub-workflow invocation is performed by a gateway capability (`CC_INVOKE_BLOCK_PROPOSAL_V0` bound to `CS_WORKFLOW_GATEWAY_V0`) — events are records, not triggers, in this architecture.
**Fit for this CR:** Partial — this is the canonical integration point and pattern for chaining block commitment after proposal: the slot workflow is extended with a second gateway invocation. No event-subscription mechanism exists or is needed.

---

## 4. Gap Analysis — What Is Missing

### Gap 1 — Dedicated CHAIN store (CRITICAL)
There is no dedicated, immutable store for the canonical sequence of *references* to committed blocks. The existing `BLOCKS` store is mutable and intended for `PROPOSED` blocks (full content), not the immutable chain of references.

**Impact:** Without a `CHAIN` store, there is no authoritative, immutable record of the blockchain's history. Block commitment cannot be governed.

### Gap 2 — Genesis Block Orchestration (CRITICAL)
There is no explicit mechanism or store for defining and bootstrapping the initial `Genesis Block` for the `chain`. The genesis block content will reside in `BLOCKS[height=0]`. The gap is the orchestration of its creation and initial commitment.

**Impact:** The blockchain cannot be initialized with a starting point, preventing the formation of a continuous chain.

### Gap 3 — Block Commitment Capability (CRITICAL)
There is no capability contract (CC) or workflow (WF) to transition a `PROPOSED` block's *reference* to a `COMMITTED` state and add it to the canonical `CHAIN`.

**Impact:** Blocks remain in a `PROPOSED` state, and the blockchain cannot advance beyond block proposal.

### Gap 4 — Chain State Management (CRITICAL)
There is no governed entity or store to track the current state of the `Chain` (e.g., `current_head_block_id`, `current_block_height`).

**Impact:** It is impossible to determine the current head of the blockchain or its length, which is crucial for verifying new blocks and maintaining chain integrity.

### Gap 5 — Immutability Enforcement for Committed Blocks (CRITICAL)
The existing `BLOCKS` store is mutable. Once a block's *reference* is committed to the `CHAIN`, that reference within the `CHAIN` must be immutable. The `CHAIN` store itself must be append-only or immutable.

**Impact:** The integrity and security of the blockchain are compromised if committed block references can be altered within the `CHAIN`.

---

## 5. Summary: Extend vs. New Subdomain

**The question:** Does the concern of managing the canonical, immutable sequence of *references* to committed blocks (the "chain") belong inside `blockchain::block` or does it require `blockchain::chain`?

**Evidence for extend (blockchain::block):** The `blockchain::block` subdomain already handles the formation and storage of individual blocks (full content). One could argue that managing the sequence of *references* to these blocks is an extension.

**Evidence for new subdomain (blockchain::chain):** The "chain" represents a distinct governance concern from individual block formation. It deals with the *ordering*, *immutability*, and *canonical status* of block *references*, as well as the overall state of the blockchain (genesis, head, height). The `block` subdomain focuses on the *content* and *proposal* of a single block. The immutability requirement for the chain also suggests a different storage paradigm than the mutable `BLOCKS` store. This separation aligns with the principle of "one store per domain entity type" and distinct ownership boundaries.

---

## 6. Open Questions for Stage 3

| # | Question | Why It Matters |
|---|----------|---------------|
| Q1 | What is the exact definition and structure of the `CHAIN` store? It is confirmed to store *references* (e.g., `block_id` and `block_hash`) to blocks, not full block records. Should it be an append-only log of these references, or a different immutable structure? | Determines the storage mechanism and how block references are retrieved from the canonical chain. |
| Q2 | How is the `Genesis Block` created and committed? Is it a special case of `Block Commitment` (for its reference), or does it require a dedicated process? | Defines the bootstrapping mechanism for the blockchain. |
| Q3 | What are the specific integrity checks required for `Block Commitment` (e.g., previous hash verification, proof-of-work/stake validation) *before its reference is added to the chain*? | Establishes the rules for adding a block reference to the canonical chain. |
| Q4 | How will the `Chain` state (head block reference, height) be updated and stored atomically with `Block Commitment`? | Ensures consistency of the blockchain's current state. |
| Q5 | Given that `WF_PROPOSE_BLOCK_V0` produces `PROPOSED` blocks (full content), what is the trigger or mechanism to initiate the `Block Commitment` process (adding its reference to the chain) in the new `chain` subdomain? | Defines the integration point between block proposal and chain commitment. |
| Q6 | The `BLOCKS` store will continue to hold the full content of `PROPOSED` blocks. A new `CHAIN` store will be created to hold immutable *references* to committed blocks. What is the precise relationship between these two stores? | Clarifies storage ownership and immutability requirements. |

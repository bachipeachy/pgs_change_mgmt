# Stage 3 — Analysis Loop: blockchain / chain
**Stage:** 3 — Analysis Loop
**CR:** 1_change_request_blockchain_chain_v0.md
**Iterations:** 2 (saturated)
**Status:** COMPLETE
**Feeds:** Stage 4 — Business Model

*Iteration 1 resolved the Stage 2 questions. Iteration 2 is the PPS verification pass (quality check): it overturned the event-driven trigger design, corrected the hash-availability assumption, and surfaced existing artifacts that Iteration 1 missed. Where Iteration 2 contradicts Iteration 1, Iteration 2 governs.*

---

## Iteration 1

### Q1 — What is the exact definition and structure of the `CHAIN` store? It is confirmed to store *references* (e.g., `block_id` and `block_hash`) to blocks, not full block records. Should it be an append-only log of these references, or a different immutable structure?

**Finding:** The `CHAIN` store must be an immutable, ordered sequence of block references. An append-only log is the most suitable structure for this purpose, as it inherently supports immutability and ordering. Each entry in the log will contain the `block_id` and `block_hash` of a committed block, along with its `round_id` (block height) and `previous_block_hash` for cryptographic linkage.

**Evidence:**
*   `2_domain_model_blockchain_chain_v0.md` specifies the `Chain` entity as an "ordered, immutable sequence of *references* to committed blocks."
*   The conceptual model emphasizes "protocol sovereignty" and "governed evolution," implying that the core chain's integrity must be paramount, which an immutable, append-only structure provides.
*   `STRUCTURE_BLOCKCHAIN_STORAGE_V0` defines `CS_APPENDONLY_JSONL_V0` as a capability side effect for append-only event journals, which aligns with the requirements for an immutable log.

**Resolution:** A new `CHAIN` store is required, implemented as an append-only log of block references. This confirms Gap 1 from Stage 2. The `CHAIN` store will be distinct from the mutable `BLOCKS` store.

**Answer:** The `CHAIN` store will be an append-only log (`CS_APPENDONLY_JSONL_V0`) storing immutable references to committed blocks. Each entry will include `block_id`, `block_hash`, `round_id`, and `previous_block_hash`.

### Q2 — How is the `Genesis Block` created and committed? Is it a special case of `Block Commitment` (for its reference), or does it require a dedicated process?

**Finding:** The `Genesis Block` requires a dedicated orchestration process for its creation and initial commitment. It is a special case of block commitment because it lacks a `previous_block_hash` and includes initial state or configuration. Crucially, it also serves to fund the chain system with 1,000,000 BachiCoin in a "MINT" wallet owned by a specially privileged actor "genesis.actor" in the user registry, establishing the closed system's initial monetary supply. This process will establish the very first immutable reference in the `CHAIN` store. This orchestration will *leverage existing capabilities* for actor registration, wallet creation, and minting. The Genesis Block content will reside in `BLOCKS[height=0]`.

**Evidence:**
*   `2_domain_model_blockchain_chain_v0.md` defines `Genesis Block` as `BLOCKS[height=0]` and its *reference* as the starting point.
*   The `blocks.json` data examined in Stage 2 did not contain an explicit genesis block, reinforcing that its creation is not part of the regular `WF_PROPOSE_BLOCK_V0` flow.
*   The CR's "Desired Outcome" explicitly mentions "starting with bootstrapped genesis block," indicating a specific initial state.
*   User clarification: The Genesis Block funds the chain with 1,000,000 BachiCoin in a "MINT" wallet owned by "genesis.actor".
*   Existing capabilities identified: `CC_PERSIST_VERIFIED_ACTOR_V0` (identity), `WF_CREATE_WALLET_V0` (wallet), `WF_MINT_V0` (transaction).

**Resolution:** A new orchestration workflow is needed for `Genesis Block` creation and its initial commitment to the `CHAIN` store. This workflow will coordinate existing capabilities for actor registration (`CC_PERSIST_VERIFIED_ACTOR_V0`), wallet creation (`WF_CREATE_WALLET_V0`), and minting (`WF_MINT_V0`), along with new capabilities for Genesis Block formation (`CC_FORM_GENESIS_BLOCK_V0`) and chain state update (`CC_UPDATE_CHAIN_STATE_V0`). This refines Gap 2 from Stage 2.

**Answer:** The `Genesis Block` (`BLOCKS[height=0]`) will be created and committed via a dedicated orchestration workflow, distinct from the regular `Block Commitment` process. This workflow will establish the initial entry in the `CHAIN` store and will include the funding of 1,000,000 BachiCoin to a "MINT" wallet owned by "genesis.actor", utilizing existing workflows for actor and wallet management.

### Q3 — What are the specific integrity checks required for `Block Commitment` (e.g., previous hash verification, proof-of-work/stake validation) *before its reference is added to the chain*?

> **⚠ REFINED in Iteration 2 (Q9).** Proposed blocks carry no hashes; linkage is constructed (not verified) at commitment. Eligibility = PROPOSED status + sequential round. Iteration 2 governs.

**Finding:** The primary integrity checks for `Block Commitment` will focus on cryptographic linkage and sequential consistency. This includes verifying that the `previous_block_hash` of the proposed block matches the `block_hash` of the current chain head, and that the `round_id` is sequential. Other validations (e.g., transaction validity, proposer stake) are assumed to have been handled during the `PROPOSE_BLOCK` phase, as per the CR's scope limitation.

**Evidence:**
*   `2_domain_model_blockchain_chain_v0.md` (Process 3 - Block Commitment): "The block's integrity (e.g., cryptographic linkage to the previous block) is verified."
*   CR's "Out of Scope" section: "There are two more blockchain process steps "Attest", "Finaize" that we will bypass for simplicity and assume all propose blocks are good to be written to chain as finalized blocks." This implies that complex validation of block *contents* (like full transaction re-validation) is deferred.
*   General blockchain principles: Cryptographic chaining is fundamental for chain integrity.

**Resolution:** A new Capability Contract, `CC_VERIFY_CHAIN_COMMIT_ELIGIBILITY_V0`, will be required to perform these integrity checks. This addresses part of Gap 3 from Stage 2.

**Answer:** Specific integrity checks for `Block Commitment` will include:
1.  Verification that the `previous_block_hash` of the proposed block matches the `block_hash` of the current head of the `CHAIN`.
2.  Verification that the `round_id` of the proposed block is sequentially correct (current chain height + 1).
These checks will be performed by `CC_VERIFY_CHAIN_COMMIT_ELIGIBILITY_V0` before adding the block reference to the `CHAIN`.

### Q4 — How will the `Chain` state (head block reference, height) be updated and stored atomically with `Block Commitment`?

**Finding:** The `Chain` state, comprising the `current_head_block_id`, `current_head_block_hash`, and `current_block_height`, must be updated atomically with the commitment of each new block reference. This implies a single, mutable record for the overall `Chain` state that is updated as part of the `Block Commitment` process.

**Evidence:**
*   `2_domain_model_blockchain_chain_v0.md` (Chain entity attributes): explicitly lists `current_head_block_id`, `current_head_block_hash`, `current_block_height`.
*   `2_domain_model_blockchain_chain_v0.md` (Process 3 - Block Commitment): "The `Chain` state is updated to reflect the new head block reference."
*   The need for atomicity is a fundamental requirement for maintaining the integrity and consistency of the blockchain's state. If the chain itself is an append-only log, a separate mutable record is needed to track its current head.
*   `STRUCTURE_BLOCKCHAIN_STORAGE_V0` defines `CS_MUTABLE_JSON_V0` for mutable state storage (e.g., `ACTOR`, `WALLET`, `VALIDATOR`). This pattern can be reused for the `Chain` state.

**Resolution:** A new mutable store will be required to hold the `Chain`'s current state (head block reference, height). This store will be updated atomically as part of the `Block Commitment` process by `CC_UPDATE_CHAIN_STATE_V0`. This addresses Gap 4 from Stage 2.

**Answer:** The `Chain` state (current head block reference and height) will be stored in a new mutable store (`CS_MUTABLE_JSON_V0`) and updated atomically as part of the `Block Commitment` process.

### Q5 — Given that `WF_PROPOSE_BLOCK_V0` produces `PROPOSED` blocks (full content), what is the trigger or mechanism to initiate the `Block Commitment` process (adding its reference to the chain) in the new `chain` subdomain?

> **⚠ OVERTURNED in Iteration 2 (Q7).** The event-driven answer below was wrong: the runtime has no event subscription. Retained as the historical record; Iteration 2 governs.

**Finding:** The `Block Commitment` process in the `chain` subdomain needs to be triggered after a block has been successfully proposed and its full content written to the `BLOCKS` store by `WF_PROPOSE_BLOCK_V0`. This suggests that `WF_PROPOSE_BLOCK_V0` should either directly invoke a new `Block Commitment` CC/WF, or emit an event that a new `chain` subdomain workflow can consume. Given the separation of concerns and the new subdomain, an event-driven approach is more aligned with the PGS architecture.

**Evidence:**
*   `WF_PROPOSE_BLOCK_V0` currently ends with `CC_RECORD_CONSENSUS_ROUND_V0` on success, after `CC_DRAIN_MEMPOOL_V0`. There is no explicit step to commit the block to a canonical chain.
*   The conceptual model emphasizes "separation of concerns by stage" and "governance externalisation" where governance acts are external to the system. An event-driven model allows the `consensus_pos` subdomain (where `WF_PROPOSE_BLOCK_V0` resides) to remain focused on proposal, while the `chain` subdomain handles commitment.
*   `STRUCTURE_BLOCKCHAIN_STORAGE_V0` defines `BLOCK_EVENTS` as an append-only journal, which is a suitable mechanism for emitting events.

**Resolution:** `WF_PROPOSE_BLOCK_V0` will need to be extended to emit a new event (`EV_BLOCK_PROPOSED_FOR_COMMITMENT_V0`) after a block is successfully formed and recorded. A new workflow in the `chain` subdomain (`WF_COMMIT_BLOCK_V0`) will then consume this event to initiate the `Block Commitment` process. This addresses part of Gap 3 from Stage 2.

**Answer:** The `Block Commitment` process will be initiated by a new event, `EV_BLOCK_PROPOSED_FOR_COMMITMENT_V0`, emitted by `WF_PROPOSE_BLOCK_V0` (owned by `blockchain::consensus_pos`) after a block is successfully proposed. A new workflow in the `chain` subdomain (`WF_COMMIT_BLOCK_V0`) will subscribe to and consume this event.

### Q6 — The `BLOCKS` store will continue to hold the full content of `PROPOSED` blocks. A new `CHAIN` store will be created to hold immutable *references* to committed blocks. What is the precise relationship between these two stores?

**Finding:** The `BLOCKS` store and the new `CHAIN` store have a clear producer-consumer relationship. `BLOCKS` acts as a temporary staging area for the full content of `PROPOSED` blocks, while `CHAIN` is the immutable, canonical record of *references* to these blocks once they are committed. The `CHAIN` store will reference blocks by their `block_id` and `block_hash`, which can then be used to retrieve the full block content from the `BLOCKS` store when needed.

**Evidence:**
*   User clarification: "The chain will only store block address not the contents of a block. The content of a block remains in its current persistent location so chain simply links the block as an immutable record."
*   `CC_FORM_BLOCK_V0` writes the full block content to the `BLOCKS` store.
*   The `CHAIN` store is defined as an append-only log of block references.
*   The `STRUCTURE_BLOCKCHAIN_STORAGE_V0` defines `BLOCKS` as a mutable store and `CHAIN` is being defined as an immutable, append-only store.

**Resolution:** The relationship is one of separation of concerns and data lifecycle. `BLOCKS` stores the mutable, full content of `PROPOSED` blocks. `CHAIN` stores immutable references to `COMMITTED` blocks. The `CHAIN` store will rely on the `BLOCKS` store for retrieving the full content of committed blocks via their `block_id`. This clarifies the storage ownership and immutability requirements, addressing Gap 5 from Stage 2.

**Answer:** The `BLOCKS` store will continue to hold the full, mutable content of `PROPOSED` blocks. The new `CHAIN` store will hold immutable references (`block_id`, `block_hash`, `round_id`, `previous_block_hash`) to committed blocks. The `CHAIN` store will act as the canonical index, and the `BLOCKS` store will serve as the content repository for committed blocks.

---

## Iteration 2 — PPS Verification Pass (Quality Check)

*Each Iteration 1 answer was re-verified against the compiled snapshot. Four findings overturn or refine Iteration 1.*

### Q7 — Does the runtime support event-driven triggering of `Block Commitment` (Iteration 1, Q5)?

**Finding:** No. The Iteration 1 answer to Q5 is overturned. EV_ artifacts record facts (control plane + observability); the runtime has no event subscription or consumption mechanism. Workflow chaining is performed by gateway capabilities.

*Evidence: `blockchain::WF_PROCESS_SLOT_V0` invokes `WF_PROPOSE_BLOCK_V0` via `CC_INVOKE_BLOCK_PROPOSAL_V0`, a CC bound to `capability_side_effects::CS_WORKFLOW_GATEWAY_V0`. The same pattern is used throughout the orchestration subdomain (`CS_WORKFLOW_LOOP_V0`, `CS_CONCURRENT_WORKFLOWS_V0`). No artifact family or runtime concern implements event subscription.*

**Resolution:** Block commitment is chained after block proposal by extending `WF_PROCESS_SLOT_V0` (orchestration) with a new gateway capability that invokes the chain subdomain's commitment workflow. The proposed `EV_BLOCK_PROPOSED_FOR_COMMITMENT_V0` and its emitting CC are dropped; `WF_PROPOSE_BLOCK_V0` is not touched.

**Answer:** Commitment is invoked by the orchestration slot workflow via a gateway CC (owned by orchestration — a dependency gap triggered by this CR), immediately after successful block proposal and before slot clock advancement.

### Q8 — Does a commitment lifecycle event already exist?

**Finding:** Yes. `blockchain::EV_BLOCK_COMMITTED_V0` already exists in the PPS, with "Emitted By: (consensus finalization CR — next CR)" — reserved for this CR. Schema: `block_hash`, `height`, `is_canonical`, `timestamp`.

*Evidence: `protocol_snapshot/artifacts/events/blockchain__EV_BLOCK_COMMITTED_V0.json`. `EV_BLOCK_PROPOSED_V0` (canonical, emitted by `CC_FORM_BLOCK_V0`), `EV_BLOCK_ATTESTED_V0`, and `EV_BLOCK_FINALIZED_V0` also exist.*

**Resolution:** REUSE `EV_BLOCK_COMMITTED_V0` for commitment signaling; update its Emitted By table during authoring. No new event artifact is authored by this CR.

**Answer:** The commitment event is the existing `EV_BLOCK_COMMITTED_V0`, recorded to the chain subdomain's event journal at commitment.

### Q9 — Do `PROPOSED` blocks carry `block_hash` and `previous_block_hash` (assumed by Iteration 1, Q3)?

**Finding:** No. `CC_FORM_BLOCK_V0` assembles `block_id`, `round_id`, `slot`, `epoch`, `proposer_id`, `tx_ids`, `timestamp`, `status: PROPOSED`, `is_canonical: false` — no hashing occurs at proposal time.

*Evidence: pipeline of `blockchain::CC_FORM_BLOCK_V0` (generate_block_id → assemble_block_record → write_block); `CT_PURE_KECCAK256_HASH_V0` exists in the transform vocabulary but is not used at proposal.*

**Resolution:** Cryptographic linkage is constructed at commitment time by the chain subdomain: `block_hash` is computed from the proposed block record (reusing `CT_PURE_KECCAK256_HASH_V0`), and `previous_block_hash` is taken from the current chain head in `CHAIN_STATE`. Eligibility verification reduces to: block exists with status `PROPOSED`, and `round_id` is sequentially correct (head height + 1). The hash-comparison transform proposed in Iteration 1 is unnecessary.

**Answer:** Hashes are computed at commit, not verified against proposal-time values. One new transform is required (sequential round check); hashing reuses the existing keccak256 transform.

### Q10 — Who may write the `BLOCKS` store (genesis block content)?

**Finding:** The `BLOCKS` store is owned by `blockchain::block` (`pgs_blockchain.registry.block.*`). Cross-subdomain writes are forbidden — a chain-owned capability may not write genesis content into `BLOCKS`.

*Evidence: `CC_FORM_BLOCK_V0` module path `pgs_blockchain.registry.block.capability_contracts`; `STRUCTURE_BLOCKCHAIN_STORAGE_V0` path `blockchain/block/blocks/blocks.json`; governance rule "cross-subdomain writes are forbidden" (GI template / orchestration GI precedent).*

**Resolution:** Genesis block formation (write to `BLOCKS`) and canonical-status marking (update of a committed block's `status`/`is_canonical` fields) are dependency-gap capabilities owned by `blockchain::block`, triggered by this CR. The chain subdomain calls them cross-subdomain (permitted) but never writes `BLOCKS` itself.

**Answer:** Two block-owned dependency-gap capabilities: genesis block formation, and mark-block-canonical. All chain-owned writes are confined to chain-owned stores.

---

## Saturation Assessment

**Three-part saturation criterion:**

| Criterion | Status | Evidence |
|-----------|--------|----------|
| No unresolved CRITICAL gaps in the gap register | SATISFIED | All CRITICAL gaps (1–5) from Stage 2 resolved; Iteration 2 corrections incorporated. |
| No open analyst questions | SATISFIED | Q1–Q6 resolved in Iteration 1; Q7–Q10 (verification findings) resolved in Iteration 2. |
| No dependency expansion in the last review pass | SATISFIED | Iteration 2 redistributed ownership (block, orchestration dependency gaps) but surfaced no new unknowns. |

**Saturation achieved in 2 iterations.**

---

## Consolidated Findings

### What Already Exists (fully reusable)

| Artifact | Status | Reuse |
|----------|--------|-------|
| `WF_RUN_CONSENSUS_LOOP_V0` | EXISTS | REUSE — Orchestrates slot processing, which now feeds chain commitment. |
| `WF_PROCESS_SLOT_V0` | EXISTS | EXTEND — Gains a gateway invocation of block commitment after block proposal (orchestration-owned change). |
| `WF_PROPOSE_BLOCK_V0` | EXISTS | REUSE — Unchanged. Produces `PROPOSED` blocks. |
| `CC_FORM_BLOCK_V0` | EXISTS | REUSE — Forms the full block content and writes to `BLOCKS` store. |
| `EV_BLOCK_COMMITTED_V0` | EXISTS | REUSE — Commitment lifecycle event reserved for this CR; Emitted By table updated. |
| `CS_WORKFLOW_GATEWAY_V0` | EXISTS | REUSE — Substrate for all gateway (sub-workflow invocation) CCs. |
| `CS_APPENDONLY_JSONL_V0` | EXISTS | REUSE — Substrate for the immutable `CHAIN` store and chain event journal. |
| `CS_MUTABLE_JSON_V0` | EXISTS | REUSE — Substrate for the mutable `CHAIN_STATE` store. |
| `CT_PURE_KECCAK256_HASH_V0` | EXISTS | REUSE — Computes block hashes at commitment. |
| `CT_PURE_GENERATE_ID_V0`, `CT_PURE_ASSEMBLE_RECORD_V0` | EXIST | REUSE — Genesis block id generation and record assembly. |
| `CC_PERSIST_VERIFIED_ACTOR_V0` | EXISTS | REUSE — Registers `genesis.actor` (cross-subdomain CC call to identity). |
| `WF_CREATE_WALLET_V0` | EXISTS | REUSE — Invoked via gateway CC to create the MINT wallet. |
| `WF_MINT_V0` | EXISTS | REUSE — Invoked via gateway CC for initial supply minting. |
| `WF_REGISTER_VALIDATOR_V0` | EXISTS | REUSE — Invoked via gateway CC to register the genesis validator. |

### What Must Be Authored (new capabilities)

*Business names only — binding FQDN codes are assigned in Stage 6b.*

| Capability (business name) | Owner | Why New (existing candidates checked) |
|----------------------------|-------|----------------------------------------|
| Chain reference store (append-only) | chain | No existing immutable store of committed block references (checked STRUCTURE_BLOCKCHAIN_STORAGE_V0). |
| Chain state store (mutable, single record) | chain | No existing store tracks chain head and height. |
| Chain event journal (append-only) | chain | Chain lifecycle events need a chain-owned journal; BLOCK_EVENTS is block-owned. |
| Chain initialization workflow + admission intent + runtime binding | chain | One-time genesis bootstrap; no existing orchestration covers it. |
| Block commitment workflow + admission intent + runtime binding | chain | No existing capability commits block references to a chain. |
| Chain-not-initialized check | chain | Enforces single-genesis invariant. |
| Gateway invocations: wallet creation, genesis mint, validator registration | chain | Sub-workflow invocation requires per-target gateway CCs (CS_WORKFLOW_GATEWAY_V0 pattern); none exist for these targets. |
| Read chain state / update chain state | chain | New store accessors. |
| Commit eligibility verification | chain | Sequential round check + proposed-status check; no existing CC performs it. |
| Append block reference / append genesis block reference | chain | Writers for the new CHAIN store. |
| Sequential round-id comparison transform | chain | Transform vocabulary has no sequence-check atom (checked CT inventory; closest is CT_PURE_VALIDATE_PARAMETER_RULES_V0 — wrong shape). |
| Genesis block formation | block (dependency gap) | Writes `BLOCKS[height=0]`; must be block-owned. CC_FORM_BLOCK_V0 cannot form a genesis block (requires proposer/tx context). |
| Mark block canonical | block (dependency gap) | Updates committed block's `status`/`is_canonical` in `BLOCKS`; must be block-owned. |
| Block commitment invocation gateway | orchestration (dependency gap) | Extends the slot workflow to chain commitment after proposal; orchestration owns slot coordination. |

### Subdomain Placement Decision

**NEW subdomain — `blockchain::chain`**

**Reasoning:** The `chain` represents a distinct governance concern focused on the *ordering*, *immutability*, and *canonical status* of block *references*, as well as the overall state of the blockchain (genesis, head, height). This is separate from the `block` subdomain's focus on the *content* and *proposal* of individual blocks. The immutability requirement for the `CHAIN` store also necessitates a different storage paradigm. Establishing a new subdomain ensures clear ownership boundaries and governance policies for these new capabilities.

---

## Inputs to Stage 4 — Business Model

1.  **New Stores:** Three chain-owned stores — append-only `CHAIN` (immutable block references), mutable `CHAIN_STATE` (single head/height record), and append-only `CHAIN_EVENTS` (chain lifecycle journal).
2.  **Genesis Bootstrap Process:** A one-time chain initialization workflow: single-genesis check → register `genesis.actor` (reuse identity CC) → create MINT wallet (gateway to `WF_CREATE_WALLET_V0`) → mint 1,000,000 BachiCoin (gateway to `WF_MINT_V0`) → register genesis validator (gateway to `WF_REGISTER_VALIDATOR_V0`) → form genesis block content in `BLOCKS[height=0]` (block-owned dependency-gap capability) → append genesis reference to `CHAIN` → initialize `CHAIN_STATE`.
3.  **Block Commitment Process:** A commitment workflow: read chain state → read proposed block from `BLOCKS` (cross-subdomain read, permitted) → verify eligibility (status `PROPOSED`; `round_id` = head height + 1) → mark block canonical in `BLOCKS` (block-owned dependency-gap capability) → compute `block_hash` (reuse keccak256 transform), link `previous_block_hash` to current head, append reference to `CHAIN`, record `EV_BLOCK_COMMITTED_V0` → update `CHAIN_STATE`.
4.  **Integration (corrected in Iteration 2):** No event-driven trigger. `WF_PROCESS_SLOT_V0` (orchestration) is extended with an orchestration-owned gateway CC that invokes the commitment workflow after successful block proposal. `WF_PROPOSE_BLOCK_V0` is unchanged.
5.  **Subdomain:** A new `blockchain::chain` subdomain houses the new capabilities and stores; storage is declared in a dedicated chain STRUCTURE artifact (orchestration precedent).
6.  **Genesis Block Content:** Stored in `BLOCKS[height=0]`, written by the block-owned genesis formation capability.
7.  **Genesis Workflow Execution:** The initialization workflow is one-time bootstrap; the single-genesis check enforces exactly-once execution.
8.  **Single Canonical Chain Model:** V0 supports a single canonical chain; fork selection, reorganization, attestation, and finalization are out of scope.
9.  **Event Reuse:** Commitment signaling reuses the existing `EV_BLOCK_COMMITTED_V0`; no new event artifact is authored.
10. **Ownership Split:** Chain capabilities write only chain stores. `BLOCKS` writes are block-owned dependency-gap capabilities; the slot-workflow extension is orchestration-owned.

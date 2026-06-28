# Stage 2 — Domain Model Verification: blockchain / chain
**Stage:** 2 — Domain Model Verification  
**CR:** change_request_chain_v0.md  
**Status:** DRAFT  
**Feeds:** Stage 3 — Analysis Loop  

> **S2 verifies the semantic model inherited from S1 — it does not discover the domain from
> scratch.** Stage 1 already established the *meaning* (vocabulary, lifecycle states, events,
> invariants, authority). S2's job is bounded: confirm that model against the compiled snapshot,
> establish what already exists for each Stage-1 **System Belief**, and capture the gaps. It
> **discovers facts**; it does not **decide** (extend-vs-new is Stage 3) and it does not author
> solution artifacts.

---

## Document Contract

**This artifact is a structured register document — not a narrative.**

VALID OUTPUT:
- Populated register tables (every required register below)
- Existing artifacts cited by exact FQDN — only in the PPS Baseline register
- Business-language entity / process / observation / gap descriptions

INVALID OUTPUT:
- Narrative summaries, reasoning essays, executive summaries
- Free-form prose replacing required registers

A required register with no rows MUST be rendered as a single row:

| NONE IDENTIFIED |

A prose-only or empty *required* register is a structural defect — the renderer rejects the
document mechanically before any human reviews it.

---

### A. Semantic Inheritance — start from Stage 1, do not re-derive

The semantic model is **given** by Stage 1; you inherit it, you do not rediscover it:

| Inherited from Stage 1 | How S2 uses it |
|------------------------|----------------|
| **Business Vocabulary** (the objects) | Seed the Business Entities register — confirm and map each object to evidence; do not invent a different object set. |
| **Lifecycle States** | The states each entity moves through — confirm the snapshot supports them; a missing state is a gap. |
| **Business Events** | The moments the domain must recognize — find what (if anything) already emits them. |
| **Business Invariants** | Facts that must hold — note any existing artifact that already enforces (or violates) one. |
| **System Beliefs** (+ Verification Goals) | The **bounded discovery targets** — see §B. |
| **Known Facts · Governance Scope** | Authoritative business truths and the subdomain neighborhood. |

S2 does NOT ask "what is a Chain?" — Stage 1 answered that. S2 asks "given these semantics, what
evidence exists in the snapshot, and what is missing?"

### B. The Spine — Belief Verification drives this stage

**Belief Verification (§3) is the spine of S2 — fill it FIRST, before any other register.** One
row per Stage-1 **System Belief**: ground its Verification Goal and record the result —
`VERIFIED` · `NOT_FOUND` · `INSUFFICIENT_EVIDENCE`. Verification is scoped to the Stage-1 **System
Beliefs** and **Requested Outcomes** — not the domain at large.

**Every other register is a PROJECTION of the verified beliefs.** An entity, process, gap,
observation, concern, or baseline artifact may appear in this stage ONLY because verifying a
belief (or serving a Requested Outcome) surfaced it. A row that traces to no belief and no
requested outcome does not belong here — its `Source Finding` must name the belief or outcome it
serves. The **PPS Baseline** contains ONLY artifacts that verify a belief or directly serve a
requested outcome; an artifact tied to no belief and no outcome — **STOP, do not list it.**

**The belief ledger is the STOP condition: S2 is complete when every System Belief has a result.**
It does NOT continue merely because additional related artifacts exist — a successful grounding is
not a new search frontier. **Absence is a final answer:** if a search returns nothing (e.g.
`GENESIS → 0 results`), record the belief as `NOT_FOUND` and move on. Never re-search variants of a
term that already returned nothing.

### C. Open Questions — a blocker list, not a scratchpad

A row belongs in **Open Questions** ONLY if it BOTH (a) blocks a Stage-3 decision AND (b) cannot
be answered from evidence. It is NOT a list of artifacts you noticed, and NOT an
end-of-budget dump. `open_questions = NONE IDENTIFIED` is a **healthy, successful** outcome.

---

### Business-Language Rule

These registers MUST NOT contain protocol artifact names or FQDNs (express discovery in
**business language**; naming solution artifacts here is premature design — FQDNs are
introduced at Stage 5+):

- Business Entities · Entity Attributes · Business Processes · Process Steps · Gaps ·
  Architectural Observations · Open Questions · Discovery Concerns

VALID: "the canonical chain that commits proposed blocks"  
INVALID: `CC_COMMIT_BLOCK_TO_CHAIN_V0`, `WF_GENESIS_BOOTSTRAP_V0`

**WHERE FQDNs GO.** When an observation, gap, or concern is grounded in an existing artifact, the
FQDN goes ONLY in that row's **Evidence** and/or **Source Finding** column — NEVER in the
content/description cell (Observation, Gap, Impact, Concern, Question, Why It Matters). Write the
*business meaning* in the content cell and let the FQDN in the evidence column carry the proof.
INVALID: `Observation = "a consensus loop workflow exists (WF_RUN_CONSENSUS_LOOP_V0)"`.
VALID: `Observation = "a consensus loop already proposes blocks and drives slot processing"` ·
`Evidence = WF_RUN_CONSENSUS_LOOP_V0`. The renderer rejects an FQDN found in a content cell.

**EXCEPTION — Belief Verification & PPS Baseline.** Those registers cite existing artifacts by
exact FQDN in their `Evidence` / `FQDN` columns — that FQDN is the evidence.

---

### Discovery Classification (DISCOVERY_CLASSIFICATION_REQUIRED)

Every discovered item carries an `Evidence Status`, so a hypothesis is never silently promoted
to a fact:

- **OBSERVED** — supported directly by grounding evidence (confirmed via a tool call).
- **INFERRED** — derived from observed evidence but NOT directly verified (a reasoned suspicion).
- **OPEN** — requires future investigation; not yet established.

**The PPS Baseline is OBSERVED-only** — every row is a grounded, verified existing artifact. A
capability you *suspect* should exist but could not ground is **INFERRED**, and it belongs in
the Gap Register (as an INFERRED gap), NEVER in the Baseline. Do NOT extrapolate an artifact
from a pattern — seeing `APPEND_TX_EVENT` + `APPEND_VALIDATOR_EVENT` does NOT mean an
`APPEND_BLOCK_EVENT` exists. If you did not ground it, it is INFERRED, not OBSERVED.

---

### Release Boundary (out_of_scope is a hard fence)

`out_of_scope` (S1 §12) is the human's explicit release boundary. A capability, process, or gap
named there is **deferred to a future CR and is NOT a candidate for modeling here.** Do not list a
deferred item as a Business Process, an in-scope Capability, or a CRITICAL Gap. You MAY note that it
is deferred (in business language, MINOR severity) — but never model it as in-scope work. The oracle
rejects a modeled-capability row that names a deferred item. Likewise, honor `business_invariants`,
`constraints`, and `authority_boundaries` — a value the human governed in S1 is a **SEED** fact, not
something to re-derive as an `OBSERVED` snapshot guess.

---

## 1. Business Entities

*Confirm/map the Stage-1 Business Vocabulary against the snapshot — these are the inherited
objects, not a new set. A thing the business talks about, not a data store or artifact.*

<!-- register:entities business_language -->
| Entity | Description | Store Model | Evidence Status | Source Finding |
|--------|-------------|-------------|-----------------|----------------|
| Chain | The authoritative append-only ledger of committed blocks that serves as canonical history. | append-only ledger of committed blocks; lifecycle Uninitialized -> Active | OBSERVED | STRUCTURE_BLOCKCHAIN_STORAGE_V0 |
| Block | A unit of the ledger produced by a proposer, carrying the transactions of its round. | immutable once committed (append-only canonical record); transient while proposed | OBSERVED | CC_FORM_BLOCK_V0; RB_PROPOSE_BLOCK_V0 |
| Proposed Block | A block produced in the consensus loop that is not yet committed and not authoritative. | transient pre-commit candidate (Proposed lifecycle state) | OBSERVED | EV_BLOCK_PROPOSED_V0 |
| Genesis Block | The chain's first block, containing the initial mint to the Genesis Actor; created once at bootstrap. | first committed block of the canonical ledger (Created Once) | OPEN | vocab_search:GENESIS -> 0 artifacts; required per CR Seed Sec4.#2 (to be authored) |
| Genesis Actor | The permanent actor receiving the initial minted supply and owning the MINT wallet thereafter. | actor record with permanent minting authority at genesis | OBSERVED | RB_REGISTER_ACTOR_UNVERIFIED_V0; RB_MINT_V0 |
| BachiCoin | The system's unit of value; a closed monetary supply conserved at 1,000,000 total. | balance tracked in wallet records | OBSERVED | IN_MINT_V0; RB_CREATE_WALLET_V0 |
| Proposer | The validator selected to produce a block in a given round. | validator record selected per round by eligibility | OBSERVED | CC_QUERY_ELIGIBLE_VALIDATORS_V0; CC_SELECT_PROPOSER_V0 |

### Entity Attributes

*One row per (entity, attribute) — attribute-level, so S5 (identity) and S6b (storage schema) can consume directly.*

<!-- register:entity_attributes business_language -->
| Entity | Attribute | Meaning | Evidence Status | Source Finding |
|--------|-----------|---------|-----------------|----------------|
| Chain | lifecycle_state | Current state of the chain indicating whether genesis has been created and consensus is active. | OBSERVED | Lifecycle states from CR Seed §9.Chain.Uninitialized, Chain.Active |
| Chain | canonicality | Whether blocks are authoritative immutable history or not yet committed candidates. | OBSERVED | Authority boundaries from CR Seed §11.History→Chain; CommittedBlock→Chain |
| Block | lifecycle_state | Current state of the block indicating whether it is proposed or committed. | OBSERVED | Lifecycle states from CR Seed §9.Block.Proposed, Block.Committed; Genesis.CreatedOnce |
| Block | predecessor_link | Reference to the previous block establishing chain continuity. | OBSERVED | Invariant: every committed block has exactly one predecessor except genesis from CR Seed §8.#5 |
| Genesis Block | mint_amount | Initial supply minted during bootstrap, fixed at 1,000,000 BachiCoin. | OBSERVED | CR Seed §4.#3; RB_MINT_V0 |
| Genesis Block | replayable | Whether the genesis block can be re-executed after initial creation. | OBSERVED | Invariant: Genesis executes exactly once at bootstrap from CR Seed §8.#2 |
| Wallet | balance | Current holdings in BachiCoin tracked for the wallet address. | OBSERVED | CC_CHECK_WALLET_EXISTS_V0; CC_APPEND_WALLET_EVENT_V0 |
| Wallet | nonce | Counter ensuring unique transaction ordering and replay protection. | OBSERVED | CT_PURE_INCREMENT_WALLET_NONCE_V0 |

---

## 2. Business Processes

*Every business process — a sequence of business decisions/actions, implementation-free.*

<!-- register:business_processes business_language -->
| Process | Initiator | Outcome | Evidence Status | Source Finding |
|---------|-----------|---------|-----------------|----------------|
| Block Proposal Workflow | Consensus loop orchestrator selecting proposer from eligible validators | A proposed block is produced and emitted as an event for downstream consumption. | OBSERVED | CC_INVOKE_BLOCK_PROPOSAL_V0; RB_PROPOSE_BLOCK_V0 |
| Consensus Loop Execution | Orchestration subdomain driving slot processing sequence | Blocks are proposed and committed to the canonical chain for each round. | OBSERVED | RB_RUN_CONSENSUS_LOOP_V0; WF_RUN_CONSENSUS_LOOP_V0 |
| Slot Processing Sequence | Consensus loop orchestrator advancing through epoch slots | Each slot produces a proposed block and advances the clock. | OBSERVED | CC_RUN_SLOT_SEQUENCE_V0; CC_ADVANCE_SLOT_CLOCK_V0 |
| Transaction Submission Pipeline | Actor submitting transactions to mempool for inclusion in blocks | Transactions are persisted to mempool and eventually claimed into a block. | OBSERVED | CC_PERSIST_MEMPOOL_TX_V0; CC_QUERY_PENDING_TRANSACTIONS_V0 |
| Validator Registration Process | Actor registering as validator with stake information | New validator record created and made eligible for proposer selection. | OBSERVED | RB_REGISTER_VALIDATOR_V0; WF_REGISTER_VALIDATOR_V0 |
| Wallet Creation Process | Actor or system creating new wallet address with keypair derivation | New wallet record created in storage for balance tracking. | OBSERVED | RB_CREATE_WALLET_V0; WF_CREATE_WALLET_V0 |
| Block Commitment | Consensus loop, after a block is proposed in a round | The proposed block is appended to the canonical chain and becomes immutable and authoritative. | OPEN | No commit capability in snapshot (Belief 1 VERIFIED); required per CR Seed Sec4.#1,#6 |
| Genesis Bootstrap | System initialization, once, before the consensus loop runs | The genesis block is created and the initial 1,000,000 BachiCoin supply is minted to the Genesis Actor. | OPEN | vocab_search:GENESIS,BOOTSTRAP -> 0; required per CR Seed Sec4.#2 |

### Process Steps

*One row per step, in order — so S6b workflow authoring can consume the sequence directly.*

<!-- register:process_steps business_language -->
| Process | Step # | Action | Record Produced | Evidence Status | Source Finding |
|---------|--------|--------|-----------------|-----------------|----------------|
| Block Proposal Workflow | 1 | Select proposer from eligible validators based on stake and status. | Proposer ID for current round | OBSERVED | CC_QUERY_ELIGIBLE_VALIDATORS_V0; CC_SELECT_PROPOSER_V0 |
| Block Proposal Workflow | 2 | Form block structure with transactions from mempool and slot context. | Proposed block payload ready for signature | OBSERVED | CC_FORM_BLOCK_V0 |
| Block Proposal Workflow | 3 | Sign proposed block with proposer keypair and emit as event. | Signed proposed-block event | OBSERVED | CC_SIGN_TRANSACTION_V0; EV_BLOCK_PROPOSED_V0 |
| Consensus Loop Execution | 1 | Initialize slot clock and prepare context for round execution. | Slot context with epoch/slot/timestamp fields | OBSERVED | CC_INITIALIZE_SLOT_CLOCK_V0; CC_PREPARE_SLOT_CONTEXT_V0 |
| Consensus Loop Execution | 2 | Execute slot sequence invoking block proposal for each round. | Proposed blocks emitted per round in loop iteration | OBSERVED | RB_RUN_CONSENSUS_LOOP_V0; CC_INVOKE_BLOCK_PROPOSAL_V0 |
| Consensus Loop Execution | 3 | Verify slot results and record consensus round outcome. | Slot-execution and consensus-round records | OBSERVED | CC_VERIFY_SLOT_RESULTS_V0 |
| Transaction Submission Pipeline | 1 | Persist transaction to mempool store with unique ID. | Mempool record for pending transaction | OBSERVED | CC_PERSIST_MEMPOOL_TX_V0 |
| Transaction Submission Pipeline | 2 | Query mempool to retrieve transactions eligible for block inclusion. | List of pending transaction records | OBSERVED | CC_QUERY_MEMPOOL_TXS_V0 |
| Validator Registration Process | 1 | Create validator record with stake and status information. | Validator registration record | OBSERVED | RB_REGISTER_VALIDATOR_V0 |
| Wallet Creation Process | 1 | Derive keypair and create wallet record in storage. | Wallet creation record | OBSERVED | RB_CREATE_WALLET_V0 |
| Block Commitment | 1 | Validate the proposed block links to the current chain head (single predecessor). | Predecessor-link validation result | OPEN | CR Seed Sec8.#5 invariant |
| Block Commitment | 2 | Append the block to the canonical chain and mark it committed and immutable. | Committed block record and block-committed event | OPEN | CR Seed Sec4.#1,#10 |
| Genesis Bootstrap | 1 | Create the genesis block as the chain's first record. | Genesis block record | OPEN | CR Seed Sec4.#2 |
| Genesis Bootstrap | 2 | Mint the initial 1,000,000 BachiCoin supply to the Genesis Actor. | Genesis mint record | OPEN | CR Seed Sec4.#3,#4 |

---

## 3. Belief Verification — THE SPINE (fill this register FIRST)

*The spine of S2: every other register projects from these rows. One row per Stage-1 System
Belief. Ground its Verification Goal and record the Result. This is the STOP condition: S2 is
complete when every belief has a result. `NOT_FOUND` is a valid, final result — absence is an
answer, not a reason to keep searching.*

<!-- register:belief_verification -->
| Belief | Result (VERIFIED, NOT_FOUND, INSUFFICIENT_EVIDENCE) | Evidence | Source Finding |
|--------|------------------------------------------------------|----------|----------------|
| The current implementation does NOT yet provide a chain that commits proposed blocks. | VERIFIED | No CC/RB commit capability found via vocab_search:COMMIT_BLOCK,APPEND_BLOCK; EV_BLOCK_COMMITTED_V0 event exists but no actual chain commitment operation implemented | CR Seed §5.#1 |
| A consensus loop already exists that proposes blocks and drives slot processing. | VERIFIED | blockchain::RB_RUN_CONSENSUS_LOOP_V0; blockchain::WF_RUN_CONSENSUS_LOOP_V0 | CR Seed §5.#2 |
| A block-proposal capability already exists. | VERIFIED | blockchain::CC_INVOKE_BLOCK_PROPOSAL_V0; blockchain::RB_PROPOSE_BLOCK_V0; blockchain::WF_PROPOSE_BLOCK_V0 | CR Seed §5.#3 |
| A validator registry already exists. | VERIFIED | blockchain::CC_QUERY_ELIGIBLE_VALIDATORS_V0 reads from VALIDATOR store via CS_MUTABLE_JSON_V0; blockchain::RB_REGISTER_VALIDATOR_V0 for registration | CR Seed §5.#4 |
| A wallet capability already exists. | VERIFIED | blockchain::CC_CHECK_WALLET_EXISTS_V0; blockchain::RB_CREATE_WALLET_V0; blockchain::WF_CREATE_WALLET_V0 | CR Seed §5.#5 |
| A transaction capability already exists. | VERIFIED | blockchain::CC_HASH_TRANSACTION_V0; blockchain::RB_SUBMIT_TRANSACTION_V0; blockchain::WF_SUBMIT_TRANSACTION_V0 | CR Seed §5.#6 |
| A mempool already exists. | VERIFIED | blockchain::CC_PERSIST_MEMPOOL_TX_V0; blockchain::CC_QUERY_MEMPOOL_TXS_V0; blockchain::RB_PROCESS_SLOT_V0 accesses MEMPOOL store | CR Seed §5.#7 |
| An orchestration subdomain already exists. | VERIFIED | blockchain::STRUCTURE_BLOCKCHAIN_ORCHESTRATION_STORAGE_V0; blockchain::RB_RUN_CONSENSUS_SLOTS_V0 drives slot processing | CR Seed §5.#8 |
| Adjacent subdomains exist: identity, wallet, transaction, mempool, consensus_pos, orchestration. | VERIFIED | fb.identity domain artifacts via vocab_search:IDENTITY; blockchain::CC_*_WALLET_* capabilities ground wallet concept within chain storage structure | CR Seed §5.#9 |

---

## 4. PPS Baseline — What Already Exists

*Read the compiled snapshot directly (grounding tools), not memory. ONLY artifacts that verify a
System Belief or directly serve a Requested Outcome — not the whole domain inventory. One row per
relevant existing capability, cited by exact FQDN. Fit ∈ EXACT | PARTIAL | MISMATCH (an
observation of how well it matches the need — NOT a reuse decision; that is Stage 3).*

<!-- register:pps_baseline_fqdns -->
| Capability | FQDN | What It Does | Fit (EXACT, PARTIAL, MISMATCH) | Cannot Do |
|-----------|------|--------------|--------------------------------|-----------|
| Consensus loop coordination workflow runtime binding | blockchain::RB_RUN_CONSENSUS_LOOP_V0 | Provides runtime bindings for executing the consensus loop slot sequence, invoking block proposals and processing rounds. | EXACT |  |
| Block proposal invocation capability contract | blockchain::CC_INVOKE_BLOCK_PROPOSAL_V0 | Invokes WF_PROPOSE_BLOCK_V0 via workflow gateway with slot context payload mapping for block formation. | EXACT |  |
| Validator eligibility query capability contract | blockchain::CC_QUERY_ELIGIBLE_VALIDATORS_V0 | Queries VALIDATOR store and filters to active validators with stake eligible for proposer selection. | EXACT |  |
| Wallet creation runtime binding | blockchain::RB_CREATE_WALLET_V0 | Provides runtime bindings for wallet creation workflow including keypair derivation and storage operations. | PARTIAL |  |
| Mint capability contract (genesis supply) | blockchain::CC_VALIDATE_MINT_POLICY_V0; blockchain::RB_MINT_V0 | Validates mint policy constraints during genesis bootstrap for initial 1,000,000 BachiCoin supply. | PARTIAL |  |
| Transaction hash capability contract | blockchain::CC_HASH_TRANSACTION_V0 | Computes cryptographic hash of transaction payload for inclusion in block and immutability verification. | EXACT |  |

---

## 5. Gap Analysis — What Is Missing

*Each gap in business language. Severity ∈ CRITICAL (blocks authoring) | OPEN QUESTION (feeds Stage 3) | MINOR (noted).*

<!-- register:gaps business_language -->
| Gap | Severity | Impact | Evidence Status | Source Finding |
|-----|----------|--------|-----------------|----------------|
| No chain commitment capability exists to make proposed blocks authoritative immutable history. | CRITICAL | Blocks remain uncommitted; canonical ledger not yet established. This CR scope addresses implementing block commit operation. | OBSERVED (absence) | Belief 1 verification: no CC/RB artifact found via vocab_search for COMMIT_BLOCK,APPEND_BLOCK terms |
| Genesis bootstrap workflow and genesis block creation not yet implemented in snapshot. | CRITICAL | Chain cannot be initialized; consensus loop has nothing to process. Genesis Actor and MINT wallet ownership not established. | OBSERVED (absence) | vocab_search:GENESIS returned 0 artifacts; genesis bootstrap required per CR Seed §4.#2 |
| No fork resolution capability exists for handling divergent chain histories. | MINOR | Forking not handled in this release as deferred out of scope. Chain commits every proposed block without reorg logic. | OBSERVED (deferred) | Out of scope per CR Seed §12.ForkResolution |
| No slashing capability exists for penalizing validators with malicious behavior. | MINOR | Validator penalties not implemented in this release. Slashing deferred to future iteration. | OBSERVED (deferred) | Out of scope per CR Seed §12.Slashing |

---

## 6. Architectural Observations

*Architectural FACTS surfaced WHILE verifying a belief — not decisions, not free discovery. Each
row's `Source Finding` names the belief it came from. Stage 3 argues extend-vs-new from these.
E.g. "a validator lifecycle already exists", "no canonical chain storage was found".*

<!-- register:architectural_observations business_language -->
| Observation | Evidence | Evidence Status | Source Finding |
|-------------|----------|-----------------|----------------|
| Chain storage uses append-only JSONL journal for immutable event records and mutable JSON stores for state. | CS_APPENDONLY_JSONL_V0; CS_MUTABLE_JSON_V0 side effects referenced in RB_PROPOSE_BLOCK_V0 | OBSERVED | RB_RUN_CONSENSUS_LOOP_V0 bindings reference STRUCTURE_BLOCKCHAIN_STORAGE_V0 |
| Consensus loop orchestrates slot processing through workflow invocation chain. | WF_RUN_CONSENSUS_LOOP_V0 invoked by RB_RUN_CONSENSUS_LOOP_V0 | OBSERVED | topology_impact:RB_RUN_CONSENSUS_LOOP_V0 shows WF_RUN_CONSENSUS_LOOP_V0 as downstream |
| Block proposal is the terminal action per slot, invoking proposer selection and block formation. | CC_INVOKE_BLOCK_PROPOSAL_V0 maps slot context to WF_PROPOSE_BLOCK_V0 payload | OBSERVED | artifact_source:CC_INVOKE_BLOCK_PROPOSAL_V0 |
| Validator eligibility filtering is centralized in a single query capability as the sole entry point. | CT_PURE_FILTER_RECORDS_V0 applied after CS_MUTABLE_JSON_V0 LIST on VALIDATOR store | OBSERVED | artifact_source:CC_QUERY_ELIGIBLE_VALIDATORS_V0 |
| Mempool transactions are claimed and drained into blocks during slot processing. | CC_CLAIM_MEMPOOL_TXS_V0; CC_DRAIN_MEMPOOL_V0 referenced in RB_PROPOSE_BLOCK_V0 bindings | OBSERVED | RB_PROPOSE_BLOCK_V0 binds MEMPOOL store access |
| Wallet creation uses registry storage for actor records and append-only journaling. | CS_REGISTRY_V0 policy path in RB_CREATE_WALLET_V0 bindings | OBSERVED | artifact_source:RB_CREATE_WALLET_V0 |

---

## 7. Discovery Concerns

*Concerns surfaced WHILE verifying a belief — each traces back to one via `Source Finding`. The
primary feed into Stage 3 (operationalizes CONCERN_TRACEABILITY_REQUIRED). Severity ∈ CRITICAL |
MAJOR | MINOR.*

<!-- register:discovery_concerns business_language -->
| Concern | Evidence | Severity | Evidence Status | Source Finding |
|---------|----------|----------|-----------------|----------------|
| No fork resolution mechanism exists; chain commits every proposed block without reorg logic. | Out of scope per CR Seed §12.ForkResolution; no artifacts found for fork handling | MINOR | OBSERVED (deferred) | Belief verification surfaced absence of fork resolution capability |
| No slashing mechanism exists to penalize validators with malicious behavior. | Out of scope per CR Seed §12.Slashing; no artifacts found for validator penalties | MINOR | OBSERVED (deferred) | Belief verification surfaced absence of slashing capability |
| No rewards mechanism exists to distribute block production and attestation incentives. | Out of scope per CR Seed §12.Rewards; no artifacts found for reward distribution | MINOR | OBSERVED (deferred) | Belief verification surfaced absence of rewards capability |
| Attestation and finalization steps deferred to future iteration. | Out of scope per CR Seed §12.Attest, Finalize; no artifacts found for PoS progression beyond commit | MINOR | OBSERVED (deferred) | Belief verification surfaced absence of attestation/finalization capabilities |

---

## 8. Open Questions for Stage 3

*A row belongs here ONLY if it blocks a Stage-3 decision AND cannot be answered from evidence (see
§C). NOT an artifact inventory. Empty (`NONE IDENTIFIED`) is a healthy outcome. Category ∈
business | governance | identity | workflow | storage | policy | unknown.*

<!-- register:open_questions business_language optional -->
| Question | Category | Why It Matters | Source Finding |
|----------|----------|----------------|----------------|
| NONE IDENTIFIED |  |  |  |

---

## gov_projection — Governed Handoff to Stage 3

*Governed, lossless, identity-preserving (Stage 0 / field manual §4.7). Every register is forwarded — Stage 3 never re-discovers what Stage 2 modelled. Emit keys match the register ids above exactly.*

| Direction | Fields |
|-----------|--------|
| **Consumes** ← Stage 1 | business_vocabulary · known_facts · system_beliefs · lifecycle_states · business_events · governance_scope · out_of_scope · constraints · business_invariants · authority_boundaries |
| **Emits** → Stage 3 | entities · entity_attributes · business_processes · process_steps · belief_verification · pps_baseline_fqdns · gaps · architectural_observations · discovery_concerns · open_questions |

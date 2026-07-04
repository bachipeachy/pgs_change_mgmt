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
| Chain | The authoritative, ordered, append-only ledger of committed blocks; the canonical record other subdomains rely on. | An append-only record holding every committed block in order, plus a pointer to the most recent committed block. | NOT_FOUND | S1 requested_outcomes #1; projection absent[COMMIT] — no ledger exists yet |
| Block | A unit of the ledger produced by a proposer; carries the transactions of its round and links to its predecessor once committed. | Recorded as an element of the chain once committed; its content is hashed as its signature. | VERIFIED | S1 business_vocabulary Block; blockchain::ENTITY_BLOCK_V0 |
| Genesis Block | The chain's first block; carries the first system transaction that mints the initial supply to the Genesis Actor. | The single first element of the chain, created once at bootstrap. | NOT_FOUND | S1 requested_outcomes #2; projection absent[GENESIS] |
| Genesis Actor | The permanent actor that receives the initial minted supply at bootstrap and owns the mint wallet thereafter. | An actor record; the owning identity of the initial supply. | PARTIAL | S1 business_vocabulary Genesis Actor; actor records exist (blockchain::ENTITY_ACTOR_V0) but no genesis actor is provisioned |

### Entity Attributes

*One row per (entity, attribute) — attribute-level, so S5 (identity) and S6b (storage schema) can consume directly.*

<!-- register:entity_attributes business_language -->
| Entity | Attribute | Meaning | Evidence Status | Source Finding |
|--------|-----------|---------|-----------------|----------------|
| Block | content signature | A hash of the block's content, computed at commit, that uniquely identifies the block. | NOT_FOUND | S1 business_vocabulary Commit |
| Block | predecessor link | A reference to the single block that precedes this one on the canonical chain (absent only for genesis). | NOT_FOUND | S1 business_invariants #5 |
| Block | contained transactions | The transactions recorded by the block in its round; they become authoritative on commit. | VERIFIED | S1 business_vocabulary Block; blockchain::ENTITY_BLOCK_V0 |
| Chain | head | The most recently committed block, against which the next block's predecessor link is checked. | NOT_FOUND | S1 business_invariants #5 |
| Genesis Block | initial mint transaction | The first system transaction crediting the initial supply to the Genesis Actor. | PARTIAL | S1 known_facts #3; minting exists (blockchain::WF_MINT_V0) but not as a genesis step |

---

## 2. Business Processes

*Every business process — a sequence of business decisions/actions, implementation-free.*

<!-- register:business_processes business_language -->
| Process | Initiator | Outcome | Evidence Status | Source Finding |
|---------|-----------|---------|-----------------|----------------|
| Commit a proposed block to the chain | The consensus loop that produced the proposed block | The block is hashed, linked to its predecessor, and recorded as canonical; the block and its transactions become authoritative and immutable. | NOT_FOUND | S1 requested_outcomes #1; projection absent[COMMIT] |
| Bootstrap the genesis chain | The one-time system bootstrap, before the consensus loop runs | A genesis block is created and the initial supply is minted to the Genesis Actor, establishing the chain and initial monetary state. | NOT_FOUND | S1 requested_outcomes #2; projection absent[GENESIS], absent[BOOTSTRAP] |
| Reconcile wallet balances after commit | The chain, after a block is committed | Wallet balances are recomputed from the committed transactions and made consistent with the canonical committed history; balances are derived, not owned as independent state. | PARTIAL | S1 known_facts #11; S1 business_events Balance Reconciled; a balance-reconciled event exists (blockchain::EV_BALANCE_RECONCILED_V0) |

### Process Steps

*One row per step, in order — so S6b workflow authoring can consume the sequence directly.*

<!-- register:process_steps business_language -->
| Process | Step # | Action | Record Produced | Evidence Status | Source Finding |
|---------|--------|--------|-----------------|-----------------|----------------|
| Commit a proposed block to the chain | 1 | Check the proposed block's predecessor link matches the current chain head. | A pass/fail predecessor-link check. | NOT_FOUND | S1 business_invariants #5 |
| Commit a proposed block to the chain | 2 | Hash the block's content to produce its canonical signature. | The block's content signature. | NOT_FOUND | S1 business_vocabulary Commit |
| Commit a proposed block to the chain | 3 | Append the signed block to the canonical record and advance the chain head. | A new committed block on the ledger and a block-committed event. | PARTIAL | S1 business_events Block Committed; event exists (blockchain::EV_BLOCK_COMMITTED_V0), no producer |
| Bootstrap the genesis chain | 1 | Create the genesis block containing the initial mint transaction. | The genesis block. | NOT_FOUND | S1 known_facts #3 |
| Bootstrap the genesis chain | 2 | Mint the fixed initial supply to the Genesis Actor and record it as the first committed block. | The initial supply credited to the Genesis Actor; the chain established at height one. | PARTIAL | S1 known_facts #4; minting exists (blockchain::WF_MINT_V0) but not as genesis |
| Reconcile wallet balances after commit | 1 | After a block commits, recompute each affected wallet balance from the committed transactions and record the reconciled balance. | Reconciled wallet balances and a balance-reconciled event. | PARTIAL | S1 known_facts #11; a balance-reconciled event exists (blockchain::EV_BALANCE_RECONCILED_V0) |

---

## 3. Belief Verification — THE SPINE (fill this register FIRST)

*The spine of S2: every other register projects from these rows. One row per Stage-1 System
Belief. Ground its Verification Goal and record the Result. This is the STOP condition: S2 is
complete when every belief has a result. `NOT_FOUND` is a valid, final result — absence is an
answer, not a reason to keep searching.*

<!-- register:belief_verification -->
| Belief | Result (VERIFIED, NOT_FOUND, INSUFFICIENT_EVIDENCE) | Evidence | Source Finding |
|--------|------------------------------------------------------|----------|----------------|
| The current implementation does not yet provide a chain that commits proposed blocks. | VERIFIED | No capability or workflow commits a proposed block; concept COMMIT resolves to 0 artifacts. A block-committed event exists but nothing emits it: blockchain::EV_BLOCK_COMMITTED_V0. | S1 system_beliefs #1; projection absent[COMMIT] |
| A consensus loop already exists that proposes blocks and drives slot processing. | VERIFIED | blockchain::WF_RUN_CONSENSUS_LOOP_V0, blockchain::WF_RUN_CONSENSUS_SLOTS_V0, blockchain::WF_PROCESS_SLOT_V0 | S1 system_beliefs #2 |
| A block-proposal capability already exists. | VERIFIED | blockchain::WF_PROPOSE_BLOCK_V0, blockchain::CC_FORM_BLOCK_V0, blockchain::CC_INVOKE_BLOCK_PROPOSAL_V0, blockchain::EV_BLOCK_PROPOSED_V0 | S1 system_beliefs #3 |
| A validator registry already exists. | VERIFIED | blockchain::WF_REGISTER_VALIDATOR_V0, blockchain::CC_WRITE_VALIDATOR_RECORD_V0, blockchain::CC_QUERY_ELIGIBLE_VALIDATORS_V0, blockchain::CC_SELECT_PROPOSER_V0 | S1 system_beliefs #4 |
| A wallet capability already exists. | VERIFIED | blockchain::WF_CREATE_WALLET_V0, blockchain::CC_CREATE_WALLET_RECORD_V0, blockchain::ENTITY_WALLET_V0 | S1 system_beliefs #5 |
| A transaction capability already exists. | VERIFIED | blockchain::WF_SUBMIT_TRANSACTION_V0, blockchain::ENTITY_TRANSACTION_V0, blockchain::CC_SIGN_TRANSACTION_V0, blockchain::CC_HASH_TRANSACTION_V0 | S1 system_beliefs #6 |
| A mempool already exists. | VERIFIED | blockchain::CC_WRITE_MEMPOOL_TX_V0, blockchain::CC_QUERY_MEMPOOL_TXS_V0, blockchain::CC_DRAIN_MEMPOOL_V0, blockchain::CC_CLAIM_MEMPOOL_TXS_V0 | S1 system_beliefs #7 |
| An orchestration subdomain already exists. | VERIFIED | blockchain::WF_RUN_CHAIN_SIMULATION_V0, blockchain::CC_RUN_SLOT_SEQUENCE_V0, blockchain::STRUCTURE_BLOCKCHAIN_ORCHESTRATION_STORAGE_V0 | S1 system_beliefs #8 |
| Adjacent subdomains exist: identity, wallet, transaction, mempool, consensus, orchestration. | VERIFIED | identity via blockchain::ENTITY_ACTOR_V0; wallet via blockchain::ENTITY_WALLET_V0; transaction via blockchain::ENTITY_TRANSACTION_V0; mempool via blockchain::CC_WRITE_MEMPOOL_TX_V0; consensus via blockchain::WF_RUN_CONSENSUS_LOOP_V0; orchestration via blockchain::WF_RUN_CHAIN_SIMULATION_V0 | S1 system_beliefs #9 |

---

## 4. PPS Baseline — What Already Exists

*Read the compiled snapshot directly (grounding tools), not memory. ONLY artifacts that verify a
System Belief or directly serve a Requested Outcome — not the whole domain inventory. One row per
relevant existing capability, cited by exact FQDN. Fit ∈ EXACT | PARTIAL | MISMATCH (an
observation of how well it matches the need — NOT a reuse decision; that is Stage 3).*

<!-- register:pps_baseline_fqdns -->
| Capability | FQDN | What It Does | Fit (EXACT, PARTIAL, MISMATCH) | Cannot Do |
|-----------|------|--------------|--------------------------------|-----------|
| Propose a block from the consensus loop | blockchain::WF_PROPOSE_BLOCK_V0 | Selects a proposer, drains the mempool, and forms a proposed block in a round. | PARTIAL | Does not commit the proposed block to a canonical ledger. |
| Block entity schema | blockchain::ENTITY_BLOCK_V0 | Defines the block record the chain commits. | EXACT | Schema only; carries no commit or predecessor-link behaviour. |
| Form a block from claimed mempool transactions | blockchain::CC_FORM_BLOCK_V0 | Assembles a proposed block from claimed transactions. | PARTIAL | Produces a proposed block; does not record it as canonical. |
| Block proposed event | blockchain::EV_BLOCK_PROPOSED_V0 | Marks that a candidate block exists. | EXACT | Observation only; not the commit trigger. |
| Block committed event | blockchain::EV_BLOCK_COMMITTED_V0 | Declares that a block became canonical. | PARTIAL | Declared but unemitted — no capability produces it today. |
| Mint supply | blockchain::WF_MINT_V0 | Mints value under a mint policy. | PARTIAL | Not wired as a one-time genesis bootstrap step before the consensus loop. |
| Consensus loop driver | blockchain::WF_RUN_CONSENSUS_LOOP_V0 | Drives slot processing and block proposal. | PARTIAL | Produces proposals; has no downstream commit-to-chain step. |
| Orchestration storage structure | blockchain::STRUCTURE_BLOCKCHAIN_ORCHESTRATION_STORAGE_V0 | Declares the orchestration subdomain's storage. | PARTIAL | Does not declare a chain/ledger store. |

---

## 5. Gap Analysis — What Is Missing

*Each gap in business language. Severity ∈ CRITICAL (blocks authoring) | OPEN QUESTION (feeds Stage 3) | MINOR (noted).*

<!-- register:gaps business_language -->
| Gap | Severity | Impact | Evidence Status | Source Finding |
|-----|----------|--------|-----------------|----------------|
| No capability commits a proposed block to a canonical chain. | HIGH | The core requested outcome — an authoritative ledger of committed blocks — cannot be met; proposed blocks have nowhere to become canonical. | NOT_FOUND | S1 requested_outcomes #1; projection absent[COMMIT] |
| No canonical chain store exists to hold committed blocks and track the chain head. | HIGH | There is no durable, append-only record for committed history. | NOT_FOUND | S1 known_facts #1 |
| No genesis bootstrap capability creates the first block and mints the initial supply before consensus runs. | HIGH | The chain cannot be initialised with its fixed initial supply and Genesis Actor. | NOT_FOUND | S1 requested_outcomes #2; projection absent[GENESIS], absent[BOOTSTRAP] |
| No predecessor-link validation guards commit, so nothing enforces one predecessor per committed block. | MEDIUM | Without it the immutability and single-predecessor invariants cannot be upheld at commit. | NOT_FOUND | S1 business_invariants #5, #6 |

---

## 6. Architectural Observations

*Architectural FACTS surfaced WHILE verifying a belief — not decisions, not free discovery. Each
row's `Source Finding` names the belief it came from. Stage 3 argues extend-vs-new from these.
E.g. "a validator lifecycle already exists", "no canonical chain storage was found".*

<!-- register:architectural_observations business_language -->
| Observation | Evidence | Evidence Status | Source Finding |
|-------------|----------|-----------------|----------------|
| The system already produces proposed blocks through a consensus loop but has no ledger to record them, so the chain plugs in directly downstream of proposal. | blockchain::WF_PROPOSE_BLOCK_V0, blockchain::CC_FORM_BLOCK_V0 | VERIFIED | S1 system_beliefs #2, #3 |
| A block-committed event is already declared but nothing emits it, indicating a commit path was anticipated in the design and left unbuilt. | blockchain::EV_BLOCK_COMMITTED_V0 | VERIFIED | S1 business_events Block Committed |
| Minting already exists and can serve the genesis supply, so bootstrap reuses minting rather than introducing a new monetary mechanism. | blockchain::WF_MINT_V0, blockchain::CC_VALIDATE_MINT_POLICY_V0 | VERIFIED | S1 known_facts #3, #5 |
| Wallet balances are not chain-owned state; they are derived from committed transactions and reconciled on-chain after commit, and a balance-reconciled event already exists to carry that moment. | blockchain::EV_BALANCE_RECONCILED_V0 | VERIFIED | S1 known_facts #11; S1 authority_boundaries Wallet Balance |

---

## 7. Discovery Concerns

*Concerns surfaced WHILE verifying a belief — each traces back to one via `Source Finding`. The
primary feed into Stage 3 (operationalizes CONCERN_TRACEABILITY_REQUIRED). Severity ∈ CRITICAL |
MAJOR | MINOR.*

<!-- register:discovery_concerns business_language -->
| Concern | Evidence | Severity | Evidence Status | Source Finding |
|---------|----------|----------|-----------------|----------------|
| The block-committed event exists with no producer, so its intended payload and emitter are unknown and must be settled when the commit path is designed. | blockchain::EV_BLOCK_COMMITTED_V0 | MEDIUM | VERIFIED | S1 business_events Block Committed |

---

## 8. Open Questions for Stage 3

*A row belongs here ONLY if it blocks a Stage-3 decision AND cannot be answered from evidence (see
§C). NOT an artifact inventory. Empty (`NONE IDENTIFIED`) is a healthy outcome. Category ∈
business | governance | identity | workflow | storage | policy | unknown.*

<!-- register:open_questions business_language optional -->
| Question | Category | Why It Matters | Source Finding |
|----------|----------|----------------|----------------|
| What fields must the block-committed event carry to be useful to downstream subdomains? | GOVERNANCE | The event already exists but is unemitted; its payload shapes how other subdomains observe committed history. | S1 business_events Block Committed |

---

## gov_projection — Governed Handoff to Stage 3

*Governed, lossless, identity-preserving (Stage 0 / field manual §4.7). Every register is forwarded — Stage 3 never re-discovers what Stage 2 modelled. Emit keys match the register ids above exactly.*

| Direction | Fields |
|-----------|--------|
| **Consumes** ← Stage 1 | business_vocabulary · known_facts · system_beliefs · lifecycle_states · business_events · governance_scope · out_of_scope · constraints · business_invariants · authority_boundaries |
| **Emits** → Stage 3 | entities · entity_attributes · business_processes · process_steps · belief_verification · pps_baseline_fqdns · gaps · architectural_observations · discovery_concerns · open_questions |

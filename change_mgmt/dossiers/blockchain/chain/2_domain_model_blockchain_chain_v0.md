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
| Chain | the authoritative, ordered, append-only ledger of committed blocks — the store this subdomain owns | append-only ledger | ABSENT | S1 §2; no ledger store in the neighbourhood |
| Committed Block | a proposed block once committed to the chain; permanent, ordered, immutable | append-only record | ABSENT | S1 §2; blockchain::EV_BLOCK_COMMITTED_V0 orphan |
| Proposed Block | a block produced by a proposer, not yet committed — produced upstream in consensus | consumed record (not owned) | EXISTING | blockchain::WF_PROPOSE_BLOCK_V0 |
| Genesis Block | the chain's first block, written once at bootstrap, carrying the initial mint | append-only record | ABSENT | S1 §2; no bootstrap sequence |
| BachiCoin | the closed-supply unit of value, minted once at genesis | reused mint policy (not owned) | EXISTING | blockchain::WF_MINT_V0 |
| Genesis Actor | the permanent actor that receives the initial supply and owns the MINT wallet | actor record | OBSERVED | S1 §2 |
| Validator | an actor eligible for proposer selection in a round | registry (adjacent) | EXISTING | blockchain::WF_REGISTER_VALIDATOR_V0 |

### Entity Attributes

*One row per (entity, attribute) — attribute-level, so S5 (identity) and S6b (storage schema) can consume directly.*

<!-- register:entity_attributes business_language -->
| Entity | Attribute | Meaning | Evidence Status | Source Finding |
|--------|-----------|---------|-----------------|----------------|
| Committed Block | height | the block's position in the chain; genesis is height zero, each commit is the next position | ABSENT | S1 §8.5 |
| Committed Block | predecessor | the block this one links to; every committed block has exactly one except genesis | ABSENT | S1 §8.5 |
| Committed Block | signature | the hash of the block content, fixed at commit | ABSENT | S1 §2 Commit |
| Chain | head | the most recently committed block; the next commit links to it | ABSENT | S1 §2 |
| BachiCoin | total_supply | fixed at 1,000,000, minted once at genesis, conserved thereafter | OBSERVED | S1 §8.3 |

---

## 2. Business Processes

*Every business process — a sequence of business decisions/actions, implementation-free.*

<!-- register:business_processes business_language -->
| Process | Initiator | Outcome | Evidence Status | Source Finding |
|---------|-----------|---------|-----------------|----------------|
| Commit a proposed block | the chain, on a proposed block from the consensus loop | the block is recorded on the canonical chain and the committed-block signal is emitted | ABSENT | S1 §3.1; no commit capability exists |
| Bootstrap genesis | the Genesis Actor, once at startup | the genesis block is written and the initial supply minted, before the consensus loop runs | ABSENT | S1 §3.2; no bootstrap sequence exists |

### Process Steps

*One row per step, in order — so S6b workflow authoring can consume the sequence directly.*

<!-- register:process_steps business_language -->
| Process | Step # | Action | Record Produced | Evidence Status | Source Finding |
|---------|--------|--------|-----------------|-----------------|----------------|
| Commit a proposed block | 1 | receive the proposed block produced by the consensus loop | the proposed block (consumed) | EXISTING | blockchain::WF_PROPOSE_BLOCK_V0 |
| Commit a proposed block | 2 | append it to the ledger at the next height, linked to the head, signed by content hash | a committed block | ABSENT | S1 §2 Commit; no ledger store |
| Commit a proposed block | 3 | emit the committed-block signal | the committed-block event | EXISTING | blockchain::EV_BLOCK_COMMITTED_V0 |
| Bootstrap genesis | 1 | write the genesis block at height zero | the genesis block | ABSENT | S1 §4.2 |
| Bootstrap genesis | 2 | mint the initial supply to the Genesis Actor once | the initial minted supply | EXISTING | blockchain::WF_MINT_V0 |

---

## 3. Belief Verification — THE SPINE (fill this register FIRST)

*The spine of S2: every other register projects from these rows. One row per Stage-1 System
Belief. Ground its Verification Goal and record the Result. This is the STOP condition: S2 is
complete when every belief has a result. `NOT_FOUND` is a valid, final result — absence is an
answer, not a reason to keep searching.*

<!-- register:belief_verification -->
| Belief | Result (VERIFIED, NOT_FOUND, INSUFFICIENT_EVIDENCE) | Evidence | Source Finding |
|--------|------------------------------------------------------|----------|----------------|
| no capability commits a proposed block to a ledger | VERIFIED | blockchain::EV_BLOCK_COMMITTED_V0 is an orphan event; no commit capability exists | S1 §5.1 |
| a consensus loop proposes blocks and drives slot processing | VERIFIED | blockchain::WF_PROCESS_SLOT_V0 | S1 §5.2 |
| a block-proposal capability produces a proposed block | VERIFIED | blockchain::WF_PROPOSE_BLOCK_V0, blockchain::CC_FORM_BLOCK_V0 | S1 §5.3 |
| a validator registry records validators for proposer selection | VERIFIED | blockchain::WF_REGISTER_VALIDATOR_V0, blockchain::CC_QUERY_ELIGIBLE_VALIDATORS_V0 | S1 §5.4 |
| a wallet capability records balances and keys | VERIFIED | blockchain::WF_CREATE_WALLET_V0 | S1 §5.5 |
| a transaction capability exists in the pipeline | VERIFIED | blockchain::WF_SUBMIT_TRANSACTION_V0 | S1 §5.6 |
| a mempool queues transactions before block formation | VERIFIED | blockchain::CC_CLAIM_MEMPOOL_TXS_V0 | S1 §5.7 |
| an orchestration subdomain drives slot processing | VERIFIED | blockchain::WF_PROCESS_SLOT_V0 | S1 §5.8 |
| adjacent subdomains identity, wallet, transaction, mempool, consensus_pos, orchestration exist | VERIFIED | blockchain::WF_CREATE_WALLET_V0, blockchain::WF_SUBMIT_TRANSACTION_V0, blockchain::WF_PROCESS_SLOT_V0 | S1 §5.9 |

---

## 4. PPS Baseline — What Already Exists

*Read the compiled snapshot directly (grounding tools), not memory. ONLY artifacts that verify a
System Belief or directly serve a Requested Outcome — not the whole domain inventory. One row per
relevant existing capability, cited by exact FQDN. Fit ∈ EXACT | PARTIAL | MISMATCH (an
observation of how well it matches the need — NOT a reuse decision; that is Stage 3).*

<!-- register:pps_baseline_fqdns -->
| Capability | FQDN | What It Does | Fit (EXACT, PARTIAL, MISMATCH) | Cannot Do |
|-----------|------|--------------|--------------------------------|-----------|
| form a proposed block | blockchain::CC_FORM_BLOCK_V0 | forms a block from mempool transactions in the consensus loop | PARTIAL | does not commit or record the block to a ledger |
| propose a block | blockchain::WF_PROPOSE_BLOCK_V0 | the upstream workflow that produces a proposed block | PARTIAL | stops at proposal; no commit |
| mint supply | blockchain::WF_MINT_V0 | mints supply under the mint policy | PARTIAL | not sequenced as a one-time genesis bootstrap |
| signal a committed block | blockchain::EV_BLOCK_COMMITTED_V0 | the committed-block event | EXACT | no producer today (orphan) |
| drain mempool transactions | blockchain::CC_CLAIM_MEMPOOL_TXS_V0 | claims queued transactions for a block | PARTIAL | not chain-specific |
| drive slot processing | blockchain::WF_PROCESS_SLOT_V0 | the consensus loop that drives rounds | PARTIAL | does not commit blocks |

---

## 5. Gap Analysis — What Is Missing

*Each gap in business language. Severity ∈ CRITICAL (blocks authoring) | OPEN QUESTION (feeds Stage 3) | MINOR (noted).*

<!-- register:gaps business_language -->
| Gap | Severity | Impact | Evidence Status | Source Finding |
|-----|----------|--------|-----------------|----------------|
| no capability commits a proposed block to a canonical ledger | CRITICAL | the core outcome of this CR cannot be met | ABSENT | S1 §5.1; blockchain::EV_BLOCK_COMMITTED_V0 orphan |
| no one-time genesis bootstrap sequence exists to write the genesis block and mint the initial supply | CRITICAL | the chain cannot be established or its supply seeded | ABSENT | S1 §3.2, §4.2 |
| no canonical ledger store owns committed history | CRITICAL | committed blocks have nowhere authoritative to live | ABSENT | S1 §2 Chain |

---

## 6. Architectural Observations

*Architectural FACTS surfaced WHILE verifying a belief — not decisions, not free discovery. Each
row's `Source Finding` names the belief it came from. Stage 3 argues extend-vs-new from these.
E.g. "a validator lifecycle already exists", "no canonical chain storage was found".*

<!-- register:architectural_observations business_language -->
| Observation | Evidence | Evidence Status | Source Finding |
|-------------|----------|-----------------|----------------|
| the committed-block event exists with no producer — the design intent for a commit capability is already latent in the snapshot | blockchain::EV_BLOCK_COMMITTED_V0 | OBSERVED | S1 §5.1 |
| block proposal and consensus are owned by consensus_pos; the chain is a distinct downstream consumer | blockchain::WF_PROPOSE_BLOCK_V0, blockchain::WF_PROCESS_SLOT_V0 | OBSERVED | S1 §11 |

---

## 7. Discovery Concerns

*Concerns surfaced WHILE verifying a belief — each traces back to one via `Source Finding`. The
primary feed into Stage 3 (operationalizes CONCERN_TRACEABILITY_REQUIRED). Severity ∈ CRITICAL |
MAJOR | MINOR.*

<!-- register:discovery_concerns business_language -->
| Concern | Evidence | Severity | Evidence Status | Source Finding |
|---------|----------|----------|-----------------|----------------|
| the mint policy must be invoked exactly once at genesis to preserve the closed-supply invariant | blockchain::WF_MINT_V0 | MEDIUM | OBSERVED | S1 §8.3 |

---

## 8. Open Questions for Stage 3

*A row belongs here ONLY if it blocks a Stage-3 decision AND cannot be answered from evidence (see
§C). NOT an artifact inventory. Empty (`NONE IDENTIFIED`) is a healthy outcome. Category ∈
business | governance | identity | workflow | storage | policy | unknown.*

<!-- register:open_questions business_language optional -->
| Question | Category | Why It Matters | Source Finding |
|----------|----------|----------------|----------------|
| should the new commit capability emit the existing committed-block event or a new one? | reuse | a duplicate event would fork the committed signal | blockchain::EV_BLOCK_COMMITTED_V0 |
| should genesis bootstrap invoke the existing mint policy or author its own? | reuse | a second minting path would break the single-supply invariant | blockchain::WF_MINT_V0 |

---

## gov_projection — Governed Handoff to Stage 3

*Governed, lossless, identity-preserving (Stage 0 / field manual §4.7). Every register is forwarded — Stage 3 never re-discovers what Stage 2 modelled. Emit keys match the register ids above exactly.*

| Direction | Fields |
|-----------|--------|
| **Consumes** ← Stage 1 | business_vocabulary · known_facts · system_beliefs · lifecycle_states · business_events · governance_scope · out_of_scope · constraints · business_invariants · authority_boundaries |
| **Emits** → Stage 3 | entities · entity_attributes · business_processes · process_steps · belief_verification · pps_baseline_fqdns · gaps · architectural_observations · discovery_concerns · open_questions |

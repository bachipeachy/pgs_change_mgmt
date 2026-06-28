# Business Intent: blockchain / chain
**Domain:** blockchain  
**Subdomain:** chain  
**Version:** V0  
**Status:** DRAFT  
**Pipeline Stage:** Stage 5 — Business Intent (WHAT)  
**Produced by:** v0.5.0 SDLC authoring pipeline  

---

## Document Contract

**This artifact is a structured register document — not a narrative.** The Business Intent captures
the irreducible WHAT — purpose, scope, invariants, actions, and provisional artifact codes. Purpose
(§1) is short prose (the one irreducible business narrative a compiler can never derive); everything
else — including Identity Semantics (§4) — is registers. The worker emits register ROWS; a
deterministic renderer owns the document. A required cell with no basis in the seed or the snapshot
is declared `UNRESOLVED` (a governed hole), never fabricated and never left blank.

VALID OUTPUT:
- The Purpose prose section (§1) filled for this subdomain
- Populated register tables (every required register below), or `UNRESOLVED` for a genuine hole
- Business-language descriptions in content columns

INVALID OUTPUT:
- Narrative essays replacing the registers
- Implementation bindings, JSONPath, op codes, module paths, or content hashes (those are Stage 6b)

A required register with no rows renders as `| NONE IDENTIFIED |`.

---

### Provisional codes

This is the first stage that assigns **provisional** artifact codes (`provisional_codes`). They are
provisional — Stage 6b assigns the binding domain-qualified FQDNs. Each carries a `_V0` suffix.
Workflow nodes are IN / CC / EXIT only; a sub-workflow call is a gateway CC, never a nested WF. EV
artifacts record facts, never trigger execution.

---

## Stage Inputs — Questions for the Human

| # | Question for the Human | How the Agent Uses the Answer (Intent) |
|---|------------------------|----------------------------------------|
| 1 | In one paragraph: what does this subdomain govern, and why does it exist? | Becomes §1 Purpose — the scope of authority everything hangs from. |
| 2 | For each business record: does history matter, can values be corrected, is deletion allowed? | Selects the Record Model in `business_objects`. |
| 3 | Which field uniquely identifies each record, where does it come from, what does a duplicate mean? | Becomes the `identity_semantics` register (§4). |
| 4 | What is always forbidden or always required, and what is the business reason? | Becomes `invariants`. |
| 5 | What verbs can be performed on these records, and who/what triggers each? | Becomes `actions` — each in-scope action yields one Intent and one Workflow. |

---

## 1. Subdomain Purpose

*One short paragraph: what this subdomain governs, what authority it establishes, what lifecycle it
manages, and the business rationale for its existence. Write for a business stakeholder. No artifact
names.*

The chain subdomain governs the canonical, append-only ledger of committed blocks — the authoritative record of the system's history. It establishes the authority to take a proposed block produced by consensus and commit it: linking it to its predecessor, fixing its content hash as its signature, and recording it as immutable and final. It also owns the one-time genesis bootstrap that creates the first block and mints the fixed initial supply to the Genesis Actor before the consensus loop runs. The chain exists so that, once a block is committed, it and its transactions can be treated as authoritative and unchangeable by every participant.

---

## 2. Scope Boundary

*What V0 commits to vs. what is explicitly deferred. A vague scope boundary is a governance defect. Status ∈ IN_SCOPE | DEFERRED.*

<!-- register:scope_boundary business_language=capability,notes -->
| Capability | Status (IN_SCOPE, DEFERRED) | Notes | Source Finding |
|------------|-----------------------------|-------|----------------|
| Commit a proposed block to the canonical chain | IN_SCOPE | the core deliverable of this CR | S4 GAP-1 |
| Bootstrap the chain from a genesis block and mint the initial supply | IN_SCOPE | one-time, before the consensus loop | S4 GAP-2 |
| Append committed blocks to the canonical chain store | IN_SCOPE | extend the existing append-only store | S4 GAP-3 |
| Attestation step of the PoS progression | DEFERRED | deferred to a future iteration | S1 out_of_scope |
| Finalization step of the PoS progression | DEFERRED | blocks committed directly this increment | S1 out_of_scope |
| Fork resolution and chain reorganization | DEFERRED | committed history is immutable; no reorg | S1 out_of_scope |
| Validator slashing and proposer rewards | DEFERRED | validator incentives out of scope | S1 out_of_scope |

---

## 3. Business Objects

*The business records this subdomain maintains and WHY each takes its form. Record Model ∈ MUTABLE_STATE (current state, correctable) | APPEND_ONLY_JOURNAL (immutable history) | IDENTITY_REGISTRY (stable key→address) | HYBRID. Business language.*

<!-- register:business_objects optional business_language=store_name,business_rationale -->
| Store Name | Record Model (MUTABLE_STATE, APPEND_ONLY_JOURNAL, IDENTITY_REGISTRY, HYBRID) | Business Rationale | Source Finding |
|------------|------------------------------------------------------------------------------|--------------------|----------------|
| canonical chain | APPEND_ONLY_JOURNAL | immutable, ordered history of committed blocks | S1 invariant immutability |
| chain head pointer | MUTABLE_STATE | tracks the most recently committed block | S4 entity Chain |

---

## 4. Identity Semantics

*Which field uniquely identifies each record, where it comes from, what a duplicate means, and any
cross-subdomain identity relationship. The compiler cannot infer identity semantics from field
names — this is irreducible business knowledge. If a cell is genuinely not derivable from the seed,
declare it `UNRESOLVED` (a governed hole a human will resolve) rather than guessing.*

<!-- register:identity_semantics business_language=identity_field,source,uniqueness_rule,cross_subdomain_relationship -->
| Store Name | Identity Field | Source | Uniqueness Rule | Cross-Subdomain Relationship | Source Finding |
|------------|----------------|--------|-----------------|------------------------------|----------------|
| Block | block hash (content hash used as the block's signature) | computed from block content at commit | one committed block per height; the hash is unique | links to its predecessor block; produced by the proposing validator | S1 vocab Commit; S1 invariant predecessor |
| Genesis Block | genesis block hash | computed at bootstrap | exactly one genesis block per chain | no predecessor; credits the MINT wallet owned by the Genesis Actor | S1 invariant one-genesis |
| Chain | chain head (height of the latest committed block) | advanced on each commit | single canonical head | consumes proposed blocks from consensus | S4 entity Chain |

---

## 5. Business Invariants

*Non-negotiable rules with a business reason. A rule without a business reason is a technical constraint and belongs elsewhere.*

<!-- register:invariants business_language=invariant,business_reason -->
| Invariant | Business Reason | Source Finding |
|-----------|-----------------|----------------|
| A committed block is immutable and never changes or disappears | the chain is the authoritative record; audit integrity | S1 invariant #4 |
| Exactly one genesis block exists and genesis executes exactly once | a single, fixed origin of the chain and supply | S1 invariant #1,#2 |
| Total supply is conserved at 1,000,000 BachiCoin | closed monetary system; no mint/burn after genesis | S1 invariant #3 |
| Every committed block has exactly one predecessor except genesis | linear, verifiable chain continuity | S1 invariant #5 |
| A block cannot be committed twice | no duplicate history | S1 invariant #6 |

---

## 6. Business Actions

*Every verb performable on this subdomain's objects, in plain business language. Each in-scope action maps to one Intent and one Workflow. Status ∈ IN_SCOPE | DEFERRED.*

<!-- register:actions business_language=object,trigger -->
| Action | Object | Trigger | Status (IN_SCOPE, DEFERRED) | Source Finding |
|--------|--------|---------|-----------------------------|----------------|
| Commit | proposed block | consensus loop, after a block is proposed | IN_SCOPE | S4 GAP-1 |
| Bootstrap | chain and genesis supply | system initialization, once | IN_SCOPE | S4 GAP-2 |
| Attest | proposed block | deferred | DEFERRED | S1 out_of_scope |
| Finalize | committed block | deferred | DEFERRED | S1 out_of_scope |

---

## 7. Provisional Artifact Codes

*Provisional AC / IN / WF / CC codes (Stage 6b assigns binding FQDNs). Each carries `_V0`. `summary` is business language. Family ∈ AC | IN | WF | CC.*

<!-- register:provisional_codes business_language=summary -->
| Provisional Code | Family (AC, IN, WF, CC) | Summary | Source Finding |
|------------------|-------------------------|---------|----------------|
| IN_COMMIT_BLOCK_V0 | IN | admit a request to commit a proposed block | S4 GAP-1 |
| WF_COMMIT_BLOCK_V0 | WF | commit a proposed block to the canonical chain | S4 GAP-1 |
| CC_COMMIT_BLOCK_CANONICAL_V0 | CC | append the validated block to the canonical chain | S4 GAP-1 |
| CC_VALIDATE_PREDECESSOR_LINK_V0 | CC | validate the block links to the current chain head | S1 invariant predecessor |
| IN_BOOTSTRAP_GENESIS_CHAIN_V0 | IN | admit a one-time genesis bootstrap request | S4 GAP-2 |
| WF_BOOTSTRAP_GENESIS_CHAIN_V0 | WF | create the genesis block and mint the initial supply | S4 GAP-2 |
| CC_CREATE_GENESIS_BLOCK_V0 | CC | create the chain's first block at bootstrap | S4 GAP-2 |

---

## 8. Cross-Subdomain References

*Capability Contracts defined in another subdomain and referenced by this subdomain's workflows. `cc_code` is the existing FQDN; do not re-document it here.*

<!-- register:cross_subdomain_refs optional business_language=role -->
| CC Code | Defined In | Role | Source Finding |
|---------|------------|------|----------------|
| blockchain::CC_INVOKE_BLOCK_PROPOSAL_V0 | blockchain (consensus) | produces the proposed block the chain commits | S2 belief #3 |
| blockchain::RB_MINT_V0 | blockchain (mint) | mints the genesis supply during bootstrap | S2 pps_baseline mint |

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 4 — Business Model | business_model_chain_v0.md | COMPLETE |
| Stage 5 — Business Intent | This document | COMPLETE |
| Stage 6 — Governance Intent | Pending | — |

---

## gov_projection — Governed Handoff to Stage 6

*The bounded inputs and emit keys mirror the engine's gov_projection schema exactly
(`contracts/gov_projection.py`): S5 consumes the S4 discovery output plus the S1 release boundary
and emits the WHAT. Emit keys match the register ids above exactly (Purpose §1 / Identity Semantics
§4 / Business Objects §3 are this stage's record, not forwarded fields).*

| Direction | Fields |
|-----------|--------|
| **Consumes** ← Stage 1 | out_of_scope |
| **Consumes** ← Stage 4 | actors · bm_entities · events · capability_graph · constraint_register |
| **Emits** → Stage 6 | scope_boundary · invariants · actions · provisional_codes · cross_subdomain_refs |

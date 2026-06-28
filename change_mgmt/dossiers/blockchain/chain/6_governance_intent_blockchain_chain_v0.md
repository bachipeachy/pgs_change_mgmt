# Governance Intent: blockchain / chain
**Domain:** blockchain  
**Subdomain:** chain  
**Version:** V0  
**Status:** DRAFT  
**Pipeline Stage:** Stage 6 — Governance Intent (WHERE)  
**Produced by:** v0.5.0 SDLC authoring pipeline  
**Purity:** WHERE only — artifact family mapping, provisional artifact codes, and store declarations excluded  

---

## Document Contract

**This artifact is a structured register document — not a narrative.** S6 declares the WHERE:
subdomain ownership, storage governance, cross-subdomain dependencies, and existing artifacts
needing action. The worker emits register ROWS; a deterministic renderer owns the document.

VALID OUTPUT:
- Populated register tables (every required register below)
- Business-language capability / dependency / storage descriptions
- Existing artifacts cited by exact FQDN in evidence / artifact columns

INVALID OUTPUT:
- Narrative summaries replacing registers
- A provisional or invented artifact code in a content column (see the discipline below)

A required register with no rows renders as `| NONE IDENTIFIED |`.

---

### Governance discipline

- **NO provisional artifact codes in this stage** (per the Purity line above). A NEW capability is
  named in **business language** (e.g. "create the genesis block at bootstrap"); ownership names the
  owning **subdomain** namespace, never an invented artifact code like `CC_CREATE_GENESIS_BLOCK_V0`.
  Existing artifacts are still cited by their real FQDN (in `evidence` / `existing_artifact` / `fqdn`
  columns). Provisional codes were assigned at Stage 5; binding FQDNs are assigned at Stage 6b.
- **Cross-subdomain writes are forbidden — no exceptions.** A store is written only by CCs of its
  owning subdomain. If this CR's process requires writing a peer's store, the writing CC is owned by
  that peer (a dependency gap declared in `cross_subdomain_deps`, Status = GAP).
- Cross-subdomain capability calls and data reads ARE permitted — declare each with explicit
  direction in `cross_subdomain_deps`.

---

## Stage Inputs — Questions for the Human

| # | Question for the Human | How the Agent Uses the Answer (Intent) |
|---|------------------------|----------------------------------------|
| 1 | Does this capability stand as its own subdomain, or extend an existing one — and why? | Sets Domain Placement (below). Subdomain existence is a governance topology declaration, never derived from the snapshot. |
| 2 | Under what authority class do these operations execute (existing ENDUSER/SYSTEM, or a new actor type)? | A new actor type expands CR scope; reuse must be stated explicitly. |
| 3 | For each capability that touches a peer subdomain: who should OWN it? | Drives `ownership` + `cross_subdomain_deps`. A capability that writes a peer's store MUST be owned by that peer. |
| 4 | Which boundary rules are non-negotiable for this subdomain? | Becomes `boundary_rules`, the invariants conformance tests will enforce. |

---

## Domain Placement (reference)

| Field | Value |
| --- | --- |
| Domain | `blockchain` |
| Primary subdomain | `chain` — [NEW — declared by this CR / EXISTING] |
| Authority class | [reuse existing ENDUSER/SYSTEM / new actor type: name] |
| Governing constitutions | `fb.constitution::CONSTITUTION_GOVERNANCE_V0`, `fb.topology::CONSTITUTION_WORKFLOW_V0`, `fb.constitution::CONSTITUTION_STRUCTURE_V0` |

*State the placement rationale in one or two sentences: if declaring a new subdomain, why it stands alone rather than nesting under an existing one.*

---

## 1. Subdomain Boundary — Ownership

*Every capability this CR needs, and who OWNS it. Disposition ∈ OWNED (this subdomain authors it) | SATISFIED (an existing artifact covers it — cite the FQDN in Evidence) | DEFERRED (future CR). `capability` is business language; `owner_subdomain` is a subdomain namespace, never an artifact code.*

<!-- register:ownership business_language=capability -->
| Capability | Owner Subdomain | Disposition (OWNED, SATISFIED, DEFERRED) | Existing Artifact | Source Finding |
|------------|-----------------|------------------------------------------|-------------------|----------------|
| Commit a proposed block to the canonical chain | chain | OWNED |  | S4 GAP-1 |
| Bootstrap the chain from genesis and mint initial supply | chain | OWNED |  | S4 GAP-2 |
| Append committed blocks to the canonical store | chain | OWNED | blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0 | S4 GAP-3 |
| Produce a proposed block | consensus | SATISFIED | blockchain::CC_INVOKE_BLOCK_PROPOSAL_V0 | S3 REUSE |
| Mint the initial supply | blockchain | SATISFIED | blockchain::RB_MINT_V0 | S3 REUSE |
| Attestation, finalization, slashing, rewards | chain | DEFERRED |  | S1 out_of_scope |

---

## 2. Storage Governance Requirements

*What persistent storage the subdomain requires, as a governance requirement — NOT store names or paths (those are Stage 6b). Business language only.*

<!-- register:storage_governance business_language=storage_need,purpose -->
| Storage Need | Purpose | Subdomain | Source Finding |
|--------------|---------|-----------|----------------|
| canonical block records | immutable, ordered history of committed blocks | chain | S1 invariant immutability |
| chain head pointer | track the latest committed block height | chain | S4 entity Chain |

---

## 3. Cross-Subdomain Dependency Declaration

*Cross-subdomain calls/reads (permitted) and dependency gaps (a peer must author a capability for this CR). `dependency` is business language; `direction` is `this_subdomain → peer`; `existing_artifact` cites an existing FQDN when reused. Status ∈ SATISFIED (reuse existing) | GAP (new, owned by the peer).*

<!-- register:cross_subdomain_deps optional business_language=dependency -->
| Dependency | Direction | Existing Artifact | Status (SATISFIED, GAP) | Source Finding |
|------------|-----------|-------------------|-------------------------|----------------|
| proposed blocks from the consensus loop | inbound | blockchain::RB_RUN_CONSENSUS_LOOP_V0 | SATISFIED | S2 belief #2 |
| mint capability for genesis supply | outbound | blockchain::RB_MINT_V0 | SATISFIED | S3 REUSE |
| wallet and actor registration for the Genesis Actor | outbound | blockchain::RB_CREATE_WALLET_V0 | SATISFIED | S3 REUSE |

---

## 4. PPS Artifacts Requiring Action

*Existing PPS artifacts that must be reviewed or replaced as part of this CR. `fqdn` is the existing artifact. Action ∈ REPLACE | REVIEW | REUSE.*

<!-- register:pps_artifacts_requiring_action optional -->
| FQDN | Current Status | Action (REPLACE, REVIEW, REUSE) | Source Finding |
|------|----------------|----------------------------------|----------------|
| blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0 | append-only block storage without commit semantics | REVIEW | S3 EXTEND storage |
| blockchain::EV_BLOCK_COMMITTED_V0 | committed-block event exists but is not emitted by any operation | REUSE | S3 REUSE event |

---

## 5. Governance Boundary Rules

*Non-negotiable boundary rules for this subdomain — each a governance invariant, not an implementation detail.*

<!-- register:boundary_rules optional -->
| Rule Name | Statement | Source Finding |
|-----------|-----------|----------------|
| NONE IDENTIFIED |  |  |

---

## 6. Governance Outcome

*Capabilities requiring protocol realization (Stage 6b assigns the artifact family + binding FQDN). Business language; organized by owning subdomain.*

<!-- register:governance_outcome optional business_language=capability -->
| Capability | Owner Subdomain | Source Finding |
|------------|-----------------|----------------|
| NONE IDENTIFIED |  |  |

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 4 — Business Model | business_model_chain_v0.md | COMPLETE |
| Stage 5 — Business Intent | business_intent_chain_v0.md | COMPLETE |
| Stage 6 — Governance Intent | This document | COMPLETE |
| Stage 6b — Design Intent | Pending | — |

---

## gov_projection — Governed Handoff to Stage 6b

*The bounded inputs and emit keys mirror the engine's gov_projection schema exactly
(`contracts/gov_projection.py`). Domain Placement, Boundary Rules (§5), and Governance Outcome (§6)
are this stage's record; the four emit registers cross to Stage 6b. Emit keys match the register ids
above exactly.*

| Direction | Fields |
|-----------|--------|
| **Consumes** ← Stage 1 | out_of_scope · governance_scope |
| **Consumes** ← Stage 4 | events · constraint_register · dependency_graph · authoring_scope |
| **Consumes** ← Stage 5 | scope_boundary · invariants · cross_subdomain_refs |
| **Emits** → Stage 6b | ownership · storage_governance · cross_subdomain_deps · pps_artifacts_requiring_action |

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
| Commit a proposed block to the canonical chain | chain | OWNED |  | S4 gap_register GAP-1 |
| Store the canonical chain ledger and track its head | chain | OWNED |  | S4 gap_register GAP-2 |
| Validate a block's predecessor link before commit | chain | OWNED |  | S4 gap_register GAP-3 |
| Compute a block's content signature | chain | OWNED |  | S4 gap_register GAP-4 |
| Bootstrap the genesis chain and initialise the supply | chain | OWNED |  | S4 gap_register GAP-5 |
| Reconcile wallet balances after commit by deriving from committed transactions and announcing the result | chain | OWNED |  | S4 gap_register GAP-6 |
| Mint the initial genesis supply | wallet | SATISFIED | blockchain::WF_MINT_V0 | S3 authoring_decisions REUSE |
| Announce that a block was committed | chain | SATISFIED | blockchain::EV_BLOCK_COMMITTED_V0 | S3 authoring_decisions REUSE |
| Announce that balances were reconciled | chain | SATISFIED | blockchain::EV_BALANCE_RECONCILED_V0 | S3 authoring_decisions REUSE |
| Record a committed block using the existing block schema | chain | SATISFIED | blockchain::ENTITY_BLOCK_V0 | S3 authoring_decisions REUSE |
| Attest proposed blocks | chain | DEFERRED |  | S1 out_of_scope attest |
| Finalize committed blocks | chain | DEFERRED |  | S1 out_of_scope finalize |

---

## 2. Storage Governance Requirements

*What persistent storage the subdomain requires, as a governance requirement — NOT store names or paths (those are Stage 6b). Business language only.*

<!-- register:storage_governance business_language=storage_need,purpose -->
| Storage Need | Purpose | Subdomain | Source Finding |
|--------------|---------|-----------|----------------|
| An append-only ledger of committed blocks with a pointer to the current head | Preserve the immutable, ordered history of committed blocks and identify the block a new commit must link to | chain | S5 business_objects; S4 gap_register GAP-2 |

---

## 3. Cross-Subdomain Dependency Declaration

*Cross-subdomain calls/reads (permitted) and dependency gaps (a peer must author a capability for this CR). `dependency` is business language; `direction` is `this_subdomain → peer`; `existing_artifact` cites an existing FQDN when reused. Status ∈ SATISFIED (reuse existing) | GAP (new, owned by the peer).*

<!-- register:cross_subdomain_deps optional business_language=dependency -->
| Dependency | Direction | Existing Artifact | Status (SATISFIED, GAP) | Source Finding |
|------------|-----------|-------------------|-------------------------|----------------|
| Read the proposed block produced by the consensus loop | chain → consensus_pos | blockchain::WF_PROPOSE_BLOCK_V0 | SATISFIED | S3 dependency_discoveries EXISTING |
| Mint the initial supply at genesis | chain → wallet | blockchain::WF_MINT_V0 | SATISFIED | S3 authoring_decisions REUSE |
| Announce reconciled balances for the wallet subdomain to apply to its own store | chain → wallet | blockchain::EV_BALANCE_RECONCILED_V0 | SATISFIED | S1 known_facts #11; the chain never writes the wallet store |

---

## 4. PPS Artifacts Requiring Action

*Existing PPS artifacts that must be reviewed or replaced as part of this CR. `fqdn` is the existing artifact. Action ∈ REPLACE | REVIEW | REUSE.*

<!-- register:pps_artifacts_requiring_action optional -->
| FQDN | Current Status | Action (REPLACE, REVIEW, REUSE) | Source Finding |
|------|----------------|----------------------------------|----------------|
| blockchain::EV_BLOCK_COMMITTED_V0 | Declared but unemitted (0 references) | REUSE | S3 verification_results; the chain becomes its emitter |
| blockchain::EV_BALANCE_RECONCILED_V0 | Declared but unreferenced | REUSE | S3 verification_results |
| blockchain::ENTITY_BLOCK_V0 | Exists, 0 consumers | REUSE | S3 impact_analysis |
| blockchain::WF_MINT_V0 | Exists; reused as the genesis mint step | REUSE | S3 authoring_decisions REUSE |

---

## 5. Governance Boundary Rules

*Non-negotiable boundary rules for this subdomain — each a governance invariant, not an implementation detail.*

<!-- register:boundary_rules optional -->
| Rule Name | Statement | Source Finding |
|-----------|-----------|----------------|
| Chain writes only its own store | The chain never writes a peer subdomain's store; balance reconciliation derives balances from committed transactions and announces them via an event, and the wallet subdomain updates its own balances. | S6 governance discipline; S1 known_facts #11 |
| Committed history is immutable | A committed block is never altered or removed once recorded. | S1 business_invariants #4 |
| Single genesis | Exactly one genesis block exists per chain; genesis runs once at bootstrap and is never replayed. | S1 business_invariants #1, #2 |
| Chain is authoritative for committed history | A proposed block is not authoritative until it is committed to the canonical chain. | S1 business_invariants #7 |
| Closed supply | Total supply is conserved at 1,000,000 BachiCoin after genesis; no minting or burning follows. | S1 business_invariants #3 |

---

## 6. Governance Outcome

*Capabilities requiring protocol realization (Stage 6b assigns the artifact family + binding FQDN). Business language; organized by owning subdomain.*

<!-- register:governance_outcome optional business_language=capability -->
| Capability | Owner Subdomain | Source Finding |
|------------|-----------------|----------------|
| Commit a proposed block to the canonical chain | chain | S4 gap_register GAP-1 |
| Store the canonical chain ledger and track its head | chain | S4 gap_register GAP-2 |
| Validate a block's predecessor link before commit | chain | S4 gap_register GAP-3 |
| Compute a block's content signature | chain | S4 gap_register GAP-4 |
| Bootstrap the genesis chain and initialise the supply | chain | S4 gap_register GAP-5 |
| Reconcile wallet balances after commit | chain | S4 gap_register GAP-6 |

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

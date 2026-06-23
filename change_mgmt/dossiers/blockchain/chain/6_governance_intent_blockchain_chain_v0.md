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
| create genesis block at bootstrap | blockchain/chain | OWNED | None | upstream handoff: authoring_scope capability create genesis block |
| commit blocks to canonical chain immutably | blockchain/chain | OWNED | None | upstream handoff: authoring_scope capability commit block; blockchain::EV_BLOCK_COMMITTED_V0 event contract |
| maintain chain state with supply conservation after genesis | blockchain/chain | OWNED | None | upstream handoff: authoring_scope capability maintain chain state; blockchain::CC_VALIDATE_MINT_POLICY_V0 for conservation |
| record consensus round outcome including skip decisions | blockchain/chain | SATISFIED | blockchain::CC_RECORD_CONSENSUS_ROUND_V0; blockchain::CC_SKIP_ROUND_V0 | upstream handoff: events Round Skipped lifecycle meaning |
| append block lifecycle events to immutable journal | blockchain/chain | SATISFIED | capability_side_effects::CS_APPENDONLY_JSONL_V0; blockchain::CC_FORM_BLOCK_V0 pipeline step append_block_event | upstream handoff: dependency_graph capability side effect reuse for event journaling |
| write committed blocks to immutable BLOCKS store | blockchain/chain | SATISFIED | capability_side_effects::CS_MUTABLE_JSON_V0; blockchain::CC_FORM_BLOCK_V0 pipeline step write_block | upstream handoff: dependency_graph capability side effect reuse for mutable store access |

---

## 2. Storage Governance Requirements

*What persistent storage the subdomain requires, as a governance requirement — NOT store names or paths (those are Stage 6b). Business language only.*

<!-- register:storage_governance business_language=storage_need,purpose -->
| Storage Need | Purpose | Subdomain | Source Finding |
|--------------|---------|-----------|----------------|
| append-only event journal for block lifecycle records | preserve historical audit trail of proposed, attested, and committed blocks with cryptographic linkage to predecessor | blockchain/chain | upstream handoff: dependency_graph capability side effect reuse; fb.topology::SURFACE_CONTRACT_STORAGE_APPENDONLY_APPEND_V0 contract |
| mutable store for committed block records with cryptographic predecessor linkage | maintain canonical chain history where each block references exactly one predecessor except genesis, ensuring linear unambiguous ordering | blockchain/chain | upstream handoff: dependency_graph capability side effect reuse; fb.topology::SURFACE_CONTRACT_STORAGE_WRITE_V0 contract |
| immutable storage structure for blockchain subdomain topology and store resolution | define registry locations, operational constraints, and canonical chain immutability after compilation per governance constitutions | blockchain/chain | upstream handoff: dependency_graph storage structure reuse; fb.blockchain::STRUCTURE_BUILD_BLOCKCHAIN_V0 topology definition |

---

## 3. Cross-Subdomain Dependency Declaration

*Cross-subdomain calls/reads (permitted) and dependency gaps (a peer must author a capability for this CR). `dependency` is business language; `direction` is `this_subdomain → peer`; `existing_artifact` cites an existing FQDN when reused. Status ∈ SATISFIED (reuse existing) | GAP (new, owned by the peer).*

<!-- register:cross_subdomain_deps optional business_language=dependency -->
| Dependency | Direction | Existing Artifact | Status (SATISFIED, GAP) | Source Finding |
|------------|-----------|-------------------|-------------------------|----------------|
| fb.blockchain configuration defining blockchain subdomain parameters and operational constraints | blockchain/chain → fb.blockchain | fb.blockchain::STRUCTURE_BUILD_BLOCKCHAIN_CONFIG_V0; fb.topology::ASSERT_CC_NO_IMPLICIT_CHAINING_V0 | SATISFIED | upstream handoff: cross_subdomain_refs configuration structure defining blockchain subdomain parameters |
| fb.blockchain topology establishing storage topology and store resolution for consensus operations | blockchain/chain → fb.topology | fb.blockchain::STRUCTURE_BUILD_BLOCKCHAIN_V0; blockchain::RB_PROPOSE_BLOCK_V0 workflow reference | SATISFIED | upstream handoff: cross_subdomain_refs structure artifact establishing blockchain subdomain storage topology |
| fb.blockchain registry location for identity subdomain cross-references and actor resolution | blockchain/chain → fb.topology | fb.blockchain::STRUCTURE_REGISTRY_LOCATION_BLOCKCHAIN_V0; blockchain::RB_REGISTER_VALIDATOR_V0 workflow reference | SATISFIED | upstream handoff: cross_subdomain_refs structure artifact defining registry location for identity subdomain |

---

## 4. PPS Artifacts Requiring Action

*Existing PPS artifacts that must be reviewed or replaced as part of this CR. `fqdn` is the existing artifact. Action ∈ REPLACE | REVIEW | REUSE.*

<!-- register:pps_artifacts_requiring_action optional -->
| FQDN | Current Status | Action (REPLACE, REVIEW, REUSE) | Source Finding |
|------|----------------|----------------------------------|----------------|
| blockchain::CC_FORM_BLOCK_V0 | canonical capability contract in PPS snapshot inventory | REUSE | upstream handoff: dependency_graph block commitment capability side effect reuse |
| blockchain::EV_BLOCK_COMMITTED_V0 | canonical event contract in PPS snapshot inventory | REUSE | upstream handoff: dependency_graph block commitment capability side effect reuse for event journaling |
| blockchain::CC_VALIDATE_MINT_POLICY_V0 | canonical policy validation contract in PPS snapshot inventory | REUSE | upstream handoff: constraint_register mint policy enforcement; blockchain::AC_SYSTEM_V0 for system-level genesis operations |

---

## 5. Governance Boundary Rules

*Non-negotiable boundary rules for this subdomain — each a governance invariant, not an implementation detail.*

<!-- register:boundary_rules optional -->
| Rule Name | Statement | Source Finding |
|-----------|-----------|----------------|
| Single Genesis Execution Rule | Exactly one genesis block exists per chain and executes exactly once at bootstrap never replayed, establishing canonical monetary base of 1 million BachiCoin to Genesis Actor | upstream handoff: invariants single-execution semantics prevent supply duplication; blockchain::AC_SYSTEM_V0 for system-level single-execution |
| Immutable Chain History Rule | Once a block commits to canonical history it cannot be altered or removed, preserving decentralized trust through unalterable record of all committed transactions | upstream handoff: invariants chain immutability; CR seed constraints #2 on immutability |
| Closed Monetary System Rule | No supply enters or leaves the system except by protocol-defined rules, preventing external manipulation of chain state and inflationary attacks after genesis completion | upstream handoff: invariants closed monetary principle; blockchain::CC_VALIDATE_MINT_POLICY_V0 for post-genesis conservation |
| Single Predecessor Linkage Rule | A committed block has exactly one predecessor except the genesis block, ensuring linear chain structure and unambiguous historical ordering without fork ambiguity in canonical history | upstream handoff: invariants single-predecessor linkage; blockchain::CC_FORM_BLOCK_V0 establishes this constraint |
| Unique Commitment Rule | A committed block cannot be committed twice to the canonical chain, preserving immutability guarantee and preventing duplicate inclusion attacks on historical records | upstream handoff: invariants uniqueness constraint; blockchain::EV_BLOCK_COMMITTED_V0 for commit event semantics |
| Cross-Subdomain Write Prohibition Rule | A store is written only by capabilities of its owning subdomain, preventing unauthorized cross-subdomain writes that could compromise integrity boundaries | upstream handoff: governance discipline cross-subdomain writes forbidden; fb.topology::ASSERT_CC_NO_IMPLICIT_CHAINING_V0 |
| Storage Conformance Rule | All storage operations must conform to topology surface contracts for append-only, read, and write semantics with immutable compilation guarantees after deployment | upstream handoff: fb.topology::ASSERT_CC_STORAGE_OP_CONFORMANCE_V0; fb.topology::INVARIANT_TOPOLOGY_IMMUTABLE_AFTER_COMPILATION_V0 |

---

## 6. Governance Outcome

*Capabilities requiring protocol realization (Stage 6b assigns the artifact family + binding FQDN). Business language; organized by owning subdomain.*

<!-- register:governance_outcome optional business_language=capability -->
| Capability | Owner Subdomain | Source Finding |
|------------|-----------------|----------------|
| create genesis block at bootstrap | blockchain/chain | upstream handoff: governance_scope chain CREATED; scope_boundary IN_SCOPE one-time bootstrap operation |
| commit blocks to canonical chain immutably | blockchain/chain | upstream handoff: events Block Committed lifecycle meaning; governance_scope ADJACENT consensus_pos, orchestration |
| maintain chain state with supply conservation after genesis | blockchain/chain | upstream handoff: invariants total supply conserved at 1 million BachiCoin; scope_boundary IN_SCOPE maintain chain state |
| record consensus round outcome including skip decisions | blockchain/chain | upstream handoff: events Round Skipped lifecycle meaning; governance_scope ADJACENT orchestration, mempool |
| append block lifecycle events to immutable journal | blockchain/chain | upstream handoff: scope_boundary IN_SCOPE append block lifecycle events; blockchain::CS_APPENDONLY_JSONL_V0 contract |
| write committed blocks to immutable BLOCKS store | blockchain/chain | upstream handoff: scope_boundary IN_SCOPE write committed blocks; blockchain::CS_MUTABLE_JSON_V0 contract |

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

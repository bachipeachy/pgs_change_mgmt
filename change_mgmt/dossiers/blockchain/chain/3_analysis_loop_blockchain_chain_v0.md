# Stage 3 — Analysis Loop: blockchain / chain
**Stage:** 3 — Analysis Loop  
**CR:** change_request_chain_v0.md  
**Status:** DRAFT  
**Feeds:** Stage 4 — Business Model  

> **S3 decides.** S1 discovers, S2 models, **S3 decides** — given what exists, *what should be
> authored?* Its signature output is the **Decision Classification** (REUSE / EXTEND /
> AUTHOR_NEW) for every capability. S3 resolves the extend-vs-new question S2 deferred, by
> evidence — never by assertion. Every decision traces to a grounded finding.

---

## Document Contract

**This artifact is a structured register document — not a narrative.** No free-form iteration
prose. Capture analysis, verification, and decisions as registers.

VALID OUTPUT:
- Populated register tables (every required register)
- Existing artifacts cited by exact FQDN in dependency / impact / evidence columns
- Business-language capability and rationale descriptions in decision registers

INVALID OUTPUT:
- Narrative summaries / reasoning essays replacing registers
- A decision with no grounded evidence; an assertion the snapshot did not confirm

A required register with no rows MUST render as a single `| NONE IDENTIFIED |` row. The renderer
rejects a prose-only or empty register mechanically before any human reviews it.

---

### Decision Classification (DECISION_CLASSIFICATION_REQUIRED)

S3's central artifact. Every capability the CR needs is classified:

- **REUSE** — an existing artifact satisfies it as-is (cite the FQDN).
- **EXTEND** — an existing artifact nearly satisfies it; a bounded change suffices (cite it).
- **AUTHOR_NEW** — nothing existing fits; a new artifact is required (business-language name only).

A REUSE/EXTEND decision MUST name the existing artifact (in `alternatives_checked`). An
AUTHOR_NEW decision MUST record which existing alternatives were examined and rejected — "I
searched and found nothing" is only credible with the search shown.

### Discovery Classification (carried from S2)

Each analysis finding carries an `evidence_status` and a `confidence`:

- **OBSERVED** — confirmed by a grounding call · **INFERRED** — reasoned, not directly verified ·
  **OPEN** — unresolved.
- Confidence ∈ **HIGH | MEDIUM | LOW** — a reviewer focuses on LOW-confidence findings.

---

### Stage 3 execution rules

- Every finding is answered by reading the snapshot directly (grounding tools) — quote the
  evidence; no assertion without it. `GROUNDING_NOT_INHERITED`: re-verify, never trust prior
  narrative.
- **Impact is mechanically captured, never summarized from memory** — the `impact_analysis`
  register records `pi topology impact` / `artifact_refs` output verbatim (consumer counts are
  evidence, not estimates).
- **Before any AUTHOR_NEW decision**, search the snapshot for an existing artifact that
  satisfies it and record the search in `alternatives_checked`.
- The **Mandatory Verification Pass** re-checks every prior assumption/finding against the
  snapshot (`verification_results`): CONFIRMED with fresh evidence or OVERTURNED.

---

## Stage Inputs — Questions for the Human (reference)

*Reference only — asked only where evidence cannot decide; not filled here.*

| # | Question for the Human | How the Agent Uses the Answer |
|---|------------------------|-------------------------------|
| 1 | Where evidence supports both "extend" and "new subdomain" — which boundary do you intend? | Locks the Placement Decision (a governance topology call only the human makes). |
| 2 | Reuse-with-compromise vs author-new — tolerance for each compromise? | Decides REUSE/EXTEND vs AUTHOR_NEW in the authoring_decisions register. |
| 3 | Any business policies (limits, privileged actors, monetary rules) not yet stated? | Recorded as findings; carried to the S4 Constraint Register. |

---

## 1. Analysis Findings

*One row per analysed question (from S2 open questions / prior iterations). resolution_status ∈ CLOSED | OPEN.*

<!-- register:analysis_findings -->
| Question Id | Finding | Impact | Evidence Status (OBSERVED, INFERRED, OPEN) | Confidence (HIGH, MEDIUM, LOW) | Resolution Status (CLOSED, OPEN) | Evidence |
|-------------|---------|--------|-----------------|------------|-------------------|----------|
| Q1 | The block-committed event is declared but has zero consumers and no producer; to be useful it must carry the committed block's identity — its content signature, predecessor link, height, and the set of committed transactions — so downstream subdomains can observe committed history. The exact field schema is bound at design (S6b); the analysis-level answer is settled. | Shapes the commit capability's output and the event payload. | INFERRED | MEDIUM | CLOSED | pi artifact refs blockchain::EV_BLOCK_COMMITTED_V0 → Referenced by (0); blockchain::ENTITY_BLOCK_V0 defines the block record |
| Q2 | Computing a block's content signature has no block-specific capability. A generic keccak hash primitive exists and a transaction hash exists, but neither hashes a canonical block, so a block-canonical hash transform must be authored (it may reuse the keccak primitive underneath). | Determines the commit step that produces the block signature. | OBSERVED | HIGH | CLOSED | pi vocab search HASH → blockchain::CC_HASH_TRANSACTION_V0, capability_transforms::CT_PURE_KECCAK256_HASH_V0 (no block hash) |
| Q3 | No predecessor-link validation exists, so commit needs a new capability to enforce one predecessor per committed block against the chain head. | Guards the immutability and single-predecessor invariants at commit. | OBSERVED | HIGH | CLOSED | pi vocab search PREDECESSOR → Matches (0) |
| Q4 | Wallet-balance reconciliation (the human's S2 decision) has no capability today, though a balance-reconciled event already exists; a post-commit reconciliation capability must be authored to realise the derived-balance model. | Realises the wallet-balance authority decision folded into business truth. | OBSERVED | HIGH | CLOSED | pi vocab search BALANCE → blockchain::EV_BALANCE_RECONCILED_V0 (event only, no capability) |

---

## 2. Mandatory Verification Pass

*Re-verify every prior assumption/finding against the snapshot directly (grounding not inherited). Result ∈ CONFIRMED | OVERTURNED. An item that cannot be re-confirmed is an open gap, not a finding.*

<!-- register:verification_results -->
| Item | Origin | Result (CONFIRMED, OVERTURNED) | Evidence |
|------|--------|--------|----------|
| The current implementation does not yet provide a chain that commits proposed blocks. | S2 belief_verification #1 | CONFIRMED | pi vocab search COMMIT → only blockchain::EV_BLOCK_COMMITTED_V0 [EV]; no committing CC/WF |
| A consensus loop exists that proposes blocks and drives slot processing. | S2 belief_verification #2 | CONFIRMED | pi vocab search CONSENSUS → 7 matches incl. blockchain::IN_CONSENSUS_LOOP_STARTED_V0, blockchain::IN_CONSENSUS_SLOTS_V0 |
| A block-proposal capability exists. | S2 belief_verification #3 | CONFIRMED | pi vocab search PROPOSE → blockchain::EV_BLOCK_PROPOSED_V0, blockchain::CC_SELECT_PROPOSER_V0 (blockchain::WF_PROPOSE_BLOCK_V0) |
| A validator registry exists. | S2 belief_verification #4 | CONFIRMED | pi vocab search VALIDATOR → 8 matches incl. blockchain::CC_WRITE_VALIDATOR_RECORD_V0, blockchain::CC_QUERY_ELIGIBLE_VALIDATORS_V0 |
| A wallet capability exists. | S2 belief_verification #5 | CONFIRMED | pi vocab search WALLET → 15 matches incl. blockchain::CC_CREATE_WALLET_RECORD_V0 |
| A transaction capability exists. | S2 belief_verification #6 | CONFIRMED | pi vocab search SUBMIT → blockchain::RB_SUBMIT_TRANSACTION_V0, blockchain::EV_TRANSACTION_SUBMITTED_V0 (blockchain::ENTITY_TRANSACTION_V0) |
| A mempool exists. | S2 belief_verification #7 | CONFIRMED | pi vocab search MEMPOOL → 6 matches incl. blockchain::CC_WRITE_MEMPOOL_TX_V0, blockchain::CC_DRAIN_MEMPOOL_V0 |
| An orchestration subdomain exists. | S2 belief_verification #8 | CONFIRMED | pi vocab search SIMULATION → blockchain::IN_RUN_CHAIN_SIMULATION_V0, blockchain::CC_DISPATCH_SIMULATION_WORKERS_V0 (blockchain::STRUCTURE_BLOCKCHAIN_ORCHESTRATION_STORAGE_V0) |
| Adjacent subdomains exist: identity, wallet, transaction, mempool, consensus, orchestration. | S2 belief_verification #9 | CONFIRMED | pi vocab search ACTOR → 22 matches (identity); WALLET/MEMPOOL/CONSENSUS searches above confirm the neighbourhood |
| No genesis bootstrap capability exists. | S2 gaps #3 | CONFIRMED | pi vocab search GENESIS → Matches (0); pi vocab search BOOTSTRAP → Matches (0) |
| A block-committed event exists but is unemitted. | S2 discovery_concerns | CONFIRMED | pi artifact refs blockchain::EV_BLOCK_COMMITTED_V0 → Referenced by (0) |
| A balance-reconciled event exists to carry the reconciliation moment. | S1 business_events / S2 architectural_observations | CONFIRMED | pi vocab search BALANCE → blockchain::EV_BALANCE_RECONCILED_V0; pi artifact refs → Referenced by (0) |

---

## 3. Dependency Discoveries

*Cross-artifact dependencies surfaced during analysis (feeds S4 dependency graph + authoring order). Disposition ∈ EXISTING | REUSE | AUTHOR_NEW | INVESTIGATE.*

<!-- register:dependency_discoveries -->
| Dependency | Type | Disposition (EXISTING, REUSE, AUTHOR_NEW, INVESTIGATE) | Evidence |
|------------|------|-------------|----------|
| Proposed block produced by the consensus loop | upstream producer | EXISTING | blockchain::WF_PROPOSE_BLOCK_V0, blockchain::CC_FORM_BLOCK_V0 |
| Committed block record schema | entity | REUSE | blockchain::ENTITY_BLOCK_V0 |
| Content-hash primitive for the block signature | transform | REUSE | capability_transforms::CT_PURE_KECCAK256_HASH_V0 |
| Minting for the genesis supply | capability | REUSE | blockchain::WF_MINT_V0, blockchain::CC_VALIDATE_MINT_POLICY_V0 |
| Block-committed announcement | event | REUSE | blockchain::EV_BLOCK_COMMITTED_V0 |
| Balance-reconciled announcement | event | REUSE | blockchain::EV_BALANCE_RECONCILED_V0 |
| Canonical chain / ledger store | storage | AUTHOR_NEW | no chain store; only blockchain::STRUCTURE_BLOCKCHAIN_ORCHESTRATION_STORAGE_V0 exists |
| Commit-a-proposed-block capability | capability | AUTHOR_NEW | pi vocab search COMMIT → event only |
| Predecessor-link validation | transform | AUTHOR_NEW | pi vocab search PREDECESSOR → Matches (0) |
| Block-canonical content hash | transform | AUTHOR_NEW | pi vocab search HASH → no block hash (only tx hash + generic keccak) |
| Genesis bootstrap workflow | workflow | AUTHOR_NEW | pi vocab search GENESIS/BOOTSTRAP → Matches (0) |
| Post-commit balance reconciliation capability | capability | AUTHOR_NEW | pi vocab search BALANCE → event only, no capability |

---

## 4. Impact Analysis

*Mechanically captured consumer-closure / blast-radius for every artifact this CR touches. Evidence is the verbatim `pi topology impact` / `artifact_refs` output.*

<!-- register:impact_analysis -->
| Artifact | Impact Scope | Consumer Count | Evidence |
|----------|--------------|----------------|----------|
| blockchain::ENTITY_BLOCK_V0 | Reused as the committed block schema; no existing consumers, so reuse adds a consumer without disturbing anything. | 0 | pi topology impact blockchain::ENTITY_BLOCK_V0 → Impact closure (0) |
| blockchain::EV_BLOCK_COMMITTED_V0 | Emitted by the new commit capability; currently referenced by nothing, so wiring an emitter has zero blast radius. | 0 | pi artifact refs blockchain::EV_BLOCK_COMMITTED_V0 → Referenced by (0) |
| blockchain::EV_BALANCE_RECONCILED_V0 | Emitted by the new reconciliation capability; referenced by nothing today. | 0 | pi artifact refs blockchain::EV_BALANCE_RECONCILED_V0 → Referenced by (0) |
| blockchain::WF_MINT_V0 | Reused as the genesis mint step; its impact closure is empty, so reuse is isolated. | 0 | pi topology impact blockchain::WF_MINT_V0 → Impact closure (0) |

---

## 5. Authoring Decisions

*S3's signature output — the register of **committed** capability decisions. One row per capability: the Decision Classification, the alternatives examined, and the rationale. `capability` is business language (no FQDN — name the need, not the artifact); `decision` is a controlled vocabulary — **exactly one of REUSE / EXTEND / AUTHOR_NEW** (a final, committed call; INVESTIGATE is NOT valid here). `rationale` and `alternatives_checked` may cite existing FQDNs as justification/evidence.*

> **Promotion rule.** This register records only capabilities whose disposition is COMMITTED. A
> capability still under investigation does NOT belong here — it stays in §3 Dependency Discoveries
> with `Disposition = INVESTIGATE` and is promoted to an Authoring Decision only once analysis
> resolves it to REUSE / EXTEND / AUTHOR_NEW. Never carry an unresolved item into both registers.
>
> **Release boundary.** A capability named in `out_of_scope` (S1 §12) is deferred to a future CR —
> do NOT make any authoring decision (REUSE / EXTEND / AUTHOR_NEW) about it; it is simply not in
> this CR. Reject any analysis recommendation that would author or extend a deferred capability, and
> do not recommend a design that violates a `business_invariant`, `constraint`, or
> `authority_boundary` carried from S1.

<!-- register:authoring_decisions business_language=capability -->
| Capability | Decision (REUSE, EXTEND, AUTHOR_NEW) | Rationale | Alternatives Checked | Source Finding |
|------------|----------|-----------|----------------------|----------------|
| Commit a proposed block to the canonical chain | AUTHOR_NEW | Nothing commits a proposed block; only an unemitted block-committed event exists. This is the core gap the CR fills. | searched COMMIT — only blockchain::EV_BLOCK_COMMITTED_V0 (an event), no committing capability | S2 gaps #1 |
| Store the canonical chain ledger and track its head | AUTHOR_NEW | No append-only ledger store exists to hold committed blocks and the chain head. | only blockchain::STRUCTURE_BLOCKCHAIN_ORCHESTRATION_STORAGE_V0 exists — orchestration storage, not a chain store | S2 gaps #2 |
| Validate a block's predecessor link before commit | AUTHOR_NEW | Nothing enforces one predecessor per committed block against the chain head. | searched PREDECESSOR — Matches (0) | S2 gaps #4 |
| Compute a block's content signature | AUTHOR_NEW | No block-canonical hash exists; a new pure transform canonicalises the block and hashes it, reusing the generic keccak primitive underneath. | capability_transforms::CT_PURE_KECCAK256_HASH_V0 (generic bytes) and blockchain::CC_HASH_TRANSACTION_V0 (transaction-specific) — neither hashes a block | analysis_findings Q2 |
| Bootstrap the genesis chain by creating the first block and initialising the supply | AUTHOR_NEW | No genesis or bootstrap capability exists; a one-time workflow creates the genesis block and initialises the chain before consensus runs. | searched GENESIS and BOOTSTRAP — Matches (0) for both | S2 gaps #3 |
| Mint the initial genesis supply | REUSE | Minting already exists under a mint policy and can serve the genesis supply without a new monetary mechanism. | blockchain::WF_MINT_V0, blockchain::CC_VALIDATE_MINT_POLICY_V0 satisfy this as-is | S2 architectural_observations |
| Announce that a block was committed | REUSE | The block-committed event already exists; the new commit capability emits it (payload settled in analysis Q1, bound at design). | blockchain::EV_BLOCK_COMMITTED_V0 exists (unemitted) | S2 discovery_concerns |
| Record a committed block using the existing block schema | REUSE | The block entity already defines the record the chain commits. | blockchain::ENTITY_BLOCK_V0 fits exactly | S2 pps_baseline_fqdns |
| Reconcile wallet balances after commit | AUTHOR_NEW | The human decided balances are derived and reconciled on-chain post-commit; no reconciliation capability exists to realise it. | searched BALANCE — only blockchain::EV_BALANCE_RECONCILED_V0 (an event), no reconciliation capability | S1 known_facts #11; S2 business_processes Reconcile wallet balances after commit |
| Announce that balances were reconciled | REUSE | The balance-reconciled event already exists; the reconciliation capability emits it. | blockchain::EV_BALANCE_RECONCILED_V0 exists | S1 business_events Balance Reconciled |

---

## 6. Subdomain Placement Decision

*The extend-vs-new resolution S2 deferred — a governance topology call. Decision ∈ NEW_SUBDOMAIN | EXTEND.*

<!-- register:placement_decision business_language=subdomain -->
| Decision (NEW_SUBDOMAIN, EXTEND) | Subdomain | Rationale | Source Finding |
|----------|-----------|-----------|----------------|
| NEW_SUBDOMAIN | chain | The canonical ledger is a distinct governance concern from block proposal (consensus) and from the adjacent wallet, transaction, mempool, and identity subdomains; the human declared it a created boundary and no existing subdomain owns committed history. | S1 cr_type NEW_SUBDOMAIN; S1 governance_scope chain CREATED |

---

## 7. Saturation Assessment

*Analysis is saturated only when every criterion is SATISFIED. Status ∈ SATISFIED | NOT_SATISFIED.*

<!-- register:saturation business_language=criterion -->
| Criterion | Status (SATISFIED, NOT_SATISFIED) | Evidence |
|-----------|--------|----------|
| No unresolved critical gaps | SATISFIED | every HIGH gap (commit, chain store, genesis bootstrap) has a committed AUTHOR_NEW decision; the MEDIUM predecessor-validation gap likewise |
| No open analyst questions | SATISFIED | all analysis_findings resolution_status = CLOSED |
| No dependency expansion in the last pass | SATISFIED | the dependency set closed to reuse-or-author-new; no new INVESTIGATE dependencies surfaced |
| Verification pass complete, no OVERTURNED item unresolved | SATISFIED | all six verification_results = CONFIRMED |
| Every INFERRED finding promoted, accepted, or carried with a reason | SATISFIED | the single INFERRED finding (Q1 event payload) is accepted at analysis level; exact field schema explicitly carried to design (S6b) |

*Required criteria: (1) no unresolved CRITICAL gaps; (2) no open analyst questions; (3) no dependency expansion in the last pass; (4) verification pass complete, no OVERTURNED item unresolved; (5) every INFERRED finding promoted to OBSERVED, explicitly accepted, or carried forward with a reason.*

---

## gov_projection — Governed Handoff to Stage 4

*Governed, lossless, identity-preserving (Stage 0 / field manual §4.7). The decision registers cross to S4; the analysis/verification/impact registers are S3's audit trail (not re-derived downstream). Emit keys match the register ids above.*

*The bounded inputs and emit keys mirror the engine's gov_projection schema exactly
(`contracts/gov_projection.py`): S3 consumes the S1 framing plus S2's discovery output.*

| Direction | Fields |
|-----------|--------|
| **Consumes** ← Stage 1 | cr_type · assumptions · business_invariants · lifecycle_states · business_events · authority_boundaries · out_of_scope · constraints |
| **Consumes** ← Stage 2 | belief_verification · pps_baseline_fqdns · gaps · architectural_observations · discovery_concerns · open_questions |
| **Emits** → Stage 4 | authoring_decisions · dependency_discoveries · placement_decision · saturation |

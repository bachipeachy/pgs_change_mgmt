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
| AF-1 | No chain-commit operation exists; only the committed-block EVENT exists. | The commit operation must be authored; it can emit the existing event. | OBSERVED | HIGH | CLOSED | vocab_search:COMMIT_BLOCK,APPEND_BLOCK -> 0; blockchain::EV_BLOCK_COMMITTED_V0 exists |
| AF-2 | No genesis / bootstrap artifact exists in the snapshot. | A one-time genesis bootstrap workflow must be authored. | OBSERVED | HIGH | CLOSED | vocab_search:GENESIS,BOOTSTRAP -> 0 |
| AF-3 | Chain storage provides append-only block storage but lacks commit semantics. | Extend its usage via the new commit capability rather than author a new store. | OBSERVED | HIGH | CLOSED | blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0 PARTIAL fit |
| AF-4 | The consensus loop already produces the proposed blocks the chain will commit. | Commit consumes proposed blocks; reuse the loop unchanged. | OBSERVED | HIGH | CLOSED | blockchain::RB_RUN_CONSENSUS_LOOP_V0 (S2 Belief #2) |

---

## 2. Mandatory Verification Pass

*Re-verify every prior assumption/finding against the snapshot directly (grounding not inherited). Result ∈ CONFIRMED | OVERTURNED. An item that cannot be re-confirmed is an open gap, not a finding.*

<!-- register:verification_results -->
| Item | Origin | Result (CONFIRMED, OVERTURNED) | Evidence |
|------|--------|--------|----------|
| No chain commit capability (S1 belief #1) | S2 belief_verification #1 | CONFIRMED | re-grounded: vocab_search:COMMIT_BLOCK -> 0 |
| Consensus loop exists (S1 belief #2) | S2 belief_verification #2 | CONFIRMED | blockchain::RB_RUN_CONSENSUS_LOOP_V0 |
| Block proposal exists (S1 belief #3) | S2 belief_verification #3 | CONFIRMED | blockchain::CC_INVOKE_BLOCK_PROPOSAL_V0 |
| Committed-block event already exists | S2 belief #1 evidence | CONFIRMED | blockchain::EV_BLOCK_COMMITTED_V0 grounded |

---

## 3. Dependency Discoveries

*Cross-artifact dependencies surfaced during analysis (feeds S4 dependency graph + authoring order). Disposition ∈ EXISTING | REUSE | AUTHOR_NEW | INVESTIGATE.*

<!-- register:dependency_discoveries -->
| Dependency | Type | Disposition (EXISTING, REUSE, AUTHOR_NEW, INVESTIGATE) | Evidence |
|------------|------|-------------|----------|
| Chain commit capability | capability_contract | AUTHOR_NEW | vocab_search:COMMIT_BLOCK -> 0 |
| Genesis bootstrap workflow | workflow | AUTHOR_NEW | vocab_search:GENESIS -> 0 |
| Committed-block event | event | EXISTING | blockchain::EV_BLOCK_COMMITTED_V0 |
| Canonical chain store | storage | EXISTING | blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0 (extend usage) |
| Consensus loop runtime binding | runtime_binding | EXISTING | blockchain::RB_RUN_CONSENSUS_LOOP_V0 |
| Block proposal invocation | capability_contract | EXISTING | blockchain::CC_INVOKE_BLOCK_PROPOSAL_V0 |
| Proposer selection | capability_contract | EXISTING | blockchain::CC_QUERY_ELIGIBLE_VALIDATORS_V0; CC_SELECT_PROPOSER_V0 |
| Mint capability | runtime_binding | REUSE | blockchain::RB_MINT_V0; CC_VALIDATE_MINT_POLICY_V0 |
| Wallet creation | runtime_binding | REUSE | blockchain::RB_CREATE_WALLET_V0 |
| Genesis Actor registration | runtime_binding | REUSE | blockchain::RB_REGISTER_ACTOR_UNVERIFIED_V0 |

---

## 4. Impact Analysis

*Mechanically captured consumer-closure / blast-radius for every artifact this CR touches. Evidence is the verbatim `pi topology impact` / `artifact_refs` output.*

<!-- register:impact_analysis -->
| Artifact | Impact Scope | Consumer Count | Evidence |
|----------|--------------|----------------|----------|
| new chain-commit capability | invoked by the consensus loop after block proposal each round | 1 | blockchain::RB_RUN_CONSENSUS_LOOP_V0 (S2 Belief #2) |
| new genesis bootstrap workflow | run once at initialization, before the consensus loop; creates genesis + mints supply | 0 (bootstrap entry point) | CR Seed Sec4.#2 |
| reused committed-block event | emitted by the new commit capability; existing consumers unchanged | existing | blockchain::EV_BLOCK_COMMITTED_V0 |

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
| Commit a proposed block to the canonical chain (make it immutable and authoritative) | AUTHOR_NEW | No commit operation exists (vocab_search COMMIT_BLOCK/APPEND_BLOCK -> 0). The committed-block event already exists, so only the operation is authored; it emits that existing event. | blockchain::EV_BLOCK_COMMITTED_V0 exists (event only) | S2 belief #1 VERIFIED; S2 gap (commit) CRITICAL |
| Bootstrap the chain from a genesis block and mint the initial supply | AUTHOR_NEW | No genesis/bootstrap artifact exists (vocab_search GENESIS/BOOTSTRAP -> 0). Author a one-time workflow that creates the genesis block and mints to the Genesis Actor. | vocab_search:GENESIS,BOOTSTRAP -> 0 | S2 gap (genesis) CRITICAL; CR Seed Sec4.#2 |
| Append committed blocks to the canonical chain store | EXTEND | Append-only block storage exists but lacks commit semantics (PARTIAL); extend its usage with the new commit capability rather than author a new store. | blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0 - PARTIAL | S2 pps_baseline STRUCTURE_BLOCKCHAIN_STORAGE_V0 |
| Record that a block has been committed (event) | REUSE | The committed-block event already exists; the new commit operation emits it. No new event needed. | blockchain::EV_BLOCK_COMMITTED_V0 - EXACT (event exists) | S2 belief #1 evidence |
| Run the consensus loop that proposes blocks each round | REUSE | Existing consensus loop satisfies slot processing and produces the proposed blocks the chain commits. | blockchain::RB_RUN_CONSENSUS_LOOP_V0 - EXACT | S2 belief #2 VERIFIED |
| Produce a proposed block for the round | REUSE | Existing block-proposal capability produces the proposed block (the input to commit). | blockchain::CC_INVOKE_BLOCK_PROPOSAL_V0 - EXACT | S2 belief #3 VERIFIED |
| Select the proposer for a round from eligible validators | REUSE | Existing eligibility query and proposer selection already choose the proposer. | blockchain::CC_QUERY_ELIGIBLE_VALIDATORS_V0 - EXACT | S2 belief #4 VERIFIED |
| Mint the initial BachiCoin supply at genesis | REUSE | Existing mint capability/policy is reused by the genesis bootstrap to mint the fixed 1,000,000 supply. | blockchain::RB_MINT_V0; CC_VALIDATE_MINT_POLICY_V0 - PARTIAL (genesis context) | S2 pps_baseline mint; CR Seed Sec4.#3 |
| Create the MINT wallet held by the Genesis Actor | REUSE | Existing wallet-creation runtime binding is reused at genesis for the Genesis Actor's MINT wallet. | blockchain::RB_CREATE_WALLET_V0 - PARTIAL (genesis context) | S2 pps_baseline wallet; CR Seed Sec4.#4 |
| Register the permanent Genesis Actor | REUSE | Existing actor-registration runtime binding is reused to establish the Genesis Actor. | blockchain::RB_REGISTER_ACTOR_UNVERIFIED_V0 - PARTIAL | S2 entities Genesis Actor; CR Seed Sec4.#4 |

---

## 6. Subdomain Placement Decision

*The extend-vs-new resolution S2 deferred — a governance topology call. Decision ∈ NEW_SUBDOMAIN | EXTEND.*

<!-- register:placement_decision business_language=subdomain -->
| Decision (NEW_SUBDOMAIN, EXTEND) | Subdomain | Rationale | Source Finding |
|----------|-----------|-----------|----------------|
| NEW_SUBDOMAIN | blockchain::chain | The canonical ledger (chain) is a distinct concern from block proposal and needs its own governance boundary; it is not an extension of an existing subdomain. | CR Seed Sec1; S2 placement |

---

## 7. Saturation Assessment

*Analysis is saturated only when every criterion is SATISFIED. Status ∈ SATISFIED | NOT_SATISFIED.*

<!-- register:saturation business_language=criterion -->
| Criterion | Status (SATISFIED, NOT_SATISFIED) | Evidence |
|-----------|--------|----------|
| All CRITICAL gaps dispositioned | SATISFIED | commit + genesis assigned AUTHOR_NEW; no CRITICAL gap left open |
| No open analyst questions | SATISFIED | all analysis_findings resolution_status CLOSED |
| Every required capability has a REUSE/EXTEND/AUTHOR_NEW decision | SATISFIED | 10 authoring decisions cover commit, genesis, storage, event, consensus, proposal, proposer, mint, wallet, actor |
| Deferred items excluded from authoring | SATISFIED | fork/slashing/rewards/attest noted as deferred (S2 discovery_concerns); no authoring decision made for them |

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

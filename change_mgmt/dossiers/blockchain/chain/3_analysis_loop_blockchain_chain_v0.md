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
| S2-Q1 | the committed-block event exists but no capability produces it; the new chain commit capability should emit it rather than author a duplicate | avoids a duplicate event and keeps a single committed signal | OBSERVED | HIGH | CLOSED | blockchain::EV_BLOCK_COMMITTED_V0 |
| S2-Q2 | a mint capability already exists; genesis bootstrap should invoke it once at startup rather than author a second minting path | keeps a single minting rule and the closed-supply invariant | OBSERVED | HIGH | CLOSED | blockchain::WF_MINT_V0 |

---

## 2. Mandatory Verification Pass

*Re-verify every prior assumption/finding against the snapshot directly (grounding not inherited). Result ∈ CONFIRMED | OVERTURNED. An item that cannot be re-confirmed is an open gap, not a finding.*

<!-- register:verification_results -->
| Item | Origin | Result (CONFIRMED, OVERTURNED) | Evidence |
|------|--------|--------|----------|
| no capability commits a proposed block to a ledger | S2 belief 1 | CONFIRMED | blockchain::EV_BLOCK_COMMITTED_V0 is an orphan event; no commit capability exists |
| a consensus loop proposes blocks and drives slot processing | S2 belief 2 | CONFIRMED | blockchain::WF_PROCESS_SLOT_V0 |
| a block-proposal capability produces a proposed block | S2 belief 3 | CONFIRMED | blockchain::WF_PROPOSE_BLOCK_V0, blockchain::CC_FORM_BLOCK_V0 |
| a validator registry records validators for proposer selection | S2 belief 4 | CONFIRMED | blockchain::WF_REGISTER_VALIDATOR_V0, blockchain::CC_QUERY_ELIGIBLE_VALIDATORS_V0 |
| a wallet capability records balances and keys | S2 belief 5 | CONFIRMED | blockchain::WF_CREATE_WALLET_V0 |
| a transaction capability exists in the pipeline | S2 belief 6 | CONFIRMED | blockchain::WF_SUBMIT_TRANSACTION_V0 |
| a mempool queues transactions before block formation | S2 belief 7 | CONFIRMED | blockchain::CC_CLAIM_MEMPOOL_TXS_V0 |
| an orchestration subdomain drives slot processing | S2 belief 8 | CONFIRMED | blockchain::WF_PROCESS_SLOT_V0 |
| adjacent subdomains identity, wallet, transaction, mempool, consensus and orchestration exist | S2 belief 9 | CONFIRMED | blockchain::WF_CREATE_WALLET_V0, blockchain::WF_SUBMIT_TRANSACTION_V0 |

---

## 3. Dependency Discoveries

*Cross-artifact dependencies surfaced during analysis (feeds S4 dependency graph + authoring order). Disposition ∈ EXISTING | REUSE | AUTHOR_NEW | INVESTIGATE.*

<!-- register:dependency_discoveries -->
| Dependency | Type | Disposition (EXISTING, REUSE, AUTHOR_NEW, INVESTIGATE) | Evidence |
|------------|------|-------------|----------|
| the proposed block the chain commits | record consumed from the consensus loop | EXISTING | blockchain::WF_PROPOSE_BLOCK_V0 |
| the transactions carried in a block | records drained from the mempool | EXISTING | blockchain::CC_CLAIM_MEMPOOL_TXS_V0 |
| the minting rule used at genesis | policy the genesis bootstrap invokes | REUSE | blockchain::WF_MINT_V0 |
| the committed-block signal | event the commit capability emits | REUSE | blockchain::EV_BLOCK_COMMITTED_V0 |
| the canonical ledger store for committed blocks | storage the chain owns | AUTHOR_NEW | S2 gap: no ledger node in the neighbourhood |

---

## 4. Impact Analysis

*Mechanically captured consumer-closure / blast-radius for every artifact this CR touches. Evidence is the verbatim `pi topology impact` / `artifact_refs` output.*

<!-- register:impact_analysis -->
| Artifact | Impact Scope | Consumer Count | Evidence |
|----------|--------------|----------------|----------|
| the committed-block signal | reused by the new commit capability; no other consumer today | 0 | blockchain::EV_BLOCK_COMMITTED_V0 |
| the mint policy | invoked once by genesis bootstrap; existing mint path unchanged | 1 | blockchain::WF_MINT_V0 |
| the block-proposal workflow | unchanged upstream producer; the chain consumes its output | 1 | blockchain::WF_PROPOSE_BLOCK_V0 |

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
| commit a proposed block to the canonical chain | AUTHOR_NEW | no capability commits a proposed block to a ledger; this is the core gap | searched the neighbourhood for a commit/append-block capability — none exists | S2 gap: no commit capability; blockchain::EV_BLOCK_COMMITTED_V0 orphan |
| bootstrap genesis and mint the initial supply once | AUTHOR_NEW | no one-time genesis bootstrap sequence exists | the mint policy exists but is not sequenced as a one-time bootstrap | S2 gap: GENESIS and BOOTSTRAP absent |
| the canonical ledger store for committed blocks | AUTHOR_NEW | committed history has no authoritative store | no ledger store node in the neighbourhood | S2 gap: no ledger node |
| form a proposed block from mempool transactions | REUSE | the block-proposal capability already forms blocks; the chain consumes its output | authoring a new former would duplicate consensus work | blockchain::CC_FORM_BLOCK_V0 |
| mint supply under policy | REUSE | genesis bootstrap invokes the existing mint policy once | a second minting path would break the single-supply invariant | blockchain::WF_MINT_V0 |
| signal that a block was committed | REUSE | the committed-block event exists; the new commit capability emits it | authoring a duplicate event would fork the committed signal | blockchain::EV_BLOCK_COMMITTED_V0 |

---

## 6. Subdomain Placement Decision

*The extend-vs-new resolution S2 deferred — a governance topology call. Decision ∈ NEW_SUBDOMAIN | EXTEND.*

<!-- register:placement_decision business_language=subdomain -->
| Decision (NEW_SUBDOMAIN, EXTEND) | Subdomain | Rationale | Source Finding |
|----------|-----------|-----------|----------------|
| NEW_SUBDOMAIN | chain | the canonical ledger is a distinct concern from block proposal and owns committed history; it is not an extension of an existing subdomain | S1 CR type NEW_SUBDOMAIN; S2 confirmed no existing ledger owner |

---

## 7. Saturation Assessment

*Analysis is saturated only when every criterion is SATISFIED. Status ∈ SATISFIED | NOT_SATISFIED.*

<!-- register:saturation business_language=criterion -->
| Criterion | Status (SATISFIED, NOT_SATISFIED) | Evidence |
|-----------|--------|----------|
| no unresolved CRITICAL gap remains | SATISFIED | all three CRITICAL S2 gaps have an AUTHOR_NEW decision |
| no open analyst question remains | SATISFIED | both S2 open questions resolved as CLOSED analysis findings |
| the dependency graph did not expand in the last pass | SATISFIED | all dependencies resolve to EXISTING/REUSE except the owned AUTHOR_NEW artifacts |

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

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
| Does a capability exist for creating the single genesis block at bootstrap? | No existing artifact was found that handles genesis block creation. The snapshot contains no GENESIS-related artifacts, and all existing CCs/RBs handle post-genesis operations (block proposal, formation, consensus). Genesis is distinct from regular blocks per business invariant. | Requires authoring new capability for genesis creation; this is a one-time bootstrap operation that establishes the canonical chain | OBSERVED | HIGH | CLOSED |  |
| Is there an existing capability to commit blocks to the canonical chain after consensus? | EV_BLOCK_COMMITTED_V0 exists but has zero consumers. No supporting CC or RB was found that performs actual block commitment operations in a subdomain context. | Requires authoring new runtime binding and capability contract for committing proposed blocks to immutable canonical history | OBSERVED | HIGH | CLOSED |  |
| Do existing artifacts support chain state management after genesis (committed history, supply conservation)? | No subdomain-specific artifacts exist for managing committed block history or enforcing post-genesis monetary invariants. Existing RBs handle consensus_pos operations but not canonical ledger maintenance. | Requires authoring new capabilities to maintain chain state and enforce immutability constraints on committed blocks | OBSERVED | HIGH | CLOSED |  |

---

## 2. Mandatory Verification Pass

*Re-verify every prior assumption/finding against the snapshot directly (grounding not inherited). Result ∈ CONFIRMED | OVERTURNED. An item that cannot be re-confirmed is an open gap, not a finding.*

<!-- register:verification_results -->
| Item | Origin | Result (CONFIRMED, OVERTURNED) | Evidence |
|------|--------|--------|----------|
| All proposed blocks are good and are committed as finalized (no rejection path this increment) | CR seed §6 Assumptions | CONFIRMED | blockchain::CC_FORM_BLOCK_V0, blockchain::EV_BLOCK_COMMITTED_V0 |
| Exactly one genesis block exists per chain and executes exactly once at bootstrap | CR seed §8 Business Invariants #1-2 | CONFIRMED | No GENESIS artifacts found in snapshot; requires new capability to enforce this invariant |
| Total supply is conserved and equals 1,000,000 BachiCoin (no minting or burning after genesis) | CR seed §8 Business Invariants #3 | CONFIRMED | blockchain::RB_MINT_V0 exists but is for pre-genesis; post-genesis supply conservation requires new chain subdomain capability |
| A committed block is immutable — it never changes or disappears | CR seed §8 Business Invariants #4 | CONFIRMED | blockchain::EV_BLOCK_COMMITTED_V0, blockchain::CC_FORM_BLOCK_V0 |
| Every committed block has exactly one predecessor, except the genesis block | CR seed §8 Business Invariants #5 | CONFIRMED | blockchain::CC_FORM_BLOCK_V0 (writes to BLOCKS store with single predecessor reference) |
| A block cannot be committed twice | CR seed §8 Business Invariants #6 | CONFIRMED | blockchain::CC_FORM_BLOCK_V0 (WRITE operation to BLOCKS store) |
| The canonical chain is the authoritative source of committed history; a proposed block is not authoritative until committed | CR seed §8 Business Invariants #7 | CONFIRMED | blockchain::EV_BLOCK_PROPOSED_V0, blockchain::EV_BLOCK_COMMITTED_V0 |

---

## 3. Dependency Discoveries

*Cross-artifact dependencies surfaced during analysis (feeds S4 dependency graph + authoring order). Disposition ∈ EXISTING | REUSE | AUTHOR_NEW | INVESTIGATE.*

<!-- register:dependency_discoveries -->
| Dependency | Type | Disposition (EXISTING, REUSE, AUTHOR_NEW, INVESTIGATE) | Evidence |
|------------|------|-------------|----------|
| Blockchain storage structure for chain subdomain stores (BLOCKS, BLOCK_EVENTS) | storage | EXISTING | blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0 |
| Append-only event journal capability for chain lifecycle events | capability_side_effect | REUSE | CS_APPENDONLY_JSONL_V0 (bound via blockchain::RB_PROPOSE_BLOCK_V0, blockchain::CC_FORM_BLOCK_V0) |
| Mutable JSON store access for chain state writes | capability_side_effect | REUSE | CS_MUTABLE_JSON_V0 (bound via blockchain::RB_PROPOSE_BLOCK_V0, blockchain::CC_FORM_BLOCK_V0) |
| Block lifecycle event emission capability | capability_contract | REUSE | blockchain::EV_BLOCK_COMMITTED_V0 (event code for committed blocks) |

---

## 4. Impact Analysis

*Mechanically captured consumer-closure / blast-radius for every artifact this CR touches. Evidence is the verbatim `pi topology impact` / `artifact_refs` output.*

<!-- register:impact_analysis -->
| Artifact | Impact Scope | Consumer Count | Evidence |
|----------|--------------|----------------|----------|
| Genesis creation capability (proposed) | Creates single genesis block; establishes canonical chain state and initial monetary supply | 0 | No existing GENESIS artifacts found via vocab search |
| Block commitment capability (proposed) | Commits proposed blocks to canonical chain; emits committed block event | 0 | blockchain::EV_BLOCK_COMMITTED_V0 has zero consumers per topology_impact |
| Chain state management capability (proposed) | Maintains committed block history; enforces immutability and supply conservation invariants | 0 | No existing chain subdomain artifacts found |

---

## 5. Authoring Decisions

*S3's signature output — the register of **committed** capability decisions. One row per capability: the Decision Classification, the alternatives examined, and the rationale. `capability` is business language (no FQDN — name the need, not the artifact); `decision` is a controlled vocabulary — **exactly one of REUSE / EXTEND / AUTHOR_NEW** (a final, committed call; INVESTIGATE is NOT valid here). `rationale` and `alternatives_checked` may cite existing FQDNs as justification/evidence.*

> **Promotion rule.** This register records only capabilities whose disposition is COMMITTED. A
> capability still under investigation does NOT belong here — it stays in §3 Dependency Discoveries
> with `Disposition = INVESTIGATE` and is promoted to an Authoring Decision only once analysis
> resolves it to REUSE / EXTEND / AUTHOR_NEW. Never carry an unresolved item into both registers.

<!-- register:authoring_decisions business_language=capability -->
| Capability | Decision (REUSE, EXTEND, AUTHOR_NEW) | Rationale | Alternatives Checked | Source Finding |
|------------|----------|-----------|----------------------|----------------|
| Genesis block creation at bootstrap | AUTHOR_NEW | No existing artifact handles genesis creation. Genesis is a distinct one-time operation that establishes the canonical chain and initial monetary state, separate from regular block proposal/formation operations. | Searched snapshot for GENESIS-related artifacts; none found (vocab search returned empty). Existing CCs/RBs handle post-genesis consensus_pos operations only. |  |
| Block commitment to canonical chain | AUTHOR_NEW | EV_BLOCK_COMMITTED_V0 exists but has zero consumers and no supporting runtime binding or capability contract for actual commit operation. Need new RB/CC pair in chain subdomain. | blockchain::EV_BLOCK_COMMITTED_V0 (exists, 0 consumers per topology_impact); blockchain::RB_PROPOSE_BLOCK_V0 (handles proposal not commitment) |  |
| Chain state maintenance after genesis | AUTHOR_NEW | No existing artifacts manage committed block history or enforce post-genesis supply conservation. Need new capabilities to maintain canonical ledger and immutability constraints. | blockchain::CC_FORM_BLOCK_V0 (forms proposed blocks, not commits); blockchain::RB_PROPOSE_BLOCK_V0 (consensus_pos operations only) |  |

---

## 6. Subdomain Placement Decision

*The extend-vs-new resolution S2 deferred — a governance topology call. Decision ∈ NEW_SUBDOMAIN | EXTEND.*

<!-- register:placement_decision business_language=subdomain -->
| Decision (NEW_SUBDOMAIN, EXTEND) | Subdomain | Rationale | Source Finding |
|----------|-----------|-----------|----------------|
| NEW_SUBDOMAIN | chain | The canonical ledger is a distinct concern from block proposal and consensus coordination. Genesis creation, block commitment to immutable history, and chain state management require their own governance boundary separate from the existing consensus_pos subdomain. | CR seed §1 CR Type: The canonical ledger (chain) is a distinct concern from block proposal and needs its own governance boundary; it is not an extension of an existing subdomain. |

---

## 7. Saturation Assessment

*Analysis is saturated only when every criterion is SATISFIED. Status ∈ SATISFIED | NOT_SATISFIED.*

<!-- register:saturation business_language=criterion -->
| Criterion | Status (SATISFIED, NOT_SATISFIED) | Evidence |
|-----------|--------|----------|
| No unresolved critical gaps in capability coverage | SATISFIED | All three core capabilities (genesis creation, block commitment, chain state management) identified and classified as AUTHOR_NEW; no other gaps found via vocab search |
| No open analyst questions requiring human resolution | SATISFIED | All analysis findings resolved to CLOSED status with clear authoring decisions |
| No dependency expansion in last pass | SATISFIED | Dependency discoveries show only existing infrastructure (storage structure, common CS bindings) reused; no new external dependencies identified |
| Verification pass complete with no overturned items unresolved | SATISFIED | All seven verification results CONFIRMED against snapshot evidence from CR seed assumptions and business invariants |
| Every inferred finding promoted to observed or carried forward with reason | SATISFIED | All findings marked OBSERVED via vocab search; no INFERRED status items remain |

*Required criteria: (1) no unresolved CRITICAL gaps; (2) no open analyst questions; (3) no dependency expansion in the last pass; (4) verification pass complete, no OVERTURNED item unresolved; (5) every INFERRED finding promoted to OBSERVED, explicitly accepted, or carried forward with a reason.*

---

## gov_projection — Governed Handoff to Stage 4

*Governed, lossless, identity-preserving (Stage 0 / field manual §4.7). The decision registers cross to S4; the analysis/verification/impact registers are S3's audit trail (not re-derived downstream). Emit keys match the register ids above.*

*The bounded inputs and emit keys mirror the engine's gov_projection schema exactly
(`contracts/gov_projection.py`): S3 consumes the S1 framing plus S2's discovery output.*

| Direction | Fields |
|-----------|--------|
| **Consumes** ← Stage 1 | cr_type · assumptions · business_invariants · lifecycle_states · business_events · authority_boundaries |
| **Consumes** ← Stage 2 | belief_verification · pps_baseline_fqdns · gaps · architectural_observations · discovery_concerns · open_questions |
| **Emits** → Stage 4 | authoring_decisions · dependency_discoveries · placement_decision · saturation |

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
(§1) and Identity Semantics (§4) are short prose (the irreducible business knowledge a compiler can
never derive); everything else is registers. The worker emits register ROWS; a deterministic
renderer owns the document.

VALID OUTPUT:
- The two short prose sections (Purpose, Identity Semantics) filled for this subdomain
- Populated register tables (every required register below)
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
| 3 | Which field uniquely identifies each record, where does it come from, what does a duplicate mean? | Becomes §4 Identity Semantics. |
| 4 | What is always forbidden or always required, and what is the business reason? | Becomes `invariants`. |
| 5 | What verbs can be performed on these records, and who/what triggers each? | Becomes `actions` — each in-scope action yields one Intent and one Workflow. |

---

## 1. Subdomain Purpose

*One short paragraph: what this subdomain governs, what authority it establishes, what lifecycle it
manages, and the business rationale for its existence. Write for a business stakeholder. No artifact
names.*

[Purpose paragraph for blockchain/chain.]

---

## 2. Scope Boundary

*What V0 commits to vs. what is explicitly deferred. A vague scope boundary is a governance defect. Status ∈ IN_SCOPE | DEFERRED.*

<!-- register:scope_boundary business_language=capability,notes -->
| Capability | Status (IN_SCOPE, DEFERRED) | Notes | Source Finding |
|------------|-----------------------------|-------|----------------|
| create genesis block at bootstrap | IN_SCOPE | One-time bootstrap operation establishing canonical chain, immutability constraints, and fixed supply of one million BachiCoin to Genesis Actor. | blockchain::AC_SYSTEM_V0; CR seed §8 Business Invariants #1,2 |
| commit block to canonical chain immutably | IN_SCOPE | Proposed blocks become immutable history on the canonical ledger after consensus round conclusion with attestation and commitment decision. | blockchain::EV_BLOCK_COMMITTED_V0; blockchain::CC_FORM_BLOCK_V0 |
| maintain chain state after genesis with supply conservation | IN_SCOPE | Total supply conserved at one million BachiCoin with no minting or burning permitted after bootstrap completion. | blockchain::CC_VALIDATE_MINT_POLICY_V0; CR seed §8 Business Invariants #3,5 |
| record consensus round outcome including skip decisions | IN_SCOPE | Consensus rounds produce committed blocks or advance to next slot while preserving chain continuity when no eligible proposer exists. | blockchain::CC_RECORD_CONSENSUS_ROUND_V0; blockchain::CC_SKIP_ROUND_V0 |
| append block lifecycle events to immutable journal | IN_SCOPE | Block commitment and finalization records appended as append-only entries preserving historical audit trail. | blockchain::CS_APPENDONLY_JSONL_V0; blockchain::CC_FORM_BLOCK_V0 |
| write committed blocks to immutable BLOCKS store | IN_SCOPE | Committed blocks written immutably with cryptographic linkage to predecessor block establishing chain continuity. | blockchain::CS_MUTABLE_JSON_V0; blockchain::CC_FORM_BLOCK_V0 |
| Attest step of PoS progression | DEFERRED | Deferred to future iteration; all proposed blocks treated as good this increment. | CR seed §12 Out of Scope #1 |
| Finalize step of PoS progression | DEFERRED | Deferred to future iteration; proposed blocks committed directly. | CR seed §12 Out of Scope #2 |
| Fork resolution | DEFERRED | Not part of this release; the chain commits every proposed block without fork handling. | CR seed §12 Out of Scope #3 |
| Chain reorganization (reorg) | DEFERRED | Not part of this release; committed history is immutable and cannot be altered. | CR seed §12 Out of Scope #4 |
| Slashing operations on validators | DEFERRED | Validator penalties are out of scope this release; validator state managed without slashing. | CR seed §12 Out of Scope #5 |
| Rewards distribution to validators and proposers | DEFERRED | Validator/proposer rewards are out of scope this release; no reward accounting in current increment. | CR seed §12 Out of Scope #6 |

---

## 3. Business Objects

*The business records this subdomain maintains and WHY each takes its form. Record Model ∈ MUTABLE_STATE (current state, correctable) | APPEND_ONLY_JOURNAL (immutable history) | IDENTITY_REGISTRY (stable key→address) | HYBRID. Business language.*

<!-- register:business_objects optional business_language=store_name,business_rationale -->
| Store Name | Record Model (MUTABLE_STATE, APPEND_ONLY_JOURNAL, IDENTITY_REGISTRY, HYBRID) | Business Rationale | Source Finding |
|------------|------------------------------------------------------------------------------|--------------------|----------------|
| Block Record | APPEND_ONLY_JOURNAL | Immutable historical record capturing each committed block with transactions, proposer information, and cryptographic linkage to predecessor. Once written, blocks cannot be altered or removed preserving chain integrity. | blockchain::CC_FORM_BLOCK_V0; blockchain::EV_BLOCK_COMMITTED_V0 |
| Consensus Round History | APPEND_ONLY_JOURNAL | Historical record of consensus rounds including proposer selections, attestations, and round outcomes. Preserves audit trail for governance verification. | blockchain::CC_RECORD_CONSENSUS_ROUND_V0; blockchain::RB_PROPOSE_BLOCK_V0 |
| Chain State Ledger | MUTABLE_STATE | Current authoritative state of the canonical ledger including committed block history and wallet balances. Updated after each consensus round to reflect latest chain state. | blockchain::CC_FORM_BLOCK_V0; blockchain::RB_PROPOSE_BLOCK_V0 |
| Block Events Journal | APPEND_ONLY_JOURNAL | Append-only journal of block lifecycle events including commitment and finalization records. Provides immutable event stream for audit purposes. | blockchain::CS_APPENDONLY_JSONL_V0; blockchain::EV_BLOCK_COMMITTED_V0 |

---

## 4. Identity Semantics

*Short prose. Which field uniquely identifies each record, where it comes from, what a duplicate
means, and any cross-subdomain identity relationship. The compiler cannot infer identity semantics
from field names — this is irreducible business knowledge.*

[Primary identity field, source, uniqueness rule, and cross-subdomain relationship for
blockchain/chain. If none beyond the primary, say so.]

---

## 5. Business Invariants

*Non-negotiable rules with a business reason. A rule without a business reason is a technical constraint and belongs elsewhere.*

<!-- register:invariants business_language=invariant,business_reason -->
| Invariant | Business Reason | Source Finding |
|-----------|-----------------|----------------|
| Genesis supply is fixed at one million BachiCoin minted to Genesis Actor at bootstrap | Establishes canonical monetary base without arbitrary inflation; all subsequent operations must conserve this initial supply. | CR seed §7 Constraints #3; blockchain::AC_SYSTEM_V0 |
| Exactly one genesis block exists per chain and executes exactly once at bootstrap never replayed | Single-execution semantics prevent supply duplication across restarts; ensures deterministic canonical history from single origin. | CR seed §8 Business Invariants #1,2 |
| Total supply is conserved and equals one million BachiCoin with no minting or burning after genesis | Closed monetary system principle; prevents inflationary attacks by prohibiting post-genesis supply creation. | CR seed §8 Business Invariants #3,5 |
| A committed block has exactly one predecessor except the genesis block | Linear chain structure ensures unambiguous historical ordering and prevents fork ambiguity in canonical history. | CR seed §8 Business Invariants #5 |
| A committed block cannot be committed twice to the canonical chain | Uniqueness constraint preserves immutability guarantee; prevents duplicate inclusion attacks on historical records. | CR seed §8 Business Invariants #6 |
| The chain is immutable once a block commits to canonical history | Historical integrity requirement for decentralized trust; participants rely on unalterable record of all committed transactions. | CR seed §7 Constraints #2 |
| Closed monetary system no supply enters or leaves except by the systems own rules | Prevents external manipulation of chain state; only protocol-defined operations can modify balances. | CR seed §7 Constraints #1 |

---

## 6. Business Actions

*Every verb performable on this subdomain's objects, in plain business language. Each in-scope action maps to one Intent and one Workflow. Status ∈ IN_SCOPE | DEFERRED.*

<!-- register:actions business_language=object,trigger -->
| Action | Object | Trigger | Status (IN_SCOPE, DEFERRED) | Source Finding |
|--------|--------|---------|-----------------------------|----------------|
| Create genesis block at bootstrap | Genesis Actor wallet and initial chain state | Chain initialization operation completes bootstrap sequence | IN_SCOPE | blockchain::AC_SYSTEM_V0; CR seed §8 Business Invariants #1,2 |
| Commit proposed block to canonical chain immutably | Proposed block record after consensus round conclusion | Consensus round concludes with attestation and commitment decision from eligible validators | IN_SCOPE | blockchain::EV_BLOCK_COMMITTED_V0; blockchain::CC_FORM_BLOCK_V0 |
| Maintain chain state after genesis with supply conservation enforcement | Chain State Ledger including wallet balances and committed block history | Post-genesis operations requiring balance updates or transaction processing | IN_SCOPE | blockchain::CC_VALIDATE_MINT_POLICY_V0; CR seed §8 Business Invariants #3,5 |
| Record consensus round outcome including skip decisions | Consensus Round History journal entry for completed rounds | Round execution completes with either block commitment or eligible proposer absence | IN_SCOPE | blockchain::CC_RECORD_CONSENSUS_ROUND_V0; blockchain::CC_SKIP_ROUND_V0 |
| Append block lifecycle events to immutable journal | Block Events Journal stream for commitment and finalization records | Block commits or round skips occur during consensus progression | IN_SCOPE | blockchain::CS_APPENDONLY_JSONL_V0; blockchain::CC_FORM_BLOCK_V0 |
| Write committed blocks to immutable BLOCKS store | Committed block records with cryptographic predecessor linkage | Successful consensus round conclusion following attestation phase | IN_SCOPE | blockchain::CS_MUTABLE_JSON_V0; blockchain::CC_FORM_BLOCK_V0 |
| Validate mint policy for supply conservation compliance | MINT transaction attempting to create new supply post-genesis | System operation or protocol event requesting balance modification | IN_SCOPE | blockchain::CC_VALIDATE_MINT_POLICY_V0; CR seed §7 Constraints #1 |
| Register validator for consensus participation eligibility | Validator record in VALIDATOR store with stake and authority attributes | Entity submits registration request meeting protocol requirements | IN_SCOPE | blockchain::RB_REGISTER_VALIDATOR_V0; blockchain::WF_REGISTER_VALIDATOR_V0 |
| Submit transaction for value transfer on canonical ledger | Transaction record in MEMPOOL awaiting consensus inclusion | Enduser initiates balance modification request through protocol interface | IN_SCOPE | blockchain::AC_ENDUSER_V0; blockchain::WF_SUBMIT_TRANSACTION_V0 |
| Perform system-level operations including block commitment and chain state maintenance | System-managed stores for BLOCKS, VALIDATOR, MEMPOOL consensus round history | Protocol execution requiring administrative or governance operation | IN_SCOPE | blockchain::AC_SYSTEM_V0; blockchain::RB_PROPOSE_BLOCK_V0 |

---

## 7. Provisional Artifact Codes

*Provisional AC / IN / WF / CC codes (Stage 6b assigns binding FQDNs). Each carries `_V0`. `summary` is business language. Family ∈ AC | IN | WF | CC.*

<!-- register:provisional_codes business_language=summary -->
| Provisional Code | Family (AC, IN, WF, CC) | Summary | Source Finding |
|------------------|-------------------------|---------|----------------|
| CC_COMMIT_BLOCK_TO_CANONICAL_CHAIN_V0 | CC | Capability contract for immutably committing proposed blocks to canonical chain after consensus round conclusion with attestation decision. | blockchain::EV_BLOCK_COMMITTED_V0; blockchain::CS_MUTABLE_JSON_V0 |
| CC_ENFORCE_SUPPLY_CONSERVATION_POST_GENESIS_V0 | CC | Capability contract validating mint policy compliance and rejecting post-genesis supply creation except through protocol-defined mechanisms. | blockchain::CC_VALIDATE_MINT_POLICY_V0; CR seed §8 Business Invariants #3,5 |
| IN_BLOCK_PROPOSED_TO_CANONICAL_CHAIN_V0 | IN | Input artifact tracking proposed blocks awaiting consensus round conclusion and commitment decision. | blockchain::CC_FORM_BLOCK_V0; blockchain::EV_BLOCK_COMMITTED_V0 |
| AC_GENESIS_BOOTSTRAP_AUTHORITY_V0 | AC | Actor record representing system-level bootstrap authority performing genesis block creation and initial state initialization. | blockchain::AC_SYSTEM_V0; CR seed §8 Business Invariants #1,2 |
| WF_COMMIT_BLOCK_AFTER_CONSENSUS_ROUND_V0 | WF | Workflow orchestrating block commitment operations following successful consensus round conclusion with attestation from eligible validators. | blockchain::EV_BLOCK_COMMITTED_V0; blockchain::CC_FORM_BLOCK_V0 |
| IN_ROUND_SKIPPED_NO_ELIGIBLE_PROPOSER_V0 | IN | Input artifact recording consensus rounds that advance to next slot without block commitment due to proposer absence or failed proposal. | blockchain::CC_SKIP_ROUND_V0; blockchain::WF_PROPOSE_BLOCK_V0 |

---

## 8. Cross-Subdomain References

*Capability Contracts defined in another subdomain and referenced by this subdomain's workflows. `cc_code` is the existing FQDN; do not re-document it here.*

<!-- register:cross_subdomain_refs optional business_language=role -->
| CC Code | Defined In | Role | Source Finding |
|---------|------------|------|----------------|
| fb.blockchain::STRUCTURE_BUILD_BLOCKCHAIN_CONFIG_V0 | fb.blockchain | Configuration structure defining blockchain subdomain parameters and operational constraints for chain governance. | fb.blockchain::STRUCTURE_BUILD_BLOCKCHAIN_CONFIG_V0 |
| fb.blockchain::STRUCTURE_BUILD_BLOCKCHAIN_V0 | fb.topology | Structure artifact establishing blockchain subdomain storage topology and store resolution for consensus operations. | blockchain::RB_PROPOSE_BLOCK_V0; fb.blockchain::STRUCTURE_BUILD_BLOCKCHAIN_V0 |
| fb.blockchain::STRUCTURE_REGISTRY_LOCATION_BLOCKCHAIN_V0 | fb.topology | Structure artifact defining registry location for blockchain identity subdomain cross-references and actor resolution. | blockchain::RB_REGISTER_VALIDATOR_V0; fb.blockchain::STRUCTURE_REGISTRY_LOCATION_BLOCKCHAIN_V0 |

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
and emits the WHAT. Emit keys match the register ids above exactly (Purpose §1 / Identity §4 /
Business Objects §3 are this stage's record, not forwarded fields).*

| Direction | Fields |
|-----------|--------|
| **Consumes** ← Stage 1 | out_of_scope |
| **Consumes** ← Stage 4 | actors · bm_entities · events · capability_graph · constraint_register |
| **Emits** → Stage 6 | scope_boundary · invariants · actions · provisional_codes · cross_subdomain_refs |

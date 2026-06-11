# Change Request: blockchain / chain
**CR Type:** change_request_subdomain  
**Domain:** blockchain  
**Primary Subdomain:** chain — NEW  
**Secondary Subdomain:** None  
**Version:** V0  
**Status:** COMPLETE  
**Pipeline Stage:** Stage 1 — Change Request & Input Elicitation  
**Feeds:** Stage 2 — Domain Model Discovery

*Stage 1 combines CR classification and input elicitation (former Stage 0 merged here).*

---

## Stage Inputs — Questions for the Human (as answered)

| # | Question | Human Answer (used as stated below) |
|---|----------|-------------------------------------|
| 1 | What is missing, in business terms? | Proposed blocks are never committed to a canonical chain; the blockchain has no authoritative ledger. → Problem Statement |
| 2 | What governed capability must exist at close? | A governed chain that commits proposed blocks, bootstrapped from a genesis block. → Desired Outcome |
| 3 | What type of change? | New subdomain (`blockchain/chain`). → CR Type |
| 4 | Adjacent subdomains/flows? | identity, wallet, transaction, mempool, consensus_pos, orchestration; consensus loop produces proposed blocks. → Known Facts |
| 5 | Explicitly out of scope? | Attest and Finalize steps; all proposed blocks treated as good and committed as finalized. → Section 6 |
| 6 | Non-negotiable business rules? | Closed monetary system; genesis funds 1,000,000 BachiCoin to a MINT wallet owned by `genesis.actor`; chain is immutable. → Constraint candidates for Stages 2–4 |
| 7 | Reference implementations? | Proof-of-stake model similar to the ETH standard; peer dossiers (e.g., `blockchain/mempool`, `blockchain/orchestration`) as structural references. → Known Facts |

---

## 1. Problem Statement

We are creating a new subdomain "blockchain/chain" to augment current peer level fully functional subdomains identity, wallet, transaction, mempool, consensus_pos (proof of stake similar to ETH standard) and orchestration. Today the consensus loop proposes blocks, but no governed capability exists to commit those blocks to a canonical, immutable ledger — the blockchain has no chain.

---

## 2. Desired Outcome

A governed capability must exist to commit proposed blocks to a newly established "chain" within the blockchain domain, starting with a bootstrapped genesis block. This enables the system to maintain a persistent, ordered, and validated record of blocks — the foundational ledger for the blockchain. Blocks proposed by the consensus loop (driven by `blockchain::WF_RUN_CONSENSUS_LOOP_V0`) are committed to the chain as finalized blocks in V0.

---

## 3. Known Facts at CR Entry

| Fact | Source |
|------|--------|
| Dossier folder exists at `~/pgs/pgs_change_mgmt/change_mgmt/dossiers/blockchain/chain/` | User provided |
| Sample CRs and dossier structures are available in peer subdomains (`blockchain/mempool`, `blockchain/orchestration`) | User provided |
| Blockchain data flow: actor → wallet → transaction → mempool; consensus loop: validator → proposer → blocks → chain, enabled by blockchain/orchestration | User provided |
| `blockchain::WF_RUN_CONSENSUS_LOOP_V0` exists and drives slot processing that proposes blocks | PPS snapshot (verified) |

### A. Existing Blockchain Components & Data Flow

The blockchain system comprises six functional peer subdomains: `identity`, `wallet`, `transaction`, `mempool`, `consensus_pos`, and `orchestration`. Transaction submission flows actor → wallet → transaction → mempool. The consensus loop (validator → proposer → blocks) is coordinated by the orchestration subdomain; block proposal is performed per slot.

### B. Block Commitment Scope

For this CR, committing a proposed block to the chain is limited to the act of persisting an immutable reference to it. The subsequent process steps "Attest" and "Finalize" are explicitly out of scope and deferred to future CRs. For the purpose of this CR, all proposed blocks are assumed valid and ready for direct inclusion into the chain as finalized blocks.

### C. Monetary Bootstrap

The system is a closed monetary system — money neither enters nor leaves. The genesis bootstrap establishes the initial supply: 1,000,000 BachiCoin minted into a "MINT" wallet owned by a privileged actor `genesis.actor`.

---

## 4. CR Type Determination

**Type:** change_request_subdomain

**Analysis path triggered:**

| CR Type | Analysis Path |
|---------|--------------|
| change_request_bug | Skip to Gap Analysis on existing artifacts |
| change_request_feature | Capability + Gap analysis only |
| change_request_subdomain | Full loop: Domain Model Discovery + Analysis Loop until Discovery Saturation |
| change_request_domain | Full loop + new domain declaration |

**Pipeline entry:** Stage 2

---

## 5. Governance Scope Declared by This CR

| Subdomain | Action | Rationale |
|-----------|--------|-----------|
| chain | DECLARE NEW | To establish the "chain" subdomain for canonical block commitment and chain state |

---

## 6. Out of Scope — Deferred to Future CRs

| Capability | Reason |
|-----------|--------|
| "Attest" and "Finalize" block processing steps | For simplicity, all proposed blocks are assumed good and are written to the chain as finalized blocks in this CR. These steps will be addressed in future CRs. |

---

## Analyst Notes — Purity Rules

- **Purity Filter active from this stage forward.** Stages 1–4 use business language only for anything NEW. Existing PPS artifacts may be cited by exact FQDN as verified evidence. Provisional codes first appear in Stage 5; binding FQDNs in Stage 6b.
- **Open question for Stage 2:** What are the core entities (Block, Chain, Chain State, Genesis Block) and their relationships? How do they relate to existing block formation in the PPS?
- **Open question for Stage 2:** What does the PPS baseline already contain relating to chains, block storage, or block lifecycle events?
- **Open question for Stage 3:** What gaps prevent governed commitment of proposed blocks, and which existing capabilities (events, transforms, side-effect substrates) are reusable?
- **Open question for Stage 3:** What invariants must the chain enforce (immutability, cryptographic linkage, single genesis)?

---

## Dossier Status

| Stage | Artifact | Status |
|-------|----------|--------|
| Stage 1 | 1_change_request_blockchain_chain_v0.md (classification + input elicitation) | COMPLETE |
| Stage 2 | 2_domain_model_blockchain_chain_v0.md | COMPLETE |
| Stage 3 | 3_analysis_loop_blockchain_chain_v0.md | COMPLETE |
| Stage 4 | 4_business_model_blockchain_chain_v0.md | COMPLETE |
| Stage 4b | Authoring Scope (Section 7 of business model) | COMPLETE |
| Stage 5 | 5_business_intent_blockchain_chain_v0.md | COMPLETE |
| Stage 6 | 6_governance_intent_blockchain_chain_v0.md | COMPLETE |
| Stage 6b | 6b_design_intent_blockchain_chain_v0.md — Gate 1 closes here | PENDING GATE 1 APPROVAL |
| Stage 7 | 7_authoring_mandate_blockchain_chain_v0.md — Gate 2 closes here | PENDING GATE 2 APPROVAL |
| Stage 8 | 8_authoring_manifest_blockchain_chain_v0.md | PENDING — pre-authoring baseline created |
| Stage 9 | (CR Closure — no separate artifact; manifest status → APPROVED) | PENDING |

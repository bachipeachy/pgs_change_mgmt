# Change Request: blockchain / consensus_pos
**CR Type:** change_request_subdomain  
**Domain:** blockchain  
**Primary Subdomain:** consensus_pos — EXISTING (extended by this CR)  
**Secondary Subdomain:** block — NEW (declared by this CR)  
**Version:** V0  
**Status:** APPROVED — dossier complete through Stage 7 (Authoring Mandate)  
**Pipeline Stage:** Stage 0 — Change Request Classification  

---

## 1. Problem Statement

The blockchain domain lacks a governed Proof-of-Stake consensus mechanism. Validator identity, enrollment, proposer selection, and block proposal are not governed protocol artifacts — they exist only as unverified external code. The result is:

- No governed validator participation registry
- No governed proposer selection (deterministic from active validator set)
- No governed block proposal workflow
- No governed consensus round record
- Existing validator registration artifact (`WF_REGISTER_VALIDATOR_V0`) was authored through a flawed pipeline that skipped the Governance Intent gate — it must be replaced

---

## 2. Desired Outcome

A governed PoS consensus round: from active validator set → proposer selection → block formation → consensus round recorded. The following governed capabilities must exist by end of this CR:

- Validator enrollment and active participation pool management
- Deterministic proposer selection from the active validator pool
- Block proposal workflow (consensus orchestrates; block subdomain executes)
- Consensus round record (proposed and skipped outcomes)
- Round skip event

---

## 3. Known Facts at CR Entry

| Fact | Source |
|------|--------|
| `blockchain::identity` subdomain is governed and deployed | PPS snapshot |
| `blockchain::transaction` subdomain is governed and deployed | PPS snapshot |
| `blockchain::CC_CHECK_ACTOR_EXISTS_V0` exists and is reusable | PPS snapshot |
| `blockchain::WF_REGISTER_VALIDATOR_V0` exists but was authored through flawed pipeline (GI gate skipped) | PPS snapshot + governance audit |
| BachiCoin local reference implementation available at `/Users/bp/BachiCoin/` | Local environment |
| PoS mechanism targets Ethereum-compatible slot/epoch/committee model | Domain knowledge |

---

## 4. CR Type Determination

**Type:** `change_request_subdomain`

**Analysis path triggered:** Full loop required — Domain Model Discovery + Analysis Loop until Discovery Saturation. A subdomain CR extending an existing namespace and declaring a new one requires the complete pipeline.

**Pipeline entry:** Stage 1 — Input Elicitation

---

## 5. Governance Scope Declared by This CR

| Subdomain | Action | Rationale |
|-----------|--------|-----------|
| `blockchain::consensus_pos` | EXTEND — existing namespace | Adds validator enrollment, proposer selection, block proposal workflow, round recording |
| `blockchain::block` | DECLARE NEW — new governed namespace | Block is a cross-consensus entity (PoS and future PoW both depend on it); consensus must not own what transcends it |
| `blockchain::transaction` | DEPENDENCY GAP — new capability required | Pending transaction query owned by transaction subdomain; consensus is its consumer |

---

## 6. Out of Scope — Deferred to Future CRs

| Capability | Reason |
|-----------|--------|
| Block attestation | Attestor role not in scope |
| Block finalization and chain population | Finalizer role not in scope |
| Stake enforcement (slashing) | Stake is declaration only this CR |
| Rewards and penalties | Future CR |
| Epoch and Checkpoint management | Beyond Consensus Round (Slot) scope |
| Multi-node coordination | Future CR |
| `blockchain::chain` subdomain | Future CR |

---

## Dossier Status

| Stage | Artifact | Status |
|-------|----------|--------|
| Stage 0 | 1_change_request_consensus_pos_v0.md | COMPLETE |
| Stage 4 | 4_business_model_consensus_pos_v0.md | COMPLETE |
| Stage 5 | 5_business_intent_consensus_pos_v0.md | COMPLETE — APPROVED |
| Stage 6 | 6_governance_intent_consensus_pos_v0.md | COMPLETE — APPROVED |
| Stage 6b | 6b_design_intent_consensus_pos_v0.md | COMPLETE — APPROVED |
| Stage 7 | 7_authoring_mandate_consensus_pos_v0.md | COMPLETE — APPROVED |
| Stage 8 | 8_authoring_manifest_consensus_pos_v0.md | PENDING — produced after artifact authoring |

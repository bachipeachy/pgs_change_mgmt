# Change Request: blockchain / consensus_propose
**CR Type:** change_request_feature  
**Domain:** blockchain  
**Primary Subdomain:** consensus_pos — EXISTING  
**Additional Subdomains:** block — EXISTING, transaction — EXISTING, wallet — EXISTING, validator — EXISTING (WIP internal module)  
**Version:** V0  
**Status:** DRAFT  
**Pipeline Stage:** Stage 0 — Change Request Classification  

---

## 1. Problem Statement

The blockchain domain has a governed block proposal path and eight governed typed transaction submission paths. All artifacts compile and build successfully but have never been invoked or tested. Entities carry no canonical data — balances are seeded at zero, transactions are unexercised, and no block has ever been proposed with realistic field values.

---

## 2. Desired Outcome

End-to-end invocation of all eight typed transaction workflows against canonical domain data, culminating in a persisted block in PROPOSED state with realistic field values — demonstrable and verifiable. Attestation, finalization, and chain commitment are deferred to sister CRs.

---

## 3. CR Type Determination

**Type:** `change_request_feature`

**Analysis path:** Full pipeline — Domain Model Discovery through Authoring Mandate.

**Pipeline entry:** Stage 1 — Input Elicitation

---

## 4. Governance Scope

| Subdomain | Action |
|-----------|--------|
| `blockchain::consensus_pos` | EXTEND |
| `blockchain::block` | EXTEND |
| `blockchain::transaction` | EXTEND |
| `blockchain::wallet` | EXTEND |
| `blockchain::validator` | EXTEND (WIP internal module) |

---

## 5. Sister CRs (planned, not yet opened)

| CR | Scope |
|----|-------|
| `consensus_attest` | Govern block attestation; advance block from PROPOSED to ATTESTED |
| `consensus_finalize` | Govern block finalization, chain commitment, and wallet balance reconciliation |

---

## Dossier Status

| Stage | Artifact | Status |
|-------|----------|--------|
| Stage 0 | 1_change_request_consensus_propose_v0.md | COMPLETE |
| Stage 1 | 1_input_elicitation_consensus_propose_v0.md | PENDING |
| Stage 2 | 2_domain_model_consensus_propose_v0.md | PENDING |
| Stage 3 | 3_analysis_loop_consensus_propose_v0.md | PENDING |
| Stage 4 | 4_business_model_consensus_propose_v0.md | PENDING |
| Stage 5 | 5_business_intent_consensus_propose_v0.md | PENDING |
| Stage 6 | 6_governance_intent_consensus_propose_v0.md | PENDING |
| Stage 6b | 6b_design_intent_consensus_propose_v0.md | PENDING |
| Stage 7 | 7_authoring_mandate_consensus_propose_v0.md | PENDING |
| Stage 8 | 8_authoring_manifest_consensus_propose_v0.md | PENDING |

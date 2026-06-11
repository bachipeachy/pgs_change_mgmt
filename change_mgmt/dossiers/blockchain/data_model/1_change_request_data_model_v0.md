# Change Request: blockchain / data_model
**CR Type:** change_request_feature  
**Domain:** blockchain  
**Primary Subdomain:** data_model — NEW (cross-cutting governance scope; not a runtime subdomain)  
**Secondary Subdomains:** identity, wallet, transaction, validator, block — EXISTING (all enriched)  
**Version:** V0  
**Status:** CLOSED  
**Pipeline Stage:** Stage 9 — CR Closure (COMPLETE)  

---

## 1. Problem Statement

The blockchain domain's five runtime subdomains (identity, wallet, transaction, validator, block) carry minimal payload fields — just enough to exercise the governed execution topology. They have no real account balances, no lifecycle status enumerations, no gas model, no validator staking fields, no block finality state. As a result the system cannot demonstrate meaningful blockchain behavior: a wallet has no balance to transfer, a transaction has no fee model, a validator has no activation lifecycle.

The protocol governs real execution paths but operates on hollow data. The demo is structurally correct but semantically empty.

---

## 2. Desired Outcome

A governed canonical data model for the blockchain domain exists — defined once, shared across all five subdomains — such that:

- Every subdomain's payload carries the fields a real blockchain operation requires (account balance, transaction type and fee model, validator lifecycle, block finality state)
- New events are declared for field-level state transitions that matter to the system (balance change, validator status change, block finalization)
- The demo workflow can show meaningful end-to-end behavior: register actor with identity, create wallet with opening balance, submit transfer transaction with gas, observe validator activation, see block finalized
- All field definitions, enumerated types, and status lifecycles are governed artifacts — not hardcoded in seeds or test payloads

---

## 3. Known Facts at CR Entry

| Fact | Source |
|------|--------|
| Five existing subdomains: identity, wallet, transaction, validator, block | PPS snapshot |
| BachiCoin (~/BachiCoin) implements ETH-aligned data model with rich schemas | BachiCoin lib_*_config.py |
| identity subdomain currently stores: actor_id, name, email, kyc_verified, status | PPS snapshot — identity artifacts |
| wallet subdomain currently stores: wallet_id, user_id, name, balance (0.0), network | PPS snapshot — wallet artifacts |
| transaction subdomain currently stores: tx_id, from_address, to_address, amount, status | PPS snapshot — transaction artifacts |
| validator subdomain currently stores: validator_id, pubkey, status | PPS snapshot — validator artifacts |
| block subdomain currently stores: block_hash, parent_hash, height, timestamp | PPS snapshot — block artifacts |
| BachiCoin user schema: 40+ fields including user_type (10 values), lifecycle status (7 values), KYC, PoS validator fields | BachiCoin/lib_user/user_config.py |
| BachiCoin wallet schema: ETH account state (balance, nonce, storage_root, code_hash), 9 wallet types, HD addresses, 3 currencies | BachiCoin/lib_wallet/wallet_config.py |
| BachiCoin transaction schema: EIP-1559 Type 2, 11 tx types, full gas model, signing/execution/block-inclusion lifecycle | BachiCoin/lib_transaction/tx_config.py |
| BachiCoin validator schema: ETH2 lifecycle (9 statuses), BLS12-381 pubkey, 32 ETH effective balance, epoch-based duties | BachiCoin/lib_validator/validator_config.py |
| BachiCoin block schema: ETH2 + Bitcoin hybrid, slot/epoch/proposer, Verkle/Merkle roots, EIP-1559 base fee, 5 block statuses | BachiCoin/lib_blockchain/blockchain_config.py |
| Structural tension: BachiCoin puts validator stake fields on the user record; PGS separates identity and validator subdomains | Design decision required |

---

## 4. CR Type Determination

**Type:** change_request_feature

**Rationale:** This CR enriches existing subdomains — it does not declare a new runtime subdomain. The `data_model` label is the dossier scope (cross-cutting enrichment governance), not a new runtime subdomain. All five existing subdomains gain richer payload fields, enumerated types, and new events. No new workflow topology is introduced.

**Analysis path triggered:**

| CR Type | Analysis Path |
|---------|--------------|
| change_request_feature | Capability + Gap analysis only |

**Pipeline entry:** Stage 1

---

## 5. Governance Scope Declared by This CR

| Subdomain | Action | Rationale |
|-----------|--------|-----------|
| identity | EXTEND | Add user_type, lifecycle status, KYC fields, contact, PoS stake reference |
| wallet | EXTEND | Add full ETH account state (balance/nonce), wallet_type, security_type, currency, HD addresses |
| transaction | EXTEND | Add tx_type enum (11 types), EIP-1559 gas model, signing/execution views, priority |
| validator | EXTEND | Add ETH2 lifecycle (9 statuses), BLS pubkey, effective balance, epoch tracking |
| block | EXTEND | Add ETH2 slot/epoch/proposer, Verkle/Merkle roots, EIP-1559 base fee, block status lifecycle |

**Key design decision deferred to Stage 2:**
Validator stake fields (stake_amount, delegation_fee, validator_address) — do they live in identity or validator? BachiCoin places them on the user; PGS separation of concerns argues for validator subdomain.

---

## 6. Out of Scope — Deferred to Future CRs

| Capability | Reason |
|-----------|--------|
| Bitcoin hybrid PoW fields (difficulty, nonce, bits, chainwork) | Complex consensus extension; not needed for demo |
| Smart contract deployment and execution (CONTRACT_DEPLOY, CONTRACT_CALL tx types) | Requires EVM substrate; out of scope for V0 |
| Multi-currency support (BTC, ETH alongside BACHI) | Cross-currency accounting complexity; BACHI only in this CR |
| HD wallet multi-address derivation paths | Crypto key management infrastructure not yet governed |
| Mempool and transaction lifecycle (pending → mined → confirmed) | Requires mempool subdomain; separate CR |
| Federation-level validator committee assignments | Cross-node consensus; out of scope for single-node demo |
| Staking economics (rewards calculation, slash penalties) | Requires epoch processing infrastructure |

---

## Dossier Status

| Stage | Artifact | Status |
|-------|----------|--------|
| Stage 0 | 1_change_request_data_model_v0.md | COMPLETE |
| Stage 1 | 1_input_elicitation_data_model_v0.md | COMPLETE |
| Stage 2 | 2_domain_model_data_model_v0.md | COMPLETE |
| Stage 3 | 3_analysis_loop_data_model_v0.md | COMPLETE |
| Stage 4 | 4_business_model_data_model_v0.md | COMPLETE |
| Stage 5 | 5_business_intent_data_model_v0.md | COMPLETE |
| Stage 6 | 6_governance_intent_data_model_v0.md | COMPLETE |
| Stage 6b | 6b_design_intent_data_model_v0.md | COMPLETE |
| Stage 7 | 7_authoring_mandate_data_model_v0.md | COMPLETE |
| Stage 8 | 8_authoring_manifest_data_model_v0.md | COMPLETE — APPROVED; 77/77 conformance PASS, snapshot VALID |
| Stage 9 | (CR Closure — no separate artifact; manifest status → APPROVED) | COMPLETE |

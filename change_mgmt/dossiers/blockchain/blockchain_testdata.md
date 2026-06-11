# Blockchain Test Data: BACHI TESTNET
**Domain:** blockchain  
**Purpose:** Canonical test population for regression testing across consensus_propose, consensus_attest, consensus_finalize, and successor CRs.  
**Last updated:** consensus_propose CR — Stage 2

---

## Actors

| Name | Email | user_type | Notes |
|------|-------|-----------|-------|
| Genesis Actor | genesis@bachi.internal | GENESIS | Seeded — owns MINT, BURN, POOL system wallets; actor_id: ACT_7a77a0461083f938 |
| Bachi Eight | bachi8@yahoo.com | INDIVIDUAL | Existing runtime actor — actor_id: AC_dc6e2a7ae93b8bae; verified |
| Gomer Adams | gomer.adams@bachi.testnet | INDIVIDUAL | Test actor — to be registered |
| Liam Adams | liam.adams@bachi.testnet | INDIVIDUAL | Test actor — to be registered |
| Isha Adams | isha.adams@bachi.testnet | INDIVIDUAL | Test actor — to be registered |
| Sophie Cyber | sophie.cyber@bachi.testnet | INDIVIDUAL | Test actor — to be registered |
| Bachi One | bachi.one@bachi.testnet | VALIDATOR | Test validator actor — to be registered |
| Bachi Two | bachi.two@bachi.testnet | VALIDATOR | Test validator actor — to be registered |
| Bachi Three | bachi.three@bachi.testnet | VALIDATOR | Test validator actor — to be registered |
| Bachi Four | bachi.four@bachi.testnet | VALIDATOR | Test validator actor — to be registered |

---

## Wallets

| Owner | wallet_type | Opening Balance | Notes |
|-------|-------------|-----------------|-------|
| Genesis Actor | MINT | 1,000,000 BACHI | Seeded |
| Genesis Actor | BURN | 0 BACHI | Seeded |
| Genesis Actor | POOL | 0 BACHI | Seeded |
| Bachi Eight | DEFAULT | 0 BACHI | Existing runtime wallet |
| Gomer Adams | PRIVATE | 0 BACHI | Created via wallet creation path |
| Gomer Adams | BUSINESS | 0 BACHI | Created via wallet creation path |
| Liam Adams | PRIVATE | 0 BACHI | Created via wallet creation path |
| Liam Adams | BUSINESS | 0 BACHI | Created via wallet creation path |
| Isha Adams | PRIVATE | 0 BACHI | Created via wallet creation path |
| Isha Adams | BUSINESS | 0 BACHI | Created via wallet creation path |
| Sophie Cyber | PRIVATE | 0 BACHI | Created via wallet creation path |
| Sophie Cyber | BUSINESS | 0 BACHI | Created via wallet creation path |

---

## Validators

| Name | Linked Actor | enrollment_status | effective_balance | Notes |
|------|-------------|-------------------|-------------------|-------|
| Bachi One | bachi.one@bachi.testnet | ACTIVE | 32,000 BACHI | To be registered |
| Bachi Two | bachi.two@bachi.testnet | ACTIVE | 32,000 BACHI | To be registered |
| Bachi Three | bachi.three@bachi.testnet | ACTIVE | 32,000 BACHI | To be registered |
| Bachi Four | bachi.four@bachi.testnet | ACTIVE | 32,000 BACHI | To be registered |

---

## Transaction Schedule

Consensus loop: 30-second slot cycle. Transactions submitted at 20-second intervals before slot fires.

| Slot | tx_type | Amount | from | to | Notes |
|------|---------|--------|------|----|-------|
| 1 | MINT | 6,000 | — | Gomer Adams / PRIVATE | System-sourced; no from_address |
| 2 | MINT | 4,000 | — | Gomer Adams / BUSINESS | System-sourced; no from_address |
| 3 | MINT | 6,000 | — | Liam Adams / PRIVATE | System-sourced; no from_address |
| 4 | MINT | 4,000 | — | Liam Adams / BUSINESS | System-sourced; no from_address |
| 5 | MINT | 6,000 | — | Isha Adams / PRIVATE | System-sourced; no from_address |
| 6 | MINT | 4,000 | — | Isha Adams / BUSINESS | System-sourced; no from_address |
| 7 | MINT | 6,000 | — | Sophie Cyber / PRIVATE | System-sourced; no from_address |
| 8 | MINT | 4,000 | — | Sophie Cyber / BUSINESS | System-sourced; no from_address |
| 9 | POOL | 10,000 | Genesis / MINT | Genesis / POOL | System tx; moves mint funds to pool |
| 10 | REWARD | 1,000 | — | Gomer Adams / PRIVATE | System-sourced; no from_address |
| 11 | SLASH | 1,000 | Liam Adams / PRIVATE | — | Penalty; no to_address; routes to BURN |
| 12 | TRANSFER | 1,000 | Gomer Adams / PRIVATE | Gomer Adams / BUSINESS | Self-transfer |
| 13 | TRANSFER | 1,000 | Gomer Adams / BUSINESS | Liam Adams / BUSINESS | P2P |
| 14 | BURN | 100 | Gomer Adams / PRIVATE | — | Supply removal; no to_address |
| 15 | STAKE | 900 | Gomer Adams / PRIVATE | Genesis / POOL | Lock funds for validator activation |
| 16 | TRANSFER | 1,000 | Gomer Adams / PRIVATE | Liam Adams / PRIVATE | P2P |
| 17 | TRANSFER | 1,000 | Gomer Adams / BUSINESS | Liam Adams / BUSINESS | P2P |
| 18 | UNSTAKE | 500 | Genesis / POOL | Gomer Adams / PRIVATE | Release staked funds |
| 19 | TRANSFER | 1,000 | Gomer Adams / BUSINESS | Isha Adams / PRIVATE | P2P |
| 20 | TRANSFER | 1,000 | Liam Adams / PRIVATE | Liam Adams / BUSINESS | Self-transfer |
| 21 | TRANSFER | 1,000 | Liam Adams / BUSINESS | Isha Adams / BUSINESS | P2P |
| 22 | BURN | 200 | Liam Adams / PRIVATE | — | Supply removal; no to_address |
| 23 | STAKE | 800 | Liam Adams / PRIVATE | Genesis / POOL | Lock funds for validator activation |
| 24 | TRANSFER | 1,000 | Liam Adams / BUSINESS | Isha Adams / PRIVATE | P2P |

**tx_type coverage:** MINT ✓ POOL ✓ REWARD ✓ SLASH ✓ TRANSFER ✓ BURN ✓ STAKE ✓ UNSTAKE ✓

---

## PGS Adaptation Notes

| Original | PGS |
|----------|-----|
| `user_type: "individual"` | `user_type: "INDIVIDUAL"` |
| `user_type: "validator"` | `user_type: "VALIDATOR"` |
| wallet `"private"` | wallet_type `PRIVATE` |
| wallet `"business"` | wallet_type `BUSINESS` |
| wallet `"mint"` | wallet_type `MINT` (system — Genesis Actor) |
| wallet `"pool"` | wallet_type `POOL` (system — Genesis Actor) |
| `"Ledger System"` | Genesis Actor (GENESIS role; ACT_7a77a0461083f938) |
| Slots 1–8: `transfer` from mint | `MINT` tx — system-sourced; no `from_address` |
| Slot 9: `transfer` mint→pool | `POOL` tx — system tx between system wallets |

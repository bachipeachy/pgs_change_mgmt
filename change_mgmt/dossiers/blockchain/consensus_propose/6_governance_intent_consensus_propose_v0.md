# Stage 6 — Governance Intent: blockchain / consensus_propose
**Domain:** blockchain
**Subdomains:** consensus_pos, transaction, validator
**Version:** V0
**Status:** DRAFT
**Pipeline Stage:** Stage 6 — Governance Intent (WHERE)
**Produced by:** v0.5.0 SDLC authoring pipeline
**Purity:** WHERE only — artifact family mapping, provisional artifact codes, and store declarations excluded

---

## 1. Domain Placement

| Field | Value |
|-------|-------|
| Domain | `blockchain` |
| Subdomain | `consensus_pos` — EXISTING; new slot loop governance added by this CR |
| Subdomain | `transaction` — EXISTING; CS wiring correction by this CR |
| Subdomain | `validator` — EXISTING; registration schema alignment by this CR |
| FQDN namespace | `blockchain` |

This CR does not declare any new subdomain. All three subdomains are existing governed namespaces within the `blockchain` domain. The primary work is in `consensus_pos` — new finite slot loop governance. The two extensions are in-scope corrections that were discovered as blockers during Stage 3 analysis: the `transaction` subdomain is missing CS wiring on five SYSTEM authority runtime bindings; the `validator` subdomain has a schema mismatch between registration and eligibility query.

All three corrections are required before the end-to-end scenario can execute. They are governed together in this CR because they were discovered as coupled runtime blockers, not as independent change initiatives.

---

## 2. Authority and Governance

| Concern | Governing Constitution |
|---------|----------------------|
| Actor authority | `fb.constitution::CONSTITUTION_GOVERNANCE_V0` |
| Execution topology (WF, IN, CC) | `fb.topology::CONSTITUTION_WORKFLOW_V0`, `fb.topology::CONSTITUTION_INTENT_V0`, `fb.topology::CONSTITUTION_CAPABILITY_CONTRACT_V0` |
| Storage topology | `fb.constitution::CONSTITUTION_STRUCTURE_V0` |
| Domain invariants | `blockchain::INVARIANT_CT_SURFACE_CLOSED_BLOCKCHAIN_V0` |

The consensus loop executes under SYSTEM authority class. No new authority class is required. The Consensus Loop Driver is a SYSTEM actor — its identity is carried in the input payload as triggered_by. ENDUSER authority (TRANSFER, STAKE, UNSTAKE) and SYSTEM authority (MINT, BURN, POOL, REWARD, SLASH) classes are already declared; this CR exercises both without modification to their authority contracts.

---

## 3. Subdomain Boundary

### Owned by consensus_pos (primary — this CR)

| Capability | Ownership Decision |
|------------|-------------------|
| Governed finite consensus slot loop | OWNED — new capability |
| Slot loop admission (input contract) | OWNED — new capability |
| Per-slot: block proposal invocation | OWNED — existing capability; slot + epoch wiring fix |
| Post-run result verification | OWNED — new capability |
| Eligible validator query (field alignment fix) | OWNED — existing capability corrected |
| Proposer selection from eligible validator set | OWNED — existing capability; no change |
| Consensus round recording (proposed + skipped) | OWNED — existing capability; no change |

### Owned by transaction (extended — this CR)

| Capability | Ownership Decision |
|------------|-------------------|
| SYSTEM WF runtime CS wiring (MINT, BURN, POOL, REWARD, SLASH) | OWNED — `blockchain::transaction` — runtime binding correction; no new capability |

The five SYSTEM authority transaction workflows each invoke a mempool persistence capability that performs tx deduplication via the registry. The runtime bindings for these five workflows are missing the registry CS binding. The fix belongs to the `transaction` subdomain because the runtime bindings are `transaction`-owned artifacts — they govern how transaction submission capabilities are wired, not how the consensus loop operates.

### Owned by validator (extended — this CR)

| Capability | Ownership Decision |
|------------|-------------------|
| Validator registration schema alignment (8-field canonical record) | OWNED — `blockchain::validator` — admission schema correction |

The validator registration intent admits the payload that becomes the validator record. The current schema admits 4 fields; the write capability requires 8; the eligibility query reads 2 fields that are not present in the admitted payload. The schema alignment fix belongs to the `validator` subdomain because the registration admission contract is a validator-owned artifact.

### Satisfied by existing subdomains — no ownership transfer

| Capability | Owned By | PPS Status |
|------------|----------|-----------|
| Block formation and persistence | `blockchain::block` | SATISFIED — declared in consensus_pos CR |
| Block proposed event | `blockchain::block` | SATISFIED — declared in consensus_pos CR |
| Pending transaction query | `blockchain::transaction` | SATISFIED — existing CC |
| Actor existence check | `blockchain::identity` | SATISFIED — existing CC reused |
| Eight typed transaction WFs (TRANSFER, STAKE, UNSTAKE, MINT, BURN, POOL, REWARD, SLASH) | `blockchain::transaction` | SATISFIED — existing WFs; invoked by slot loop CC |

### Deferred to future CRs — not owned this CR

| Capability | Reason |
|------------|--------|
| Block attestation | consensus_attest CR |
| Block finalization + chain commitment | consensus_finalize CR |
| Balance reconciliation after block | consensus_finalize CR |
| Live unbounded consensus loop (daemon mode) | No governed artifact needed — daemon calls single-slot WF directly; architecturally distinct from bounded loop |
| Epoch-triggered validator status transitions | Future CR |

---

## 4. Composition — Extension Pattern

| Composition Decision | Detail |
|---------------------|--------|
| Domain | Extend existing `blockchain` domain — no new domain created |
| Subdomain (primary) | Extend existing `consensus_pos` namespace — new slot loop governance added |
| Subdomain (transaction) | Extend existing `blockchain::transaction` namespace — CS wiring correction only |
| Subdomain (validator) | Extend existing `blockchain::validator` namespace — schema alignment only |
| New subdomains | None — this CR declares no new governed subdomains |
| Actor types | Reuse existing — no new actor type required |
| Execution substrate | Reuse existing capability substrate |
| block dependency | Cross-subdomain capability call — block formation; `blockchain::block` owned (declared in consensus_pos CR) |
| transaction dependency | Cross-subdomain read + invocation — pending tx query + typed WF invocations; `blockchain::transaction` owned |
| identity dependency | Cross-subdomain read — actor existence check; `blockchain::identity` owned |
| Storage topology | No new stores required — all required stores declared in prior CRs; see Section 5 |

Cross-subdomain writes are forbidden. The consensus loop CC that drives slot execution invokes governed WFs belonging to other subdomains — it does not write directly to transaction, block, validator, or identity stores. All store writes occur through the owned CCs of their respective subdomains.

---

## 5. Storage Governance Requirements

All stores required by this CR were declared in prior CRs. No new stores are required. This section confirms the governance ownership of each store accessed by this CR.

**consensus_pos subdomain storage:**
- Consensus round records (round outcomes: proposed + skipped) — declared in consensus_pos CR; written by this CR
- Validator registry (eligibility read) — declared in consensus_pos CR; read-only from slot loop

**blockchain::block subdomain storage:**
- Proposed blocks — declared in consensus_pos CR; written by block-owned capabilities invoked via WF_PROPOSE_BLOCK_V0

**blockchain::transaction subdomain storage:**
- Mempool (PENDING transactions) — declared in transaction CR; written by typed transaction WFs invoked within the slot loop CC; read by pending transaction query

**blockchain::validator subdomain storage:**
- Validator registry — declared in validator CR; read-only from consensus_pos eligibility query; written by validator registration WF (schema alignment fix in this CR does not change store structure)

---

## 6. Cross-Subdomain Dependency Declaration

| Dependency | Direction | Existing PPS Artifact | Status |
|------------|-----------|----------------------|--------|
| Block formation | consensus_pos → block | `blockchain::CC_FORM_BLOCK_V0` | SATISFIED — exists; slot + epoch wiring fix required (IN + WF update) |
| Pending transaction query | consensus_pos → transaction | `blockchain::CC_QUERY_PENDING_TRANSACTIONS_V0` | SATISFIED — reuse |
| Actor existence check | consensus_pos → identity | `blockchain::CC_CHECK_ACTOR_EXISTS_V0` | SATISFIED — reuse |
| Typed tx WF invocations (8) | slot_loop_CC → transaction | All 8 typed WFs | SATISFIED — existing WFs; invoked by CC_EXECUTE_SLOT_SEQUENCE_V0 per slot |
| Mempool persistence CS wiring | transaction WFs → CS_REGISTRY | `blockchain::CS_REGISTRY_V0` | GAP — missing from 5 SYSTEM WF runtime bindings; corrected in transaction subdomain |
| Validator eligibility query | consensus_pos → validator | `blockchain::CC_QUERY_ELIGIBLE_VALIDATORS_V0` | GAP — filter fields misaligned; corrected in consensus_pos; IN schema corrected in validator |

---

## 7. Governance Boundary Rules

1. **WF_RUN_CONSENSUS_SLOTS_V0 governs bounded runs only** — this WF is not a live-protocol artifact; live operation is a different architecture (decoupled streams, no termination concept); the two must never be conflated
2. **Termination declared in input** — the slot loop CC exits when its input schedule is exhausted; no external kill signal, no polling, no ambient control of any kind
3. **Slot loop CC is an orchestrator, not a domain actor** — CC_EXECUTE_SLOT_SEQUENCE_V0 invokes governed WFs; it contains no domain logic; all domain behavior lives in the WFs and CCs it calls
4. **CS writes scoped to owning subdomain** — consensus_pos does not write to transaction, block, validator, or identity stores; all writes occur through owned CCs of the respective subdomain
5. **Validator eligibility is read-only from the slot loop** — the consensus loop reads validator status; it does not change it; validator status changes belong to the validator subdomain under its own governed paths
6. **SYSTEM WF CS fix is a transaction subdomain concern** — the runtime binding correction for MINT, BURN, POOL, REWARD, SLASH is governed by `blockchain::transaction`; consensus_pos has no ownership over those bindings

---

## 8. PPS Artifacts Requiring Action

| Artifact | Current Status | Action |
|----------|---------------|--------|
| `blockchain::IN_BLOCK_PROPOSED_V0` | EXISTS — missing slot, epoch fields | UPDATE — add slot and epoch as required fields |
| `blockchain::WF_PROPOSE_BLOCK_V0` | EXISTS — CC_FORM_BLOCK_V0 node missing slot, epoch bindings | UPDATE — wire slot and epoch to CC_FORM_BLOCK_V0 node inputs |
| `blockchain::CC_QUERY_ELIGIBLE_VALIDATORS_V0` | EXISTS — filter on enrollment_status, stake (non-canonical fields) | UPDATE — filter on status = ACTIVE_ONGOING and effective_balance present |
| `blockchain::IN_VALIDATOR_REGISTERED_V0` | EXISTS — 4-field schema; missing 4 canonical fields | UPDATE — extend to 8-field schema; add status, effective_balance, activation_epoch, exit_epoch |
| `blockchain::RB_MINT_V0` | EXISTS — missing CS_REGISTRY_V0 binding | UPDATE — add CS_REGISTRY_V0 for tx dedup steps |
| `blockchain::RB_BURN_V0` | EXISTS — missing CS_REGISTRY_V0 binding | UPDATE — add CS_REGISTRY_V0 for tx dedup steps |
| `blockchain::RB_POOL_V0` | EXISTS — missing CS_REGISTRY_V0 binding | UPDATE — add CS_REGISTRY_V0 for tx dedup steps |
| `blockchain::RB_REWARD_V0` | EXISTS — missing CS_REGISTRY_V0 binding | UPDATE — add CS_REGISTRY_V0 for tx dedup steps |
| `blockchain::RB_SLASH_V0` | EXISTS — missing CS_REGISTRY_V0 binding | UPDATE — add CS_REGISTRY_V0 for tx dedup steps |

---

## 9. Governance Outcome

Capabilities that require protocol realization. Design Intent (Stage 6b) determines which artifact family each maps to and assigns FQDN codes. Organized by subdomain ownership.

**consensus_pos subdomain — new capabilities:**
- Finite consensus slot loop — governed execution of a declared, bounded slot sequence
- Slot loop input contract — admission gate for the slot schedule payload
- Post-run result verification — assertion that PROPOSED blocks and all tx types are present

**consensus_pos subdomain — corrected capabilities:**
- Slot + epoch wiring in block proposal input contract
- Slot + epoch wiring in block proposal workflow node bindings
- Eligible validator query — filter field alignment to canonical stored fields

**blockchain::transaction subdomain — corrected runtime bindings:**
- CS_REGISTRY_V0 wiring in MINT runtime binding
- CS_REGISTRY_V0 wiring in BURN runtime binding
- CS_REGISTRY_V0 wiring in POOL runtime binding
- CS_REGISTRY_V0 wiring in REWARD runtime binding
- CS_REGISTRY_V0 wiring in SLASH runtime binding

**blockchain::validator subdomain — corrected admission schema:**
- Validator registration input contract extended to 8-field canonical schema

---

## 10. Governance Decision Gate

**Presenting for Analyst approval:**

1. No new subdomains declared — all three affected subdomains (consensus_pos, transaction, validator) are existing governed namespaces
2. The SYSTEM WF CS wiring fix is owned by `blockchain::transaction`, not `consensus_pos` — the runtime bindings are transaction artifacts
3. The validator registration schema fix is owned by `blockchain::validator` — the admission contract is a validator artifact; the eligibility query fix is owned by `consensus_pos`
4. WF_RUN_CONSENSUS_SLOTS_V0 is a bounded-run artifact only — live daemon operation is architecturally distinct and requires no new artifact
5. CC_EXECUTE_SLOT_SEQUENCE_V0 is an orchestrator that invokes governed WFs across subdomains — it contains no domain logic; this is the Collatz pattern applied to side-effectful iteration
6. No new storage is required — all stores (BLOCKS, CONSENSUS_ROUNDS, TRANSACTION mempool, VALIDATOR) were declared in prior CRs
7. Cross-subdomain writes are forbidden — slot loop CC invokes WFs; it does not write directly to any store
8. Block attestation, finalization, chain commitment, and live daemon operation are explicitly deferred

*Analyst approval of this document gates entry into Stage 6b — Design Intent.*

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 1 — Input Elicitation | Problem + Outcome + Known Facts | COMPLETE |
| Stage 2 — Domain Model Discovery | Entities, Processes, PPS Baseline, Gap Analysis | COMPLETE |
| Stage 3 — Analysis Loop | Q1–Q6 resolved; 2 iterations; 6 gaps registered and resolved | COMPLETE — SATURATED |
| Stage 4 — Business Model | Capability graph, dependency graph, constraints, gaps, design decisions, authoring scope | COMPLETE |
| Stage 5 — Business Intent | 5_business_intent_consensus_propose_v0.md | COMPLETE |
| Stage 6 — Governance Intent | This document | PENDING APPROVAL |
| Stage 6b — Design Intent | PENDING |
| Stage 7 — Authoring Mandate | PENDING |
| Stage 8 — Authoring Manifest | PENDING |

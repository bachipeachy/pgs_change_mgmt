# Governance Intent: blockchain / orchestration
**Domain:** blockchain  
**Subdomain:** orchestration  
**Version:** V0  
**Status:** COMPLETE  
**Pipeline Stage:** Stage 6 — Governance Intent (WHERE)  
**Produced by:** v0.5.0 SDLC authoring pipeline  
**Purity:** WHERE only — artifact family mapping, provisional artifact codes, and store declarations excluded  

---

## 1. Domain Placement

| Field | Value |
|-------|-------|
| Domain | `blockchain` |
| Primary subdomain | `orchestration` — NEW, declared by this CR |
| Secondary subdomains | `consensus_pos` — EXISTING (dependency); `transaction` — EXISTING (dependency); `mempool` — EXISTING (transitive dependency via consensus_pos) |
| FQDN namespace | `blockchain` |
| orchestration status | NEW — declared by this CR as a governed subdomain |
| consensus_pos status | EXISTING — dependency; no structural changes |
| transaction status | EXISTING — dependency; no structural changes |

The `blockchain::orchestration` subdomain is declared as a new governed namespace by this CR. It owns the coordination of concurrent blockchain domain workflows — a concern that no existing subdomain owns and that crosses the governance boundaries of consensus_pos, transaction, and mempool. Extending any existing subdomain would conflate coordination with execution: orchestration decides *when and in what sequence* workflows run; the dependency subdomains decide *how* those workflows execute internally.

Subdomain existence is a governance topology declaration. It is not derived from the presence of any artifact in the snapshot. Governance declares the subdomain; artifacts then belong to it.

---

## 2. Authority and Governance

| Concern | Governing Constitution |
|---------|------------------------|
| Actor authority | `fb.constitution::CONSTITUTION_GOVERNANCE_V0` |
| Execution topology (WF, IN, CC) | `fb.topology::CONSTITUTION_WORKFLOW_V0`, `fb.topology::CONSTITUTION_INTENT_V0`, `fb.topology::CONSTITUTION_CAPABILITY_CONTRACT_V0` |
| Storage topology | `fb.constitution::CONSTITUTION_STRUCTURE_V0` |
| Domain invariants | `blockchain::INVARIANT_CT_SURFACE_CLOSED_BLOCKCHAIN_V0` |

Orchestration operations execute under `SYSTEM` authority class. The simulation launch is a system-initiated operation — it is not user-facing and does not require an enduser actor record. No new authority class is required. No new actor type is required — the Simulation Operator is a transport-layer entry trigger, not a governed actor in the orchestration domain.

---

## 3. Subdomain Boundary

### Owned by orchestration (this CR)

| Capability | Ownership Decision |
|-----------|-------------------|
| Simulation launch coordination | OWNED — `blockchain::orchestration` |
| Slot clock state (protocol-visible slot position) | OWNED — `blockchain::orchestration`; exclusively owned; no other subdomain reads or writes this store |
| Concurrent worker dispatch declaration | OWNED — `blockchain::orchestration`; uses CS substrate from capability_side_effects |
| Consensus loop coordination (slot sequence governing) | OWNED — `blockchain::orchestration` |
| TX workload coordination (TX sequence governing) | OWNED — `blockchain::orchestration` |
| Discrete slot execution unit (TX-agnostic) | OWNED — `blockchain::orchestration` |
| Slot context preparation (slot/epoch derivation) | OWNED — `blockchain::orchestration`; pure computation owned by this subdomain |
| Simulation summary recording | OWNED — `blockchain::orchestration` |
| Simulation configuration seed | OWNED — `blockchain::orchestration`; at seeds/blockchain/orchestration/ |
| Orchestration compiler structure | OWNED — `blockchain::orchestration`; declares slot clock entity and subdomain artifact families |

### Satisfied by existing subdomains — no ownership transfer

| Capability | Owned By | PPS Status |
|-----------|---------|------------|
| Block proposal (select proposer, form block, drain mempool) | `blockchain::consensus_pos` | SATISFIED — `blockchain::WF_PROPOSE_BLOCK_V0` reused; no changes required |
| Transaction submission — MINT | `blockchain::transaction` | SATISFIED — `blockchain::WF_MINT_V0` reused; no changes required |
| Transaction submission — TRANSFER | `blockchain::transaction` | SATISFIED — `blockchain::WF_TRANSFER_V0` reused; no changes required |
| Transaction submission — BURN | `blockchain::transaction` | SATISFIED — `blockchain::WF_BURN_V0` reused; no changes required |
| Transaction submission — STAKE, UNSTAKE, POOL, REWARD, SLASH | `blockchain::transaction` | SATISFIED — corresponding typed WFs reused; no changes required |
| Single WF invocation substrate | `capability_side_effects` | SATISFIED — `capability_side_effects::CS_WORKFLOW_GATEWAY_V0` reused |
| Sequential loop substrate | `capability_side_effects` | SATISFIED — `capability_side_effects::CS_WORKFLOW_LOOP_V0` reused |
| Mutable JSON store substrate | `capability_side_effects` | SATISFIED — `capability_side_effects::CS_MUTABLE_JSON_V0` reused for slot clock store |

### Dependency gap — new capability required in capability infrastructure (not blockchain)

| Capability | Owner | Status |
|-----------|-------|--------|
| Concurrent WF dispatch substrate | `capability_side_effects` | GAP — `CS_CONCURRENT_WORKFLOWS_V0` must be authored in the capability infrastructure; this CR declares the need; capability substrate owns the artifact; this is a substrate capability that may be consumed by any domain requiring governed parallel execution |

### Deferred to future CRs — not owned this CR

| Capability | Reason |
|-----------|--------|
| AR_ governed retirement artifact family | Future pgs_governance CR — new artifact type declaration required |
| Compiler enforcement for RETIRED artifacts | Future pgs_governance CR — depends on AR_ family |
| WF_PROCESS_EPOCH_V0 | Future CR — epoch coordination not confirmed as distinct business concern in V0 |
| Distributed orchestration | Future CR — no multi-node model justified |
| Generic cross-domain orchestration substrate | Future CR — abstract when second domain triggers same pattern |

---

## 4. Composition — Extension Pattern

| Composition Decision | Detail |
|---------------------|--------|
| Domain | Extend existing `blockchain` domain — no new domain created |
| Subdomain (primary) | Declare NEW `blockchain::orchestration` namespace — established by this CR |
| Actor types | Reuse existing — no new actor type required |
| Execution substrate — single WF | Reuse `capability_side_effects::CS_WORKFLOW_GATEWAY_V0` |
| Execution substrate — sequential loop | Reuse `capability_side_effects::CS_WORKFLOW_LOOP_V0` |
| Execution substrate — mutable store | Reuse `capability_side_effects::CS_MUTABLE_JSON_V0` |
| Execution substrate — concurrent dispatch | NEW — `capability_side_effects::CS_CONCURRENT_WORKFLOWS_V0` required; authored in capability infrastructure, not blockchain |
| consensus_pos dependency | Cross-subdomain WF invocation — block proposal; `blockchain::consensus_pos` owned; no changes to that subdomain |
| transaction dependency | Cross-subdomain WF invocation — typed TX submissions; `blockchain::transaction` owned; no changes to that subdomain |
| Storage topology | New STRUCTURE required — `STRUCTURE_BLOCKCHAIN_ORCHESTRATION_STORAGE_V0` declares slot clock entity, simulation summary entity, and orchestration subdomain artifact families; see Section 5 |

Cross-subdomain WF invocations are permitted within the `blockchain` domain. Cross-subdomain writes are forbidden — `blockchain::orchestration` does not write to consensus_pos, transaction, mempool, or any other subdomain's stores. The slot clock store and simulation summary store are exclusively owned by orchestration.

---

## 5. Storage Governance Requirements

The existing `STRUCTURE_BUILD_BLOCKCHAIN_CONFIG_V0` does not cover orchestration. A new structure artifact is required.

**orchestration subdomain storage:**
- Slot clock store — one mutable record per active simulation; keyed by simulation_id; holds current_slot, slot_start_ts, slot_duration_seconds; read before each slot execution and advanced after each slot execution
- Simulation summary store — append-only journal; one record appended per simulation run completion; holds outcome (SUCCESS/VIOLATION) and aggregate metrics; immutable after write

*Design Intent (Stage 6b) declares actual store paths, entity schema, and STRUCTURE artifact bindings.*

---

## 6. Cross-Subdomain Dependency Declaration

| Dependency | Direction | Existing PPS Artifact | Status |
|-----------|-----------|----------------------|--------|
| Block proposal invocation | orchestration → consensus_pos | `blockchain::WF_PROPOSE_BLOCK_V0` | SATISFIED — reuse via CS_WORKFLOW_GATEWAY_V0; no changes required |
| Typed TX submission — MINT | orchestration → transaction | `blockchain::WF_MINT_V0` | SATISFIED — reuse via CS_WORKFLOW_LOOP_V0 dispatch mapping |
| Typed TX submission — TRANSFER | orchestration → transaction | `blockchain::WF_TRANSFER_V0` | SATISFIED — reuse via CS_WORKFLOW_LOOP_V0 dispatch mapping |
| Typed TX submission — BURN, STAKE, UNSTAKE, POOL, REWARD, SLASH | orchestration → transaction | corresponding typed WFs | SATISFIED — reuse via CS_WORKFLOW_LOOP_V0 dispatch mapping |
| Concurrent WF dispatch substrate | orchestration → capability_side_effects | None | GAP — `CS_CONCURRENT_WORKFLOWS_V0` must be authored; owned by capability infrastructure |
| Sequential loop substrate | orchestration → capability_side_effects | `capability_side_effects::CS_WORKFLOW_LOOP_V0` | SATISFIED — reuse |
| Single WF invocation substrate | orchestration → capability_side_effects | `capability_side_effects::CS_WORKFLOW_GATEWAY_V0` | SATISFIED — reuse |
| Mutable store substrate | orchestration → capability_side_effects | `capability_side_effects::CS_MUTABLE_JSON_V0` | SATISFIED — reuse for slot clock store |

---

## 7. Governance Boundary Rules

1. **Orchestration invokes governed WFs — never dependency subdomain CCs** — `blockchain::orchestration` invokes `blockchain::consensus_pos` and `blockchain::transaction` via their published WF entry points only; orchestration cannot call consensus_pos or transaction CCs directly; cross-domain coupling at the CC level would make orchestration dependent on dependency subdomain internals

2. **PGS governs orchestration intent, not execution mechanics** — the protocol declares what runs, when, and under what termination criteria; threads, asyncio, OS timers, and process scheduling are transport-layer implementation details; `CS_CONCURRENT_WORKFLOWS_V0` is the protocol boundary: the CC declares concurrent dispatch intent; the RB implements it via asyncio.gather

3. **Slot clock exclusively owned by orchestration** — no other subdomain reads or writes the SLOT_CLOCK store; slot state is orchestration-internal governed state; it is not a cross-subdomain contract

4. **Bootstrap is a pre-condition for simulation launch** — orchestration does not create actors, wallets, or validators; those must exist in their respective subdomains before any simulation invocation; orchestration admission must gate on pre-populated seed state, not perform environment setup

5. **One slot = one governed invocation = one trace = complete** — WF_PROCESS_SLOT_V0 is a single discrete execution unit; WF_RUN_CONSENSUS_LOOP_V0 governs repeated invocations via the Collatz loop substrate; no perpetual loop WFs; every WF terminates

6. **Cross-subdomain writes are forbidden** — `blockchain::orchestration` does not write to consensus_pos, transaction, mempool, identity, or wallet stores; it writes only to its own SLOT_CLOCK and SIMULATION_SUMMARY stores

7. **TX type dispatch is a seed concern, not an orchestration routing concern** — the tx_type routing table (MINT → WF_MINT_V0, etc.) is declared in the seed configuration and the CC dispatch spec; it is not runtime branching logic in the orchestration WF DAG

8. **Capability promotion requires demonstrated cross-domain reuse** — additional orchestration capabilities require demonstrated reuse before promotion to `capability_side_effects`; domain-local CTs and CCs that solve a specific domain concern belong to the domain that owns that concern; premature abstraction into the capability infrastructure layer is forbidden

9. **Subdomain execution ownership is non-negotiable** — orchestration owns coordination; `consensus_pos` owns consensus; `transaction` owns transaction execution; no subdomain may absorb another's execution concerns through cross-subdomain CC invocation or store access

---

## 8. PPS Artifacts Requiring Action

| Artifact | Current Status | Action |
|----------|---------------|--------|
| `blockchain::WF_RUN_CONSENSUS_SLOTS_V0` | EXISTS — bundles TX dispatch + slot execution under consensus_pos | HISTORICAL — no deprecation; lifecycle retirement metadata (lifecycle.status = RETIRED + replacement references) added during authoring pass; artifact otherwise unchanged |
| `blockchain::CC_EXECUTE_SLOT_SEQUENCE_V0` | EXISTS — Collatz loop substrate with bundled TX sub-sequence | HISTORICAL — unchanged; no action; remains in snapshot as historical artifact |
| `blockchain::IN_TRANSACTION_SUBMITTED_V0` | EXISTS — status RETIRED, superseded_by typed INs | NO ACTION — already retired; this CR does not use it and does not modify it |
| `capability_side_effects::CS_CONCURRENT_WORKFLOWS_V0` | DOES NOT EXIST | AUTHOR — new infrastructure CS; owned by capability_side_effects namespace; triggered by this CR; governs concurrent WF dispatch intent; implemented via asyncio.gather in its RB |

---

## 9. Governance Outcome

The following capabilities require protocol realization. Design Intent (Stage 6b) determines which artifact family each maps to and assigns FQDN codes.

**blockchain::orchestration subdomain:**
- Simulation launch admission and configuration validation
- Slot clock initialization (write initial slot position at simulation start)
- Slot clock read (read current slot state before each slot execution)
- Slot clock advancement (advance slot N → N+1 after each slot execution)
- Concurrent worker dispatch declaration (declare two concurrent WFs; wait for both)
- Consensus loop coordination (govern repeated slot execution via Collatz loop)
- TX workload coordination (govern repeated typed TX submission via Collatz loop with dispatch mapping)
- Discrete slot execution unit (read clock → derive context → invoke block proposal → advance clock)
- Slot context derivation (pure computation: slot = round_number % slots_per_epoch; epoch = round_number // slots_per_epoch)
- Block proposal invocation (call WF_PROPOSE_BLOCK_V0 with prepared slot context)
- Simulation summary recording (aggregate sub-WF results; append outcome record)
- Simulation configuration seed (pre-resolved TX payloads + launch parameters)
- Orchestration compiler structure (STRUCTURE artifact declaring clock entity + subdomain families)

**capability_side_effects subdomain (infrastructure gap — triggered by this CR):**
- Concurrent WF dispatch substrate (`CS_CONCURRENT_WORKFLOWS_V0`) — invokes multiple WFs concurrently via asyncio.gather; waits for all; returns aggregate result

---

## 10. Governance Decision Gate

**Presenting for Analyst approval:**

1. `blockchain::orchestration` declared as NEW governed subdomain — owns simulation coordination, slot clock, concurrent dispatch, loop coordination, simulation summary; no existing subdomain owns these concerns
2. `CS_CONCURRENT_WORKFLOWS_V0` is owned by `capability_side_effects` (infrastructure), NOT by `blockchain::orchestration` — consistent with CS_WORKFLOW_GATEWAY_V0 and CS_WORKFLOW_LOOP_V0 placement; orchestration declares the capability need via CC; the substrate artifact belongs to capability infrastructure; `CS_CONCURRENT_WORKFLOWS_V0` is a substrate capability that may be consumed by any domain requiring governed parallel execution — it contains no blockchain domain concepts
3. `CT_PURE_DERIVE_SLOT_EPOCH_V0` is owned by `blockchain::orchestration` — domain-specific computation (PoS slot/epoch math); not a generic reusable CT; belongs to the subdomain that uses it; `CT_PURE_DERIVE_SLOT_EPOCH_V0` has no demonstrated cross-domain reuse and therefore remains domain-local
4. All business-domain dependencies are satisfied; only one new substrate capability is required — consensus_pos, transaction, mempool subdomains require no new artifacts for this CR; typed TX WFs and WF_PROPOSE_BLOCK_V0 are reused unchanged; the single gap is `CS_CONCURRENT_WORKFLOWS_V0` in the capability infrastructure layer
5. `WF_RUN_CONSENSUS_SLOTS_V0` and `CC_EXECUTE_SLOT_SEQUENCE_V0` remain as historical artifacts — no deprecation action; lifecycle retirement metadata added during authoring pass only
6. Cross-subdomain writes are forbidden — orchestration writes only to SLOT_CLOCK and SIMULATION_SUMMARY stores (both exclusively owned by orchestration)
7. New STRUCTURE required — `STRUCTURE_BLOCKCHAIN_ORCHESTRATION_STORAGE_V0` declares slot clock entity and simulation summary entity for the orchestration subdomain
8. Bootstrap pre-condition enforced — orchestration admission gates on pre-seeded environment state; no environment creation inside orchestration
9. Transport-layer concurrency model confirmed — PGS governs concurrent dispatch intent via CC + CS; asyncio.gather is the RB implementation detail
10. Artifact lifecycle retirement framework deferred to future pgs_governance CR — `AR_RETIRE_ARTIFACT_V0` family not in scope for V0

*Analyst approval of this document gates entry into Protocol Stage 6b — Design Intent.*

---

## Pipeline Provenance

| Stage | Output | Status |
|-------|--------|--------|
| Stage 0 — Classification | 1_change_request_orchestration_v0.md | COMPLETE |
| Stage 1 — Input Elicitation | 1_input_elicitation_orchestration_v0.md | COMPLETE |
| Stage 2 — Domain Model Discovery | 2_domain_model_orchestration_v0.md | COMPLETE |
| Stage 3 — Analysis Loop | 3_analysis_loop_orchestration_v0.md | COMPLETE — SATURATED |
| Stage 4 — Business Model | 4_business_model_orchestration_v0.md | COMPLETE |
| Stage 5 — Business Intent | 5_business_intent_orchestration_v0.md | COMPLETE |
| Stage 6 — Governance Intent | This document | COMPLETE |
| Stage 6b — Design Intent | 6b_design_intent_orchestration_v0.md | PENDING |
| Stage 7 — Authoring Mandate | 7_authoring_mandate_orchestration_v0.md | PENDING |
| Stage 8 — Authoring Manifest | 8_authoring_manifest_orchestration_v0.md | PENDING |

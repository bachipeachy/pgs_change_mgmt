# Governance Intent: blockchain / consensus_pos
**Domain:** blockchain  
**Subdomain:** consensus_pos  
**Version:** V0  
**Status:** DRAFT  
**Pipeline Stage:** Stage 6 — Governance Intent (WHERE)  
**Produced by:** v0.5.0 SDLC authoring pipeline  
**Purity:** WHERE only — artifact family mapping, provisional artifact codes, and store declarations excluded  

---

## 1. Domain Placement

| Field | Value |
| --- | --- |
| Domain | `blockchain` |
| Primary subdomain | `consensus_pos` |
| Secondary subdomain | `block` — NEW, declared by this CR |
| FQDN namespace | `blockchain` |
| consensus_pos status | EXISTING — declared in PPS namespace topology |
| block status | NEW — declared by this CR as a governed subdomain |

The `consensus_pos` subdomain is an existing governed namespace within the `blockchain` domain. This CR extends and corrects it. Additionally, this CR declares `blockchain::block` as a new governed subdomain.

**Architectural rationale for block as a separate subdomain:** Block and Chain are cross-consensus entities — they are consumed by any consensus mechanism (PoS, PoW, or future variants). If a future `consensus_pow` CR were added, it would depend on the same `blockchain::block` subdomain. Block is not a consensus-private concept; it is a shared domain entity that consensus mechanisms produce and reference. Governing it under a consensus subdomain would create a wrong dependency inversion: `consensus_pos` would own something that transcends `consensus_pos`. The correct governance topology is: `blockchain::block` stands alone; consensus mechanisms depend on it.

Note: subdomain existence is a governance topology declaration. It is not derived from the presence of any artifact (WF, CC, or otherwise) in the snapshot. Governance declares the subdomain; artifacts then belong to it.

---

## 2. Authority and Governance

| Concern | Governing Constitution |
| --- | --- |
| Actor authority | `fb.constitution::CONSTITUTION_GOVERNANCE_V0` |
| Execution topology (WF, IN, CC) | `fb.topology::CONSTITUTION_WORKFLOW_V0`, `fb.topology::CONSTITUTION_INTENT_V0`, `fb.topology::CONSTITUTION_CAPABILITY_CONTRACT_V0` |
| Storage topology | `fb.constitution::CONSTITUTION_STRUCTURE_V0` |
| Domain invariants | `blockchain::INVARIANT_CT_SURFACE_CLOSED_BLOCKCHAIN_V0` |

Consensus operations execute under `SYSTEM` authority class. No new authority class is required. The Validator is not a new actor type — it is an identity actor with a transient consensus participation role managed within `consensus_pos`.

---

## 3. Subdomain Boundary

### Owned by consensus_pos (this CR)

| Capability | Ownership Decision |
| --- | --- |
| Validator enrollment and participation registry | OWNED |
| Active participation pool management | OWNED |
| Consensus round coordination (proposer selection) | OWNED |
| Block proposal process (governing workflow) | OWNED |
| Validator registration | OWNED — re-author through correct pipeline |
| Chain entity placeholder (structural pre-wire only) | OWNED — no execution this CR |
| Consensus round record (proposed and skipped outcomes) | OWNED |
| Round skip record and event | OWNED |

### Owned by blockchain::block (new subdomain, declared this CR)

| Capability | Ownership Decision |
| --- | --- |
| Block formation and assembly | OWNED — `blockchain::block` |
| Block persistence (block record store) | OWNED — `blockchain::block` |
| Block lifecycle events (block proposed event) | OWNED — `blockchain::block` |

`blockchain::block` is declared as a governed subdomain by this CR. The business dependency graph places Block as a foundational entity that consensus depends on — not a concept that consensus defines. Governance topology declares the boundary definitively: Block is not a consensus concern; it is a block concern. `consensus_pos` depends on `blockchain::block` for block formation capability.

`consensus_pos` DEPENDS ON `blockchain::block` for:
- Block formation — capability owned and implemented by `blockchain::block`
- Block persistence — store governed by `blockchain::block`
- Block proposed event — lifecycle event owned by `blockchain::block`

### Satisfied by existing subdomains — no ownership transfer

| Capability | Owned By | PPS Status |
| --- | --- | --- |
| Actor identity and registration | `blockchain::identity` | SATISFIED |
| Actor existence resolution | `blockchain::identity` | SATISFIED — `blockchain::CC_CHECK_ACTOR_EXISTS_V0` reused |
| Transaction submission | `blockchain::transaction` | SATISFIED |
| Pending transaction persistence (mempool write) | `blockchain::transaction` | SATISFIED — `blockchain::CC_PERSIST_MEMPOOL_TX_V0` |

### Deferred to future CRs — not owned this CR

| Capability | Reason |
| --- | --- |
| Block attestation | Future CR — Attestor role not in scope |
| Block finalization and chain population | Future CR — Finalizer role not in scope |
| Stake enforcement (slashing) | Future CR — stake is declaration only |
| Rewards | Future CR |
| Epoch and Checkpoint management | Future CR — beyond Consensus Round (Slot) scope |
| Multi-node coordination | Future CR |
| Live validator enrollment sync from identity | Future CR — enrollment seeded at bootstrap |

---

## 4. Composition — Extension Pattern

| Composition Decision | Detail |
| --- | --- |
| Domain | Extend existing `blockchain` domain — no new domain created |
| Subdomain (primary) | Extend existing `consensus_pos` namespace — already in PPS topology |
| Subdomain (new) | Declare `blockchain::block` as a new governed namespace — established by this CR |
| Actor types | Reuse existing — no new actor type required |
| Execution substrate | Reuse existing capability substrate |
| Identity dependency | Cross-subdomain read — actor existence check; `blockchain::identity` owned |
| Transaction dependency | Cross-subdomain read — pending transaction query; `blockchain::transaction` owned |
| Block dependency | Cross-subdomain capability call — block formation; `blockchain::block` owned, declared this CR |
| Storage topology | Extension required to `STRUCTURE_BLOCKCHAIN_STORAGE_V0` — see Section 5 |

Cross-subdomain reads and capability calls are permitted within the `blockchain` domain. Cross-subdomain writes are forbidden — `consensus_pos` does not write to identity, transaction, or block stores. Block stores are governed by `blockchain::block`; writes to those stores are performed by block-owned capabilities only.

---

## 5. Storage Governance Requirements

The existing `STRUCTURE_BLOCKCHAIN_STORAGE_V0` already declares storage for:

| Existing Coverage | Status |
| --- | --- |
| Validator registry (identity → enrollment pointer) | EXISTING — sufficient for validator registration re-author |
| Validator lifecycle events | EXISTING |

Governance requires persistent storage for the following additional concerns, organized by subdomain governance. Design Intent and STRUCTURE update will declare actual store names and paths:

**consensus_pos subdomain storage:**
- Validator enrollment (active participation status + stake credential) — enriches existing VALIDATOR store
- Consensus round records (round outcomes: proposed and skipped)
- Consensus lifecycle events (round skip event journal)

**blockchain::block subdomain storage:**
- Proposed blocks (block formation records)
- Block lifecycle events (block proposed event journal)

---

## 6. Cross-Subdomain Dependency Declaration

| Dependency | Direction | Existing PPS Artifact | Status |
| --- | --- | --- | --- |
| Actor existence check | consensus_pos → identity | `blockchain::CC_CHECK_ACTOR_EXISTS_V0` | SATISFIED — reuse |
| Actor ID resolution | consensus_pos → identity | `blockchain::CC_RESOLVE_ACTOR_ID_V0` | SATISFIED — available |
| Pending transaction query | consensus_pos → transaction | None | GAP — new capability required; owned by `blockchain::transaction` |
| Block formation | consensus_pos → block | None | GAP — new capability required; owned by `blockchain::block` (new subdomain, declared this CR) |

---

## 7. Governance Boundary Rules

1. **Single chain, single proposer per round** — at most one block proposed per consensus round; no fork resolution this CR
2. **Append-only block record** — proposed blocks are never removed or modified once written
3. **Identity prerequisite gate** — a validator must exist in the identity registry before enrollment in consensus_pos participation
4. **No ambient authority** — all validator selection and block proposal authority flows from declared WF and CC artifacts; no runtime branching
5. **Stake as declaration only** — stake field recorded on enrollment; no deposit, withdrawal, or enforcement owned by this subdomain

---

## 8. PPS Artifacts Requiring Action

The following existing PPS artifacts require review or replacement as part of this CR:

| Artifact | Current Status | Action |
| --- | --- | --- |
| `blockchain::WF_REGISTER_VALIDATOR_V0` | EXISTS — authored through flawed pipeline (GI gate skipped) | REPLACE: re-author through correct governed pipeline (GI gate now satisfied by this document) |
| `blockchain::IN_VALIDATOR_REGISTERED_V0` | EXISTS | REVIEW — verify semantic alignment with re-authored WF |
| `blockchain::CC_CHECK_VALIDATOR_EXISTS_V0` | EXISTS | REUSE — execution logic sound |
| `blockchain::CC_WRITE_VALIDATOR_RECORD_V0` | EXISTS | REVIEW — stake qualification field must be confirmed |
| `blockchain::CC_APPEND_VALIDATOR_EVENT_V0` | EXISTS | REUSE |
| `blockchain::EV_VALIDATOR_REGISTERED_V0` | EXISTS | REUSE |
| `blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0` | EXISTS | EXTEND — add storage for enrollment, rounds, blocks, block events |

---

## 9. Governance Outcome

The following capabilities require protocol realization. Design Intent (Stage 6b) determines which artifact family each maps to and assigns FQDN codes. Capabilities are organized by subdomain ownership.

**consensus_pos subdomain:**
- Validator Enrollment (enroll, update status, query eligibility)
- Active Participation Pool Query
- Proposer Selection (from active pool, per consensus round)
- Block Proposal Process (the governing workflow — consensus orchestrates, block subdomain executes)
- Consensus Round Recording (proposed and skipped outcomes)
- Round Skipped Event

**blockchain::block subdomain (new — declared this CR):**
- Block Formation
- Block Persistence
- Block Proposed Event

**blockchain::transaction subdomain (dependency gap — new capability owned by transaction):**
- Pending Transaction Query (cross-subdomain read; capability owned by transaction, not consensus_pos)

---

## 10. Governance Decision Gate

**Presenting for Analyst approval:**

1. Domain `blockchain`, subdomain `consensus_pos` — existing namespace, extended by this CR
2. `blockchain::block` declared as new governed subdomain by this CR — Block is not a consensus concept; it is a block concern
3. `consensus_pos` DEPENDS ON `blockchain::block` for block formation — not the reverse
4. Subdomain existence declared by governance topology — not derived from artifact presence
5. No new actor types — Validator is an identity actor with transient consensus role
6. Identity and transaction capabilities remain owned by their respective subdomains; cross-subdomain capability calls permitted within the `blockchain` domain
7. Cross-subdomain writes are forbidden — consensus_pos does not write to block, transaction, or identity stores
8. STRUCTURE extension required for: consensus_pos (round records, consensus events); blockchain::block (block records, block events)
9. Pending transaction query is a new gap — capability owned by `blockchain::transaction`, not consensus_pos
10. Stake enforcement, attestation, finalization, epoch/checkpoint — all deferred to future CRs

*Analyst approval of this document gates entry into Protocol Stage 6b — Design Intent.*

---

## Pipeline Provenance

| Stage | Output | Status |
| --- | --- | --- |
| Stage 0 — Classification | change_request_subdomain | COMPLETE |
| Stage 1 — Input Elicitation | Problem + Outcome + Known Facts | COMPLETE |
| Stage 2 — Domain Model Discovery | Actors, Entities, Resources, Events, Relationships | COMPLETE |
| Stage 3 — Analysis Loop | Capability Graph, Dependency Graph, Constraints, Gap Register | COMPLETE — SATURATED |
| Stage 4 — Business Model | 4_business_model_consensus_pos_v0.md | COMPLETE |
| Stage 4b — Authoring Scope | IN/FUTURE CR boundary | COMPLETE — APPROVED |
| Stage 5 — Business Intent | 5_business_intent_consensus_pos_v0.md | COMPLETE |
| Stage 6 — Governance Intent | This document | PENDING APPROVAL |
| Stage 6b — Design Intent | Pending | — |
| Stage 7 — Authoring Plan | Pending | — |

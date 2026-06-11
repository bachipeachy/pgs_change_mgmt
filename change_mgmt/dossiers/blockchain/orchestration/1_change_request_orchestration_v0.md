# Change Request: blockchain / orchestration
**CR Type:** change_request_subdomain  
**Domain:** blockchain  
**Primary Subdomain:** orchestration — NEW  
**Secondary Subdomain:** consensus_pos — EXISTING (dependency); transaction — EXISTING (dependency); mempool — EXISTING (dependency)  
**Version:** V0  
**Status:** COMPLETE  
**Pipeline Stage:** Stage 0 — Change Request Classification  

---

## 1. Problem Statement

The blockchain domain has no governed mechanism for coordinating concurrent workflow execution. Scheduling, timing, slot progression, and work distribution are performed by external scripts that operate outside the PGS governance boundary. The immediate concrete gap: TX submission and the Consensus Loop must be able to run concurrently, but there is no governed unit that owns this coordination — it is currently handled by `scripts/test_blockchain_e2e.py` as unprotocol imperative code.

The result is:

- No governed slot timing — slot duration, slot number, and slot progression are external state invisible to the protocol
- No governed concurrent workflow coordination — orchestration decisions are made outside the governance boundary
- No governed entry point for slot-driven execution — the external test harness is the de facto orchestrator
- External code (`test_blockchain_e2e.py`) carries business-level coordination logic that belongs inside the protocol

---

## 2. Desired Outcome

A governed `blockchain::orchestration` subdomain that owns concurrent blockchain workflow coordination end-to-end:

- Governed slot-based execution unit — each slot is a single, discrete, fully traceable governed execution
- Governed slot state — slot number, slot start timestamp, and slot duration are protocol-visible, auditable state (not external timer state)
- Governed concurrent coordination — TX submission and slot processing run concurrently under protocol governance, not under external script control
- Governed entry point — the external trigger (timer, test harness, cron) becomes a thin transport-layer signal; all business logic after invocation is governed
- `scripts/test_blockchain_e2e.py` is refactored: orchestration logic moves into the governed subdomain; the script becomes a thin config/param entry point (shell or minimal Python) that invokes the orchestrator with slot duration, slot count, and TX submission parameters

---

## 3. Known Facts at CR Entry

| Fact | Source |
|------|--------|
| `blockchain::consensus_pos` subdomain is governed and deployed — WF_PROPOSE_BLOCK_V0, WF_FINALIZE_BLOCK_V0 exist | PPS snapshot |
| `blockchain::transaction` subdomain is governed — WF_SUBMIT_TRANSACTION_V0 exists | PPS snapshot |
| `blockchain::mempool` subdomain is governed — CC_WRITE_MEMPOOL_TX_V0, CC_QUERY_MEMPOOL_TXS_V0, CC_DRAIN_MEMPOOL_V0 exist | PPS snapshot |
| `scripts/test_blockchain_e2e.py` currently owns slot timing (sleep-based), TX submission sequencing, and consensus loop invocation — all outside the governance boundary | Codebase |
| External timers/triggers are valid PGS transport-layer entry points — analogous to HTTP ingress; they carry no domain semantics | Strategic architecture (orchestration_domain_proposal.md) |
| Loop workflows (never-terminating) violate the PGS execution model — every WF must be: input → deterministic behavior → output → trace → complete | Core Doctrine |
| Slot state (current_slot, slot_start_ts, slot_duration_seconds) must be protocol-visible state, not external script state | Strategic architecture (orchestration_domain_proposal.md) |
| No changes to the WF execution model, CT/CC execution, governance pipeline, or snapshot model are required | Strategic architecture (orchestration_domain_proposal.md) |

---

## 4. CR Type Determination

**Type:** `change_request_subdomain`

**Analysis path triggered:** Full loop required — Domain Model Discovery + Analysis Loop until Discovery Saturation. Declaring a new subdomain with cross-subdomain dependencies (consensus_pos, transaction, mempool) and a new governed clock store requires the complete pipeline.

**Pipeline entry:** Stage 1 — Input Elicitation

| CR Type | Analysis Path |
|---------|--------------|
| change_request_bug | Skip to Gap Analysis on existing artifacts |
| change_request_feature | Capability + Gap analysis only |
| change_request_subdomain | Full loop: Domain Model Discovery + Analysis Loop until Discovery Saturation |
| change_request_domain | Full loop + new domain declaration |

---

## 5. Governance Scope Declared by This CR

| Subdomain | Action | Rationale |
|-----------|--------|-----------|
| `blockchain::orchestration` | DECLARE NEW | Owns slot-based execution coordination — slot state, concurrent WF invocation, governed entry point |
| `blockchain::consensus_pos` | DEPENDENCY | Orchestration drives slot processing; consensus_pos WFs are invoked by the orchestration subdomain |
| `blockchain::transaction` | DEPENDENCY | Orchestration drives concurrent TX submission; WF_SUBMIT_TRANSACTION_V0 is called under orchestration coordination |
| `blockchain::mempool` | DEPENDENCY | Slot processing reads and drains mempool via mempool-owned CCs; orchestration is a declared consumer |

---

## 6. Out of Scope — Deferred to Future CRs

| Capability | Reason |
|-----------|--------|
| Generic `pgs_orchestration` repository / cross-domain substrate | Premature — no second domain use case yet; abstract when pattern repeats independently |
| Event subscription model (event registry, subscription dispatch, routing rules) | YAGNI — one use case does not justify dispatch machinery; deferred until a second domain triggers the same event type |
| Distributed orchestration artifacts (lease, distributed lock, scheduled event, leader election) | Deferred — requires multi-node model not yet justified |
| `WF_PROCESS_EPOCH_V0` | May be in scope; deferred to Input Elicitation for confirmation |
| Slot expiry and failed-slot retry governance | Future CR — requires failure model design |
| Multi-proposer or parallel slot processing | Future CR — single proposer per slot is V0 model |

---

## Dossier Status

| Stage | Artifact | Status |
|-------|----------|--------|
| Stage 0 | 1_change_request_orchestration_v0.md | COMPLETE |
| Stage 1 | 1_input_elicitation_orchestration_v0.md | COMPLETE |
| Stage 2 | 2_domain_model_orchestration_v0.md | COMPLETE |
| Stage 3 | 3_analysis_loop_orchestration_v0.md | COMPLETE |
| Stage 4 | 4_business_model_orchestration_v0.md | COMPLETE |
| Stage 5 | 5_business_intent_orchestration_v0.md | COMPLETE |
| Stage 6 | 6_governance_intent_orchestration_v0.md | COMPLETE |
| Stage 6b | 6b_design_intent_orchestration_v0.md | COMPLETE |
| Stage 7 | 7_authoring_mandate_orchestration_v0.md | COMPLETE |
| Stage 8 | 8_authoring_manifest_orchestration_v0.md | BASELINE — pre-authoring snapshot; rows updated as authoring proceeds |
| Stage 9 | (CR Closure — no separate artifact; manifest status → APPROVED) | COMPLETE |
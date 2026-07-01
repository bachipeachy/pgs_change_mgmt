"""Deterministic proof of the STRUCTURED dossier stage (S4) — no live worker.

A stub worker emits register ROWS (structured intent); the engine renders them through the
DossierStageRenderer and judges them with the structural oracle. Proves: structured-intent →
renderer → document, the oracle figure of merit, [domain]/[subdomain] substitution, and that
the handoff persists only the declared emit-fields. Writes to a temp dir.

Run:  PGS_WORKSPACE=/abs python -m pgs_change_mgmt.engine._dossier_structured_selftest
"""

from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

from ..contracts import StageInput, StageOutput
from ..grounding import PiGroundingProvider
from .dossier import DOSSIER_SEEDS, run_dossier

CLEAN_S4 = {
    "actors": [{"actor": "Validator", "role": "Proposes/commits blocks", "authority_class": "SYSTEM", "source_finding": "S2-A1"}],
    "bm_entities": [{"entity": "Block", "description": "Canonical chain record", "store_model": "append-only", "source_finding": "S2-E1"}],
    "events": [{"event": "Block committed", "trigger": "consensus round closes", "lifecycle_meaning": "state advance", "source_finding": "S2-V1"}],
    "capability_graph": [{"capability": "Commit a validated block to the canonical chain", "source_finding": "S3-C1", "status": "CRITICAL", "gap_register_entry": "GAP-1", "notes": ""}],
    "dependency_graph": [{"from": "chain", "to": "consensus_pos", "dependency_type": "event", "pps_status": "SATISFIED", "source_finding": "S3-D1"}],
    "constraint_register": [{"num": "1", "constraint": "Chain is immutable", "source_finding": "S1-K6", "source": "governance rule"}],
    "gap_register": [{"gap_code": "GAP-1", "source_finding": "S3-C1", "capability": "Commit block to canonical chain", "owner_subdomain": "chain", "resolution": "NEW"}],
    "design_decisions": [{"num": "1", "decision": "Attest/Finalize out of scope", "source_finding": "S1-Q5", "rationale": "all blocks treated good", "constraints_imposed": "no finalization gate"}],
    "authoring_scope": [{"capability": "Commit block to chain", "gap_register_ref": "GAP-1"}],
}


# A clean Stage-6b binding-FQDN set: genesis codes are genuinely new (GENESIS → 0 in the snapshot),
# every referenced code is declared, spellings are consistent, counts reconcile.
def _na(cap, fam, code):
    return {"capability": cap, "family": fam, "code": code, "owner_subdomain": "chain",
            "status": "NEW", "source_finding": "GAP-1"}


CLEAN_6B = {
    "new_artifacts": [
        _na("register the genesis block", "WF", "blockchain::WF_REGISTER_GENESIS_BLOCK_V0"),
        _na("admit a genesis registration", "IN", "blockchain::IN_REGISTER_GENESIS_BLOCK_V0"),
        _na("bind the genesis workflow", "RB", "blockchain::RB_REGISTER_GENESIS_BLOCK_V0"),
        _na("write the genesis record", "CC", "blockchain::CC_WRITE_GENESIS_RECORD_V0"),
        _na("generate the genesis id", "CT", "blockchain::CT_PURE_GENERATE_GENESIS_ID_V0"),
        _na("emit genesis registered", "EV", "blockchain::EV_GENESIS_REGISTERED_V0"),
    ],
    "existing_inventory": [{"fqdn": "blockchain::CC_FORM_BLOCK_V0", "action": "REUSE", "reason": "forms blocks", "source_finding": "S3"}],
    "rb_declarations": [{"rb_code": "blockchain::RB_REGISTER_GENESIS_BLOCK_V0", "binds_wf": "blockchain::WF_REGISTER_GENESIS_BLOCK_V0", "cs_bindings": "capability_side_effects::CS_MUTABLE_JSON_V0", "storage_structure": "blockchain::STRUCTURE_BLOCKCHAIN_STORAGE_V0", "source_finding": "S6"}],
    "execution_topology": [
        {"workflow": "blockchain::WF_REGISTER_GENESIS_BLOCK_V0", "node": "blockchain::IN_REGISTER_GENESIS_BLOCK_V0", "node_type": "IN", "routing": "ACK -> CC_WRITE_GENESIS_RECORD_V0, NACK -> EXIT", "source_finding": "S6b"},
        {"workflow": "blockchain::WF_REGISTER_GENESIS_BLOCK_V0", "node": "blockchain::CC_WRITE_GENESIS_RECORD_V0", "node_type": "CC", "routing": "SUCCESS -> EXIT_SUCCESS, VIOLATION -> EXIT", "source_finding": "S6b"},
        {"workflow": "blockchain::WF_REGISTER_GENESIS_BLOCK_V0", "node": "EXIT_SUCCESS", "node_type": "EXIT_SUCCESS", "routing": "-", "source_finding": "S6b"},
    ],
    "artifact_summary": [
        {"action": "NEW", "subdomain": "chain", "count": "6", "artifacts": "WF, IN, RB, CC, CT, EV"},
    ],
}


class StubStructuredWorker:
    name = "stub-structured"

    def __init__(self, registers=None):
        self._registers = registers if registers is not None else CLEAN_S4

    def execute_stage(self, task: StageInput) -> StageOutput:
        telem = "[tool-loop: iters=3/24 tool_calls=5 reason=finished final_chars=0]"
        return StageOutput(stage=task.stage, registers=self._registers, findings=(telem,))


def main() -> int:
    grounding = PiGroundingProvider()
    with tempfile.TemporaryDirectory() as tmp:
        seed = replace(DOSSIER_SEEDS["blockchain_chain"], output_dir=Path(tmp) / "chain")
        result = run_dossier(StubStructuredWorker(), grounding, seed, stages=("4",),
                             runs_root=Path(tmp) / "runs")
        s = result.stages[0]
        print(f"  S4 structured={s.structured} ok={s.ok} rating={s.rating}/5 "
              f"oracle_issues={s.oracle_issues} identity={s.identity}")

        assert s.structured, "S4 should use the structured path"
        assert s.ok and not s.oracle_issues, f"oracle not clean: {s.oracle_issues}"
        assert s.rating == 5, f"clean structured stage should rate 5, got {s.rating}"

        md = (Path(tmp) / "chain" / "4_business_model_blockchain_chain_v0.md").read_text()
        assert "blockchain / chain" in md, "[domain]/[subdomain] not substituted"
        assert "Commit a validated block to the canonical chain" in md, "register data not rendered"
        assert "## Document Contract" in md, "template structure not preserved"
        print("  rendered: template preserved ✓, [domain]/[subdomain] substituted ✓, rows injected ✓")

        hf = json.loads((Path(tmp) / "chain" / "_handoff" / "4.json").read_text())
        assert "capability_graph" in hf and "resources" not in hf, "handoff != declared emit-fields"
        print(f"  handoff persisted: {sorted(hf)} (declared emit-fields only — resources/relationships excluded) ✓")

    # ---- Stage 6b: structured binding-FQDN stage + cross-register oracle ----
    with tempfile.TemporaryDirectory() as tmp:
        seed = replace(DOSSIER_SEEDS["blockchain_chain"], output_dir=Path(tmp) / "chain")
        result = run_dossier(StubStructuredWorker(CLEAN_6B), grounding, seed, stages=("6b",),
                             runs_root=Path(tmp) / "runs")
        s = result.stages[0]
        print(f"\n  S6b structured={s.structured} ok={s.ok} rating={s.rating}/5 "
              f"governed={s.governed_coverage} oracle_issues={s.oracle_issues}")
        assert s.structured, "S6b should now use the structured path"
        assert s.ok and not s.oracle_issues, f"clean S6b oracle not clean: {s.oracle_issues}"
        assert s.rating == 5, f"clean S6b should rate 5, got {s.rating}"

    # NOTE: S9 (Construction Record) is intentionally NOT exercised here. It is post-construction
    # EVIDENCE produced by the Construction engine (`construct_chain.render_s9`) from the actual
    # compiler verdicts — not a dossier-engine worker stage. Its proof lives in the construction
    # selftest, where S9 is rendered from real compiler results, not stubbed registers.

    # ---- Stage 7: structured mandate + cross-stage oracle (codes ⊆ Stage 6b registers) ----
    _c = "blockchain::"
    CLEAN_7 = {
        "build_order": [
            {"wave": "1", "step": "1", "code": _c + "CT_PURE_GENERATE_GENESIS_ID_V0", "action": "NEW", "subdomain": "chain", "depends_on": "—"},
            {"wave": "1", "step": "2", "code": _c + "CC_WRITE_GENESIS_RECORD_V0", "action": "NEW", "subdomain": "chain", "depends_on": "—"},
            {"wave": "2", "step": "3", "code": _c + "IN_REGISTER_GENESIS_BLOCK_V0", "action": "NEW", "subdomain": "chain", "depends_on": "—"},
            {"wave": "2", "step": "4", "code": _c + "RB_REGISTER_GENESIS_BLOCK_V0", "action": "NEW", "subdomain": "chain", "depends_on": "—"},
            {"wave": "2", "step": "5", "code": _c + "EV_GENESIS_REGISTERED_V0", "action": "NEW", "subdomain": "chain", "depends_on": "—"},
            {"wave": "3", "step": "6", "code": _c + "WF_REGISTER_GENESIS_BLOCK_V0", "action": "NEW", "subdomain": "chain", "depends_on": "IN_REGISTER_GENESIS_BLOCK_V0"},
        ],
        "critical_path": [{"position": "1", "code": _c + "IN_REGISTER_GENESIS_BLOCK_V0"}, {"position": "2", "code": _c + "WF_REGISTER_GENESIS_BLOCK_V0"}],
        "mandate_artifact_summary": [{"action": "NEW", "count": "6", "description": "genesis registration cluster"}],
        "field_declarations": [{"code": _c + "WF_REGISTER_GENESIS_BLOCK_V0", "subdomain_field": "chain"}, {"code": _c + "CC_WRITE_GENESIS_RECORD_V0", "subdomain_field": "chain"}],
    }
    with tempfile.TemporaryDirectory() as tmp:
        seed = replace(DOSSIER_SEEDS["blockchain_chain"], output_dir=Path(tmp) / "chain")
        hd = Path(tmp) / "chain" / "_handoff"
        hd.mkdir(parents=True)
        (hd / "6b.json").write_text(json.dumps({k: CLEAN_6B[k] for k in
            ("new_artifacts", "existing_inventory", "rb_declarations", "execution_topology", "artifact_summary")}))
        result = run_dossier(StubStructuredWorker(CLEAN_7), grounding, seed, stages=("7",),
                             runs_root=Path(tmp) / "runs")
        s = result.stages[0]
        print(f"  S7 structured={s.structured} ok={s.ok} rating={s.rating}/5 oracle_issues={s.oracle_issues}")
        assert s.structured and s.ok and s.rating == 5, f"clean S7 should rate 5: {s.oracle_issues}"

    # ---- Stages 5 & 6: plain-structured (generic oracle: required/traceability/enum/business-language) ----
    CLEAN_5 = {
        "scope_boundary": [{"capability": "create the genesis block at bootstrap", "status": "IN_SCOPE", "notes": "once, before the consensus loop", "source_finding": "S4-CAP1"}],
        "invariants": [{"invariant": "a committed block is immutable", "business_reason": "audit integrity and supply conservation", "source_finding": "S4-C2"}],
        "actions": [{"action": "REGISTER", "object": "genesis block", "trigger": "bootstrap", "status": "IN_SCOPE", "source_finding": "S4"}],
        "provisional_codes": [{"provisional_code": "WF_REGISTER_GENESIS_BLOCK_V0", "family": "WF", "summary": "register the genesis block", "source_finding": "S4"}],
        "identity_semantics": [{"store_name": "canonical chain", "identity_field": "block height", "source": "consensus round counter", "uniqueness_rule": "one committed block per height", "cross_subdomain_relationship": "references the proposing validator", "source_finding": "S4"}],
    }
    CLEAN_6 = {
        "ownership": [{"capability": "create the genesis block", "owner_subdomain": "chain", "disposition": "OWNED", "existing_artifact": "", "source_finding": "S5"}],
        "storage_governance": [{"storage_need": "canonical block records", "purpose": "immutable history of committed blocks", "subdomain": "chain", "source_finding": "S5"}],
    }
    for stage, regs in (("5", CLEAN_5), ("6", CLEAN_6)):
        with tempfile.TemporaryDirectory() as tmp:
            seed = replace(DOSSIER_SEEDS["blockchain_chain"], output_dir=Path(tmp) / "chain")
            result = run_dossier(StubStructuredWorker(regs), grounding, seed, stages=(stage,),
                                 runs_root=Path(tmp) / "runs")
            s = result.stages[0]
            print(f"  S{stage} structured={s.structured} ok={s.ok} rating={s.rating}/5 "
                  f"oracle_issues={s.oracle_issues} gaps={len(s.incomplete_sections)}")
            assert s.structured and not s.oracle_issues, \
                f"clean S{stage} registers should be clean: {s.oracle_issues}"
            if stage == "5":
                # §1 Purpose is now supplied upstream in the seed (Authoring Completeness) and
                # injected at render — it is no longer an S5 authoring hole. A register-clean S5
                # with the seed's Purpose present is fully clean and rates 5.
                assert s.ok and s.rating == 5 and not s.incomplete_sections, \
                    f"S5 §1 Purpose should fill from the seed (no prose gap): {s.incomplete_sections}"
                assert not s.unresolved_cells, "clean S5 has no declared holes"
            else:
                assert s.ok and s.rating == 5, f"clean S{stage} should rate 5"

    # ---- Phase 1: UNRESOLVED declared holes (the legal home for uncertainty) ----
    # A worker that cannot derive a required cell declares it `UNRESOLVED` instead of fabricating
    # or leaving it blank. The hole is COUNTED + scored (a gap) but is NOT an oracle issue (the
    # register stays clean / governed coverage intact), is ADMISSIBLE (hands off downstream, does
    # not halt), and renders verbatim. The row must still justify the hole in Source Finding.
    HOLE_5 = dict(CLEAN_5)
    HOLE_5["identity_semantics"] = [{
        "store_name": "canonical chain", "identity_field": "UNRESOLVED", "source": "UNRESOLVED",
        "uniqueness_rule": "UNRESOLVED", "cross_subdomain_relationship": "none",
        "source_finding": "seed declares no identity field for chain blocks — needs human input"}]
    with tempfile.TemporaryDirectory() as tmp:
        seed = replace(DOSSIER_SEEDS["blockchain_chain"], output_dir=Path(tmp) / "chain")
        result = run_dossier(StubStructuredWorker(HOLE_5), grounding, seed, stages=("5",),
                             runs_root=Path(tmp) / "runs")
        s = result.stages[0]
        print(f"  S5+hole structured={s.structured} ok={s.ok} rating={s.rating}/5 "
              f"unresolved={s.unresolved_cells} oracle_issues={s.oracle_issues}")
        assert not s.oracle_issues, f"a declared hole is NOT an oracle issue: {s.oracle_issues}"
        assert s.unresolved_cells and all("identity_semantics[0]." in u for u in s.unresolved_cells), \
            f"the three UNRESOLVED cells must be counted: {s.unresolved_cells}"
        assert not s.inadmissible, "a declared hole is admissible (visible hole, non-halting)"
        assert not s.ok, "a stage with a declared hole is not-ok (awaits clarification)"
        assert s.governed_coverage in (None, 1.0), "a hole must not dirty governed coverage"
        # §1 Purpose now fills from the seed; only the declared UNRESOLVED hole costs a star → 4/5
        assert s.rating == 4, f"S5 with a declared hole should rate 4 (§1 fills from seed): got {s.rating}"
        md = (Path(tmp) / "chain" / "5_business_intent_blockchain_chain_v0.md").read_text()
        assert "| UNRESOLVED |" in md, "the UNRESOLVED hole must render in the document"
        assert (Path(tmp) / "chain" / "_handoff" / "5.json").exists(), \
            "a declared hole still hands off downstream (admissible)"
        print("  S5 hole: counted + admissible + non-halting + rendered, register stays clean ✓")

    # A hole still demands justification: UNRESOLVED with no Source Finding is an oracle issue.
    BADHOLE_5 = dict(CLEAN_5)
    BADHOLE_5["identity_semantics"] = [{
        "store_name": "x", "identity_field": "UNRESOLVED", "source": "", "uniqueness_rule": "",
        "cross_subdomain_relationship": "", "source_finding": ""}]
    with tempfile.TemporaryDirectory() as tmp:
        seed = replace(DOSSIER_SEEDS["blockchain_chain"], output_dir=Path(tmp) / "chain")
        result = run_dossier(StubStructuredWorker(BADHOLE_5), grounding, seed, stages=("5",),
                             runs_root=Path(tmp) / "runs")
        s = result.stages[0]
        assert any("no traceability" in m for m in s.oracle_issues), \
            f"an unjustified hole (no Source Finding) must be flagged: {s.oracle_issues}"
        print("  S5 unjustified hole (no Source Finding) is rejected ✓")

    from ..evaluator.design_intent_oracle import check_authoring_mandate
    up = {"new_artifacts": CLEAN_6B["new_artifacts"], "existing_inventory": CLEAN_6B["existing_inventory"]}
    bad7 = {"build_order": [{"step": "1", "code": _c + "CC_WRITE_GENEISIS_RECORD_V0", "action": "NEW"}]}
    assert any("not in any Stage 6b register" in m for _, m in check_authoring_mandate(bad7, up)), \
        "S7 cross-stage oracle missed a re-typed code"
    print("  S7 cross-stage oracle blocks a re-typed code (not in 6b registers) ✓")

    # cross-register oracle catches the GENEISIS-class typo a free-form stage would relay
    from ..evaluator.design_intent_oracle import check_design_intent
    typo = {
        "new_artifacts": [
            _na("validate predecessor (genesis)", "CC", "blockchain::CC_VALIDATE_PREDECESSOR_LINKAGE_GENEISIS_V0"),
            _na("write the genesis record", "CC", "blockchain::CC_WRITE_GENESIS_RECORD_V0"),
            _na("register the genesis block", "WF", "blockchain::WF_REGISTER_GENESIS_BLOCK_V0"),
        ],
    }
    issues = check_design_intent(typo, grounding)
    assert any("GENEISIS" in m and "near-duplicate" in m for _, m in issues), \
        f"near-dup oracle missed the GENESIS/GENEISIS typo: {issues}"
    print("  S6b cross-register oracle catches GENEISIS typo ✓")

    # §6 Capability Composition oracle: a CC's inside is governed CT/CS steps, declared + routed.
    from ..evaluator.design_intent_oracle import check_cc_composition
    comp_clean = dict(CLEAN_6B)
    comp_clean["existing_inventory"] = CLEAN_6B["existing_inventory"] + [
        {"fqdn": "capability_side_effects::CS_MUTABLE_JSON_V0", "action": "REUSE",
         "reason": "writes the genesis record", "source_finding": "S6"}]
    comp_clean["cc_composition"] = [
        {"cc_code": "blockchain::CC_WRITE_GENESIS_RECORD_V0", "step": "1",
         "capability": "blockchain::CT_PURE_GENERATE_GENESIS_ID_V0", "kind": "CT",
         "operation": "COMPUTE", "consumes": "block", "produces": "genesis_id"},
        {"cc_code": "blockchain::CC_WRITE_GENESIS_RECORD_V0", "step": "2",
         "capability": "capability_side_effects::CS_MUTABLE_JSON_V0", "kind": "CS",
         "operation": "SET", "consumes": "genesis_id", "produces": "result_status"},
    ]
    assert not check_cc_composition(comp_clean, grounding), \
        f"clean CT→CS composition should pass: {check_cc_composition(comp_clean, grounding)}"
    print("  S6b cc_composition oracle: clean CT→CS composition passes ✓")

    comp_bad = dict(CLEAN_6B)
    comp_bad["cc_composition"] = [
        {"cc_code": "blockchain::CC_WRITE_GENESIS_RECORD_V0", "step": "1",
         "capability": "blockchain::CT_PURE_FABRICATED_NOWHERE_V0", "kind": "CT",
         "operation": "COMPUTE", "consumes": "x", "produces": "y"},                  # fabricated step
        {"cc_code": "blockchain::CC_WRITE_GENESIS_RECORD_V0", "step": "2",
         "capability": "blockchain::CC_FORM_BLOCK_V0", "kind": "CS",
         "operation": "CALL", "consumes": "y", "produces": "z"},                      # a CC as a step
        {"cc_code": "blockchain::CC_ORPHAN_NOT_ROUTED_V0", "step": "1",
         "capability": "blockchain::CT_PURE_GENERATE_GENESIS_ID_V0", "kind": "CT",
         "operation": "COMPUTE", "consumes": "a", "produces": "b"},                   # undeclared CC
    ]
    bad = [m for _, m in check_cc_composition(comp_bad, grounding)]
    assert any("CT_PURE_FABRICATED_NOWHERE_V0" in m and "neither declared" in m for m in bad), \
        f"must flag a fabricated composition step: {bad}"
    assert any("CC_FORM_BLOCK_V0" in m and "composes only CT/CS" in m for m in bad), \
        f"must flag a CC used as a composition step: {bad}"
    assert any("CC_ORPHAN_NOT_ROUTED_V0" in m and "not a declared CC" in m for m in bad), \
        f"must flag an undeclared composed CC: {bad}"
    print("  S6b cc_composition oracle: fabricated step + CC-as-step + undeclared CC rejected ✓")

    # ---- governing fence: out_of_scope oracle (deterministic, lexical) ----
    from ..evaluator.scope_oracle import check_scope_boundary
    OOS = {"out_of_scope": [{"item": "Slashing."}, {"item": "Rewards."},
                            {"item": "Chain reorganization (reorg)."}],
           "business_vocabulary": [{"term": "Chain"}, {"term": "Block"}, {"term": "Validator"}]}
    leak2 = {"business_processes": [
        {"process": "Slash Enforcement"}, {"process": "Reward Distribution"},
        {"process": "Consensus Loop Execution"}, {"process": "Genesis Bootstrap"}]}
    msgs = [m for _, m in check_scope_boundary("2", leak2, OOS)]
    assert any("business_processes[0]." in m for m in msgs), "must fence 'Slash Enforcement' (Slashing)"
    assert any("business_processes[1]." in m for m in msgs), "must fence 'Reward Distribution' (Rewards)"
    assert not any("[2]." in m or "[3]." in m for m in msgs), "must NOT flag consensus/genesis"
    # the in-scope noun allowlist spares a legitimate 'chain' capability despite 'Chain reorganization'
    clean2 = {"business_processes": [{"process": "Commit Block To Canonical Chain"}]}
    assert not check_scope_boundary("2", clean2, OOS), "in-scope 'chain' must not trip the reorg fence"
    # S4 capability_graph, allowlist from entities
    oos4 = {"out_of_scope": [{"item": "Slashing."}],
            "entities": [{"entity": "Chain"}, {"entity": "Validator"}]}
    leak4 = {"capability_graph": [{"capability": "Slash a misbehaving validator"},
                                  {"capability": "Commit a proposed block"}]}
    h4 = [m for _, m in check_scope_boundary("4", leak4, oos4)]
    assert len(h4) == 1 and "capability_graph[0]." in h4[0], f"S4 fences slash only: {h4}"
    # no out_of_scope forwarded → no enforcement (no false halt on stages that never receive it)
    assert not check_scope_boundary("2", leak2, {}), "no out_of_scope forwarded → oracle no-ops"
    print("  scope oracle: fences deferred Slash/Reward at S2 + Slash at S4, spares in-scope chain ✓")

    print("\nSTRUCTURED DOSSIER STAGE PROOF OK ✓ — register-intent → renderer → document, "
          "structural oracle figure of merit, bounded handoff, S6b binding-FQDN integrity")
    return 0


if __name__ == "__main__":
    sys.exit(main())

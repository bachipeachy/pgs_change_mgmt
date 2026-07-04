"""Design Review Contract proof (§13) — engine certifies Part A; worker facilitates Part B (bounded).

Hermetic + deterministic. Proves: (1) Part A is a faithful projection of a `StageResult` across the
three readiness bands (READY / READY_WITH_WARNINGS / NOT_READY), inventing nothing; (2) a valid, bounded
Part B is carried; (3) the Part-B boundary oracle rejects any row that strays into engine-owned territory
(confidence / readiness / percentage / self-eval); (4) the optional `human_engagement` register is
ADVERTISED on every stage — in the shared authoring SYSTEM_PROMPT (all transports) and in the guided
stage package's expected_output.md (structured + free-form).

Run:  python -m pgs_change_mgmt.engine._design_review_selftest
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import design_review as dr
from .stage_package import _PART_B_ADVISORY, _expected_output_md
from ..worker._authoring import SYSTEM_PROMPT


@dataclass
class _SR:
    """A minimal StageResult stand-in — only the fields assemble_engine_certified reads."""
    stage: str = "6b"
    identity: dict = field(default_factory=dict)
    oracle_issues: list = field(default_factory=list)
    incomplete_sections: list = field(default_factory=list)
    unresolved_cells: list = field(default_factory=list)
    missing: list = field(default_factory=list)
    halt_reason: Any = None
    coverage: float = 1.0
    governed_coverage: float | None = None


def main() -> int:
    # 1 — Part A projection across the three readiness bands (pure projection of the StageResult)
    clean = dr.build_drc(_SR())
    assert clean.engine_certified.readiness == dr.READY, clean.engine_certified.readiness
    assert clean.human_engagement is None, "no worker Part B ⇒ human_engagement stays None (never fabricated)"
    warn = dr.build_drc(_SR(oracle_issues=["CC step binds an op not in the governed vocabulary"],
                            missing=["pipeline"]))
    assert warn.engine_certified.readiness == dr.READY_WITH_WARNINGS
    assert warn.engine_certified.unknowns, "warnings must surface classified unknowns"
    blocked = dr.build_drc(_SR(halt_reason="EMPTY_EMIT_PROJECTION", identity={"E_FABRICATION": 1}))
    assert blocked.engine_certified.readiness == dr.NOT_READY
    assert blocked.engine_certified.blocking, "an inadmissible stage must certify blocking facts"
    print("  Part A: READY / READY_WITH_WARNINGS / NOT_READY projected from StageResult; unknowns classified ✓")

    # 2 — a valid, bounded Part B is carried through build_drc
    good = dr.HumanEngagement(decisions=[dr.HumanDecision(
        question="Which subdomain owns genesis bootstrap?",
        why="ownership is a policy call PI/governance cannot settle",
        tradeoffs="place it in chain vs a new bootstrap subdomain")])
    assert dr.validate_human_engagement(good) == [], "a clean Part B must pass the boundary oracle"
    carried = dr.build_drc(_SR(), human_engagement=good)
    assert carried.human_engagement and carried.human_engagement.decisions, "a valid Part B must be carried"
    print("  Part B: a bounded question (question/why/tradeoffs) passes the oracle and is carried ✓")

    # 3 — the boundary oracle rejects engine-owned assertions and empty questions
    for bad in ("I am confident this is READY_FOR_NEXT_STAGE", "about 80% sure", "readiness is high"):
        strayed = dr.HumanEngagement(decisions=[dr.HumanDecision(question="ok to proceed?", why=bad)])
        assert dr.validate_human_engagement(strayed), f"boundary oracle must reject {bad!r}"
    assert dr.validate_human_engagement(
        dr.HumanEngagement(decisions=[dr.HumanDecision(question="", why="x")])), "empty question must be rejected"
    print("  Part B boundary: confidence/readiness/percentage/self-eval + empty question all rejected ✓")

    # 4 — the optional register is advertised on every stage, in both transports
    assert "human_engagement" in SYSTEM_PROMPT and "Part B" in SYSTEM_PROMPT, \
        "the shared authoring SYSTEM_PROMPT must advertise the Part-B register (all transports)"
    struct_md = _expected_output_md({"structured": True, "registers": {}})
    free_md = _expected_output_md({"structured": False, "emit_fields": []})
    assert _PART_B_ADVISORY in struct_md and _PART_B_ADVISORY in free_md, \
        "the guided expected_output.md must carry the Part-B advisory (structured + free-form)"
    print("  Advertised: human_engagement in the shared SYSTEM_PROMPT + guided expected_output.md ✓")

    # 5 — the guided ingress must ADMIT the Part-B register on any stage (advertised → must be accepted).
    #     Regression lock: without the diagnostic allowlist the ingress rejected `human_engagement` as an
    #     undeclared register, so Part B could never reach the engine (found live on the chain S2 import).
    from ..worker.interactive_ingress import InteractiveIngressValidator
    v = InteractiveIngressValidator.__new__(InteractiveIngressValidator)
    v.schema = {"structured": True, "schema_hash": "test", "registers": {
        "entities": {"columns": ["entity"], "required": True, "business_language": False,
                     "bl_columns": None, "evidence_columns": [], "enums": {}}}}
    v.grounding_spec = {"validation_mode": "strict"}
    good = v.validate({"entities": [], "human_engagement": [
        {"question": "own balance state?", "why": "policy call", "tradeoffs": "duplication vs authority"}]})
    assert good.ok, f"ingress must admit the Part-B register: {good.issues}"
    bad = v.validate({"entities": [], "bogus_register": [{}]})
    assert not bad.ok and any("bogus_register" in i for i in bad.issues), \
        "ingress must still reject a genuinely-undeclared register"
    print("  Ingress: admits human_engagement on any stage; still rejects undeclared registers ✓")

    print("\nDESIGN REVIEW CONTRACT PROOF OK ✓ — engine certifies Part A (3 readiness bands, classified "
          "unknowns); worker facilitates a bounded Part B; the boundary oracle holds; the optional "
          "human_engagement register is advertised on every stage across transports.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
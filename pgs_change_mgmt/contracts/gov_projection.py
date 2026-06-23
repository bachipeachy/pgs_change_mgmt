"""gov_projection — the engine's boundary object and its schema.

A `gov_projection` is the governed, lossless handoff one pipeline stage emits for the
next. It is the single object that crosses every seam of the engine (worker → engine,
stage → stage, engine → evaluator). Everything the engine coordinates is expressed as a
`gov_projection` or a transform over one.

Two things live here:

  1. The SCHEMA — `GOV_PROJECTION_SCHEMA`: the declared set of handoff fields, each with
     its producing stage, declared consumers, and justification. Mirrors the compiler's
     discipline: a field exists only because a declared downstream stage consumes it; a
     field with no consumer is inadmissible (it stays in the stage's narrative, never
     forwarded).

  2. The INSTANCE — `GovProjection`: the typed object a stage actually emits, checkable
     against the schema for that stage (lossless-handoff and undeclared-field checks).

FQDN-pointer fields carry FQDN strings re-resolved via a GroundingProvider at
consume-time — never quoted from prior-stage prose (that is what kills drift).

Promoted from the Phase-0 experiment `change_agent/soa_contracts.py`; the term
"SOA" / "stage output artifact" is retired in favour of `gov_projection`. See
pgs_workspace/doc/parkinglot/stage_output_artifact_model.md §5.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

CLOSURE = "CLOSURE"  # sentinel consumer: CR closure / next-CR, outside the staged pipeline


@dataclass(frozen=True)
class GovProjectionField:
    """One schema row: a handoff field and its provenance."""

    field: str
    producer: str
    consumers: tuple[str, ...]
    justification: str
    fqdn_pointer: bool = False  # value(s) carry FQDN(s) re-resolved via grounding, not quoted prose


# The schema. Order is by producing stage. A field exists only because a declared
# downstream stage consumes it (see validate_schema).
GOV_PROJECTION_SCHEMA: tuple[GovProjectionField, ...] = (
    # ---- S1 Change Request (Clarification & Fact Capture — interrogation, not authoring) ----
    # Consumer assignments validated by a full all-structured run (1→7, 2026-06-22).
    GovProjectionField("cr_type", "1", ("3", "4"), "S1 §1 CR Type — selects analysis depth"),
    GovProjectionField("business_vocabulary", "1", ("2",), "S1 §2 Business Vocabulary — governed definitions that ground S2 discovery"),
    GovProjectionField("requested_outcomes", "1", ("8",), "S1 §3 Requested Outcomes — S8 acceptance boundary (was desired_outcome)"),
    GovProjectionField("known_facts", "1", ("2",), "S1 §4 Known Facts — business truths (human-authoritative; certainty-tagged)"),
    GovProjectionField("system_beliefs", "1", ("2",), "S1 §5 Existing-System Beliefs — Stage-2 discovery targets (verified, never trusted)"),
    GovProjectionField("assumptions", "1", ("3",), "S1 §6 Assumptions — S3 analysis must validate"),
    GovProjectionField("constraints", "1", ("4",), "S1 §7 Constraints — feed S4 constraint register"),
    GovProjectionField("business_invariants", "1", ("3", "4"), "S1 §8 Business Invariants — always-true business truths; S3 uses them to eliminate inadmissible designs"),
    GovProjectionField("lifecycle_states", "1", ("2", "3"), "S1 §9 Lifecycle States — states each core object moves through; S2 models, S3 scopes transitions"),
    GovProjectionField("business_events", "1", ("2", "3"), "S1 §10 Business Events — business moments the domain must recognize; S2 models, S3 scopes"),
    GovProjectionField("authority_boundaries", "1", ("3", "4"), "S1 §11 Authority Boundaries — who is authoritative for each object; drives S3 REUSE-vs-AUTHOR_NEW"),
    GovProjectionField("out_of_scope", "1", ("5", "6"), "S1 §12 Out of Scope — deferred to future CRs (explicit release boundary)"),
    GovProjectionField("governance_scope", "1", ("2", "6"), "S1 §13 Governance Scope Declared by This CR (with relationship)"),
    GovProjectionField("clarification_requests", "1", (CLOSURE,), "S1 §14 Clarification Requests — resolved by human/discovery at the S1 gate (agent asks, does not guess)"),
    GovProjectionField("acceptance_criteria", "1", ("8",), "S1 §15 Acceptance Criteria — S8 acceptance boundary (business-observable)"),
    # ---- S2 Domain Model Discovery (Discovery Projection — lossless, every register forwarded) ----
    # Consumer assignments govern which downstream stage loads each register from S2's handoff;
    # validated by a full all-structured run (1→7, 2026-06-22).
    GovProjectionField("entities", "2", ("4",), "S2 §1 Business Entities"),
    GovProjectionField("entity_attributes", "2", ("4", "6b"), "S2 §1 Entity Attributes (attribute-level: identity S5, storage S6b)"),
    GovProjectionField("business_processes", "2", ("4",), "S2 §2 Business Processes"),
    GovProjectionField("process_steps", "2", ("6b",), "S2 §2 Process Steps (workflow nodes at S6b)"),
    GovProjectionField("belief_verification", "2", ("3",), "S2 §3 Belief Verification — VERIFIED/NOT_FOUND/INSUFFICIENT per S1 System Belief (bounded-discovery STOP ledger)"),
    GovProjectionField("pps_baseline_fqdns", "2", ("3", "4"), "S2 §4 PPS Baseline — artifacts that verify a belief or serve an outcome (Fit observational, no reuse decision)", True),
    GovProjectionField("gaps", "2", ("3",), "S2 §5 Gap Analysis — what is missing"),
    GovProjectionField("architectural_observations", "2", ("3",), "S2 §6 Architectural Observations — facts feeding S3 extend-vs-new"),
    GovProjectionField("discovery_concerns", "2", ("3",), "S2 §7 Discovery Concerns — primary feed into S3 (CONCERN_TRACEABILITY)"),
    GovProjectionField("open_questions", "2", ("3",), "S2 §8 Open Questions for Stage 3 (blocker list, not inventory; may be empty)"),
    # ---- S3 Analysis Loop (Decision stage: REUSE/EXTEND/AUTHOR_NEW). analysis_findings /
    #      verification_results / impact_analysis are doc-only audit registers (not forwarded). ----
    GovProjectionField("authoring_decisions", "3", ("4",), "S3 §5 Authoring Decisions — REUSE/EXTEND/AUTHOR_NEW per capability (supersedes reusable_fqdns + must_author)"),
    GovProjectionField("dependency_discoveries", "3", ("4",), "S3 §3 Dependency Discoveries — feeds S4 dependency graph + authoring order", True),
    GovProjectionField("placement_decision", "3", ("4",), "S3 §6 Subdomain Placement Decision"),
    GovProjectionField("saturation", "3", ("4",), "S3 §7 Saturation Assessment"),
    # ---- S4 Business Model (the hub) ----
    GovProjectionField("actors", "4", ("5",), "S4 §1 Discovery Summary — Actors"),
    GovProjectionField("bm_entities", "4", ("5",), "S4 §1 Discovery Summary — Entities"),
    GovProjectionField("events", "4", ("5", "6"), "S4 §1 Discovery Summary — Events"),
    GovProjectionField("capability_graph", "4", ("5",), "S4 §2 Capability Graph"),
    GovProjectionField("dependency_graph", "4", ("6",), "S4 §3 Dependency Graph"),
    GovProjectionField("constraint_register", "4", ("5", "6"), "S4 §4 Constraint Register"),
    GovProjectionField("gap_register", "4", ("6b",), "S4 §5 Gap Register"),
    GovProjectionField("design_decisions", "4", ("6b",), "S4 §6 Design Decisions Register"),
    GovProjectionField("authoring_scope", "4", ("6", "6b"), "S4 §7 Authoring Scope"),
    # ---- S5 Business Intent ----
    GovProjectionField("scope_boundary", "5", ("6", "6b"), "S5 §2 Scope Boundary"),
    GovProjectionField("invariants", "5", ("6", "6b"), "S5 §5 Business Invariants"),
    GovProjectionField("actions", "5", ("6b",), "S5 §6 Business Actions"),
    GovProjectionField("provisional_codes", "5", ("6b",), "S5 §7–10 AC/IN/WF/CC (provisional codes)"),
    GovProjectionField("cross_subdomain_refs", "5", ("6",), "S5 §11 Cross-Subdomain References"),
    # ---- S6 Governance Intent ----
    GovProjectionField("ownership", "6", ("6b",), "S6 §3 Subdomain Boundary — ownership"),
    GovProjectionField("storage_governance", "6", ("6b",), "S6 §5 Storage Governance Requirements"),
    GovProjectionField("cross_subdomain_deps", "6", ("6b",), "S6 §6 Cross-Subdomain Dependency Declaration"),
    GovProjectionField("pps_artifacts_requiring_action", "6", ("6b",), "S6 §8 PPS Artifacts Requiring Action", True),
    # ---- S6b Design Intent ----
    GovProjectionField("new_artifacts", "6b", ("7",), "S6b §4 Artifact Family Mapping — New Artifacts (binding FQDNs)", True),
    GovProjectionField("existing_inventory", "6b", ("7",), "S6b §3 Artifact Inventory — Existing", True),
    GovProjectionField("rb_declarations", "6b", ("7",), "S6b §4c Runtime Binding Declarations"),
    GovProjectionField("execution_topology", "6b", ("7",), "S6b §5 Execution Topology"),
    GovProjectionField("artifact_summary", "6b", ("7",), "S6b §11 Artifact Summary"),
    # ---- S7 Authoring Mandate ----
    GovProjectionField("build_order", "7", ("8",), "S7 §1 Build Dependency Order"),
    GovProjectionField("critical_path", "7", ("8",), "S7 §2 Critical Path"),
    GovProjectionField("mandate_artifact_summary", "7", ("8",), "S7 §3 Artifact Summary"),
    GovProjectionField("field_declarations", "7", ("8",), "S7 §4 Subdomain Field Declarations"),
    # ---- S8 Authoring Manifest (terminal — feeds CR closure / next CR) ----
    GovProjectionField("deviations", "8", (CLOSURE,), "S8 §1 Approved Deviations"),
    GovProjectionField("discoveries", "8", (CLOSURE,), "S8 §2 Architectural Discoveries"),
    GovProjectionField("as_designed_vs_built", "8", (CLOSURE,), "S8 §7 As-Designed vs As-Built Reconciliation"),
    GovProjectionField("dividend_metrics", "8", (CLOSURE,), "S8 §8 Governed Evolution Metrics"),
    GovProjectionField("future_cr_candidates", "8", (CLOSURE,), "S8 §6 Future CR Candidates"),
)


def fields_emitted_by(stage: str) -> list[GovProjectionField]:
    """Schema fields this stage emits in its gov_projection."""
    return [f for f in GOV_PROJECTION_SCHEMA if f.producer == stage]


def fields_consumed_by(stage: str) -> list[GovProjectionField]:
    """Bounded context: upstream fields that declare this stage as a consumer."""
    return [f for f in GOV_PROJECTION_SCHEMA if stage in f.consumers]


def validate_schema() -> list[str]:
    """Admissibility: every field must declare at least one consumer.

    Returns the list of orphan field names (none ⇒ schema valid).
    """
    return [f.field for f in GOV_PROJECTION_SCHEMA if not f.consumers]


@dataclass(frozen=True)
class GovProjection:
    """A stage's emitted handoff instance — the boundary object that crosses seams.

    `values` maps schema field name → value. FQDN-pointer fields carry FQDN strings to be
    re-resolved via a GroundingProvider at consume-time, never quoted from prose.
    """

    stage: str
    values: Mapping[str, Any]

    def field_names(self) -> set[str]:
        return set(self.values)

    def missing_fields(self) -> list[str]:
        """Schema fields this stage must emit but did not — the lossless-handoff check."""
        return [f.field for f in fields_emitted_by(self.stage) if f.field not in self.values]

    def extra_fields(self) -> list[str]:
        """Emitted fields not declared in this stage's schema — undeclared handoff."""
        declared = {f.field for f in fields_emitted_by(self.stage)}
        return [k for k in self.values if k not in declared]

    def fqdn_pointer_fields(self) -> list[str]:
        """Emitted fields whose values are FQDN pointers (re-resolved via grounding)."""
        pointers = {f.field for f in fields_emitted_by(self.stage) if f.fqdn_pointer}
        return [k for k in self.values if k in pointers]


if __name__ == "__main__":
    orphans = validate_schema()
    assert not orphans, f"orphan gov_projection fields (no consumer): {orphans}"
    stages = ["1", "2", "3", "4", "5", "6", "6b", "7", "8"]
    print("gov_projection schema — fields per stage and bounded inputs:\n")
    for s in stages:
        emits = [f.field for f in fields_emitted_by(s)]
        ins = [(f.producer, f.field) for f in fields_consumed_by(s)]
        print(f"S{s:3} emits {len(emits):2}: {', '.join(emits)}")
        print(f"     reads {len(ins):2}: {ins}\n")
    print("schema valid: every field has a consumer ✓")

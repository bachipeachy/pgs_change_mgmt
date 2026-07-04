"""Design Review Contract (DRC) — the human-facing projection of a stage's reasoning boundaries.

Two separately-owned sections (`engine certifies facts, worker facilitates design, human decides`):

  A. **Engine-Certified** (authoritative, deterministic) — a *projection* of what the engine already
     computed for the stage (`StageResult`: oracle verdicts, coverage, declared holes, blocking). No new
     reasoning; the engine only certifies facts it already established.
  B. **Human-Engagement** (bounded worker) — only questions · why · tradeoffs · PI-unobtainable info. NO
     confidence score, NO readiness, NO self-evaluation (a `drc_oracle` enforces this boundary).

The DRC is **diagnostic only**: it never changes stage behaviour, gates, or sequencing.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# --- controlled vocabularies -------------------------------------------------------------------------

# Readiness — engine-certified only. Tells the human whether the stage's output is safe to carry forward.
READY = "READY_FOR_NEXT_STAGE"
READY_WITH_WARNINGS = "READY_WITH_WARNINGS"
NOT_READY = "NOT_READY"

# Unknown classification — tells the human whether more protocol grounding is possible (PI) or whether
# architectural judgement is required. The whole point of the DRC: never a vague "not sure".
PI_RESOLVABLE = "PI_RESOLVABLE"      # the answer is in the snapshot/governance — a PI query resolves it
HUMAN_DECISION = "HUMAN_DECISION"    # business policy / preference / ambiguous requirement — only a human
AUTHORING_GAP = "AUTHORING_GAP"      # this authoring stage left something undeclared/inconsistent
GOVERNANCE_GAP = "GOVERNANCE_GAP"    # a governed artifact/rule is missing (may be PI-resolvable if it exists)
FUTURE_STAGE = "FUTURE_STAGE"        # legitimately deferred to a later stage


# --- schema ------------------------------------------------------------------------------------------

@dataclass
class Unknown:
    description: str
    classification: str          # one of the vocab above
    pi_resolvable: bool


@dataclass
class EngineCertified:
    """Authoritative facts — produced ONLY by the engine, projected from StageResult + grounding log."""
    readiness: str
    oracle_verdicts: list[str] = field(default_factory=list)
    grounding_coverage: float | None = None
    pi_queries_executed: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    unknowns: list[Unknown] = field(default_factory=list)
    blocking: list[str] = field(default_factory=list)


@dataclass
class HumanDecision:
    question: str
    why: str
    tradeoffs: str = ""
    pi_unobtainable: bool = True     # Part B exists precisely because PI/governance cannot answer it


@dataclass
class HumanEngagement:
    """Bounded worker facilitation — questions only. Never confidence, readiness, or a self-verdict."""
    decisions: list[HumanDecision] = field(default_factory=list)


@dataclass
class DRC:
    stage: str
    engine_certified: EngineCertified
    human_engagement: HumanEngagement | None = None      # None ⇒ worker surfaced nothing (never fabricated)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# --- deterministic classification --------------------------------------------------------------------

def _classify_oracle_issue(text: str) -> tuple[str, bool]:
    """Classify a structural-oracle finding by its content. Deterministic, keyed on the issue phrasing."""
    t = text.lower()
    if "governed vocabulary" in t or "core.policy.operations" in t:
        return AUTHORING_GAP, False           # design chose an op the CS contract doesn't declare
    if "collision" in t or "already exists" in t:
        return AUTHORING_GAP, False           # re-minted an existing FQDN
    if "misspell" in t or "near-duplicate" in t:
        return AUTHORING_GAP, False           # typo mints a second artifact
    if "not in any stage 6b register" in t or "does not introduce" in t:
        return AUTHORING_GAP, False
    if "referenced" in t and ("declared" in t or "snapshot" in t):
        return AUTHORING_GAP, False           # referenced⇒declared failure — this stage's gap
    return GOVERNANCE_GAP, True               # otherwise a governed rule/artifact may resolve it via PI


def classify_unknown(source: str, text: str) -> Unknown:
    """Map an engine-observed gap to the DRC taxonomy. `source` is where the fact came from."""
    if source == "unresolved_cell":
        # a declared governed hole the worker could not resolve — awaits human clarification
        return Unknown(text, HUMAN_DECISION, False)
    if source == "incomplete_section":
        return Unknown(text, HUMAN_DECISION, False)     # a required human-authored section left blank
    if source == "missing_handoff":
        return Unknown(text, AUTHORING_GAP, False)      # a declared emit-field the stage did not produce
    if source == "oracle_issue":
        cls, pi = _classify_oracle_issue(text)
        return Unknown(text, cls, pi)
    return Unknown(text, AUTHORING_GAP, False)


# --- Part A assembler: project the StageResult (the engine certifies facts) --------------------------

def assemble_engine_certified(sr: Any, pi_queries: list[str] | None = None) -> EngineCertified:
    """Project a `StageResult` into the authoritative DRC section. Pure projection — reads only fields the
    engine already computed; invents nothing. `pi_queries` is the stage's grounding log (ops executed)."""
    fabricated = int(getattr(sr, "identity", {}) .get("E_FABRICATION", 0)) if getattr(sr, "identity", None) else 0
    oracle_issues = list(getattr(sr, "oracle_issues", []) or [])
    incomplete = list(getattr(sr, "incomplete_sections", []) or [])
    unresolved = list(getattr(sr, "unresolved_cells", []) or [])
    missing = list(getattr(sr, "missing", []) or [])
    halt = getattr(sr, "halt_reason", None)

    blocking: list[str] = []
    if halt:
        blocking.append(f"inadmissible: {halt}")
    if fabricated:
        blocking.append(f"fabrication detected ({fabricated})")

    if blocking:
        readiness = NOT_READY
    elif oracle_issues or incomplete or unresolved or missing:
        readiness = READY_WITH_WARNINGS
    else:
        readiness = READY

    unknowns = (
        [classify_unknown("unresolved_cell", u) for u in unresolved]
        + [classify_unknown("incomplete_section", s) for s in incomplete]
        + [classify_unknown("missing_handoff", m) for m in missing]
        + [classify_unknown("oracle_issue", o) for o in oracle_issues]
    )

    return EngineCertified(
        readiness=readiness,
        oracle_verdicts=oracle_issues or ["clean — no structural-oracle findings"],
        grounding_coverage=getattr(sr, "governed_coverage", None) if getattr(sr, "governed_coverage", None) is not None
        else getattr(sr, "coverage", None),
        pi_queries_executed=list(pi_queries or []),
        missing_evidence=unresolved + incomplete + missing,
        unknowns=unknowns,
        blocking=blocking,
    )


def build_drc(sr: Any, *, pi_queries: list[str] | None = None,
              human_engagement: HumanEngagement | None = None) -> DRC:
    """Assemble the full DRC for a stage: engine-certified Part A (projection) + optional bounded Part B."""
    return DRC(stage=str(getattr(sr, "stage", "?")),
               engine_certified=assemble_engine_certified(sr, pi_queries),
               human_engagement=human_engagement)


# --- Part B boundary oracle: the worker facilitates design, it does not self-evaluate ----------------

import re as _re

# A Part-B item may not assert engine-owned facts (confidence, readiness, a self-verdict). This keeps the
# "engine certifies facts, worker facilitates design" boundary from eroding into LLM self-assessment.
_FORBIDDEN = _re.compile(
    r"\bconfiden(?:ce|t)\b|\breadiness\b|\bready_for_next_stage\b|\bnot_ready\b|\bready_with_warnings\b|"
    r"\d{1,3}\s*%|\bi\s+am\s+(?:sure|certain|confident)\b|\bi\s+(?:believe|think)\s+(?:this|the|it)\b",
    _re.IGNORECASE)


def validate_human_engagement(he: HumanEngagement | None) -> list[str]:
    """Reject any Part-B content that strays into engine-owned territory (confidence / readiness /
    self-evaluation) or is not a genuine human question. Returns issue strings (empty ⇒ clean)."""
    issues: list[str] = []
    if he is None:
        return issues
    for i, d in enumerate(he.decisions, 1):
        for fieldname, val in (("question", d.question), ("why", d.why), ("tradeoffs", d.tradeoffs)):
            m = _FORBIDDEN.search(str(val or ""))
            if m:
                issues.append(f"decision {i} .{fieldname}: contains engine-owned assertion "
                              f"{m.group(0)!r} — Part B is questions only (no confidence/readiness/self-eval)")
        if not str(d.question or "").strip():
            issues.append(f"decision {i}: empty question")
    return issues


# --- rendering: the brief's human-readable layout (two clearly-owned sections) ------------------------

def render(drc: DRC) -> str:
    ec = drc.engine_certified
    L = ["=" * 54, "DESIGN REVIEW CONTRACT (DRC)", f"Stage: {drc.stage}", "=" * 54, "",
         "## A. ENGINE-CERTIFIED (authoritative)", "",
         "Stage Readiness", "---------------", ec.readiness, "",
         "Oracle Verdicts", "---------------"]
    L += [f"  - {v}" for v in ec.oracle_verdicts]
    cov = "n/a" if ec.grounding_coverage is None else f"{ec.grounding_coverage:.0%}"
    L += ["", "Grounding", "---------", f"Coverage: {cov}", "PI Executed:"]
    L += [f"  ✓ {q}" for q in ec.pi_queries_executed] or ["  (none recorded)"]
    L += ["", "Remaining Unknowns", "------------------"]
    if ec.unknowns:
        for i, u in enumerate(ec.unknowns, 1):
            L += [f"  {i}. {u.description}",
                  f"     classification: {u.classification}   pi_resolvable: {'yes' if u.pi_resolvable else 'no'}"]
    else:
        L.append("  None")
    L += ["", "Blocking", "--------"] + ([f"  - {b}" for b in ec.blocking] or ["  None"])
    L += ["", "Recommended Action", "------------------", {
        READY: "Proceed to the next stage.",
        READY_WITH_WARNINGS: "Review the warnings/unknowns before proceeding.",
        NOT_READY: "Resolve the blocking issues before proceeding.",
    }[ec.readiness]]

    L += ["", "## B. HUMAN-ENGAGEMENT (design facilitation — decisions for the human)", ""]
    he = drc.human_engagement
    if he and he.decisions:
        for i, d in enumerate(he.decisions, 1):
            L += [f"Decision {i}", f"  Question: {d.question}", f"  Why: {d.why}"]
            if d.tradeoffs:
                L.append(f"  Tradeoffs: {d.tradeoffs}")
            L.append(f"  PI-unobtainable: {'yes' if d.pi_unobtainable else 'no'}")
            L.append("")
    else:
        L += ["(no human decisions surfaced by the worker)", ""]
    return "\n".join(L)

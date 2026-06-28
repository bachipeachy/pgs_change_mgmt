"""SemanticEquivalenceOracle — ASSERT_ROUNDTRIP_EQUIVALENCE over the Compiler Semantic Interface.

The oracle proves the compiler is information-preserving up to semantic equivalence: a Forward IPM
(the declared model, from canonical frontmatter) and a Reverse IPM (the compiled model, reconstructed
from the evidence graph) must agree axis-by-axis.

HARD BOUNDARY (Patch 2): the oracle consumes ONLY two `IntermediateProtocolModel`s. It never imports
or inspects evidence graphs, frontmatter, or any compiler artifact directly — all substrate access
lives in the compiler-side CSI (`pgs_compiler.compiler.projections.{ipm,reverse}`). That keeps
verification a pure function of the IPM contract.

SELF-DESCRIBING AXES (Patch 3): each axis declares `name`, `version`, and three pure functions —
`extract(ipm)` (pull this axis's comparable data), `compare(forward, reverse)` (diff them), and
`explain(diff)` (render one difference). Future protocol concepts plug in as new `Axis` entries in
`AXES` with no change to the oracle engine.

Increment 1 ships the Identity and Workflow axes — structural identity + behavioral reconstruction,
the two that together demonstrate a true round trip while keeping the axes orthogonal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from pgs_compiler.compiler.projections.ipm import IntermediateProtocolModel


# ---- diff model -------------------------------------------------------------------------------

@dataclass(frozen=True)
class Diff:
    """One axis-level difference. `direction` ∈ {missing_in_reverse, missing_in_forward, mismatch}."""
    direction: str
    subject: str
    detail: str = ""


def _set_diff(forward: set, reverse: set, render: Callable[[Any], str]) -> list[Diff]:
    """Symmetric set difference rendered as Diffs — the shared primitive for set-shaped axes."""
    diffs = [Diff("missing_in_reverse", render(x)) for x in sorted(forward - reverse, key=render)]
    diffs += [Diff("missing_in_forward", render(x)) for x in sorted(reverse - forward, key=render)]
    return diffs


# ---- self-describing axis -------------------------------------------------------------------

@dataclass(frozen=True)
class Axis:
    name: str
    version: int
    extract: Callable[[IntermediateProtocolModel], Any]
    compare: Callable[[Any, Any], list[Diff]]
    explain: Callable[[Diff], str]
    # magnitude = the count of declared (forward) elements this axis compares — the denominator for
    # Semantic Coverage. Defaults to the size of the extracted collection; axes with nested structure
    # (Workflow) override it to count their atoms.
    magnitude: Callable[[IntermediateProtocolModel], int] | None = None


# Identity axis — the set of protocol identities (fqdn, kind).
def _identity_compare(fwd, rev) -> list[Diff]:
    return _set_diff(set(fwd), set(rev), lambda i: f"{i.fqdn} [{i.kind}]")


def _identity_explain(d: Diff) -> str:
    side = "reverse (compiled)" if d.direction == "missing_in_reverse" else "forward (declared)"
    return f"Identity {d.subject} absent from {side}"


IdentityAxis = Axis(
    name="Identity",
    version=1,
    extract=lambda ipm: set(ipm.identities),
    compare=_identity_compare,
    explain=_identity_explain,
    magnitude=lambda ipm: len(ipm.identities),
)


# Workflow axis — per-workflow start node, contained node set, and non-terminal routing.
def _workflow_compare(fwd: dict, rev: dict) -> list[Diff]:
    diffs: list[Diff] = []
    diffs += _set_diff(set(fwd), set(rev), str)          # presence of the workflows themselves
    for wf in sorted(set(fwd) & set(rev)):
        f, r = fwd[wf], rev[wf]
        if f.start_node != r.start_node:
            diffs.append(Diff("mismatch", wf, f"start_node declared={f.start_node} compiled={r.start_node}"))
        diffs += _set_diff(set(f.nodes), set(r.nodes), lambda i: f"{wf}:{i.fqdn}[{i.kind}]")
        diffs += _set_diff(set(f.routing), set(r.routing),
                           lambda t: f"{wf}: {t.source} --{t.outcome}--> {t.target}")
    return diffs


def _workflow_explain(d: Diff) -> str:
    if d.direction == "mismatch":
        return f"Workflow {d.subject}: {d.detail}"
    side = "reverse (compiled)" if d.direction == "missing_in_reverse" else "forward (declared)"
    return f"Workflow element {d.subject} absent from {side}"


WorkflowAxis = Axis(
    name="Workflow",
    version=1,
    extract=lambda ipm: {w.fqdn: w for w in ipm.workflows},
    compare=_workflow_compare,
    explain=_workflow_explain,
    # atoms: each workflow + its start node + its contained nodes + its routing edges.
    magnitude=lambda ipm: sum(2 + len(w.nodes) + len(w.routing) for w in ipm.workflows),
)


def _set_axis(name: str, version: int, extract: Callable[[Any], Any],
              render: Callable[[Any], str], *, preservation: bool = False) -> Axis:
    """Build a set-shaped axis.

    Two equivalence modes. `exact` (default): the forward and reverse sets must be identical — the
    right invariant for axes that are 1:1 projections (Identity, Workflow, Composition, Bindings,
    Routing). `preservation`: declared ⊆ compiled — the right invariant for a *derived* axis whose
    compiled form is a closure the compiler synthesizes beyond what artifacts declare (Authority:
    GOVERNED_BY is a governance closure). Preservation flags only declarations the compiler dropped;
    compiler-added derived elements are expected, not failures.
    """
    def compare(f: set, r: set) -> list[Diff]:
        if preservation:
            return [Diff("not_preserved", render(x)) for x in sorted(f - r, key=render)]
        return _set_diff(f, r, render)

    def explain(d: Diff) -> str:
        if d.direction == "not_preserved":
            return f"{name}: declared {d.subject} not preserved in the compiled snapshot"
        side = "reverse (compiled)" if d.direction == "missing_in_reverse" else "forward (declared)"
        return f"{name} {d.subject} absent from {side}"

    return Axis(
        name=name, version=version,
        extract=lambda ipm: set(extract(ipm)),
        compare=compare,
        explain=explain,
        magnitude=lambda ipm: len(set(extract(ipm))),
    )


CapabilityCompositionAxis = _set_axis(
    "Capability Composition", 1, lambda ipm: ipm.compositions,
    lambda c: f"{c.cc} #{c.pipeline_index} {c.step} → {c.target} [{c.kind}]")

BindingsAxis = _set_axis(
    "Bindings", 1, lambda ipm: ipm.bindings,
    lambda b: f"{b.source} --{b.relation}--> {b.target}")

RoutingAxis = _set_axis(
    "Routing", 1, lambda ipm: ipm.step_routings,
    lambda r: f"{r.cc}:{r.step} {r.outcome}→{r.disposition}")

# Authority is a DERIVED axis: GOVERNED_BY is a governance closure the compiler synthesizes beyond
# declarations. The governing rule — derived semantic axes may EXPAND but may not ERASE authored
# governance intent — is exactly preservation (declared ⊆ compiled): the compiler may add governance,
# never drop an authored governed_by.
AuthorityAxis = _set_axis(
    "Authority", 1, lambda ipm: ipm.authority,
    lambda a: f"{a.artifact} GOVERNED_BY {a.governed_by}", preservation=True)


# Definitional axes (Compilation Fidelity): the compiled frontmatter.core faithfully carries the
# authored definition. Exact equality — the compiler normalizes the machine block, it must not alter it.
EntitiesAxis = _set_axis(
    "Entities", 1, lambda ipm: ipm.attributes,
    lambda a: f"{a.entity}.{a.name}:{a.type}{'?' if a.optional else ''}"
              f"{('['+'|'.join(a.enum)+']') if a.enum else ''} card={a.cardinality}")

LifecycleAxis = _set_axis(
    "Lifecycle", 1, lambda ipm: ipm.lifecycles,
    lambda l: f"{l.entity}.{l.field}: {l.initial}→{'→'.join(l.stages)}⊣{l.terminal}")

RelationshipsAxis = _set_axis(
    "Relationships", 1, lambda ipm: ipm.relationships,
    lambda r: f"{r.entity}.{r.name} ({r.cardinality}) via {r.field} → {r.target}")

InvariantsAxis = _set_axis(
    "Invariants", 1, lambda ipm: ipm.invariants,
    lambda i: f"{i.owner} [{i.invariant_id}]: {i.constraint}")


# The axis registry — future protocol concepts extend the oracle by appending here.
AXES: tuple[Axis, ...] = (
    IdentityAxis, WorkflowAxis, CapabilityCompositionAxis, BindingsAxis, RoutingAxis, AuthorityAxis,
    EntitiesAxis, LifecycleAxis, RelationshipsAxis, InvariantsAxis,
)


# ---- oracle report ---------------------------------------------------------------------------

@dataclass
class AxisResult:
    name: str
    version: int
    ok: bool
    issues: list[str] = field(default_factory=list)
    magnitude: int = 0                      # declared elements compared (coverage denominator)
    coverage: float = 1.0                   # fraction of declared elements that round-tripped


@dataclass
class OracleReport:
    ipm_version: int
    structure_id: str
    results: list[AxisResult]

    @property
    def ok(self) -> bool:
        return all(r.ok for r in self.results)

    def issues(self) -> list[str]:
        return [f"ASSERT_ROUNDTRIP_EQUIVALENCE[{r.name}]: {i}"
                for r in self.results for i in r.issues]

    @property
    def coverage(self) -> float:
        """Overall Semantic Coverage — declared atoms that round-tripped, weighted across axes."""
        total = sum(r.magnitude for r in self.results)
        if total == 0:
            return 1.0
        matched = sum(max(0, r.magnitude - len(r.issues)) for r in self.results)
        return matched / total

    def coverage_map(self) -> str:
        """A structured semantic coverage map — per-axis PASS/FAIL, coverage %, plus an Overall roll-up.

        This is the diagnostic surface: a regression localizes to one axis (and its coverage drop)
        rather than collapsing the whole assertion to a single pass/fail.
        """
        lines = [f"ASSERT_ROUNDTRIP_EQUIVALENCE  (IPM v{self.ipm_version}, structure={self.structure_id})"]
        rows = [(r.name, "PASS" if r.ok else "FAIL", r.coverage, len(r.issues)) for r in self.results]
        rows.append(("Overall", "PASS" if self.ok else "FAIL", self.coverage, 0))
        for i, (name, status, cov, n) in enumerate(rows):
            conn = "└──" if i == len(rows) - 1 else "├──"
            detail = f"  ({n} diff{'s' if n != 1 else ''})" if n else ""
            lines.append(f"{conn} {name:<24} {status}  {cov * 100:5.1f}%{detail}")
        return "\n".join(lines)


def assert_roundtrip_equivalence(forward: IntermediateProtocolModel,
                                 reverse: IntermediateProtocolModel,
                                 *, axes: tuple[Axis, ...] = AXES) -> OracleReport:
    """Compare two IPMs axis-by-axis. The report is green iff every axis is equivalent.

    The two models must share an IPM version (the contract they speak); a version skew is itself a
    failure, surfaced as a synthetic axis so the oracle never silently compares incompatible models.
    """
    results: list[AxisResult] = []
    if forward.ipm_version != reverse.ipm_version:
        results.append(AxisResult("IpmVersion", 0, False,
                                  [f"version skew: forward={forward.ipm_version} reverse={reverse.ipm_version}"]))
        return OracleReport(forward.ipm_version, forward.structure_id, results)

    for axis in axes:
        diffs = axis.compare(axis.extract(forward), axis.extract(reverse))
        mag = axis.magnitude(forward) if axis.magnitude else 0
        coverage = 1.0 if mag == 0 else max(0.0, 1.0 - len(diffs) / mag)
        results.append(AxisResult(axis.name, axis.version, not diffs,
                                  [axis.explain(d) for d in diffs], magnitude=mag, coverage=coverage))
    return OracleReport(forward.ipm_version, forward.structure_id, results)

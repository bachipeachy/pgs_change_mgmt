"""Pipeline 3 — Execution Validation (generic, CR-transparent).

    candidate snapshot  →  execute the CR's declared acceptance scenario  →  observe  →  compare  →  evidence

The CR owns the *expectation* (an `acceptance_scenario` artifact in its dossier); this engine owns the
*mechanism*. It never guesses workflows, payloads, or success criteria, and it has zero domain knowledge:
an observation only *resolves an address and compares a value* (Patch 2). Consumed by the thin `validate`
CLI; the whole thing is in-process (no CLI-to-CLI, Patch 4).

Address grammar for references (payloads) and observations, over the protocol surface only:
    $.steps.<id>.surface.<path>     — a field of the workflow's result surface at step <id>
    $.steps.<id>.store.<store>.<path>   — state of a declared store after step <id> (…​.count on a list)
"""
from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from . import compilation_unit as cu
from . import expression
from .construction_model import build


# ─────────────────────────── evidence model (Patch 5: lives outside the snapshot) ──────────────────

@dataclass
class StepOutcome:
    step: str
    workflow: str
    outcome: str
    expect_outcome: str
    passed: bool
    satisfies: list[str] = field(default_factory=list)


@dataclass
class ObservationOutcome:
    address: str
    expected: Any
    actual: Any
    passed: bool
    satisfies: list[str] = field(default_factory=list)


@dataclass
class CriterionOutcome:
    id: str
    statement: str
    satisfied_by: list[str]            # step/observation refs that satisfy this criterion
    proven: bool                       # every satisfying element passed (and there is at least one)


@dataclass
class ValidationReport:
    verdict: str                       # PASS | FAIL
    subject: str
    scenario_code: str
    objective: str
    construction: dict
    steps: list[StepOutcome] = field(default_factory=list)
    observations: list[ObservationOutcome] = field(default_factory=list)
    criteria: list[CriterionOutcome] = field(default_factory=list)   # the Acceptance Intent, proven
    candidate_snapshot: str = ""
    timestamp: str = ""

    def to_dict(self) -> dict:
        return {
            "status": "EXECUTION_VALIDATED" if self.verdict == "PASS" else "EXECUTION_INVALID",
            "verdict": self.verdict,
            "subject": self.subject,
            "scenario_code": self.scenario_code,
            "objective": self.objective,
            "candidate_snapshot": self.candidate_snapshot,
            "construction": self.construction,
            "acceptance_intent": [vars(c) for c in self.criteria],
            "steps": [vars(s) for s in self.steps],
            "observations": [vars(o) for o in self.observations],
            "timestamp": self.timestamp,
        }


# ─────────────────────────── construction service (in-process admit) ───────────────────────────────

def admit_candidate(projection: Path, *, domain: str, subdomain: str, workspace: Path,
                    out_workspace: Path) -> cu.Persisted:
    """Construct + admit the CR delta and persist a full isolated candidate snapshot. In-process — the
    same `build` + `persist_test_snapshot` the admit CLI uses, called directly (no subprocess)."""
    res = build(projection, domain=domain, subdomain=subdomain, workspace=workspace)
    if res.violations:
        raise ValidationError(f"construction is not VALID ({len(res.violations)} violations) — cannot validate")
    delta = {nid: a for nid, a in res.artifacts.items() if isinstance(a, str)}
    return cu.persist_test_snapshot(delta, domain=domain, subdomain=subdomain, out_workspace=out_workspace)


class ValidationError(RuntimeError):
    pass


# ─────────────────────────── acceptance scenario loading + admissibility (Patch 6) ─────────────────

def load_acceptance(dossier: Path) -> list[dict]:
    """Load the S7 acceptance artifacts. Each carries two separated concerns: `acceptance_intent` (the
    business objective + success criteria) and `acceptance_scenario` (its executable realization)."""
    acc = dossier / "acceptance"
    if not acc.exists():
        return []
    return [yaml.safe_load(p.read_text()) for p in sorted(acc.glob("*.y*ml"))]


def _ref_step(path: str) -> str | None:
    """`$.steps.s1.store.…` → 's1' (the step id an address/ref points at), else None."""
    parts = str(path).split(".")
    return parts[2] if len(parts) >= 3 and parts[0] == "$" and parts[1] == "steps" else None


def _refs(obj: Any) -> list[str]:
    """Every `{ref: …}` path anywhere in a payload tree."""
    out: list[str] = []
    if isinstance(obj, dict):
        if "ref" in obj and len(obj) == 1:
            out.append(str(obj["ref"]))
        else:
            for v in obj.values():
                out.extend(_refs(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_refs(v))
    return out


def check_scenario(scenario: dict, *, workflows: set[str]) -> list[str]:
    """VALIDATION_SCENARIO_SCHEMA — structural admissibility of an acceptance scenario, evaluated before
    execution (same philosophy as INVOCATION_INTERFACE: reject an impossible artifact at admit, do not
    discover it at runtime). Returns issues; empty ⇒ admissible."""
    issues: list[str] = []
    steps = scenario.get("steps", [])
    step_ids = [s.get("step") for s in steps]
    if len(step_ids) != len(set(step_ids)):
        issues.append("duplicate step ids")
    seen: set[str] = set()
    for s in steps:
        wf = s.get("workflow", "")
        if wf not in workflows:                                           # ✓ workflow exists
            issues.append(f"step {s.get('step')!r}: unknown workflow {wf!r}")
        for ref in _refs(s.get("payload", {})):                           # ✓ refs point backward, no cycles
            tgt = _ref_step(ref)
            if tgt is not None and tgt not in seen:
                issues.append(f"step {s.get('step')!r}: ref {ref!r} does not point at a prior step")
        try:
            json.dumps(s.get("payload", {}))                              # ✓ payload serializable
        except (TypeError, ValueError):
            issues.append(f"step {s.get('step')!r}: payload is not serializable")
        seen.add(s.get("step"))
    for o in scenario.get("observations", []):
        tgt = _ref_step(o.get("address", ""))
        if tgt is not None and tgt not in set(step_ids):                  # ✓ observation addresses a real step
            issues.append(f"observation {o.get('address')!r} addresses unknown step {tgt!r}")
        try:
            json.dumps(o.get("expected"))                                 # ✓ expected serializable
        except (TypeError, ValueError):
            issues.append(f"observation {o.get('address')!r}: expected value not serializable")
    return issues


def check_intent_coverage(criteria: list[dict], scenario: dict) -> list[str]:
    """ACCEPTANCE_INTENT_COVERAGE — the guard against Intent/Scenario drift: every declared success
    criterion must be `satisfied` by at least one scenario element, and every element's `satisfies` must
    name a real criterion. Structural (does not run anything). Mirrors INVOCATION_INTERFACE."""
    ids = {c.get("id") for c in (criteria or [])}
    issues: list[str] = []
    covered: set[str] = set()
    for elem in list(scenario.get("steps", [])) + list(scenario.get("observations", [])):
        for sc in elem.get("satisfies", []) or []:
            if sc not in ids:
                issues.append(f"element satisfies unknown criterion {sc!r}")
            covered.add(sc)
    for c in sorted(i for i in ids if i is not None):
        if c not in covered:
            issues.append(f"success criterion {c!r} is not satisfied by any scenario element (orphan intent)")
    return issues


def prove_criteria(criteria: list[dict], steps: list[StepOutcome],
                   observations: list[ObservationOutcome]) -> list[CriterionOutcome]:
    """A success criterion is proven iff at least one element satisfies it and every satisfying element
    passed. Pure evidence — no authored knowledge (Patch: Validation proves each declared Intent)."""
    out: list[CriterionOutcome] = []
    elements: list[tuple[str, list[str], bool]] = (
        [(f"step:{s.step}", s.satisfies, s.passed) for s in steps]
        + [(f"obs:{o.address}", o.satisfies, o.passed) for o in observations])
    for c in (criteria or []):
        cid = c.get("id")
        satisfying = [(ref, ok) for ref, sats, ok in elements if cid in (sats or [])]
        proven = bool(satisfying) and all(ok for _ref, ok in satisfying)
        out.append(CriterionOutcome(cid, c.get("statement", ""), [ref for ref, _ in satisfying], proven))
    return out


# ─────────────────────────── address resolution (protocol surface + store) ─────────────────────────

class _Context:
    """Execution context accumulated across a scenario's steps: each step's result surface, plus a live
    reader of declared-store state (read from the shared data-root, mapped via the candidate snapshot's
    STRUCTURE). Reference/observation addresses resolve against this — nothing domain-specific."""

    def __init__(self, snapshot: Path, data_root: Path, domain: str):
        self.surfaces: dict[str, dict] = {}
        self._data_root = data_root
        self._store_paths = _store_map(snapshot, domain)

    def record(self, step_id: str, surface: dict) -> None:
        self.surfaces[step_id] = surface or {}

    def resolve(self, address: str) -> Any:
        parts = str(address).split(".")
        if len(parts) < 4 or parts[0] != "$" or parts[1] != "steps":
            raise ValidationError(f"unresolvable address {address!r}")
        _step, kind, rest = parts[2], parts[3], parts[4:]
        if kind == "surface":
            return _navigate(self.surfaces.get(parts[2], {}), rest)
        if kind == "store":
            if not rest:
                raise ValidationError(f"store address needs a store name: {address!r}")
            store, sub = rest[0], rest[1:]
            return _navigate(self._read_store(store), sub)
        raise ValidationError(f"address kind must be 'surface' or 'store': {address!r}")

    def _read_store(self, store: str) -> Any:
        rel = self._store_paths.get(store)
        if rel is None:
            raise ValidationError(f"unknown store {store!r} (declared: {sorted(self._store_paths)})")
        p = self._data_root / rel
        if not p.exists():
            return [] if p.suffix == ".jsonl" else {}
        if p.suffix == ".jsonl":
            return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
        return json.loads(p.read_text())


def _navigate(obj: Any, parts: list[str]) -> Any:
    for part in parts:
        if isinstance(obj, list) and part in ("count", "length"):
            obj = len(obj)
        elif isinstance(obj, list) and part.lstrip("-").isdigit():
            obj = obj[int(part)]
        elif isinstance(obj, dict):
            obj = obj.get(part)
        else:
            raise ValidationError(f"cannot navigate {part!r} on {type(obj).__name__}")
    return obj


def _store_map(snapshot: Path, domain: str) -> dict[str, str]:
    """{store_name: relative-path} from the candidate snapshot's STRUCTURE storage artifacts (declared
    entity_stores). Read once; domain-agnostic — the engine never hardcodes a path."""
    out: dict[str, str] = {}
    root = snapshot / "protocol_snapshot" / "artifacts" / "structures"
    for p in sorted(root.glob(f"{domain}__*.json")) if root.exists() else []:
        try:
            content = json.loads(p.read_text()).get("content", "")
            import re
            m = re.search(r"```yaml\n(.*?)```", content, re.S)
            core = (yaml.safe_load(m.group(1)) if m else {}).get("core", {})
        except Exception:
            continue
        for name, spec in (core.get("entity_stores") or {}).items():
            if isinstance(spec, dict) and spec.get("path"):
                out[name] = spec["path"]
    return out


def _resolve_tree(obj: Any, resolve_ref) -> Any:
    """Resolve every expression node (`{literal:…}` / `{ref:…}`) in a payload tree; pass plain structure
    through. Uses the shared expression grammar (Patch 3)."""
    if isinstance(obj, dict):
        if len(obj) == 1 and ("literal" in obj or "ref" in obj):
            return expression.evaluate(expression.parse_structured(obj), resolve_ref)
        return {k: _resolve_tree(v, resolve_ref) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_tree(x, resolve_ref) for x in obj]
    return obj


# ─────────────────────────── the validate service ──────────────────────────────────────────────────

def validate(dossier: Path, *, domain: str, subdomain: str, workspace: Path,
             evidence_dir: Path | None = None) -> ValidationReport:
    """Run the CR's declared acceptance scenarios against a fresh candidate snapshot and produce
    validation evidence. Generic across CRs; the only CR-specific input is the declared scenario."""
    from pgs_runtime.api import run_workflow                              # lazy — runtime only needed here

    projection = dossier / "cr_ir"
    docs = load_acceptance(dossier)
    if not docs:
        raise ValidationError(f"no acceptance artifact found under {dossier / 'acceptance'}")
    doc = docs[0]                                                         # (one acceptance artifact per CR for now)
    intent = doc.get("acceptance_intent", {}) or {}
    scenario = doc.get("acceptance_scenario", {}) or {}
    criteria = intent.get("success_criteria", []) or []
    objective = intent.get("objective", "")

    with tempfile.TemporaryDirectory(prefix="cm_validate_") as tmp:
        snap, data = Path(tmp) / "snapshot", Path(tmp) / "data"
        persisted = admit_candidate(projection, domain=domain, subdomain=subdomain,
                                    workspace=workspace, out_workspace=snap)
        construction = {"admission": "PASS" if persisted.ok else "FAIL",
                        "delta_present": len(persisted.delta_present),
                        "status": "ADMITTED_UNVALIDATED" if persisted.ok else "REJECTED"}
        if not persisted.ok:
            raise ValidationError("candidate snapshot did not admit — cannot validate")

        # admissibility: scenario schema (Patch 6) + intent coverage (guard against Intent/Scenario drift)
        workflows = {p.stem.split("__")[-1] for p in (snap / "protocol_snapshot" / "artifacts" / "workflows").glob("*.json")}
        workflows |= {f"{domain}::{w}" for w in workflows}
        issues = check_scenario(scenario, workflows=workflows) + check_intent_coverage(criteria, scenario)
        if issues:
            raise ValidationError("acceptance artifact is not admissible:\n  - " + "\n  - ".join(issues))

        ctx = _Context(snap, data, domain)
        steps: list[StepOutcome] = []
        for s in scenario["steps"]:
            payload = _resolve_tree(s.get("payload", {}), ctx.resolve)    # resolve refs against prior state
            run = run_workflow(wf_fqdn=s["workflow"], payload=payload, data_root=data, workspace=snap)
            ctx.record(s["step"], run.surface)
            expect = s.get("expect_outcome", "SUCCESS")
            steps.append(StepOutcome(s["step"], s["workflow"], run.status, expect,
                                     run.status == expect, list(s.get("satisfies", []) or [])))

        observations: list[ObservationOutcome] = []
        for o in scenario.get("observations", []):
            actual = ctx.resolve(o["address"])
            observations.append(ObservationOutcome(o["address"], o.get("expected"), actual,
                                                   actual == o.get("expected"), list(o.get("satisfies", []) or [])))

        criteria_outcomes = prove_criteria(criteria, steps, observations)
        verdict = ("PASS" if all(s.passed for s in steps) and all(o.passed for o in observations)
                   and all(c.proven for c in criteria_outcomes) else "FAIL")
        report = ValidationReport(
            verdict=verdict, subject=f"{domain}::{subdomain}",
            scenario_code=doc.get("scenario_code", "?"), objective=objective,
            construction=construction, steps=steps, observations=observations, criteria=criteria_outcomes,
            candidate_snapshot="(ephemeral)",
            timestamp=datetime.now(timezone.utc).isoformat())

    # evidence outside any snapshot (Patch 5)
    out = (evidence_dir or (dossier / "validation"))
    out.mkdir(parents=True, exist_ok=True)
    (out / "validation_report.json").write_text(json.dumps(report.to_dict(), indent=2) + "\n")
    return report

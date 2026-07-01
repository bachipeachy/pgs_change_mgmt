"""Guided-Mode validation (SPP · DP6) — the DP3 measurement made repeatable and oracle-gated.

The DP3 experiment (search ≈50% → projection 94% → refined roots 100%, belief spine identical) was a
one-off manual measurement. DP6 turns it into a deterministic report over a Guided stage's package +
response, on four axes that separate producer quality from consumer obligation from the invariant:

  * **Completeness** (consumer, GATED) — did the worker dispose of every projected element? (DP4.)
  * **Efficiency** (producer, DIAGNOSTIC) — RELEVANT / (RELEVANT + NOT_APPLICABLE). Has a *judgment
    floor* (Knowledge Partition Theorem): a low value is not a defect, so it is reported, never gated.
  * **Coverage** (evidence, DIAGNOSTIC) — of a golden reference's cited artifacts, how many the
    platform's evidence floor reached. Measures the projection, not the worker.
  * **Judgment preservation** (the INVARIANT, GATED) — the belief spine disposes every S1 System
    Belief. Across DP3's three runs this held constant while coverage/efficiency moved — the thesis:
    the platform improves deterministic evidence while judgment stays invariant.

The gate passes iff completeness AND judgment preservation hold; efficiency and coverage are surfaced
as signals. This encodes the theorem in a metric: we gate on determinism-and-invariant, never on meaning.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..worker._authoring import parse_output
from ..evaluator.disposition_completeness import assess
from .disposition_gate import _explicit_dispositions

_FQDN_RE = re.compile(r"[a-z_]+::[A-Z][A-Z0-9_]*_V\d+")
_MARK = re.compile(r"register:([a-z0-9_]+)")
_BELIEF_RESULTS = frozenset({"VERIFIED", "NOT_FOUND", "INSUFFICIENT_EVIDENCE"})


@dataclass(frozen=True)
class GuidedValidationReport:
    completeness: float
    completeness_ok: bool
    efficiency: float
    dispositions: dict[str, int]
    evidence_coverage: float | None      # vs a golden reference (None if not provided)
    depth_coverage: float | None         # register-row depth vs golden (None if not provided)
    beliefs_disposed: int
    beliefs_total: int

    @property
    def judgment_preserved(self) -> bool:
        # every S1 System Belief carries a spine disposition (the invariant that held across DP3 runs)
        return self.beliefs_total > 0 and self.beliefs_disposed == self.beliefs_total

    @property
    def ok(self) -> bool:
        return self.completeness_ok and self.judgment_preserved

    def render(self) -> str:
        def pct(x: float | None) -> str:
            return "n/a" if x is None else f"{x:.0%}"
        head = "PASS" if self.ok else "FAIL"
        lines = [
            f"Guided-Mode validation: {head}",
            f"  completeness (GATE):    {self.completeness:.0%}  {'✓' if self.completeness_ok else '✗'}"
            f"   {self.dispositions}",
            f"  judgment preserved (GATE): {self.beliefs_disposed}/{self.beliefs_total} beliefs disposed"
            f"  {'✓' if self.judgment_preserved else '✗'}",
            f"  efficiency (diagnostic): {self.efficiency:.0%}  (judgment floor — not gated)",
            f"  coverage vs golden (diagnostic): evidence {pct(self.evidence_coverage)} · "
            f"depth {pct(self.depth_coverage)}",
        ]
        return "\n".join(lines)


def _register_counts(doc_text: str) -> dict[str, int]:
    """Row count per register in a rendered stage document (for depth coverage)."""
    counts: dict[str, int] = {}
    cur = None
    hdr = 0
    for ln in doc_text.splitlines():
        m = _MARK.search(ln)
        if m:
            cur = m.group(1)
            counts[cur] = 0
            hdr = 2
            continue
        if cur and ln.lstrip().startswith("|"):
            if hdr > 0:
                hdr -= 1
                continue
            if "NONE IDENTIFIED" in ln:
                continue
            counts[cur] += 1
    return counts


def validate_guided_stage(package_dir: str | Path, *, s1_beliefs: list | None = None,
                          golden_text: str | None = None,
                          rendered_doc: str | None = None) -> GuidedValidationReport:
    """Compute the four-axis Guided-Mode validation over an exported package + its pasted response."""
    pkg = Path(package_dir)
    projection = json.loads((pkg / "context" / "discovery_projection.json").read_text())
    raw = (pkg / "response.md").read_text()
    registers, _q, _f = parse_output("interactive", raw)
    explicit = _explicit_dispositions(raw)

    # completeness + efficiency (consumer + producer) from the disposition oracle
    report = assess(projection, registers, explicit)
    disp = report.by_disposition()
    rel = disp.get("RELEVANT", 0)
    na = disp.get("NOT_APPLICABLE", 0)
    efficiency = rel / (rel + na) if (rel + na) else 1.0

    # coverage (evidence + depth) vs a golden reference, if given
    evidence_cov = depth_cov = None
    if golden_text is not None:
        existing = {n["fqdn"] for n in projection["evidence"]["existing"]}
        gold_fqdns = set(_FQDN_RE.findall(golden_text))
        evidence_cov = (len([f for f in gold_fqdns if f in existing]) / len(gold_fqdns)
                        if gold_fqdns else None)
        if rendered_doc is not None:
            gc, mc = _register_counts(golden_text), _register_counts(rendered_doc)
            gtot = sum(gc.values())
            depth_cov = (sum(min(mc.get(k, 0), v) for k, v in gc.items()) / gtot) if gtot else None

    # judgment preservation (the invariant): every S1 belief disposed in the spine
    spine = registers.get("belief_verification") or []
    disposed = sum(1 for r in spine if isinstance(r, dict)
                   and str(r.get("result", "")).strip() in _BELIEF_RESULTS)
    total = len(s1_beliefs) if s1_beliefs is not None else len(spine)

    return GuidedValidationReport(
        completeness=report.coverage, completeness_ok=report.ok,
        efficiency=efficiency, dispositions=disp,
        evidence_coverage=evidence_cov, depth_coverage=depth_cov,
        beliefs_disposed=disposed, beliefs_total=total)

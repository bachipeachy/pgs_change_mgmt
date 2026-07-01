"""Disposition Completeness gate (SPP · DP4 wiring) — enforcement of judgment completeness.

Runs at Guided import, AFTER ingress and BEFORE the engine, WHEN the Stage Package carries a Computed
Semantic Neighborhood. It enforces that the worker DISPOSED of every projected element (SPP.0 — the
platform acquires evidence; the worker disposes of it). No projected `existing` node or `absent`
concept may be silently ignored.

**Boundary-creep guard (the one real failure mode left).** This gate checks disposition *completeness*
— a mechanical property — and NEVER judges the *content* of a disposition (whether RELEVANT is the
"right" call is meaning, and meaning is the worker's). That strict split is the invariant:

    DP1 carries no meaning · DP4 manipulates no structure.

The worker supplies dispositions two ways, both judgment: implicit RELEVANT (a projected FQDN cited in
any register) and explicit **group rules** in a `neighbourhood_disposition` array (segment/kind patterns
so an adjacent-subdomain internal set is disposed in one line). `absent` resolves via the gaps register
(GAP) or an explicit rule (REPRESENTED / NOT_APPLICABLE)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..worker._authoring import last_json_block, parse_output
from ..evaluator.disposition_completeness import assess, DispositionReport


@dataclass(frozen=True)
class DispositionGateResult:
    applicable: bool                       # False ⇒ no projection in the package (gate is a no-op)
    report: DispositionReport | None = None

    @property
    def ok(self) -> bool:
        return not self.applicable or (self.report is not None and self.report.ok)

    def render(self) -> str:
        if not self.applicable:
            return "disposition gate: n/a (no Computed Semantic Neighborhood in this package)"
        r = self.report
        head = "COMPLETE" if r.ok else "INCOMPLETE"
        lines = [f"disposition gate: {head} — coverage {r.coverage:.0%}  {r.by_disposition()}"]
        if not r.ok:
            und_e = [f.split("::")[-1] for f in r.undisposed_existing[:12]]
            lines.append(f"  {len(r.undisposed_existing)} undisposed node(s): {und_e}"
                         + (" …" if len(r.undisposed_existing) > 12 else ""))
            if r.undisposed_absent:
                lines.append(f"  {len(r.undisposed_absent)} undisposed absent concept(s): "
                             f"{r.undisposed_absent}")
            lines.append("  → add `neighbourhood_disposition` group rules (RELEVANT / EXCLUDED / "
                         "NOT_APPLICABLE / REPRESENTED) or cite/GAP them; the platform acquired the "
                         "neighbourhood, the worker must dispose of it.")
        return "\n".join(lines)


def _explicit_dispositions(raw: str) -> list[dict[str, Any]]:
    """The worker's explicit `neighbourhood_disposition` group rules from the response json block."""
    block = last_json_block(raw)
    if not block:
        return []
    try:
        obj = json.loads(block)
    except json.JSONDecodeError:
        return []
    rules = obj.get("neighbourhood_disposition") if isinstance(obj, dict) else None
    return [r for r in rules if isinstance(r, dict)] if isinstance(rules, list) else []


def check_disposition(package_dir: str | Path) -> DispositionGateResult:
    """Assess disposition completeness of the pasted response over the package's projection."""
    pkg = Path(package_dir)
    proj_path = pkg / "context" / "discovery_projection.json"
    if not proj_path.exists():
        return DispositionGateResult(applicable=False)
    projection = json.loads(proj_path.read_text())
    raw = (pkg / "response.md").read_text()
    registers, _q, _f = parse_output("interactive", raw)   # for implicit RELEVANT (cited FQDNs)
    explicit = _explicit_dispositions(raw)
    report = assess(projection, registers, explicit)
    return DispositionGateResult(applicable=True, report=report)

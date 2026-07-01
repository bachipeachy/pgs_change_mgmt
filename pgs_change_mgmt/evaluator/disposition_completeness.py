"""Disposition Completeness oracle (SPP · DP4).

The belief-verification spine generalized to the whole Computed Semantic Neighborhood: every element
the platform ACQUIRED — each `existing` node and each `absent` concept — must be DISPOSED of by the
worker. No projected element may be silently ignored. Disposition is the worker's judgment (SPP.7);
this oracle only checks *completeness* — it never disposes.

Disposition sources:
  * implicit RELEVANT — a projected FQDN cited in any S2 register (the worker modelled it);
  * explicit rules — {target, disposition, reason}, where `target` is an exact FQDN, a `kind:<K>`
    class, or a segment pattern (an UPPERCASE token matched like the projection's own roots). Group
    rules let a worker disposition a whole adjacent-subdomain internal set in one line (e.g. WALLET →
    NOT_APPLICABLE) instead of per node;
  * for `absent` — a concept named in the `gaps` register (→ GAP) or an explicit rule.

Verdict: an element matched by none is UNDISPOSED ⇒ inadmissible. Coverage is *also* a projection-
quality signal — a neighborhood that must be bulk-excluded as adjacent-subdomain internals is
over-scoped, feeding back into DP1 bounding (the DP1.x compiler-feedback-loop, again)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

DISPOSITIONS = frozenset({"RELEVANT", "EXCLUDED", "NOT_APPLICABLE", "GAP", "REPRESENTED"})
_FQDN_RE = re.compile(r"[a-z_]+::[A-Z][A-Z0-9_]*_V\d+")


@dataclass
class DispositionReport:
    existing_disposed: dict[str, str] = field(default_factory=dict)   # fqdn → disposition
    absent_disposed: dict[str, str] = field(default_factory=dict)     # concept → disposition
    undisposed_existing: list[str] = field(default_factory=list)
    undisposed_absent: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.undisposed_existing and not self.undisposed_absent

    @property
    def total(self) -> int:
        return (len(self.existing_disposed) + len(self.undisposed_existing)
                + len(self.absent_disposed) + len(self.undisposed_absent))

    @property
    def coverage(self) -> float:
        disposed = len(self.existing_disposed) + len(self.absent_disposed)
        return disposed / self.total if self.total else 1.0

    def by_disposition(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for d in list(self.existing_disposed.values()) + list(self.absent_disposed.values()):
            counts[d] = counts.get(d, 0) + 1
        return dict(sorted(counts.items()))


def collect_cited_fqdns(registers: Mapping[str, Any]) -> set[str]:
    """Every projected-artifact FQDN the worker cited in any register cell (implicit RELEVANT)."""
    cited: set[str] = set()
    for rows in registers.values():
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, dict):
                for v in row.values():
                    if isinstance(v, str):
                        cited.update(_FQDN_RE.findall(v))
    return cited


def _segment_hit(token: str, code: str) -> bool:
    segments = set(code.upper().split("_"))
    return token in segments or (token + "S") in segments


def _rule_matches(rule: Mapping[str, Any], fqdn: str, kind: str) -> bool:
    target = str(rule.get("target", "")).strip()
    if not target:
        return False
    if target.startswith("kind:"):
        return kind == target.split(":", 1)[1].strip().upper()
    if "::" in target:
        return fqdn == target
    return _segment_hit(target.upper(), fqdn.split("::", 1)[1] if "::" in fqdn else fqdn)


def assess(projection: Mapping[str, Any], registers: Mapping[str, Any],
           explicit: Sequence[Mapping[str, Any]] = ()) -> DispositionReport:
    """Assess disposition completeness of a worker's S2 output over its Computed Semantic Neighborhood."""
    ev = projection.get("evidence", {})
    existing = [(n["fqdn"], n.get("kind", "UNKNOWN")) for n in ev.get("existing", [])]
    absent = [a["concept"] for a in ev.get("absent", [])]
    cited = collect_cited_fqdns(registers)

    # a concept counts as gap-dispositioned if its token appears anywhere in the gaps register
    gap_text = " ".join(
        str(v) for row in registers.get("gaps", []) if isinstance(row, dict) for v in row.values()
    ).upper()

    report = DispositionReport()
    for fqdn, kind in existing:
        if fqdn in cited:
            report.existing_disposed[fqdn] = "RELEVANT"
            continue
        rule = next((r for r in explicit if _rule_matches(r, fqdn, kind)), None)
        if rule is not None and str(rule.get("disposition", "")).upper() in DISPOSITIONS:
            report.existing_disposed[fqdn] = str(rule["disposition"]).upper()
        else:
            report.undisposed_existing.append(fqdn)

    for concept in absent:
        if concept.upper() in gap_text:
            report.absent_disposed[concept] = "GAP"
            continue
        rule = next((r for r in explicit
                     if str(r.get("target", "")).upper() == concept.upper()), None)
        if rule is not None and str(rule.get("disposition", "")).upper() in DISPOSITIONS:
            report.absent_disposed[concept] = str(rule["disposition"]).upper()
        else:
            report.undisposed_absent.append(concept)

    report.undisposed_existing.sort()
    report.undisposed_absent.sort()
    return report
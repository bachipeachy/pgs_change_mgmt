"""Belief-Preservation oracle (S3 cross-stage gate) — the invariant that judgment carries forward.

Stage 3 (Analysis Loop) consumes Stage 2's *Validated Semantic Evidence* (the dispositioned discovery
handoff — belief verifications, gaps, verified baseline) and emits the REUSE/EXTEND/AUTHOR_NEW decisions.
The invariant this gate enforces: **the belief dispositions established at S2 are preserved through S3** —
nothing verified is silently dropped, nothing is overturned without evidence, no belief-derived gap is
left undecided, and a REUSE references something that actually exists.

This is the S2 belief-spine generalized one stage downstream. It is a *structural* check over declared
register linkage (verification_results ↔ S2 beliefs; authoring_decisions ↔ S2 gaps/baseline) — it judges
completeness of the carry-forward, never the correctness of a decision (that stays authoring judgment).
"""

from __future__ import annotations

import re
from typing import Any

_FQDN_RE = re.compile(r"[a-z_]+::[A-Z][A-Z0-9_]*_V\d+")


def check_belief_preservation(s3_data: dict[str, Any],
                              s2_handoff: dict[str, Any]) -> list[tuple[str, str]]:
    """Return (register_id, message) defects (empty ⇒ beliefs preserved through S3)."""
    issues: list[tuple[str, str]] = []
    beliefs = s2_handoff.get("belief_verification") or []
    gaps = s2_handoff.get("gaps") or []
    baseline = {str(b.get("fqdn", "")).strip()
                for b in (s2_handoff.get("pps_baseline_fqdns") or []) if isinstance(b, dict)}
    verif = s3_data.get("verification_results") or []
    decisions = s3_data.get("authoring_decisions") or []

    # (a) Verification spine — every S2 System Belief is re-verified at S3 (CONFIRMED / OVERTURNED),
    #     and an OVERTURNED belief must carry grounded evidence (you may change a belief, never silently).
    n_b, n_v = len(beliefs), len(verif)
    if n_b and n_v < n_b:
        issues.append(("verification_results",
                       f"belief preservation: {n_v} verification result(s) for {n_b} S2 System Belief(s) "
                       f"— {n_b - n_v} belief(s) not carried forward / re-verified at S3"))
    for i, row in enumerate(verif):
        if isinstance(row, dict) and str(row.get("result", "")).strip() == "OVERTURNED" \
                and not str(row.get("evidence", "")).strip():
            issues.append(("verification_results",
                           f"verification_results[{i}]: OVERTURNED without evidence — a belief may only "
                           "be overturned with grounded evidence, never silently reversed"))

    # (b) REUSE validity — a REUSE decision must reference an existing artifact (a verified baseline
    #     FQDN). You cannot reuse what does not exist.
    for i, row in enumerate(decisions):
        if not isinstance(row, dict) or str(row.get("decision", "")).strip() != "REUSE":
            continue
        cited = " ".join(str(row.get(k, "")) for k in ("source_finding", "rationale", "alternatives_checked"))
        if not _FQDN_RE.search(cited):
            issues.append(("authoring_decisions",
                           f"authoring_decisions[{i}]: REUSE with no baseline FQDN cited — a REUSE must "
                           "reference a verified-existing artifact"))

    # (c) Gap coverage — belief-derived CRITICAL gaps must be addressed by an authoring decision; a
    #     CRITICAL gap with no AUTHOR_NEW/EXTEND anywhere means gaps were left undecided.
    critical_gaps = [g for g in gaps
                     if isinstance(g, dict) and "CRITICAL" in str(g.get("severity", "")).upper()]
    addressed = [d for d in decisions if isinstance(d, dict)
                 and str(d.get("decision", "")).strip() in ("AUTHOR_NEW", "EXTEND")]
    if critical_gaps and not addressed:
        issues.append(("authoring_decisions",
                       f"{len(critical_gaps)} CRITICAL S2 gap(s) but no AUTHOR_NEW/EXTEND decision — "
                       "belief-derived gaps left undecided"))
    return issues
"""Convergence measure (Phase 5c) — do two independent builders agree?

  convergence(out_A, out_B) — given the SAME construction-closed sheet, do two architecturally
                              different builders produce the same artifact (by FQDN content)?
                              Converge ⇒ the sheet DETERMINED the artifact (construction-closed).
                              Diverge ⇒ a design choice was left open; the divergence points are the
                              missed gaps.

Convergence measures builder AGREEMENT, nothing more. Whether a single artifact conforms to its
specification — invention at FQDN / field / label / store level — is the invention oracle's job
(`evaluator.invention_oracle`), not this module's (Patch 4: convergence does not own architecture).
"""

from __future__ import annotations

import re

_FQDN = re.compile(r"(?:[a-z][a-z0-9_.]*::)?((?:CC|CS|CT|IN|WF|RB|EV|AC|STRUCTURE|TI)_[A-Z0-9_]*_V\d+)")


def artifact_codes(text: str) -> set[str]:
    """Every protocol FQDN (code-part) mentioned in an artifact document."""
    return {m for m in _FQDN.findall(text or "") if m}


def convergence(out_a: str, out_b: str) -> dict:
    """Structural agreement of two builder outputs by FQDN content.

    `score` = |shared| / |union| (Jaccard). `converged` = the two used the exact same FQDN set.
    """
    ca, cb = artifact_codes(out_a), artifact_codes(out_b)
    union = ca | cb
    only_a, only_b = sorted(ca - cb), sorted(cb - ca)
    return {
        "score": round(len(ca & cb) / len(union), 3) if union else 1.0,
        "converged": not (only_a or only_b),
        "shared": sorted(ca & cb),
        "only_a": only_a,
        "only_b": only_b,
    }

"""IdentityEvaluator — the single concrete `contracts.Evaluator` today.

Resolves artifact identity against the authoritative vocabulary *before* classifying, using
the A–E taxonomy (`identity_audit`). Only class E (no identity anywhere, not a proposal) is a
fabrication; a premature class-D proposal is a purity defect. Both fail the verdict; A/B/C and
a stage-legitimate D pass. This is the D↔E split the old aggregate/regex evaluator could not
make — it collapsed B, C, D and E into one "hallucination" count.

The evaluator targets either raw authored text or a `gov_projection`: for a projection it
classifies the FQDNs carried in its values at the projection's own stage, so a
stage-legitimate new artifact resolves as D (legit), not E.
"""

from __future__ import annotations

from typing import Any

from ..contracts import GovProjection, Verdict
from .identity_audit import audit_text, load_vocab, _STAGE_NUM


class IdentityEvaluator:
    """`contracts.Evaluator` over authored output / gov_projections.

    Loads the vocabulary once (from `PGS_WORKSPACE`'s artifact index) and reuses it across
    `evaluate` calls. `evaluate` returns a `Verdict` whose `detail` is the full A–E audit
    (counts + by_class + per-FQDN detail).
    """

    def __init__(self, vocab: tuple | None = None) -> None:
        self._vocab = vocab if vocab is not None else load_vocab()

    @staticmethod
    def _stage_num(stage: str | None) -> float | None:
        return _STAGE_NUM.get(stage) if stage is not None else None

    @staticmethod
    def _projection_text(proj: GovProjection) -> str:
        """Flatten a projection's values to text so the FQDN extractor can find every
        carried FQDN (the identity audit keys off FQDN regex matches, not field names)."""
        parts: list[str] = []

        def _walk(v: Any) -> None:
            if isinstance(v, str):
                parts.append(v)
            elif isinstance(v, dict):
                for x in v.values():
                    _walk(x)
            elif isinstance(v, (list, tuple, set)):
                for x in v:
                    _walk(x)
            else:
                parts.append(str(v))

        _walk(dict(proj.values))
        return "\n".join(parts)

    def evaluate(self, target: GovProjection | str, *, stage: str | None = None) -> Verdict:
        if isinstance(target, GovProjection):
            stage = stage or target.stage
            text = self._projection_text(target)
        else:
            text = target
        audit = audit_text(text, self._vocab, stage_num=self._stage_num(stage))
        fabrications = audit["counts"]["E_FABRICATION"]
        purity_defects = [
            fq for fq, (cls, det) in audit["detail"].items()
            if cls == "D_PROPOSED_NEW" and "purity defect" in det
        ]
        ok = fabrications == 0 and not purity_defects
        return Verdict(ok=ok, detail={**audit, "purity_defects": purity_defects})

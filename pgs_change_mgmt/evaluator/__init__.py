"""evaluator — identity-aware evaluation of authored output / gov_projections.

Resolves artifact identity before classifying (A–E taxonomy); only no-identity-anywhere is a
fabrication (E), and a premature proposal (D before its legitimate stage) is a purity defect.
`IdentityEvaluator` is the single concrete `contracts.Evaluator` today.

The lower-level taxonomy functions (`audit_text`, `classify`, `load_vocab`) are re-exported
for direct auditing and tests.
"""

from .evaluator import IdentityEvaluator
from .identity_audit import audit_text, classify, load_vocab

__all__ = [
    "IdentityEvaluator",
    "audit_text",
    "classify",
    "load_vocab",
]

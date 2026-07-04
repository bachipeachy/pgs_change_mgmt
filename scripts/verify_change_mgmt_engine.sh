#!/usr/bin/env bash
# verify_change_mgmt_engine.sh — offline verification suite for the pgs_change_mgmt engine.
#
# Run this before a commit or after changing any seam: it proves the engine's PLUMBING is
# correct — the four seams (grounding / evaluator / renderer / worker) conform to their
# contracts, the renderers emit admissible YAML per kind, and the engine wires
# worker→evaluator→renderer→artifact end-to-end. Fast, deterministic, offline — except the
# grounding smoke, which reads the live compiled snapshot via `pi`.
#
# It does NOT run the live qwen model or a real compile — that is the Phase 4A equivalence
# proof (see doc/PHASE_4A_EQUIVALENCE_RUNBOOK.md), which is slow and run separately.
#
# Usage:
#   PGS_WORKSPACE=/abs/path/to/pgs_workspace bash scripts/verify_change_mgmt_engine.sh
set -euo pipefail

: "${PGS_WORKSPACE:?set PGS_WORKSPACE to the absolute pgs_workspace path}"

# Activate the workspace venv if pgs_change_mgmt isn't importable yet.
if ! python -c "import pgs_change_mgmt" 2>/dev/null; then
  source "$PGS_WORKSPACE/.venv/bin/activate"
fi

echo "════════ 1. contracts schema (gov_projection: every field has a consumer) ════════"
python -c "from pgs_change_mgmt.contracts import validate_schema; \
o=validate_schema(); assert not o, o; print('gov_projection schema valid ✓')"

echo ""; echo "════════ 2. seam conformance (Protocol checks) ════════"
python -c "
from pgs_change_mgmt.contracts import GroundingProvider, Evaluator, Renderer, Worker
from pgs_change_mgmt.grounding import PiGroundingProvider
from pgs_change_mgmt.evaluator import IdentityEvaluator
from pgs_change_mgmt.renderer import CCRenderer, INRenderer, RBRenderer, WFRenderer
from pgs_change_mgmt.worker import OllamaWorker
g = PiGroundingProvider()
assert isinstance(g, GroundingProvider) and isinstance(IdentityEvaluator(), Evaluator)
assert isinstance(OllamaWorker(g), Worker)
assert all(isinstance(r, Renderer) for r in (CCRenderer(),INRenderer(),RBRenderer(),WFRenderer()))
print('grounding, evaluator, renderer(×4), worker all conform ✓')
"

echo ""; echo "════════ 3. grounding smoke (live pi snapshot) ════════"
python -m pgs_change_mgmt.grounding.smoke_pi_tools | tail -1

echo ""; echo "════════ 4. renderer admissibility (CC/IN/WF/RB → valid YAML) ════════"
python -m pgs_change_mgmt.renderer._selftest | tail -1

echo ""; echo "════════ 5. evaluator A–E identity + D↔E split ════════"
python -c "
from pgs_change_mgmt.evaluator import IdentityEvaluator
ev = IdentityEvaluator()
real='blockchain::CC_GENERATE_ACTOR_ID_V0'; fake='blockchain::CC_NOPE_V0'
assert ev.evaluate(f'{real} {fake}', stage='2').ok is False   # fake = fabrication (E) early
assert ev.evaluate(fake, stage='6b').ok is True               # same fake = legit proposal (D) later
print('A–E identity + D↔E split correct ✓')
"

echo ""; echo "════════ 6. artifact-engine wiring (stub worker → artifact, deps A_EXACT) ════════"
python -m pgs_change_mgmt.engine._selftest | tail -1

echo ""; echo "════════ 7. dossier-engine wiring (staged S1→S2, bounded gov_projection handoff) ════════"
python -m pgs_change_mgmt.engine._dossier_selftest | tail -1

echo ""; echo "════════ 8. structured dossier stage (S4: register-intent → renderer → oracle) ════════"
python -m pgs_change_mgmt.engine._dossier_structured_selftest | tail -1

echo ""; echo "════════ 9. S8 build-sheet projection (S2/S5/S6b/S7 → assembled sheets, gap-classified) ════════"
python -m pgs_change_mgmt.engine._build_sheet_selftest | tail -1

echo ""; echo "════════ 10. construction harness (sheet → constructor → invention + convergence; S9 evidence) ════════"
python -m pgs_change_mgmt.engine._construction_selftest | tail -1

echo ""; echo "════════ 11. Construction Model engine (Project→Construct→Validate→Serialize; graph + lowering pipeline + constraints) ════════"
python -m pgs_change_mgmt.engine._construction_model_selftest | tail -1

echo ""; echo "════════ 12. Construction Compiler CLI (thin orchestration → compiler report + status) ════════"
python -m pgs_change_mgmt.engine._construction_cli_selftest | tail -1

echo ""; echo "════════ 13. Design Review Contract (engine-certified Part A every stage; bounded Part B) ════════"
python -m pgs_change_mgmt.engine._design_review_selftest | tail -1

echo ""; echo "✅ ALL OFFLINE SELF-TESTS GREEN"

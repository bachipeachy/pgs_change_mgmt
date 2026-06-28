"""Construction harness + convergence proof (Phase 5, mock builder — no model invoked).

Proves the plumbing: a CONSTRUCTION_READY Build Sheet → constructor prompt → artifact; zero-invention
catches a fabricated FQDN; convergence catches a divergent second builder. The real run swaps the
MockBuilder for `OllamaClient(model="qwen3:14b")` / `"qwen3.5:latest"`.
"""

from __future__ import annotations

import re
from pathlib import Path

from .build_sheet import project_build_sheets, load_registers
from ..worker.construction import transcribe, build_prompt, CONSTRUCTOR_SYSTEM
from ..evaluator.invention_oracle import sheet_codes, structural_invention, text_invention
from ..evaluator.construction_oracle import evaluate_build

CHAIN = Path(__file__).resolve().parents[2] / "change_mgmt" / "dossiers" / "blockchain" / "chain"


class MockBuilder:
    """Returns a canned artifact; records the messages it was given (to assert prompt shape)."""
    def __init__(self, artifact: str):
        self.artifact = artifact
        self.last_messages = None

    def chat(self, messages, tools=None):
        self.last_messages = messages
        return {"message": {"content": self.artifact}}


def main() -> int:
    up = load_registers(CHAIN / "_handoff")   # authoritative JSON path (no markdown re-parse)
    model = project_build_sheets(up, domain="blockchain", subdomain="chain")
    sheet = {s.code: s for s in model.sheets}["CC_COMMIT_BLOCK_CANONICAL_V0"]

    authorized = sorted(sheet_codes(sheet))
    assert "CC_COMMIT_BLOCK_CANONICAL_V0" in authorized and "CT_PURE_HASH_BLOCK_V0" in authorized, authorized
    print(f"  sheet authorises {len(authorized)} FQDNs: {authorized}")

    # a faithful transcription uses ONLY authorised codes
    faithful = f"# CC_COMMIT_BLOCK_CANONICAL_V0\n\nPipeline composes: {' '.join('blockchain::'+c if not c.startswith(('CS_','CT_PURE_COMPARE')) else 'capability_side_effects::'+c for c in authorized)}\n"
    mb = MockBuilder(faithful)
    out = transcribe(sheet, "## CC FORMAT EXEMPLAR\n...", mb)

    # prompt shape: constructor role + the sheet spec in the user turn
    sys_msg, user_msg = mb.last_messages
    assert sys_msg["role"] == "system" and "CONSTRUCTOR" in sys_msg["content"], "system role must forbid design"
    assert "CC_COMMIT_BLOCK_CANONICAL_V0" in user_msg["content"], "sheet spec must be in the prompt"
    assert "FORMAT EXEMPLAR" in user_msg["content"], "format exemplar must be in the prompt"
    assert out.startswith("# CC_COMMIT_BLOCK_CANONICAL_V0"), "transcribe must return the artifact"
    print("  prompt: constructor-not-designer system role + sheet spec + format exemplar ✓")

    # invention oracle — a faithful artifact invents nothing at any level
    ev = evaluate_build(sheet, out)
    assert ev.conformant and not ev.structural_invention, f"faithful artifact must be conformant: {ev.structural_invention}"
    print("  structural_invention: faithful → conformant (no FQDN/field/label invention) ✓")

    # the FQDN blind spot is still closed (structural, ERROR)
    inventing = out + "\nblockchain::CC_FABRICATED_NOWHERE_V0\n"
    assert "CC_FABRICATED_NOWHERE_V0" in structural_invention(inventing, sheet).get("fqdns", []), "must flag an invented FQDN"

    # NEW — field-level: a JSONPath reference to an unauthorised field is structural invention
    field_inv = out + "\n| input | $.results.CC_COMMIT_BLOCK_CANONICAL_V0.fabricated_field_xyz |\n"
    assert "fabricated_field_xyz" in structural_invention(field_inv, sheet).get("fields", []), \
        f"must flag an invented JSONPath field: {structural_invention(field_inv, sheet)}"

    # NEW — label-level: an unauthorised routing outcome is structural invention…
    label_inv = out + "\n| routing | FABRICATED_OUTCOME → EXIT |\n"
    assert "FABRICATED_OUTCOME" in structural_invention(label_inv, sheet).get("labels", []), \
        f"must flag an invented routing label: {structural_invention(label_inv, sheet)}"
    # …but the SAME label only in prose is TEXT invention (WARN), not structural (Patch 3 severity split)
    prose_inv = out + "\nThe outcome FABRICATED_OUTCOME is described informally here.\n"
    assert "FABRICATED_OUTCOME" not in structural_invention(prose_inv, sheet).get("labels", []), "prose mention is not structural"
    assert "FABRICATED_OUTCOME" in text_invention(prose_inv, sheet).get("labels", []), "prose mention is text invention"
    print("  field-level + label-level invention caught; prose mention → text (WARN) not structural (ERROR) ✓")

    # convergence (own module) — identical builders converge; a divergent second builder is localised
    div = evaluate_build(sheet, out, inventing).convergence
    assert evaluate_build(sheet, out, out).convergence["converged"], "identical outputs must converge"
    assert not div["converged"] and "CC_FABRICATED_NOWHERE_V0" in div["only_b"], f"divergence must localise: {div}"
    print(f"  convergence: identical → converged ; divergent → score={div['score']} only_b={div['only_b']} ✓")

    # the prompt is deterministic and self-contained (no model state)
    assert build_prompt(sheet)[0]["content"] == CONSTRUCTOR_SYSTEM

    # ---- S9 Construction Record renders from REAL bridge evidence (not stubbed registers) ----
    # S9 is post-construction EVIDENCE: render_s9 turns the bridge's per-artifact compiler verdicts
    # into the record. Proven here in Construction — S9 is NOT a dossier-engine authoring stage.
    from .construct_chain import render_s9
    from .bridge import BridgeResult
    green = BridgeResult(code="blockchain::CC_COMMIT_BLOCK_CANONICAL_V0",
                         dest=Path("registry/chain/capability_contracts/CC_COMMIT_BLOCK_CANONICAL_V0.md"),
                         compiled=True, validated=True, kept=True)
    red = BridgeResult(code="blockchain::CC_BROKEN_V0", dest=Path("registry/chain/x.md"),
                       compiled=True, validated=False,
                       diagnostics=["ERROR: ASSERT_TOPOLOGY_ROUTING_COMPLETE failed"])
    s9 = render_s9([green, red], abstained=[("blockchain::CC_GAP_V0", "STOP: located gap, not invention")],
                   build_structure="STRUCTURE_BUILD_BLOCKCHAIN_CONFIG_V0")
    assert s9.startswith("# Construction Record") and "1 compiled · 1 rejected · 1 abstained" in s9, \
        f"S9 outcome line wrong: {s9[:200]}"
    assert "CC_COMMIT_BLOCK_CANONICAL_V0 |" in s9, "S9 §1 must list the compiled+validated artifact"
    assert "CC_BROKEN_V0" in s9 and "ASSERT_TOPOLOGY_ROUTING_COMPLETE failed" in s9, \
        "S9 §2 must record the rejected artifact + its diagnostics"
    assert "CC_GAP_V0" in s9, "S9 §3 must record the abstention"
    print("  S9 Construction Record renders real bridge evidence (§1 built · §2 rejected+diagnostics · §3 abstained) ✓")

    print("\nCONSTRUCTION HARNESS PROOF OK ✓ — sheet → constructor prompt → artifact; structural-invention "
          "(FQDN+field+label) + convergence wired via the Construction Oracle; builder interchangeable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Stage Package export proof (I1) — deterministic, NO model, NO grounding.

Exports the governed Stage Package for S1 (seed-only) and S2 (consumes an S1 handoff fixture) and
asserts the package is complete, the hashes are stable across two builds, the register schema
matches the template, and the grounding frontier is non-empty and in-scope.

Run: python -m pgs_change_mgmt.engine._stage_package_selftest
"""

from __future__ import annotations

import dataclasses
import json
import tempfile
from pathlib import Path

from .dossier import DOSSIER_SEEDS
from .stage_package import StagePackageBuilder, derive_required_tokens
from ..renderer.template_compiler import compile_template

PASS, FAIL = "✅", "❌"


def _check(cond: bool, label: str) -> bool:
    print(f"  {PASS if cond else FAIL} {label}")
    return cond


# A minimal S1 handoff fixture so S2 export has a bounded scope to derive its frontier from
# (term-bearing `business_vocabulary` rows + a couple of belief/fact rows the harvester ignores).
_S1_HANDOFF_FIXTURE = {
    "business_vocabulary": [
        {"term": "Chain", "definition": "the append-only ledger", "source_finding": "seed §2"},
        {"term": "Block", "definition": "a unit of the ledger", "source_finding": "seed §2"},
        {"term": "Genesis Block", "definition": "the first block", "source_finding": "seed §2"},
    ],
    "system_beliefs": [{"belief": "a canonical chain exists", "certainty": "HIGH"}],
    "known_facts": [{"fact": "supply is closed", "certainty": "HIGH"}],
}


def main() -> int:
    ok = True
    base = DOSSIER_SEEDS["blockchain_chain"]
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        cfg = dataclasses.replace(base, output_dir=tmp_root / "dossier")
        out_root = tmp_root / "packages"

        # ---- S1 (seed-only) ----------------------------------------------------------------
        print("S1 — seed-only export")
        builder = StagePackageBuilder(cfg)   # no grounding ⇒ snapshot_hash null (hermetic)
        pkg1 = builder.build("1", out_root=out_root)

        expected = ["manifest.json", "prompt_bundle.json", "system_prompt.md", "user_prompt.md",
                    "context/handoff.json", "context/grounding_spec.json", "expected_output.md",
                    "schema.json"]
        ok &= _check(all((pkg1 / f).exists() for f in expected), "all package files written")
        ok &= _check(not (pkg1 / "response.md").exists(), "no response.md on export")

        manifest = json.loads((pkg1 / "manifest.json").read_text())
        bundle = json.loads((pkg1 / "prompt_bundle.json").read_text())
        schema = json.loads((pkg1 / "schema.json").read_text())
        gspec = json.loads((pkg1 / "context" / "grounding_spec.json").read_text())

        ok &= _check(manifest["snapshot_hash"] is None, "snapshot_hash null (no grounding passed)")
        ok &= _check(manifest["mode"] == "guided", "manifest mode = guided")
        ok &= _check(bundle["prompt_hash"].startswith("sha256:"), "bundle carries a prompt_hash")

        # schema ↔ template: structured S1 register ids match the compiled template exactly
        template = (cfg.templates_dir / "1_change_request_template_v0.md").read_text()
        reg_ids = {r.register_id for r in compile_template(template)}
        ok &= _check(set(schema["registers"]) == reg_ids, "schema registers match S1 template")

        # hash linkage across the three files
        ok &= _check(
            manifest["schema_hash"] == schema["schema_hash"] == bundle["register_contract"]["schema_hash"],
            "schema_hash consistent (manifest = schema.json = bundle.register_contract)")
        ok &= _check(manifest["prompt_hash"] == bundle["prompt_hash"], "prompt_hash consistent")

        # grounding frontier: non-empty and in-scope (every token derivable from the seed)
        tokens1 = gspec["required_tokens"]
        ok &= _check(bool(tokens1), f"S1 required_tokens non-empty ({len(tokens1)}: {tokens1[:8]}…)")
        seed_text = cfg.seed_path.read_text().upper()
        ok &= _check(all(t in seed_text for t in tokens1), "every S1 token appears in the seed (in-scope)")
        ok &= _check("BLOCK" in tokens1 and "GENESIS" in tokens1,
                     "S1 frontier includes domain tokens BLOCK + GENESIS")
        ok &= _check(gspec["validation_mode"] == "strict", "grounding_spec validation_mode = strict")

        # ---- determinism: a second build is byte-stable on the hashes ----------------------
        out_root2 = tmp_root / "packages2"
        pkg1b = builder.build("1", out_root=out_root2)
        b2 = json.loads((pkg1b / "prompt_bundle.json").read_text())
        s2 = json.loads((pkg1b / "schema.json").read_text())
        ok &= _check(b2["prompt_hash"] == bundle["prompt_hash"], "prompt_hash stable across builds")
        ok &= _check(s2["schema_hash"] == schema["schema_hash"], "schema_hash stable across builds")

        # ---- S2 (consumes the S1 handoff fixture) ------------------------------------------
        print("S2 — consumes S1 handoff fixture")
        handoff_dir = cfg.output_dir / "cr_ir"
        handoff_dir.mkdir(parents=True, exist_ok=True)
        (handoff_dir / "1.json").write_text(json.dumps(_S1_HANDOFF_FIXTURE, indent=2))

        pkg2 = builder.build("2", out_root=out_root)
        handoff2 = json.loads((pkg2 / "context" / "handoff.json").read_text())
        gspec2 = json.loads((pkg2 / "context" / "grounding_spec.json").read_text())
        tokens2 = gspec2["required_tokens"]

        ok &= _check("business_vocabulary" in handoff2,
                     "S2 bounded handoff carried business_vocabulary from S1")
        ok &= _check(bool(tokens2), f"S2 required_tokens non-empty ({len(tokens2)}: {tokens2[:8]}…)")
        ok &= _check("BLOCK" in tokens2 and "GENESIS" in tokens2,
                     "S2 frontier derived from the handoff terms (BLOCK + GENESIS)")
        # in-scope: every S2 token traces to the bounded handoff (never the domain at large)
        pool = json.dumps(handoff2, default=str).upper()
        ok &= _check(all(t in pool for t in tokens2), "every S2 token traces to the bounded handoff")

        # frontier is a function of scope, not an answer key: empty scope ⇒ empty frontier
        ok &= _check(derive_required_tokens({}, None) == [], "empty scope ⇒ empty frontier")

    print(f"\n{'ALL PASS' if ok else 'FAILURES PRESENT'}")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

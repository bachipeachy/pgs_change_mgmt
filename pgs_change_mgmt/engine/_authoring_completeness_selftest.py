"""Authoring Completeness proof — the Authority-vs-Authorship boundary is enforced, not vacuous.

Asserts the gate PASSES when a human-owned field is supplied and STOPS (AUTHORING_INCOMPLETE) when
it is absent; that the value flows to its renderer target; and that ``required_before`` /
``renderer_target`` map a field to the stage(s) that may not proceed without it.

Run: python -m pgs_change_mgmt.engine._authoring_completeness_selftest
"""

from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from ..contracts.authoring_completeness import (
    extract_seed_section, fields_due_before, load_registry, supplied_value)
from .authoring_completeness import check_authoring_completeness, fill_authoring_targets

PASS, FAIL = "✅", "❌"

_REGISTRY = {"fields": {"subdomain_purpose": {
    "owner": "human", "derivable": False, "phase": "seed", "type": "narrative",
    "required_before": "1", "why": "why it exists", "prompt": "state the purpose",
    "source": {"kind": "seed", "section": "Subdomain Purpose"},
    "renderer_target": {"stage": "5", "placeholder": "[Purpose paragraph for {domain}/{subdomain}.]"}}}}

_SEED_FILLED = """# CR Seed

---

## Subdomain Purpose (human, non-derivable)

*Guidance italics that span
two lines and must be stripped.*

The chain subdomain keeps the official ledger of accepted blocks.

---

## 1. CR Type
NEW_SUBDOMAIN
"""

_SEED_MISSING = """# CR Seed

---

## Subdomain Purpose (human, non-derivable)

*Guidance only — the human never wrote the paragraph.*

[Purpose paragraph for [domain]/[subdomain].]

---

## 1. CR Type
NEW_SUBDOMAIN
"""


@dataclass
class _Cfg:
    templates_dir: Path
    seed_path: Path
    domain: str = "blockchain"
    subdomain: str = "chain"


def _check(cond: bool, label: str) -> bool:
    print(f"  {PASS if cond else FAIL} {label}")
    return cond


def main() -> int:
    ok = True
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        (base / "templates").mkdir()
        (base / "authoring_fields.json").write_text(json.dumps(_REGISTRY))
        reg = load_registry(base / "authoring_fields.json")

        # extraction strips multi-line italics, placeholders, and thematic breaks
        v = extract_seed_section(_SEED_FILLED, "Subdomain Purpose")
        ok &= _check(v == "The chain subdomain keeps the official ledger of accepted blocks.",
                     f"extraction is clean human prose only: {v!r}")
        ok &= _check(extract_seed_section(_SEED_MISSING, "Subdomain Purpose") == "",
                     "unfilled section (guidance + placeholder only) ⇒ empty ⇒ a gap")

        # obligation graph: field is due at its required_before (1) and its consumption stage (5)
        due = {f.id for f in fields_due_before(reg, "1")}
        due5 = {f.id for f in fields_due_before(reg, "5")}
        due3 = {f.id for f in fields_due_before(reg, "3")}
        ok &= _check("subdomain_purpose" in due and "subdomain_purpose" in due5 and not due3,
                     "due before stage 1 (required_before) and stage 5 (renderer_target); not stage 3")

        seed = base / "seed.md"

        # supplied ⇒ gate PASSES + value fills the renderer target
        seed.write_text(_SEED_FILLED)
        cfg = _Cfg(base / "templates", seed)
        r = check_authoring_completeness(cfg, "5")
        ok &= _check(r.ok, "supplied seed ⇒ gate passes (stage 5)")
        filled = fill_authoring_targets("§1\n[Purpose paragraph for blockchain/chain.]\n", cfg, "5")
        ok &= _check("[Purpose paragraph" not in filled and "keeps the official ledger" in filled,
                     "renderer target filled from the seed value (never invented)")

        # absent ⇒ gate STOPS with AUTHORING_INCOMPLETE (proves non-vacuous)
        seed.write_text(_SEED_MISSING)
        r = check_authoring_completeness(cfg, "1")
        ok &= _check(not r.ok and "AUTHORING_INCOMPLETE" in r.render()
                     and "subdomain_purpose" in r.render(),
                     "missing seed field ⇒ AUTHORING_INCOMPLETE, names the field")
        ok &= _check(fill_authoring_targets("[Purpose paragraph for blockchain/chain.]", cfg, "5")
                     == "[Purpose paragraph for blockchain/chain.]",
                     "absent value ⇒ placeholder left intact (never fabricated)")

    print(f"\n{'ALL PASS' if ok else 'FAILURES PRESENT'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

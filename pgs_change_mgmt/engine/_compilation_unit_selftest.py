"""Compilation Unit source-ingest proof — offline, hermetic.

Locks `compilation_unit.load_sources`: the origin-agnostic ingest that lets the Snapshot Admission
Gate form a Compilation Unit from any on-disk artifact sources (generated delta, reused library, or
temporary support). It asserts the plumbing that makes the "compile CR artifacts" gate REPEATABLE:

  - FQDN is recovered from the snapshot filename convention `<namespace>__<CODE>.md` (`::` → `__`);
  - non-qualified `.md` files (README, notes) are ignored as documentation, not artifacts;
  - duplicate FQDNs across sources are refused;
  - a missing source directory fails hard.

No real compiler, no live repos — just the loader contract. The live end-to-end admission PASS over
the chain Compilation Unit is documented in README.md → "The Snapshot Admission Gate".

Run:  python -m pgs_change_mgmt.engine._compilation_unit_selftest
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from . import compilation_unit as cu


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "src"
        src.mkdir()
        (src / "blockchain__STRUCTURE_CHAIN_STORAGE_V0.md").write_text("# STRUCTURE\n")
        (src / "capability_transforms__CT_PURE_COMPARE_EQUAL_V0.md").write_text("# CT\n")
        (src / "README.md").write_text("# docs — not an artifact\n")
        (src / "notes.md").write_text("scratch notes\n")

        loaded = cu.load_sources([src], default_namespace="blockchain")

        # FQDN recovered from filename; namespace preserved across domains; docs ignored.
        assert set(loaded) == {
            "blockchain::STRUCTURE_CHAIN_STORAGE_V0",
            "capability_transforms::CT_PURE_COMPARE_EQUAL_V0",
        }, f"unexpected FQDN set: {sorted(loaded)}"
        assert loaded["blockchain::STRUCTURE_CHAIN_STORAGE_V0"] == "# STRUCTURE\n"

        # Empty include list is a no-op (delta-only Compilation Unit).
        assert cu.load_sources([], default_namespace="blockchain") == {}

        # Duplicate FQDN across sources is refused (no silent last-wins).
        dup = Path(tmp) / "dup"
        dup.mkdir()
        (dup / "blockchain__STRUCTURE_CHAIN_STORAGE_V0.md").write_text("# other\n")
        try:
            cu.load_sources([src, dup], default_namespace="blockchain")
            raise AssertionError("duplicate FQDN across sources should raise")
        except ValueError as e:
            assert "duplicate" in str(e).lower()

        # Missing source directory fails hard (never guesses).
        try:
            cu.load_sources([Path(tmp) / "nope"], default_namespace="blockchain")
            raise AssertionError("missing source dir should raise")
        except FileNotFoundError:
            pass

    print("\nCOMPILATION UNIT SOURCE PROOF OK ✓ — load_sources recovers FQDNs from qualified filenames, "
          "ignores docs, refuses duplicates, fails hard on a missing source (origin-agnostic ingest).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

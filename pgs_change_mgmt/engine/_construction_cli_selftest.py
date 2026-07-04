"""Construction Compiler CLI proof (§12) — thin orchestration emits a compiler report + status.

Hermetic: runs `construction_cli validate` against the frozen chain fixture's regenerated `cr_ir`,
asserting the CLI surfaces `CONSTRUCTION_VALID` (D4 closed → zero violations) and exit code 0. Proves
the public CLI seam without touching the live working dossier.

Run:  PGS_WORKSPACE=/abs python -m pgs_change_mgmt.engine._construction_cli_selftest
"""
from __future__ import annotations

import os

from . import construction_cli as cli
from ._fixture import authored, chain_dossier


def main() -> int:
    assert os.environ.get("PGS_WORKSPACE"), "set PGS_WORKSPACE"
    if not authored():
        print("CONSTRUCTION CLI PROOF PENDING ⏳ — frozen chain fixture predates S7 authoring; "
              "CONSTRUCTION_VALID needs D4 closed. Re-freeze from the first governed from-seed run.")
        return 0
    with chain_dossier() as chain:
        rc = cli.main(["validate", "--projection", str(chain / "cr_ir"),
                       "--domain", "blockchain", "--subdomain", "chain"])
    assert rc == cli.VALID, f"construction_cli validate should be CONSTRUCTION_VALID (0), got {rc}"
    print("\nCONSTRUCTION CLI PROOF OK ✓ — validate emits a compiler report + CONSTRUCTION_VALID status "
          "over the frozen chain fixture (hermetic; no live dossier).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
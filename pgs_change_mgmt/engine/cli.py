"""`pgs_change` — the single user-facing executable for the change-management lifecycle.

One executable, four lifecycle verbs. The user thinks in phases; the stages (S1…S9) and the
compiler mechanics (build / admit / persist) stay internal:

    pgs_change author    [--guided] --worker … --model … [--stage N]   # S1–S7  → CR-IR
    pgs_change construct  --projection … --domain … --subdomain … [--persist DIR]
                                                                       # CR-IR  → ADMITTED_UNVALIDATED
    pgs_change validate   --dossier blockchain/chain                   #        → EXECUTION_VALIDATED
    pgs_change promote    --dossier … --registry-root … [--from DIR] [--confirm]   # S9

This module is a THIN facade: every verb forwards into the existing engine modules unchanged
(`run_dossier` / `run_interactive` / `construction_cli` / `lifecycle_cli`). It contains no
authoring, construction, validation, or promotion logic — only dispatch. That is what lets the
internals be reorganized later without moving this contract.
"""
from __future__ import annotations

import argparse
import os
import sys

from . import construction_cli, lifecycle_cli, run_dossier, run_interactive

_USAGE = __doc__


def _author(rest: list[str]) -> int:
    """S1–S7. Default transport = automated worker; `--guided` = interactive export/import."""
    if "--guided" in rest:
        return run_interactive.main([a for a in rest if a != "--guided"])
    return run_dossier.main(rest)


def _construct(rest: list[str]) -> int:
    """CR-IR → ADMITTED_UNVALIDATED. Internally: build (write finale .md) → admit (Compilation Unit).

    `build` and `admit` are compiler mechanics, deliberately hidden behind the single `construct` verb.
    """
    ap = argparse.ArgumentParser(prog="pgs_change construct",
                                 description="Compile the CR-IR into an admitted protocol delta.")
    ap.add_argument("--projection", required=True, help="Construction Projection dir (the cr_ir dir)")
    ap.add_argument("--domain", required=True)
    ap.add_argument("--subdomain", required=True)
    ap.add_argument("--workspace", default=os.environ.get("PGS_WORKSPACE"))
    ap.add_argument("--out", default="constructed",
                    help="write the finale artifact set (.md) here — the input to `promote` (default: constructed/)")
    ap.add_argument("--include", action="append", default=[], metavar="DIR",
                    help="supplementary artifact source dir(s) merged into the Compilation Unit (repeatable)")
    ap.add_argument("--persist", metavar="DIR",
                    help="persist the ADMITTED_UNVALIDATED test-snapshot at DIR (full isolated build)")
    ap.add_argument("--structure", help="build STRUCTURE (default: STRUCTURE_BUILD_<DOMAIN>_CONFIG_V0)")
    args = ap.parse_args(rest)
    args.domain_repo = None  # cmd_admit reads this; not exposed on the lifecycle verb

    rc = construction_cli.cmd_build(args)          # generate the delta → args.out
    if rc != 0:
        return rc
    return construction_cli.cmd_admit(args)        # form the Compilation Unit and ask the compiler


_VERBS = {
    "author": _author,
    "construct": _construct,
    "validate": lambda rest: lifecycle_cli.main(["validate", *rest]),
    "promote": lambda rest: lifecycle_cli.main(["promote", *rest]),
}


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(_USAGE)
        return 0 if argv else 2
    verb, rest = argv[0], argv[1:]
    fn = _VERBS.get(verb)
    if fn is None:
        print(f"pgs_change: unknown verb {verb!r} — expected one of: {', '.join(_VERBS)}", file=sys.stderr)
        print(_USAGE, file=sys.stderr)
        return 2
    return fn(rest)


if __name__ == "__main__":
    raise SystemExit(main())

"""Thin CLI over the pipeline-3 lifecycle services — `validate` and `promote`.

The CLI parses args and renders; all mechanics live in the services (Patch 4). Generic across CRs: the
only CR-specific input is the dossier's declared `acceptance_scenario`.

    python -m pgs_change_mgmt.engine.lifecycle_cli validate --dossier blockchain/chain
    python -m pgs_change_mgmt.engine.lifecycle_cli promote  --dossier blockchain/chain [--confirm]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import validation as V

PASS, FAIL = 0, 2


def _dossier_path(arg: str) -> tuple[Path, str, str]:
    """`blockchain/chain` (or an abs path) → (dossier_dir, domain, subdomain)."""
    p = Path(arg)
    if not p.is_absolute():
        p = Path(__file__).resolve().parents[2] / "change_mgmt" / "dossiers" / arg
    domain, subdomain = p.parent.name, p.name
    return p, domain, subdomain


def _workspace() -> Path:
    ws = os.environ.get("PGS_WORKSPACE", "")
    if not ws:
        print("error: set PGS_WORKSPACE (absolute path)", file=sys.stderr)
        raise SystemExit(FAIL)
    return Path(ws)


def _tick(ok: bool) -> str:
    return "✓" if ok else "✗"


def cmd_validate(args) -> int:
    dossier, domain, subdomain = _dossier_path(args.dossier)
    try:
        report = V.validate(dossier, domain=domain, subdomain=subdomain, workspace=_workspace())
    except V.ValidationError as exc:
        print(f"Validation Status : FAIL\n  {exc}")
        return FAIL

    print(f"Validation Status : {report.verdict}")
    print(f"  Subject         : {report.subject}")
    print(f"  Construction    : {report.construction['delta_present']} artifacts, {report.construction['status']}")
    print(f"  Scenario        : {report.scenario_code}")
    print(f"  Objective       : {report.objective}")
    print("  Steps")
    for s in report.steps:
        print(f"    {s.step}  {s.workflow.split('::')[-1]:<32} → {s.outcome:<8} {_tick(s.passed)}")
    print("  Observations")
    for o in report.observations:
        print(f"    {o.address}  == {json.dumps(o.expected)}  (actual {json.dumps(o.actual)})  {_tick(o.passed)}")
    print("  Acceptance Intent (proven by the scenario)")
    for c in report.criteria:
        print(f"    {c.id}  {c.statement:<52} {_tick(c.proven)}  ← {', '.join(c.satisfied_by)}")
    print(f"  Evidence        : {dossier / 'validation' / 'validation_report.json'}")
    return PASS if report.verdict == "PASS" else FAIL


def cmd_promote(args) -> int:
    """Promotion gate — boring by construction: refuse unless PASS validation evidence exists for this
    CR. The actual fast-forward into the production snapshot is a deliberate, guarded step (--confirm)."""
    dossier, domain, subdomain = _dossier_path(args.dossier)
    report_path = dossier / "validation" / "validation_report.json"
    if not report_path.exists():
        print(f"Promotion REFUSED — no validation evidence at {report_path}\n"
              f"  run: validate --dossier {args.dossier}")
        return FAIL
    report = json.loads(report_path.read_text())
    if report.get("verdict") != "PASS":
        print(f"Promotion REFUSED — validation verdict is {report.get('verdict')!r} (need PASS).")
        return FAIL

    print(f"Promotion gate    : PASS  (validation evidence {report.get('status')})")
    print(f"  Subject         : {report.get('subject')}")
    print(f"  Scenario        : {report.get('scenario_code')}")
    if not args.confirm:
        print("  Ready to promote. Re-run with --confirm to fast-forward the validated candidate into "
              "the production snapshot (a deliberate, hard-to-reverse step).")
        return PASS
    # Actual promotion (candidate → protocol_snapshot) is intentionally not automated here yet — it
    # mutates the production snapshot and is owned by the operator. See validation_pipeline_design §8.
    print("  --confirm given, but automated production promotion is not enabled in this build.\n"
          "  Promote manually via the governed snapshot build once you have reviewed the evidence.")
    return PASS


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="pgs lifecycle", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate", help="execute the CR's acceptance scenario against a candidate snapshot")
    v.add_argument("--dossier", required=True, help="domain/subdomain (e.g. blockchain/chain) or abs path")
    v.set_defaults(fn=cmd_validate)
    p = sub.add_parser("promote", help="gate: promote only if validation evidence is PASS")
    p.add_argument("--dossier", required=True)
    p.add_argument("--confirm", action="store_true", help="perform the promotion (deliberate)")
    p.set_defaults(fn=cmd_promote)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())

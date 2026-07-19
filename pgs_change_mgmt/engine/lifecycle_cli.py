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
from datetime import datetime, timezone
from pathlib import Path

from . import governance_surface
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

    finale = Path(args.frm)
    if not finale.is_absolute():
        finale = Path.cwd() / finale
    if not finale.exists():
        print(f"Promotion REFUSED — finale artifact dir not found: {finale}\n"
              f"  produce it first: construct … --out {args.frm}")
        return FAIL

    # Governance gate — a CR discovers the surface changes it needs (governance_impact.json) but never
    # performs them. Promotion refuses until the canonical surface already satisfies the impact; the
    # governance authority approves separately. Promotion NEVER writes governance.
    gi_path = finale / "governance_impact.json"
    if gi_path.exists():
        impact_doc = json.loads(gi_path.read_text())
        missing = governance_surface.missing_approvals(impact_doc)
        if missing:
            print("Governance gate   : BLOCKED — the canonical CT surface does not yet admit:")
            for fq in missing:
                print(f"    - {fq}")
            print(f"  These are DISCOVERY, not authority: the governance authority must approve them "
                  f"(add to the canonical surface). See {gi_path}. Promotion never writes governance.")
            return FAIL
        print("Governance gate   : PASS  (all required CT surface additions approved)")

    if not args.confirm:
        print("  Ready to promote. Re-run with --confirm to copy the finale artifact set into the owning "
              "source registries and let the compiler be the gate (a deliberate, hard-to-reverse step).")
        return PASS

    # Actual promotion (S9) — KISS: copy the finale artifact set into each owning PROTOCOL SOURCE
    # registry (never the read-only snapshot), then the compiler is the gate. Rollback-all-on-red.
    from . import bridge
    structure = f"STRUCTURE_BUILD_{domain.upper()}_CONFIG_V0"
    override = Path(args.registry_root) if args.registry_root else None
    dest_desc = str(override) if override else "governed owner registries (from placement manifest)"
    print(f"  Promoting {domain}/{subdomain} finale set → {dest_desc}  (compiler is the gate) ...")
    try:
        res = bridge.promote_set(finale, registry_root=override,
                                 workspace=_workspace(), build_structure=structure)
    except FileNotFoundError as exc:
        print(f"Promotion REFUSED — {exc}")
        return FAIL
    for d in res.dests:
        print(f"    → {d}")
    if res.ok:
        # S9 closure evidence — the Promotion certificate, symmetric with validation_report.json.
        # Records the PROMOTED transition: what was promoted, where, and that the compiler accepted it.
        report_out = dossier / "promotion" / "promotion_report.json"
        report_out.parent.mkdir(parents=True, exist_ok=True)
        report_out.write_text(json.dumps({
            "subject": report.get("subject"),
            "scenario_code": report.get("scenario_code"),
            "status": "PROMOTED",
            "validation_evidence": report.get("status"),
            "artifacts_promoted": len(res.dests),
            "repos": res.repos,
            "destinations": [str(d) for d in res.dests],
            "snapshot": "compiles + validates (pi validate --strict)",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }, indent=2) + "\n")
        print(f"  Promotion COMPLETE — {len(res.dests)} artifacts promoted into "
              f"{len(res.repos)} repo(s): {', '.join(res.repos)}; snapshot compiles + validates.")
        print(f"  Evidence          : {report_out}")
        return PASS
    print("  Promotion FAILED — rolled back (registry unchanged). Compiler diagnostics:")
    for ln in res.diagnostics:
        print("      " + ln)
    return FAIL


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="pgs lifecycle", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate", help="execute the CR's acceptance scenario against a candidate snapshot")
    v.add_argument("--dossier", required=True, help="domain/subdomain (e.g. blockchain/chain) or abs path")
    v.set_defaults(fn=cmd_validate)
    p = sub.add_parser("promote", help="gate: promote only if validation evidence is PASS")
    p.add_argument("--dossier", required=True)
    p.add_argument("--registry-root", dest="registry_root", default=None,
                   help="OPTIONAL override of the promotion destination root (e.g. a throwaway dir for a "
                        "dry-run). Default: governed owner registries from the placement manifest — a "
                        "cross-repo delta routes to each owning repo. NEVER the read-only protocol_snapshot")
    p.add_argument("--from", dest="frm", default="constructed",
                   help="finale artifact dir (the constructed .md set); default: ./constructed")
    p.add_argument("--confirm", action="store_true", help="perform the promotion (deliberate)")
    p.set_defaults(fn=cmd_promote)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())

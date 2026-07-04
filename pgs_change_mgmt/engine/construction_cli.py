"""Construction Compiler CLI — the thin public interface to the Construction Compiler.

Orchestration ONLY: load the Construction Projection → invoke the Construction Compiler → write
artifacts → print diagnostics. It contains **no** lowering / propagation / binding / type / graph /
rendering logic — all of that lives in the compiler passes (`engine/construction_model.py`). Keeping
the CLI logic-free is what makes the eventual move into `pgs_compiler` (as `pgs construction …`) trivial.
The CLI never knows which artifact families exist — the compiler decides.

    python -m pgs_change_mgmt.engine.construction_cli build \
        --projection <cr_ir_dir> --domain blockchain --subdomain chain --out constructed/
    python -m pgs_change_mgmt.engine.construction_cli validate --projection … --domain … --subdomain …
    python -m pgs_change_mgmt.engine.construction_cli graph    --projection … --domain … --subdomain …
    python -m pgs_change_mgmt.engine.construction_cli explain  --projection … --domain … --subdomain …

Exit codes:  0 = CONSTRUCTION_VALID   ·   2 = CONSTRUCTION_INVALID   ·   1 = usage/error.
"""
from __future__ import annotations

import argparse
import os
from collections import Counter
from pathlib import Path

from .construction_model import build, LOWERING_PIPELINE, PASS_CONSTRAINT

VALID, INVALID = 0, 2


def _run(args):
    ws = args.workspace or os.environ.get("PGS_WORKSPACE")
    if not ws:
        raise SystemExit("error: set --workspace or PGS_WORKSPACE")
    return build(Path(args.projection), domain=args.domain, subdomain=args.subdomain, workspace=Path(ws))


def _pass_status(res) -> list[tuple[str, str]]:
    by_constraint = Counter(v.constraint for v in res.violations)
    rows = [("Normalize", "PASS")]
    for rule, _fn in LOWERING_PIPELINE:
        con = PASS_CONSTRAINT.get(rule)
        rows.append((rule.replace("DEFAULT_", "").replace("_", " ").title(),
                     "PASS" if not con or by_constraint.get(con, 0) == 0 else "FAIL"))
    return rows


def _report(res, projection: str, artifacts: int) -> int:
    g = res.graph
    print("Construction Compiler\n")
    print(f"  Projection:          {projection}")
    print(f"  Nodes:               {len(g.nodes)}")
    print(f"  Edges:               {len(g.edges)}")
    print("  Passes:")
    for name, status in _pass_status(res):
        print(f"      {name:<26s} {status}")
    if res.violations:
        print("  Violations:")
        for con, n in sorted(Counter(v.constraint for v in res.violations).items()):
            print(f"      {n} {con}")
    else:
        print("  Violations:          NONE")
    ok = not res.violations
    print(f"  Artifacts Generated: {artifacts}")
    print(f"  Compiler Status:     {'CONSTRUCTION_VALID' if ok else 'CONSTRUCTION_INVALID'}")
    return VALID if ok else INVALID


def cmd_build(args) -> int:
    res = _run(args)
    written = 0
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        for nid, art in res.artifacts.items():
            if isinstance(art, str):                       # a serialized (constraint-clean) artifact
                (out / f"{nid.split('::')[-1]}.md").write_text(art)
                written += 1
    else:
        written = sum(1 for a in res.artifacts.values() if isinstance(a, str))
    code = _report(res, f"{args.domain}/{args.subdomain}", written)
    if args.out and written:
        print(f"  Output:              {args.out}")
    return code


def cmd_validate(args) -> int:
    res = _run(args)
    return _report(res, f"{args.domain}/{args.subdomain}",
                   sum(1 for a in res.artifacts.values() if isinstance(a, str)))


def cmd_graph(args) -> int:
    g = _run(args).graph
    print("Construction Graph\n")
    print("  Nodes:")
    for concept, n in sorted(Counter(x.concept for x in g.nodes.values()).items()):
        print(f"      {concept:<24s} {n}")
    print("  Edges:")
    for role, n in sorted(Counter(e.role for e in g.edges).items()):
        print(f"      {role:<24s} {n}")
    return VALID


def cmd_admit(args) -> int:
    """Compilation Unit → Protocol Compiler — the compiler-to-compiler contract (no mutation)."""
    from . import compilation_unit as cu
    res = _run(args)
    artifacts = {nid: a for nid, a in res.artifacts.items() if isinstance(a, str)}   # keep FQDN for ownership
    if res.violations or not artifacts:
        print("Construction is not VALID — nothing to admit (run `build` / `validate` first).")
        return INVALID
    structure = args.structure or f"STRUCTURE_BUILD_{args.domain.upper()}_CONFIG_V0"
    adm = cu.admit(artifacts, domain=args.domain, subdomain=args.subdomain, structure=structure)
    print(adm.manifest(structure=structure))
    if not adm.ok:
        print("\n  --- compiler diagnostics (tail) ---")
        for ln in adm.output.strip().splitlines()[-14:]:
            print("      " + ln)
    return VALID if adm.ok else INVALID


def cmd_explain(args) -> int:
    res = _run(args)
    if not res.violations:
        print("No violations — CONSTRUCTION_VALID.")
        return VALID
    print("Violations (why construction is not yet valid):\n")
    for v in res.violations:
        print(f"  [{v.constraint}] {v.obj}\n      {v.detail}  ({v.gap_class})")
    return INVALID


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="pgs construction", description="Construction Compiler CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn, has_out in [("build", cmd_build, True), ("validate", cmd_validate, False),
                              ("graph", cmd_graph, False), ("explain", cmd_explain, False),
                              ("admit", cmd_admit, False)]:
        p = sub.add_parser(name)
        p.add_argument("--projection", required=True, help="Construction Projection dir (the cr_ir dir)")
        p.add_argument("--domain", required=True)
        p.add_argument("--subdomain", required=True)
        p.add_argument("--workspace", default=os.environ.get("PGS_WORKSPACE"))
        if has_out:
            p.add_argument("--out", help="write serialized artifacts here (constraint-clean nodes only)")
        if name == "admit":
            p.add_argument("--domain-repo", dest="domain_repo",
                           help="path to the domain repo (default: sibling pgs_<domain>)")
            p.add_argument("--structure", help="build STRUCTURE (default: STRUCTURE_BUILD_<DOMAIN>_CONFIG_V0)")
        p.set_defaults(fn=fn)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())

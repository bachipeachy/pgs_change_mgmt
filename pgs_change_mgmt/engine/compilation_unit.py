"""Compilation Unit — the Construction Compiler ↔ Protocol Compiler contract, as a **virtual federation
workspace**.

A Compilation Unit packages a **canonical view** of every involved repository with a **candidate
overlay**, and lets `pgs_compiler` answer *"can the Protocol Compiler consume what the Construction
Compiler emitted?"* → PASS / FAIL — **with no repository mutation** (`SINGLE_COMPILATION_CONTEXT`).

Two conceptually distinct phases (kept separate for testability):
  1. **Ownership Resolution** — *where does each artifact belong?* → `ownership.resolve` (governed).
  2. **Federation Assembly** — *build the virtual workspace* → `assemble` (mount = copy today; overlay
     filesystem / symlink tree / in-memory mount tomorrow, without changing Compilation Unit semantics).

There is **no promotion here.** Admission is purely observational: it ends at an Admission Manifest and
STOPs. Promotion (`copy_if_green` into canonical repos + snapshot rebuild + S9) is a separate concern
that runs *only after* a PASS, and can consume the manifest rather than rediscovering ownership.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from pgs_governance.implementation.artifact_kinds import REGISTRY   # kind → registry sub-dir (single source)

import re

from . import ownership
from . import governance_surface

# Responsible-Phase triage map for admission assertions. This is a *diagnostic aid* for the Admission
# Report (which phase owns a failure) — NOT governance logic and NOT consulted during construction; the
# Construction Compiler never becomes aware of governance rules. Four outcomes: PAS renderer enhancement,
# Projection/Contract enhancement, Governance surface expansion, or (rare) a Compiler bug.
RESPONSIBLE_PHASE: dict[str, str] = {
    "ASSERT_SCHEMA_CONFORMANCE": "PAS Renderer",
    "ASSERT_TOPOLOGY_INPUT_REFERENCE_DECLARED": "PAS Renderer",
    "ASSERT_CT_SURFACE_CLOSED": "Governance surface",
    "ASSERT_CS_SURFACE_CLOSED": "Governance surface",
    "ASSERT_CC_STORAGE_OP_CONFORMANCE": "Contract / Projection",
}


def _phase_for(assertion: str) -> str:
    key = re.sub(r"(_BLOCKCHAIN)?_V\d+$", "", assertion)      # strip domain suffix + version
    return RESPONSIBLE_PHASE.get(key, "Protocol Compiler / unclassified")


@dataclass
class Mount:
    """One repository in the federation: its canonical source and its mounted view (canonical+overlay)."""
    repo: str
    canonical: Path
    view: Path


@dataclass
class Placement:
    fqdn: str
    code: str
    kind: str
    owner_layer: str
    repo: str
    overlay: str            # path of the candidate within the mount, relative to the registry
    registry_root: str = "" # governed owner registry root (absolute) — where a promotion writes this


@dataclass
class CompilationUnit:
    domain: str
    subdomain: str
    root: Path
    mounts: dict[str, Mount] = field(default_factory=dict)
    placements: list[Placement] = field(default_factory=list)

    @property
    def pythonpath(self) -> str:
        # every mounted package is copied to root/<package>; a single entry (root) imports them all —
        # shadowing the editable installs — while unmounted repos still resolve from site-packages.
        # This is layout-agnostic: it works for doubly-nested domain repos and the singly-nested,
        # namespace-package governance repo alike (the package dir is what gets mounted, not the repo).
        return str(self.root)


@dataclass
class Assertion:
    name: str
    stage: str
    count: int
    phase: str          # Responsible Phase — which phase owns the fix


@dataclass
class Admission:
    unit: CompilationUnit
    ok: bool
    output: str
    per_artifact: dict[str, str] = field(default_factory=dict)   # fqdn → outcome
    assertions: list["Assertion"] = field(default_factory=list)  # structured failures (Responsible Phase)

    def manifest(self, *, structure: str = "") -> str:
        u = self.unit
        L = ["Compilation Unit — Admission Manifest", "=" * 42,
             f"Domain: {u.domain}    Subdomain: {u.subdomain}    Compiler: pgs_compiler"
             + (f" · {structure}" if structure else ""),
             f"Federation mounts ({len(u.mounts)}): "
             + ", ".join(f"{m.repo} (canonical→view)" for m in u.mounts.values()),
             "",
             f"  {'artifact':32s} {'kind':4s} {'owner layer':20s} {'repo':16s} outcome"]
        for p in u.placements:
            L.append(f"  {p.code:32s} {p.kind:4s} {p.owner_layer:20s} {p.repo:16s} "
                     f"{self.per_artifact.get(p.fqdn, '—')}")
        if self.assertions:
            L += ["", "Admission failures (by Responsible Phase):",
                  f"  {'assertion':44s} {'stage':14s} {'n':>3s}  responsible phase"]
            for a in self.assertions:
                L.append(f"  {a.name:44s} {a.stage:14s} {a.count:>3d}  {a.phase}")
        L += ["", f"Result: {'PASS — admitted' if self.ok else 'FAIL — rejected'}"]
        return "\n".join(L)


# --- Compilation Unit sources (origin-agnostic) -----------------------------------------------------

def load_sources(dirs, *, default_namespace: str) -> dict[str, str]:
    """Load `.md` artifact sources from one or more directories into a `{fqdn: markdown}` map.

    A Compilation Unit is assembled from artifact *sources* with no regard for why an artifact is
    present — a source may be a generated delta, a reused protocol library, a shared cross-domain
    artifact, or temporary support. This loader is that origin-agnostic ingest for on-disk sources.

    An artifact source file is **namespace-qualified** by the snapshot filename convention
    `<namespace>__<CODE>.md` (`::` → `__`), so each file self-declares its FQDN and can be placed by
    ownership resolution with no per-CR wiring. Any `.md` without `__` (README, notes) is treated as
    documentation and ignored. `default_namespace` is accepted for signature stability but not needed
    when files are qualified. Duplicate FQDNs across sources are refused.
    """
    artifacts: dict[str, str] = {}
    for d in dirs:
        d = Path(d)
        if not d.is_dir():
            raise FileNotFoundError(f"artifact source directory not found: {d}")
        for f in sorted(d.glob("*.md")):
            if "__" not in f.stem:
                continue  # documentation, not a namespace-qualified artifact
            fqdn = f.stem.replace("__", "::", 1)
            if fqdn in artifacts:
                raise ValueError(f"duplicate artifact {fqdn!r} across Compilation Unit sources")
            artifacts[fqdn] = f.read_text()
    return artifacts


# --- Phase 2: Federation Assembly -------------------------------------------------------------------

_IGNORE = shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".venv", ".idea")


def _mount_package(unit: CompilationUnit, package_dir: Path) -> Mount:
    """Mount an importable package once as a read-only copy under `root/<package>`. Mounting the
    *package* (not the repo) is layout-agnostic: `root/<package>` is importable via PYTHONPATH=root
    regardless of whether the canonical repo nests the package one or two levels deep."""
    name = package_dir.name
    if name not in unit.mounts:
        view = unit.root / name
        shutil.copytree(package_dir, view, ignore=_IGNORE)
        unit.mounts[name] = Mount(name, package_dir, view)
    return unit.mounts[name]


def assemble(artifacts: dict[str, str], *, domain: str, subdomain: str) -> CompilationUnit:
    """Build the virtual federation workspace: for each candidate, resolve its owner (Phase 1), mount
    that owner *package* once (copy), and overlay the candidate at its registry location. The
    construction `subdomain` applies only to artifacts owned by the domain under construction; reusable
    capabilities place at `registry/<kind_dir>/` per their own layer's layout.

    Candidate governance-surface overlays (declaring new CTs legal) are applied last, onto the same
    read-only copies — so a construction's new opcodes are admitted *inside the unit*, never in the
    canonical governance registry (`governance_surface`)."""
    root = Path(tempfile.mkdtemp(prefix="compilation_unit_"))
    unit = CompilationUnit(domain=domain, subdomain=subdomain, root=root)
    for fqdn, md in artifacts.items():
        owner = ownership.resolve(fqdn)                                    # Phase 1: Ownership Resolution
        m = _mount_package(unit, owner.repo_root / owner.package)          # mount the importable package
        code = fqdn.split("::")[-1]
        kind_dir = REGISTRY.directory(code.split("_", 1)[0])
        sub = subdomain if owner.namespace == domain else None            # subdomain only for constructed domain
        rel = (Path(sub) if sub else Path()) / kind_dir / f"{code}.md"
        dest = m.view / "registry" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(md)
        unit.placements.append(Placement(fqdn, code, code.split("_", 1)[0],
                                         owner.layer, m.repo, str(rel), str(owner.registry_root)))
    for ov in governance_surface.surface_overlays([f for f in artifacts if governance_surface.is_ct(f)]):
        m = _mount_package(unit, ov.package_dir)                          # surface's owner (may be pgs_governance)
        surf = m.view / ov.rel
        surf.write_text(governance_surface.compose(surf.read_text(), ov.entries))
    return unit


# --- Placement Manifest: the ownership decision, computed once and persisted ------------------------
#
# Ownership Resolution (Phase 1) is the single authoritative place that answers *where does each
# artifact belong*. The Placement Manifest persists that decision so every downstream concern —
# promotion, packaging, release notes, impact analysis, dependency visualization — CONSUMES it rather
# than re-resolving ownership. Compute once, persist, consume everywhere; never rediscover an
# authoritative decision.

PLACEMENT_MANIFEST = "placement_manifest.json"


def build_plan(unit: CompilationUnit) -> dict:
    """The declared REBUILD SCOPE — computed once here from ownership, consumed verbatim by promotion.

    A delta that stays inside the constructed domain rebuilds only that domain's structure. A delta
    that touches *any other namespace* — a domain-neutral / platform artifact such as a reusable
    `capability_transforms::` transform — is platform-touching and rebuilds the whole platform (every
    structure). Promotion executes this plan; it never re-derives whether a CR is "mixed" or decides
    how much to rebuild. Scope is data, declared here; not logic, inferred there."""
    domain = unit.domain
    cross = sorted({p.fqdn.split("::", 1)[0] for p in unit.placements
                    if p.fqdn.split("::", 1)[0] != domain})
    if cross:
        return {"mode": "all", "structures": [],
                "reason": f"platform-touching — cross-namespace artifact(s): {', '.join(cross)}"}
    return {"mode": "structures",
            "structures": [f"STRUCTURE_BUILD_{domain.upper()}_CONFIG_V0"],
            "reason": f"domain-only ({domain})"}


def placement_manifest(unit: CompilationUnit) -> dict:
    """The artifact-placement decision for a Compilation Unit, as a serializable manifest.

    Each entry carries the governed destination — owner `registry_root` + registry-relative
    `relative_path` — so a consumer writes `registry_root / relative_path` with zero ownership logic.
    The `build_plan` declares the rebuild scope promotion must execute (compute once, consume there).
    """
    return {
        "domain": unit.domain,
        "subdomain": unit.subdomain,
        "build_plan": build_plan(unit),
        "placements": [
            {"code": p.code, "fqdn": p.fqdn, "kind": p.kind, "owner_layer": p.owner_layer,
             "package": p.repo, "registry_root": p.registry_root, "relative_path": p.overlay}
            for p in sorted(unit.placements, key=lambda p: p.code)
        ],
    }


def write_placement_manifest(unit: CompilationUnit, out_dir: Path) -> Path:
    """Persist the Placement Manifest alongside the finale artifact set (the input to promotion)."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / PLACEMENT_MANIFEST
    path.write_text(json.dumps(placement_manifest(unit), indent=2) + "\n")
    return path


# --- Phase 3: Protocol Compiler invocation (diagnostics only, no mutation) --------------------------

def _parse_assertions(output: str) -> list[Assertion]:
    stage = ""
    m = re.search(r"failed at (S\d+_\w+)", output) or re.search(r"(S\d+_\w+) failed with", output)
    if m:
        stage = m.group(1)
    seen: dict[str, int] = {}
    for am in re.finditer(r"(ASSERT_[A-Z0-9_]+_V\d+)\s+[—-]+\s+(\d+)\s+violation", output):
        seen[am.group(1)] = int(am.group(2))
    return [Assertion(name=n, stage=stage, count=c, phase=_phase_for(n)) for n, c in seen.items()]


def compile_unit(unit: CompilationUnit, *, structure: str, timeout: float = 300.0) -> Admission:
    try:
        env = dict(os.environ, PYTHONPATH=unit.pythonpath)      # candidate views shadow the editable installs
        r = subprocess.run(["python", "-m", "pgs_compiler.cli", "compile", "--structure", structure],
                           capture_output=True, text=True, env=env, timeout=timeout)
        ok = r.returncode == 0
        out = r.stdout + r.stderr
        per = {p.fqdn: ("ADMITTED" if ok else ("REJECTED" if p.code in out else "—")) for p in unit.placements}
        return Admission(unit=unit, ok=ok, output=out, per_artifact=per, assertions=_parse_assertions(out))
    finally:
        shutil.rmtree(unit.root, ignore_errors=True)


def admit(artifacts: dict[str, str], *, domain: str, subdomain: str, structure: str,
          timeout: float = 300.0) -> Admission:
    """Ownership Resolution + Federation Assembly + compile. Non-mutating; canonical repos untouched."""
    return compile_unit(assemble(artifacts, domain=domain, subdomain=subdomain),
                        structure=structure, timeout=timeout)


# --- Persisted target: the admitted Compilation Unit as a test-snapshot candidate -------------------

# The compile-contributing repos of the platform build topology — the same set the real sync script
# (pgs_compiler/scripts/sync_protocol_snapshot.sh) reads — plus the compiler itself, copied so the
# sync's BASE_DIR resolves to the isolated base rather than the editable install. Platform topology,
# not CR-specific: the persisted build is domain-agnostic.
_BUILD_REPOS = ("pgs_governance", "pgs_capabilities", "pgs_blockchain", "pgs_ai_governance", "pgs_compiler")


@dataclass
class Persisted:
    ok: bool
    workspace: Path
    delta_present: list[str]
    delta_missing: list[str]
    output: str


def _isolated_pythonpath(base: Path) -> str:
    """PYTHONPATH that makes every governed package in `base` importable, shadowing editable installs.

    A repo whose root is itself a package (`<repo>/__init__.py`) imports from `base`; a container repo
    (packages nested one level in, e.g. pgs_capabilities/pgs_transforms) needs `base/<repo>` on the path.
    Derived from layout, so it is agnostic to how each repo nests its package(s)."""
    parts = [str(base)]
    for repo in _BUILD_REPOS:
        if (base / repo).is_dir() and not (base / repo / "__init__.py").exists():
            parts.append(str(base / repo))
    return os.pathsep.join(parts)


def persist_test_snapshot(artifacts: dict[str, str], *, domain: str, subdomain: str,
                          out_workspace: Path, timeout: float = 900.0) -> Persisted:
    """Persist the admitted Compilation Unit as a COMPLETE, compile-verified test-snapshot candidate.

    Baseline platform topology + generated delta + supplementary artifacts, compiled by the REAL
    compiler and assembled by the REAL sync into `out_workspace` — with zero mutation of the canonical
    repos (everything happens under an isolated federation base). This is the *persisted* form of the
    Snapshot Admission Gate: the same Compilation Unit written to disk instead of thrown away, so the
    Implementation and Execution-Validation phases consume the exact admitted snapshot.

    The gate here is compile-time admissibility (`compile --all-structures` succeeds + the delta lands
    in the assembled snapshot). Runtime conformance (`pi validate --strict`, `pgs_runtime run`) is a
    LATER phase — it executes CT/CS implementations, which admission does not require — so the snapshot
    is marked ADMITTED_UNVALIDATED, never VALID, until those implementations exist and `pgs build` runs.
    """
    out_workspace = Path(out_workspace)
    pgs_root = ownership.resolve(f"{domain}::_PROBE_V0").repo_root.parent   # sibling root, derived — not hardcoded
    base = Path(tempfile.mkdtemp(prefix="persist_base_"))
    try:
        ignore = shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".venv", ".idea", "compiled")
        for repo in _BUILD_REPOS:
            shutil.copytree(pgs_root / repo, base / repo, ignore=ignore)

        # overlay generated delta + supplementary artifacts into the base registries
        for fqdn, md in artifacts.items():
            owner = ownership.resolve(fqdn)
            code = fqdn.split("::")[-1]
            kind_dir = REGISTRY.directory(code.split("_", 1)[0])
            sub = subdomain if owner.namespace == domain else None
            dest = (base / owner.repo_root.name / owner.package / "registry"
                    / (Path(sub) if sub else Path()) / kind_dir / f"{code}.md")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(md)
        for ov in governance_surface.surface_overlays([f for f in artifacts if governance_surface.is_ct(f)]):
            surf = base / ov.package_dir.relative_to(pgs_root) / ov.rel
            surf.write_text(governance_surface.compose(surf.read_text(), ov.entries))

        env = dict(os.environ, PYTHONPATH=_isolated_pythonpath(base))
        out = ""

        # compile every structure so the assembled snapshot is complete (the delta rides inside it)
        r = subprocess.run(["python", "-m", "pgs_compiler.cli", "compile", "--all-structures"],
                           capture_output=True, text=True, env=env, timeout=timeout)
        out += r.stdout + r.stderr
        if r.returncode != 0:
            return Persisted(False, out_workspace, [], sorted(artifacts), out)

        # assemble the snapshot with the REAL sync (BASE_DIR resolves to the isolated base)
        out_workspace.mkdir(parents=True, exist_ok=True)
        sync = base / "pgs_compiler" / "scripts" / "sync_protocol_snapshot.sh"
        senv = dict(env, PGS_WORKSPACE=str(out_workspace), PGS_INVOKED_BY_BUILD="1")
        r = subprocess.run(["bash", str(sync)], capture_output=True, text=True, env=senv, timeout=timeout)
        out += r.stdout + r.stderr
        if r.returncode != 0:
            return Persisted(False, out_workspace, [], sorted(artifacts), out)

        # federated query metadata (consumed by pi / change-mgmt evidence)
        from pgs_compiler.compiler.projections.artifact_index import build_artifact_index, write_artifact_index
        from pgs_compiler.compiler.projections.store_index import build_store_index, write_store_index
        write_artifact_index(out_workspace, build_artifact_index(out_workspace))
        write_store_index(out_workspace, build_store_index(out_workspace))

        # confirm the delta actually landed in the assembled snapshot
        artifacts_dir = out_workspace / "protocol_snapshot" / "artifacts"
        gov_dir = out_workspace / "protocol_snapshot" / "governance" / "artifacts"
        present, missing = [], []
        for fqdn in sorted(artifacts):
            fname = fqdn.replace("::", "__") + ".json"
            found = any(artifacts_dir.rglob(fname)) or any(gov_dir.rglob(fname))
            (present if found else missing).append(fqdn)

        # honest marker: admitted at compile time, NOT execution-validated (impls pending) — never VALID
        status = {
            "status": "ADMITTED_UNVALIDATED",
            "reason": "compile-admitted test-snapshot candidate; conformance/execution not run "
                      "(implementations pending). Not for production consumption.",
            "compile_verified": True,
            "delta_artifacts": len(present),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        (out_workspace / "snapshot_status.json").write_text(json.dumps(status, indent=2) + "\n")

        return Persisted(not missing, out_workspace, present, missing, out)
    finally:
        shutil.rmtree(base, ignore_errors=True)

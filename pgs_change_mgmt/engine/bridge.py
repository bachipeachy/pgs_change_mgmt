"""Construction → Compiler bridge (Phase 6) — promote a constructed artifact into the protocol source
and let the compiler be the gate.

The construction worker emits an artifact's authoring markdown (header + prose + ``## Machine`` block).
This bridge closes the SDLC loop: it writes that markdown to the domain registry at the governed path,
runs the compiler, and validates the snapshot. The compiler is the acceptance gate — nothing here
judges the artifact; the protocol does.

TRANSITIONAL — PROMOTION IS AN SDLC CONCERN, NOT A CM CONCERN. Writing the constructed artifact into
the *domain* registry (`registry_root`) is a cross-repo mutation: a known transitional shortcut. CM
governs; it must not mutate repositories. The long-term home of this promote step is the SDLC pipeline
(Authoring → Construction → **Promotion** → Compiler → Verification), not this bridge — it is kept here
only to close the loop end-to-end while the Construction/Promotion boundary is built out.

Design:
  * PATH IS DERIVED, NOT GUESSED — the registry sub-directory comes from the ArtifactKindRegistry
    (`REGISTRY.directory(prefix)`), the same single source of truth the compiler uses. No hardcoded
    kind→dir map (that was the substrate sprawl we retired).
  * COMPILER IS THE GATE — `compile --structure` + `pi validate --strict`. Green ⇒ the constructed
    artifact is admissible protocol; red ⇒ it is not.
  * GENERATE, NEVER PATCH — on failure the artifact is rolled back (removed) and the compiler
    diagnostics are returned. The next iteration REGENERATES from the mandate + those diagnostics; the
    registry only ever retains validated artifacts. (See feedback_artifact_generate_not_patch.)
  * NO HARDCODED PATHS — registry root, subdomain and workspace are explicit parameters.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from pgs_governance.implementation.artifact_kinds import REGISTRY

_CODE_HEADER = re.compile(r"^-\s*\*\*Artifact Code:\*\*\s*([A-Z][A-Z0-9_]*_V\d+)", re.MULTILINE)
_CODE_TITLE = re.compile(r"^#\s*([A-Z][A-Z0-9_]*_V\d+)\s*$", re.MULTILINE)


def artifact_code(authoring_md: str) -> str:
    """The artifact code declared in the authoring markdown (header line, else the title)."""
    m = _CODE_HEADER.search(authoring_md) or _CODE_TITLE.search(authoring_md)
    if not m:
        raise ValueError("no 'Artifact Code' / title code found in authoring markdown")
    return m.group(1)


def registry_dest(registry_root: Path, subdomain: str, code: str) -> Path:
    """Governed source path for an artifact: <registry>/<subdomain>/<kind_dir>/<CODE>.md.

    `kind_dir` is resolved from the ArtifactKindRegistry by the code's type prefix — never hardcoded.
    """
    prefix = code.split("_", 1)[0]
    kind_dir = REGISTRY.directory(prefix)   # raises ValueError on an unknown kind (the legacy contract)
    return Path(registry_root) / subdomain / kind_dir / f"{code}.md"


@dataclass
class BridgeResult:
    code: str
    dest: Path
    compiled: bool = False
    validated: bool = False
    kept: bool = False                      # True ⇒ artifact retained in the registry (green)
    diagnostics: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.compiled and self.validated and self.kept


def _run(cmd: list[str], cwd: Path | None = None, timeout: float = 600.0) -> tuple[bool, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)
        return r.returncode == 0, (r.stdout + r.stderr)
    except Exception as exc:  # transport / timeout failures are diagnostics, not crashes
        return False, f"{type(exc).__name__}: {exc}"


def _diagnostics(output: str, code: str, limit: int = 12) -> list[str]:
    """The compiler/validator lines worth feeding back to regeneration."""
    keep = [ln for ln in output.splitlines()
            if any(k in ln for k in ("ERROR", "FAIL", "violation", "Unknown", code))]
    return keep[:limit] or output.strip().splitlines()[-limit:]


def promote_and_compile(authoring_md: str, *, registry_root: Path, subdomain: str,
                        workspace: Path, build_structure: str,
                        keep_on_fail: bool = False) -> BridgeResult:
    """Write the artifact to the governed registry path, compile + validate, keep-if-green else roll back.

    `build_structure` is the STRUCTURE_BUILD_*_CONFIG the compiler drives (e.g. the blockchain config).
    """
    code = artifact_code(authoring_md)
    dest = registry_dest(registry_root, subdomain, code)
    res = BridgeResult(code=code, dest=dest)

    pre_existing = dest.exists()
    prior = dest.read_text() if pre_existing else None
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(authoring_md)

    compiled, cout = _run(["python", "-m", "pgs_compiler.cli", "compile", "--structure", build_structure])
    res.compiled = compiled
    if not compiled:
        res.diagnostics = _diagnostics(cout, code)
    else:
        built, bout = _run(["python", "-m", "pgs_compiler.cli", "build", "--workspace", str(workspace)])
        validated, vout = _run(["pi", "--workspace", str(workspace), "validate", "--strict"])
        res.validated = built and validated
        if not res.validated:
            res.diagnostics = _diagnostics(bout + vout, code)

    if res.compiled and res.validated:
        res.kept = True
    elif not keep_on_fail:
        # roll back so a non-admissible artifact never pollutes the registry; next iteration regenerates
        if prior is not None:
            dest.write_text(prior)
        else:
            dest.unlink(missing_ok=True)
            # remove now-empty kind/subdomain dirs the promotion created (leave a pre-existing tree alone)
            for d in (dest.parent, dest.parent.parent):
                try:
                    d.rmdir()
                except OSError:
                    break
    return res

"""Compiler-as-oracle — the objective verdict for the Phase 4A equivalence proof.

The engine treats the compiler as the oracle: an authored artifact is *correct* iff, once
placed in its domain registry, the domain recompiles and the snapshot validates strict. This
is a `CompileOracle` (artifact path → (ok, detail)) the engine calls after rendering.

CONSEQUENTIAL — running this recompiles the domain and rewrites `protocol_snapshot/`. Run it
on a throwaway branch (the artifacts are written into the real domain registry by the engine's
`dest_root`). It shells out to the compiler exactly as the workspace docs prescribe; it never
edits the snapshot by hand.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Callable


def compiler_oracle(
    *,
    workspace: str | None = None,
    structure: str = "STRUCTURE_BUILD_BLOCKCHAIN_CONFIG_V0",
    compiler_repo: str | None = None,
    python: str = "python",
) -> Callable[[Path], "tuple[bool, dict[str, Any]]"]:
    """Build a `CompileOracle`: compile the structure, build the snapshot, validate strict.

    Returns (ok, detail) where ok is True iff the snapshot validates with zero violations.
    The artifact path is informational — the oracle judges the whole recompiled snapshot, the
    real admissibility surface (a single artifact is not admissible in isolation).
    """
    ws = workspace or os.environ.get("PGS_WORKSPACE", "")
    if not ws:
        raise ValueError("compiler_oracle needs a workspace (arg or PGS_WORKSPACE)")
    repo = compiler_repo or str(Path(ws).parent / "pgs_compiler")

    def _run(*argv: str) -> subprocess.CompletedProcess:
        return subprocess.run([python, "-m", "pgs_compiler.cli", *argv],
                              cwd=repo, capture_output=True, text=True,
                              env={**os.environ, "PGS_WORKSPACE": ws})

    def oracle(artifact: Path) -> "tuple[bool, dict[str, Any]]":
        compile_p = _run("compile", "--structure", structure)
        build_p = _run("build", "--workspace", ws)
        # Validate via the same JSON surface the grounding provider uses.
        val = subprocess.run(
            [str(Path(ws) / ".venv" / "bin" / "pi"), "--workspace", ws, "validate", "--strict", "--json"],
            capture_output=True, text=True, env={**os.environ, "PGS_WORKSPACE": ws},
        )
        try:
            payload = json.loads(val.stdout)
            res = payload.get("result", {})
            ok = bool(res.get("valid")) and not res.get("violations")
        except json.JSONDecodeError:
            ok, res = False, {"validate_stderr": val.stderr[-500:]}
        return ok, {
            "artifact": str(artifact),
            "compile_rc": compile_p.returncode,
            "build_rc": build_p.returncode,
            "validate": res,
        }

    return oracle

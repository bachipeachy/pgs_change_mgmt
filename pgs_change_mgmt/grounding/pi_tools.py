"""pi-as-tools — bounded, read-only function wrappers over Protocol Inspection.

This is the Phase 0 substrate for the change-management agent. It maps a curated
set of ``pi`` subcommands to Python functions and to model-facing tool/function
definitions (ollama / OpenAI shape).

Doctrine this module enforces by construction:

  * Read-only.  Every wrapped command is a ``pi`` *query* (``pi answers questions;
    the compiler performs changes; the runtime performs execution``).  No subcommand
    here mutates the snapshot.
  * Evidence, not weights.  Each call returns ``pi``'s stable JSON envelope
    (``query`` / ``result`` / ``schema_version``) verbatim.  The model is meant to
    cite ``result`` payloads, never assert protocol facts from its own parameters.
  * Path-explicit.  The workspace is passed via ``PGS_WORKSPACE`` (or --workspace);
    ``pi`` never guesses from cwd, and neither does this wrapper.

The wrapper deliberately has zero third-party dependencies: ``pi`` is invoked as a
subprocess and its ``--json`` output is parsed with the stdlib.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any, Callable

# Artifact kinds that have a PPS source surface (artifact_source works); others (EV, STRUCTURE,
# AC, TI, …) are routed gracefully to topology_impact / artifact_refs instead of erroring.
SOURCEABLE_KINDS = frozenset({"CC", "CS", "CT", "IN", "RB", "WF"})


class PiError(RuntimeError):
    """A ``pi`` invocation failed (non-zero exit or unparseable JSON).

    Carries the command, exit code, and captured stderr so the orchestrator can
    surface a grounded failure instead of letting the model paper over it.
    """

    def __init__(self, argv: list[str], returncode: int, stderr: str):
        self.argv = argv
        self.returncode = returncode
        self.stderr = stderr.strip()
        super().__init__(
            f"pi failed (exit {returncode}): {' '.join(argv)}\n{self.stderr}"
        )


def _default_pi_bin() -> str:
    """Resolve the ``pi`` executable.

    Prefers an explicit ``PI_BIN`` override, then the workspace venv's ``pi``,
    then whatever is on PATH.  Never guesses a relative path.
    """
    override = os.environ.get("PI_BIN")
    if override:
        return override
    ws = os.environ.get("PGS_WORKSPACE")
    if ws:
        candidate = os.path.join(ws, ".venv", "bin", "pi")
        if os.path.isfile(candidate):
            return candidate
    found = shutil.which("pi")
    if found:
        return found
    raise PiError(["pi"], 127, "pi executable not found (set PI_BIN or activate the workspace venv)")


@dataclass
class PiClient:
    """Thin, deterministic gateway to the read-only ``pi`` query surface.

    Parameters
    ----------
    workspace:
        Absolute path to ``pgs_workspace`` root.  Defaults to ``PGS_WORKSPACE``.
        ``pi`` requires this and never infers it from cwd.
    pi_bin:
        Path to the ``pi`` executable.  Resolved via :func:`_default_pi_bin`.
    timeout:
        Per-call subprocess timeout (seconds).
    """

    workspace: str = ""
    pi_bin: str = ""
    timeout: float = 60.0

    def __post_init__(self) -> None:
        self.workspace = self.workspace or os.environ.get("PGS_WORKSPACE", "")
        if not self.workspace:
            raise PiError(["pi"], 2, "workspace not set (pass workspace= or set PGS_WORKSPACE)")
        if not os.path.isabs(self.workspace):
            raise PiError(["pi"], 2, f"workspace must be an absolute path, got: {self.workspace}")
        self.pi_bin = self.pi_bin or _default_pi_bin()

    # ---- core invocation -------------------------------------------------

    def _run(self, *args: str) -> dict[str, Any]:
        """Run ``pi <args> --json`` and return the parsed envelope."""
        argv = [self.pi_bin, "--workspace", self.workspace, *args, "--json"]
        env = {**os.environ, "PGS_WORKSPACE": self.workspace}
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            env=env,
            timeout=self.timeout,
        )
        # validate --strict legitimately exits non-zero on a dirty snapshot, but
        # still emits JSON; only treat as error when we cannot parse stdout.
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            raise PiError(argv, proc.returncode, proc.stderr or proc.stdout)
        return payload

    # ---- wrapped queries (one per exposed tool) --------------------------

    def vocab_search(self, term: str) -> dict[str, Any]:
        """Substring search over all indexed FQDNs (case-insensitive)."""
        return self._run("vocab", "search", term)

    def artifact_refs(self, ref: str, transitive: bool = False) -> dict[str, Any]:
        """Who references this artifact (direct consumers, or full closure)."""
        extra = ("--transitive",) if transitive else ()
        return self._run("artifact", "refs", ref, *extra)

    def artifact_source(self, ref: str) -> dict[str, Any]:
        """Authoring Markdown for an FQDN, retrieved from the PPS snapshot.

        Only CC/CS/CT/IN/RB/WF kinds have a PPS source surface. For other kinds (EV, STRUCTURE,
        AC, TI, …) this returns a graceful envelope routing the caller to topology_impact /
        artifact_refs, rather than a hard error the worker would retry."""
        kind = ref.split("::")[-1].split("_", 1)[0]
        if kind not in SOURCEABLE_KINDS:
            return {
                "query": {"command": "artifact source", "ref": ref},
                "schema_version": "v0",
                "result": {
                    "fqdn": ref, "kind": kind, "source_available": False,
                    "note": (f"artifact kind '{kind}' has no source surface — use "
                             f"topology_impact or artifact_refs for {kind} artifacts"),
                },
            }
        return self._run("artifact", "source", ref)

    def topology_impact(self, ref: str) -> dict[str, Any]:
        """Transitive consumer closure, grouped by kind and domain."""
        return self._run("topology", "impact", ref)

    def behavior_logic_show(self, ref: str) -> dict[str, Any]:
        """Execution tree of a workflow, from its materialized graph.json."""
        return self._run("behavior_logic", "show", ref)

    def validate(self, strict: bool = False) -> dict[str, Any]:
        """Snapshot validity + violations in one pass (the authoring gate)."""
        extra = ("--strict",) if strict else ()
        return self._run("validate", *extra)

    # ---- verification oracle (NOT a model tool) --------------------------

    def is_indexed(self, fqdn: str) -> bool:
        """True iff an FQDN resolves in the artifact index.

        Used by the A/B grounding check to tell a real cited artifact from an
        invented one. ``pi vocab resolve`` prints a non-JSON error for an unknown
        FQDN, which surfaces here as a parse failure → not indexed. (A NEW artifact
        the CR proposes is legitimately *not* indexed yet — the harness disambiguates
        that case against the golden dossier, not here.)
        """
        try:
            env = self._run("vocab", "resolve", fqdn)
        except PiError:
            return False
        return bool(env.get("result", {}).get("fqdn"))


# ---- model-facing tool definitions ---------------------------------------
#
# Shape: OpenAI / ollama "tools" array. Each entry's name maps 1:1 to a PiClient
# method via DISPATCH below. Descriptions are written for the model: they state
# what evidence the tool returns and, critically, that it is the *only* source of
# that fact — discouraging the model from answering protocol questions from weights.

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "vocab_search",
            "description": (
                "Search the compiled snapshot's address space for artifact FQDNs whose "
                "code contains TERM (case-insensitive). Use this to discover the exact "
                "FQDN of an artifact before any other query. Never guess an FQDN."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "term": {
                        "type": "string",
                        "description": "Substring to match, e.g. 'REGISTER_ACTOR' or 'WALLET'.",
                    }
                },
                "required": ["term"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "artifact_refs",
            "description": (
                "List the consumers that reference a given artifact FQDN. This is the "
                "authoritative answer to 'who uses X' — do not infer references from "
                "weights. Set transitive=true for the full consumer closure."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ref": {
                        "type": "string",
                        "description": "Full FQDN, e.g. 'blockchain::CC_GENERATE_ACTOR_ID_V0'.",
                    },
                    "transitive": {
                        "type": "boolean",
                        "description": "If true, return the full transitive consumer closure.",
                    },
                },
                "required": ["ref"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "artifact_source",
            "description": (
                "Retrieve the authoring Markdown for an artifact FQDN from the PPS "
                "snapshot. This is the canonical content of the artifact; quote it "
                "rather than reconstructing artifact content from memory. Works ONLY for "
                "CC/CS/CT/IN/RB/WF kinds — for EV/STRUCTURE/AC/TI artifacts use "
                "topology_impact or artifact_refs instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ref": {
                        "type": "string",
                        "description": "Full FQDN of the artifact to fetch source for.",
                    }
                },
                "required": ["ref"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "topology_impact",
            "description": (
                "Compute the transitive consumer closure of an artifact FQDN, grouped "
                "by kind and domain. This is the authoritative change-impact / blast-"
                "radius evidence for a proposed change. Use it before asserting what a "
                "change affects."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ref": {
                        "type": "string",
                        "description": "Full FQDN whose downstream impact you need.",
                    }
                },
                "required": ["ref"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "behavior_logic_show",
            "description": (
                "Show the execution tree (governed DAG traversal) of a workflow FQDN "
                "from its compiled graph.json. This is the authoritative routing/"
                "topology of a workflow — do not describe a workflow's steps from weights."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ref": {
                        "type": "string",
                        "description": "Full WF_ FQDN, e.g. 'blockchain::WF_REGISTER_ACTOR_UNVERIFIED_V0'.",
                    }
                },
                "required": ["ref"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "validate",
            "description": (
                "Run the snapshot validity + violations pass. Returns VALID/INVALID, "
                "conformance counts, snapshot hash, and any violations. Set strict=true "
                "for the hard CI/authoring gate semantics."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "strict": {
                        "type": "boolean",
                        "description": "If true, apply strict gate semantics (fail unless VALID, zero violations).",
                    }
                },
                "required": [],
            },
        },
    },
]


def dispatch(client: PiClient, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Route a model-emitted tool call to the matching PiClient method.

    Returns the ``pi`` JSON envelope. Raises KeyError for an unknown tool name and
    propagates PiError on query failure — the orchestrator is expected to feed
    failures back to the model as grounded tool results, never to silently drop them.
    """
    table: dict[str, Callable[..., dict[str, Any]]] = {
        "vocab_search": client.vocab_search,
        "artifact_refs": client.artifact_refs,
        "artifact_source": client.artifact_source,
        "topology_impact": client.topology_impact,
        "behavior_logic_show": client.behavior_logic_show,
        "validate": client.validate,
    }
    if name not in table:
        raise KeyError(f"unknown tool: {name}")
    return table[name](**(arguments or {}))


TOOL_NAMES = tuple(t["function"]["name"] for t in TOOL_SCHEMAS)

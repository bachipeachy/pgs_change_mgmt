"""Authoring Completeness — the declared registry of human-owned, non-derivable fields.

Boundary 2 (Authority vs Authorship): the compiler derives what is derivable, the human provides
what is not, the worker transforms between them. A field in the registry is information no compiled
artifact can produce (``owner: human, derivable: false``); it must be supplied by a human **before
the first stage that depends on it** (``required_before``) — the point of first use, not system
entry. Seed is the *first* checkpoint, not the *global* one: a ``phase: seed`` field is caught at
the earliest boundary; a stage-emergent obligation is caught at its own stage boundary. The
``required_before`` edges are the embryonic Authoring Obligation Graph over the stage DAG.

Adding a human-owned field is a declaration in ``change_mgmt/authoring_fields.json`` — not code.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HumanOwnedField:
    id: str
    owner: str
    derivable: bool
    phase: str                       # "seed" (pre-execution) | "stage" (emergent)
    type: str                        # "narrative" | "decision" | "enumeration" | "approval"
    required_before: str             # the first stage that depends on it (point of first use)
    why: str
    prompt: str
    source: dict                     # {"kind": "seed", "section": ...} | {"kind": "authoring_inputs"}
    renderer_target: dict | None     # {"stage": ..., "placeholder": ...} — where the value is consumed


def load_registry(path: str | Path) -> dict[str, HumanOwnedField]:
    raw = json.loads(Path(path).read_text())
    out: dict[str, HumanOwnedField] = {}
    for fid, f in raw.get("fields", {}).items():
        out[fid] = HumanOwnedField(
            id=fid, owner=f["owner"], derivable=bool(f.get("derivable", False)),
            phase=f["phase"], type=f["type"], required_before=str(f["required_before"]),
            why=f.get("why", ""), prompt=f.get("prompt", ""),
            source=f.get("source", {}), renderer_target=f.get("renderer_target"))
    return out


def fields_due_before(registry: dict[str, HumanOwnedField], stage: str) -> list[HumanOwnedField]:
    """Human-owned fields whose obligation deadline (``required_before``) OR consumption point
    (``renderer_target.stage``) is ``stage`` — i.e. the fields this stage may not proceed without."""
    stage = str(stage)
    due: list[HumanOwnedField] = []
    for f in registry.values():
        target = str(f.renderer_target["stage"]) if f.renderer_target else None
        if f.required_before == stage or target == stage:
            due.append(f)
    return due


_ITALIC = re.compile(r"^\s*\*.*\*\s*$")               # guidance italics under a template heading
_PLACEHOLDER = re.compile(r"^\s*\[.*\]\s*$")           # an unfilled [...] placeholder (nested [ ] ok)
_HEADING = re.compile(r"^#{1,6}\s")
_HR = re.compile(r"^\s*([-*_])\1{2,}\s*$")             # thematic break — a section boundary


def extract_seed_section(seed_text: str, section: str) -> str:
    """The human prose under the seed heading matching ``section`` (guidance italics — including
    multi-line ``*…*`` blocks — and ``[...]`` placeholders stripped). Empty string ⇒ the section is
    absent or unfilled — i.e. a gap."""
    body: list[str] = []
    capturing = False
    in_italic = False
    for ln in seed_text.splitlines():
        if _HEADING.match(ln):
            if capturing:
                break
            capturing = section.lower() in ln.lower()
            continue
        if not capturing:
            continue
        if _HR.match(ln):                              # next section boundary — stop
            break
        s = ln.strip()
        if in_italic:                                  # inside a multi-line *…* guidance block
            if s.endswith("*"):
                in_italic = False
            continue
        if s.startswith("*") and not _ITALIC.match(ln):  # opens a multi-line italic block
            in_italic = True
            continue
        if _ITALIC.match(ln) or _PLACEHOLDER.match(ln) or not s:
            continue
        body.append(s)
    return " ".join(body).strip()


def supplied_value(field: HumanOwnedField, seed_text: str) -> str:
    """The human-supplied value for ``field`` (empty ⇒ not supplied). Seed-sourced today; the
    ``authoring_inputs`` source (stage-emergent decisions) is wired when a stage first needs one."""
    if field.source.get("kind") == "seed":
        return extract_seed_section(seed_text, field.source.get("section", ""))
    return ""
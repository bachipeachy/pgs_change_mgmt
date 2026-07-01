"""Authoring Completeness gate — the pre-stage check that human-owned inputs are supplied.

Structural only: it verifies *presence*, never judges *content* (content is human authority — the
Knowledge-Partition guardrail). Symmetric with ingress admissibility:
``AUTHORING_INCOMPLETE : stage  ::  NACK : ingress``. A field due before a stage that is not
supplied halts the stage BEFORE it exports; the report names exactly what is missing, its phase and
type, and why — and offers *where* to supply it, never a decision.
"""

from __future__ import annotations

from dataclasses import dataclass, field as _dcfield
from pathlib import Path

from ..contracts.authoring_completeness import (
    HumanOwnedField, fields_due_before, load_registry, supplied_value)


def _registry_path(cfg) -> Path:
    return cfg.templates_dir.parent / "authoring_fields.json"


def _where(f: HumanOwnedField) -> str:
    src = f.source
    if src.get("kind") == "seed":
        return f"the seed's '## {src.get('section')}' section"
    if src.get("kind") == "authoring_inputs":
        return f"_authoring/human_inputs.json → {f.id}"
    return "(unspecified source)"


@dataclass
class AuthoringReadiness:
    stage: str
    gaps: list[HumanOwnedField] = _dcfield(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.gaps

    def render(self) -> str:
        if self.ok:
            return f"authoring completeness (stage {self.stage}): ✓ human-owned inputs supplied"
        out = [f"⛔ AUTHORING_INCOMPLETE — human decision required (stage {self.stage})",
               f"   {len(self.gaps)} human-owned field(s) not supplied; the stage was NOT run.",
               "   Not a validation/compiler/worker failure — the protocol simply cannot continue "
               "until the human supplies what only the human owns.\n"]
        for g in self.gaps:
            out += [f"   • {g.id}   [phase={g.phase} · type={g.type} · owner={g.owner}]",
                    f"       required before : stage {g.required_before}",
                    f"       why            : {g.why}",
                    f"       supply in      : {_where(g)}",
                    f"       prompt         : {g.prompt}\n"]
        return "\n".join(out)


def check_authoring_completeness(cfg, stage: str) -> AuthoringReadiness:
    """Return the readiness of human-owned inputs due before ``stage`` (``.ok`` ⇒ proceed)."""
    reg = load_registry(_registry_path(cfg))
    seed_text = cfg.seed_path.read_text()
    r = AuthoringReadiness(stage=str(stage))
    for f in fields_due_before(reg, stage):
        if not supplied_value(f, seed_text):
            r.gaps.append(f)
    return r


def fill_authoring_targets(doc: str, cfg, stage: str) -> str:
    """Substitute each human-owned field's ``renderer_target`` placeholder (for this stage) with the
    human-supplied value. The value flows from its declared source — it is never invented here."""
    reg = load_registry(_registry_path(cfg))
    seed_text = cfg.seed_path.read_text()
    for f in reg.values():
        if not f.renderer_target or str(f.renderer_target["stage"]) != str(stage):
            continue
        val = supplied_value(f, seed_text)
        if val:
            ph = f.renderer_target["placeholder"].format(domain=cfg.domain, subdomain=cfg.subdomain)
            doc = doc.replace(ph, val)
    return doc

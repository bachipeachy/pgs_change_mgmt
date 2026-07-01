"""PromptIR — the structured, hashable prompt object behind a Stage Package (Trifecta P1).

A worker prompt is not free-text the Validator cannot reason about: it is a governed contract.
`PromptIR` makes it **structured, diffable, and hashable** so the same prompt produces the same
`prompt_hash` forever, and so CSI can later extend upward into the authoring layer.

Three concerns, exactly as the plan declares them:

    system       the governed mandate, structured (the authoring mandate + governance_version +
                 allowed grounding tools + the register contract the response must satisfy)
    user         objective + governance rules + the bounded upstream handoff pointer
    constraints  the grounding_spec (required_tokens, query_rule, validation_mode)

`prompt_bundle.json` (§4) is this object's serialization; `system_prompt.md` / `user_prompt.md`
are *rendered views* of it for pasting into a chat UI, hash-linked back to the bundle. Tempering
note (plan §4a): this stays a dataclass + serialization — no diff tooling / CSI-over-prompts yet.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


def sha256_of(obj: Any) -> str:
    """Canonical, stable `sha256:…` digest of a json-serializable object.

    Canonicalization is `sort_keys` + compact separators, so the digest is invariant to key order
    and whitespace — the property the export selftest pins (two builds ⇒ identical hash)."""
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PromptIR:
    """The structured prompt a `StagePackageBuilder` produces and a Stage Package serializes."""

    system: dict      # {"mandate", "governance_version", "allowed_tools", "register_contract"}
    user: dict        # {"stage", "objective", "governance_rules", "handoff"}
    constraints: dict  # the grounding_spec: {"required_tokens", "query_rule", "validation_mode"}

    # ---- rendered views (the .md the human pastes) ----------------------------------------

    def render_system(self) -> str:
        """The system prompt: the governed mandate + the typed grounding constraint, rendered.

        The mandate already forbids ungrounded protocol facts; the grounding constraint makes the
        stage's frontier explicit (the code-tokens to confirm via `pi`, and the query rule that
        fixes the Case-C phrase-query failure by declaration)."""
        parts = [str(self.system.get("mandate", "")).strip(), "", _render_grounding(self.constraints)]
        return "\n".join(parts).strip() + "\n"

    def render_user(self) -> str:
        """The user prompt: the bounded stage task (objective + rules + handoff).

        Mirrors the automated worker's `render_task` framing so a Guided response is judged on the
        identical task an automated worker would have received — only the transport differs."""
        u = self.user
        rules = "\n".join(f"- {r}" for r in u.get("governance_rules", ())) or "- (none)"
        bounded = json.dumps(u.get("handoff", {}), indent=2, default=str)
        return (
            f"# STAGE {u.get('stage', '?')}\n\n"
            f"## Objective\n{u.get('objective', '')}\n\n"
            f"## Governance rules in force\n{rules}\n\n"
            f"## Upstream handoff you may read (bounded context)\n```json\n{bounded}\n```\n"
        )

    # ---- serialization (the canonical contract) -------------------------------------------

    def prompt_hash(self) -> str:
        """Stable digest over the rendered prompt content (system + user).

        Keyed on the rendered views, not the structured dicts, so the hash tracks exactly what the
        worker is asked to execute. The register contract carries its own `schema_hash`."""
        return sha256_of({"system_prompt": self.render_system(), "user_prompt": self.render_user()})

    def to_bundle(self) -> dict:
        """Serialize to the canonical `prompt_bundle.json` shape (plan §4)."""
        return {
            "system_prompt": self.render_system(),
            "user_prompt": self.render_user(),
            "prompt_hash": self.prompt_hash(),
            "governance_version": self.system.get("governance_version"),
            "allowed_tools": list(self.system.get("allowed_tools", ())),
            "register_contract": self.system.get("register_contract", {}),
        }


def _render_grounding(spec: dict) -> str:
    """Render the grounding_spec as an explicit constraint block in the system prompt."""
    if not spec:
        return ""
    tokens = ", ".join(spec.get("required_tokens", ())) or "(none derived)"
    rule = spec.get("query_rule", "")
    mode = spec.get("validation_mode", "strict")
    return (
        "## Grounding constraint (typed)\n"
        f"Query rule: {rule}\n"
        f"Validation mode: {mode}\n"
        f"Grounding frontier — confirm each of these protocol code-tokens via `pi` before you use "
        f"it (this is a frontier to verify, NEVER an answer key; a 0-result is a final answer):\n"
        f"  {tokens}"
    )

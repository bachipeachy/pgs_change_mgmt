"""Shared renderer scaffolding — the parts every artifact-kind renderer reuses.

Each kind's machine block is different, but the *envelope* is uniform: a Header block, prose
sections, and a fenced ```yaml machine block the compiler ingests. These helpers own that
envelope so a per-kind renderer only declares its sections + machine `core`. Grounded in the
real authoring sources (IN/WF/RB/CC) the compiler already accepts.
"""

from __future__ import annotations

from typing import Any

import yaml

GOVERNED_BY_PREFIX = "fb.topology::"

# kind → (artifact_kind label, constitution code). Mirrors the real authoring headers.
KIND_META: dict[str, tuple[str, str]] = {
    "CC": ("capability_contract", "CONSTITUTION_CAPABILITY_CONTRACT_V0"),
    "IN": ("intent", "CONSTITUTION_INTENT_V0"),
    "WF": ("workflow", "CONSTITUTION_WORKFLOW_V0"),
    "RB": ("runtime_binding", "CONSTITUTION_RUNTIME_BINDING_V0"),
}


class ContractError(ValueError):
    """The contract object is structurally invalid (a reasoning/shape error, not syntax)."""


def constitution(kind: str) -> str:
    """Bare constitution code for a kind's `Governed By` header."""
    return KIND_META[kind][1]


def governed_by(kind: str) -> str:
    """Fully-qualified `governed_by` for the machine block."""
    return GOVERNED_BY_PREFIX + KIND_META[kind][1]


def machine_block(doc: dict[str, Any]) -> str:
    """Serialize a machine document to a valid YAML string.

    `safe_dump` guarantees correct quoting of colons, '{{timestamp}}', and other
    YAML-special scalars — eliminating the unquoted-scalar parse errors by construction.
    """
    return yaml.safe_dump(doc, sort_keys=False, default_flow_style=False, width=100)


def header(code: str, kind: str, *, deps: list[str] | None = None,
           status: str = "draft", supersedes: str = "NONE",
           include_deps: bool = True) -> list[str]:
    """The mandatory Header block lines shared by every artifact kind."""
    label, const = KIND_META[kind]
    lines = [
        f"# {code}", "",
        "## Header (Mandatory)", "",
        f"- **Artifact Code:** {code}",
        f"- **Artifact Kind:** {label}",
        f"- **Governed By:** {const}",
        "- **Version:** v0",
        f"- **Status:** {status}",
        f"- **Supersedes:** {supersedes}",
    ]
    if include_deps:
        lines.append(f"- **Dependencies:** {', '.join(deps) if deps else 'NONE'}")
    return lines


def section(title: str, body: str) -> list[str]:
    """A `## N. Title` prose section with a trailing rule."""
    return ["", "---", "", f"## {title}", "", body]


def machine_section(machine_yaml: str) -> list[str]:
    return ["", "---", "", "## Machine", "", "```yaml", machine_yaml.rstrip(), "```", ""]


def assemble(parts: list[str]) -> str:
    return "\n".join(parts)

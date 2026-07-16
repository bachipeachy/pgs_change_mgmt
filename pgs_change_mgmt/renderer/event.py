"""EVRenderer — structured contract object → admissible event (EV) Markdown.

Grounded in the real authoring schema (e.g. EV_BLOCK_COMMITTED_V0): an EV declares a recorded fact —
a summary, a description, and the typed payload `schema` the event carries.

This is a **semantic renderer** (per the Construction renderer taxonomy: template / projection / semantic).
Unlike a template renderer, it cannot manufacture its inputs. An event's payload schema and its emitter
are protocol-design decisions carried upstream — S6b `events` (the protocol viewpoint: payload) and
S6b `execution_outputs` (the execution relationship: which node emits it). If either is absent, the
renderer **fails** — it never infers a payload or guesses an emitter. Constructing an EV whose semantics
are undeclared is a gap, not a rendering. (The construction model surfaces that as a gap before calling
this renderer; the guards here enforce the same invariant if the renderer is invoked directly.)

The machine block matches the compiled EV shape exactly (`core.summary/description/schema`, schema fields
carrying `type`/`required`/`format`). The per-field `description` and the `emitted_by` relationship are
projected into prose sections — richer human artifact, still zero invention (both come from the registers).
"""

from __future__ import annotations

from typing import Any

from .base import ContractError, governed_by, header, machine_block, machine_section, section, assemble


def _required(v: Any) -> bool:
    return str(v).strip().lower() == "true"


def _schema(payload: list[dict]) -> dict[str, Any]:
    schema: dict[str, Any] = {}
    for f in payload:
        name = f.get("field")
        if not name:
            raise ContractError("EV payload row missing 'field'")
        spec: dict[str, Any] = {"type": f.get("type") or "string", "required": _required(f.get("required"))}
        if f.get("format"):
            spec["format"] = f["format"]
        schema[name] = spec
    return schema


def _validate(obj: dict[str, Any]) -> None:
    if not obj.get("summary"):
        raise ContractError("EV contract missing required field: summary")
    # Semantic-renderer invariant: fail, never infer.
    if not obj.get("payload"):
        raise ContractError(f"EV {obj.get('code')!r}: no payload schema (S6b.events) — "
                            "a semantic renderer does not infer payloads")
    if not obj.get("emitted_by"):
        raise ContractError(f"EV {obj.get('code')!r}: no emitter (S6b.execution_outputs) — "
                            "a semantic renderer does not guess emitters")


def _machine(code: str, obj: dict[str, Any]) -> str:
    core = {
        "summary": obj["summary"],
        "description": obj.get("description") or obj["summary"],
        "schema": _schema(obj["payload"]),
    }
    doc = {"ev_code": code, "version": "v0", "governed_by": governed_by("EV"), "core": core}
    return machine_block(doc)


class EVRenderer:
    """`contracts.Renderer` for events (kind="EV") — a semantic renderer over payload + emitter."""

    kind = "EV"

    def render(self, contract: dict[str, Any]) -> str:
        obj = dict(contract)
        code = obj.pop("code", None) or obj.pop("ev_code", None)
        if not code:
            raise ContractError("EV contract is missing 'code'")
        obj["code"] = code  # retained for the semantic-gap error messages
        _validate(obj)
        parts = header(code, "EV", status="draft")
        parts += section("1. Fact", obj["summary"])
        # §2 Emitted By — the execution relationship (S6b.execution_outputs), projected, not invented.
        parts += section("2. Emitted By", "\n".join(f"- `{e}`" for e in obj["emitted_by"]))
        # §3 Schema — the payload (S6b.events), incl. per-field description (prose only; machine block
        # keeps the compiled shape). Projected verbatim from the register.
        rows = ["| Field | Type | Required | Format | Description |",
                "|-------|------|----------|--------|-------------|"]
        for f in obj["payload"]:
            rows.append(f"| {f.get('field', '')} | {f.get('type', '')} | {f.get('required', '')} "
                        f"| {f.get('format', '')} | {f.get('description', '')} |")
        parts += section("3. Schema", "\n".join(rows))
        parts += machine_section(_machine(code, obj))
        return assemble(parts)

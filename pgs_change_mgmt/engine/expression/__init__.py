"""Shared binding-expression grammar — one grammar, many consumers.

The lesson from CT/CS invocation binding was "one grammar, multiple consumers." This module is that
grammar: a small, extensible expression model reused by every consumer that binds one thing to another —
CT invocation binding, CS invocation binding, and (pipeline 3) acceptance-scenario payloads + observation
addresses. Do NOT fork a second grammar per consumer.

Two concerns are cleanly separated:

  * **the grammar** (here) — an `Expression` is a `Literal` or a `Reference` today; a future compile-time
    form (`Concat`, `Hash`, `Default`) adds one class + one `evaluate` branch, never a redesign.
  * **evaluation context** (the consumer) — a `Reference` means different things per consumer: the
    invocation binding resolves it to a compile-time JSONPath along the construction dataflow; the
    acceptance engine resolves it to a runtime value from a prior step's surface/store. So each consumer
    passes its own `resolve_reference` callable to `evaluate`; the module never assumes a context.

Surface parsers (both produce the same model):
  * `parse_compact` — the CR-IR cell form used by invocation bindings: a bare name is a reference, a
    double-quoted token is a literal (`block`, `key="head"`).
  * `parse_structured` — the YAML form used by acceptance scenarios: `{literal: v}` / `{ref: "$.…"}`,
    with a bare scalar treated as a literal and a `$.`-prefixed string as a reference.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Union


@dataclass(frozen=True)
class Literal:
    """A constant expression — its value is used verbatim."""
    value: Any


@dataclass(frozen=True)
class Reference:
    """A reference expression — `path` names something the consumer resolves in its own context (a
    CC-local field for invocation binding; a `$.steps.<id>.surface|store.<…>` address for acceptance)."""
    path: str


Expression = Union[Literal, Reference]


def parse_compact(source: Any) -> Expression:
    """Parse the compact CR-IR cell form: a double-quoted token → `Literal`; anything else → `Reference`."""
    s = str(source).strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return Literal(s[1:-1])
    return Reference(s)


def parse_structured(obj: Any) -> Expression:
    """Parse the structured YAML form: `{literal: v}` / `{ref: "$.…"}`; a bare `$.`-string → `Reference`;
    any other bare scalar → `Literal`."""
    if isinstance(obj, dict):
        if "literal" in obj:
            return Literal(obj["literal"])
        if "ref" in obj:
            return Reference(str(obj["ref"]))
        raise ValueError(f"expression object must have 'literal' or 'ref': {obj!r}")
    if isinstance(obj, str) and obj.startswith("$."):
        return Reference(obj)
    return Literal(obj)


def evaluate(expr: Expression, resolve_reference: Callable[[str], Any]) -> Any:
    """Evaluate an expression. `Literal` → its value; `Reference` → `resolve_reference(path)`. The
    consumer owns reference resolution; new expression kinds extend this dispatch one branch each."""
    if isinstance(expr, Literal):
        return expr.value
    if isinstance(expr, Reference):
        return resolve_reference(expr.path)
    raise TypeError(f"unknown expression: {expr!r}")


__all__ = ["Literal", "Reference", "Expression", "parse_compact", "parse_structured", "evaluate"]


if __name__ == "__main__":
    assert parse_compact("proposed_block") == Reference("proposed_block")
    assert parse_compact('"head"') == Literal("head")
    assert parse_structured({"literal": 0}) == Literal(0)
    assert parse_structured({"ref": "$.steps.s1.store.chain_head.head"}) == Reference("$.steps.s1.store.chain_head.head")
    assert parse_structured("$.a.b") == Reference("$.a.b")
    assert parse_structured(5) == Literal(5)
    assert evaluate(Literal("x"), lambda p: "NO") == "x"
    assert evaluate(Reference("k"), lambda p: {"k": 9}[p]) == 9
    print("expression grammar self-test OK — literal/reference, compact+structured parse, context-free evaluate")

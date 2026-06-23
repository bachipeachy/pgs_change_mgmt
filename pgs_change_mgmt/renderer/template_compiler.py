"""Template Compiler — derive a stage's register schema FROM its template.

The template is the single governing artifact. Rather than hand-code each stage's registers
(id / columns / required / business_language) — four artifacts that can drift — the schema is
*compiled* from the template's register markers and table headers:

    <!-- register:actors business_language -->
    | Actor | Role | Authority Class | Source Finding |
        ↓  compile_template()
    Register(register_id="actors",
             columns=(("actor","Actor"),("role","Role"),("authority_class","Authority Class"),
                      ("source_finding","Source Finding")),
             required=True, business_language=True, traceability_key="source_finding")

Marker grammar:  `<!-- register:<id> [optional] [business_language[=col1,col2]] -->`
  * `optional`                → required=False (default is required)
  * `business_language`       → no protocol artifact names allowed in any content column
  * `business_language=a,b`   → column-scoped: only columns a,b are business-language-checked
Column keys are normalized from the table header (`Authority Class` → `authority_class`,
`#` → `num`). A header may declare a controlled vocabulary inline — `Decision (REUSE, EXTEND,
AUTHOR_NEW)` — and the compiler extracts the allowed values into the register's `enums`.
`traceability_key` is inferred: "source_finding" if that column is present.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

MARKER = re.compile(r"<!--\s*register:([a-z0-9_]+)([^>]*?)-->")


from dataclasses import field

# A column header may declare a controlled vocabulary inline: "Decision (REUSE, EXTEND, AUTHOR_NEW)".
# The allowed values live in the template (the governed artifact); the compiler extracts them.
# Comma-separated UPPERCASE tokens — `|` can't be used (it is the Markdown table column separator),
# and requiring uppercase tokens avoids misreading a descriptive lowercase parenthetical as an enum.
ENUM_HEADER_RE = re.compile(
    r"^(?P<name>.*?)\s*\((?P<vals>[A-Z][A-Z0-9_]*(?:\s*,\s*[A-Z][A-Z0-9_]*)+)\)\s*$"
)


@dataclass(frozen=True)
class Register:
    """One register table in a stage document: id, columns, governance flags."""

    register_id: str
    columns: tuple[tuple[str, str], ...]   # (data_key, display_header)
    required: bool = True
    business_language: bool = False
    traceability_key: str | None = "source_finding"
    enums: dict[str, tuple[str, ...]] = field(default_factory=dict)   # column key → allowed values
    # business-language scope: None ⇒ all content columns; a tuple ⇒ only those columns are
    # business-language-checked (column-scoped, per the S3 column-type distinction).
    bl_columns: tuple[str, ...] | None = None

    @property
    def keys(self) -> tuple[str, ...]:
        return tuple(k for k, _ in self.columns)

    @property
    def headers(self) -> tuple[str, ...]:
        return tuple(h for _, h in self.columns)


def header_to_key(header: str) -> str:
    """Deterministic header → data-key normalization (the worker emits these keys)."""
    h = header.strip()
    m = ENUM_HEADER_RE.match(h)   # strip an inline enum "(A | B | C)" before keying
    if m:
        h = m.group("name").strip()
    if h == "#":
        return "num"
    return re.sub(r"[^a-z0-9]+", "_", h.lower()).strip("_")


def _column_enum(header: str) -> tuple[str, ...] | None:
    """Allowed values if the header declares an inline vocabulary, else None."""
    m = ENUM_HEADER_RE.match(header.strip())
    return tuple(v.strip() for v in m.group("vals").split(",")) if m else None


def has_registers(template: str) -> bool:
    """A stage is *structured* iff its template declares register markers."""
    return bool(MARKER.search(template))


def compile_template(template: str) -> tuple[Register, ...]:
    """Compile a stage template into its register schema (empty if free-form)."""
    lines = template.splitlines()
    regs: list[Register] = []
    i = 0
    while i < len(lines):
        m = MARKER.search(lines[i])
        if not m:
            i += 1
            continue
        rid = m.group(1)
        flags = m.group(2).split()
        # business-language flag: bare `business_language` ⇒ all content columns; the form
        # `business_language=col1,col2` ⇒ only those columns are business-language-checked.
        bl = any(f == "business_language" or f.startswith("business_language=") for f in flags)
        bl_columns: tuple[str, ...] | None = None
        for f in flags:
            if f.startswith("business_language="):
                bl_columns = tuple(c.strip() for c in f.split("=", 1)[1].split(",") if c.strip())
        # the first table after the marker defines the columns
        j = i + 1
        while j < len(lines) and not lines[j].lstrip().startswith("|"):
            j += 1
        if j < len(lines):
            headers = [c.strip() for c in lines[j].strip().strip("|").split("|") if c.strip()]
            cols = tuple((header_to_key(h), h) for h in headers)
            keys = {k for k, _ in cols}
            enums = {header_to_key(h): _column_enum(h) for h in headers if _column_enum(h)}
            regs.append(Register(
                register_id=rid,
                columns=cols,
                required="optional" not in flags,
                business_language=bl,
                traceability_key="source_finding" if "source_finding" in keys else None,
                enums=enums,
                bl_columns=bl_columns,
            ))
            i = j
        else:
            i += 1
    return tuple(regs)


def to_jsonable(regs: tuple[Register, ...]) -> list[dict]:
    """Inspection form (template_schema.json)."""
    return [
        {"register_id": r.register_id, "columns": list(r.keys), "required": r.required,
         "business_language": r.business_language, "traceability_key": r.traceability_key,
         "enums": {k: list(v) for k, v in r.enums.items()},
         "bl_columns": list(r.bl_columns) if r.bl_columns is not None else None}
        for r in regs
    ]


if __name__ == "__main__":   # dump a template's compiled schema for inspection
    import json
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else None
    if not path:
        print("usage: python -m pgs_change_mgmt.renderer.template_compiler <template.md>")
        sys.exit(2)
    schema = to_jsonable(compile_template(open(path).read()))
    print(json.dumps(schema, indent=2))

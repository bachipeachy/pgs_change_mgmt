"""DossierStageRenderer + structural oracle — structured register intent → stage document.

The dossier-tier realization of the system's core pattern: the worker authors *structured
intent* (register rows), and a deterministic renderer owns the Markdown. Same shape as the
artifact tier (`contract object → CCRenderer → protocol artifact`), one layer up
(`register rows → DossierStageRenderer → Stage-N document`).

The register schema is NOT hand-coded — it is **compiled from the template** (`template_compiler`),
so the template is the single governing artifact (no template/schema/renderer/prompt drift).

Two responsibilities:
  * RENDER — fill the template's register tables (located by `<!-- register:id -->`) from the
    worker's row data; an empty *required* register renders as `| NONE IDENTIFIED |`. The
    template stays the single source of structure.
  * ORACLE — `check()` mechanically decides completeness/admissibility BEFORE a human reviews:
    every required register populated, every row carries a Source Finding (traceability),
    business-language registers carry no protocol artifact names in *content* columns (the
    source_finding column legitimately cites the grounded artifact by FQDN — that is evidence).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .template_compiler import Register, compile_template, has_registers

# Catches qualified (domain::CC_X_V0) and bare (CC_X_V0) artifact names — the leakage the
# business-language *content* columns must not contain.
ARTIFACT_NAME_RE = re.compile(
    r"\b(?:[a-z_][a-z0-9_]*::)?(?:CC|CS|CT|IN|WF|RB|EV|AC|STRUCTURE|TI)_[A-Z0-9_]*_V\d+\b"
)

# Column-type distinction (per the S4 review): EVIDENCE / SOURCE / REFERENCE columns legitimately
# cite a grounded artifact by FQDN — that IS the evidence — and are exempt from the
# business-language check. CONTENT / DESCRIPTION columns are not. A column is an evidence column
# iff its data-key is one of these (the template author names the column accordingly).
EVIDENCE_COLUMNS = frozenset({"source_finding", "evidence", "fqdn", "reference",
                              "alternatives_checked"})

# CODE columns hold a binding/assigned FQDN and must be well-formed (`domain::PREFIX_NAME_V<n>`).
# This is the generic half of the S6b binding-FQDN discipline — any structured stage with a code
# column gets format-validation for free. Cross-register checks (collision / referenced⇒declared /
# near-duplicate) are stage-specific and live in evaluator.design_intent_oracle.
# Scoped to NEW-code columns only (not `fqdn`, which holds existing-artifact evidence in the
# locked S2 template — left untouched to preserve the baseline).
FQDN_COLUMNS = frozenset({"code", "rb_code", "binds_wf", "storage_structure"})
FQDN_RE = re.compile(r"^[a-z][a-z0-9_.]*::(?:CC|CS|CT|IN|WF|RB|EV|AC|STRUCTURE|TI)_[A-Z0-9_]*_V\d+$")


@dataclass
class OracleResult:
    ok: bool
    issues: list[str] = field(default_factory=list)
    populated: list[str] = field(default_factory=list)
    empty_required: list[str] = field(default_factory=list)
    dirty: set[str] = field(default_factory=set)   # register_ids with ≥1 issue (for split coverage)


class DossierStageRenderer:
    """Render structured register intent into a stage document; mechanically check completeness.

    Construct with the stage **template text** — the register schema is compiled from it.
    """

    def __init__(self, template: str) -> None:
        self.template = template
        self.registers: dict[str, Register] = {r.register_id: r for r in compile_template(template)}
        if not self.registers:
            raise ValueError("template declares no register markers — not a structured stage")

    # ---- structural oracle ----------------------------------------------

    def check(self, data: dict[str, list[dict[str, Any]]]) -> OracleResult:
        res = OracleResult(ok=True)

        def flag(rid: str, msg: str) -> None:
            res.issues.append(msg)
            res.dirty.add(rid)

        for rid in data:
            if rid not in self.registers:
                flag(rid, f"unknown register id: {rid!r}")
        for reg in self.registers.values():
            rows = data.get(reg.register_id) or []
            if rows:
                res.populated.append(reg.register_id)
            elif reg.required:
                res.empty_required.append(reg.register_id)
                flag(reg.register_id, f"required register '{reg.register_id}' is empty")
            ev_cols = [k for k in reg.keys if k in EVIDENCE_COLUMNS]
            for i, row in enumerate(rows):
                # traceability: a register with any evidence/source column must cite at least
                # one of them per row (source_finding OR evidence OR fqdn) — not one specific
                # column. Avoids redundant-column false flags when a register has e.g. both
                # `evidence` and `source_finding`.
                if ev_cols and not any(str(row.get(k, "")).strip() for k in ev_cols):
                    flag(reg.register_id, f"{reg.register_id}[{i}]: no traceability (fill one of {ev_cols})")
                # controlled-vocabulary enforcement: an enum column (declared in the template
                # header as "Name (A | B | C)") may only contain a declared value. This is the
                # contract the malformed free-text `decision` violated.
                for k, allowed in reg.enums.items():
                    v = str(row.get(k, "")).strip()
                    if v and v not in allowed:
                        flag(reg.register_id,
                             f"{reg.register_id}[{i}].{k}: '{v}' is not in the controlled "
                             f"vocabulary {list(allowed)}")
                # FQDN well-formedness: a code column must hold a `domain::PREFIX_NAME_V<n>` FQDN.
                for k in reg.keys:
                    if k in FQDN_COLUMNS:
                        v = str(row.get(k, "")).strip()
                        if v and not FQDN_RE.match(v):
                            flag(reg.register_id,
                                 f"{reg.register_id}[{i}].{k}: '{v}' is not a well-formed FQDN "
                                 f"(domain::PREFIX_NAME_V<n>)")
                if reg.business_language:
                    for k, v in row.items():
                        # business-language scope is column-scoped: if the template declared
                        # `business_language=cols`, only those columns are checked; otherwise all
                        # content columns are. Evidence/source/reference columns and enum columns
                        # legitimately carry FQDNs / controlled tokens (S4 column-type distinction).
                        if reg.bl_columns is not None and k not in reg.bl_columns:
                            continue
                        if k in EVIDENCE_COLUMNS or k == reg.traceability_key or k in reg.enums:
                            continue
                        m = ARTIFACT_NAME_RE.search(str(v))
                        if m:
                            flag(reg.register_id,
                                 f"{reg.register_id}[{i}].{k}: protocol artifact name "
                                 f"'{m.group(0)}' in a business-language register")
        res.ok = not res.issues
        return res

    # ---- render (template injection) ------------------------------------

    def render(self, data: dict[str, list[dict[str, Any]]]) -> str:
        lines = self.template.splitlines()
        out: list[str] = []
        i = 0
        marker = re.compile(r"<!--\s*register:([a-z0-9_]+)")
        while i < len(lines):
            m = marker.search(lines[i])
            if not m:
                out.append(lines[i]); i += 1
                continue
            rid = m.group(1)
            out.append(lines[i]); i += 1
            while i < len(lines) and not lines[i].lstrip().startswith("|"):
                out.append(lines[i]); i += 1
            if i < len(lines) and lines[i].lstrip().startswith("|"):            # header
                out.append(lines[i]); i += 1
            if i < len(lines) and re.match(r"\s*\|[\s:|-]+\|", lines[i]):        # separator
                out.append(lines[i]); i += 1
            while i < len(lines) and lines[i].lstrip().startswith("|"):          # drop placeholders
                i += 1
            out.extend(self._rows(rid, data.get(rid) or []))
        return "\n".join(out) + "\n"

    def _rows(self, rid: str, rows: list[dict[str, Any]]) -> list[str]:
        reg = self.registers.get(rid)
        if reg is None:
            return []
        if not rows:
            return ["| " + " | ".join(["NONE IDENTIFIED"] + [""] * (len(reg.columns) - 1)) + " |"]
        rendered = []
        for row in rows:
            cells = [str(row.get(k, "")).replace("|", "\\|").replace("\n", " ") for k in reg.keys]
            rendered.append("| " + " | ".join(cells) + " |")
        return rendered


def is_structured_template(template: str) -> bool:
    return has_registers(template)

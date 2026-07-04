"""InteractiveIngressValidator — the typed gate at the human mutation boundary (Trifecta P2).

In Guided Authoring Mode the human is a *mutation layer between stages*: they run the exported
Stage Package through a chat LLM and paste the response back. Left untyped, that paste is the one
place the pipeline could bypass the compiler / CSI / structural oracle. This validator runs BEFORE
the engine ever sees a guided response — it parses the pasted `response.md`, checks it against the
package's register schema (`schema_hash` / declared fields) and its grounding constraint
(`grounding_spec.validation_mode`), and rejects a malformed handoff at the boundary.

It is an *additional, fail-fast, transport-specific* gate — NOT a replacement for the engine's
downstream structural oracle, which still runs on import. Where the oracle judges completeness and
business-language across the whole document, the ingress validator catches the boundary failures:
the human pasted the wrong thing, an undeclared register, a row with garbage columns, an FQDN
smuggled into a content column, or an ungrounded assertion with no traceability.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from ._authoring import parse_output

# A protocol artifact identifier: a domain-qualified FQDN (`domain::CODE_Vn`) or a bare versioned
# artifact code (`WF_…_V0`). Used to flag an FQDN smuggled into a business-language content column.
_FQDN_RE = re.compile(r"\b([a-z_]+::[A-Z][A-Z0-9_]*|[A-Z]{2,}_[A-Z0-9_]+_V\d+)\b")
_EVIDENCE_COLUMNS = frozenset({"source_finding", "evidence", "fqdn", "reference", "evidence_status"})

# Diagnostic registers a worker MAY emit on ANY stage that are NOT stage content — permitted past the
# undeclared-register check. `human_engagement` is the DRC Part-B register: the engine consumes it for
# the design review and strips it from the handoff (kept in sync with engine.dossier.DRC_REGISTER).
_DIAGNOSTIC_REGISTERS = frozenset({"human_engagement"})


@dataclass(frozen=True)
class IngressVerdict:
    """The boundary verdict — admissible iff `ok`. `issues` names every defect (fail-fast list)."""

    ok: bool
    issues: tuple[str, ...]
    schema_hash: str
    fields_present: tuple[str, ...]

    def render(self) -> str:
        head = "ADMISSIBLE" if self.ok else "REJECTED"
        body = "\n".join(f"  - {i}" for i in self.issues) or "  (no issues)"
        return f"ingress: {head} (schema {self.schema_hash[:18]}…)\n{body}"


class InteractiveIngressValidator:
    """Validate a pasted guided response against its exported Stage Package, before import."""

    def __init__(self, package_dir: str | Path) -> None:
        self.package_dir = Path(package_dir)
        self.schema = json.loads((self.package_dir / "schema.json").read_text())
        self.grounding_spec = json.loads(
            (self.package_dir / "context" / "grounding_spec.json").read_text())

    # ---- entry points ---------------------------------------------------------------------

    def validate_response_file(self) -> tuple[IngressVerdict, dict[str, Any]]:
        """Parse `response.md` (interactive mode) and validate the registers it carries."""
        resp = self.package_dir / "response.md"
        if not resp.exists():
            verdict = IngressVerdict(False, (f"no response.md in {self.package_dir} — paste the "
                                             "model's reply there before importing",),
                                     self.schema.get("schema_hash", ""), ())
            return verdict, {}
        registers, _questions, _findings = parse_output("interactive", resp.read_text())
        return self.validate(registers), registers

    def validate(self, registers: Mapping[str, Any]) -> IngressVerdict:
        """Validate parsed registers against the package schema + grounding constraint."""
        issues: list[str] = []
        strict = self.grounding_spec.get("validation_mode", "strict") == "strict"

        if not isinstance(registers, dict) or not registers:
            issues.append("response carried no parseable ```json registers object")
            return IngressVerdict(False, tuple(issues), self.schema.get("schema_hash", ""), ())

        declared = set(self.schema.get("registers", {})) if self.schema.get("structured") \
            else {f["field"] for f in self.schema.get("emit_fields", ())}
        present = tuple(sorted(registers))

        # (1) undeclared keys — the human pasted something not in this stage's contract. Diagnostic
        #     registers (the DRC Part-B `human_engagement`) are permitted on ANY stage: they are not
        #     stage content — the engine consumes them for the design review and filters them out of the
        #     handoff (engine.dossier.DRC_REGISTER) — so they are legitimately absent from every schema.
        for key in registers:
            if key not in declared and key not in _DIAGNOSTIC_REGISTERS:
                issues.append(f"register '{key}' is not declared by this stage's schema "
                              f"(declared: {sorted(declared)})")

        # (2) per-register structural conformance (structured stages only — the engine's renderer
        #     consumes register rows; free-form stages carry scalar handoff fields the oracle judges)
        if self.schema.get("structured"):
            specs = self.schema["registers"]
            for rid, spec in specs.items():
                if rid not in registers:
                    continue                              # completeness is the engine oracle's job
                issues += self._check_register(rid, spec, registers[rid], strict)

        ok = not issues
        return IngressVerdict(ok, tuple(issues), self.schema.get("schema_hash", ""), present)

    # ---- per-register checks --------------------------------------------------------------

    def _check_register(self, rid: str, spec: dict, value: Any, strict: bool) -> list[str]:
        issues: list[str] = []
        if not isinstance(value, list):
            return [f"register '{rid}' must be a list of rows, got {type(value).__name__}"]
        columns = set(spec.get("columns", ()))
        evidence_cols = set(spec.get("evidence_columns", ())) or (columns & _EVIDENCE_COLUMNS)
        enums = spec.get("enums", {})
        business = spec.get("business_language", False)
        content_cols = columns - _EVIDENCE_COLUMNS

        for i, row in enumerate(value):
            if not isinstance(row, dict):
                issues.append(f"{rid}[{i}] must be an object, got {type(row).__name__}")
                continue
            extra = set(row) - columns
            if extra:
                issues.append(f"{rid}[{i}] has undeclared column(s) {sorted(extra)} "
                              f"(declared: {sorted(columns)})")
            # controlled vocabulary
            for col, allowed in enums.items():
                cell = str(row.get(col, "")).strip()
                if cell and cell not in allowed:
                    issues.append(f"{rid}[{i}].{col} = {cell!r} is not in {list(allowed)}")
            if strict:
                # (a) traceability — a register that declares evidence column(s) must fill ≥1 per row
                if evidence_cols and not any(str(row.get(c, "")).strip() for c in evidence_cols):
                    issues.append(f"{rid}[{i}] is ungrounded — fill traceability in one of "
                                  f"{sorted(evidence_cols)}")
                # (b) no FQDN smuggled into a business-language content column. Scope: `bl_columns`
                #     names the business-language columns (None ⇒ the whole register). A column-scoped
                #     register (e.g. S6b new_artifacts: bl_columns=['capability']) legitimately carries
                #     binding FQDNs in its OTHER content columns (`code`), so only the named columns are
                #     checked — mirroring the renderer's oracle.
                if business:
                    bl = spec.get("bl_columns")
                    checked = (content_cols & set(bl)) if bl else content_cols
                    for col in checked:
                        cell = str(row.get(col, ""))
                        m = _FQDN_RE.search(cell)
                        if m:
                            issues.append(f"{rid}[{i}].{col} contains a protocol identifier "
                                          f"{m.group(0)!r} — FQDNs belong only in the evidence "
                                          f"column at this stage")
        return issues

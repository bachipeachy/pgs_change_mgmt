"""Construction harness (Phase 5) — transcribe a CONSTRUCTION_READY Build Sheet into a protocol
artifact, with an interchangeable builder.

Because the Build Sheet is construction-closed, the builder's task is TRANSCRIPTION, not synthesis:
every pipeline step, input, output and routing outcome is already governed. The system role forbids
design — if a required element is missing the builder must STOP and report, never invent. This is the
thin-slice lesson operationalised: the failed renderer asked a model to *synthesise* the contract;
this asks it only to *materialise* an already-complete specification. The builder (qwen3:14b, qwen3.5,
Claude, a future generator) is interchangeable — authority lives in the sheet, not the builder.
"""

from __future__ import annotations

from typing import Any, Protocol

from ..engine.build_sheet import BuildSheetModel, FieldValue, GAP, code_part

CONSTRUCTOR_SYSTEM = (
    "You are a CONSTRUCTOR, not a designer. You materialise a governed Build Sheet into a protocol "
    "artifact authoring document. The Build Sheet is COMPLETE: every pipeline step, input, output and "
    "routing outcome is already decided and given to you. Your ONLY job is to transcribe it into the "
    "artifact's authoring markdown, following the FORMAT EXEMPLAR's structure exactly.\n"
    "RULES:\n"
    "- Introduce NO design decision. Use ONLY what the Build Sheet states.\n"
    "- Copy every FQDN VERBATIM. Invent no code, field, step, or outcome.\n"
    "- If a REQUIRED element is missing from the sheet, output exactly one line "
    "`STOP: missing <what>` and nothing else — do NOT guess.\n"
    "- Output ONLY the artifact markdown, no commentary."
)


class Builder(Protocol):
    """Anything with an ollama-style chat (e.g. `worker.ollama_client.OllamaClient`)."""
    def chat(self, messages: list[dict[str, Any]], tools: list | None = ...) -> dict[str, Any]: ...


def _fv(fv: FieldValue | None) -> str:
    if fv is None:
        return "—"
    if fv.status == GAP:
        return f"<GAP: {fv.value}>"
    v = fv.value
    if isinstance(v, list):
        if v and isinstance(v[0], dict) and "step" in v[0]:        # composition steps
            return " | ".join(
                f"step {r.get('step')}: {code_part(r.get('capability'))} "
                f"({r.get('kind')}.{r.get('operation')}) "
                f"consumes[{r.get('consumes')}] produces[{r.get('produces')}]" for r in v)
        if v and isinstance(v[0], dict):                            # topology / bindings rows
            return "; ".join(", ".join(f"{k}={vv}" for k, vv in r.items()) for r in v)
        return ", ".join(str(x) for x in v)
    return str(v) if v is not None else "—"


def sheet_spec(sheet: BuildSheetModel) -> str:
    """The Build Sheet rendered as a transcription brief (Part A + Part B + open GAPs)."""
    lines = [f"BUILD SHEET — {sheet.code}  (kind {sheet.kind}, action {sheet.action})", "",
             "## Governing Truth"]
    lines += [f"- {k}: {_fv(fv)}" for k, fv in sheet.part_a.items()]
    lines += ["", "## Construction Specification"]
    lines += [f"- {k}: {_fv(fv)}" for k, fv in sheet.part_b.items()]
    if getattr(sheet, "entity_fields", ()):
        lines += ["", "## Governed Field Vocabulary (use ONLY these field names; invent none)",
                  "  " + ", ".join(sheet.entity_fields)]
    if sheet.gaps:
        lines += ["", "## OPEN GAPS (do NOT invent — STOP if any blocks construction)"]
        lines += [f"- {g.gap_class}[{g.field}]" for g in sheet.gaps]
    return "\n".join(lines)


def build_prompt(sheet: BuildSheetModel, fmt_exemplar: str = "") -> list[dict[str, str]]:
    user = [sheet_spec(sheet)]
    if fmt_exemplar:
        user += ["", "## FORMAT EXEMPLAR — follow this artifact's structure exactly", "", fmt_exemplar]
    user += ["", f"Now produce the authoring markdown for {sheet.code}. Transcribe the Build Sheet "
                 f"faithfully; invent nothing."]
    return [{"role": "system", "content": CONSTRUCTOR_SYSTEM},
            {"role": "user", "content": "\n".join(user)}]


def _content(resp: Any) -> str:
    if isinstance(resp, dict):
        m = resp.get("message")
        if isinstance(m, dict) and "content" in m:
            return m["content"]
        for k in ("content", "response"):
            if k in resp:
                return resp[k]
    return str(resp)


def extract_markdown(text: str) -> str:
    """Strip a reasoning model's chain-of-thought and a single wrapping ``` fence.

    Reasoning models (deepseek-r1, etc.) prepend a `<think>…</think>` block before the answer; we
    keep only what follows it, so the artifact audit measures the artifact — not the reasoning.
    """
    t = text.strip()
    if "</think>" in t:                       # reasoning-model chain-of-thought → keep the answer only
        t = t.split("</think>")[-1].strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.strip()


def transcribe(sheet: BuildSheetModel, fmt_exemplar: str, builder: Builder) -> str:
    """Construct the artifact authoring markdown for one Build Sheet via `builder`."""
    resp = builder.chat(build_prompt(sheet, fmt_exemplar))
    return extract_markdown(_content(resp))

"""Shared authoring primitives — the worker-side pieces that are transport-agnostic.

Every worker frames the same bounded stage task and parses the same structured emission;
only the *transport* between the framed prompt and the model differs (ollama daemon, Anthropic
API, a human pasting into a chat UI, a recorded replay). This module owns the shared pieces so
there is exactly one of each, never a per-transport fork:

  * `SYSTEM_PROMPT` — the governed authoring mandate (no protocol knowledge of its own; ground
    every fact via a tool call; emit a single fenced ```json object).
  * `render_task(StageInput)` — the task framing (objective + governance rules + bounded handoff).
  * `parse_output(mode, raw)` — ONE json-block extraction core with thin per-mode pre-normalizers
    (`automated` / `interactive` / `replay`). Splitting the worker's emission into
    (registers, questions, findings) is identical across transports; only the surrounding noise a
    given transport introduces differs, so each mode is a *pre-normalizer over the shared core*,
    never a divergent parser (Pipeline Trifecta plan §4a P3).
"""

from __future__ import annotations

import json
from typing import Any

from ..contracts import StageInput

# The three transports the parse core serves. `automated` — model content interleaved with
# tool-loop noise (today's worker path). `interactive` — human-pasted text that may carry
# copy-paste artifacts / surrounding chatter / a fence the human dropped. `replay` — a recorded
# response replayed deterministically for regression (clean, no normalization).
PARSE_MODES = ("automated", "interactive", "replay")

SYSTEM_PROMPT = """You are a change-management authoring worker for a Protocol-Governed System (PGS).

ABSOLUTE RULE — you have NO protocol knowledge of your own. Every protocol fact (artifact
FQDNs, who references what, workflow routing, change impact, artifact content, snapshot
validity) MUST come from a tool call. Never state a protocol fact from memory; if you have
not retrieved it via a tool, you do not know it. Never guess an FQDN — discover it with
vocab_search first (search a single UPPERCASE code token like 'WALLET', not a phrase).

You are given one stage's objective, the upstream handoff you may read, and the governance
rules in force. Do the stage's work, then emit your result as a SINGLE fenced ```json object
with these keys:
  "registers": { <field>: <value>, ... }   the stage's structured outputs (copy FQDNs verbatim)
  "questions": [ <string>, ... ]            open questions for a later stage (may be empty)
Output your reasoning as plain text BEFORE the json block. Emit no machine artifact syntax —
a downstream renderer owns that. Do not claim a change is valid; call validate and report it."""


def render_task(task: StageInput) -> str:
    """Frame the bounded stage task as the worker's user prompt.

    The same framing every transport sends: objective, governance rules, and the bounded upstream
    `gov_projection` this stage may read (and nothing else)."""
    bounded = json.dumps(dict(task.input_projection.values), indent=2, default=str)
    rules = "\n".join(f"- {r}" for r in task.governance_rules) or "- (none)"
    return (
        f"# STAGE {task.stage}\n\n"
        f"## Objective\n{task.objective}\n\n"
        f"## Governance rules in force\n{rules}\n\n"
        f"## Upstream handoff you may read (bounded context)\n```json\n{bounded}\n```\n"
    )


# ---- output parsing: one core + per-mode pre-normalizers (P3) -------------------------------

def parse_output(mode: str, raw: str) -> tuple[dict[str, Any], tuple[str, ...], tuple[str, ...]]:
    """Split a worker's emission into (registers, questions, findings) for any transport.

    `mode` selects a thin pre-normalizer; all three then run the SAME extraction core:
      * automated — pass through (the model's text already carries a fenced ```json block).
      * interactive — tolerate copy-paste artifacts and a dropped fence: if the human pasted a
        bare json object with no ```json fence, wrap it so the core can find it; otherwise identical.
      * replay — pass through (a recorded response is already clean and deterministic).
    Unknown modes are a programming error, not input to tolerate."""
    if mode not in PARSE_MODES:
        raise ValueError(f"unknown parse mode {mode!r} — expected one of {PARSE_MODES}")
    if mode == "interactive":
        raw = _normalize_interactive(raw)
    return _parse_core(raw)


def _parse_core(text: str) -> tuple[dict[str, Any], tuple[str, ...], tuple[str, ...]]:
    """The shared extraction core (promoted verbatim from OllamaWorker._parse_output).

    The structured result is a single fenced ```json object. Accept BOTH shapes a model produces
    in practice:
      * enveloped — {"registers": {...}, "questions": [...]}  (the asked-for shape), and
      * bare      — the contract object itself at top level ({"summary":..,"pipeline":..}).
    A model emits these interchangeably, so keying strictly on "registers" silently dropped a
    complete, correct contract. Free text outside the block → `findings`. A missing/unparseable
    block yields empty registers (the engine's handoff check then flags the lossless-handoff
    failure)."""
    registers: dict[str, Any] = {}
    questions: tuple[str, ...] = ()
    findings: tuple[str, ...] = (text,) if text else ()
    block = last_json_block(text)
    if block is not None:
        try:
            obj = json.loads(block)
        except json.JSONDecodeError:
            return registers, questions, findings
        if isinstance(obj, dict):
            reg = obj.get("registers")
            if isinstance(reg, dict):
                registers = reg                       # enveloped form
                q = obj.get("questions") or []
                questions = tuple(str(x) for x in q) if isinstance(q, (list, tuple)) else ()
            else:
                registers = obj                       # bare contract object
    return registers, questions, findings


def last_json_block(text: str) -> str | None:
    """Return the contents of the last ```json fenced block, if any."""
    marker = "```json"
    idx = text.rfind(marker)
    if idx == -1:
        return None
    rest = text[idx + len(marker):]
    end = rest.find("```")
    return rest[:end].strip() if end != -1 else rest.strip()


def _normalize_interactive(raw: str) -> str:
    """Pre-normalize human-pasted text so the shared core can extract its json block.

    The core keys on a ```json fence. A human pasting from a chat UI sometimes drops the fence
    (pastes the bare object) or uses a plain ``` fence. When there is no ```json fence, locate the
    outermost balanced top-level json object and re-wrap it in a ```json fence — synthesizing what
    the core expects rather than forking a second extractor. If a ```json fence is already present,
    the text is returned unchanged (interactive then behaves exactly like automated)."""
    if "```json" in raw:
        return raw
    obj = _outermost_json_object(raw)
    if obj is None:
        return raw
    return f"```json\n{obj}\n```"


def _outermost_json_object(text: str) -> str | None:
    """Return the first balanced `{...}` substring that parses as a json object, else None.

    Scans from the first `{`, tracking brace depth while skipping string literals, so a brace
    inside a quoted value does not unbalance the scan. Used only by the interactive pre-normalizer
    — the automated/replay paths require an explicit fence and never reach here."""
    start = text.find("{")
    while start != -1:
        depth = 0
        in_str = False
        esc = False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start:i + 1]
                    try:
                        json.loads(candidate)
                        return candidate
                    except json.JSONDecodeError:
                        break   # unbalanced/invalid from this start; advance to the next `{`
        start = text.find("{", start + 1)
    return None

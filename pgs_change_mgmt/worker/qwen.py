"""QwenWorker — the single concrete `contracts.Worker` today (a local qwen via ollama).

The worker executes one bounded stage task: it is handed a `StageInput` (the stage, its
objective, the bounded upstream `gov_projection` it may read, and the governance rules in
force) and returns a `StageOutput` (registers / questions / findings). It grounds every
protocol fact through an injected `GroundingProvider` — it never reaches the compiler, the
runtime, governance internals, or storage, and it never emits machine syntax (that is the
Renderer's job).

Two proven Phase-0 mechanisms are folded in:
  * the grounded tool-loop (model turn → tool call → `pi` evidence → model turn), so every
    protocol claim traces to a query result; and
  * structured emission — the worker ends with a single ```json object carrying its
    `registers` (and optional `questions`), which the engine projects into the stage's
    `gov_projection`. Free-text reasoning becomes `findings`.

`num_ctx` is pinned high on the transport (`OllamaClient`, 65536): ollama otherwise defaults
to ~4096 and silently truncates the large authoring prompt *from the front*, dropping the
template/seed. The worker re-asserts that pin explicitly so a transport default can never
quietly shrink it.
"""

from __future__ import annotations

import json
from typing import Any, Callable

from ..contracts import StageInput, StageOutput
from ..contracts import GroundingProvider
from ..grounding import TOOL_SCHEMAS, TOOL_NAMES, PiError
from .ollama_client import OllamaClient, OllamaError

# The context window is a correctness property of authoring, not a tuning knob — pin it.
PINNED_NUM_CTX = 65536

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


class QwenWorker:
    """`contracts.Worker` backed by a local qwen model over ollama, grounded by PI."""

    def __init__(
        self,
        grounding: GroundingProvider,
        *,
        model: str = "qwen3.5:latest",
        system_prompt: str = SYSTEM_PROMPT,
        max_iters: int = 12,
        llm: OllamaClient | None = None,
        on_event: "Callable[..., None] | None" = None,
    ) -> None:
        self.grounding = grounding
        self.name = model
        self.system_prompt = system_prompt
        self.max_iters = max_iters
        # Optional observability hook: called as on_event(kind, **fields) for each tool call
        # and the convergence guard. The engine/CLI wires this to a colored verbose printer.
        self.on_event = on_event
        # Build the transport with the pin re-asserted; never inherit an implicit default.
        self.llm = llm or OllamaClient(model=model, num_ctx=PINNED_NUM_CTX)
        if self.llm.num_ctx < PINNED_NUM_CTX:
            self.llm.num_ctx = PINNED_NUM_CTX

    def _emit(self, kind: str, **fields: Any) -> None:
        if self.on_event is not None:
            self.on_event(kind, **fields)

    @staticmethod
    def _result_size(envelope: Any) -> int:
        """How many results a pi envelope carries (for the green/yellow anomaly flag)."""
        if not isinstance(envelope, dict):
            return 0
        res = envelope.get("result")
        if isinstance(res, list):
            return len(res)
        if isinstance(res, dict):
            return len(res)
        return 0 if res is None else 1

    # ---- the bounded stage task ------------------------------------------

    def execute_stage(self, task: StageInput) -> StageOutput:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self._render_task(task)},
        ]
        final_text, telem = self._agent_loop(messages)
        registers, questions, findings = self._parse_output(final_text)
        # Always surface loop telemetry as the first finding, so a failed/empty authoring
        # is diagnosable (did the model finish, exhaust max_iters, or stall on empty turns?).
        telem_line = (f"[tool-loop: iters={telem['iters']}/{self.max_iters} "
                      f"tool_calls={telem['tool_calls']} reason={telem['reason']} "
                      f"final_chars={len(final_text)}]")
        return StageOutput(
            stage=task.stage,
            registers=registers,
            questions=questions,
            findings=(telem_line, *findings),
        )

    # ---- task framing ----------------------------------------------------

    @staticmethod
    def _render_task(task: StageInput) -> str:
        bounded = json.dumps(dict(task.input_projection.values), indent=2, default=str)
        rules = "\n".join(f"- {r}" for r in task.governance_rules) or "- (none)"
        return (
            f"# STAGE {task.stage}\n\n"
            f"## Objective\n{task.objective}\n\n"
            f"## Governance rules in force\n{rules}\n\n"
            f"## Upstream handoff you may read (bounded context)\n```json\n{bounded}\n```\n"
        )

    # ---- the grounded tool-loop (worker mechanism) -----------------------

    def _agent_loop(self, messages: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
        """Drive model↔grounding turns until the model stops calling tools.

        Each tool call is dispatched to the read-only `GroundingProvider.query`; the verbatim
        envelope is fed back as a tool message, so every protocol fact traces to evidence.
        Returns (final_content, telemetry) where telemetry = {iters, tool_calls, reason} and
        reason ∈ {finished, max_iters, empty_stall}. `final` falls back to reasoning if content
        is empty.
        """
        final = ""
        reason = "max_iters"     # default: loop exhausted its iteration budget
        tool_calls = 0
        seen: set[str] = set()   # (name,args) signatures, for repeat-query anomaly flagging
        nudged = False
        empty_retries = 0
        chat_errors = 0
        i = 0
        while i < self.max_iters:
            i += 1
            try:
                msg = self.llm.chat(messages, tools=TOOL_SCHEMAS)
            except OllamaError as exc:
                # a slow/hung/unreachable model must NOT crash the run — retry a couple of
                # times (transient), then end the stage gracefully (the engine records an
                # empty doc + the telemetry, rating 0, rather than bombing the pipeline).
                chat_errors += 1
                self._emit("model_error", attempt=chat_errors, error=str(exc))
                if chat_errors <= 2:
                    i -= 1
                    continue
                reason = "model_error"
                break
            calls = msg.get("tool_calls") or []
            content = (msg.get("content") or "").strip()
            thinking = (msg.get("thinking") or "").strip()

            if not calls and not content and len(thinking) < 40:
                empty_retries += 1
                if empty_retries <= 3:
                    i -= 1  # a stalled/garbled turn — retry without spending an iteration
                    continue
                reason = "empty_stall"
                break

            messages.append(msg)
            if not calls:
                if not content and thinking and not nudged:
                    nudged = True
                    messages.append({
                        "role": "user",
                        "content": "Now write your final answer and the ```json result block.",
                    })
                    continue
                final = content or thinking
                reason = "finished"
                break

            for call in calls:
                fn = call["function"]
                name = fn["name"]
                args = fn.get("arguments") or {}
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}
                tool_calls += 1
                sig = f"{name}({json.dumps(args, sort_keys=True)})"
                is_repeat = sig in seen
                seen.add(sig)
                try:
                    result_payload: Any = self.grounding.query(name, **args)
                    err = None
                    n_results = self._result_size(result_payload)
                except (PiError, KeyError, TypeError) as exc:
                    result_payload = {"error": str(exc)}
                    err = str(exc)
                    n_results = 0
                # anomaly flag: error → red, empty/repeat → yellow, results → green
                flag = "red" if err else ("yellow" if (n_results == 0 or is_repeat) else "green")
                self._emit("tool_call", name=name, args=args, ok=err is None,
                           n_results=n_results, repeat=is_repeat, error=err, flag=flag)
                messages.append({
                    "role": "tool",
                    "tool_name": name,
                    "content": json.dumps(result_payload),
                })

        # Convergence guard: the model exhausted its budget (or stalled) without ever writing
        # a final answer. Force ONE tool-free turn demanding the result with the evidence in
        # hand — a discovery-heavy stage otherwise grounds forever and emits nothing.
        if not final:
            messages.append({
                "role": "user",
                "content": "You have used your full tool budget — do NOT call any more tools. "
                           "Using only the evidence already gathered, write your final answer "
                           "now (the completed document, then the single ```json result block).",
            })
            try:
                msg = self.llm.chat(messages)  # no tools offered → must answer
                forced = (msg.get("content") or msg.get("thinking") or "").strip()
            except Exception:
                forced = ""
            self._emit("convergence_forced", produced=bool(forced))
            if forced:
                final = forced
                reason = "finished_forced"

        return final, {"iters": i, "tool_calls": tool_calls, "reason": reason}

    # ---- output projection ----------------------------------------------

    @staticmethod
    def _parse_output(text: str) -> tuple[dict[str, Any], tuple[str, ...], tuple[str, ...]]:
        """Split the worker's emission into (registers, questions, findings).

        The structured result is a single fenced ```json object. We accept BOTH shapes the
        model produces in practice:
          * enveloped — {"registers": {...}, "questions": [...]}  (the asked-for shape), and
          * bare      — the contract object itself at top level ({"summary":..,"pipeline":..}).
        A local model emits these interchangeably, so keying strictly on "registers" silently
        dropped a complete, correct contract (observed on CC_QUERY_MEMPOOL_TXS_V0). Free text
        outside the block → `findings`. A missing/unparseable block yields empty registers
        (the engine's handoff check then flags the lossless-handoff failure)."""
        registers: dict[str, Any] = {}
        questions: tuple[str, ...] = ()
        findings: tuple[str, ...] = (text,) if text else ()
        block = QwenWorker._last_json_block(text)
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

    @staticmethod
    def _last_json_block(text: str) -> str | None:
        """Return the contents of the last ```json fenced block, if any."""
        marker = "```json"
        idx = text.rfind(marker)
        if idx == -1:
            return None
        rest = text[idx + len(marker):]
        end = rest.find("```")
        return rest[:end].strip() if end != -1 else rest.strip()

"""ClaudeWorker — a second `contracts.Worker`, backed by Claude via the Anthropic API.

(`worker/__init__.py`: "A second worker (Claude, GPT, a human analyst) is an addition here,
never a refactor.") This is that addition. It exists for one purpose: a controlled A/B against
`QwenWorker` — *is the dossier pipeline hard to execute (design problem), or is the local qwen
under-powered (worker problem)?* To make the comparison clean, this worker is a true drop-in:

  * SAME bounded task — it receives only the `StageInput` the engine builds (objective + the
    template + the upstream handoff). A programmatic worker has no ambient context: no CLAUDE.md,
    no auto-memory, no skills. The only thing it sees is what the engine sends — so there is
    nothing to "wipe" for a pristine run.
  * SAME system prompt, task framing, and output parsing — reused verbatim from `QwenWorker`
    (`SYSTEM_PROMPT`, `_render_task`, `_parse_output`, `_result_size`). The contract the worker
    must satisfy is byte-identical to qwen's.
  * SAME grounded tool-loop shape, SAME `max_iters` budget, SAME `on_event` telemetry, SAME
    convergence guard. Only the transport (Anthropic Messages API) and the model differ.

What it deliberately does NOT control: parametric capability. Claude is a far stronger base
model than `qwen3.5:latest`; that confound is unremovable and is the whole point — this measures
the *ceiling* a capable worker reaches on the same contract.

Transport is raw HTTP via stdlib `urllib` (the workspace forbids `pip install`, and the
`anthropic` SDK is not present). Model defaults to `claude-opus-4-8` with adaptive thinking —
the strongest config, since this is a ceiling test. `ANTHROPIC_API_KEY` must be in the
environment at run time (the worker has no key baked in).
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Callable

from ..contracts import StageInput, StageOutput
from ..contracts import GroundingProvider
from ..grounding import TOOL_SCHEMAS, PiError
from .qwen import QwenWorker, SYSTEM_PROMPT

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-opus-4-8"

# Translate the ollama/openai function schemas the grounding layer publishes into the Anthropic
# tool shape: {name, description, input_schema}. Same tools, same descriptions — only the
# envelope differs, so the worker sees an identical capability surface to qwen's.
ANTHROPIC_TOOLS = [
    {
        "name": s["function"]["name"],
        "description": s["function"]["description"],
        "input_schema": s["function"]["parameters"],
    }
    for s in TOOL_SCHEMAS
]


class ClaudeError(RuntimeError):
    """Anthropic transport failure (non-retryable, or retries exhausted)."""


class ClaudeWorker:
    """`contracts.Worker` backed by Claude over the Anthropic Messages API, grounded by PI.

    A drop-in twin of `QwenWorker` for A/B: identical contract, identical loop shape, identical
    telemetry — only the model and transport change.
    """

    def __init__(
        self,
        grounding: GroundingProvider,
        *,
        model: str = DEFAULT_MODEL,
        system_prompt: str = SYSTEM_PROMPT,
        max_iters: int = 24,
        on_event: "Callable[..., None] | None" = None,
        api_key: str | None = None,
        effort: str = "high",
        # S3 (analysis loop) spends heavily on adaptive-thinking tokens, which count toward
        # max_tokens; 16000 truncated its final register block (the only reason the S3 A/B was
        # inconclusive). 32000 gives thinking + the largest register payload room to complete.
        max_tokens: int = 32000,
        timeout: float = 900.0,
    ) -> None:
        self.grounding = grounding
        self.name = model
        self.model = model
        self.system_prompt = system_prompt
        self.max_iters = max_iters
        self.on_event = on_event
        self.effort = effort
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ClaudeError(
                "ANTHROPIC_API_KEY is not set — the Claude worker needs it at run time. "
                "Export it (or run: ! export ANTHROPIC_API_KEY=...) before invoking."
            )

    def _emit(self, kind: str, **fields: Any) -> None:
        if self.on_event is not None:
            self.on_event(kind, **fields)

    # ---- the bounded stage task (mirrors QwenWorker.execute_stage exactly) ------

    def execute_stage(self, task: StageInput) -> StageOutput:
        messages = [{"role": "user", "content": QwenWorker._render_task(task)}]
        final_text, telem = self._agent_loop(messages)
        registers, questions, findings = QwenWorker._parse_output(final_text)
        telem_line = (f"[tool-loop: iters={telem['iters']}/{self.max_iters} "
                      f"tool_calls={telem['tool_calls']} reason={telem['reason']} "
                      f"final_chars={len(final_text)}]")
        return StageOutput(
            stage=task.stage,
            registers=registers,
            questions=questions,
            findings=(telem_line, *findings),
        )

    # ---- transport -------------------------------------------------------

    def _post(self, body: dict[str, Any]) -> dict[str, Any]:
        """One Messages API call (raw HTTP), with retry on 429/5xx/529."""
        data = json.dumps(body).encode()
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }
        last_exc: Exception | None = None
        for attempt in range(4):
            req = urllib.request.Request(ANTHROPIC_URL, data=data, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return json.loads(resp.read())
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode(errors="replace")
                if exc.code in (429, 500, 502, 503, 529) and attempt < 3:
                    last_exc = ClaudeError(f"HTTP {exc.code}: {detail[:300]}")
                    time.sleep(min(2 ** attempt + 0.5, 20))
                    continue
                raise ClaudeError(f"HTTP {exc.code}: {detail[:500]}") from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                last_exc = ClaudeError(f"transport error: {exc}")
                if attempt < 3:
                    time.sleep(min(2 ** attempt + 0.5, 20))
                    continue
                raise last_exc from exc
        raise last_exc or ClaudeError("request failed")

    def _chat(self, messages: list[dict[str, Any]], *, use_tools: bool) -> dict[str, Any]:
        """Adaptive thinking + high effort = the strongest config (this is a ceiling test)."""
        body: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": self.system_prompt,
            "messages": messages,
            "thinking": {"type": "adaptive"},
            "output_config": {"effort": self.effort},
            "tools": ANTHROPIC_TOOLS,
        }
        if not use_tools:
            body["tool_choice"] = {"type": "none"}   # forced final turn — no more tools
        return self._post(body)

    # ---- the grounded tool-loop (same shape as QwenWorker._agent_loop) ----

    def _agent_loop(self, messages: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
        final = ""
        reason = "max_iters"
        tool_calls = 0
        seen: set[str] = set()
        chat_errors = 0
        i = 0
        while i < self.max_iters:
            i += 1
            try:
                msg = self._chat(messages, use_tools=True)
            except ClaudeError as exc:
                chat_errors += 1
                self._emit("model_error", attempt=chat_errors, error=str(exc))
                if chat_errors <= 2:
                    i -= 1
                    continue
                reason = "model_error"
                break

            blocks = msg.get("content") or []
            stop = msg.get("stop_reason")
            tool_uses = [b for b in blocks if b.get("type") == "tool_use"]
            text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text").strip()

            if stop != "tool_use" or not tool_uses:
                final = text
                # surface a truncated turn so an empty/short authoring is diagnosable
                reason = "finished" if stop != "max_tokens" else "finished_truncated"
                break

            # preserve the assistant turn verbatim — thinking + tool_use blocks must be carried
            # back unmodified for the API to continue a thinking-enabled tool loop.
            messages.append({"role": "assistant", "content": blocks})
            results = []
            for tu in tool_uses:
                name = tu.get("name", "")
                args = tu.get("input") or {}
                tool_calls += 1
                sig = f"{name}({json.dumps(args, sort_keys=True)})"
                is_repeat = sig in seen
                seen.add(sig)
                try:
                    payload: Any = self.grounding.query(name, **args)
                    err = None
                    n_results = QwenWorker._result_size(payload)
                except (PiError, KeyError, TypeError) as exc:
                    payload = {"error": str(exc)}
                    err = str(exc)
                    n_results = 0
                flag = "red" if err else ("yellow" if (n_results == 0 or is_repeat) else "green")
                self._emit("tool_call", name=name, args=args, ok=err is None,
                           n_results=n_results, repeat=is_repeat, error=err, flag=flag)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": tu.get("id"),
                    "content": json.dumps(payload),
                })
            messages.append({"role": "user", "content": results})

        # Convergence guard: budget exhausted without a final answer. Force ONE tool-free turn.
        if not final:
            messages.append({
                "role": "user",
                "content": "You have used your full tool budget — do NOT call any more tools. "
                           "Using only the evidence already gathered, write your final answer "
                           "now (the completed document, then the single ```json result block).",
            })
            try:
                msg = self._chat(messages, use_tools=False)
                forced = "".join(b.get("text", "") for b in (msg.get("content") or [])
                                 if b.get("type") == "text").strip()
            except ClaudeError:
                forced = ""
            self._emit("convergence_forced", produced=bool(forced))
            if forced:
                final = forced
                reason = "finished_forced"

        return final, {"iters": i, "tool_calls": tool_calls, "reason": reason}

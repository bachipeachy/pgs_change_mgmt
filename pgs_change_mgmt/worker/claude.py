"""ClaudeWorker — a second `contracts.Worker`, backed by Claude via the Anthropic API.

(`worker/__init__.py`: "A second worker (Claude, GPT, a human analyst) is an addition here,
never a refactor.") This is that addition. It exists for one purpose: a controlled A/B against
`OllamaWorker` — *is the dossier pipeline hard to execute (design problem), or is the local qwen
under-powered (worker problem)?* To make the comparison clean, this worker is a true drop-in:

  * SAME bounded task — it receives only the `StageInput` the engine builds (objective + the
    template + the upstream handoff). A programmatic worker has no ambient context: no CLAUDE.md,
    no auto-memory, no skills. The only thing it sees is what the engine sends.
  * SAME system prompt, task framing, output parsing — reused verbatim from `OllamaWorker`
    (`SYSTEM_PROMPT`, `_render_task`, `_parse_output`).
  * SAME grounded tool-loop — literally the shared `_loop.run_tool_loop` (budget, convergence
    guard, forced-finalization contract, telemetry). Only the transport (Anthropic Messages API)
    and the model differ — that is the whole point of a worker.

What it deliberately does NOT control: parametric capability. Claude is a far stronger base
model than `qwen3.5:latest`; that confound is unremovable and is the whole point — this measures
the *ceiling* a capable worker reaches on the same contract.

Transport is raw HTTP via stdlib `urllib` (the workspace forbids `pip install`, and the
`anthropic` SDK is not present). Model defaults to `claude-opus-4-8` with adaptive thinking.
`ANTHROPIC_API_KEY` must be in the environment at run time (the worker has no key baked in).
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
from ..grounding import TOOL_SCHEMAS
from ._loop import ToolCall, Turn, TransportError, run_tool_loop
from .ollama_worker import OllamaWorker, SYSTEM_PROMPT

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


class AnthropicTransport:
    """`_loop.Transport` for Claude over the Anthropic Messages API — owns the native block history.

    Normalizes Anthropic content-block turns (`text` / `tool_use`, `stop_reason`) into a `Turn`, and
    translates the loop's `ToolCall` results back into a `tool_result` user message. The assistant
    turn (thinking + tool_use blocks) is carried back verbatim so a thinking-enabled tool loop
    continues correctly.
    """

    def __init__(self, chat: "Callable[..., dict[str, Any]]", task_text: str) -> None:
        self._chat = chat   # ClaudeWorker._chat (system prompt + credentials + config live there)
        self.messages: list[dict[str, Any]] = [{"role": "user", "content": task_text}]

    def model_turn(self, *, use_tools: bool) -> Turn:
        try:
            msg = self._chat(self.messages, use_tools=use_tools)
        except ClaudeError as exc:
            raise TransportError(str(exc)) from exc
        blocks = msg.get("content") or []
        stop = msg.get("stop_reason")
        tool_uses = [b for b in blocks if b.get("type") == "tool_use"]
        text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text").strip()
        active = stop == "tool_use" and bool(tool_uses)
        if active:
            # preserve the assistant turn verbatim — thinking + tool_use blocks must be carried
            # back unmodified for the API to continue a thinking-enabled tool loop.
            self.messages.append({"role": "assistant", "content": blocks})
        tool_calls = ([ToolCall(id=tu.get("id"), name=tu.get("name", ""), args=tu.get("input") or {})
                       for tu in tool_uses] if active else [])
        return Turn(text=text, tool_calls=tool_calls, truncated=(stop == "max_tokens"))

    def add_tool_results(self, calls: list[ToolCall]) -> None:
        self.messages.append({"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": call.id, "content": json.dumps(call.payload)}
            for call in calls]})

    def add_user(self, text: str) -> None:
        self.messages.append({"role": "user", "content": text})


class ClaudeWorker:
    """`contracts.Worker` backed by Claude over the Anthropic Messages API, grounded by PI.

    A drop-in twin of `OllamaWorker` for A/B: identical contract, identical (shared) loop, identical
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
        # max_tokens; 16000 truncated its final register block. 32000 gives thinking + the largest
        # register payload room to complete.
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

    # ---- the bounded stage task (shared loop; only the transport is Claude's) ------

    def execute_stage(self, task: StageInput) -> StageOutput:
        transport = AnthropicTransport(self._chat, OllamaWorker._render_task(task))
        final_text, telem = run_tool_loop(
            transport, self.grounding, max_iters=self.max_iters, emit=self._emit)
        registers, questions, findings = OllamaWorker._parse_output(final_text)
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

"""OllamaWorker — a `contracts.Worker` backed by ANY local model served over ollama.

The defining trait is the **transport** (the ollama daemon), not the model: one worker serves
qwen, deepseek, llama, … interchangeably by its `model` tag. Provider-specific workers
(`ClaudeWorker`, `GeminiWorker`) exist only because they are *different transports* — a
deepseek-over-ollama builder is this same worker with a different tag.

The worker executes one bounded stage task: it is handed a `StageInput` (the stage, its
objective, the bounded upstream `gov_projection` it may read, and the governance rules in
force) and returns a `StageOutput` (registers / questions / findings). It grounds every
protocol fact through an injected `GroundingProvider` — it never reaches the compiler, the
runtime, governance internals, or storage, and it never emits machine syntax (that is the
Renderer's job).

The grounded tool-loop itself lives in `_loop.run_tool_loop` (shared by every worker — its policy
is governance, not a per-model trait). This module contributes only the ollama **transport**
(`OllamaTransport`) plus the task framing / output parsing. `num_ctx` is pinned high on the
transport (`OllamaClient`, 65536): ollama otherwise defaults to ~4096 and silently truncates the
large authoring prompt *from the front*, dropping the template/seed; the worker re-asserts the pin.
"""

from __future__ import annotations

import json
from typing import Any, Callable

from ..contracts import StageInput, StageOutput
from ..contracts import GroundingProvider
from ..grounding import TOOL_SCHEMAS
from .ollama_client import OllamaClient, OllamaError
from ._loop import ToolCall, Turn, TransportError, run_tool_loop
# Shared, transport-agnostic authoring primitives (one of each, never a per-transport fork).
# SYSTEM_PROMPT is re-exported here for back-compat (worker/__init__ and callers import it from
# this module); the canonical definition lives in `_authoring`.
from ._authoring import SYSTEM_PROMPT, render_task, parse_output

# The context window is a correctness property of authoring, not a tuning knob — pin it.
PINNED_NUM_CTX = 65536


class OllamaTransport:
    """`_loop.Transport` for any local model over ollama — owns the ollama-native message history.

    Normalizes ollama's `{content, thinking, tool_calls}` turn into a `Turn`, and translates the
    loop's `ToolCall` results back into ollama `role: tool` messages. The empty-turn detection
    (ollama can return a stalled/garbled turn) is encoded here as `Turn.empty`.
    """

    def __init__(self, llm: OllamaClient, system_prompt: str, task_text: str) -> None:
        self.llm = llm
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task_text},
        ]

    def model_turn(self, *, use_tools: bool) -> Turn:
        try:
            msg = (self.llm.chat(self.messages, tools=TOOL_SCHEMAS) if use_tools
                   else self.llm.chat(self.messages))   # forced final turn: no tools offered
        except OllamaError as exc:
            raise TransportError(str(exc)) from exc
        calls = msg.get("tool_calls") or []
        content = (msg.get("content") or "").strip()
        thinking = (msg.get("thinking") or "").strip()
        empty = not calls and not content and len(thinking) < 40
        if not empty:
            self.messages.append(msg)   # carry the assistant turn for continuation
        tool_calls: list[ToolCall] = []
        for call in calls:
            fn = call["function"]
            args = fn.get("arguments") or {}
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            tool_calls.append(ToolCall(name=fn["name"], args=args))
        return Turn(text=content, thinking=thinking, tool_calls=tool_calls, empty=empty)

    def add_tool_results(self, calls: list[ToolCall]) -> None:
        for call in calls:
            self.messages.append({
                "role": "tool", "tool_name": call.name, "content": json.dumps(call.payload),
            })

    def add_user(self, text: str) -> None:
        self.messages.append({"role": "user", "content": text})


class OllamaWorker:
    """`contracts.Worker` backed by any local model over ollama, grounded by PI."""

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

    # ---- the bounded stage task ------------------------------------------

    def execute_stage(self, task: StageInput) -> StageOutput:
        task_text = render_task(task)
        transport = OllamaTransport(self.llm, self.system_prompt, task_text)
        tool_names = tuple(t.get("function", {}).get("name", "") for t in TOOL_SCHEMAS)
        # Layer 1 — Request: the contract PGS handed this worker (Worker Observability Protocol).
        self._emit("wpt_request", stage=task.stage, worker="ollama", model=self.name,
                   prompt_chars=len(task_text), num_ctx=self.llm.num_ctx, tools=list(tool_names))
        final_text, telem = run_tool_loop(
            transport, self.grounding, max_iters=self.max_iters, emit=self._emit, tool_names=tool_names)
        registers, questions, findings = parse_output("automated", final_text)
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

    # Task framing (`render_task`) and output parsing (`parse_output`) are shared, transport-
    # agnostic primitives — see `_authoring`. OllamaWorker contributes only the ollama transport.

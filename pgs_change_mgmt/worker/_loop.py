"""The shared grounded tool-loop — sovereign, worker-independent authoring orchestration.

Every worker (qwen/claude/gemini) used to re-implement this loop, so its policy — budget,
stall/nudge handling, the convergence guard, the forced-finalization output contract, telemetry —
drifted per worker (the "completed document" forced prompt was fixed in one worker and not the
others). That is intelligence living in the *worker*, which breaks worker-interchangeability: which
model authored a stage must not change how the stage is governed. So the loop lives here, ONCE, and
a worker is reduced to a `Transport` — the only thing that legitimately differs (how you say
`model_turn` to ollama vs. the Anthropic API vs. Gemini). Runtime-Dumbness, one tier up.

The loop is transport-agnostic: it speaks only in `Turn` / `ToolCall`, never a native message
shape. Each `Transport` owns its native conversation history and translates to/from these.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from ..grounding import PiError


# Worker Observability — detect-only (never act on this). Whether a model expressed tool intent as
# TEXT (rather than a native tool call) is the signal that distinguishes a worker integration gap from
# a genuine model limitation. This recognizes common textual conventions and any advertised tool name.
_TOOL_MARKERS = ("```tool", "<tool_call", "tool_call", "function_call")


def _textual_tool_hint(text: str, thinking: str, tool_names: tuple[str, ...]) -> bool:
    blob = f"{text}\n{thinking}".lower()
    if any(m in blob for m in _TOOL_MARKERS):
        return True
    return any(f"{n.lower()}(" in blob or f'"{n.lower()}"' in blob for n in tool_names)


class TransportError(RuntimeError):
    """A transport (model/API) failure. Per-worker errors subclass this so the loop catches one type."""


@dataclass
class ToolCall:
    """A tool the model asked to call; `payload` is filled by the loop with the grounding result."""
    name: str
    args: dict[str, Any]
    id: str | None = None
    payload: Any = None


@dataclass
class Turn:
    """One model turn, normalized across transports.

    `tool_calls` empty ⇒ the model is finishing. `empty` ⇒ a stalled/garbled turn to retry.
    `truncated` ⇒ the turn ended on the token cap (diagnostic only)."""
    text: str = ""
    thinking: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    truncated: bool = False
    empty: bool = False


class Transport(Protocol):
    """The only per-worker surface: drive one model turn and append to the native history.

    `model_turn` MUST append the assistant turn it produced to the transport's own history when it
    carries tool calls (so the subsequent `add_tool_results` continues a valid conversation)."""

    def model_turn(self, *, use_tools: bool) -> Turn: ...
    def add_tool_results(self, calls: list[ToolCall]) -> None: ...
    def add_user(self, text: str) -> None: ...


# The forced-finalization output contract (was duplicated + drifted across workers). A budget-forced
# turn must still emit the json `registers` block — NOT a prose "document" (the old wording let a
# model reply with a prose summary and drop the registers → empty projection → halt).
FORCED_PROMPT = (
    "You have used your full tool budget — do NOT call any more tools. "
    "Using only the evidence already gathered, emit your final result NOW. "
    "It MUST be the single fenced ```json object with the \"registers\" key "
    "(populate every required register from the evidence). That json block "
    "is the required deliverable — a prose summary WITHOUT it is rejected. "
    "Put any brief reasoning before it, then the ```json block."
)

# A mid-loop nudge when the model produced only hidden reasoning and no answer (ollama quirk).
_NUDGE = "Now write your final answer and the ```json result block."


def result_size(envelope: Any) -> int:
    """How many results a pi envelope carries (for the green/yellow tool-call anomaly flag)."""
    if not isinstance(envelope, dict):
        return 0
    res = envelope.get("result")
    if isinstance(res, list):
        return len(res)
    if isinstance(res, dict):
        return len(res)
    return 0 if res is None else 1


def run_tool_loop(
    transport: Transport,
    grounding: Any,
    *,
    max_iters: int,
    emit: Callable[..., None],
    tool_names: tuple[str, ...] = (),
) -> tuple[str, dict[str, Any]]:
    """Drive model↔grounding turns until the model stops calling tools (or the budget forces it).

    Returns (final_text, telemetry) where telemetry = {iters, tool_calls, reason} and
    reason ∈ {finished, finished_truncated, finished_forced, max_iters, empty_stall, model_error}.
    """
    final = ""
    reason = "max_iters"     # default: loop exhausted its iteration budget
    tool_calls = 0
    seen: set[str] = set()   # (name,args) signatures, for the repeat-query anomaly flag
    empty_retries = 0
    nudged = False
    errors = 0
    i = 0
    while i < max_iters:
        i += 1
        try:
            turn = transport.model_turn(use_tools=True)
        except TransportError as exc:
            errors += 1
            emit("model_error", attempt=errors, error=str(exc))
            if errors <= 2:        # transient — retry without spending an iteration
                i -= 1
                continue
            reason = "model_error"
            break

        # Layer 2 — Response: what the worker returned this turn (observational; no decision here).
        emit("wpt_response", iter=i,
             native_tool_calls=len(turn.tool_calls), parsed_tool_calls=len(turn.tool_calls),
             text_len=len(turn.text), thinking_len=len(turn.thinking),
             truncated=turn.truncated, empty=turn.empty,
             textual_tool_hint=_textual_tool_hint(turn.text, turn.thinking, tool_names))

        if turn.empty:             # a stalled/garbled turn — retry a few times, then give up
            empty_retries += 1
            if empty_retries <= 3:
                i -= 1
                continue
            reason = "empty_stall"
            break

        if not turn.tool_calls:    # the model is finishing
            if not turn.text and turn.thinking and not nudged:
                nudged = True
                transport.add_user(_NUDGE)
                continue
            final = turn.text
            reason = "finished_truncated" if turn.truncated else "finished"
            break

        for call in turn.tool_calls:
            tool_calls += 1
            sig = f"{call.name}({json.dumps(call.args, sort_keys=True)})"
            is_repeat = sig in seen
            seen.add(sig)
            t0 = time.monotonic()
            try:
                call.payload = grounding.query(call.name, **call.args)
                err = None
                n_results = result_size(call.payload)
            except (PiError, KeyError, TypeError) as exc:
                call.payload = {"error": str(exc)}
                err = str(exc)
                n_results = 0
            duration_ms = int((time.monotonic() - t0) * 1000)
            flag = "red" if err else ("yellow" if (n_results == 0 or is_repeat) else "green")
            # Layer 3 — Dispatch: the orchestrator's handling of one tool call (+ execution time).
            emit("tool_call", name=call.name, args=call.args, ok=err is None,
                 n_results=n_results, repeat=is_repeat, error=err, flag=flag, duration_ms=duration_ms)
        transport.add_tool_results(turn.tool_calls)
        # Layer 4 — Reinjection: the results are now in the history, so the model will SEE them.
        emit("wpt_reinjection", iter=i, injected=True, n_calls=len(turn.tool_calls),
             total_results=sum(result_size(c.payload) for c in turn.tool_calls))

    # Convergence guard: budget exhausted (or stalled) without a final answer. Force ONE tool-free
    # turn demanding the json registers — a discovery-heavy stage otherwise grounds forever and
    # emits nothing. The forced prompt re-asserts the OUTPUT CONTRACT (registers, not a prose doc).
    if not final:
        transport.add_user(FORCED_PROMPT)
        try:
            turn = transport.model_turn(use_tools=False)
            forced = turn.text
        except TransportError:
            forced = ""
        emit("convergence_forced", produced=bool(forced))
        if forced:
            final = forced
            reason = "finished_forced"

    # Layer 5 — Termination: the canonical reason the loop exited (observational).
    emit("wpt_termination", reason=reason, tool_calls_total=tool_calls, iters=i, final_chars=len(final))
    return final, {"iters": i, "tool_calls": tool_calls, "reason": reason}

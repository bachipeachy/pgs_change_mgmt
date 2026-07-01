"""Worker Observability Protocol — execution evidence for the Worker Protocol.

This is the fourth PGS pillar, alongside the Authoring Protocol, the Compiler, and the CSI. It is NOT
a per-model debugger: it is a permanent, model-independent record of *how any worker interacted with
the protocol* during a stage, organized around the worker lifecycle:

    Layer 1  Request      — what PGS asked the worker to do (stage, model, prompt/context size, tools)
    Layer 2  Response     — what the worker returned (native tool calls, textual hints, finish shape)
    Layer 3  Dispatch     — what the orchestrator did with each tool call (args, success, results, time)
    Layer 4  Reinjection  — whether the tool result was put back so the model could SEE it
    Layer 5  Termination  — why the loop exited (one canonical enum)

A `WorkerProtocolTrace` consumes the worker's `on_event` stream and renders two views: a model-neutral
**Worker Protocol Trace** summary (valid for any future worker) and a linear **Protocol Timeline** that
shows exactly where execution stopped. It assigns every failure to exactly one layer — it never repairs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Termination(str, Enum):
    """Canonical reasons a worker tool-loop terminates — the single vocabulary for Layer 5."""
    MODEL_FINISHED = "MODEL_FINISHED"            # model emitted a final answer after using tools
    NO_TOOL_CALLS = "NO_TOOL_CALLS"              # model finished without ever calling a tool
    MAX_ITERATIONS = "MAX_ITERATIONS"            # exhausted the tool budget
    EMPTY_STALL = "EMPTY_STALL"                  # repeated empty/garbled turns
    TRANSPORT_ERROR = "TRANSPORT_ERROR"          # the model/API transport failed
    FORCED_FINALIZATION = "FORCED_FINALIZATION"  # budget forced a tool-free final turn
    HUMAN_BOUNDARY = "HUMAN_BOUNDARY"            # guided transport: a human/Claude-Code paste, no loop


def canonical_termination(loop_reason: str, tool_calls_total: int) -> Termination:
    """Map the loop's internal reason string to the canonical Worker-Protocol termination enum."""
    if loop_reason in ("finished", "finished_truncated"):
        return Termination.MODEL_FINISHED if tool_calls_total > 0 else Termination.NO_TOOL_CALLS
    return {
        "finished_forced": Termination.FORCED_FINALIZATION,
        "max_iters": Termination.MAX_ITERATIONS,
        "empty_stall": Termination.EMPTY_STALL,
        "model_error": Termination.TRANSPORT_ERROR,
    }.get(loop_reason, Termination.MODEL_FINISHED)


def _mark(ok: bool, detail: str = "") -> str:
    return ("✓" if ok else "✗") + (f" {detail}" if detail else "")


@dataclass
class WorkerProtocolTrace:
    """Collects a worker's lifecycle events into execution evidence; renders the trace, never repairs."""

    request: dict[str, Any] | None = None
    timeline: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    termination_reason: str | None = None
    termination_tool_calls: int = 0

    # ---- collection (wire as worker on_event) -------------------------------------------------
    def collect(self, kind: str, **fields: Any) -> None:
        if kind == "wpt_request":
            self.request = dict(fields)
        if kind == "wpt_termination":
            self.termination_reason = fields.get("reason")
            self.termination_tool_calls = fields.get("tool_calls_total", 0)
        # everything observational lands on the timeline, in order
        if kind in ("wpt_response", "tool_call", "wpt_reinjection", "wpt_termination",
                    "convergence_forced", "model_error"):
            self.timeline.append((kind, dict(fields)))

    # ---- derived layer facts ------------------------------------------------------------------
    @property
    def _responses(self) -> list[dict]:
        return [f for k, f in self.timeline if k == "wpt_response"]

    @property
    def _dispatches(self) -> list[dict]:
        return [f for k, f in self.timeline if k == "tool_call"]

    @property
    def native_tool_calls(self) -> int:
        return sum(f.get("native_tool_calls", 0) for f in self._responses)

    @property
    def parsed_tool_calls(self) -> int:
        return sum(f.get("parsed_tool_calls", 0) for f in self._responses)

    @property
    def dispatched(self) -> int:
        return len(self._dispatches)

    @property
    def results_returned(self) -> int:
        return sum(f.get("n_results", 0) for f in self._dispatches)

    @property
    def reinjected(self) -> bool:
        return any(k == "wpt_reinjection" and f.get("injected") for k, f in self.timeline)

    @property
    def grounding_rounds(self) -> int:
        """How many turns made native tool calls — i.e. how many distinct rounds of grounding."""
        return sum(1 for f in self._responses if f.get("native_tool_calls", 0) > 0)

    @property
    def textual_hint_without_native(self) -> bool:
        # Only meaningful when the model made NO native tool call anywhere in the stage; a final-answer
        # turn that merely mentions a tool name must not be mistaken for an attempted textual call.
        return self.native_tool_calls == 0 and any(f.get("textual_tool_hint") for f in self._responses)

    @property
    def transport(self) -> str:
        return (self.request or {}).get("transport", "tool_loop")

    @property
    def is_interactive(self) -> bool:
        """Guided transport — a human/Claude-Code paste, not an observable in-loop tool cycle."""
        return self.transport == "interactive"

    @property
    def termination(self) -> Termination:
        if self.is_interactive:
            return Termination.HUMAN_BOUNDARY
        return canonical_termination(self.termination_reason or "finished", self.termination_tool_calls)

    # ---- ownership verdict (assign the failure to exactly one layer) --------------------------
    def ownership(self) -> tuple[str, str]:
        """(case, explanation) — the single layer that owns the outcome. Never a repair, only a verdict."""
        if self.is_interactive:
            # The observability boundary IS the human mutation boundary: grounding happened in the
            # chat session (Claude Code has pi in-session) and is not visible in a PGS tool-loop.
            # The honest verdict is not a model/worker failure — it is that observation stops here,
            # where the InteractiveIngressValidator gates the pasted response (schema + grounding_spec).
            return ("OK — HUMAN BOUNDARY (out-of-band grounding)",
                    "guided transport: the worker is a human/Claude-Code paste; in-session grounding "
                    "is not observable in a PGS tool-loop. Observation stops at the mutation boundary, "
                    "where the InteractiveIngressValidator gates the response (schema + grounding_spec).")
        if self.native_tool_calls > 0 and self.parsed_tool_calls == 0:
            return ("A — WORKER (parser)",
                    "model emitted tool calls but the worker parsed none — parser/transport drops them")
        if self.textual_hint_without_native:
            return ("A/B — WORKER (integration)",
                    "model expressed tool intent as TEXT but emitted no native tool call, and the "
                    "worker has no text-tool parser — integration gap, not a model limitation")
        if self.parsed_tool_calls > 0 and self.dispatched == 0:
            return ("B — INTEGRATION (dispatch)",
                    "tool calls parsed but never dispatched — the orchestrator dropped them")
        if self.dispatched > 0 and self.results_returned == 0:
            return ("C — PROMPT/ORCHESTRATION (query formation)",
                    "tools dispatched but every query returned 0 results — the worker asked the wrong "
                    "question (e.g. natural-language phrase vs protocol identifier); the protocol "
                    "answered truthfully")
        if self.native_tool_calls == 0:
            return ("D — MODEL LIMITATION",
                    "model never attempted a tool call (native or textual) — it answered from memory")
        # Dispatched with real results and a normal exit: the WORKER did its job. Whether the stage
        # is admissible is a projection/governance verdict, NOT a worker-observability concern.
        return ("OK — WORKER GROUNDED",
                f"{self.grounding_rounds} grounding round(s), {self.results_returned} result(s) returned; "
                "stage admissibility is a projection/governance concern, not worker behavior")

    # ---- rendering ----------------------------------------------------------------------------
    def summary(self) -> str:
        r = self.request or {}
        tools = r.get("tools") or []
        case, why = self.ownership()
        if self.is_interactive:
            # Honest interactive view: no in-loop tool cycle to report. Show that grounding tools
            # were AVAILABLE to the human, that in-loop grounding is not observable, and that the
            # boundary gate is the InteractiveIngressValidator.
            return "\n".join([
                f"Worker Protocol Trace — stage {r.get('stage', '?')} · worker=interactive · "
                f"model={r.get('model', '?')} · transport=interactive",
                f"  Request — response={r.get('prompt_chars', '?')} chars (human-pasted)",
                f"  Grounding tools available:  {_mark(bool(tools), f'({len(tools)}: ' + ', '.join(tools) + ')')} "
                f"— available in-session (e.g. Claude Code `pi`)",
                "  In-loop grounding observed: N/A (out-of-band at the human mutation boundary)",
                "  Boundary gate:              InteractiveIngressValidator (schema + grounding_spec, strict)",
                f"  Exited:                     {self.termination.value}",
                f"  OWNERSHIP:                  Case {case}",
                f"                              {why}",
            ])
        emitted = (_mark(self.native_tool_calls > 0, f"({self.native_tool_calls})")
                   if self.native_tool_calls else
                   ("✗ (textual hint only)" if self.textual_hint_without_native else "✗"))
        lines = [
            f"Worker Protocol Trace — stage {r.get('stage', '?')} · worker={r.get('worker', '?')} · "
            f"model={r.get('model', '?')}",
            f"  Request — prompt={r.get('prompt_chars', '?')} chars · num_ctx={r.get('num_ctx', '?')}",
            f"  Tools advertised:           {_mark(bool(tools), f'({len(tools)}: ' + ', '.join(tools) + ')')}",
            f"  Model emitted tool call:    {emitted}",
            f"  Worker parsed tool call:    {_mark(self.parsed_tool_calls > 0, f'({self.parsed_tool_calls})') if self.native_tool_calls else 'N/A'}",
            f"  Dispatcher invoked:         {_mark(self.dispatched > 0, f'({self.dispatched})')}",
            f"  Tool results returned:      {_mark(self.results_returned > 0, f'({self.results_returned})') if self.dispatched else 'N/A'}",
            f"  Tool results reinjected:    {_mark(self.reinjected) if self.dispatched else 'N/A'}",
            f"  Model grounded further:     {_mark(self.grounding_rounds > 1, f'({self.grounding_rounds} rounds)')}",
            f"  Loop exited:                {self.termination.value}",
            f"  OWNERSHIP:                  Case {case}",
            f"                              {why}",
        ]
        return "\n".join(lines)

    def protocol_timeline(self) -> str:
        lines = ["Protocol Timeline"]
        it = 0
        for kind, f in self.timeline:
            if kind == "wpt_response":
                it += 1
                hint = " +textual-hint" if f.get("textual_tool_hint") else ""
                shape = ("empty" if f.get("empty") else
                         f"native_calls={f.get('native_tool_calls', 0)} text={f.get('text_len', 0)}c "
                         f"think={f.get('thinking_len', 0)}c{hint}")
                lines.append(f"  iter {it}: model response → {shape}")
            elif kind == "tool_call":
                args = ", ".join(f"{k}={v!r}" for k, v in (f.get("args") or {}).items())
                outcome = (f"ERROR {f['error']}" if f.get("error")
                           else f"{f.get('n_results', 0)} results"
                                + (" (repeat)" if f.get("repeat") else ""))
                dur = f" [{f['duration_ms']}ms]" if f.get("duration_ms") is not None else ""
                lines.append(f"          ├─ dispatch {f.get('name')}({args}) → {outcome}{dur}")
            elif kind == "wpt_reinjection":
                lines.append(f"          └─ reinjected {f.get('n_calls', 0)} result(s) "
                             f"({f.get('total_results', 0)} rows) → next iteration")
            elif kind == "convergence_forced":
                lines.append(f"  forced finalization → {'produced output' if f.get('produced') else 'still empty'}")
            elif kind == "model_error":
                lines.append(f"  transport error (attempt {f.get('attempt')}): {str(f.get('error'))[:120]}")
            elif kind == "wpt_termination":
                lines.append(f"  ▸ loop exit: {self.termination.value} "
                             f"(reason={f.get('reason')}, tool_calls={f.get('tool_calls_total')})")
        return "\n".join(lines)

    def render(self) -> str:
        return self.summary() + "\n\n" + self.protocol_timeline()

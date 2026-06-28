"""Deterministic proof of the Worker Observability Protocol — no live model.

Replays synthetic worker-lifecycle event streams (the same shape the tool-loop emits) and asserts the
Worker Protocol Trace assigns each to exactly one layer. Model-independent by construction: these
verdicts must hold for any future worker. Locks the two ownership bugs the qwen S2 trace exposed —
a final-answer turn mentioning a tool name must NOT read as an attempted textual call, and a
successful grounding must NOT be mislabelled as a failure.
"""

from __future__ import annotations

import sys

from ._diagnostics import WorkerProtocolTrace, Termination


def _trace(*events) -> WorkerProtocolTrace:
    t = WorkerProtocolTrace()
    t.collect("wpt_request", stage="2", worker="ollama", model="probe",
              prompt_chars=100, num_ctx=65536, tools=["vocab_search", "validate"])
    for kind, fields in events:
        t.collect(kind, **fields)
    return t


def _resp(native, *, parsed=None, hint=False, text=0, think=0):
    return ("wpt_response", {"iter": 1, "native_tool_calls": native,
                             "parsed_tool_calls": native if parsed is None else parsed,
                             "text_len": text, "thinking_len": think, "empty": False,
                             "truncated": False, "textual_tool_hint": hint})


def _dispatch(n_results, name="vocab_search"):
    return ("tool_call", {"name": name, "args": {"term": "x"}, "ok": True,
                          "n_results": n_results, "repeat": False, "error": None,
                          "flag": "green", "duration_ms": 1})


def _reinject(n_calls, total):
    return ("wpt_reinjection", {"iter": 1, "injected": True, "n_calls": n_calls, "total_results": total})


def _term(reason, total):
    return ("wpt_termination", {"reason": reason, "tool_calls_total": total, "iters": 1, "final_chars": 0})


def main() -> int:
    cases = {
        # D — model never attempted a tool (deepseek S2): no native, no textual hint.
        "D": (_trace(_resp(0, text=3905, think=2886), _term("finished", 0)),
              Termination.NO_TOOL_CALLS),
        # A/B — model expressed tool intent only as TEXT, never natively (a worker-integration gap).
        "A/B": (_trace(_resp(0, hint=True), _term("finished", 0)),
                Termination.NO_TOOL_CALLS),
        # A — model emitted native calls but the parser recognized none (parser/transport bug).
        "A —": (_trace(_resp(3, parsed=0), _term("finished", 0)),
                Termination.NO_TOOL_CALLS),
        # B — calls parsed but never dispatched (orchestrator dropped them).
        "B —": (_trace(_resp(2, parsed=2), _term("finished", 0)),
                Termination.NO_TOOL_CALLS),
        # C — dispatched but every query returned 0 results (qwen S2: phrase vs identifier). The
        # final-answer turn mentions a tool name (hint=True) and MUST NOT be read as Case A/B.
        "C —": (_trace(_resp(9), *[_dispatch(0) for _ in range(9)], _reinject(9, 0),
                       _resp(0, hint=True, text=9680), _term("finished", 9)),
                Termination.MODEL_FINISHED),
        # OK — real grounding across two rounds with results; a normal finish. NOT a failure.
        "OK": (_trace(_resp(2), _dispatch(5), _dispatch(5), _reinject(2, 10),
                      _resp(1), _dispatch(3), _reinject(1, 3), _resp(0), _term("finished", 3)),
               Termination.MODEL_FINISHED),
    }

    for expected_case, (trace, expected_term) in cases.items():
        case, why = trace.ownership()
        assert case.startswith(expected_case), f"expected Case {expected_case!r}, got {case!r} ({why})"
        assert trace.termination == expected_term, \
            f"{expected_case}: expected {expected_term}, got {trace.termination}"
        assert "Worker Protocol Trace" in trace.summary() and "Protocol Timeline" in trace.render()
        print(f"  Case {expected_case:<4} → {case}  [{trace.termination.value}] ✓")

    # the qwen regression specifically: 9 native calls + a textual hint on the final turn → Case C, not A/B
    qwen = cases["C —"][0]
    assert qwen.native_tool_calls == 9 and not qwen.textual_hint_without_native, \
        "a model that made native calls must never be flagged textual-hint-without-native"
    assert qwen.grounding_rounds == 1, "qwen did a single grounding round"

    print("\nWORKER OBSERVABILITY PROOF OK ✓ — five lifecycle layers; ownership assigns each failure to "
          "one layer; canonical termination enum; model-independent (no live model).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

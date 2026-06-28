"""Deterministic proof of the shared worker tool-loop (worker/_loop.py) — no model, no network.

A FakeTransport scripts model turns; a FakeGrounding answers tool calls. This unit-tests the loop
policy that used to be welded into each worker (and silently drifted): natural finish, the grounded
tool→evidence→turn cycle, empty-stall, the reasoning-only nudge, and — the one that caused the S3
halt — the convergence guard emitting the json `registers` under FORCED_PROMPT. Before the
extraction this logic was untestable (welded to ollama); now it is provable in isolation.

Run:  python -m pgs_change_mgmt.worker._worker_loop_selftest
"""

from __future__ import annotations

import sys

from ._loop import FORCED_PROMPT, ToolCall, Turn, run_tool_loop


class FakeGrounding:
    def query(self, name, **args):
        return {"result": [f"{name}:ok"]}


class FakeTransport:
    """Scripts a list of Turns; records the user messages and tool-result batches it is handed."""

    def __init__(self, turns):
        self._turns = list(turns)
        self.users: list[str] = []          # add_user texts (nudge / forced prompt)
        self.tool_batches: list[list] = []  # add_tool_results batches

    def model_turn(self, *, use_tools):
        return self._turns.pop(0) if self._turns else Turn(text="")

    def add_tool_results(self, calls):
        self.tool_batches.append(calls)

    def add_user(self, text):
        self.users.append(text)


def _events():
    log: list = []
    return log, (lambda kind, **f: log.append((kind, f)))


def main() -> int:
    g = FakeGrounding()

    # 1. natural finish — text, no tools
    t = FakeTransport([Turn(text="done\n```json\n{}\n```")])
    _, emit = _events()
    final, telem = run_tool_loop(t, g, max_iters=24, emit=emit)
    assert telem["reason"] == "finished" and telem["tool_calls"] == 0 and "```json" in final, telem
    print("  natural finish ✓")

    # 2. tool call → grounding dispatched, payload attached + results appended → finish
    t = FakeTransport([
        Turn(tool_calls=[ToolCall(name="vocab_search", args={"term": "X"})]),
        Turn(text="answer\n```json\n{}\n```"),
    ])
    log, emit = _events()
    final, telem = run_tool_loop(t, g, max_iters=24, emit=emit)
    assert telem["tool_calls"] == 1 and telem["reason"] == "finished", telem
    assert t.tool_batches and t.tool_batches[0][0].payload == {"result": ["vocab_search:ok"]}
    assert any(k == "tool_call" for k, _ in log)
    print("  tool → evidence → finish ✓")

    # 3. empty-stall — 4 empty turns (3 retries don't spend budget) → empty_stall
    t = FakeTransport([Turn(empty=True)] * 4)
    _, emit = _events()
    _, telem = run_tool_loop(t, g, max_iters=24, emit=emit)
    assert telem["reason"] == "empty_stall", telem
    print("  empty-stall ✓")

    # 4. reasoning-only nudge — no text but has thinking → ONE nudge, then finish (not the forced prompt)
    t = FakeTransport([Turn(text="", thinking="x" * 50), Turn(text="final\n```json\n{}\n```")])
    _, emit = _events()
    _, telem = run_tool_loop(t, g, max_iters=24, emit=emit)
    assert telem["reason"] == "finished", telem
    assert FORCED_PROMPT not in t.users and any("final answer" in u for u in t.users), t.users
    print("  reasoning-only nudge ✓")

    # 5. convergence guard — model only ever calls tools → budget exhausted → forced turn emits json
    t = FakeTransport(
        [Turn(tool_calls=[ToolCall(name="vocab_search", args={"term": "X"})])] * 24
        + [Turn(text='forced\n```json\n{"registers":{}}\n```')]
    )
    log, emit = _events()
    final, telem = run_tool_loop(t, g, max_iters=24, emit=emit)
    assert telem["reason"] == "finished_forced" and telem["tool_calls"] == 24, telem
    assert t.users and t.users[-1] == FORCED_PROMPT, "forced turn must use the json-demanding prompt"
    assert "```json" in final and "registers" in final
    assert any(k == "convergence_forced" for k, _ in log)
    print("  convergence guard forces json registers (the S3 halt, fixed in the shared loop) ✓")

    print("\nSHARED TOOL-LOOP PROOF OK ✓ — finish / tool-cycle / empty-stall / nudge / forced-json, "
          "transport-agnostic, in one place")
    return 0


if __name__ == "__main__":
    sys.exit(main())

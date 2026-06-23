"""RunLog — the engine's append-only audit trail for one governed run.

Promoted verbatim-in-spirit from the Phase-0 `orchestrator.py`. Each run records its meta
(snapshot hash, worker, seed, started/finished) plus an append-only `events.jsonl` of every
step: worker turns, tool calls with their `pi` envelope, evaluator verdicts, renders, and the
compiler-oracle result. That is the per-step evidence→snapshot-version chain that lets an
authored artifact be attested against a snapshot version.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


def now_stamp() -> str:
    return _dt.datetime.now().strftime("%Y%m%dT%H%M%S")


class RunLog:
    """Append-only audit trail for one engine run."""

    def __init__(self, run_dir: Path, meta: dict[str, Any]):
        self.run_dir = run_dir
        run_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = run_dir / "events.jsonl"
        self.meta_path = run_dir / "meta.json"
        self.meta = meta
        self._write_meta()

    def _write_meta(self) -> None:
        self.meta_path.write_text(json.dumps(self.meta, indent=2))

    def event(self, kind: str, **fields: Any) -> None:
        rec = {"ts": _dt.datetime.now().isoformat(timespec="seconds"), "kind": kind, **fields}
        with self.events_path.open("a") as fh:
            fh.write(json.dumps(rec, default=str) + "\n")

    def finalize(self, **fields: Any) -> None:
        self.meta.update(fields)
        self._write_meta()

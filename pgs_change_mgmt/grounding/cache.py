"""CachingGroundingProvider — a `contracts.GroundingProvider` that memoizes pi queries.

A decorator over any `GroundingProvider`. Safe by construction: `pi` is read-only over an
*immutable* compiled snapshot, so an identical query returns an identical envelope for the
life of that snapshot. The cache is keyed by `(snapshot_hash, op, kwargs)` and persisted to
disk, so:
  * the same search repeated across dossier stages is served from cache (the redundancy is
    large — discovery stages re-search the same terms), and
  * because each checkpoint `--stage` run is a *separate process*, the disk cache carries hits
    across runs (an in-memory cache could not).
Recompiling the snapshot changes `snapshot_hash`, which transparently invalidates the cache.

`validate` is never cached (it is the freshness probe that yields the hash). Errors are not
cached — only successful envelopes — so a transient/ë failure is always retried.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

# default cache root lives under the gitignored engine_runs/ (run state, never source)
_DEFAULT_CACHE = Path(__file__).resolve().parents[2] / "engine_runs" / "_pi_cache"


class CachingGroundingProvider:
    """`contracts.GroundingProvider` that serves repeated pi queries from a disk cache."""

    def __init__(self, inner: Any, *, cache_dir: Path | None = None) -> None:
        self.inner = inner
        self.cache_dir = cache_dir or _DEFAULT_CACHE
        self._hash: str | None = None
        self.hits = 0
        self.misses = 0

    # expose the underlying client (e.g. for the evaluator's is_indexed oracle) if present
    @property
    def client(self):
        return getattr(self.inner, "client", None)

    def available_ops(self):
        return getattr(self.inner, "available_ops", lambda: ())()

    def _snapshot_hash(self) -> str:
        if self._hash is None:
            env = self.inner.query("validate")
            self._hash = str(env.get("result", {}).get("snapshot_hash", "nohash"))
        return self._hash

    @staticmethod
    def _key(op: str, kwargs: dict[str, Any]) -> str:
        raw = op + "|" + json.dumps(kwargs, sort_keys=True, default=str)
        return hashlib.sha1(raw.encode()).hexdigest()[:16]

    def query(self, op: str, /, **kwargs: Any) -> Mapping[str, Any]:
        if op == "validate":
            return self.inner.query(op, **kwargs)   # freshness probe — never cached
        path = self.cache_dir / self._snapshot_hash() / f"{op}_{self._key(op, kwargs)}.json"
        if path.exists():
            try:
                env = json.loads(path.read_text())
                self.hits += 1
                return env
            except json.JSONDecodeError:
                pass  # corrupt entry → fall through and refetch
        env = self.inner.query(op, **kwargs)        # may raise (e.g. PiError) — uncached
        self.misses += 1
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(env))
        return env

    @property
    def stats(self) -> str:
        total = self.hits + self.misses
        rate = (self.hits / total * 100) if total else 0.0
        return f"pi cache: {self.hits} hits / {total} queries ({rate:.0f}% hit)"

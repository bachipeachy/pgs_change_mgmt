"""Minimal ollama chat client — stdlib only, tool-calling capable.

Talks to the local ollama daemon's REST API (``/api/chat``). No third-party SDK,
so the change_agent stays dependency-free and the workspace venv is untouched.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any


class OllamaError(RuntimeError):
    pass


@dataclass
class OllamaClient:
    """Thin wrapper over ``POST /api/chat`` (non-streaming).

    Parameters
    ----------
    model:
        ollama model tag, e.g. ``qwen3.5:latest``.
    host:
        Base URL of the ollama daemon.
    temperature:
        Sampling temperature. Default 0 for the most reproducible orchestration
        we can get from a non-deterministic drafter (determinism is enforced
        downstream by pi/compiler, not here).
    num_ctx:
        Context window in tokens. CRITICAL: ollama defaults this to ~4096
        regardless of the model's real capacity, and silently truncates longer
        prompts *from the front* — which drops the template/seed and makes the
        model claim it received no instructions. Authoring prompts (template +
        seed + prior stages) are large, so default this high.
    timeout:
        Per-request timeout (seconds). Tool-calling turns can be slow.
    """

    model: str = "qwen3.5:latest"
    host: str = field(default_factory=lambda: os.environ.get("OLLAMA_HOST", "http://localhost:11434"))
    temperature: float = 0.0
    # Later dossier stages accumulate all prior stage outputs + a large template, so
    # both the context window and the per-call timeout must scale. qwen3.5 supports far
    # more, but 65536 tokens covers the full 8-stage cumulative prompt with headroom;
    # generation of a large stage on a local 9.7B model can take many minutes.
    num_ctx: int = 65536
    timeout: float = 900.0

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        """Send a chat turn; return the assistant ``message`` dict.

        The returned message may contain ``content`` and/or ``tool_calls``.
        """
        body: dict[str, Any] = {
            "model": self.model,
            "stream": False,
            "messages": messages,
            "options": {"temperature": self.temperature, "num_ctx": self.num_ctx},
        }
        if tools:
            body["tools"] = tools
        req = urllib.request.Request(
            f"{self.host}/api/chat",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                payload = json.load(resp)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            # daemon down, connection refused, or a socket-read TIMEOUT (raises a bare
            # TimeoutError that is NOT a URLError) — wrap them all so the worker can handle
            # a slow/hung model gracefully instead of crashing the run.
            raise OllamaError(f"ollama request failed: {exc}") from exc
        if "message" not in payload:
            raise OllamaError(f"unexpected ollama response: {payload!r}")
        return payload["message"]

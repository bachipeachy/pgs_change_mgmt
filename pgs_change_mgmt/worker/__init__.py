"""worker — replaceable workers conforming to `contracts.Worker`.

Two workers today: `QwenWorker` (a local qwen via ollama) and `ClaudeWorker` (Claude via the
Anthropic API). A worker knows only how to execute a bounded stage task — it must never know the
compiler, the runtime, governance internals, or storage, and never emits machine syntax.
`ClaudeWorker` is a drop-in twin of `QwenWorker` for A/B (same contract, same loop, same
telemetry — only the model and transport differ); it is an addition, not a refactor.

`OllamaClient` (the qwen transport, with `num_ctx` pinned) is re-exported for callers that
drive the model directly.
"""

from .qwen import QwenWorker, PINNED_NUM_CTX, SYSTEM_PROMPT
from .ollama_client import OllamaClient, OllamaError
from .claude import ClaudeWorker, ClaudeError, DEFAULT_MODEL as CLAUDE_DEFAULT_MODEL

__all__ = [
    "QwenWorker",
    "PINNED_NUM_CTX",
    "SYSTEM_PROMPT",
    "OllamaClient",
    "OllamaError",
    "ClaudeWorker",
    "ClaudeError",
    "CLAUDE_DEFAULT_MODEL",
]

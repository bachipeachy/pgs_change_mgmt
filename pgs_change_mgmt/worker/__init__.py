"""worker — replaceable workers conforming to `contracts.Worker`.

Three workers today: `OllamaWorker` (any local model via the ollama daemon — qwen, deepseek, llama,
…; named for its transport because it is genuinely multi-model), `ClaudeWorker` (Claude via the
Anthropic API), and `GeminiWorker` (via the Google API) — the single-family API workers keep their
brand name. A worker knows only how to execute a bounded stage task — it must never know the
compiler, the runtime, governance internals, or storage, and never emits machine syntax.
`ClaudeWorker`/`GeminiWorker` are drop-in twins of `OllamaWorker` for A/B (same contract, same loop,
same telemetry — only the model and transport differ).

`OllamaClient` (the ollama transport, with `num_ctx` pinned) is re-exported for callers that drive
the model directly (e.g. the construction builder).
"""

from ._authoring import SYSTEM_PROMPT, render_task, parse_output
from .ollama_worker import OllamaWorker, PINNED_NUM_CTX
from .ollama_client import OllamaClient, OllamaError
from .claude import ClaudeWorker, ClaudeError, DEFAULT_MODEL as CLAUDE_DEFAULT_MODEL
from .gemini import GeminiWorker, GeminiError, DEFAULT_MODEL as GEMINI_DEFAULT_MODEL
from .interactive import InteractiveWorker
from .interactive_ingress import InteractiveIngressValidator, IngressVerdict

__all__ = [
    "OllamaWorker",
    "PINNED_NUM_CTX",
    "SYSTEM_PROMPT",
    "render_task",
    "parse_output",
    "OllamaClient",
    "OllamaError",
    "ClaudeWorker",
    "ClaudeError",
    "CLAUDE_DEFAULT_MODEL",
    "GeminiWorker",
    "GeminiError",
    "GEMINI_DEFAULT_MODEL",
    "InteractiveWorker",
    "InteractiveIngressValidator",
    "IngressVerdict",
]

"""GeminiWorker — a third `contracts.Worker`, backed by Google Gemini via the Generative
Language API.

Same purpose and discipline as `ClaudeWorker`: a true drop-in twin of `OllamaWorker` for a
controlled capability A/B on the dossier pipeline. It reuses qwen's task framing, system prompt,
and output parsing verbatim (`SYSTEM_PROMPT`, `_render_task`, `_parse_output`) and the shared
`_loop.run_tool_loop`; only the transport (Gemini `generateContent`) and the model differ.

Transport is raw HTTP via stdlib `urllib` (the workspace forbids `pip install`; no SDK is
present). The API key is read from `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) at run time. Gemini's
function-calling protocol differs: a turn carries `functionCall` parts (no distinct stop reason —
tool use is detected by their presence), the model turn is echoed back verbatim (preserving
`thoughtSignature` for thinking continuity), and each result is a `functionResponse` part in a
`role: "user"` content.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Callable

from ..contracts import StageInput, StageOutput
from ..contracts import GroundingProvider
from ..grounding import TOOL_SCHEMAS
from ._loop import ToolCall, Turn, TransportError, run_tool_loop
from .ollama_worker import OllamaWorker, SYSTEM_PROMPT

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = "gemini-flash-latest"

# Translate the openai/ollama function schemas the grounding layer publishes into the Gemini
# shape: a single tools entry with `functionDeclarations: [{name, description, parameters}]`.
GEMINI_TOOLS = [{
    "functionDeclarations": [
        {
            "name": s["function"]["name"],
            "description": s["function"]["description"],
            "parameters": s["function"]["parameters"],
        }
        for s in TOOL_SCHEMAS
    ]
}]


class GeminiError(RuntimeError):
    """Gemini transport failure (non-retryable, or retries exhausted)."""


class GeminiTransport:
    """`_loop.Transport` for Gemini over generateContent — owns the native `contents` history.

    Normalizes a generateContent turn (`functionCall` / `text` parts, `finishReason`) into a
    `Turn`, and translates the loop's `ToolCall` results back into `functionResponse` parts. The
    model turn is echoed back verbatim (preserving `thoughtSignature`) for thinking continuity.
    """

    def __init__(self, chat: "Callable[..., dict[str, Any]]",
                 parts: "Callable[[dict[str, Any]], tuple]", task_text: str) -> None:
        self._chat = chat       # GeminiWorker._chat
        self._parts = parts     # GeminiWorker._parts
        self.contents: list[dict[str, Any]] = [{"role": "user", "parts": [{"text": task_text}]}]

    def model_turn(self, *, use_tools: bool) -> Turn:
        try:
            resp = self._chat(self.contents, use_tools=use_tools)
        except GeminiError as exc:
            raise TransportError(str(exc)) from exc
        parts, model_content, finish = self._parts(resp)
        fcalls = [p["functionCall"] for p in parts if "functionCall" in p]
        text = "".join(p.get("text", "") for p in parts if "text" in p).strip()
        if fcalls:
            self.contents.append(model_content)   # echo the model turn verbatim (thoughtSignature)
        tool_calls = [ToolCall(name=fc.get("name", ""), args=fc.get("args") or {}) for fc in fcalls]
        return Turn(text=text, tool_calls=tool_calls, truncated=(finish == "MAX_TOKENS"))

    def add_tool_results(self, calls: list[ToolCall]) -> None:
        responses = []
        for call in calls:
            # Gemini requires the functionResponse `response` to be a JSON object.
            resp_obj = call.payload if isinstance(call.payload, dict) else {"result": call.payload}
            responses.append({"functionResponse": {"name": call.name, "response": resp_obj}})
        self.contents.append({"role": "user", "parts": responses})

    def add_user(self, text: str) -> None:
        self.contents.append({"role": "user", "parts": [{"text": text}]})


class GeminiWorker:
    """`contracts.Worker` backed by Gemini over the Generative Language API, grounded by PI.

    A drop-in twin of `OllamaWorker`/`ClaudeWorker`: identical contract, identical (shared) loop,
    identical telemetry — only the model and transport change.
    """

    def __init__(
        self,
        grounding: GroundingProvider,
        *,
        model: str = DEFAULT_MODEL,
        system_prompt: str = SYSTEM_PROMPT,
        max_iters: int = 24,
        on_event: "Callable[..., None] | None" = None,
        api_key: str | None = None,
        # The S3 register payload is large and Gemini "thinking" tokens count toward the output
        # budget; keep this generous so a heavy stage's final register block is never truncated.
        max_output_tokens: int = 32768,
        timeout: float = 600.0,
    ) -> None:
        self.grounding = grounding
        self.name = model
        self.model = model
        self.system_prompt = system_prompt
        self.max_iters = max_iters
        self.on_event = on_event
        self.max_output_tokens = max_output_tokens
        self.timeout = timeout
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise GeminiError(
                "GEMINI_API_KEY is not set — the Gemini worker needs it at run time. "
                "Export it (or run: ! export GEMINI_API_KEY=...) before invoking."
            )
        # Auth is credential-type-dependent: an AI Studio API key ('AIza...') goes in
        # `x-goog-api-key`; an OAuth2/ephemeral access token (e.g. 'AQ....') goes in an
        # `Authorization: Bearer` header. Try the prefix-appropriate one first; fall back on 401.
        self._auth: dict[str, str] | None = None

    def _emit(self, kind: str, **fields: Any) -> None:
        if self.on_event is not None:
            self.on_event(kind, **fields)

    # ---- the bounded stage task (shared loop; only the transport is Gemini's) ------

    def execute_stage(self, task: StageInput) -> StageOutput:
        transport = GeminiTransport(self._chat, self._parts, OllamaWorker._render_task(task))
        final_text, telem = run_tool_loop(
            transport, self.grounding, max_iters=self.max_iters, emit=self._emit)
        registers, questions, findings = OllamaWorker._parse_output(final_text)
        telem_line = (f"[tool-loop: iters={telem['iters']}/{self.max_iters} "
                      f"tool_calls={telem['tool_calls']} reason={telem['reason']} "
                      f"final_chars={len(final_text)}]")
        return StageOutput(
            stage=task.stage,
            registers=registers,
            questions=questions,
            findings=(telem_line, *findings),
        )

    # ---- transport -------------------------------------------------------

    def _auth_candidates(self) -> list[dict[str, str]]:
        """Auth headers to try, prefix-appropriate first. 'AIza...' is an API key (x-goog-api-key);
        anything else is treated as an OAuth2/ephemeral access token (Authorization: Bearer)."""
        apikey = {"x-goog-api-key": self.api_key}
        bearer = {"authorization": f"Bearer {self.api_key}"}
        return [apikey, bearer] if self.api_key.startswith("AIza") else [bearer, apikey]

    def _post(self, body: dict[str, Any]) -> dict[str, Any]:
        """One generateContent call (raw HTTP). Tries each auth variant (remembering the one that
        works), with retry on 429/5xx and a 401 fallback to the alternate credential type."""
        url = GEMINI_URL.format(model=self.model)
        data = json.dumps(body, default=str).encode()
        candidates = [self._auth] if self._auth else self._auth_candidates()
        last_exc: Exception | None = None
        for auth in candidates:
            headers = {"content-type": "application/json", **auth}
            for attempt in range(4):
                req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                try:
                    with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                        self._auth = auth          # remember the credential type that authenticated
                        return json.loads(resp.read())
                except urllib.error.HTTPError as exc:
                    detail = exc.read().decode(errors="replace")
                    if exc.code == 401:
                        last_exc = GeminiError(f"HTTP 401: {detail[:300]}")
                        self._auth = None
                        break                      # wrong credential type → try the next variant
                    if exc.code in (429, 500, 502, 503) and attempt < 3:
                        last_exc = GeminiError(f"HTTP {exc.code}: {detail[:300]}")
                        time.sleep(min(2 ** attempt + 0.5, 20))
                        continue
                    raise GeminiError(f"HTTP {exc.code}: {detail[:500]}") from exc
                except (urllib.error.URLError, TimeoutError) as exc:
                    last_exc = GeminiError(f"transport error: {exc}")
                    if attempt < 3:
                        time.sleep(min(2 ** attempt + 0.5, 20))
                        continue
                    break
        raise last_exc or GeminiError("request failed")

    def _chat(self, contents: list[dict[str, Any]], *, use_tools: bool) -> dict[str, Any]:
        body: dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": self.system_prompt}]},
            "contents": contents,
            "generationConfig": {"maxOutputTokens": self.max_output_tokens},
        }
        if use_tools:
            body["tools"] = GEMINI_TOOLS
            body["toolConfig"] = {"functionCallingConfig": {"mode": "AUTO"}}
        else:
            # forced final turn — disable function calling (mode NONE)
            body["toolConfig"] = {"functionCallingConfig": {"mode": "NONE"}}
        return self._post(body)

    @staticmethod
    def _parts(resp: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any] | None, str]:
        """Extract (parts, model_content, finishReason) from a generateContent response."""
        cands = resp.get("candidates") or []
        if not cands:
            return [], None, resp.get("promptFeedback", {}).get("blockReason", "no_candidates")
        cand = cands[0]
        content = cand.get("content") or {}
        return content.get("parts") or [], content, cand.get("finishReason", "")

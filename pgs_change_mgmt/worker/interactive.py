"""InteractiveWorker — the Guided Authoring transport: a human (or Claude Code) is the worker.

The third execution mode of the trifecta. It is a `contracts.Worker` like any other — same
`execute_stage(StageInput) -> StageOutput` seam — but its *transport* is a human pasting a model's
reply into `stage_<N>/response.md`. It calls no model and builds nothing: it reads the recorded
response, parses it through the SHARED `parse_output("interactive", …)` core (tolerating copy-paste
artifacts), stamps the **Human Mutation Boundary** provenance (plan §4a P5), and returns the
`StageOutput`. The engine then renders, runs the structural oracle, persists the handoff, and
computes the figure of merit — IDENTICAL to the automated path. Only the transport differs.

Grounding for this worker happens out-of-band, in the human's chat session (Claude Code has `pi`
in-session), so PGS cannot observe it in a tool-loop. The worker therefore emits only a Layer-1
`wpt_request` (transport=`interactive`) into the Worker Protocol Trace — an honest record that the
work crossed the human boundary, not a fabricated in-loop grounding trace.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from ..contracts import StageInput, StageOutput
from ._authoring import parse_output


class InteractiveWorker:
    """A `contracts.Worker` whose transport is a human-pasted `response.md` in a Stage Package."""

    def __init__(self, package_dir: str | Path, *, model_label: str = "unknown",
                 on_event: "Callable[..., None] | None" = None) -> None:
        self.package_dir = Path(package_dir)
        self.model_label = model_label
        self.on_event = on_event
        self.name = f"interactive:{model_label}"
        manifest_path = self.package_dir / "manifest.json"
        self.manifest: dict[str, Any] = (
            json.loads(manifest_path.read_text()) if manifest_path.exists() else {})

    def _emit(self, kind: str, **fields: Any) -> None:
        if self.on_event is not None:
            self.on_event(kind, **fields)

    def execute_stage(self, task: StageInput) -> StageOutput:
        pkg_stage = self.manifest.get("stage")
        if pkg_stage is not None and str(pkg_stage) != str(task.stage):
            raise ValueError(f"package is for stage {pkg_stage!r} but engine requested stage "
                             f"{task.stage!r} — point the worker at the matching stage_<N>/ package")
        resp = self.package_dir / "response.md"
        if not resp.exists():
            raise FileNotFoundError(
                f"no response.md in {self.package_dir} — export the package, paste the model's "
                f"reply into response.md, then import. (Guided Mode builds nothing on its own.)")
        raw = resp.read_text()

        prompt_hash = self.manifest.get("prompt_hash")
        allowed_tools = self._allowed_tools()
        # Layer 1 — Request: an honest record that the work crossed the human boundary. transport=
        # interactive; the grounding tools were AVAILABLE to the human (Claude Code has pi in-session)
        # but their use is out-of-band and not observed here.
        self._emit("wpt_request", stage=task.stage, worker="interactive", model=self.model_label,
                   transport="interactive", prompt_chars=len(raw), num_ctx=None, tools=allowed_tools)

        registers, questions, findings = parse_output("interactive", raw)
        telem = (f"[interactive: response_chars={len(raw)} registers={len(registers)} "
                 f"prompt_hash={prompt_hash}]")
        provenance = {
            "origin": "human_guided",
            "mutation_boundary": True,
            "validated_by": "ingress_validator",
            "prompt_hash": prompt_hash,
            "model_label": self.model_label,
        }
        return StageOutput(
            stage=task.stage,
            registers=registers,
            questions=questions,
            findings=(telem, *findings),
            provenance=provenance,
        )

    def _allowed_tools(self) -> list[str]:
        bundle = self.package_dir / "prompt_bundle.json"
        if bundle.exists():
            return list(json.loads(bundle.read_text()).get("allowed_tools", ()))
        return []

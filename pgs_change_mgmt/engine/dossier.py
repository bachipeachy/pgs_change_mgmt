"""DossierEngine — the staged S1→S7 dossier-authoring pipeline (Phase 5, dossier tier).

The dossier pipeline ends at S7 (the Authoring Mandate). S8 (Authoring Manifest) is a
POST-authoring artifact produced by the authoring tier after the .md artifacts are created from
the S7 mandate, compiled, and tested — it is invokable here (`--stage 8`, renders the baseline)
but is not part of the default run.

Where `ChangeEngine` (Phase 4A) authors machine artifacts judged by the compiler, this drives
the *dossier* tier: a worker authors each SDLC stage document (change request → … → authoring
manifest) for a CR, and the bounded `gov_projection` is the handoff between stages — only the
fields a downstream stage *declares* it consumes cross the seam (not the full prior document).
That bounded handoff is the drift-killer the Phase-0 experiment confirmed.

Dossier documents do not compile, so there is no compiler oracle. The per-stage **figure of
merit** is instead objective and structural:
  1. lossless handoff — the stage emitted every gov_projection field its schema declares;
  2. identity — `IdentityEvaluator` over the projection (zero fabrications; new-subdomain
     FQDNs are legitimate class-D proposals, not hallucinations);
  3. template coverage — the document filled the stage template's sections.

One `Worker.execute_stage` call per stage: the worker writes the document as its content and a
trailing ```json `registers` block (the handoff). We validate this one-call shape on S1–S2
first; if register quality is weak we can split into author-then-extract without touching the
seams.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..contracts import (
    GovProjection, StageInput, Worker, GroundingProvider, Evaluator,
    fields_emitted_by, fields_consumed_by,
)
from ..evaluator import IdentityEvaluator
from ..renderer.dossier_stage import is_structured_template, DossierStageRenderer, EVIDENCE_COLUMNS
from .run_log import RunLog, now_stamp

PKG_REPO = Path(__file__).resolve().parents[2]
CM = PKG_REPO / "change_mgmt"
TEMPLATES = CM / "templates"
AGENT_CONTEXT = TEMPLATES / "0_agent_context_template_v0.md"

# stage → template/output basename (mirrors the Phase-0 dossier_chain mapping)
STAGE_BASENAME: dict[str, str] = {
    "1": "1_change_request", "2": "2_domain_model", "3": "3_analysis_loop",
    "4": "4_business_model", "5": "5_business_intent", "6": "6_governance_intent",
    "6b": "6b_design_intent", "7": "7_authoring_mandate", "8": "8_authoring_manifest",
}
# The dossier pipeline ends at S7 (the Authoring Mandate) — the last artifact derivable from the
# dossier alone. S8 (Authoring Manifest) is a POST-authoring artifact: it records as-built reality
# (deviations, as-designed-vs-as-built, conformance, dividend metrics) that exists only AFTER the
# .md artifacts are authored from the S7 mandate, compiled, and tested. S8 is produced by the
# authoring tier — runnable here via `--stage 8` (which renders the pre-authoring baseline), but it
# is NOT part of the default dossier run. STAGE_BASENAME still maps "8" so the stage is invokable.
STAGE_ORDER: tuple[str, ...] = ("1", "2", "3", "4", "5", "6", "6b", "7")

# S2 anchors on the imperative objective, not the appended template prose. A stage whose
# schema declares a `belief_verification` register is a *verification* stage, not a discovery
# stage: the belief ledger is the spine that bounds every other register. This imperative is
# injected ahead of the register list so the worker reads the bound as a directive, not advice.
VERIFICATION_SPINE: str = (
    "THIS IS A VERIFICATION STAGE, NOT A DISCOVERY STAGE. The semantic model (vocabulary, "
    "lifecycle states, events, invariants, authority) was already established by Stage 1 and "
    "handed to you. You do NOT re-derive the domain and you do NOT search the domain at large.\n"
    "THE SPINE — `belief_verification`. Fill it FIRST: one row per Stage-1 System Belief, each "
    "with a Result ∈ {VERIFIED, NOT_FOUND, INSUFFICIENT_EVIDENCE}. This register is the STOP "
    "condition — discovery is COMPLETE the moment every System Belief has a Result.\n"
    "EVERY OTHER REGISTER IS A PROJECTION OF THE VERIFIED BELIEFS — bounded by the System Beliefs "
    "and Requested Outcomes you were given. An entity, process, gap, observation, concern, or "
    "baseline artifact may appear ONLY because verifying a belief (or serving a requested "
    "outcome) surfaced it. A row that traces to no belief and no requested outcome does not "
    "belong in this stage — do not invent it.\n"
    "ABSENCE IS A FINAL ANSWER. A grounding search that returns 0 results (e.g. `GENESIS → 0`) "
    "RESOLVES that belief as NOT_FOUND — record it and move on. Never re-search variants of a "
    "term that already returned nothing; a 0-result is the answer, not a new search frontier."
)

GOVERNANCE_RULES: tuple[str, ...] = (
    "You have NO protocol knowledge of your own — confirm every EXISTING artifact FQDN "
    "(codes, who-references-what, workflow routing, snapshot state) via a grounding tool call.",
    "Mark every NEW artifact you propose as NEW/provisional — do not present it as existing.",
    "Follow the stage template exactly: same sections, headings, terminology.",
    "End with a single ```json block whose `registers` holds exactly the listed handoff fields.",
)

# ---- attention coloring (R/Y/G flags + star rating) ----------------------------------------
_ANSI = {"red": "\033[31m", "yellow": "\033[33m", "green": "\033[32m",
         "dim": "\033[2m", "bold": "\033[1m", "reset": "\033[0m"}
_DOT = {"red": "🔴", "yellow": "🟡", "green": "🟢"}


def color(flag: str, text: str) -> str:
    return f"{_ANSI.get(flag, '')}{text}{_ANSI['reset']}"


def stars(n: int) -> str:
    return "★" * n + "☆" * (5 - n)


def rate_stage(sr: "StageResult") -> int:
    """Deterministic 0–5 figure-of-merit rating (5 best, 0 = abandoned).

    −2 fabricated FQDN · −1 missing handoff field(s) · −1 didn't converge naturally
    (forced/max_iters/stall) · −1 template coverage < 0.5. No document → 0 (abandon)."""
    if sr.doc_path is None:
        return 0
    score = 5
    if sr.identity.get("E_FABRICATION", 0) > 0:
        score -= 2
    if sr.missing:
        score -= 1
    if "reason=finished " not in sr.telemetry:   # "finished_forced"/"max_iters"/"empty_stall"
        score -= 1
    # coverage penalty: structured stages set coverage to a binary oracle verdict (1.0 ok / 0.0
    # dirty), so 0.5 is the right gate. Free-form stages (S5/S6) use heading-fraction, which run-
    # to-run variance proved too noisy to gate a rating on (a clean 5/5-handoff doc can land at
    # 21% by phrasing headings differently) — so coverage is informational only for them. The
    # governance-meaningful criteria for a free-form stage are already scored above: a complete
    # lossless handoff (no `missing`) and zero fabrication.
    if sr.structured and sr.coverage < 0.5:
        score -= 1
    return max(0, min(5, score))


@dataclass(frozen=True)
class DossierSeedConfig:
    """A dossier run: which CR, from which seed, written where."""

    name: str
    domain: str
    subdomain: str
    seed_path: Path
    output_dir: Path
    templates_dir: Path = TEMPLATES
    agent_context: Path = AGENT_CONTEXT


DOSSIER_SEEDS: dict[str, DossierSeedConfig] = {
    "blockchain_chain": DossierSeedConfig(
        name="blockchain_chain", domain="blockchain", subdomain="chain",
        # The frozen human elicitation — the Stage-1 INPUT artifact (the conversation that produces
        # it is deferred). Named per the canonical `1_input_elicitation_*` convention and colocated
        # with the dossier (the engine writes `1_change_request_*`, so they coexist, not collide).
        seed_path=CM / "dossiers" / "blockchain" / "chain" / "1_input_elicitation_blockchain_chain_v0.md",
        output_dir=CM / "dossiers" / "blockchain" / "chain",
    ),
}


@dataclass
class StageResult:
    stage: str
    doc_path: Path | None = None
    emitted: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)   # lossless-handoff failures
    extra: list[str] = field(default_factory=list)      # undeclared handoff fields
    identity: dict[str, int] = field(default_factory=dict)  # A–E counts
    coverage: float = 0.0                                # template section coverage [0,1]
    telemetry: str = ""                                  # worker tool-loop telemetry
    structured: bool = False                             # rendered via DossierStageRenderer
    oracle_issues: list[str] = field(default_factory=list)  # structural-oracle findings
    # split coverage (structured stages only): the S4-bound emit registers vs the doc-only
    # audit registers. Strict/binary per partition — separates governance integrity from
    # audit-trail completeness. None when not applicable.
    governed_coverage: float | None = None
    audit_coverage: float | None = None

    @property
    def ok(self) -> bool:
        if self.structured:
            return self.doc_path is not None and not self.oracle_issues \
                and self.identity.get("E_FABRICATION", 0) == 0
        return (self.doc_path is not None and not self.missing
                and self.identity.get("E_FABRICATION", 0) == 0)

    @property
    def rating(self) -> int:
        return rate_stage(self)


@dataclass
class DossierResult:
    seed: str
    run_dir: Path
    stages: list[StageResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return bool(self.stages) and all(s.ok for s in self.stages)


class DossierEngine:
    """Drives the staged S1→S8 dossier authoring across worker + grounding + evaluator."""

    def __init__(self, worker: Worker, grounding: GroundingProvider, *,
                 evaluator: Evaluator | None = None, runs_root: Path | None = None,
                 verbose: bool = False) -> None:
        self.worker = worker
        self.grounding = grounding
        self.evaluator = evaluator if evaluator is not None else IdentityEvaluator()
        self.runs_root = runs_root or (PKG_REPO / "engine_runs")
        self.verbose = verbose

    def run(self, seed: str | DossierSeedConfig, *,
            stages: tuple[str, ...] | None = None) -> DossierResult:
        cfg = seed if isinstance(seed, DossierSeedConfig) else _resolve_seed(seed)
        order = stages or STAGE_ORDER

        gate = self.grounding.query("validate")
        snapshot_hash = gate.get("result", {}).get("snapshot_hash")
        run_dir = self.runs_root / f"dossier_{cfg.name}_{now_stamp()}"
        log = RunLog(run_dir, {
            "engine": "DossierEngine", "phase": "5_dossier", "seed": cfg.name,
            "subdomain": f"{cfg.domain}/{cfg.subdomain}", "stages": list(order),
            "worker": getattr(self.worker, "name", "?"), "snapshot_hash": snapshot_hash,
        })
        cfg.output_dir.mkdir(parents=True, exist_ok=True)

        result = DossierResult(seed=cfg.name, run_dir=run_dir)
        for stage in order:
            sr = self._run_stage(cfg, stage, log)          # handoff persisted to disk per stage
            result.stages.append(sr)
        log.finalize(ok=result.ok,
                     stages_ok=sum(s.ok for s in result.stages), n_stages=len(result.stages))
        return result

    # ---- one stage -------------------------------------------------------

    def _run_stage(self, cfg: DossierSeedConfig, stage: str, log: RunLog) -> StageResult:
        template = (cfg.templates_dir / f"{STAGE_BASENAME[stage]}_template_v0.md").read_text()
        task = self._stage_input(cfg, stage, template)
        bounded = sorted(task.input_projection.values)
        log.event("stage_input", stage=stage, objective_chars=len(task.objective),
                  bounded_fields=bounded)
        if self.verbose:
            print(color("bold", f"\n┌─ Stage {stage} ({STAGE_BASENAME[stage]}) ─ "
                                f"bounded input: {bounded or '(seed only)'}"))

        output = self.worker.execute_stage(task)
        sr = StageResult(stage=stage, structured=is_structured_template(template))
        sr.telemetry = output.findings[0] if output.findings else ""
        doc_path = cfg.output_dir / f"{STAGE_BASENAME[stage]}_{cfg.domain}_{cfg.subdomain}_v0.md"

        if sr.structured:
            # structured intent → deterministic renderer + structural oracle (no free-form doc).
            # The register schema is compiled from the template (single source of truth).
            data = {k: v for k, v in dict(output.registers).items() if isinstance(v, list)}
            renderer = DossierStageRenderer(template)
            oracle = renderer.check(data)
            # Stage-6b binding-FQDN integrity: cross-register checks the per-register oracle cannot
            # express (referenced⇒declared, collision, count reconciliation, near-duplicate spelling).
            # Issues mark the offending register dirty → governed coverage drops → no 5/5 on a typo.
            if stage == "6b":
                from ..evaluator.design_intent_oracle import check_design_intent
                for rid, msg in check_design_intent(data, self.grounding):
                    oracle.issues.append(msg)
                    oracle.dirty.add(rid)
                oracle.ok = not oracle.issues
            elif stage == "7":
                # cross-STAGE: every mandate code must trace to a Stage 6b register (no typo
                # re-introduction), steps contiguous, counts reconcile with 6b.
                from ..evaluator.design_intent_oracle import check_authoring_mandate
                for rid, msg in check_authoring_mandate(data, dict(task.input_projection.values)):
                    oracle.issues.append(msg)
                    oracle.dirty.add(rid)
                oracle.ok = not oracle.issues
            doc = (renderer.render(data)
                   .replace("[domain]", cfg.domain).replace("[subdomain]", cfg.subdomain))
            # handoff = the registers that are declared gov_projection emit-fields for this stage
            emit = {f.field for f in fields_emitted_by(stage)}
            proj = GovProjection(stage=stage, values={k: v for k, v in data.items() if k in emit})
            sr.oracle_issues = oracle.issues
            sr.missing = oracle.empty_required
            sr.coverage = 1.0 if oracle.ok else 0.0
            # split coverage (strict/binary per partition): the S4-bound emit registers vs the
            # doc-only audit registers — separates governance integrity from audit completeness.
            audit_ids = set(renderer.registers) - emit
            sr.governed_coverage = 0.0 if (oracle.dirty & emit) else 1.0
            sr.audit_coverage = (0.0 if (oracle.dirty & audit_ids) else 1.0) if audit_ids else None
        else:
            proj = GovProjection(stage=stage, values=dict(output.registers))
            doc = self._document(output)
            sr.missing = proj.missing_fields()
            sr.extra = proj.extra_fields()
            sr.coverage = self._template_coverage(doc, template)

        doc_path.write_text(doc or "(no document produced)")
        sr.doc_path = doc_path if doc.strip() else None
        self._save_handoff(cfg, stage, proj)   # standalone-reviewable bounded handoff

        sr.emitted = sorted(proj.values)
        verdict = self.evaluator.evaluate(proj, stage=stage)
        sr.identity = dict(verdict.detail.get("counts", {}))

        log.event("stage_figure_of_merit", stage=stage, doc=str(doc_path), structured=sr.structured,
                  doc_chars=len(doc), emitted=sr.emitted, missing=sr.missing,
                  oracle_issues=sr.oracle_issues, identity=sr.identity,
                  coverage=round(sr.coverage, 2), governed_coverage=sr.governed_coverage,
                  audit_coverage=sr.audit_coverage, telemetry=sr.telemetry, rating=sr.rating, ok=sr.ok)
        if not sr.doc_path:
            (log.run_dir / f"{stage}_raw_output.txt").write_text(
                "\n\n".join(output.findings) or "(empty)")
        if self.verbose:
            self._print_footer(sr, doc_path)
        return sr

    def _print_footer(self, sr: StageResult, doc_path: Path) -> None:
        flag = "green" if sr.rating >= 4 else ("yellow" if sr.rating >= 2 else "red")
        notes = []
        if sr.missing:
            notes.append(color("red", f"missing {sr.missing}"))
        if sr.identity.get("E_FABRICATION", 0):
            notes.append(color("red", f"{sr.identity['E_FABRICATION']} FABRICATION"))
        a = sr.identity.get("A_EXACT", 0)
        notes.append(f"{a} grounded")
        if sr.structured and sr.governed_coverage is not None:
            gc = color("green" if sr.governed_coverage == 1.0 else "red", f"governed {sr.governed_coverage:.0%}")
            ac = (f"audit {sr.audit_coverage:.0%}" if sr.audit_coverage is not None else "audit n/a")
            notes.append(f"{gc} · {ac}")
        else:
            notes.append(f"cover {sr.coverage:.0%}")
        notes.append(sr.telemetry.strip("[]") if sr.telemetry else "")
        doc_state = "written" if sr.doc_path else color("red", "NO DOCUMENT (abandoned)")
        print(color(flag, f"└─ {stars(sr.rating)} {sr.rating}/5  {doc_state}  — ") +
              "  ".join(n for n in notes if n))

    # ---- task framing ----------------------------------------------------

    def _stage_input(self, cfg: DossierSeedConfig, stage: str, template: str) -> StageInput:
        if is_structured_template(template):
            parts = self._structured_objective(cfg, stage, template)
        else:
            emit = fields_emitted_by(stage)
            emit_spec = "\n".join(f"  - {f.field}: {f.justification}" for f in emit) or "  (none)"
            parts = [
                f"Author Stage {stage} ({STAGE_BASENAME[stage]}) of the change dossier for "
                f"`{cfg.domain}/{cfg.subdomain}` (a NEW subdomain).",
                "Write the COMPLETED stage document in Markdown, following the template below "
                "exactly. Then end with a SINGLE ```json block: {\"registers\": { ... }} holding "
                "EXACTLY these handoff fields (copy FQDNs verbatim; [] or null when not applicable):",
                emit_spec,
                "# Agent context (reading assignment)", cfg.agent_context.read_text(),
            ]
            if stage == "1":
                parts += ["# Human elicitation — the CR seed (your only human input)",
                          cfg.seed_path.read_text()]
            parts += [f"# Stage {stage} template — fill it for {cfg.domain}/{cfg.subdomain}", template]

        # bounded handoff: only the upstream fields this stage declares it consumes,
        # loaded from each producer's PERSISTED projection (so a standalone --stage run works).
        values: dict[str, Any] = {}
        for f in fields_consumed_by(stage):
            prod = self._load_handoff(cfg, f.producer)
            if prod is not None and f.field in prod:
                values[f.field] = prod[f.field]

        return StageInput(stage=stage, objective="\n\n".join(parts),
                          input_projection=GovProjection(stage=stage, values=values),
                          governance_rules=GOVERNANCE_RULES)

    def _structured_objective(self, cfg: DossierSeedConfig, stage: str, template: str) -> list[str]:
        """Document Contract: the worker emits register ROWS (structured intent), not Markdown.
        The renderer owns the document; the structural oracle decides completeness."""
        regs = DossierStageRenderer(template).registers
        specs = []
        enum_lines = []
        for reg in regs.values():
            cols = ", ".join(f'"{k}"' for k in reg.keys)
            req = "REQUIRED" if reg.required else "optional"
            bl = " — BUSINESS LANGUAGE ONLY (no protocol artifact names / FQDNs)" if reg.business_language else ""
            # name THIS register's traceability column(s) — not every register has
            # `source_finding`; some use `evidence`/`fqdn`/`reference`. The worker must fill the
            # one(s) this register actually declares, else the oracle flags the row untraceable.
            ev = [k for k in reg.keys if k in EVIDENCE_COLUMNS]
            trace = f" — fill traceability in: {', '.join(ev)}" if ev else ""
            specs.append(f'  "{reg.register_id}": [ {{ {cols} }} ]   ({req}{bl}{trace})')
            for k, allowed in reg.enums.items():
                enum_lines.append(f'  {reg.register_id}.{k} ∈ {{{", ".join(allowed)}}}')
        parts = [
            f"Author Stage {stage} ({STAGE_BASENAME[stage]}) for `{cfg.domain}/{cfg.subdomain}` "
            "(a NEW subdomain).",
            "OUTPUT CONTRACT — emit a SINGLE json object of REGISTER ROWS. NOT a document, NOT "
            "prose, NOT Markdown — the renderer owns all formatting. Each key is a register id; "
            "each value is a list of row objects using EXACTLY the listed keys. Every row MUST "
            "carry non-empty traceability in THIS register's evidence column — whichever it "
            "declares (`source_finding`, `evidence`, `fqdn`, or `reference`; named per register "
            "below). A register with nothing to report → [].",
            "BUSINESS-LANGUAGE rule — every CONTENT/DESCRIPTION cell (capability, entity, actor, "
            "observation, concern, gap, impact, why_it_matters, record_produced, decision, etc.) "
            "contains a business-language description ONLY: NO artifact names, FQDNs, workflow/"
            "capability/intent/event names, register bindings, or any protocol identifier. Write "
            "'participate in a consensus round', NEVER 'CC_PARTICIPATE_CONSENSUS_ROUND_V0'.",
            "WHERE FQDNs GO — if you need to reference a grounded artifact, put its FQDN ONLY in "
            "the row's evidence column (`source_finding`, `evidence`, `fqdn`, or `reference` — "
            "whichever THIS register declares) — never in a description column. EVERY row MUST "
            "carry non-empty traceability in that column. That is the required traceability and "
            "the ONLY place a protocol identifier belongs at this stage.",
            "Emit exactly these registers:",
            "\n".join(specs),
        ]
        if "belief_verification" in regs:
            # verification stage: lift the belief-bounded contract into the imperative zone,
            # ahead of the register list, so it is read as a directive rather than appended prose.
            parts.insert(1, VERIFICATION_SPINE)
        if enum_lines:
            parts.append(
                "CONTROLLED VOCABULARY — these columns accept ONLY a value from the listed set "
                "(exact uppercase token); any other value is rejected by the oracle:\n"
                + "\n".join(enum_lines))
        parts += ["# Agent context (reading assignment)", cfg.agent_context.read_text()]
        if stage == "1":   # S1 is the stage that consumes the human elicitation (the seed)
            parts += ["# Human elicitation — the CR seed (your only human input)",
                      cfg.seed_path.read_text()]
        parts += [
            f"# Stage {stage} template (structure reference — you fill registers; the renderer "
            "renders the document)", template,
        ]
        return parts

    # ---- handoff persistence (the checkpoint keystone) -------------------

    @staticmethod
    def _handoff_path(cfg: DossierSeedConfig, stage: str) -> Path:
        return cfg.output_dir / "_handoff" / f"{stage}.json"

    def _save_handoff(self, cfg: DossierSeedConfig, stage: str, proj: GovProjection) -> None:
        p = self._handoff_path(cfg, stage)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(dict(proj.values), indent=2, default=str))

    def _load_handoff(self, cfg: DossierSeedConfig, stage: str) -> dict[str, Any] | None:
        p = self._handoff_path(cfg, stage)
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError:
            return None

    # ---- helpers ---------------------------------------------------------

    @staticmethod
    def _document(output) -> str:
        """The dossier document = the worker's content, cleaned for the free-form path.

        Strips: (1) the trailing registers ```json block (the json is the handoff, not the
        document); (2) any conversational preamble before the first Markdown heading — trimming
        to the first heading also drops an opening ```markdown fence the worker may wrap the doc
        in; (3) a single trailing wrapper fence. Interior code fences (e.g. ASCII diagrams) are
        left intact — only an end-of-document closing fence is removed."""
        text = output.findings[1] if len(output.findings) > 1 else ""
        idx = text.rfind("```json")
        if idx != -1:
            text = text[:idx]
        h = re.search(r"^#{1,3}\s+\S", text, re.M)
        if h:
            text = text[h.start():]
        text = re.sub(r"\n```[ \t]*$", "", text.rstrip())
        return text.strip()

    @staticmethod
    def _template_coverage(doc: str, template: str) -> float:
        """Fraction of the template's *output* headings that appear in the authored document.

        Two corrections over a naive heading match (both were inflating false-negatives on the
        free-form authoring-guide templates, S5/S6): (1) ignore scaffolding headings the worker
        is never expected to echo — HTML-comment markers (`<...>`) and `{{placeholder}}` headings;
        (2) match on whitespace-normalized text, so a heading that differs only by a double space
        or a trailing decoration still counts."""
        def norm(s: str) -> str:
            return re.sub(r"\s+", " ", s).strip()
        heads = [h.strip() for h in re.findall(r"^#{1,4}\s+.+$", template, re.M)]
        heads = [h for h in heads if "<" not in h and "{{" not in h]
        if not heads:
            return 1.0
        doc_n = norm(doc)
        present = sum(1 for h in heads if norm(h) in doc_n)
        return present / len(heads)


def _resolve_seed(name: str) -> DossierSeedConfig:
    if name not in DOSSIER_SEEDS:
        raise KeyError(f"unknown dossier seed: {name!r} (known: {sorted(DOSSIER_SEEDS)})")
    return DOSSIER_SEEDS[name]


def run_dossier(worker: Worker, grounding: GroundingProvider, seed: str | DossierSeedConfig, *,
                stages: tuple[str, ...] | None = None, runs_root: Path | None = None,
                evaluator: Evaluator | None = None, verbose: bool = False) -> DossierResult:
    """Entry point: drive the staged dossier authoring for a CR seed.

    Pass `stages=("2",)` to author a single stage (checkpoint mode): it loads upstream handoffs
    from disk, so you can author → review → resume one deliverable at a time."""
    engine = DossierEngine(worker, grounding, evaluator=evaluator, runs_root=runs_root,
                           verbose=verbose)
    return engine.run(seed, stages=stages)


def tool_event_printer(kind: str, **f: Any) -> None:
    """Wire as QwenWorker(on_event=...) for the live R/Y/G grounding stream."""
    if kind == "tool_call":
        dot = _DOT[f["flag"]]
        args = ", ".join(f"{k}={v!r}" for k, v in (f.get("args") or {}).items())
        if f.get("error"):
            tail = color("red", f"ERROR {f['error']}")
        else:
            tail = f"{f['n_results']} results" + (color("yellow", " (repeat)") if f.get("repeat") else "")
        print(f"   {dot} {f['name']}({args}) → {tail}")
    elif kind == "convergence_forced":
        print(color("yellow", "   ⚠ tool budget exhausted — forced finalization "
                              f"({'produced output' if f.get('produced') else 'still empty'})"))

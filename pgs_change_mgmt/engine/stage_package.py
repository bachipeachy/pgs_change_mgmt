"""StagePackageBuilder — export a governed Stage Package (the Guided Authoring artifact, §4).

Guided Authoring Mode makes the human the synchronization point between stages: PGS exports a
governed **Stage Package**, the human runs it through a conversational LLM (Claude Code, a chat
UI), and pastes the response back for import + validation. This module owns the *export* half —
pure governance, **no model is called**. It turns a `StageInput` (built by the same
`DossierEngine._stage_input` the automated path uses) into a `PromptIR` and serializes it to a
`stage_<N>/` directory:

    stage_<N>/
      manifest.json          stage, domain/subdomain, seed, snapshot_hash, mode, gov_version, prompt_hash
      prompt_bundle.json      CANONICAL contract (serialized PromptIR + prompt_hash/schema_hash)
      system_prompt.md         rendered view of prompt_bundle.system_prompt (paste into a chat UI)
      user_prompt.md           rendered view of prompt_bundle.user_prompt
      context/handoff.json     the bounded upstream gov_projection this stage may read
      context/grounding_spec.json  the TYPED grounding constraint (required_tokens + query_rule)
      expected_output.md        the shape of the ```json registers block (fields + worked example)
      schema.json              the stage's register emit-field schema (fields, types, required)

The `.md` files are rendered VIEWS of `prompt_bundle.json` (the source of truth), hash-linked
back via `prompt_hash`. Markdown ≠ contract — the Validator reasons over the bundle.

**grounding_spec sourcing (the I1 design task, §7/P4).** `required_tokens` is the stage's
grounding *frontier*: the protocol code-tokens the worker must confirm via `pi` before using.
Per the approved rule it is derived from the stage's *bounded scope only* — the upstream handoff
this stage consumes plus (for S1, which has no upstream) the elicitation seed's business
vocabulary — never the whole domain vocabulary. It is a frontier to verify, never an answer key.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Sequence

from ..contracts import GroundingProvider, fields_emitted_by
from ..grounding import TOOL_SCHEMAS
from ..renderer.dossier_stage import is_structured_template, EVIDENCE_COLUMNS
from ..renderer.template_compiler import compile_template
from ..evaluator import IdentityEvaluator
from .dossier import DossierEngine, DossierSeedConfig, STAGE_BASENAME, _resolve_seed
from .prompt_ir import PromptIR, sha256_of

PKG_REPO = Path(__file__).resolve().parents[2]

# The query rule that fixes the Case-C phrase-query failure BY DECLARATION (not heuristic rewrite):
# the worker searches single UPPERCASE code tokens, and treats a 0-result as a final answer.
QUERY_RULE = (
    "Search a single UPPERCASE protocol code token (e.g. 'BLOCK', 'TRANSACTION'), never a phrase "
    "or sentence. A search that returns 0 results is a FINAL answer (the artifact does not exist) "
    "— never re-search variants of a token that already returned nothing."
)

# DP3 — the directive that shifts a discovery stage from ad-hoc SEARCH to DISPOSITION + DELTA when the
# platform has already ACQUIRED the neighbourhood (a Computed Semantic Neighborhood ships in the
# package). The worker no longer finds evidence; it disposes of supplied evidence and authors the delta.
DISCOVERY_PROJECTION_DIRECTIVE = (
    "DISCOVERY PROJECTION — YOUR EVIDENCE FLOOR (context/discovery_projection.json). The platform has "
    "already ACQUIRED the existing protocol neighbourhood for this scope: `evidence.existing` (nodes "
    "that exist, each with inclusion provenance), `evidence.absent` (concepts confirmed to resolve to "
    "ZERO artifacts), `evidence.relationships`, and reliable structural observations. DO NOT search "
    "the snapshot for the neighbourhood — it is supplied and deterministic. Your job is DISPOSITION + "
    "DELTA: (1) DISPOSITION every `existing` element as you populate the discovery registers — RELEVANT "
    "(model it), EXCLUDED (out of scope, with reason), or NOT_APPLICABLE; a concept in `absent` is a "
    "CONFIRMED gap, never a search target. (2) Author the NEW DELTA the projection cannot contain — "
    "entities/processes that do not yet exist. Verify each S1 System Belief against the projection: "
    "present in `existing` ⇒ VERIFIED (cite the FQDN); named in `absent` ⇒ the gap it declares. You "
    "should need ZERO new tool lookups — the evidence floor is already in hand."
)

# Term-bearing register columns: the value of one of these keys in a handoff row is a domain term
# (not a sentence), so it contributes code-tokens to the grounding frontier / projection roots.
# `scope_item` harvests the CR's declared governance scope (S1 §13) — the adjacent subdomains the
# change plugs into (consensus_pos, orchestration, wallet, transaction, mempool, identity). These are
# exactly the belief-target neighbourhoods a discovery stage must reach, so they seed the roots of the
# Computed Semantic Neighborhood (SPP.6 — roots from the *declared transformation scope*).
_TERM_COLUMNS = ("term", "entity", "name", "object", "actor", "state", "event", "attribute",
                 "scope_item")

# ── Semantic concept classification (DP1.1) ──────────────────────────────────────────────────
# A harvested token's semantic CATEGORY is the register column it came from — the register schema
# already declares what each column means (a domain term vs a lifecycle state vs a relationship).
# Only ENTITY/CONCEPT-class columns participate in ABSENCE reasoning: a lifecycle state ('Active') or
# a relationship value ('Adjacent') that matches no artifact is a *different semantic category*, not a
# gap. This strengthens the compiler's semantic type system rather than denylisting words:
#   ENTITY/CONCEPT (→ absence frontier + roots): term, entity, name, object, actor, event, attribute,
#                                                scope_item (the declared adjacent subdomains)
#   LIFECYCLE ('state') · RELATIONSHIP ('relationship') · VALUE (certainty, enums): NOT concept-class —
#     they never define negative evidence (a state/relationship/value is not a domain artifact).
_CONCEPT_COLUMNS = ("term", "entity", "name", "object", "actor", "event", "attribute", "scope_item")

# Tokens that are structural/controlled-vocabulary noise, not domain code-tokens — excluded from the
# frontier. (Controlled-vocabulary enum values, certainty tags, and table-scaffolding words.)
_STOP_TOKENS = frozenset({
    # english scaffolding
    "THE", "AND", "FOR", "ITS", "ARE", "WAS", "WERE", "WITH", "THAT", "THIS", "FROM", "INTO",
    "EACH", "PER", "NOT", "ANY", "ALL", "NEW", "OLD", "ONE", "TWO", "MUST", "SHALL", "MAY",
    "CAN", "WILL", "HAS", "HAVE", "BEEN", "OVER", "ONLY", "ALSO", "SUCH", "WHEN", "WHICH",
    # controlled vocabulary / dispositions / certainty
    "VERIFIED", "NOT_FOUND", "INSUFFICIENT_EVIDENCE", "REUSE", "EXTEND", "AUTHOR_NEW", "TRUE",
    "FALSE", "NULL", "NONE", "YES", "HIGH", "MEDIUM", "LOW", "UNRESOLVED", "REQUIRED", "OPTIONAL",
    # table scaffolding / column names
    "TERM", "DEFINITION", "DESCRIPTION", "SOURCE", "FINDING", "EVIDENCE", "STATUS", "STORE",
    "MODEL", "NAME", "NUM", "ROW", "JSON", "PGS", "FQDN",
})

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9]{2,}")          # a candidate code-token (alpha-led, ≥3)
_ALLCAPS_RE = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b")         # an already-uppercase code-token
_MAX_TOKENS = 40                                            # frontier cap (bounded, not exhaustive)


# ---- grounding frontier derivation (P4 — the I1 design task) --------------------------------

def derive_required_tokens(bounded: dict[str, Any], seed_text: str | None) -> list[str]:
    """The stage's grounding frontier: code-tokens from its BOUNDED scope only (never the domain).

    Sources, in scope order: (1) term-bearing columns of the bounded upstream handoff (the terms
    this stage was actually handed); (2) for a seed-only stage (S1, no upstream), the elicitation
    seed's Business Vocabulary terms; (3) already-uppercase code-tokens appearing in either. Each
    phrase is tokenized to uppercase code-tokens, structural/controlled-vocabulary noise removed,
    deduped, sorted, and capped. The worker must still confirm each via `pi`."""
    phrases: list[str] = _terms_from_handoff(bounded)
    text_pool = json.dumps(bounded, default=str)
    if seed_text:
        phrases += _vocab_terms_from_seed(seed_text)
        text_pool += "\n" + seed_text

    tokens: set[str] = set()
    for phrase in phrases:
        tokens.update(_tokenize_phrase(phrase))
    tokens.update(t for t in _ALLCAPS_RE.findall(text_pool) if t not in _STOP_TOKENS and len(t) >= 3)
    tokens = {t for t in tokens if t not in _STOP_TOKENS}
    return sorted(tokens)[:_MAX_TOKENS]


def derive_concept_frontier(bounded: dict[str, Any],
                            seed_text: str | None) -> tuple[list[str], list[str]]:
    """(concept_tokens, root_hint_tokens) for the Computed Semantic Neighborhood (DP1.1).

    Applies semantic concept classification so negative evidence is precise:
      * `concept_tokens` — ENTITY/CONCEPT-class only (from `_CONCEPT_COLUMNS` + seed vocabulary,
        ≥4 chars to drop fragments like 'POS'). These seed roots AND define the absence frontier, so
        a zero-match means "a domain concept has no artifact" — a genuine gap, never a lifecycle state
        or relationship value.
      * `root_hint_tokens` — already-uppercase prose tokens (MINT, ETH): seed roots, NEVER absence.
    Lifecycle-state / relationship / value tokens are simply not concept-class: they neither match
    artifacts nor name gaps, so they are excluded from the projection (they remain in the worker's
    broad grounding frontier via `derive_required_tokens`)."""
    phrases = _concept_terms_from_handoff(bounded)
    if seed_text:
        phrases += _vocab_terms_from_seed(seed_text)
    concept: set[str] = set()
    for phrase in phrases:
        for tok in _tokenize_phrase(phrase):
            if len(tok) >= 4:
                concept.add(tok)
    pool = json.dumps(bounded, default=str) + (("\n" + seed_text) if seed_text else "")
    root_hints = {t for t in _ALLCAPS_RE.findall(pool)
                  if t not in _STOP_TOKENS and len(t) >= 3 and t not in concept}
    return sorted(concept)[:_MAX_TOKENS], sorted(root_hints)


def out_of_scope_tokens(bounded: dict[str, Any], concept_tokens: Sequence[str]) -> list[str]:
    """CR-DECLARED out-of-scope concepts (S1 §12) — deterministic trim tokens for the projection (DP1.3).

    A declaration, never a relevance judgment. Excludes any token that is also a concept, so a phrase
    like 'chain reorganization' never trims chain artifacts. Lexical resolution is best-effort: an item
    whose word form differs from the artifact segment (e.g. 'slashing' vs 'SLASH') is simply not trimmed
    here and falls to the worker's disposition — the platform trims what is declared and resolvable, and
    never guesses the rest."""
    concept = {t.upper() for t in concept_tokens}
    toks: set[str] = set()
    for row in bounded.get("out_of_scope") or []:
        if isinstance(row, dict):
            for t in _tokenize_phrase(row.get("item", "")):
                if len(t) >= 4:
                    toks.add(t)
    return sorted(toks - concept)


def _concept_terms_from_handoff(bounded: dict[str, Any]) -> list[str]:
    """Harvest ENTITY/CONCEPT-class cell values from concept-bearing columns only (DP1.1)."""
    terms: list[str] = []
    for value in bounded.values():
        if not isinstance(value, list):
            continue
        for row in value:
            if not isinstance(row, dict):
                continue
            for col in _CONCEPT_COLUMNS:
                cell = row.get(col)
                if isinstance(cell, str) and cell.strip():
                    terms.append(cell)
    return terms


def _tokenize_phrase(phrase: str) -> list[str]:
    """Split a domain term into uppercase code-tokens, dropping scaffolding words."""
    out = []
    for m in _TOKEN_RE.findall(str(phrase)):
        tok = m.upper()
        if tok not in _STOP_TOKENS:
            out.append(tok)
    return out


def _terms_from_handoff(bounded: dict[str, Any]) -> list[str]:
    """Harvest domain terms from term-bearing columns of every list-of-rows register handed in."""
    terms: list[str] = []
    for value in bounded.values():
        if not isinstance(value, list):
            continue
        for row in value:
            if not isinstance(row, dict):
                continue
            for col in _TERM_COLUMNS:
                cell = row.get(col)
                if isinstance(cell, str) and cell.strip():
                    terms.append(cell)
    return terms


def _vocab_terms_from_seed(seed_text: str) -> list[str]:
    """Extract first-column terms from the seed's Business Vocabulary markdown table.

    Scans rows of the `| Term | Definition | … |` table under the Business Vocabulary heading and
    returns each Term cell. Falls back to no terms if the section/table is absent (the all-caps
    scan still contributes)."""
    terms: list[str] = []
    in_section = False
    for line in seed_text.splitlines():
        if re.match(r"^#{1,4}\s", line):
            in_section = bool(re.search(r"business vocabulary", line, re.I))
            continue
        if not in_section:
            continue
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells or not cells[0]:
            continue
        first = cells[0]
        if first.lower() in ("term", "") or set(first) <= set("-: "):   # header / separator row
            continue
        terms.append(first)
    return terms


_BELIEF_COLUMNS = ("belief", "why_it_matters", "verification_goal")


def belief_target_terms(bounded: dict[str, Any]) -> list[str]:
    """Domain concepts named in the CR's system-belief prose (S1 §5) — ROOT-ONLY neighbourhood seeds.

    The belief targets (a validator registry, slot processing, …) are adjacent capabilities a
    discovery stage must reach but that the structured vocabulary / governance-scope columns do not
    name. Harvested loosely (≥4-char tokens minus stopwords); the projection's whole-segment matcher
    filters prose noise (verb/noun form mismatches like 'SELECTION' vs 'SELECT'), and these never
    contribute to `absent`, so over-harvesting is safe — extra roots are dispositioned, not false
    gaps. This realizes "roots from the declared transformation scope" for the belief-named part."""
    beliefs = bounded.get("system_beliefs") or []
    tokens: set[str] = set()
    for row in beliefs:
        if not isinstance(row, dict):
            continue
        for col in _BELIEF_COLUMNS:
            for tok in _tokenize_phrase(row.get(col, "")):
                if len(tok) >= 4:
                    tokens.add(tok)
    return sorted(tokens)


# ---- register contract (schema.json + the bundle's register_contract) -----------------------

def build_register_contract(stage: str, template: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return (schema, register_contract) for a stage.

    `schema` is the full per-register column schema written to `schema.json`. `register_contract`
    is the compact {fields, schema_hash} the bundle embeds — both carry the SAME `schema_hash`, so
    the ingress validator can confirm a response was authored against this exact contract."""
    if is_structured_template(template):
        regs = compile_template(template)
        registers = {
            r.register_id: {
                "columns": list(r.keys),
                "required": r.required,
                "business_language": r.business_language,
                # column-scope of the business-language rule: None ⇒ all content columns; a list ⇒
                # only those columns are business-language-checked (e.g. S6b new_artifacts: only
                # `capability` — `code` legitimately carries a binding FQDN). Mirrors the renderer.
                "bl_columns": list(r.bl_columns) if r.bl_columns else None,
                "evidence_columns": [k for k in r.keys if k in EVIDENCE_COLUMNS],
                "enums": {k: list(v) for k, v in r.enums.items()},
            }
            for r in regs
        }
        body = {"stage": stage, "structured": True, "registers": registers}
        fields = sorted(registers)
    else:
        emit = fields_emitted_by(stage)
        emit_fields = [
            {"field": f.field, "justification": f.justification,
             "optional": f.optional, "rollout": f.rollout, "fqdn_pointer": f.fqdn_pointer}
            for f in emit
        ]
        body = {"stage": stage, "structured": False, "emit_fields": emit_fields}
        fields = [f.field for f in emit]

    schema_hash = sha256_of(body)
    schema = {**body, "schema_hash": schema_hash}
    register_contract = {"fields": fields, "schema_hash": schema_hash}
    return schema, register_contract


# DRC Part B — the OPTIONAL `human_engagement` register the worker MAY add to any stage to surface
# genuine design questions for the human. Advertised on EVERY stage (both transports). It is diagnostic
# only: never enters the handoff, never affects a gate or the stage's readiness. Its questions-only
# boundary is enforced by design_review.validate_human_engagement.
_PART_B_ADVISORY = """
## Design Review — Part B (optional · diagnostic · never stage content)

Inside `registers` you MAY add ONE extra key, `human_engagement`, to raise design decisions that
protocol inspection (`pi`) and governance genuinely CANNOT answer — business policy, preference, or an
ambiguous requirement only a human can settle. It never enters the handoff and never changes any gate
or the stage's readiness.

- `human_engagement` (optional) — a list of rows, columns: question, why, tradeoffs
- Questions ONLY. Do NOT state confidence, readiness, a percentage, or any self-evaluation
  (`READY_FOR_NEXT_STAGE` / "I am confident" / "80%") — those are engine-certified facts (Part A),
  and a Part-B row that asserts them is rejected.
- Omit the register entirely when you have no genuine human decision to raise (never fabricate one).

```json
{
  "registers": {
    "human_engagement": [
      {"question": "…a decision only a human can make…", "why": "…why PI/governance cannot answer it…", "tradeoffs": "…the options and their costs…"}
    ]
  }
}
```
"""


def _expected_output_md(schema: dict[str, Any]) -> str:
    """A worked example of the ```json registers block the response must carry."""
    if schema.get("structured"):
        registers = schema["registers"]
        example = {rid: [] for rid in registers}
        lines = ["# Expected output", "",
                 "Emit a SINGLE fenced ```json object of register rows (the renderer owns formatting).",
                 "Each key is a register id; each value is a list of row objects using EXACTLY the "
                 "listed columns. A register with nothing to report → [].", "",
                 "## Registers (columns · required)"]
        for rid, spec in registers.items():
            req = "REQUIRED" if spec["required"] else "optional"
            cols = ", ".join(spec["columns"])
            bl = " · business-language only" if spec["business_language"] else ""
            lines.append(f"- `{rid}` ({req}{bl}) — columns: {cols}")
            for col, allowed in spec["enums"].items():
                lines.append(f"    - `{col}` ∈ {{{', '.join(allowed)}}}")
        worked = json.dumps({"registers": example}, indent=2)
        lines += ["", "## Worked skeleton", "```json", worked, "```"]
        return "\n".join(lines) + "\n" + _PART_B_ADVISORY
    # free-form: a registers envelope keyed by emit field
    example = {f["field"]: None for f in schema["emit_fields"]}
    lines = ["# Expected output", "",
             "End with a SINGLE fenced ```json object: {\"registers\": { … }} holding EXACTLY these "
             "handoff fields (copy FQDNs verbatim; [] or null when not applicable).", "",
             "## Handoff fields"]
    for f in schema["emit_fields"]:
        tag = " (optional)" if f["optional"] else (" (rollout)" if f["rollout"] else "")
        lines.append(f"- `{f['field']}`{tag} — {f['justification']}")
    worked = json.dumps({"registers": example}, indent=2)
    lines += ["", "## Worked skeleton", "```json", worked, "```"]
    return "\n".join(lines) + "\n" + _PART_B_ADVISORY


# ---- the builder ----------------------------------------------------------------------------

class StagePackageBuilder:
    """Export a governed Stage Package for one stage — pure governance, no model called.

    Reuses `DossierEngine._stage_input` so a Guided stage is framed from the IDENTICAL bounded task
    an automated worker receives; only the transport (human paste) differs."""

    MODE = "guided"

    def __init__(self, seed: str | DossierSeedConfig, *,
                 grounding: GroundingProvider | None = None,
                 governance_version: str | None = None) -> None:
        self.cfg = seed if isinstance(seed, DossierSeedConfig) else _resolve_seed(seed)
        # grounding is OPTIONAL and used ONLY to stamp the snapshot hash into the manifest (binding
        # the package to a snapshot). Frontier derivation never grounds. None ⇒ snapshot_hash null
        # (hermetic export, e.g. the selftest).
        self.grounding = grounding
        self.governance_version = governance_version or _pkg_version()
        # A no-model engine purely to reuse _stage_input (it never touches the worker/grounding).
        self._engine = DossierEngine(_NoWorker(), _NoGrounding(), evaluator=IdentityEvaluator())

    def build_ir(self, stage: str, template: str) -> tuple[PromptIR, dict[str, Any], dict[str, Any] | None]:
        """Build the `PromptIR`, the full `schema`, and the Computed Semantic Neighborhood (DP2).

        When a neighbourhood is available, the objective gains the DP3 directive (disposition + delta,
        do not search); returns `(ir, schema, projection)` — projection is None in a hermetic export."""
        task = self._engine._stage_input(self.cfg, stage, template)
        bounded = dict(task.input_projection.values)
        schema, register_contract = build_register_contract(stage, template)
        seed_text = self.cfg.seed_path.read_text() if stage == "1" else None
        tokens = derive_required_tokens(bounded, seed_text)   # broad worker grounding frontier
        grounding_spec = {
            "required_tokens": tokens,
            "query_rule": QUERY_RULE,
            "validation_mode": "strict",
        }
        # The Computed Semantic Neighborhood (Discovery Projection) belongs to the DISCOVERY stage (S2)
        # ONLY. S1 is fact-capture from the seed; S3+ are analysis over S2's *Validated Semantic
        # Evidence* (the dispositioned discovery handoff) — a downstream stage consumes validated
        # knowledge, it does not re-discover the neighbourhood. So exactly one stage ships a projection.
        if stage != "2":
            projection = None
        else:
            concept_tokens, root_hints = derive_concept_frontier(bounded, seed_text)
            root_only = sorted(set(root_hints) | set(belief_target_terms(bounded)))
            excluded = out_of_scope_tokens(bounded, concept_tokens)   # DP1.3 CR-declared out-of-scope
            projection = self._discovery_projection(concept_tokens, root_only, excluded)
        objective = task.objective
        if projection is not None:
            # DP3 — the neighbourhood is supplied, so the stage shifts from search to disposition+delta.
            objective = f"{objective}\n\n{DISCOVERY_PROJECTION_DIRECTIVE}"
        ir = PromptIR(
            system={
                "mandate": _SYSTEM_PROMPT,
                "governance_version": self.governance_version,
                "allowed_tools": _tool_names(),
                "register_contract": register_contract,
            },
            user={
                "stage": stage,
                "objective": objective,
                "governance_rules": list(task.governance_rules),
                "handoff": bounded,
            },
            constraints=grounding_spec,
        )
        return ir, schema, projection

    def build(self, stage: str, *, out_root: Path) -> Path:
        """Export the `stage_<N>/` package under `out_root`; returns the package directory."""
        if stage not in STAGE_BASENAME:
            raise ValueError(f"stage {stage!r} is not a worker-authored dossier stage "
                             f"(valid: {sorted(STAGE_BASENAME)})")
        template = (self.cfg.templates_dir / f"{STAGE_BASENAME[stage]}_template_v0.md").read_text()
        # DP2 — the Computed Semantic Neighborhood ships with the package; DP3 — its presence adds the
        # disposition+delta directive to the objective (build_ir). None in a hermetic export.
        ir, schema, projection = self.build_ir(stage, template)
        bundle = ir.to_bundle()

        pkg = Path(out_root) / f"stage_{stage}"
        (pkg / "context").mkdir(parents=True, exist_ok=True)

        manifest = {
            "stage": stage,
            "domain": self.cfg.domain,
            "subdomain": self.cfg.subdomain,
            "seed": self.cfg.name,
            "snapshot_hash": self._snapshot_hash(),
            "mode": self.MODE,
            "governance_version": self.governance_version,
            "prompt_hash": bundle["prompt_hash"],
            "schema_hash": schema["schema_hash"],
            "discovery_projection_id": (
                projection["projection_identity"]["projection_id"] if projection else None),
        }
        _write_json(pkg / "manifest.json", manifest)
        _write_json(pkg / "prompt_bundle.json", bundle)
        (pkg / "system_prompt.md").write_text(ir.render_system())
        (pkg / "user_prompt.md").write_text(ir.render_user())
        _write_json(pkg / "context" / "handoff.json", ir.user["handoff"])
        _write_json(pkg / "context" / "grounding_spec.json", ir.constraints)
        if projection is not None:
            _write_json(pkg / "context" / "discovery_projection.json", projection)
        (pkg / "expected_output.md").write_text(_expected_output_md(schema))
        _write_json(pkg / "schema.json", schema)
        return pkg

    def _discovery_projection(self, tokens: list[str], root_only: list[str] | None = None,
                              excluded: list[str] | None = None) -> dict[str, Any] | None:
        """Compute the Discovery Projection (a *Computed* Semantic Neighborhood) for this scope.

        Invokes the compiler product directly (SPP.2 — the compiler implements, the Stage Package
        exports). `tokens` are the structured concept tokens (roots + absence frontier); `root_only`
        are belief-target concepts that seed roots but never absence. Requires a resolvable workspace
        + compiled snapshot; returns None when the workspace is unset or no scope tokens exist, so a
        hermetic export degrades gracefully. A genuinely broken snapshot fails hard (not swallowed)."""
        ws_root = os.environ.get("PGS_WORKSPACE")
        if not ws_root or not tokens:
            return None
        from pgs_compiler.inspection.loader import Workspace
        from pgs_compiler.inspection.traversal import SemanticGraph
        from pgs_compiler.inspection.discovery import (
            TransformationScope, compute_discovery_projection)
        graph = SemanticGraph(Workspace(Path(ws_root)))
        scope = TransformationScope(
            domain=self.cfg.domain, subdomain=self.cfg.subdomain, concept_tokens=tuple(tokens),
            root_only_tokens=tuple(root_only or ()), excluded_tokens=tuple(excluded or ()))
        return compute_discovery_projection(graph, scope)

    def _snapshot_hash(self) -> str | None:
        if self.grounding is None:
            return None
        gate = self.grounding.query("validate")
        return gate.get("result", {}).get("snapshot_hash")


# ---- helpers --------------------------------------------------------------------------------

def _write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, default=str) + "\n")


def _tool_names() -> list[str]:
    return [t.get("function", {}).get("name", "") for t in TOOL_SCHEMAS]


def _pkg_version() -> str:
    """The change_mgmt package release (the governance version stamped into the package)."""
    pyproject = PKG_REPO / "pyproject.toml"
    if pyproject.exists():
        m = re.search(r'(?m)^version\s*=\s*"([^"]+)"', pyproject.read_text())
        if m:
            return m.group(1)
    return "0.0.0"


class _NoWorker:
    name = "stage-package-export"

    def execute_stage(self, task):   # pragma: no cover - export never calls a worker
        raise RuntimeError("StagePackageBuilder exports a governed package; it calls no worker.")


class _NoGrounding:
    def query(self, op, /, **kwargs):   # pragma: no cover - _stage_input never grounds
        raise RuntimeError("StagePackageBuilder export does not ground; pass grounding= for "
                           "the snapshot hash only.")


# The canonical authoring mandate, imported lazily to avoid a hard worker-package import cycle
# at module load (stage_package is engine-side; _authoring is worker-side).
from ..worker._authoring import SYSTEM_PROMPT as _SYSTEM_PROMPT  # noqa: E402

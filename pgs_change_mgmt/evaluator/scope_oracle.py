"""Scope-boundary oracle — deterministic out-of-scope fence (governing-fence contract fix, 2026-06-24).

A discovery/model stage must not model a capability the human deferred in S1 §12 Out of Scope. Once
`out_of_scope` is forwarded into the stage's bounded input (the contract fix), this oracle enforces
it deterministically: a deferred term that prefix-matches a token in a modeled-capability NAME column
is a governance violation, and the offending register drops the stage's governed coverage.

Strictly lexical and deterministic — NO embeddings, semantic similarity, LLM judging, or ontology
reasoning (per the expert's "simple lexical variants are enough; revisit only if you hit
`Slashing → Validator Penalty Processing`"). Matching is prefix-based with a 4-char floor, which
absorbs the real variants (`Slashing`↔`Slash Enforcement`, `reorg`↔`reorganization`).

In-scope nouns (Chain, Block, Validator …) are excluded via an allowlist drawn from the governed
in-scope registers already present in the stage's bounded input — `business_vocabulary` at S2,
`entities` at S4 — so "Chain reorganization" fences `reorganization`/`reorg`, never `chain`.
"""

from __future__ import annotations

import re

# Modeled-capability NAME columns per stage — where the document asserts "this is part of the
# design." Deliberately narrow: the name column only, never evidence / notes / impact (those may
# legitimately *mention* a deferred concept). S3 is intentionally NOT hard-enforced in v1: its
# bounded input carries no clean in-scope noun allowlist, so it receives `out_of_scope` (forwarded)
# plus template guidance only — hardening it is deferred until an allowlist source is settled.
SCOPE_TARGETS: dict[str, tuple[tuple[str, str], ...]] = {
    "2": (("business_processes", "process"),),
    "4": (("capability_graph", "capability"),),
}

# In-scope noun sources already in the stage's bounded input (register id → name column key).
_INSCOPE_NOUNS = {"business_vocabulary": "term", "entities": "entity", "bm_entities": "entity"}

# Structural / scaffolding words in the `out_of_scope` item phrasings that are not deferred concepts
# ("The Attest *step* of the *PoS progression*", "Fork *resolution*"). In-scope domain nouns are NOT
# listed here — they are excluded dynamically via the governed allowlist.
_STOP = {"the", "of", "a", "an", "and", "or", "to", "in", "on", "for", "this", "that", "these",
         "those", "step", "pos", "progression", "resolution", "future", "iteration", "increment",
         "part", "release", "deferred", "proposed", "good", "treated", "with", "from", "into",
         "additional"}

_WORD = re.compile(r"[A-Za-z]+")
_MIN = 4   # ignore short tokens; both match sides honour this floor


def _words(text: object) -> list[str]:
    return [w.lower() for w in _WORD.findall(str(text)) if len(w) >= _MIN]


def _prefix_match(a: str, b: str) -> bool:
    """Deterministic lexical kinship: one token is a prefix of the other (4-char floor already
    applied). Absorbs singular/plural/gerund/derivation without fuzzy similarity."""
    return a.startswith(b) or b.startswith(a)


def _allowlist(projection_values: dict) -> set[str]:
    """In-scope noun words drawn from the governed registers in the stage's bounded input."""
    allow: set[str] = set()
    for reg, key in _INSCOPE_NOUNS.items():
        for row in projection_values.get(reg) or []:
            if isinstance(row, dict):
                allow |= set(_words(row.get(key, "")))
    return allow


def _deferred_terms(out_of_scope: object, allow: set[str]) -> set[str]:
    """Distinctive deferred words: item words that are neither scaffolding nor an in-scope noun."""
    terms: set[str] = set()
    for row in out_of_scope or []:
        item = row.get("item") if isinstance(row, dict) else row
        for w in _words(item):
            if w in _STOP:
                continue
            if any(_prefix_match(w, a) for a in allow):   # an in-scope noun, not a deferred concept
                continue
            terms.add(w)
    return terms


def check_scope_boundary(stage: str, data: dict, projection_values: dict) -> list[tuple[str, str]]:
    """Return (register_id, issue) for every modeled-capability row naming a deferred capability.

    `data` = the stage's authored registers; `projection_values` = its bounded input (must include
    `out_of_scope` for the check to run). No-op for stages without targets or with no deferred set.
    """
    targets = SCOPE_TARGETS.get(stage)
    if not targets:
        return []
    deferred = _deferred_terms(projection_values.get("out_of_scope"), _allowlist(projection_values))
    if not deferred:
        return []
    issues: list[tuple[str, str]] = []
    for rid, namecol in targets:
        for i, row in enumerate(data.get(rid) or []):
            cell = row.get(namecol, "") if isinstance(row, dict) else row
            hits = sorted({d for d in deferred for t in _words(cell) if _prefix_match(t, d)})
            if hits:
                issues.append((rid, f"{rid}[{i}].{namecol}: models a capability deferred in "
                                    f"S1 §12 Out of Scope ({hits}) — not a candidate for this CR"))
    return issues

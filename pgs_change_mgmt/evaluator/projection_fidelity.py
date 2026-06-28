"""ASSERT_PROJECTION_FIDELITY — the pipeline-validation gate.

A stage emits its governed information once; the engine then renders it into several *projections*
(markdown doc, JSON handoff, later: compiler input, tokenized snapshot). The Phase-4 discovery was
that these had silently diverged — the chain `_handoff/*.json` carried only ~25–40 % of the rows its
own rendered markdown carried. The JSON was therefore not an *incomplete* handoff; it was a
**non-authoritative projection**. A projection that does not carry exactly the governed information
intended for downstream is INVALID, not merely lossy.

    Projection Fidelity:  Projection(markdown)  ==  Projection(JSON)      (over the stage's emit-fields)

This oracle makes that a measurable, governed property. It is the first gate in the pipeline order
(Governance → **Projection Fidelity** → Construction Closure → Compiler → Runtime → Evidence): the
fidelity gate validates the *pipeline*, before construction closure validates the *specification*.

Scope: fidelity is asserted over a stage's **declared emit-fields** only (`fields_emitted_by`). A
register the markdown carries but the schema does not forward (no declared consumer) stays in the
stage's narrative by design — it is not part of the projection and not compared here.

KISS: the same `parse_registers` primitive that reads the markdown register tables defines both sides
— the migration *writes* this equality into the JSON; this oracle *asserts* it. They cannot drift
apart without one of them failing.
"""

from __future__ import annotations

from ..contracts.gov_projection import fields_emitted_by
from ..engine.build_sheet import parse_registers

# the renderer represents an EMPTY register as a single placeholder row rather than zero rows; both
# projections must read that as "empty" so a doc-side sentinel does not look like a dropped JSON row.
_EMPTY_CELL = {"", "-", "—", "none", "none identified", "n/a", "na", "tbd", "none yet"}


def _is_sentinel(row: dict) -> bool:
    return all(str(v).strip().lower() in _EMPTY_CELL for v in row.values())


def _clean(rows: list) -> list[dict]:
    """Drop renderer empty-placeholder rows so an empty register normalises to [] on both sides."""
    real = [r for r in rows if isinstance(r, dict) and not _is_sentinel(r)]
    return real


def _md_projection(md_text: str, stage: str) -> dict[str, list[dict]]:
    """The stage's projection as carried by its rendered markdown — emit-fields only, sentinels dropped."""
    emit = {f.field for f in fields_emitted_by(stage)}
    return {rid: _clean(rows) for rid, rows in parse_registers(md_text).items() if rid in emit}


def _json_projection(handoff: dict, stage: str) -> dict[str, list[dict]]:
    """The stage's projection as carried by its JSON handoff — emit-fields only, sentinels dropped."""
    emit = {f.field for f in fields_emitted_by(stage)}
    return {k: _clean(v) for k, v in (handoff or {}).items()
            if k in emit and isinstance(v, list)}


def _rollout_fields(stage: str) -> set[str]:
    return {f.field for f in fields_emitted_by(stage) if f.rollout}
def _optional_fields(stage: str) -> set[str]:
    return {f.field for f in fields_emitted_by(stage) if f.optional}


def assert_projection_fidelity(stage: str, md_text: str, handoff: dict) -> list[str]:
    """Issues where the JSON handoff is not a faithful projection of the stage's markdown.

    Empty ⇒ the two projections are equal over the stage's emit-fields (fidelity holds). Checks, per
    emit-field register: present in both, identical row count, identical row keys, identical values,
    identical order — no dropped row, no invented row, no reordering. A `rollout` / `optional` field
    absent from BOTH sides is not a fidelity failure (it is the migration ratchet's concern, not this
    gate's); absent from only one side IS a fidelity failure (the projections disagree).
    """
    md = _md_projection(md_text, stage)
    js = _json_projection(handoff, stage)
    tolerant = _rollout_fields(stage) | _optional_fields(stage)
    issues: list[str] = []

    for reg in sorted(set(md) | set(js)):
        in_md, in_js = reg in md, reg in js
        if not in_md and not in_js:
            continue
        if in_md != in_js:
            if reg in tolerant and not (md.get(reg) or js.get(reg)):
                continue  # absent-or-empty on the missing side, field is mid-rollout/optional
            present, absent = ("markdown", "JSON") if in_md else ("JSON", "markdown")
            issues.append(f"ASSERT_PROJECTION_FIDELITY[{stage}]: register '{reg}' present in "
                          f"{present} but absent from {absent} (projections disagree)")
            continue
        mrows, jrows = md[reg], js[reg]
        if len(mrows) != len(jrows):
            issues.append(f"ASSERT_PROJECTION_FIDELITY[{stage}]: register '{reg}' row count "
                          f"markdown={len(mrows)} != JSON={len(jrows)} "
                          f"({'dropped' if len(jrows) < len(mrows) else 'invented'} rows)")
            continue
        for idx, (mr, jr) in enumerate(zip(mrows, jrows)):
            if set(mr) != set(jr):
                issues.append(f"ASSERT_PROJECTION_FIDELITY[{stage}]: register '{reg}' row {idx} keys "
                              f"markdown={sorted(mr)} != JSON={sorted(jr)}")
            elif mr != jr:
                diff = [k for k in mr if mr.get(k) != jr.get(k)]
                issues.append(f"ASSERT_PROJECTION_FIDELITY[{stage}]: register '{reg}' row {idx} "
                              f"value drift on {diff}")
    return issues

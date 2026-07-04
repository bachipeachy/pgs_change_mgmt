"""Frozen chain fixture — a committed, test-owned slice of the golden blockchain/chain dossier.

The construction selftests (§9–§12) consume the chain corpus (S5/S6b/S7 markdown → `cr_ir/`).
They must NOT read the *live* working dossier under `change_mgmt/dossiers/blockchain/chain`, because
that dossier is deliberately cleared for a from-seed run — clearing it would break the suite. Instead
each selftest materializes THIS frozen fixture into a throwaway tmp dossier, regenerates the handoffs,
and runs against the copy. Deterministic, hermetic, and independent of any live run.

The fixture markdown is a byte-copy of the golden chain reference (the exemplar the selftests already
assert against); it is versioned test data, never subject to dossier-clearing.
"""
from __future__ import annotations

import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

FIXTURE = Path(__file__).resolve().parent / "_fixtures" / "chain"
STAGES = ("5", "6b", "7")

# The fixture is a PLACEHOLDER until the first governed from-seed S1→S8 run produces the real corpus.
# The current markdown is a byte-copy of the committed chain golden, which PREDATES S7 authoring of
# `new_capabilities`/`new_intents` (gov_projection now emits them) — so it cannot close D4. The D4-closed
# regression tests (§11/§12) stay PENDING until the fixture is re-frozen from the governed pipeline
# output. `authored()` is the switch: it flips true the moment the frozen S7 markdown carries the
# authoring registers, auto-converting the pending skips into full assertions. Never inject content from
# scratch/bootstrap aids into this fixture — it must originate exclusively from the governed pipeline.
_AUTHORING_MARK = "<!-- register:new_capabilities"


def authored() -> bool:
    """True once the frozen S7 markdown carries the S7 authoring registers (governed from-seed corpus)."""
    return any(_AUTHORING_MARK in p.read_text() for p in FIXTURE.glob("7_*_v0.md"))


@contextmanager
def chain_dossier() -> Iterator[Path]:
    """Yield a tmp `…/blockchain/chain` dossier: frozen markdown + freshly-migrated `cr_ir/`.

    The directory is named `blockchain/chain` so the migration's `{parent.name}/{name}` resolution and
    the selftests' `blockchain_chain` filenames line up with the golden. Cleaned up on exit.
    """
    from ._migrate_cr_ir_from_baseline import migrate_stage

    root = Path(tempfile.mkdtemp(prefix="cm_chain_fixture_"))
    dossier = root / "blockchain" / "chain"
    dossier.mkdir(parents=True)
    for md in sorted(FIXTURE.glob("*_v0.md")):
        shutil.copy(md, dossier / md.name)
    for stage in STAGES:
        _, issues = migrate_stage(dossier, stage)
        assert not issues, f"frozen fixture failed projection fidelity at S{stage}: {issues}"
    try:
        yield dossier
    finally:
        shutil.rmtree(root, ignore_errors=True)
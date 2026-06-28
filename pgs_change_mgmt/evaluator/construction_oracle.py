"""The Construction Oracle (Patch 4) — the single surface over construction quality.

One responsibility per gate, assembled here so no single measure quietly owns architecture:

    Construction Oracle
        ├── structural completeness      ┐
        ├── provenance completeness      ├─ STATIC  — over the Build Sheet (build_sheet_oracle)
        ├── decision completeness        ┘  raises BUILDABLE → CONSTRUCTION_READY
        ├── structural invention            EMPIRICAL — over a built artifact (invention_oracle)
        └── convergence                     EMPIRICAL — over two built artifacts (convergence)

The static three validate the SPECIFICATION (is the sheet construction-closed?); the empirical two
validate the BUILD (did the builder conform, and do independent builders agree?). This mirrors the
pipeline gate order — Projection Fidelity (the pipeline) → Construction Closure (the spec) → the
build — each gate with exactly one job.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..engine.build_sheet import BuildSheetModel, BuildSheetSetModel
# static gate (re-exported: the Construction Oracle's specification half)
from .build_sheet_oracle import assert_construction_closed  # noqa: F401
from .invention_oracle import structural_invention, text_invention
from .convergence import convergence


@dataclass
class BuildEvaluation:
    """The empirical half of the oracle for one Build Sheet, over one or two builder outputs."""
    code: str
    structural_invention: dict[str, list[str]] = field(default_factory=dict)  # ERROR
    text_invention: dict[str, list[str]] = field(default_factory=dict)        # WARN
    convergence: dict | None = None                                           # None ⇒ <2 builders

    @property
    def conformant(self) -> bool:
        """No structural invention ⇒ the artifact added no design beyond the sheet (the ERROR gate)."""
        return not self.structural_invention

    @property
    def converged(self) -> bool | None:
        return None if self.convergence is None else self.convergence["converged"]


def evaluate_build(sheet: BuildSheetModel, artifact_a: str, artifact_b: str | None = None) -> BuildEvaluation:
    """Run the empirical oracles for one sheet: structural + text invention, and (if two outputs)
    convergence. Structural invention is the gate; text invention and convergence are diagnostics."""
    ev = BuildEvaluation(
        code=sheet.code,
        structural_invention=structural_invention(artifact_a, sheet),
        text_invention=text_invention(artifact_a, sheet),
    )
    if artifact_b is not None:
        ev.convergence = convergence(artifact_a, artifact_b)
    return ev


def construction_ready_sheets(model: BuildSheetSetModel) -> list[BuildSheetModel]:
    """Run the static gate and return the sheets it raised to CONSTRUCTION_READY (specification half)."""
    from ..engine.build_sheet import CONSTRUCTION_READY
    assert_construction_closed(model)
    return [s for s in model.sheets if s.readiness == CONSTRUCTION_READY]

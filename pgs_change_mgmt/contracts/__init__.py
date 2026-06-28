"""Engine boundary contracts — the stable architectural seam.

`gov_projection` is the boundary object every seam crosses. Each seam is declared in its
own module so it can evolve (and grow a second conforming implementation) independently:

    gov_projection  the handoff object + schema
    worker          Worker / StageInput / StageOutput   (Plugin #1)
    grounding       GroundingProvider                   (Plugin #2)
    evaluator       Evaluator / Verdict                 (Plugin #3)
    renderer        Renderer                            (Plugin #4)

This package is the public façade: import contracts from `pgs_change_mgmt.contracts`,
never from the individual seam modules.
"""

from .gov_projection import (
    CLOSURE,
    GOV_PROJECTION_SCHEMA,
    GovProjection,
    GovProjectionField,
    fields_consumed_by,
    fields_emitted_by,
    validate_schema,
)
from .worker import StageInput, StageOutput, Worker
from .grounding import GroundingProvider
from .evaluator import Evaluator, Verdict
from .renderer import Renderer
from .provenance import (
    Clarification,
    is_admissible,
    PROVENANCE_TYPES,
    DISPOSITIONS,
    OWNERS,
    PRIORITIES,
    SEED,
    GROUNDED,
    INFERRED,
    CLARIFIED,
    ACCEPTED,
    REJECTED,
    PENDING,
    HUMAN,
    SNAPSHOT,
    GOVERNANCE,
    CRITICAL,
    IMPORTANT,
    OPTIONAL,
    UNRESOLVED,
)

__all__ = [
    "CLOSURE",
    "GOV_PROJECTION_SCHEMA",
    "GovProjection",
    "GovProjectionField",
    "fields_consumed_by",
    "fields_emitted_by",
    "validate_schema",
    "Evaluator",
    "GroundingProvider",
    "Renderer",
    "StageInput",
    "StageOutput",
    "Verdict",
    "Worker",
    # provenance / governed-inference (Phase 1)
    "Clarification",
    "is_admissible",
    "PROVENANCE_TYPES",
    "DISPOSITIONS",
    "OWNERS",
    "PRIORITIES",
    "SEED",
    "GROUNDED",
    "INFERRED",
    "CLARIFIED",
    "ACCEPTED",
    "REJECTED",
    "PENDING",
    "HUMAN",
    "SNAPSHOT",
    "GOVERNANCE",
    "CRITICAL",
    "IMPORTANT",
    "OPTIONAL",
    "UNRESOLVED",
]

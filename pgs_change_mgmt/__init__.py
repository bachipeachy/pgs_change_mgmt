"""PGS Change Management Engine — the governance projection engine.

A first-class subsystem (not a repo of scripts) that coordinates governed change:

    Change Request → process engine → worker → governed contracts (gov_projection)
                   → renderers → compiler → admissible protocol

It sits in the tri-layer separation as the *coordination* layer:

    pgs_change_mgmt = governance projection engine   (this package)
    pgs_compiler    = admissibility engine
    runtime         = execution engine

Core invariant: **Process ≠ Worker.** The engine owns the seam contracts
(`contracts/`); concrete implementations (a worker, a grounding provider, an evaluator,
a renderer) conform to them. The boundary object that crosses every seam is the
`gov_projection`.

Subpackages map to the future plugin seams (single conforming implementation each today;
a second is an addition, never a refactor):

    contracts/   gov_projection (boundary object + schema) + worker/grounding/eval/renderer seams
    engine/      orchestration core (worker-agnostic process engine)
    evaluator/   identity-aware grounding/identity audit
    renderer/    structured contract -> machine artifact, one per artifact kind
    grounding/   external grounding authority (PI today)
    worker/      replaceable worker (qwen today, the only current worker)

The Phase-0 `change_agent` experiment that produced this substrate is retired; its full
history lives on branch `ca`.
"""

__version__ = "0.1.0"

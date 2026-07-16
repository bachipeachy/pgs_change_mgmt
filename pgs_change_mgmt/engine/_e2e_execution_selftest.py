"""PGS lifecycle regression — the womb-to-birth guard, now a thin wrapper over `validate`.

    construct → admit → execute the CR's declared acceptance scenario → observe → PASS

This test holds ZERO domain data. It materializes the frozen chain fixture into a throwaway dossier and
calls the generic `validation_service.validate(...)` — the same engine a user runs via
`pgs_change_mgmt.engine.lifecycle_cli validate --dossier blockchain/chain`. Payloads and expected results
live in the CR's governed `acceptance_scenario`, not here: this is a *lifecycle* regression, not a
*blockchain acceptance* test.

Heavier than the offline suite (a real admit + two runtime executions), so it is NOT part of
`verify_change_mgmt_engine.sh`. Run explicitly:

    PGS_WORKSPACE=/abs python -m pgs_change_mgmt.engine._e2e_execution_selftest
"""
from __future__ import annotations

import os
from pathlib import Path

from ._fixture import chain_dossier
from . import validation as V

WS = os.environ.get("PGS_WORKSPACE", "")


def main() -> int:
    assert WS, "set PGS_WORKSPACE"
    with chain_dossier() as chain:
        report = V.validate(chain, domain="blockchain", subdomain="chain", workspace=Path(WS))
    assert report.verdict == "PASS", f"validation FAILED: {report.to_dict()}"
    assert all(s.passed for s in report.steps), report.steps
    assert all(o.passed for o in report.observations), report.observations
    assert report.criteria and all(c.proven for c in report.criteria), report.criteria
    print(f"E2E LIFECYCLE REGRESSION OK ✓ — validate({report.subject}) = {report.verdict}; "
          f"scenario {report.scenario_code}; "
          f"{len(report.steps)} steps + {len(report.observations)} observations; "
          f"{len(report.criteria)} Acceptance-Intent criteria proven. "
          "Human seed → Acceptance Intent → Acceptance Scenario → Validation Report → (Promotion).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

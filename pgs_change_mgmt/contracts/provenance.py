"""provenance — the governed-inference vocabulary, admissibility rule, and Clarification Protocol.

Phase 1 of the Provenance Ratchet (doc/parkinglot/THE_PROVENANCE_RATCHET_V0.md). This module is
the single source of truth for two orthogonal axes every governed cell carries, plus the rule
that decides whether a cell may cross a stage boundary. It is pure foundation: it defines the
vocabulary and the predicate; wiring it into registers / the engine / the oracle is later phases.

The doctrine is **"no *undisposed* inference crosses a governance boundary"** — inference is
allowed; it just cannot be hidden. A cell is admissible iff it is a human truth, a re-resolved
snapshot fact, an *accepted* inference, or an answered clarification.

Two axes (both controlled vocabularies, both stored in a cell's `source_finding`):

  provenance  — where the value came from
  disposition — the recorded human concurrence

`SUPERSEDED` is deliberately NOT a disposition; it is a Governed-Fact-Log lifecycle state
(a later phase). `VERIFIED` is the S2 `belief_verification` *result* enum, unrelated to these.
"""

from __future__ import annotations

from dataclasses import dataclass

# ---- provenance: where a cell's value came from ----------------------------------------------
SEED = "SEED"            # a human business truth (cite CR seed §X)
GROUNDED = "GROUNDED"    # a snapshot fact, re-resolved via grounding at consume-time
INFERRED = "INFERRED"    # agent synthesis reasoned from grounded facts (matches S2 OBSERVED|INFERRED|OPEN)
CLARIFIED = "CLARIFIED"  # an answered clarification, folded back in
PROVENANCE_TYPES: tuple[str, ...] = (SEED, GROUNDED, INFERRED, CLARIFIED)

# ---- disposition: the recorded human concurrence ---------------------------------------------
ACCEPTED = "ACCEPTED"
REJECTED = "REJECTED"
PENDING = "PENDING"      # not yet dispositioned (the "unresolved" state)
DISPOSITIONS: tuple[str, ...] = (ACCEPTED, REJECTED, PENDING)

# ---- clarification routing (who can answer) + priority (does it block) ------------------------
HUMAN = "HUMAN"          # only the requester can answer
SNAPSHOT = "SNAPSHOT"    # discovery/grounding answers it
GOVERNANCE = "GOVERNANCE"  # a governance/topology decision
OWNERS: tuple[str, ...] = (HUMAN, SNAPSHOT, GOVERNANCE)

CRITICAL = "CRITICAL"    # halts the line individually until answered
IMPORTANT = "IMPORTANT"  # batched to the stage gate
OPTIONAL = "OPTIONAL"    # noted, non-blocking
PRIORITIES: tuple[str, ...] = (CRITICAL, IMPORTANT, OPTIONAL)

# A register row whose value is not yet known — a declared, governed hole (never blank, never
# silently inferred). Carried as the row's provenance/disposition marker until a clarification
# resolves it.
UNRESOLVED = "UNRESOLVED"


def is_admissible(provenance: str, disposition: str = PENDING) -> bool:
    """The cross-stage admissibility rule (the heart of governed inference):

        admissible ⇔  provenance ∈ {SEED, GROUNDED}
                   OR (provenance = INFERRED ∧ disposition = ACCEPTED)
                   OR  provenance = CLARIFIED

    Everything else — most importantly INFERRED + PENDING (an *undisposed* inference) — is
    inadmissible. An unknown provenance is inadmissible (fail closed)."""
    if provenance in (SEED, GROUNDED, CLARIFIED):
        return True
    if provenance == INFERRED:
        return disposition == ACCEPTED
    return False


@dataclass(frozen=True)
class Clarification:
    """A governed clarification — the unit by which an unresolved cell is surfaced for an answer.

    Not free-form chat: every field is structured so the request is routable (`owner`),
    triagable (`priority`), traceable (`raised_by_stage`), and resolvable (`resolution` +
    `disposition`). A `CRITICAL` clarification that is still `PENDING` blocks the line; others
    batch to the stage gate."""

    clarification_id: str            # stable id, e.g. "CL-007"
    raised_by_stage: str             # the stage that surfaced it (S1..S7)
    rationale: str                   # why it is being asked
    impact: str                      # what cannot proceed without it
    owner: str = HUMAN               # HUMAN | SNAPSHOT | GOVERNANCE
    priority: str = CRITICAL         # CRITICAL | IMPORTANT | OPTIONAL
    resolution: str | None = None    # the answer, once given
    disposition: str = PENDING       # ACCEPTED | REJECTED | PENDING

    @property
    def blocking(self) -> bool:
        """A CRITICAL, still-PENDING clarification halts the pipeline; nothing else does."""
        return self.priority == CRITICAL and self.disposition == PENDING

    @property
    def resolved(self) -> bool:
        return self.disposition in (ACCEPTED, REJECTED)

    def validate(self) -> list[str]:
        """Controlled-vocabulary check — returns the list of violations (empty ⇒ valid)."""
        errs: list[str] = []
        if self.owner not in OWNERS:
            errs.append(f"owner {self.owner!r} not in {list(OWNERS)}")
        if self.priority not in PRIORITIES:
            errs.append(f"priority {self.priority!r} not in {list(PRIORITIES)}")
        if self.disposition not in DISPOSITIONS:
            errs.append(f"disposition {self.disposition!r} not in {list(DISPOSITIONS)}")
        return errs


if __name__ == "__main__":   # admissibility truth table + clarification invariants
    # (SEED|GROUNDED) admissible regardless of disposition
    for p in (SEED, GROUNDED):
        for d in DISPOSITIONS:
            assert is_admissible(p, d), (p, d)
    # CLARIFIED admissible regardless of disposition
    for d in DISPOSITIONS:
        assert is_admissible(CLARIFIED, d), d
    # INFERRED admissible ONLY when ACCEPTED — the whole point
    assert is_admissible(INFERRED, ACCEPTED)
    assert not is_admissible(INFERRED, PENDING)    # the hidden-inference violation
    assert not is_admissible(INFERRED, REJECTED)
    # unknown provenance fails closed
    assert not is_admissible("GUESSED", ACCEPTED)
    # clarification: CRITICAL+PENDING blocks; others don't
    assert Clarification("CL-1", "1", "r", "i", priority=CRITICAL, disposition=PENDING).blocking
    assert not Clarification("CL-2", "1", "r", "i", priority=IMPORTANT, disposition=PENDING).blocking
    assert not Clarification("CL-3", "1", "r", "i", priority=CRITICAL, disposition=ACCEPTED).blocking
    assert not Clarification("CL-1", "1", "r", "i", owner="ROBOT").validate() == []
    print("provenance contract OK — admissibility truth table + Clarification invariants hold")
    print(f"  provenance:  {PROVENANCE_TYPES}")
    print(f"  disposition: {DISPOSITIONS}")
    print(f"  admissible ⇔ (SEED|GROUNDED) ∨ (INFERRED∧ACCEPTED) ∨ CLARIFIED")

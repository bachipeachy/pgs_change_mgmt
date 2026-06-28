# CSI Finding #001 — Four declared `GOVERNED_BY` relationships not preserved (TI_HTTP_*)

**Detected by:** `ASSERT_ROUNDTRIP_EQUIVALENCE` — Authority axis (Semantic Preservation Gate)
**Severity:** Semantic Preservation violation (authored governance intent erased)
**Status:** RESOLVED 2026-06-27
**First detected:** CSI v1, blockchain structure
**Resolution:** Compiler fix in `pgs_compiler/compiler/stages/s1_extract.py` `_extract_references` —
list-valued singular reference fields (notably `governed_by`) were silently dropped (only `str` was
handled), so the `GOVERNED_BY` edge was never emitted. Now both scalar and list values become
`REFERENCES` edges. After recompiling all three structures, blockchain Authority coverage is 100% and
every structure is a Release Candidate. The semantic oracle discovered this; no prior compiler stage
(syntax, governance, addressing, evidence integrity, `s8_verify` roundtrip) did.

## Statement

Four `TI_` (Transport Ingress) artifacts in the `blockchain` structure declare a `governed_by`
relationship to `fb.transport::CONSTITUTION_TRANSPORT_V0` in their canonical frontmatter, but the
compiler emits **no** corresponding `GOVERNED_BY` edge into the evidence graph. The nodes exist; the
authored governance edge does not. This violates the governing rule of the Authority axis:

> Derived semantic axes may **expand**, but they may not **erase** authored governance intent.

Affected artifacts:

- `blockchain::TI_HTTP_CREATE_WALLET_V0` → `fb.transport::CONSTITUTION_TRANSPORT_V0`
- `blockchain::TI_HTTP_REGISTER_ACTOR_V0` → `fb.transport::CONSTITUTION_TRANSPORT_V0`
- `blockchain::TI_HTTP_SUBMIT_TRANSACTION_V0` → `fb.transport::CONSTITUTION_TRANSPORT_V0`
- `blockchain::TI_HTTP_VERIFY_ACTOR_V0` → `fb.transport::CONSTITUTION_TRANSPORT_V0`

Authority coverage on `blockchain`: **98.7%** (4 erased of ~310 declared). `ai_governance` and
`platform` are at 100% — the finding is isolated to the `TI_` artifact kind in `blockchain`.

## Why this is evidence, not noise

The Semantic Equivalence Oracle reasons over compiler outputs only (evidence graph + canonical
frontmatter); it never reads authoring sources. The two representations are independently derived, so
a divergence is a genuine compiler behavior, not a parser artifact. No prior validation (syntax,
governance, addressing, evidence-graph integrity, `s8_verify` roundtrip) detected this — the semantic
oracle did. That is exactly what a semantic-preservation check is for.

## Likely cause (to investigate when this is picked up)

`TI_` (Transport Ingress) artifacts appear to have their `governed_by` declaration dropped during
graph construction — either TI governance is intended to be carried by a mechanism other than a
`GOVERNED_BY` edge, or the compiler's governance-edge emission does not cover the `TI_` kind. This is
a focused compiler-side investigation, to be done **after** CSI v1 is locked, so the verification
system drives the compiler fix rather than being entangled with it.

## Reproduce

```bash
export PGS_WORKSPACE=/abs/path/to/pgs_workspace
python -m pgs_change_mgmt.engine.semantic_preservation_gate --structure blockchain
```

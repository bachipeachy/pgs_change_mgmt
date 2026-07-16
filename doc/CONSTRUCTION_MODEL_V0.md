# Construction Model V0 — Doctrine + Specification

**Status:** The single conceptual reference for the Construction phase — **Part I (Doctrine)** = the
rationale and proven architecture; **Part II (Specification)** = the object model. The governing rules
live in `CONSTITUTION_CONSTRUCTION_V0` (`UNIQUELY_DETERMINED_OR_STOP`, `PROJECTION_COMPLETENESS`,
promotion law); an *implementation* of this model is the **Construction Compiler**
(`engine/construction_model.py`).
**Date:** 2026-07-02 (merged `CONSTRUCTION_DOCTRINE_V0` + `CONSTRUCTION_MODEL_V0` into one two-part doc).
**Naming:** spell out **Construction Model** (concept) and **Construction Compiler** (implementation);
if the graph needs an abbreviation use **CG**. **Never `CM`** — that is Change Management
(`PROMOTION_SEMANTICS_GOVERNED_BY_CM`).

The question is no longer *"can an LLM author protocol artifacts?"* nor even *"what is the minimum
governed specification under which builders are interchangeable?"* — it is *"is construction a reasoning
problem at all?"* **It is not.** Construction is deterministic compilation.

---
---

# PART I — DOCTRINE

## I.1 Construction Compiler Architecture (Proven)

**Validated in code (no LLM), CI-locked (`engine/_construction_model_selftest`).** The chain CC slice
runs this end-to-end:

```
Construction Projection
        ↓
Construction Graph (IR)
        ↓
Normalization
        ↓
Lowering            (expansion · propagation · derivation)
        ↓
Constraint Evaluation   ← the gap census
        ↓
Artifact Contract
        ↓
PAS Renderer
        ↓
Protocol Artifact
```

A **compiler, not a prompt**: the Construction Projection is *sufficient* to deterministically generate
protocol artifacts; the LLM is optional. A missing type is a **compiler failure** (`TYPED_PORT`
violation), not "the model didn't know."

**Two levels — do not conflate.** **Construction Model** = the conceptual architecture (this document).
**Construction Compiler** = an implementation of it. Naming them separately leaves room for alternative
implementations without changing the model.

**Separation-of-concerns invariant (enforced from now):** every Construction Compiler class has **zero
dependency on S1–S7** — only on the Construction Projection schema and the PAS backend, so a future
extraction (conceptually alongside `pgs_compiler`, change-management ending at the Construction
Projection) is a *file move*, not a redesign.

> **Version 1 is architecture-complete.** Remaining work — D4 (typed capability interfaces), then the
> other artifact families — is *completing coverage*, not discovering architecture.

## I.2 Design · Lowering · Serialization

S0–S7 define *what the system should be*; the Construction phase deterministically **lowers** that into
executable protocol artifacts; the markdown is one serialized representation. Intelligence belongs on
the **design** side; construction on the **compiler** side.

The pipeline, in the names it will keep (reserved vocabulary):

```
Construction Projection → Construction Graph → Lowering Engine → Artifact Contract → PAS Renderer → Protocol Artifact
```

- **Construction Projection** — the compiler-owned normalized representation lowered from. The **Build
  Sheet** is merely its human-readable rendering (as a source listing renders an AST). *The graph is the
  IR; the Build Sheet is one projection of it.*
- **Construction Graph** — nodes + attributed edges (Part II).
- **Lowering Engine** — runs the ordered Lowering Pipeline. It *lowers*; the renderer constructs.
- **Artifact Contract** — the per-artifact object handed to the renderer.
- **PAS Renderer** — formats an Artifact Contract and does **nothing else**: never infers, derives,
  expands, propagates, or validates.
- **Protocol Artifact** — the output; the *compiler* validates it.

**Three activities, by how many valid outcomes exist:** **Design** (many valid — Human + S1–S7) ·
**Lowering** (exactly one — Construction) · **Serialization** (encodes, creates none — Construction).
Construction is the parent; Lowering and Serialization are its two deterministic activities.

**Three transformation shapes.** **Expansion** *inserts* a governed default where the control-flow graph
is silent (information increases). **Propagation** *copies* a declared attribute along existing edges
(information constant; STOPs on gap/mismatch/ambiguity). **Derivation** *computes* an attribute from
existing structure. Each obeys `UNIQUELY_DETERMINED_OR_STOP`.

**The lowering analogy.** Exactly a compiler's *lowering*: high-level IR (the Construction Projection) →
lowering → low-level IR (the artifact). Lowering routinely inserts what was never authored — default
control flow, temporaries, labels, jump targets — and those belong to the compiler's lowering rules,
never the language spec. Nobody writes `goto next_line`; only branches are explicit.

**Owner hierarchy (stable):**

```
Human · Business Intent
  │
Design (S1–S7)                 — which solution (many valid)
  │
Execution Specification (S6b)  — topology · stores · bindings · entities · orchestration · capability contracts
  │
Construction (over the Construction Graph)
  ├─ Lowering        — expansion + propagation + derivation; annotate nodes/edges
  └─ Serialization   — encode the annotated graph (final step)
  │
Protocol Artifact  →  Compiler (admissibility)  →  Runtime
```

**Types belong to contracts, not to S6b.** A capability *contract* owns its complete typed interface;
S6b only introduces or references contracts. Reused capability types are joined from the snapshot; a new
capability's types come from constructing its contract — never a field bolted onto the composition.

**The decision procedure** (placement is mechanical): *is there exactly one constitutional answer?* —
yes → **Lowering** (a rule in the catalog); no → **Design** (owed upstream).

**Rule vs pass (governance terminology vs implementation).** The doctrine names **rules**
(`TYPE_PROPAGATION`, `BINDING_PROPAGATION`, …); the Construction Compiler implements **passes**
(`TypePropagationPass` / `type_propagation_pass`). One rule may have one or more pass implementations.
Doctrine describes rules; the compiler implements passes.

## I.3 Definition of Done — the CC family (D4 success criteria)

Finish **one** artifact family (CC) to 100% before generalizing. CC is complete when *all* hold —
**architectural** criteria, not implementation milestones:

1. Every capability contract declares a **complete typed interface**.
2. `TYPE_PROPAGATION` reaches a **fixed point**.
3. **Zero** `TYPED_PORT` violations remain.
4. **No inferred types** exist (every type is joined or propagated, never guessed).
5. Serialization succeeds with **no injected information**.
6. The generated CC **matches the PAS grammar** (compiles).
7. The **compiler is the sole authority** for typing.

Meeting these proves a further compiler property: *all semantic typing is governed, propagated, and
validated — never inferred.*

## I.4 Construction gates (single responsibility each)

| Gate | Validates | Owner |
|------|-----------|-------|
| Projection Fidelity | the **pipeline** — every projection carries the same governed information | `evaluator/projection_fidelity.py` |
| Construction Closure | the **specification** — no design decision left to the builder | `evaluator/build_sheet_oracle.py` |
| Structural Invention | the **build** — no design added beyond the spec | `evaluator/invention_oracle.py` |
| Convergence | builder **agreement** — independent builders agree | `evaluator/convergence.py` |
| Compiler / Runtime / Evidence | admissibility / execution / record | downstream |

Convergence measures *agreement*, not conformance; no single measure quietly owns architecture.

## I.5 Projection principles

- **Projection Completeness.** Every downstream stage consumes only declared structured projections; no
  stage recovers information by re-parsing narrative. Markdown is documentation, not input. (One fenced
  one-time *migration* reads markdown for pre-principle baselines; a migration is not a stage.)
- **Projection Fidelity.** A projection is valid only if `Projection(markdown) == Projection(JSON)` over
  the stage's emit-fields; differing ⇒ *invalid*, not merely incomplete. (The Phase-4 discovery: the
  chain handoffs carried ~25–40 % of their markdown's rows — a non-authoritative projection.)
- **Construction Reliability = Specification Completeness × Builder Abstention Fidelity.** Either factor
  at zero makes the product zero. Design is open; construction must converge.

## I.6 Authority, thesis, evidence

**The builder is never authoritative.** It produces an artifact; it does not get to say whether the
artifact conforms. Conformance is measured *externally* (invention, convergence, compiler admissibility)
and recorded as evidence independent of the builder — which is why builders are interchangeable, and why
a deterministic generator (the Construction Compiler) is just another "builder" behind the same gates.

**Thesis (as evidence carries it).** Construction is governed by the specification rather than by model
intelligence — supported across two independent local model families (Qwen, DeepSeek) on the chain
commit-cluster CCs. Not yet universal (three CCs, two families, one domain); the narrow statement is the
strong one. Worked evidence: both builders independently invented `block_id` and renamed `content_hash`
→ `hash` — the convergence signal that the Build Sheet *under-specified its field vocabulary* (exactly
what typed interfaces + `TYPE_PROPAGATION` now close, deterministically).

## I.7 Deferred (research, not architecture)

Injected-gap abstention benchmark (E7) · convergence matrix across builders/kinds (E6) · RegisterModel
unification (one in-memory model per stage renders both markdown and JSON, retiring markdown parsing).

---
---

# PART II — SPECIFICATION

## II.1 Principle

The Construction Model is **one typed, attributed, directed graph** over the whole Execution
Specification (WF · IN · CC · CT · CS · RB · EV · Store), built from the **Construction Projection**. An
instance is a **Construction Graph**. Nodes are **domain concepts, never files** — the serializer maps
concepts to artifacts as the *final* step. Every transformation does one thing: **annotate
node/edge/port attributes**, subject to declared **constraints**. No CC-boundary special case — an edge
is an edge.

## II.2 Lifecycle

```
Project  →  Normalize  →  Lower  →  Validate  →  Serialize
(build)     (canonicalize) (annotate) (evaluate    (concept → artifact, via PAS)
                                      constraints)
```

1. **Project** — build nodes, interfaces, ports from the Construction Projection (S6b/S7); set all
   **Design-owned** attributes.
2. **Normalize** — deterministic canonicalization (sort ports, order edges/IDs, expand aliases, canonical
   capability references). Everything after assumes canonical input, so **Lower** stays purely semantic.
3. **Lower** — the ordered Lowering Pipeline; each pass annotates one attribute class
   (uniquely-determined-or-leave-absent): expansion · propagation · derivation.
4. **Validate** — evaluate the declared **constraints**. The unsatisfied set **is** the gap census
   (every gap is `Projection Gap → Constraint → Violation`, never a special-case error). Validates the
   Model's own consistency — not protocol admissibility.
5. **Serialize** — project each constructible node's subgraph to an **Artifact Contract** and render it
   through the per-kind **PAS Renderer**. Invents nothing.

## II.3 Nodes

A node = `{ id, concept, attrs{}, interface? }`.

| concept | represents | constructible? | serializes to |
|---|---|---|---|
| `Capability` | a CT/CS being constructed | yes | CT.md / CS.md |
| `CapabilityReference` | a **reused** CT/CS (dependency) | no (read-only) | — |
| `CapabilityComposition` | a CC (contains Steps) | yes | CC.md |
| `Workflow` | a WF (graph of Composition/Intent) | yes | WF.md |
| `Intent` | an IN | yes | IN.md |
| `Binding` | an RB | yes | RB.md |
| `Event` | an EV | yes | EV.md |
| `Store` | an entity store | via STRUCTURE | STRUCTURE `entity_stores` |
| `Step` | an invocation of a Capability inside a Composition | — | CC pipeline rows |

`Capability`/`CapabilityComposition`/`Intent`/`CapabilityReference` expose an **Interface** (II.4). Only
constructible nodes serialize; a `CapabilityReference` exists for type/binding resolution but is never
built.

## II.4 Interface and Ports

The **Interface** is the first-class, typed contract surface a node exposes — the single type authority.

- **Interface** = `{ id, owner: NodeID, ports: [Port] }`
- **Port** = `{ id, name, direction: in|out, type, required: bool }`

A `CapabilityReference`'s Interface is **joined** (read-only) from the snapshot; a `Capability` /
`Composition` / `Intent` Interface is **constructed** (port `type`s are **Contract**-owned). A `Step`'s
ports **bind against** the invoked capability's Interface; `TYPE_PROPAGATION` copies types along that
binding. External-input types resolve up-graph to an `Intent` payload Interface — **the IN payload
schema is authoritative; no entity-model shortcut** (one type system).

## II.5 Edges

An edge = `{ id, role, from, to, attrs{} }`.

| role | from → to | attrs | owner |
|---|---|---|---|
| `CONTAINS` | Composition → Step; Workflow → node | `order` | Design |
| `INVOKES` | Step → Capability/Reference | — | Design |
| `DATAFLOW` | out-Port → in-Port | `binding`, `type`, … | Construction |
| `CONTROLFLOW` | node → node | `condition` (SUCCESS/FAILURE/DEFAULT/…) | Design + Construction |
| `ACCESSES` | Step → Store | `access`, `op` | Construction |

`CONTROLFLOW` carries a `condition`; the target is the endpoint. `DATAFLOW` is the primary abstraction —
future attributes (provenance, ownership, effects, security) attach here and propagate over the same edges.

**Persistence is a binding, not a port (store-read invariant).** A `CS` Step's store is resolved by
`STORE_JOIN` into an `ACCESSES` edge — from the step capability's `storage_type` + the `STRUCTURE` — never
from a consumed dataflow field. `TYPED_PORT` therefore never models persistence: a store read/write
declares **no** dataflow `consumes` for the store itself; it `produces` the read value (typed by its
capability contract), and a write targets the bound store. Naming a store in `consumes` is a category
error — the store has no producer, so `TYPE_PROPAGATION` (correctly) cannot type it and construction is
rejected `TYPED_PORT / GAP_DOSSIER`, never guessed. (Proven on `blockchain/chain` S8, 2026-07-03: the
`CS_MUTABLE_JSON` READ and `CS_APPENDONLY_JSONL` GET_ALL entry steps.)

## II.6 Stable identity

Every node/port/interface/edge has a stable, content-derived ID (diagnostics/provenance/traces attach by ID).

| object | ID scheme | example |
|---|---|---|
| Node (FQDN) | the FQDN | `blockchain::CC_COMMIT_BLOCK_CANONICAL_V0` |
| Step | `<compFQDN>#step:<n>` | `…CC_COMMIT_BLOCK_CANONICAL_V0#step:2` |
| Store | `store:<subdomain>:<name>` | `store:chain:chain_head` |
| Interface | `iface:<ownerNodeID>` | `iface:blockchain::CT_PURE_HASH_BLOCK_V0` |
| Port | `<nodeID>:<dir>:<name>` | `…#step:2:in:content_hash` |
| Edge | `<role>:<from>→<to>` | `DATAFLOW:…out:content_hash→…in:content_hash` |

## II.7 Attribute ownership + provenance

Three owners only:

| attribute | owner |
|---|---|
| node concepts/codes/purpose, `CONTAINS.order`, explicit `CONTROLFLOW.condition` | **Design** |
| Interface port `type` | **Contract** |
| `DATAFLOW.binding`, `DATAFLOW.type`, default `CONTROLFLOW`, `ACCESSES.store` | **Construction** |

Every attribute carries provenance `{ value, source, owner, confidence }`; absence = `value: null`,
adjudicated by constraints — never by the attribute. (Subsumes today's `FieldValue`.)

## II.8 Constraints (first-class)

Declared model invariants — where `UNIQUELY_DETERMINED_OR_STOP` becomes concrete. **Validate = evaluate
constraints; gap census = the unsatisfied set.** A constraint =
`{ id, selector, predicate, on_violation: GAP_class, evaluable_after: stage }`.

| constraint | predicate | encodes |
|---|---|---|
| `SINGLE_PRODUCER` | every in-Port has exactly one incoming `DATAFLOW` edge | binding unique-or-STOP |
| `TYPED_PORT` | every required in-Port has a non-null `type`, consistent with its producer | type unique-or-STOP |
| `SINGLE_SUCCESSOR` | exactly one `CONTROLFLOW` successor per `condition` | expansion (fan-out = branch = STOP) |
| `STORE_RESOLVED` | every CS `Step` has exactly one `ACCESSES` edge to an existing Store | store join |
| `INVOKES_EXISTS` | every `INVOKES` target node exists | structural |
| `ACYCLIC_DATAFLOW` | the `DATAFLOW` sub-graph has no cycles | structural |

A pass satisfies a constraint by *uniquely* determining the attribute; if it cannot, it leaves it null
and the constraint reports at Validate. **No pass may violate a constraint to make progress** — that is
invention.

## II.9 Transformations (the Lowering Pipeline)

The **Lowering Engine** runs a governed, ordered pipeline of passes. Doctrine names the **rule**; the
compiler implements the **pass** (e.g. rule `TYPE_PROPAGATION` → pass `TypePropagationPass`).

| # | rule | shape | annotates | constraint served |
|---|---|---|---|---|
| 1 | `DEFAULT_EXECUTION_EXPANSION` | expansion | `CONTROLFLOW` where silent | `SINGLE_SUCCESSOR` |
| 2 | `BINDING_PROPAGATION` | propagation | `DATAFLOW.binding` | `SINGLE_PRODUCER` |
| 3 | `TYPE_PROPAGATION` | propagation | `DATAFLOW.type` (from producer Interface) | `TYPED_PORT` |
| 4 | `STORE_JOIN` | join | `ACCESSES.store` | `STORE_RESOLVED` |
| 5 | `SURFACE_DERIVATION` | derivation | node outcome surface | — |

*Reserved (same engine):* `CAPABILITY_RESOLUTION`, `OWNERSHIP_PROPAGATION`, `PROVENANCE_PROPAGATION`,
`EFFECT_PROPAGATION`, `SECURITY_PROPAGATION`. The engine is **invariant** — new attributes add
rules + constraints over the same graph, never new engine code. Scheduling (one traversal / several /
fixed-point) is implementation, not doctrine. `SURFACE_DERIVATION` lives here, not in the renderer.

## II.10 Serialization (concept → artifact, via PAS)

The final, information-free step. Each constructible node's subgraph projects to an **Artifact Contract**
the per-kind **PAS Renderer** encodes — and *only* encodes. A node with any unsatisfied constraint is
**not serializable** (a gap).

| concept | renderer | output |
|---|---|---|
| `CapabilityComposition` | CC | CC.md |
| `Capability` (CT/CS) | CT/CS | CT.md / CS.md |
| `Workflow` · `Intent` · `Binding` · `Event` | WF · IN · RB · EV | WF/IN/RB/EV.md |

## II.11 Relationship to the current implementation

| today (`engine/build_sheet.py`) | Construction Model |
|---|---|
| `BuildSheetModel.part_a/part_b` | node **attributes** (+ provenance) |
| pipeline step rows | `Step` nodes + `CONTAINS`/`INVOKES`/`DATAFLOW` edges |
| `FieldValue{sources,confidence,status}` | per-attribute provenance |
| `build_sheet_oracle` asserts | `Validate` = evaluate constraints |
| D2 store join / D3 bindings (banked) | `STORE_JOIN` / `BINDING_PROPAGATION` passes |
| `render_markdown` | one branch of `Serialize` (the PAS) |

Implemented today in `engine/construction_model.py` (zero S1–S7 dependency).

## II.12 Deferred (not v0)

Provenance/effects/ownership/security propagation (same edges, new passes) · on-disk serialization of the
Model itself · full Workflow/Intent payload-Interface construction.

## Invariants (summary)

- One graph; **concepts, not files**; serialization last.
- Every object has a **stable ID**.
- **Types belong to Interfaces** (contracts); one type system.
- **Persistence is a binding, not a port** — a `CS` store access is an `ACCESSES` edge (Store Join, from `storage_type`), never a typed dataflow port; `TYPED_PORT` never models storage.
- Every attribute has **one owner** (Design | Contract | Construction) + provenance.
- **Constraints are declared**; Validate evaluates them; gap census = unsatisfied constraints.
- **Construction validates its own Model; the compiler validates the artifacts.**

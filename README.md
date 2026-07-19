# pgs_change_mgmt

**Governed SDLC change-management pipeline for Protocol-Governed Systems.**

Every change to a Protocol-Governed System (PGS) begins as a **Change Request (CR)** and is driven
through a governed, gated pipeline — from a plain-language problem statement to an **Authoring
Mandate** — producing a complete, reviewable **dossier** *before* any protocol artifact is written.

> *Intent declared. Design approved. Mandate issued. Artifacts authored.*

---

## Status — v0.8.0

Public debut in **PGS v0.5.0**; `pi` Protocol-Inspection surface wired in at **v0.5.1**.

**v0.8.0 — one CLI, four lifecycle verbs.** The whole change-management lifecycle is now driven by a
single executable — `pgs_change author → construct → validate → promote` — mapping to the four
user-visible phases (Design → Construction → Execution Validation → Promotion). The governance stages
(S1–S9) and compiler mechanics (build / admit / persist) are internal; `--stage` remains only as a
debug flag. **Stage 9 (Promotion) is now wired end-to-end** — `promote` copies the constructed finale
artifacts into the domain protocol-source registry and lets the compiler be the gate. See
[The `pgs_change` CLI](#the-pgs_change-cli--four-lifecycle-verbs). The CLI is a thin facade over the
existing engine modules (frozen contract); the internal package reorg is a post-release refactor.

**v0.6.1 — the all-structured pipeline.** Every dossier stage (1 → 7) is now a **structured
register document** — the worker emits register rows, a deterministic renderer owns the document,
and a **structural oracle** mechanically validates it (well-formed FQDNs, controlled vocabularies,
traceability, and cross-stage consistency such as "every mandate code traces to a Design-Intent
register") before a human ever reviews it. The dossier pipeline **ends at Stage 7** (the Authoring
Mandate); protocol-artifact authoring and the Stage 8 manifest happen *after* Gate 2 (see
[After Stage 7](#after-stage-7--author-compile-test-close)).

Each component repo versions independently (MAJOR.MINOR.PATCH); the authoritative version is each
repo's own `pyproject.toml`. There is no single PGS release version.

---

## What It Is

`pgs_change_mgmt` governs the **Change Request → Protocol Artifact** lifecycle in two tiers:

```
  ── DOSSIER TIER (this pipeline — `pgs_change author`) ─────────────────────────────────
  Stage 1   Change Request          classification + problem / outcome / known facts
  Stage 2   Domain Model            confirm the semantic model against the snapshot
  Stage 3   Analysis Loop           REUSE / EXTEND / AUTHOR_NEW decisions, by evidence
  Stage 4   Business Model          the canonical hub — consolidates Stages 1–3
  Stage 5   Business Intent (WHAT)  scope, invariants, actions, provisional codes
  Stage 6   Governance Intent (WHERE)  ownership, storage, cross-subdomain dependencies
  Stage 6b  Design Intent (HOW)     binding FQDNs assigned to every new artifact
  Stage 7   Authoring Mandate       the build sequence (topological sort of the design)
                          │
                          ▼   ══ Gate 2 — Mandate Approval ══
  ── AUTHORING TIER (after Gate 2) ──────────────────────────────────────────────────────
  author the .md protocol artifacts from the mandate  →  compiler governs admissibility
      →  runtime tests + trace verification  →  Stage 8 manifest populated  →  Stage 9 closure
```

**Two approval gates — not one per stage.** Stages run as a continuous, iterative session; any
prior-stage artifact may be amended as knowledge accumulates, until a gate closes.

- **Gate 1 — Design Approval (after Stage 6b):** the full dossier (Stages 1–6b) is reviewed as a
  body. Approval authorizes the Stage 7 Authoring Mandate.
- **Gate 2 — Mandate Approval (after Stage 7):** the mandate is reviewed. Approval authorizes
  protocol-artifact authoring. **No artifact is authored before Gate 2.** After it, Stages 1–7 lock.

No stage may be skipped. For simple CRs the two gates may collapse into one review session.

---

## How to Start: the CR Seed

A CR begins with a **seed** — the frozen human elicitation, stored as the Stage-1 input artifact:

```
change_mgmt/dossiers/[domain]/[subdomain]/1_input_elicitation_[subdomain]_v0.md
```

The seed stands in for the human↔agent conversation that would normally produce it (that
interactive elicitation is a separate concern; the seed is its frozen output). Stage 1 consumes the
seed and projects it into the governed `1_change_request` artifact. **To run a new CR, author a seed
at that path** describing the change in business language: what problem, what outcome, what is in
and out of scope, what is already known, and which CR type it is.

### CR Types — frame the seed

The first thing Stage 1 classifies is the **CR type**. Knowing it up front shapes the whole seed:

| CR Type | Use when… | Example |
|---|---|---|
| `NEW_SUBDOMAIN` | a brand-new capability area needing its own governance boundary | add a canonical `chain` ledger to the blockchain domain |
| `EXTEND_SUBDOMAIN` | adding capabilities to an existing subdomain | add a new workflow to `mempool` |
| `MODIFY` | changing the behavior or shape of existing artifacts | change a validation rule in an existing CC |
| `DEPRECATE` | retiring an artifact or capability | remove a superseded workflow |

A `NEW_SUBDOMAIN` CR carries the most: vocabulary, lifecycle states, events, invariants, and
authority boundaries — the semantic model Stage 2 will verify and the rest of the pipeline projects.

---

## CR Artifact Projection — and why you can start at any stage

Each stage emits a small, governed **projection** of the stages before it — the `gov_projection`
handoff. A downstream stage consumes **only the upstream fields it declares it needs** (its bounded
context), not the full prior documents. The Business Model (Stage 4) is the hub; the later stages
are *projections* of it, not independent re-derivations.

Two consequences make the pipeline pleasant to operate:

1. **Loose coupling.** Stages are joined only by these declared field handoffs, each **persisted to
   disk** (`dossiers/[domain]/[subdomain]/cr_ir/<stage>.json`). A stage never re-reads the whole
   history — only its declared upstream projections.
2. **Start (or resume) at any stage.** Because the handoffs are on disk, you can run a single stage
   on its own — `--stage 6b` — as long as its declared upstream handoffs exist. This lets you:
   regenerate one stage after review, resume mid-pipeline, or even **swap the worker model between
   stages**. Authority lives in the *artifact*, not the actor — a different worker can pick up
   mid-pipeline from the governed handoffs.

This is the same governance dividend the compiler gives at the artifact level, one tier up: bounded,
declared context instead of "the whole world."

---

## The `pgs_change` CLI — four lifecycle verbs

One executable drives the whole lifecycle. The user thinks in **phases**; the governance stages
(S1–S9) and the compiler mechanics (build / admit / persist) stay internal — `--stage` survives only
as a debug flag, never the public model.

| Verb | Phase | Produces |
|------|-------|----------|
| `pgs_change author` | S1–S7 (Design) | **CR-IR** — `--guided` switches from the automated worker to interactive export/import |
| `pgs_change construct` | S8 + Admission | **ADMITTED_UNVALIDATED** delta — internally runs build → admit |
| `pgs_change validate` | Execution Validation | **EXECUTION_VALIDATED** — runs the CR's acceptance scenario |
| `pgs_change promote` | S9 (Promotion) | **Production Baseline** — copies the finale artifacts to the domain source registry; the compiler is the gate |

```bash
pgs_change author    [--guided] --worker … --model … [--stage N]
pgs_change construct  --projection <cr_ir> --domain … --subdomain … [--persist DIR]
pgs_change validate   --dossier blockchain/chain
pgs_change promote    --dossier blockchain/chain --registry-root <domain-source-registry> [--from constructed] --confirm
```

From the workspace, `scripts/run_change_mgmt.sh` wraps this (sets `PGS_WORKSPACE` and the venv).
`pgs_change` is a **thin facade** — each verb forwards into the existing engine modules unchanged.
`python -m pgs_change_mgmt.engine.cli <verb>` works today; the `pgs_change` console script activates on
the next editable reinstall. `pgs_construct` remains a deprecated alias for `construct`.

---

## Running the Pipeline — `author` (Stages 1→7)

From the workspace (sets `PGS_WORKSPACE` and the venv for you):

```bash
cd pgs_workspace/scripts

# Full dossier pipeline (Stages 1→7)
./run_change_mgmt.sh author --worker qwen --model qwen3.5:latest

# A single stage (loads its upstream handoffs from disk)
./run_change_mgmt.sh author --worker qwen --model qwen3.5:latest --stage 6b

# An explicit subset
./run_change_mgmt.sh author --worker qwen --model qwen3.5:latest --stages 6b,7

# A stronger / different worker
./run_change_mgmt.sh author --worker qwen   --model qwen2.5-coder:32b
./run_change_mgmt.sh author --worker claude --model claude-opus-4-8     # needs ANTHROPIC_API_KEY
```

*(The older `run_change_mgmt_dossier.sh` / `run_change_mgmt_interactive.sh` shells still work as
deprecated forwarders to `run_change_mgmt.sh author` / `author --guided`.)*

`--worker` and `--model` are **required** — the model is always a conscious choice, never a silent
default. Each stage prints a live R/Y/G grounding stream and a per-stage figure of merit:

- **structured stages** report `governed` (the fields that cross to the next stage) and `audit`
  (this stage's own record) coverage — both must be clean for a 5/5;
- a dirty register (malformed FQDN, bad enum, missing traceability, cross-stage mismatch) drops the
  score and is named in the log. **The oracle catches it here, not three stages later.**

---

## Three Execution Modes — the Authoring Trifecta

The command above is the **Automated** mode. All three modes share one worker interface, one
validation path, one figure of merit — only the *transport* between a stage's governed prompt and
the actor changes. Authority never moves: the oracle, the schema, and the gates are identical.

| Mode | Transport | Worker | Cost | When |
|------|-----------|--------|------|------|
| **Automated** | in-loop tool calls | `OllamaWorker` / `ClaudeWorker` / `GeminiWorker` | API/compute | CI, batch, A/B |
| **Guided Authoring** | human paste (chat UI / a coding assistant with `pi`) | `InteractiveWorker` | zero API | long-form quality, human-in-loop |
| **Offline replay** | recorded `response.md` | `InteractiveWorker` | zero | deterministic regression |

**Guided Authoring Mode** exports a governed **Stage Package**, you author the response through any
conversational model, and PGS ingress-validates and imports it — identical downstream to Automated:

```bash
# 1. EXPORT — write the governed Stage Package for a stage (stamps the live snapshot hash)
pgs_change author --guided --seed blockchain_chain --stage 1 --export
#    → open stage_1/system_prompt.md + user_prompt.md in a chat LLM; ground each token in
#      stage_1/context/grounding_spec.json via `pi vocab search <TOKEN>`; paste the reply into
#      stage_1/response.md  (a 0-result is a FINAL answer — the artifact does not exist)

# 2. IMPORT — ingress-validate at the human mutation boundary, then run the engine for that stage
pgs_change author --guided --seed blockchain_chain --stage 1 --import \
    --model-label claude-code --diagnose
```

The **Stage Package** is a machine contract, not prose: its hashed `prompt_bundle.json` (a serialized
`PromptIR`) is the source of truth; the `.md` files are rendered views. The **InteractiveIngressValidator**
runs *before* the engine sees your paste — it rejects an undeclared register, a malformed row, an
ungrounded assertion, or an FQDN smuggled into a business-language column, so the human cannot become
an untyped compiler bypass. The accepted response carries **Human Mutation Boundary** provenance
(origin, prompt hash, model label) and, under `--diagnose`, an honest Worker Protocol Trace: grounding
happened in your session and is out-of-band, so the trace terminates at the boundary rather than
faking an in-loop failure.

> **The protocol is the system of record; automation is an optimization on top of it, not a
> prerequisite.** A human expert, a local model, a frontier API, or a coding assistant is just
> another worker conforming to the same governed contract.

---

## After Stage 7 — author, compile, test, close

The dossier pipeline stops at Stage 7 because Stage 7 is the last thing derivable from the dossier
alone. Everything after is **as-built reality**, produced by the authoring tier:

1. **Gate 2** approves the Authoring Mandate.
2. **Author** the protocol-artifact `.md` files (WF / IN / RB / CC / CT / EV / STRUCTURE) from the
   mandate's build order — codes copied verbatim from the Design Intent, never re-minted.
3. **Compile** them with `pgs_compiler` — the compiler governs admissibility (routing, contract
   closure, schema). This is the authoritative gate; a drafted artifact is not admissible until it
   compiles into the snapshot.
4. **Test** at runtime — execute the new workflows, verify the traces (correct decision, determinism).
5. **Stage 8 — Authoring Manifest:** created as a pre-authoring baseline at Stage 7 close, then
   **populated** with the as-built reality — approved deviations, as-designed-vs-as-built deltas,
   conformance results, and governed-evolution metrics. Run it with `--stage 8`.
6. **Stage 9 — CR Closure:** every PENDING section filled with real execution data, completion
   criteria met, manifest status → `APPROVED`. The CR is not closed until then.

So: **the dossier proves the design; the authoring tier proves the build.** The manifest is the
seam between them — which is why it is a *post-authoring* artifact, not a dossier stage.

### The Snapshot Admission Gate

When the protocol delta is produced by the **Construction Compiler** (the deterministic Stage-8
path) rather than hand-authored, steps 2–4 above are consolidated into one repeatable, non-mutating
gate that runs **before any implementation work**:

> *Can this protocol delta be admitted into a protocol snapshot?*

The gate forms a **Compilation Unit** and hands it to the real `pgs_compiler`:

```
Compilation Unit  =  Baseline Overlay  ∪  Generated Delta  ∪  Supplementary Artifacts
```

- **Baseline Overlay** — read-only copies of the owning repos' canonical registries.
- **Generated Delta** — the artifacts the Construction Compiler produced from the CR-IR.
- **Supplementary Artifacts** — artifacts that must travel with the unit but were not generated:
  reused libraries or shared cross-domain artifacts. The compiler is **origin-agnostic** — it never
  learns *why* an artifact is present. *(Historically this also covered a `construction_gap/` of
  families S8 could not yet render; the blockchain/chain CR closed that gap — S8 now renders all its
  families, so it admits with zero supplementary. See the S8 renderer taxonomy below.)*

```bash
pgs_change construct \
    --projection <dossier>/cr_ir [--include <supplementary_dir>] \
    --domain <domain> --subdomain <subdomain>
# → Construction Status : CONSTRUCTION COMPLETE      (verdict first)
# → Admission Status    : PASS                        (exit 0; 2 = rejected)
# → Completeness        : 16 / 16  (100%)
```

`construct` runs the two S8 mechanics as one verb — it emits the finale artifact set (to `--out`,
default `constructed/`, the input to `promote`) and then forms the Compilation Unit and runs this
admission gate. The underlying `construction_cli {build|validate|graph|explain|admit}` subcommands
remain for isolated use (e.g. the pure non-emitting `admit` gate).

The report **leads with the verdict, not the count**. Two distinct states:

- **Construction Status** — did S8 *generate* everything this CR needs? `CONSTRUCTION COMPLETE` iff no
  supplementary artifact is an `UNRENDERED_FAMILY`. This is the S8-maturity result: `0 supplementary` is
  not bookkeeping, it is *evidence* that the whole protocol delta was produced deterministically.
- **Admission Status** — does the Protocol Compiler *accept* the unit? `PASS` / `FAIL`.

Supplementary artifacts are **classified**, so a non-zero count is diagnostic: `UNRENDERED_FAMILY` (a real
construction gap — S8 can't render that family yet; counts against completeness), `EXTERNAL_LIBRARY` (a
reused cross-domain artifact; a legitimate dependency, excluded from the completeness score), or
`SHARED_BASELINE`. **Completeness** = `generated / (generated + unrendered_family)` — the KPI that read
14/16 (87.5%) before STRUCTURE landed, 15/16 (93.8%) after, and 16/16 (100%) once EV closed the gap.

- **Repeatable** — the delta is reconstructed from the CR-IR each run; nothing is CR-specific.
- **Zero-pollution** — assembled in a throwaway temp federation and torn down; `protocol_snapshot/`
  and the canonical repos are byte-identical before and after.
- **No implementations required** — admission is compile-time. A CT contract *declares* its
  `implementation.module`; the compiler records the reference but never imports it. Missing CT/CS
  implementations block Execution Validation (a later phase), not admission.

Supply supplementary artifacts with `--include DIR` (repeatable); each file is namespace-qualified by
the snapshot convention `<namespace>__<CODE>.md`, so it self-declares its FQDN and is placed by
ownership resolution — no per-CR wiring. Locked offline by `scripts/verify_change_mgmt_engine.sh` §14.

**Persisting the admitted unit** — add `--persist DIR` to write the admitted Compilation Unit to disk
as a **complete test-snapshot candidate** (an isolated full build; compiles every structure so the
delta rides inside a whole snapshot). The Implementation and Execution-Validation phases consume *this
exact snapshot* — the chain of custody is `Constructed Delta → Admitted Compilation Unit → Executed
Snapshot → Promoted Baseline`, with no recompilation at promotion.

```bash
pgs_change construct \
    --projection <dossier>/cr_ir [--include <supplementary_dir>] \
    --domain <domain> --subdomain <subdomain> --persist /abs/test_ws
# → Construction Status : CONSTRUCTION COMPLETE
# → Admission Status    : PASS
# → Snapshot Status     : ADMITTED_UNVALIDATED
```

The snapshot is marked **`ADMITTED_UNVALIDATED`**, never `VALID`: it is admissible at compile time, but
runtime conformance (`pi validate --strict`, `pgs_runtime run`) executes CT/CS *implementations*, which
admission does not require. Those checks run in the **Execution Validation** phase, after the missing
implementations are authored and `pgs build` marks the snapshot `VALID`. Zero-pollution: the whole build
happens under an isolated federation base; the canonical repos are untouched.

### CR Lifecycle — five states, all five now driven by a CLI verb

A change request moves through five **machine-distinguishable** states, each a stronger claim than the
last. These states *emerged from implementation* — they were not invented up front. Each transition is
enforced as a gate and driven by one `pgs_change` verb.

```
DRAFT
  ↓   author              → CR-IR
CONSTRUCTION_COMPLETE   ← S8 generated every artifact the CR needs (0 UNRENDERED_FAMILY)   [GATE ✓]  construct
  ↓   admission (Protocol Admission Certificate)
ADMITTED_UNVALIDATED    ← the Protocol Compiler accepts the Compilation Unit                [GATE ✓]  construct
  ↓   implementation + execution
EXECUTION_VALIDATED     ← CT/CS impls present; conformance + runtime pass                   [GATE ✓]  validate
  ↓   promotion
PROMOTED                ← finale artifacts copied to each owning source registry;
                          the compiler is the gate (compile → build → pi validate --strict) [GATE ✓]  promote
```

```bash
# Execution Validation — run the CR's acceptance scenario against the candidate snapshot
pgs_change validate --dossier blockchain/chain          # → Validation Status : PASS

# Promotion (S9) — gated on PASS evidence + explicit --confirm; rollback-all-on-red
pgs_change promote  --dossier blockchain/chain --confirm   # → Promotion COMPLETE
```

Promotion writes only to **protocol source** registries (never the read-only `protocol_snapshot/`); the
normal compiler build then regenerates the snapshot. It is **owner-aware**: each artifact is written to
the registry its owner governs, read from the **Placement Manifest** (`placement_manifest.json`, emitted
beside the finale set at construction). The manifest also carries a **`build_plan`**: construction
computes the rebuild *scope* once (a delta touching only its own domain rebuilds that domain's structure;
a **platform-touching** delta — one that introduces a domain-neutral artifact such as a reusable
`capability_transforms::` transform — rebuilds the whole platform via `compile --all-structures`).
Promotion *executes* the declared plan; it never infers whether a CR is "mixed" or decides how much to
rebuild. Compute once, declare once, consume everywhere. The build is **transactional**: the workspace
snapshot is backed up first and restored on any failure, so a red build leaves registries *and*
workspace byte-identical. A delta that spans repositories — e.g. a blockchain CR that
introduces a reusable `capability_transforms::` transform owned by `pgs_transforms` — routes each
artifact to its owning repo, then a single compile + build + `pi validate --strict` gates the whole set
(the build discovers every layer, so cross-repo references resolve); red rolls back across *all* touched
repos. Ownership is resolved once (Admission) and persisted — promotion **consumes** the decision, it
never recomputes it. `--registry-root` remains as an optional override of the destination root (e.g. a
throwaway dir for a dry-run); by default promotion routes by governed ownership. Because `promote`
rebuilds the whole workspace snapshot as its gate, expect the rebuilt snapshot to be part of the
release commit.

**Governance Impact — a CR discovers governance changes; it never makes them.** When a CR introduces
new protocol vocabulary (e.g. new capability transforms), those opcodes must be admitted by a governed
`allowed_capability_transforms` surface — a **governance act**. Under PGS doctrine a CR never performs
that act. Construction emits a **`governance_impact.json`** beside the finale set: a purely descriptive
enumeration of the surface additions this CR *requires* (which surface, which repo, which FQDNs) — zero
authority. The governance authority then decides — approve, reject, modify, defer — and, if approved,
adds the entries to the canonical surface separately. Promotion **gates** on it: `promote` refuses (before
touching anything) until the canonical surface already satisfies the impact, and it **never writes the
surface itself**. This closes the transformation story symmetrically — *construction discovers,
governance authorizes, promotion deploys* — and makes governance change itself protocol-governed rather
than an ambient side effect of deployment.

`ADMITTED_UNVALIDATED` is a **protocol lifecycle state, not merely a snapshot attribute**: it names a
delta that is construction-complete and compile-admitted but not yet execution-validated. The **Protocol
Admission Certificate** (the report above) is the artifact that certifies the transition
`CONSTRUCTION_COMPLETE → ADMITTED_UNVALIDATED`. The output of Change Management is precisely this: *an
admitted protocol delta* — everything downstream (implementation, execution, promotion) is a separate
concern. `Construction Status : CONSTRUCTION COMPLETE` is no longer an aspiration or a design principle;
it is a machine-verifiable property.

### S8 Renderer Taxonomy — three ways an artifact family is constructed

Every family the Construction Compiler emits is rendered by exactly one of three renderer classes. The
class determines what the CR-IR must carry: *construction is compilation, never interpretation.*

| Class | Families | What it needs from the CR-IR | On missing input |
|-------|----------|------------------------------|------------------|
| **Template** | STRUCTURE | Only the CR-specific table (store set); doctrine/boilerplate are renderer constants | n/a — always constructible |
| **Projection** | CC · WF · IN · RB · CT | Maps CR-IR registers directly onto artifact fields | reports a design gap |
| **Semantic** | EV *(ASSERT, …)* | Requires protocol semantics declared upstream; joins them | **fails** — never infers |

A **semantic** renderer is the strict one: it cannot manufacture its inputs. The EV renderer is a pure
join of two S6b registers and refuses to fabricate either half:

- **`events`** — the *protocol* viewpoint of an event: its payload schema (`field · type · required ·
  format · description`). Deliberately distinct from **S4 `events`**, the *business* viewpoint (why the
  event exists — its trigger and meaning). Two viewpoints, two registers, no conflation.
- **`execution_outputs`** — the emission *relationship*: `producer · output_kind · output_code`. General
  by design (`output_kind ∈ EVENT | STORE | ASSERT | …`) so emission scales without turning
  `execution_topology` into a kitchen sink. Emission originates at the producer; the event stays ignorant
  of who emits it (as a Store is ignorant of who writes it).

`EV artifact = events ⋈ execution_outputs (on ev_code == output_code)` — no inference, no heuristics.
When both halves are declared, the family is construction-complete; the `construction_gap/` directory
that previously hand-supplied it goes empty and disappears.

---

## Dossier-First Ontology

The primary unit is the **governed change dossier**, not the artifact type. All stage documents for
one CR live flat in the dossier directory, each filename prefixed with its stage number so the
directory lists in stage order:

```
change_mgmt/dossiers/[domain]/[subdomain]/
  1_input_elicitation_[subdomain]_v0.md     ← the seed (Stage-1 input)
  1_change_request_[subdomain]_v0.md
  2_domain_model_[subdomain]_v0.md
  3_analysis_loop_[subdomain]_v0.md
  4_business_model_[subdomain]_v0.md
  5_business_intent_[subdomain]_v0.md
  6_governance_intent_[subdomain]_v0.md
  6b_design_intent_[subdomain]_v0.md
  7_authoring_mandate_[subdomain]_v0.md
  8_authoring_manifest_[subdomain]_v0.md    ← produced after authoring closes
  cr_ir/<stage>.json                         ← the bounded gov_projection per stage
```

The stage-template set under `change_mgmt/templates/` uses the same stage-number prefixes
(`0_agent_context` … `8_authoring_manifest`).

---

## Where This Fits

| Repo | Role |
|------|------|
| `pgs_governance` | Constitutional governance, invariant enforcement, FB_CHANGE_MGMT constitution |
| `pgs_compiler` | Compiler pipeline; admissibility construction; the `pi` inspection surface |
| `pgs_transport` | Ingress/egress adapters |
| `pgs_runtime` | Execution engine |
| `pgs_capabilities` | Governed capability substrate |
| `pgs_blockchain` | Blockchain domain |
| `pgs_ai_governance` | AI governance domain |
| **`pgs_change_mgmt` ← here** | **Governed SDLC pipeline — Change Request to Authoring Mandate** |
| `pgs_workspace` | Entry point — snapshot + scripts + runtime execution |

---

## License

Apache-2.0. See LICENSE and NOTICE for details.

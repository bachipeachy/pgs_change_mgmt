"""Construction Model engine — the four-stage deterministic lowering of the Execution Specification
into protocol artifacts, per `doc/CONSTRUCTION_MODEL_V0.md` and `CONSTITUTION_CONSTRUCTION_V0`.

    Project  →  Normalize  →  Lower  →  Validate  →  Serialize
    (build)     (canonicalize) (annotate) (evaluate    (concept → artifact, via PAS)
                                          constraints)

The graph is the compiler IR; the Build Sheet is merely one serialized projection of it. `Normalize`
canonicalizes the graph (deterministic ordering/IDs) so `Lower` sees canonical input and stays purely
semantic. `Lower` (renamed from "construct" — everything here is construction; *lowering* is precise) is
the ordered Lowering Pipeline.

This is the compiler back end: it builds a **Construction Graph** (concepts, not files), runs the
ordered **Lowering Pipeline** (expansion + propagation + derivation transformations that annotate
nodes/edges), evaluates declared **constraints** (unsatisfied = the gap census), and serializes each
constructible concept via the per-kind PAS renderer. Every transformation obeys the primitive theorem
`UNIQUELY_DETERMINED_OR_STOP`: it annotates only where the answer is unique, else leaves it absent for a
constraint to report. No transformation guesses.

v0 scope: the CC vertical slice (CapabilityComposition + Step + Capability/Reference + Store), reusing
the S6b/S7 handoffs (`build_sheet.load_registers`) as the Construction Projection and the CC renderer as
the PAS. `build_sheet.py` remains the prior path; this module is proven alongside it.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..renderer import cc as cc_renderer          # the PAS backend (CC family)
from ..renderer import transform as ct_renderer   # the PAS backend (CT family)
from ..renderer.intent import INRenderer          # the PAS backend (IN family)
from ..renderer.workflow import WFRenderer         # the PAS backend (WF family)
from ..renderer.runtime_binding import RBRenderer   # the PAS backend (RB family)
from ..renderer.structure import StructureRenderer   # the PAS backend (STRUCTURE family)
from ..renderer.event import EVRenderer               # the PAS backend (EV family)
from . import ownership                                # governed owner (package · impl namespace)
from . import expression                               # shared binding-expression grammar (one grammar)

# --- Construction Projection schema utilities (self-contained: zero dependency on S1–S7 / build_sheet,
#     so the Construction Compiler extracts later as a file move, not a redesign) ---------------------
_CODE = re.compile(r"(?:[a-z][a-z0-9_.]*::)?((?:CC|CS|CT|IN|WF|RB|EV|AC|STRUCTURE|TI)_[A-Z0-9_]*_V\d+)")


def code_part(s: Any) -> str | None:
    m = _CODE.search(str(s or ""))
    return m.group(1) if m else None


def _fields(cell: Any) -> list[str]:
    return [t.strip() for t in str(cell or "").split(",") if t.strip() and t.strip() not in ("—", "-")]


def _typed_fields(spec: Any) -> dict[str, str]:
    """Parse a typed-field declaration into {name: type}. Accepts the markdown-authored string form
    (`"block:object, hash:string"`) or an already-structured dict (test/JSON handoff). Empty → {}."""
    if isinstance(spec, dict):
        return {str(k): str(v) for k, v in spec.items()}
    out: dict[str, str] = {}
    for part in str(spec or "").split(","):
        if ":" in part:
            n, t = part.split(":", 1)
            if n.strip() and n.strip() not in ("—", "-"):
                out[n.strip()] = t.strip()
    return out


def _parse_interface(spec: Any) -> dict[str, dict[str, str]]:
    """Parse a step's explicit **invocation** interface into {"inputs": {formal: source}, "outputs":
    {formal: cc_local}} — capability-kind-agnostic (CT and CS are the two users; the compiler never
    branches on kind). Accepts the markdown-authored string form
    (`"in: left=predecessor_hash, key=\"head\"; out: value=current_head"`) — the compact CR-IR cell,
    consistent with the `consumes`/`produces` string convention — or an already-structured dict.

    Both halves are keyed by the CAPABILITY-side formal name. An input `source` is either a CC-local
    field name (bound to its producer's JSONPath at lowering) or a double-quoted literal (`key=\"head\"`);
    source strings are stored verbatim and the quoting is interpreted at lowering. Empty cell → {}."""
    if isinstance(spec, dict):
        return spec
    s = str(spec or "").strip()
    if not s or s in ("—", "-"):
        return {}
    iface: dict[str, dict[str, str]] = {}
    for seg in s.split(";"):
        seg = seg.strip()
        if seg.lower().startswith("in:"):
            side, body = "inputs", seg[3:]
        elif seg.lower().startswith("out:"):
            side, body = "outputs", seg[4:]
        else:
            continue
        for pair in body.split(","):
            if "=" in pair:
                formal, local = pair.split("=", 1)
                if formal.strip() and local.strip():
                    iface.setdefault(side, {})[formal.strip()] = local.strip()
    return iface


def load_registers(handoff_dir: Path | str, stages: tuple[str, ...] = ("5", "6b", "7")) -> dict[str, list]:
    """Load the Construction Projection — merge the governed JSON handoffs into {register_id: [rows]}."""
    root = Path(handoff_dir)
    up: dict[str, list] = {}
    for stage in stages:
        p = root / f"{stage}.json"
        if not p.exists():
            raise FileNotFoundError(f"missing governed handoff: {p}")
        for rid, rows in json.loads(p.read_text()).items():
            if isinstance(rows, list):
                up[rid] = rows
    return up


def _rows(up: dict[str, list], rid: str) -> list[dict]:
    return [r for r in (up.get(rid) or []) if isinstance(r, dict)]


def _find(up: dict[str, list], rid: str, *code_cols: str, code: str) -> dict | None:
    for r in _rows(up, rid):
        for c in code_cols:
            if code_part(r.get(c, "")) == code:
                return r
    return None

# ---------------------------------------------------------------------------
# graph model  (spec §3–§7)
# ---------------------------------------------------------------------------


@dataclass
class Port:
    id: str
    name: str
    direction: str                 # in | out
    type: str | None = None        # annotated by TYPE_PROPAGATION
    required: bool = True


@dataclass
class Interface:
    id: str
    owner: str                     # NodeID
    ports: list[Port] = field(default_factory=list)

    def port(self, name: str, direction: str) -> Port | None:
        return next((p for p in self.ports if p.name == name and p.direction == direction), None)


@dataclass
class Node:
    id: str
    concept: str                   # Capability|CapabilityReference|CapabilityComposition|Step|Store|…
    attrs: dict[str, Any] = field(default_factory=dict)
    interface: Interface | None = None


@dataclass
class Edge:
    id: str
    role: str                      # CONTAINS|INVOKES|DATAFLOW|CONTROLFLOW|ACCESSES
    frm: str                       # NodeID or PortID
    to: str
    attrs: dict[str, Any] = field(default_factory=dict)


@dataclass
class Violation:
    constraint: str
    obj: str
    detail: str
    gap_class: str


@dataclass
class ConstructionGraph:
    domain: str
    subdomain: str
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    workspace: Any = None                                     # snapshot root — for per-operation contract joins
    external_types: dict[str, str] = field(default_factory=dict)  # IN-payload field→type (ingress contract)

    # -- construction helpers -------------------------------------------------
    def add(self, node: Node) -> Node:
        self.nodes[node.id] = node
        return node

    def link(self, role: str, frm: str, to: str, **attrs: Any) -> Edge:
        e = Edge(id=f"{role}:{frm}->{to}", role=role, frm=frm, to=to, attrs=dict(attrs))
        self.edges.append(e)
        return e

    def by_concept(self, concept: str) -> list[Node]:
        return [n for n in self.nodes.values() if n.concept == concept]

    def by_role(self, role: str) -> list[Edge]:
        return [e for e in self.edges if e.role == role]

    def out_edges(self, node_id: str, role: str) -> list[Edge]:
        return [e for e in self.edges if e.role == role and e.frm.split(":in:")[0].split(":out:")[0] == node_id
                or (e.role == role and e.frm == node_id)]

    def contained_steps(self, cc_id: str) -> list[Node]:
        ids = [e.to for e in self.edges if e.role == "CONTAINS" and e.frm == cc_id]
        steps = [self.nodes[i] for i in ids if i in self.nodes]
        return sorted(steps, key=lambda n: int(n.attrs.get("index", 0)))


# ---------------------------------------------------------------------------
# capability interface join  (Contract-owned types; spec §4)
# ---------------------------------------------------------------------------

_KIND_DIR = {"CT": "capability_transforms", "CS": "capability_side_effects"}


def load_capability_interface(workspace: Path, fqdn: str, *, operation: str | None = None) -> Interface | None:
    """Join a reused capability's typed Interface from the compiled snapshot.

    CT artifacts carry typed `inputs`/`outputs` maps. CS artifacts are operation-keyed with *untyped*
    name lists (`operations[OP].input/output`) — those ports get names but no type (an honest gap the
    TYPED_PORT constraint reports; CS contracts do not yet declare field types).
    """
    code = code_part(fqdn) or fqdn.split("::")[-1]
    prefix = code.split("_", 1)[0]
    sub = _KIND_DIR.get(prefix)
    if not sub:
        return None
    hits = sorted((Path(workspace) / "protocol_snapshot" / "artifacts" / sub).glob(f"*__{code}.json"))
    if not hits:
        return None
    core = json.loads(hits[0].read_text()).get("frontmatter", {}).get("core", {})
    iface = Interface(id=f"iface:{fqdn}", owner=fqdn)
    if prefix == "CT":
        for name, spec in (core.get("inputs") or {}).items():
            iface.ports.append(Port(f"{iface.id}:in:{name}", name, "in", (spec or {}).get("type")))
        for name, spec in (core.get("outputs") or {}).items():
            iface.ports.append(Port(f"{iface.id}:out:{name}", name, "out", (spec or {}).get("type")))
    else:  # CS — operation-keyed name lists; types from the contract's shared `field_types` map
        ftypes = core.get("field_types") or {}
        op = (core.get("operations") or {}).get(operation or "", {})
        # CS field optionality is not yet governed (operations declare bare name lists) — so a CS formal
        # input is NOT assumed required. The invocation oracle stays generic: requiredness is data on the
        # port (CT=required, CS=lax), never a kind-branch in the validator.
        for name in op.get("input", []):
            iface.ports.append(Port(f"{iface.id}:in:{name}", name, "in", ftypes.get(name), required=False))
        for name in op.get("output", []):
            iface.ports.append(Port(f"{iface.id}:out:{name}", name, "out", ftypes.get(name)))
    return iface


# ---------------------------------------------------------------------------
# STAGE 1 — Project  (build the graph from the Construction Projection)
# ---------------------------------------------------------------------------


def project(up: dict[str, list], *, domain: str, subdomain: str, workspace: Path) -> ConstructionGraph:
    g = ConstructionGraph(domain=domain, subdomain=subdomain, workspace=workspace)
    new_codes = {code_part(r.get("code", "")) for r in _rows(up, "new_artifacts")}

    for cc_row in [r for r in _rows(up, "cc_composition")]:
        pass  # (composition rows are grouped per CC below)

    cc_codes = list(dict.fromkeys(
        code_part(r.get("cc_code", "")) for r in _rows(up, "cc_composition") if code_part(r.get("cc_code", ""))))

    for cc_code in cc_codes:
        cc_fqdn = f"{domain}::{cc_code}"
        cc = g.add(Node(cc_fqdn, "CapabilityComposition",
                        attrs={"code": cc_code, "action": "NEW", "subdomain": subdomain}))
        cc.interface = Interface(id=f"iface:{cc_fqdn}", owner=cc_fqdn)

        steps = sorted(
            [r for r in _rows(up, "cc_composition") if code_part(r.get("cc_code", "")) == cc_code],
            key=lambda r: int(re.sub(r"[^0-9]", "", str(r.get("step", "0"))) or 0))

        for r in steps:
            idx = int(re.sub(r"[^0-9]", "", str(r.get("step", "0"))) or 0)
            cap_fqdn = r.get("capability", "")
            cap_code = code_part(cap_fqdn) or cap_fqdn.split("::")[-1]
            operation = r.get("operation", "")
            step_id = f"{cc_fqdn}#step:{idx}"
            step = g.add(Node(step_id, "Step",
                              attrs={"index": idx, "kind": r.get("kind", ""), "operation": operation,
                                     "capability": cap_fqdn,
                                     # Explicit invocation interface (S6b-authored): the single contract
                                     # binding this step to the invoked capability's formal parameters —
                                     # {"inputs": {ct_formal: cc_local}, "outputs": {ct_output: cc_local}}.
                                     "interface": _parse_interface(r.get("interface"))}))
            step.interface = Interface(id=f"iface:{step_id}", owner=step_id)
            for name in _fields(r.get("consumes", "")):
                step.interface.ports.append(Port(f"{step_id}:in:{name}", name, "in", None))
            for name in _fields(r.get("produces", "")):
                step.interface.ports.append(Port(f"{step_id}:out:{name}", name, "out", None))
            g.link("CONTAINS", cc_fqdn, step_id, order=idx)

            # the invoked capability: a constructed Capability (new) or a CapabilityReference (reused)
            if cap_fqdn not in g.nodes:
                concept = "Capability" if cap_code in new_codes else "CapabilityReference"
                cap = g.add(Node(cap_fqdn, concept, attrs={"code": cap_code, "kind": r.get("kind", "")}))
                if concept == "CapabilityReference":
                    cap.interface = load_capability_interface(workspace, cap_fqdn, operation=operation)
            g.link("INVOKES", step_id, cap_fqdn, operation=operation)

        # CC-level design-owned control flow (terminal routing) is attached for expansion to consume
        node = _find(up, "execution_topology", "node", code=cc_code)
        cc.attrs["result_routing"] = (node or {}).get("routing", "")

    # Store nodes (structure_stores)
    for s in _rows(up, "structure_stores"):
        name = s.get("store_name")
        if not name:
            continue
        sid = f"store:{subdomain}:{name}"
        if sid not in g.nodes:
            g.add(Node(sid, "Store", attrs={"store_name": name, "storage_type": s.get("storage_type"),
                                            "path": s.get("proposed_path"), "used_by": s.get("used_by", "")}))
    return g


def _derive_ct_machine(fqdn: str, code: str) -> dict[str, Any]:
    """Derive the CT machine block — *protocol realization*, the compiler's job. The author declares
    business intent; the compiler derives kind, purity, operation, and a DEFAULT implementation binding.
    The binding is a Runtime-Binding concern that may override this default: a capability exists before
    any Python does, so the default need not resolve to an existing module.

    The implementation module path is *materialized*, not interpreted: the physical layout (owning
    package · intra-package implementation namespace) is governed metadata resolved through the
    ownership service, so the compiler embeds zero knowledge of package organization."""
    owner = ownership.resolve(fqdn)
    return {
        "ct_kind": "atom", "ct_purity": "ct_pure", "operation": "COMPUTE",
        "implementation": {"module": owner.implementation_module(code), "callable": "execute"},
    }


def project_ct(g: ConstructionGraph, new_caps: list[dict]) -> None:
    """CT projector (definition-level) — realize each *new* `Capability` (CT) into a full
    CapabilityContract from its authored `new_capabilities` DECLARATION (business intent: code · purpose ·
    typed inputs · typed outputs). The declaration owns *semantics*; the Construction Compiler DERIVES the
    protocol realization (kind · purity · constitution · machine/implementation default). Kept separate
    from the CC (composition-level) projector: a CT *defines* a capability, a CC *composes* them. Reused
    capabilities (`CapabilityReference`) are dependencies, joined from their own contracts."""
    decls = {code_part(r.get("code", "")): r for r in (new_caps or [])}
    for cap in g.by_concept("Capability"):
        code = cap.attrs.get("code")
        d = decls.get(code)
        if not d:
            continue
        cap.attrs.setdefault("summary", d.get("purpose", code))
        cap.attrs["machine"] = _derive_ct_machine(cap.id, code)          # compiler derives protocol realization
        iface = Interface(id=f"iface:{cap.id}", owner=cap.id)
        for n, t in _typed_fields(d.get("inputs")).items():
            iface.ports.append(Port(f"{cap.id}:in:{n}", n, "in", t))
        for n, t in _typed_fields(d.get("outputs")).items():
            iface.ports.append(Port(f"{cap.id}:out:{n}", n, "out", t))
        cap.interface = iface


def project_in(g: ConstructionGraph, new_intents: list[dict]) -> None:
    """IN projector (definition-level) — realize each new `Intent` (ingress admission gate) from its
    authored `new_intents` declaration (business intent: code · purpose · workflow · typed payload). The
    author declares *which workflow the intent admits into* — a business design decision, like purpose.
    The compiler derives protocol realization only: the ACK/NACK admission surface, the intent
    constitution (`governed_by`), machine. Intents are standalone gates — not part of the CC dataflow
    graph — so they carry no ports and no `TYPED_PORT` obligation."""
    for r in (new_intents or []):
        code = code_part(r.get("code", ""))
        if not code:
            continue
        fqdn = r["code"] if "::" in str(r.get("code", "")) else f"{g.domain}::{code}"
        g.add(Node(fqdn, "Intent", attrs={
            "code": code, "summary": r.get("purpose", code),
            "workflow": code_part(r.get("workflow", "")) or str(r.get("workflow", "")),   # authored
            "inputs": _typed_fields(r.get("inputs")),
            "outcomes": ["ACK", "NACK"],                                                   # derived surface
        }))


def _parse_routing(routing: str) -> dict[str, str]:
    """`OUTCOME -> target, OUTCOME -> target` → {OUTCOME: target}. Targets are node names (codes/terminals)."""
    out: dict[str, str] = {}
    for part in str(routing or "").split(","):
        if "->" in part:
            oc, tgt = part.split("->", 1)
            out[oc.strip()] = code_part(tgt.strip()) or tgt.strip()
    return out


def project_wf(g: ConstructionGraph, up: dict[str, list]) -> None:
    """WF projector (topology-level) — realize each new `Workflow` from its authored business design: the
    orchestration graph (`execution_topology`), the RB binding (`rb_declarations`), and the summary
    (`new_artifacts`). The author declares the topology + bindings; the Construction Compiler derives the
    protocol realization: contract format, `governed_by`, `start_node` resolution, EXIT synthesis, machine.
    A WF references its IN/CC nodes (candidates) — the closed execution graph."""
    rbs = {code_part(r.get("binds_wf", "")): str(r.get("rb_code", "")).strip()   # FQDN — do not strip namespace
           for r in _rows(up, "rb_declarations")}
    summaries = {code_part(r.get("code", "")): r.get("capability", "")
                 for r in _rows(up, "new_artifacts") if str(r.get("family", "")).upper() == "WF"}
    wfs: dict[str, list[dict]] = {}
    for r in _rows(up, "execution_topology"):
        wf = code_part(r.get("workflow", ""))
        if wf:
            wfs.setdefault(wf, []).append(r)
    for wf, rows in wfs.items():
        nodes: list[dict] = []
        start = None
        referenced_exits: set[str] = set()
        for r in rows:
            nt = str(r.get("node_type", "")).upper()
            nname = code_part(r.get("node", "")) or str(r.get("node", ""))
            if nt in ("IN", "CC"):
                nxt = _parse_routing(r.get("routing", ""))
                if nt == "IN":
                    start = nname
                    # An IN emits its DERIVED admission surface (ACK/NACK), never SUCCESS — realize the
                    # authored admission-success target on the ACK edge and route NACK to an EXIT terminal.
                    admit_target = nxt.get("ACK") or nxt.get("SUCCESS")
                    nxt = {**({"ACK": admit_target} if admit_target else {}), "NACK": "EXIT"}
                nodes.append({"node": nname, "type": nt, "code": f"{g.domain}::{nname}", "next": nxt})
                referenced_exits |= {t for t in nxt.values() if t.startswith("EXIT")}
            elif nt.startswith("EXIT"):
                nodes.append({"node": nname, "type": "EXIT",
                              "reason": "COMPLETED" if "SUCCESS" in nname else "EXITED"})   # governed EXIT-reason enum
        declared = {n["node"] for n in nodes}
        for e in referenced_exits - declared:                    # synthesize referenced-but-undeclared terminals
            nodes.append({"node": e, "type": "EXIT", "reason": "COMPLETED" if "SUCCESS" in e else "EXITED"})
        g.add(Node(f"{g.domain}::{wf}", "Workflow", attrs={
            "code": wf, "summary": summaries.get(wf, wf),
            "runtime_binding": rbs.get(wf, ""),                  # authored WF→RB binding (rb_declarations)
            "start_node": start, "nodes": nodes,
        }))


def project_rb(g: ConstructionGraph, up: dict[str, list]) -> None:
    """RB projector (binding-level) — realize each new `RuntimeBinding` from its authored `rb_declarations`
    (business intent: which CS side-effects the workflow binds, and the storage structure). The author
    declares the bindings; the compiler derives protocol realization (contract format, `governed_by`,
    default policies, machine). An RB is a pure binding document — it names CS FQDNs + storage, and does
    not reference the WF back (WF→RB is one-directional), so it closes the execution cluster without a cycle."""
    summaries = {code_part(r.get("code", "")): r.get("capability", "")
                 for r in _rows(up, "new_artifacts") if str(r.get("family", "")).upper() == "RB"}
    for r in _rows(up, "rb_declarations"):
        rb = str(r.get("rb_code", "")).strip()
        code = code_part(rb)
        if not code:
            continue
        bindings = [{"capability": c.strip(), "policy": {}}
                    for c in str(r.get("cs_bindings", "")).split(",") if c.strip()]
        g.add(Node(rb if "::" in rb else f"{g.domain}::{code}", "RuntimeBinding", attrs={
            "code": code, "summary": summaries.get(code, code),
            "storage_structure": str(r.get("storage_structure", "")).strip(),
            "bindings": bindings,
        }))


def project_ev(g: ConstructionGraph, up: dict[str, list], *, domain: str) -> None:
    """EV projector (observation-level) — realize each new `Event` from its authored declaration. Unlike
    the projection families (CC/WF), an EV is a *semantic* concept: its constructible content — the payload
    schema and the emitter — is NOT derivable, it is declared upstream. `new_artifacts` (family=EV) names
    the event; S6b `events` carries its payload (the protocol viewpoint); S6b `execution_outputs` carries
    the emitter relationship (which producer emits it, joined on output_code == ev_code). The EV renderer
    is a pure join over the two — no inference. Absent payload/emitter is a gap the model reports (below),
    never a fabricated artifact."""
    for r in [r for r in _rows(up, "new_artifacts") if str(r.get("family", "")).upper() == "EV"]:
        code = code_part(r.get("code", ""))
        if not code:
            continue
        payload = [row for row in _rows(up, "events") if code_part(row.get("ev_code", "")) == code]
        emitters = [row.get("producer") for row in _rows(up, "execution_outputs")
                    if str(row.get("output_kind", "")).upper() == "EVENT"
                    and code_part(row.get("output_code", "")) == code]
        g.add(Node(f"{domain}::{code}", "Event", attrs={
            "code": code, "summary": r.get("capability", code),
            "payload": payload, "emitted_by": emitters,
        }))


def project_structure(g: ConstructionGraph, up: dict[str, list], *, domain: str, subdomain: str) -> None:
    """STRUCTURE projector (topology-level) — realize the subdomain's storage STRUCTURE from its authored
    declaration (`new_artifacts` family=STRUCTURE) over the already-projected `Store` nodes
    (`structure_stores`). The author declares the store set (names · storage types · paths); the
    Construction Compiler derives the protocol realization — the storage-root convention and the
    resolution/isolation/migration doctrine — in the STRUCTURE renderer. This is a *template* renderer:
    no upstream semantics beyond the store table are required, so STRUCTURE is construction-complete today."""
    struct_rows = [r for r in _rows(up, "new_artifacts") if str(r.get("family", "")).upper() == "STRUCTURE"]
    if not struct_rows:
        return
    stores = [{"name": s.attrs["store_name"], "storage_type": s.attrs.get("storage_type"),
               "path": s.attrs.get("path")} for s in g.by_concept("Store")]
    for r in struct_rows:
        code = code_part(r.get("code", ""))
        if not code:
            continue
        g.add(Node(f"{domain}::{code}", "StorageStructure", attrs={
            "code": code, "summary": r.get("capability", code),
            "domain": domain, "subdomain": subdomain, "stores": stores,
        }))


# ---------------------------------------------------------------------------
# STAGE 2–3 — Normalize + Lower  (the Lowering Pipeline; spec §9)
# ---------------------------------------------------------------------------


def binding_propagation_pass(g: ConstructionGraph) -> None:
    """Propagation — resolve each Step in-port to its unique producer out-port along the pipeline,
    creating a DATAFLOW edge. A field produced by no prior step is an external input (bound to the CC
    in-port). >1 prior producer ⇒ ambiguous ⇒ left unbound (SINGLE_PRODUCER reports)."""
    for cc in g.by_concept("CapabilityComposition"):
        produced: dict[str, list[str]] = {}       # field → [producer out-PortID] (prior steps only)
        for step in g.contained_steps(cc.id):
            for p in [p for p in step.interface.ports if p.direction == "in"]:
                producers = produced.get(p.name, [])
                if len(producers) == 1:
                    g.link("DATAFLOW", producers[0], p.id, binding=f"step:{producers[0]}")
                elif len(producers) == 0:
                    # external input: expose on the CC interface and bind port → CC in-port
                    if not cc.interface.port(p.name, "in"):
                        cc.interface.ports.append(Port(f"{cc.id}:in:{p.name}", p.name, "in", None))
                    g.link("DATAFLOW", f"{cc.id}:in:{p.name}", p.id, binding="input")
                # >1 → leave unbound (constraint SINGLE_PRODUCER reports)
            for p in [p for p in step.interface.ports if p.direction == "out"]:
                produced.setdefault(p.name, []).append(p.id)
        # CC out-port: result_status (the routed outcome surface)
        if not cc.interface.port("result_status", "out"):
            cc.interface.ports.append(Port(f"{cc.id}:out:result_status", "result_status", "out", "string"))


def store_join_pass(g: ConstructionGraph) -> None:
    """Join — a CS Step's unique Store: exactly one Store of the step capability's storage_type;
    when several share it, the one whose used_by names the CC disambiguates."""
    stores = g.by_concept("Store")
    for step in g.by_concept("Step"):
        if str(step.attrs.get("kind", "")).upper() != "CS":
            continue
        cc_id = step.id.split("#")[0]
        cc_code = code_part(cc_id)
        cap = step.attrs.get("capability", "")
        by_type = [s for s in stores if s.attrs.get("storage_type") == (code_part(cap) or "")
                   or code_part(str(s.attrs.get("storage_type"))) == code_part(cap)]
        names = list(dict.fromkeys(s.id for s in by_type))
        chosen = None
        if len(names) == 1:
            chosen = names[0]
        else:
            used = [s.id for s in by_type
                    if any(code_part(u) == cc_code for u in str(s.attrs.get("used_by", "")).split(","))]
            if len(set(used)) == 1:
                chosen = used[0]
        if chosen:
            g.link("ACCESSES", step.id, chosen, access="write", op=step.attrs.get("operation"))


_CONTROL_FIELDS = {"result_status"}   # control outputs, not data — excluded from data-output seeding


def _cap_data_out_type(g: ConstructionGraph, cap_fqdn: str, op: str | None) -> str | None:
    """The single DATA output type of a capability's operation, read from the capability's OWN contract
    interface — reused caps join their typed interface from the snapshot per operation, new caps carry
    theirs from the CT projector. The data output is the operation's outputs minus control fields
    (`result_status`); exactly one data output ⇒ the type its step's produced field takes. No invention."""
    cap = g.nodes.get(cap_fqdn)
    if cap is not None and cap.concept == "CapabilityReference":
        iface = load_capability_interface(g.workspace, cap_fqdn, operation=op)
    else:
        iface = cap.interface if cap is not None else None
    if iface is None:
        return None
    data = {p.type for p in iface.ports
            if p.direction == "out" and p.name not in _CONTROL_FIELDS and p.type}
    return next(iter(data)) if len(data) == 1 else None


def type_propagation_pass(g: ConstructionGraph) -> None:
    """Propagation — SEED every Step out-port from its invoked capability's declared DATA output type
    (read from the capability's OWN contract interface: reused caps from the snapshot per operation, new
    caps from the CT projector) and every external CC in-port from the declared external-input type, then
    COPY producer.type → consumer.type along DATAFLOW edges to a fixed point. Nothing is inferred: a type
    is either declared on a contract interface or propagated from one; an undeclared/unpropagated port
    stays absent and `TYPED_PORT` reports it. No guessing."""
    ext_in = g.external_types           # IN-payload field→type (the ingress contract owns arriving types)

    # 1. seed Step out-ports from the invoked capability's data-output type (per operation)
    for step in g.by_concept("Step"):
        t = _cap_data_out_type(g, step.attrs.get("capability", ""), step.attrs.get("operation"))
        if t:
            for p in [p for p in step.interface.ports if p.direction == "out" and not p.type]:
                p.type = t
    # 2. seed external CC in-ports (bound to "input") from declared external-input types
    for cc in g.by_concept("CapabilityComposition"):
        for p in [p for p in cc.interface.ports if p.direction == "in" and not p.type]:
            if p.name in ext_in:
                p.type = ext_in[p.name]
    # 3. propagate along DATAFLOW edges to a fixed point
    port_index = {p.id: p for n in g.nodes.values() if n.interface for p in n.interface.ports}
    changed = True
    while changed:
        changed = False
        for e in g.by_role("DATAFLOW"):
            producer, consumer = port_index.get(e.frm), port_index.get(e.to)
            if producer is not None and consumer is not None and producer.type and not consumer.type:
                consumer.type = producer.type
                e.attrs["type"] = producer.type
                changed = True


def execution_expansion_pass(g: ConstructionGraph) -> None:
    """Expansion — where intra-CC control flow is silent, insert the governed default: each step
    SUCCESS → the next step; the last step SUCCESS → exit; the CC's declared non-success outcomes →
    exit. A branch (an outcome with >1 legal target) is Design, owed by S6b (SINGLE_SUCCESSOR reports)."""
    for cc in g.by_concept("CapabilityComposition"):
        steps = g.contained_steps(cc.id)
        outcomes = _routing_outcomes(cc.attrs.get("result_routing", ""))
        for i, step in enumerate(steps):
            nxt = steps[i + 1].id if i + 1 < len(steps) else None
            g.link("CONTROLFLOW", step.id, nxt or "exit", condition="SUCCESS")
            for oc in [o for o in outcomes if o != "SUCCESS"]:
                g.link("CONTROLFLOW", step.id, "exit", condition=oc)
            step.attrs["on_result"] = {"SUCCESS": ("continue" if nxt else "exit"),
                                       **{o: "exit" for o in outcomes if o != "SUCCESS"}}


def surface_derivation_pass(g: ConstructionGraph) -> None:
    """Derivation — a node's outcome surface is the set of its CONTROLFLOW conditions (moved out of the
    renderer per renderer-knows-nothing)."""
    for step in g.by_concept("Step"):
        conds = [e.attrs.get("condition") for e in g.edges
                 if e.role == "CONTROLFLOW" and e.frm == step.id and e.attrs.get("condition")]
        step.attrs["result_surface"] = list(dict.fromkeys(conds))


def wf_binding_pass(g: ConstructionGraph) -> None:
    """Binding — map each WF CC node's external inputs to the workflow payload. A CC receives the fields
    its steps consume as `$.inputs.<field>`; the WF node supplies them by binding each to `$.payload.<field>`
    (the ingress payload the IN admits). Derived from the referenced CC's external in-ports (exposed by
    BINDING_PROPAGATION) — identity realization, zero invention."""
    for wf in g.by_concept("Workflow"):
        for node in wf.attrs.get("nodes", []):
            if node.get("type") != "CC":
                continue
            cc = g.nodes.get(node.get("code", ""))
            if cc is None or cc.interface is None:
                continue
            ext = [p.name for p in cc.interface.ports if p.direction == "in"]
            if ext:
                node["inputs"] = {name: f"$.payload.{name}" for name in ext}


def _routing_outcomes(routing: str) -> list[str]:
    outs = re.findall(r"([A-Z_]+)\s*->", routing or "")
    return list(dict.fromkeys(outs)) or ["SUCCESS"]


LOWERING_PIPELINE = [
    ("DEFAULT_EXECUTION_EXPANSION", execution_expansion_pass),
    ("BINDING_PROPAGATION", binding_propagation_pass),
    ("TYPE_PROPAGATION", type_propagation_pass),
    ("STORE_JOIN", store_join_pass),
    ("SURFACE_DERIVATION", surface_derivation_pass),
    ("WF_PAYLOAD_BINDING", wf_binding_pass),
]

# rule → the constraint it serves (compiler metadata; the CLI reports per-pass PASS/FAIL from this so
# the CLI itself stays logic-free).
PASS_CONSTRAINT: dict[str, str | None] = {
    "DEFAULT_EXECUTION_EXPANSION": "SINGLE_SUCCESSOR",
    "BINDING_PROPAGATION": "SINGLE_PRODUCER",
    "TYPE_PROPAGATION": "TYPED_PORT",
    "STORE_JOIN": "STORE_RESOLVED",
    "SURFACE_DERIVATION": None,
    "WF_PAYLOAD_BINDING": None,
}


def normalize(g: ConstructionGraph) -> None:
    """Deterministic canonicalization before lowering — sort each interface's ports (by direction then
    name), sort edges by id, so everything after Normalize assumes canonical input and Lowering stays
    purely semantic. Idempotent."""
    for n in g.nodes.values():
        if n.interface:
            n.interface.ports.sort(key=lambda p: (p.direction, p.name))
    g.edges.sort(key=lambda e: (e.role, e.id))


def lower(g: ConstructionGraph) -> None:
    """Graph Lowering — apply the ordered Lowering Pipeline; each transformation annotates the graph."""
    for _name, transform in LOWERING_PIPELINE:
        transform(g)


# ---------------------------------------------------------------------------
# STAGE 3 — Validate  (evaluate declared constraints; spec §8)
# ---------------------------------------------------------------------------


def validate(g: ConstructionGraph) -> list[Violation]:
    v: list[Violation] = []
    port_index = {p.id: p for n in g.nodes.values() if n.interface for p in n.interface.ports}
    dataflow_to: dict[str, list[str]] = {}
    for e in g.by_role("DATAFLOW"):
        dataflow_to.setdefault(e.to, []).append(e.frm)

    # SINGLE_PRODUCER + TYPED_PORT over every required Step in-port
    for step in g.by_concept("Step"):
        for p in [p for p in (step.interface.ports if step.interface else []) if p.direction == "in"]:
            producers = dataflow_to.get(p.id, [])
            if len(producers) != 1:
                v.append(Violation("SINGLE_PRODUCER", p.id,
                                   f"{len(producers)} producers", "GAP_DECISION" if producers else "GAP_DOSSIER"))
            if p.required and not p.type:
                v.append(Violation("TYPED_PORT", p.id, "no type resolved", "GAP_DOSSIER"))

    # STORE_RESOLVED — every CS Step has exactly one ACCESSES edge
    for step in g.by_concept("Step"):
        if str(step.attrs.get("kind", "")).upper() == "CS":
            n = len([e for e in g.by_role("ACCESSES") if e.frm == step.id])
            if n != 1:
                v.append(Violation("STORE_RESOLVED", step.id, f"{n} stores", "GAP_DOSSIER"))

    # SINGLE_SUCCESSOR — one CONTROLFLOW target per (node, condition)
    seen: dict[tuple[str, str], int] = {}
    for e in g.by_role("CONTROLFLOW"):
        k = (e.frm, e.attrs.get("condition"))
        seen[k] = seen.get(k, 0) + 1
    for (frm, cond), n in seen.items():
        if n > 1:
            v.append(Violation("SINGLE_SUCCESSOR", f"{frm}:{cond}", f"{n} targets", "GAP_DECISION"))

    # INVOKES_EXISTS
    for e in g.by_role("INVOKES"):
        if e.to not in g.nodes:
            v.append(Violation("INVOKES_EXISTS", e.to, "target node missing", "GAP_IMPLEMENTATION"))

    # INVOCATION_INTERFACE — every CC step's explicit invocation binding must satisfy the invoked
    # capability's declared interface, uniformly for any capability kind (CT, CS, …): every REQUIRED
    # formal input bound, each binding to a real formal from a real CC-local (or a literal), every
    # produced CC-local surfaced from a real declared output, no unknown/duplicate. Fully generic —
    # requiredness is interface data on the port (set by the loader), never a kind-branch here.
    for step in g.by_concept("Step"):
        cap = g.nodes.get(step.attrs.get("capability", ""))
        cap_iface = (load_capability_interface(g.workspace, step.attrs.get("capability", ""),
                                               operation=step.attrs.get("operation"))
                     if cap is not None and cap.concept == "CapabilityReference"
                     else (cap.interface if cap is not None else None))
        if cap_iface is None:
            continue
        in_ports = [p for p in cap_iface.ports if p.direction == "in"]
        decl_in = {p.name for p in in_ports}
        decl_out = {p.name for p in cap_iface.ports if p.direction == "out" and p.name not in _CONTROL_FIELDS}
        bound_in = (step.attrs.get("interface") or {}).get("inputs") or {}
        bound_out = (step.attrs.get("interface") or {}).get("outputs") or {}
        consumes = {p.name for p in step.interface.ports if p.direction == "in"}
        produces = {p.name for p in step.interface.ports if p.direction == "out"}
        for p in in_ports:                                       # every REQUIRED formal input bound
            if p.required and p.name not in bound_in:
                v.append(Violation("INVOCATION_INTERFACE", step.id, f"unbound required input {p.name!r}", "GAP_DOSSIER"))
        for formal, source in bound_in.items():                  # no unknown formal; reference to a real CC-local
            expr = expression.parse_compact(source)
            if formal not in decl_in:
                v.append(Violation("INVOCATION_INTERFACE", step.id, f"binding to unknown input {formal!r}", "GAP_DOSSIER"))
            elif isinstance(expr, expression.Reference) and expr.path not in consumes:
                v.append(Violation("INVOCATION_INTERFACE", step.id, f"input {formal!r} bound to unknown CC-local {source!r}", "GAP_DOSSIER"))
        if len(set(bound_in.values())) != len(bound_in):         # no duplicate input source
            v.append(Violation("INVOCATION_INTERFACE", step.id, "duplicate input binding source", "GAP_DOSSIER"))
        for formal, cc_local in bound_out.items():               # mapped output exists / targets a real CC-local
            if formal not in decl_out:
                v.append(Violation("INVOCATION_INTERFACE", step.id, f"binding from unknown output {formal!r}", "GAP_DOSSIER"))
            elif cc_local not in produces:
                v.append(Violation("INVOCATION_INTERFACE", step.id, f"output {formal!r} bound to unknown CC-local {cc_local!r}", "GAP_DOSSIER"))
        for pf in produces:                                      # every produced CC-local is mapped
            if pf not in bound_out.values():
                v.append(Violation("INVOCATION_INTERFACE", step.id, f"produced CC-local {pf!r} has no output binding", "GAP_DOSSIER"))
    return v


# ---------------------------------------------------------------------------
# STAGE 4 — Serialize  (concept → Artifact Contract → PAS; spec §10)
# ---------------------------------------------------------------------------


def _jsonpath(binding: str, producer_port_id: str) -> str:
    # Governed JSONPath convention (matches golden CC artifacts): external inputs are `$.inputs.<field>`;
    # a step output is `$.results.<step_id>.<field>` where <step_id> is the producing step's pipeline id
    # (s1, s2, …). The producing step and field are already declared in the contract — this is pure
    # representation (the renderer's job), not new meaning.
    if binding == "input":
        return "$.inputs." + producer_port_id.split(":in:")[-1]
    step_id = producer_port_id.split(":out:")[0]
    field_name = producer_port_id.split(":out:")[-1]
    step_no = step_id.split("#step:")[-1]
    return f"$.results.s{step_no}.{field_name}"


def _eval_binding(step: "Node", source: str, inedges: dict[str, list["Edge"]]) -> Any:
    """Evaluate an invocation input-binding expression to its lowered value, in the *construction*
    context: a `Literal` → its value; a `Reference` → the JSONPath of the named CC-local's producer
    (external CC input or a prior step's output) along the dataflow graph. Grammar is the shared
    `engine.expression` module (one grammar, many consumers); only the reference-resolution context is
    local here."""
    def _resolve_reference(cc_local: str) -> Any:
        port = step.interface.port(cc_local, "in") if step.interface else None
        edges = inedges.get(port.id) if port else None
        e = edges[0] if edges else None
        return _jsonpath(e.attrs.get("binding", "input"), e.frm) if e else None

    return expression.evaluate(expression.parse_compact(source), _resolve_reference)


def cc_contract(g: ConstructionGraph, cc: Node) -> dict[str, Any]:
    """Build the CC Artifact Contract from the fully-lowered subgraph (the object the PAS renders)."""
    port_index = {p.id: p for n in g.nodes.values() if n.interface for p in n.interface.ports}
    inedges: dict[str, list[Edge]] = {}
    for e in g.by_role("DATAFLOW"):
        inedges.setdefault(e.to, []).append(e)

    pipeline = []
    for step in g.contained_steps(cc.id):
        iface = step.attrs.get("interface") or {}
        if iface:
            # Materialize the invocation interface (validated by INVOCATION_INTERFACE) — capability-kind
            # agnostic: step inputs are keyed by the invoked capability's FORMAL parameter (CT or CS),
            # valued by the bound source (a prior/external CC-local's JSONPath, or a literal); each output
            # surfaces the capability's declared output field into its bound CC-local via the runtime's
            # `$.capability_result.<field>` convention. No name-identity assumption, no kind-branch.
            inputs = {formal: _eval_binding(step, source, inedges)
                      for formal, source in (iface.get("inputs") or {}).items()}
            outputs = {cc_local: f"$.capability_result.{formal}"
                       for formal, cc_local in (iface.get("outputs") or {}).items()}
        else:
            inputs = {}
            for p in [p for p in step.interface.ports if p.direction == "in"]:
                e = (inedges.get(p.id) or [None])[0]
                inputs[p.name] = _jsonpath(e.attrs.get("binding", "input"), e.frm) if e else None
            outputs = {p.name: {"from": "step"} for p in step.interface.ports if p.direction == "out"}
        access = next((a for a in g.by_role("ACCESSES") if a.frm == step.id), None)
        pipeline.append({
            "step": f"s{step.attrs['index']}", "kind": step.attrs["kind"],
            "capability": step.attrs["capability"], "op": step.attrs.get("operation", ""),
            "store": g.nodes[access.to].attrs["store_name"] if access else None,
            "inputs": inputs, "outputs": outputs,
            "on_result": step.attrs.get("on_result", {"SUCCESS": "exit"}),
        })
    return {
        "code": cc.attrs["code"], "summary": cc.attrs.get("purpose", cc.attrs["code"]),
        "pipeline": pipeline,
        "outputs": [{"name": "result_status", "type": "string"}],
        "extensions": {"subdomain": cc.attrs.get("subdomain", ""), "notes": []},
    }


def ct_contract(cap: Node) -> dict[str, Any]:
    """The CT Artifact Contract from a Capability node's typed Interface (the object the PAS renders)."""
    ports = cap.interface.ports if cap.interface else []
    return {
        "code": cap.attrs["code"], "summary": cap.attrs.get("summary", cap.attrs["code"]),
        "inputs": {p.name: p.type for p in ports if p.direction == "in"},
        "outputs": {p.name: p.type for p in ports if p.direction == "out"},
        "machine": cap.attrs.get("machine"),
    }


def in_contract(node: Node) -> dict[str, Any]:
    """The IN Artifact Contract from an Intent node (the object the PAS renders). `workflow` is authored;
    `outcomes` are the derived ACK/NACK admission surface."""
    return {
        "code": node.attrs["code"], "summary": node.attrs.get("summary", node.attrs["code"]),
        "workflow": node.attrs.get("workflow"),
        "inputs": [{"name": n, "type": t, "required": True} for n, t in (node.attrs.get("inputs") or {}).items()],
        "outcomes": [{"name": o} for o in node.attrs.get("outcomes", ["ACK", "NACK"])],
    }


def wf_contract(node: Node) -> dict[str, Any]:
    """The WF Artifact Contract from a Workflow node (the object the PAS renders)."""
    return {
        "code": node.attrs["code"], "summary": node.attrs.get("summary", node.attrs["code"]),
        "runtime_binding": node.attrs.get("runtime_binding"),
        "start_node": node.attrs.get("start_node"),
        "nodes": node.attrs.get("nodes", []),
    }


def rb_contract(node: Node) -> dict[str, Any]:
    """The RB Artifact Contract from a RuntimeBinding node (the object the PAS renders)."""
    return {
        "code": node.attrs["code"], "summary": node.attrs.get("summary", node.attrs["code"]),
        "storage_structure": node.attrs.get("storage_structure"),
        "bindings": node.attrs.get("bindings", []),
    }


def structure_contract(node: Node) -> dict[str, Any]:
    """The STRUCTURE Artifact Contract from a StorageStructure node (the object the PAS renders)."""
    return {
        "code": node.attrs["code"], "summary": node.attrs.get("summary", node.attrs["code"]),
        "domain": node.attrs.get("domain"), "subdomain": node.attrs.get("subdomain"),
        "stores": node.attrs.get("stores", []),
    }


def ev_contract(node: Node) -> dict[str, Any]:
    """The EV Artifact Contract from an Event node (the object the semantic renderer joins + renders)."""
    return {
        "code": node.attrs["code"], "summary": node.attrs.get("summary", node.attrs["code"]),
        "payload": node.attrs.get("payload", []),
        "emitted_by": node.attrs.get("emitted_by", []),
    }


# The artifact families the Construction Compiler (S8) renders today. The AUTHORITATIVE source is
# serialize() below — one renderer branch per family; keep this in lockstep. A supplementary artifact
# whose family is NOT in this set is an UNRENDERED_FAMILY construction gap (S8 cannot yet produce it);
# one whose family IS here was supplied for a different reason (reused / cross-domain). Consumed by the
# admission gate to classify supplementary artifacts and score construction completeness.
RENDERED_FAMILIES: frozenset[str] = frozenset({"CC", "CT", "IN", "WF", "RB", "STRUCTURE", "EV"})


def serialize(g: ConstructionGraph, violations: list[Violation]) -> dict[str, Any]:
    """Serialize each constructible node whose subgraph is constraint-clean, routing each concept to its
    per-kind PAS renderer. A node with any violation is not serializable (a gap). Returns
    {node_id: markdown | {"gap": [violations]}}."""
    out: dict[str, Any] = {}
    # CC family (composition) — gated on the CC subgraph's violations
    for cc in g.by_concept("CapabilityComposition"):
        step_ids = {s.id for s in g.contained_steps(cc.id)}
        cc_viols = [v for v in violations
                    if v.obj == cc.id or v.obj.split("#")[0] == cc.id
                    or v.obj.split(":in:")[0].split("#")[0] == cc.id
                    or any(v.obj.startswith(sid) for sid in step_ids)]
        out[cc.id] = {"gap": cc_viols} if cc_viols else cc_renderer.render(cc.attrs["code"], cc_contract(g, cc))
    # CT family (definition) — a new Capability with a complete typed Interface serializes
    for cap in g.by_concept("Capability"):
        if not (cap.interface and cap.interface.ports):
            out[cap.id] = {"gap": [Violation("TYPED_PORT", cap.id, "no typed interface", "GAP_DOSSIER")]}
        else:
            out[cap.id] = ct_renderer.render(cap.attrs["code"], ct_contract(cap))
    # IN family (ingress) — a standalone admission gate, rendered from its authored declaration
    for node in g.by_concept("Intent"):
        out[node.id] = INRenderer().render(in_contract(node))
    # WF family (topology) — the governed execution graph over its IN/CC nodes
    for node in g.by_concept("Workflow"):
        out[node.id] = WFRenderer().render(wf_contract(node))
    # RB family (binding) — the runtime binding document that closes the execution cluster
    for node in g.by_concept("RuntimeBinding"):
        out[node.id] = RBRenderer().render(rb_contract(node))
    # STRUCTURE family (storage topology) — a template renderer over the declared store set
    for node in g.by_concept("StorageStructure"):
        out[node.id] = StructureRenderer().render(structure_contract(node))
    # EV family (observation) — a SEMANTIC renderer: payload + emitter must be declared upstream, never
    # inferred. Absent semantics ⇒ a gap (not a fabricated artifact), mirroring the CT typed-interface gate.
    for node in g.by_concept("Event"):
        ev_viols = []
        if not node.attrs.get("payload"):
            ev_viols.append(Violation("EV_PAYLOAD_DECLARED", node.id,
                                      "no payload schema declared (S6b.events)", "GAP_DOSSIER"))
        if not node.attrs.get("emitted_by"):
            ev_viols.append(Violation("EV_EMITTER_DECLARED", node.id,
                                      "no emitter declared (S6b.execution_outputs)", "GAP_DOSSIER"))
        out[node.id] = {"gap": ev_viols} if ev_viols else EVRenderer().render(ev_contract(node))
    return out


# ---------------------------------------------------------------------------
# orchestrator
# ---------------------------------------------------------------------------


@dataclass
class Result:
    graph: ConstructionGraph
    violations: list[Violation]
    artifacts: dict[str, Any]


def build(handoff_dir: Path, *, domain: str, subdomain: str, workspace: Path) -> Result:
    up = load_registers(Path(handoff_dir))
    g = project(up, domain=domain, subdomain=subdomain, workspace=workspace)
    # ingress contract: external-input types are owned by the IN payloads (`new_intents`) — the union
    # of what arrives at each intent boundary. D4 is gone; nothing reads g.interfaces any more.
    g.external_types = {f: t for it in _rows(up, "new_intents")
                        for f, t in _typed_fields(it.get("inputs")).items()}
    project_ct(g, _rows(up, "new_capabilities"))                      # new caps from authored business intent
    project_in(g, _rows(up, "new_intents"))                           # new intents (ingress) from authored intent
    project_wf(g, up)                                                  # new workflows (topology) from authored design
    project_rb(g, up)                                                  # new runtime bindings from authored declarations
    project_structure(g, up, domain=domain, subdomain=subdomain)      # storage topology from authored store set
    project_ev(g, up, domain=domain)                                   # events (semantic) from authored payload + emitter
    normalize(g)
    lower(g)
    violations = validate(g)
    artifacts = serialize(g, violations)
    return Result(graph=g, violations=violations, artifacts=artifacts)

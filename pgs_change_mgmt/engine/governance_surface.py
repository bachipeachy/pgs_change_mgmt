"""Governance-surface seam — *discover* which CTs a construction needs the governance surface to admit.

When the Construction Compiler emits a new capability transform, that CT does not yet appear in the
governed `allowed_capability_transforms` surface (`INVARIANT_CT_SURFACE_CLOSED`). Declaring it legal is
a **governance act** — analogous to declaring a new opcode legal in an ISA spec — and under PGS
doctrine a CR never performs that act: **construction discovers, governance decides, promotion deploys
only what governance already approved.**

Two responsibilities live here, both *descriptive*, neither *normative*:
  * `surface_overlays` / `compose` — build the EPHEMERAL admission overlay: a read-only copy of the
    surface with the candidate CTs added, used only to prove the delta *would* be admissible once
    governance approves. It is never written to any canonical registry.
  * `impact` / `missing_approvals` — compute the **Governance Impact**: the exact surface additions this
    CR requires (`governance_impact.json`, emitted at construction) and, at promotion, which of them are
    still unapproved. Zero authority — construction reports *what must change*; the governance authority
    decides whether to approve, reject, modify, or defer; promotion refuses until the canonical surface
    already satisfies the impact. Promotion NEVER writes the surface.

The **Construction Compiler stays unaware of all this** — the front-end only produces contracts.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

# FQDN namespace → the governed CT-surface that must admit it. The surface may live in a *different*
# repo than the CT itself: reusable transforms (`capability_transforms::`) are admitted by the
# PLATFORM surface in `pgs_governance`, not by their own package. Declarative governance routing.
_SURFACE: dict[str, dict[str, str]] = {
    "blockchain": {
        "layer": "BLOCKCHAIN",
        "rel": "registry/assertions/ASSERT_CT_SURFACE_CLOSED_BLOCKCHAIN_V0.md",
    },
    "capability_transforms": {
        "layer": "GOVERNANCE",
        "rel": "registry/FB_TOPOLOGY/assertions/ASSERT_CT_SURFACE_CLOSED_V0.md",
    },
}

_LIST_KEY = "allowed_capability_transforms:"


@dataclass(frozen=True)
class SurfaceOverlay:
    package_dir: Path        # the importable package to mount (copytree) — e.g. …/pgs_governance
    rel: str                 # surface path relative to package_dir
    entries: tuple[str, ...] # candidate CT FQDNs to ensure declared


def is_ct(fqdn: str) -> bool:
    return fqdn.split("::", 1)[-1].startswith("CT_")


def surface_overlays(ct_fqdns: list[str]) -> list[SurfaceOverlay]:
    """Group candidate CTs by their governing surface and resolve that surface's owning package.
    Namespaces with no governed CT-surface are skipped (never guessed)."""
    from .ownership import _layer_resolver
    groups: dict[str, list[str]] = defaultdict(list)
    for fqdn in ct_fqdns:
        ns = fqdn.split("::", 1)[0]
        if ns in _SURFACE:
            groups[ns].append(fqdn)
    out: list[SurfaceOverlay] = []
    for ns, fqdns in groups.items():
        spec = _SURFACE[ns]
        pkg_dir = _layer_resolver().resolve_layer_repo_root(spec["layer"])
        out.append(SurfaceOverlay(pkg_dir, spec["rel"], tuple(sorted(set(fqdns)))))
    return out


def _scan_list(lines: list[str]) -> tuple[int, int, str, set[str]]:
    """Scan the `allowed_capability_transforms:` block: (key index, last-item index, item indent,
    declared FQDNs). Tolerates `# comment` group headers and blank lines interspersed among the items —
    the surface groups entries under comment headers, so the block is not a contiguous run of `- `."""
    key_ix = next((i for i, ln in enumerate(lines) if ln.strip() == _LIST_KEY), None)
    if key_ix is None:
        raise ValueError(f"surface has no {_LIST_KEY!r} block")
    indent, last_item, decl = None, key_ix, set()
    i = key_ix + 1
    while i < len(lines):
        ln, s = lines[i], lines[i].strip()
        if s == "":                                            # blank line inside the block
            i += 1; continue
        if ln[:1] in (" ", "\t") and (s.startswith("- ") or s.startswith("#")):
            if s.startswith("- "):                             # a declared entry
                if indent is None:
                    indent = ln[: len(ln) - len(ln.lstrip())]
                decl.add(s[2:].strip())
                last_item = i
            i += 1; continue                                   # entry or comment header — stay in block
        break                                                  # dedent / closing fence / next key
    return key_ix, last_item, indent or "  ", decl


def declared(surface_text: str) -> set[str]:
    """The FQDNs currently declared in a surface's `allowed_capability_transforms:` list."""
    return _scan_list(surface_text.splitlines())[3]


def compose(current: str, entries: tuple[str, ...] | list[str]) -> str:
    """Return `current` with each FQDN in `entries` present in the `allowed_capability_transforms:`
    list. Idempotent (already-declared entries are left alone); preserves indentation and inserts after
    the last existing item (so comment-grouped lists stay intact). Operates on the passed text only —
    the caller applies the result to the overlay copy, never to the canonical source."""
    lines = current.splitlines()
    _, last_item, indent, present = _scan_list(lines)
    additions = [f"{indent}- {e}" for e in entries if e not in present]
    if not additions:
        return current
    out = lines[: last_item + 1] + additions + lines[last_item + 1 :]
    return "\n".join(out) + ("\n" if current.endswith("\n") else "")


def impact(ct_fqdns: list[str]) -> dict:
    """The **Governance Impact** of a construction: the surface additions it requires, computed against
    the *canonical* surface (so only genuinely-undeclared CTs appear). Purely descriptive — it reports
    *what must change* for this CR to be promotable; it neither decides nor writes anything. An empty
    `ct_surface` means the governance surface already admits every CT (nothing for governance to do)."""
    changes = []
    for ov in surface_overlays(ct_fqdns):
        path = ov.package_dir / ov.rel
        have = declared(path.read_text()) if path.exists() else set()
        add = [fq for fq in ov.entries if fq not in have]
        if add:
            changes.append({"surface": Path(ov.rel).stem, "package": ov.package_dir.name,
                            "path": str(path), "add": add})
    return {"ct_surface": sorted(changes, key=lambda c: c["surface"])}


def missing_approvals(impact_doc: dict) -> list[str]:
    """Given a `governance_impact` document, the FQDNs it requires that the *canonical* surface does not
    yet declare. Empty ⇒ governance has approved the impact (promotion may proceed). Reads canonical
    surfaces only — never writes. This is the promotion-time governance gate."""
    changes = impact_doc.get("required_changes", impact_doc).get("ct_surface", [])
    missing: list[str] = []
    for ch in changes:
        p = Path(ch["path"])
        have = declared(p.read_text()) if p.exists() else set()
        missing += [fq for fq in ch.get("add", []) if fq not in have]
    return sorted(set(missing))

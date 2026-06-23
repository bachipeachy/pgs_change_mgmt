"""Identity-preserving artifact-reference evaluator.

Replaces the regex "not-found ⇒ hallucination" check (empirically falsified) with an
identity resolver + classifier over the authoritative vocabulary
(`protocol_snapshot/artifact_index/index.json`, 442 FQDNs).

Artifact Reference Error Taxonomy — only E is a hallucination:
  A. EXACT        — FQDN resolves as written            (valid reference)
  B. TYPO/ALIAS   — bare code ~matches a real code      (identity preserved; reference defect)
  C. WRONG_DOMAIN — bare code exists under another domain(identity preserved; namespace defect)
  D. PROPOSED_NEW — no identity, introduced as a NEW artifact (legit if at an allowed stage;
                    PREMATURE = purity defect if before stage 5)
  E. FABRICATION  — no identity anywhere, not a proposal (the only true hallucination)

Identity is preserved in A/B/C/D; only E is fabrication. The old evaluator collapsed
B, C, D, and E into one "hallucination" number — which produced false conclusions.
"""

from __future__ import annotations

import difflib
import json
import os
import re
from pathlib import Path

FQDN_RE = re.compile(r"\b[a-z_]+(?:\.[a-z_]+)*::[A-Z][A-Z0-9_]*_V\d+\b")
# A proposal is admissible from stage 5 (provisional codes); see purity ladder.
PROVISIONAL_FROM = 5
PROVISIONAL_MARKERS = ("provisional", "proposed", "propose ", "new artifact", "to be created",
                       "does not exist", "must exist", "would be", "new:", "(new", "gap")


def _index_path() -> Path:
    ws = os.environ.get("PGS_WORKSPACE", "")
    if not ws:
        raise RuntimeError(
            "PGS_WORKSPACE not set — the identity evaluator needs it to locate the artifact "
            "index. Set PGS_WORKSPACE to the absolute pgs_workspace path (fail-hard, no relative "
            "guess).")
    return Path(ws) / "protocol_snapshot" / "artifact_index" / "index.json"


def load_vocab() -> tuple[set[str], dict[str, set[str]], set[str]]:
    """Return (all_fqdns, code→{domains}, all_codes) from the artifact index."""
    d = json.loads(_index_path().read_text())["artifacts"]
    all_fqdns = set(d)
    code_to_domains: dict[str, set[str]] = {}
    for fq in all_fqdns:
        dom, code = fq.split("::", 1)
        code_to_domains.setdefault(code, set()).add(dom)
    return all_fqdns, code_to_domains, set(code_to_domains)


def classify(fqdn: str, vocab, *, stage_num: float | None = None,
             in_golden: bool = False, proposal_marked: bool = False) -> tuple[str, str]:
    """Classify one emitted FQDN by the A–E taxonomy. Returns (class, detail)."""
    all_fqdns, code_to_domains, all_codes = vocab
    if fqdn in all_fqdns:
        return "A_EXACT", "valid reference"
    dom, code = fqdn.split("::", 1) if "::" in fqdn else ("", fqdn)
    # C — exact code exists under a different domain → namespace defect, identity preserved
    if code in all_codes:
        return "C_WRONG_DOMAIN", f"real as {sorted(code_to_domains[code])[0]}::{code}"
    # B — close to a real code → typo/alias, identity (probably) preserved
    near = difflib.get_close_matches(code, all_codes, n=1, cutoff=0.88)
    if near:
        return "B_TYPO_ALIAS", f"~{near[0]} (real)"
    # no identity anywhere → D (proposal) or E (fabrication)
    allowed = stage_num is None or stage_num >= PROVISIONAL_FROM
    if in_golden or proposal_marked or allowed:
        tag = "legit" if (allowed or in_golden) else "premature(purity defect)"
        return "D_PROPOSED_NEW", tag
    return "E_FABRICATION", "no identity anywhere"


def audit_text(text: str, vocab, *, stage_num: float | None = None,
               golden_codes: set[str] | None = None) -> dict:
    golden_codes = golden_codes or set()
    out: dict[str, list[str]] = {k: [] for k in
                                 ("A_EXACT", "B_TYPO_ALIAS", "C_WRONG_DOMAIN",
                                  "D_PROPOSED_NEW", "E_FABRICATION")}
    detail = {}
    for fq in sorted(set(FQDN_RE.findall(text))):
        code = fq.split("::", 1)[-1]
        marked = any(m in ln.lower() for ln in text.splitlines() if fq in ln for m in PROVISIONAL_MARKERS)
        cls, det = classify(fq, vocab, stage_num=stage_num,
                            in_golden=(code in golden_codes), proposal_marked=marked)
        out[cls].append(fq); detail[fq] = (cls, det)
    return {"counts": {k: len(v) for k, v in out.items()}, "by_class": out, "detail": detail}


_STAGE_NUM = {"1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "6b": 6.5, "7": 7, "8": 8}


def _stage_of(path: Path) -> float | None:
    m = re.match(r"(\d+b?)_", path.name)
    return _STAGE_NUM.get(m.group(1)) if m else None


if __name__ == "__main__":
    import sys
    ws = os.environ.get("PGS_WORKSPACE", "")
    vocab = load_vocab()
    print(f"vocab: {len(vocab[0])} FQDNs, {len(vocab[2])} distinct codes\n")
    # audit each .md given as a dir or file arg (no default — this module is package code
    # and must not reach into experiment run dirs).
    args = sys.argv[1:]
    if not args:
        print("usage: python -m pgs_change_mgmt.evaluator.identity_audit <dir-or-file.md> ...")
        sys.exit(0)
    for a in args:
        p = Path(a)
        files = sorted(p.glob("*.md")) if p.is_dir() else [p]
        if not files:
            continue
        print(f"==== {p.name} ====")
        for f in files:
            r = audit_text(f.read_text(), vocab, stage_num=_stage_of(f))
            c = r["counts"]
            # spotlight non-A classes (the ones the old evaluator mislabeled)
            nonA = {k: v for k, v in c.items() if k != "A_EXACT" and v}
            print(f"  {f.name[:46]:46} A={c['A_EXACT']:2}  {nonA if nonA else '(all exact)'}")
            for cls in ("B_TYPO_ALIAS", "C_WRONG_DOMAIN", "E_FABRICATION"):
                for fq in r["by_class"][cls]:
                    print(f"        {cls}: {fq}  [{r['detail'][fq][1]}]")

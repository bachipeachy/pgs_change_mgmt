# Stage 3 — Analysis Loop: [domain] / [subdomain]
**Stage:** 3 — Analysis Loop
**CR:** change_request_[subdomain]_v0.md
**Iterations:** [N] ([saturated | in progress])
**Status:** DRAFT
**Feeds:** Stage 4 — Business Model

---

## Stage Inputs — Questions for the Human

*Most Stage 3 questions are answered by the agent reading PPS artifacts. Ask the human only what evidence cannot decide. Answer crisply; the right column states how each answer is used.*

| # | Question for the Human | How the Agent Uses the Answer (Intent) |
|---|------------------------|----------------------------------------|
| 1 | Where evidence supports both "extend existing subdomain" and "declare new subdomain" — which governance boundary do you intend? | Locks the Subdomain Placement Decision. This is a governance topology declaration only the human can make. |
| 2 | When a gap could be closed by reusing an existing capability with compromises, or by authoring a new one — what is your tolerance for each compromise? | Decides REUSE vs NEW in Consolidated Findings, which fixes the authoring scope and cost. |
| 3 | Any business policies (limits, privileged actors, initial conditions, monetary rules) not yet stated in Stages 1–2? | Recorded as evidence under the relevant question and carried into the Stage 4 Constraint Register with source "User clarification". |

**Agent execution rules for this stage:**
- Every question is answered by reading PPS artifacts directly — quote the evidence. No assertions without evidence.
- Impact analysis is mechanically generated, never hand-assembled: cite `pi topology impact <fqdn> --json` as the consumer-closure evidence for any artifact this CR touches (`pi artifact refs` for direct consumers, `pi store consumers` for storage). Inspection output carries snapshot authority; the review question becomes "is this generated list acceptable?", not "did you find everything?".
- Before any "What Must Be Authored" entry: search the snapshot inventory for an existing artifact that satisfies it (events, transforms, and side-effect substrates are the most commonly missed; `pi vocab search <term>` is the search surface). Record what was searched.
- New capabilities are named in business language here. Provisional codes appear in Stage 5; binding FQDNs in Stage 6b. Existing artifacts are cited by exact FQDN.
- The iteration count in the header MUST match the iteration sections actually present in this document.

---

## Iteration 1

*Each iteration resolves the open questions from Stage 2 or from the prior iteration by reading PPS artifacts directly. Answer each question with: the finding, the source evidence, and the resolution.*

### Q1 — [Question from Stage 2]

**Finding:** [One-sentence verdict.]

*[Evidence: what you read, what it says. Quote relevant fields if useful. No assertions without evidence.]*

**Resolution:** [What this finding implies for the authoring scope. Is the gap real? Does it require new artifacts? Does it expand the scope?]

**Answer:** [The definitive answer that feeds into the Business Model.]

---

### Q2 — [Question from Stage 2]

**Finding:** [One-sentence verdict.]

*[Evidence.]*

**Resolution:** [Implication for scope/design.]

**Answer:** [Definitive answer.]

---

*Add additional Q[n] sections as needed. If a question surfaces a new unknown, record it as Q[n+1] and resolve it in this iteration or the next.*

---

## Saturation Assessment

**Three-part saturation criterion:**

| Criterion | Status | Evidence |
|-----------|--------|----------|
| No unresolved CRITICAL gaps in the gap register | [SATISFIED \| NOT SATISFIED] | [what gap(s) remain, if any] |
| No open analyst questions | [SATISFIED \| NOT SATISFIED] | [what questions remain, if any] |
| No dependency expansion in the last review pass | [SATISFIED \| NOT SATISFIED] | [what new dependencies appeared, if any] |

**[Saturation achieved in N iterations. | NOT SATURATED — proceed to Iteration 2.]**

---

## Consolidated Findings

*Produced at saturation. This section is the authoritative input to Stage 4.*

### What Already Exists (fully reusable)

| Artifact | Status | Reuse |
|----------|--------|-------|
| [artifact or capability] | EXISTS | [REUSE — reason] |

### What Must Be Authored (new capabilities)

| Capability (business name) | Why New (and what existing artifacts were checked) |
|----------------------------|---------------------------------------------------|
| [business capability name — codes assigned in Stage 6b] | [why no existing artifact satisfies it; name the candidates examined] |

### Subdomain Placement Decision

**[NEW subdomain — [name] | EXTEND existing — [name]]**

*State the reasoning. A new subdomain is required when: the governance policy (CC configuration, tool registries, tier mappings, parameter constraints) is distinct from any existing subdomain's policy. Extending an existing subdomain is correct when: the capability is structurally the same and only the artifact FQDN binding differs.*

---

## Inputs to Stage 4 — Business Model

*Summarize the key facts that Stage 4 must incorporate.*

1. **[Fact category]:** [what was discovered]
2. **[Fact category]:** [what was discovered]
3. **[Fact category]:** [what was discovered]

*Every CRITICAL gap resolution, subdomain placement decision, and reuse vs. new-artifact decision must appear here. Stage 4 takes these as given — they are not re-litigated in Business Model.*

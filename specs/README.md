# Specifications

`specs/` holds Corytm's current normative truth — accepted behavioral contracts implementation must satisfy. A specification may describe behavior not yet implemented; the moment it exists here, it is current, not a draft.

## What belongs here

A SPEC represents an accepted behavioral contract intended to remain normative beyond a particular unit of work — durable repository truth, not a delivery checklist. Test: would this requirement still matter as repository truth after the originating work item is done? A later, unrelated Task needing to consult it is useful evidence of that, but not a prerequisite — a contract can earn a SPEC immediately at acceptance if it's clearly durable product/system behavior.

Most Feature/Task Acceptance Criteria stay local to their own work item and never graduate into a SPEC.

## What does not belong here

A Task, an implementation plan, a changelog, a design diary, an ADR, current-implementation documentation, an architecture justification, a backlog, or test-implementation detail. Unsettled product behavior does not belong here either — it stays in PMO/Task context, escalated under `CLAUDE.md` §5 if protected, and becomes a SPEC only once actually accepted.

## Granularity

One SPEC per coherent behavioral contract that can be reasoned about, implemented, validated, and evolved as a unit — never one SPEC for the whole project, never one per individual function, endpoint, or button. No `REQ-###` sub-numbering: the SPEC file itself is the traceable unit.

## Identifiers

Immutable, sequential: `SPEC-001`, `SPEC-002`, ... — no domain, hierarchy, or lifecycle encoded. Filename is ID-only (`specs/SPEC-001.md`); the title lives inside the file.

## Status

None. A SPEC's presence at HEAD is its status — current normative truth. There is no draft state: an unsettled requirement stays outside `specs/`, in PMO/Task context, until it's accepted. There is no separate historical copy either — Git owns textual history and previous versions, not this file.

## Evolution

A legitimate requirement change is a direct in-place edit — the current file is replaced, not appended to. Obsolete wording is not preserved for "historical completeness"; Git owns that history. The change needs the authority `CLAUDE.md` §5 already assigns: formalizing already-agreed behavior or fixing genuine ambiguity is autonomous; introducing behavior not already agreed is protected and needs explicit approval. If the change is substantial enough to need its own decision, record why in a separate ADR and reference it from `Related decisions`.

If code, tests, or docs contradict an accepted SPEC, the SPEC is not silently rewritten to match them. If two SPECs conflict, or a SPEC conflicts with an accepted ADR or `CLAUDE.md`, surface and resolve the conflict under normal repository governance — never invent a parallel resolution process.

## Format

Required: **ID**, **Title**, **Normative Behavior** — the `must` / `must not` / `should` statements, opening with enough framing to establish purpose and scope.

Conditional (omit when inapplicable — never "N/A"):
- **Boundaries/Scope** — only if not already clear from Normative Behavior.
- **Verification** — only if how to verify isn't obvious from the normative statements themselves.
- **Related decisions** — ADR IDs that explain or govern a constraint here, when useful. References only — the rationale itself lives in the ADR, not here. List as many as are genuinely relevant; don't accumulate them for their own sake. The referenced ADR has no obligation to reference back.
- **Related specs** — IDs of genuinely interdependent peer specs. Neither side is required to mirror the other.
- **Notes / open questions** — narrow and explicitly scoped only. Never a substitute for an actual decision.

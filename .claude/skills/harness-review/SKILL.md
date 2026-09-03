---
description: Audit consistency across the harness itself — CLAUDE.md, PMO/project docs, roadmap, decisions/specs usage, skills, and memory — for staleness, contradiction, misplaced duplication, or governance that no longer scales. Invoke explicitly on request, or opportunistically only when concrete evidence already surfaced during other work indicates a likely inconsistency. Never invoked by default on every Continue Corytm.
---

Ground truth is `CLAUDE.md` §4 (source-of-truth order and each artifact's exactly-one canonical home) and §11 (Knowledge & Harness Governance) — consult them directly; this skill sequences how to audit the repository against them, it never restates their content or adds new governance of its own.

## Trigger

- **Explicit**: the user requests a harness audit, periodic or otherwise.
- **Opportunistic**: only when concrete evidence already in view during other work indicates a likely inconsistency — a doc contradicting another doc the session is already reading, a memory entry contradicted by code just read, a PMO record referencing something that no longer exists. Never run speculatively "just in case," and never as a routine step of `state-reconciliation` or `next-work-selection` — those check project state, not harness rules.

## What it audits

- Consistency between canonical artifacts (`CLAUDE.md`, `docs/project/{plan,format,status,risks}.md`, `docs/product/roadmap/`, `decisions/`, `specs/`).
- Stale or contradictory governance/project-state statements — a canonical doc asserting something the current repository state has since made false.
- A rule duplicated in a location other than its one canonical home (`CLAUDE.md` §4), risking drift between the copies.
- A governance mechanism whose own scale assumptions no longer hold (a check that made sense at a smaller repository size and now under- or over-fires).
- Provisional knowledge in `.claude/memory/` that has been repeated or validated enough to promote into a canonical doc, skill, decision, or spec (`CLAUDE.md` §11) — and, conversely, memory or skills that are obsolete, superseded, or redundant with something now canonical.
- Whether `specs/`, `decisions/`, or the PMO structure itself are being used as `CLAUDE.md` §4 intends, or have drifted from it.

## Boundary

This is a harness audit, not general repository cleanup: it never reviews code quality, test coverage, or product content — those belong to code review, `testing-review`, and the CPO's own judgment respectively. It never reconciles a specific Feature/Task's project state — that is `state-reconciliation`. It never adjudicates a lifecycle transition — that is `lifecycle-review`. Scope each invocation to the specific inconsistency class under investigation; do not let a narrow trigger expand into an unscoped tour of the whole repository.

## Mechanism: proportional delegation

- A narrow, localized contradiction (two specific files disagreeing) — inspect directly, in the current session's own context.
- A broad, cross-artifact audit (checking every canonical doc against every other) — delegate the read-heavy discovery phase to the existing general-purpose or `Explore` agent, to protect the main context window, then reason over its findings directly. This introduces no new permanent agent type; it is the same dispatch mechanism already available for any other broad read-only investigation.

## What it may fix directly versus only propose

- **May fix directly**: an unambiguous, already-approved-elsewhere factual staleness — a stale path reference, a memory entry a canonical doc has since superseded — the same authority any session already has per `CLAUDE.md` §7 to fix an ambiguity whose intended meaning is already clear.
- **May only propose, for human review**: any new skill or agent; any `CLAUDE.md` wording change; any PMO-structure change; any source-of-truth reassignment between canonical artifacts; retiring or materially rewriting an existing skill or memory entry. Never silently applies a material governance redesign.

## Output

A findings list, most-significant first, each citing the specific canonical artifact(s) involved and whether it was fixed directly or is proposed for review — mirroring `ui-ux-review`'s own pass/gap-per-point format.

## Out of scope

Does not run by default on every `Continue Corytm` invocation. Does not become generic repository cleanup. Does not decide product direction, architecture, or testing policy — it may note that one of those documents looks stale or contradictory, but the actual correction belongs to whichever universe (`CLAUDE.md` §3) owns that artifact.

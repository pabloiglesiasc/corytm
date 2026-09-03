---
description: Establish what is actually true about Corytm's project state — Git/delivery state, exact-commit CI evidence, manual/live/external evidence, Feature/Epic/Milestone/Risk state — before trusting any recorded summary. Use at the start of autonomous-mode work, and whenever a session is about to rely on a PMO record's or status.md's stated status without having independently checked it this session.
---

Ground truth is `CLAUDE.md` §6 (Feature/Task status model and transitions) and `docs/project/format.md`'s State Transitions and Evidence Traceability sections — consult them directly; this skill only sequences how to verify against them, it never restates their content.

## Evidence-first semantics

Establish what is actually true before updating any PMO/status summary — never the reverse. A prior session's own narrative in `status.md` describes what was believed true when it was written; it is not itself evidence. Re-verify independently:

1. **Git state** — `git status`/`git log`: does the working tree match what the last session's handoff described? Was anything pushed since the last recorded entry?
2. **Exact-commit CI evidence** — for any `validating` Feature, `gh run view`/`gh api` matched by `headSha` against the exact delivery commit named in its Evidence field — never a run's mere existence, recency, or the user's report alone. A `conclusion` field beats an "in_progress" assumption; a downloaded log beats a green checkmark when the record's own history shows a prior false-positive on this exact surface.
3. **Manual/live/external evidence** — has a human-only confirmation (audible playback, real UI click-through, a `live_llm` evaluation) actually been reported since the record was last touched, and does the record reflect it yet?
4. **PMO state itself** — does every `active`/`validating`/`blocked` status among the current Milestone/Epic/Feature/Task/Risk records still match what (1)–(3) just established? A Task marked `active` whose acceptance criteria are visibly already met, or a Risk whose named CI run has since resolved, is stale until reconciled.

## Reconciling a discrepancy

When (1)–(4) surface a mismatch, reconcile the affected record's Status field per `docs/project/format.md`'s State Transitions before proceeding on top of it — a `validating` Feature whose evidence actually failed moves to `active`/`blocked` per that table; a Risk whose CI run resolved gets its real outcome recorded, not left "in_progress." Do this synchronously, as part of establishing truth, not deferred to a later "sync" step.

## The fast path

If reconciliation confirms an existing Active Feature has safe, executable work remaining — its own scope isn't exhausted, nothing about it is newly blocked, and nothing just reconciled above invalidates an assumption it depends on — the verdict is **continue that Feature directly**. Do not invoke `next-work-selection` merely because a session is starting; that skill exists for the moment a new Feature or workstream must actually be chosen, not as a routine portfolio review on every resumption.

## Output

A short statement covering: what was independently verified (and how — command/evidence cited, not asserted); what, if anything, was reconciled and why; and the verdict — either "continue the existing Active Feature" (fast path) or "a new Feature/workstream selection is needed" (hand off to `next-work-selection`).

## Out of scope

Does not decide *what* to work on next when the fast path doesn't apply — that is `next-work-selection`'s job entirely. Does not adjudicate a lifecycle-phase transition — that is `lifecycle-review`'s. Does not audit the harness's own rules for consistency — that is `harness-review`'s. Does not weaken any evidence requirement to reach a faster verdict: an unconfirmed CI run stays unconfirmed regardless of how inconvenient that is to the session's own momentum.

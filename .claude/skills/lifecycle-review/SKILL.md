---
description: Review whether a lifecycle-phase transition (e.g. Alpha to Beta) is genuinely justified. Invoke whenever a phase transition is being recommended, or a Milestone's outcome is being cited as evidence for one — not during ordinary Milestone close-out where phase exit isn't implicated.
---

Ground truth is `docs/project/plan.md`'s Lifecycle Model and Current Phase sections — consult them directly for the current phase's actual Objective and Exit criteria; this skill only sequences how to check a proposed transition against them, it never restates or reinterprets that document's own criteria. A lifecycle-definition change is a `CLAUDE.md` §5 Protected Product Decision regardless of this skill's outcome — this skill informs that proposal, it never substitutes for the human approval it requires.

## Trigger

Narrow and explicit: invoke when a session is about to recommend or apply a lifecycle-phase transition, or when a Milestone reaching `achieved` is being used as part of the case for one. Do not invoke on every Milestone close-out — most Milestones close without any phase-exit implication at all, and running this review then is exactly the kind of routine ceremony this skill is not for.

## The three checks

This project has already gotten a lifecycle-exit judgment wrong once, in practice, expensively: a Milestone's own Outcome being satisfied, plus a capability checklist looking complete, was treated as equivalent to the phase itself being done — rejected by the user as underspecified, requiring a multi-round product-governance consolidation to correct. Apply these three checks explicitly every time, not from memory of what "felt" satisfied:

1. **Milestone achievement ≠ lifecycle completion.** A Milestone reaching `achieved` proves only its own, narrower, stated Outcome. It is evidence toward a phase-exit case, never the case itself. Name explicitly which of the current phase's Exit criteria the Milestone's Outcome actually covers, and which it does not.
2. **A literal evidence checkbox ≠ the semantic product promise it stands for.** Check whether each named acceptance/exit item could be satisfied by something narrower than what the phase's own Objective was actually meant to guarantee (a single hardcoded proof standing in for the general capability; an offline-only proof standing in for a "real-time" requirement). If a checkbox's letter is satisfiable by a materially weaker case than its evident intent, the phase is not exited yet even though the box reads "done."
3. **Roadmap capability-list completion ≠ the phase's own qualitative exit gate.** `docs/product/roadmap/`'s current-phase file lists *which* capabilities belong to this phase; `docs/project/plan.md`'s Current Phase section separately names *qualitative* conditions the capability list alone does not guarantee (for Alpha: real-time behavior over offline proxies, aggregate credibility over an isolated proof, vertical integration over a backend-only mechanism). Confirm both independently — a fully-checked capability list does not by itself satisfy conditions plan.md states explicitly are not guaranteed by it.

## Output

Either: "exit criteria genuinely met" — with each of the current phase's named Exit criteria (both the roadmap-capability half and plan.md's own additional qualitative conditions) cited against specific, real evidence; or "not yet" — naming exactly which check above is unmet and what evidence would close it. Either way, this is a proposal surfaced to the user per `CLAUDE.md` §5, never a silent transition.

## Out of scope

Does not itself decide the transition — always a human Protected Decision. Does not audit the harness's own rules or documents for consistency beyond the specific phase-exit question at hand — that is `harness-review`'s job. Does not select what the next Milestone/Epic should be once a transition is decided — that is `next-work-selection`'s job, run afterward against the now-current phase.

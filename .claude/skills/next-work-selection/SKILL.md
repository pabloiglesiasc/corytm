---
description: Select the next Epic/Feature/workstream when autonomous work must actually choose one — after state-reconciliation's fast path doesn't apply. Applies docs/project/plan.md's Next-Work Selection Priority and the dependency-safety check for a Validating Feature. Use only when a new Feature or workstream genuinely needs selecting, not on every resumed session.
---

Ground truth is `docs/project/plan.md`'s Next-Work Selection Priority and Rolling-Wave Planning sections — consult them directly; this skill sequences how to apply that list and the dependency-safety check, it never restates or reorders the priorities themselves. `CLAUDE.md` §5 governs when the result requires a Protected Product Decision instead of a selection.

## Preconditions

Run only after `state-reconciliation` has established current truth and found its fast path does not apply (no existing Active Feature has safe, executable work remaining, or none is Active at all).

## Applying the priority list

Weigh `docs/project/plan.md`'s five priorities against real, cited evidence — never a numeric or weighted score. This project's own risk register already resists fake precision (likelihood/impact as `low`/`med`/`high` bands, never numbers); scoring "AI-native differentiation" or "user-visible value" on an invented scale would be the same mistake in a new place. State the comparison qualitatively: which candidate is better supported by which priority, and why, citing the actual document/record that supports it — the current Milestone's own Outcome; `docs/project/plan.md`'s current lifecycle phase and its exit requirements; `docs/product/roadmap/`'s current-phase file for unrealized capabilities (rolling-wave: an unmaterialized PMO record is never itself evidence that no work exists — the roadmap, not the existing Epic/Feature tree, is the backlog); open Risks (`docs/project/risks.md`); `docs/technical/architecture.md`'s Unresolved section; `docs/product/design.md`/strategy direction; dependency safety (below); and, where genuinely differentiating between otherwise-comparable candidates, user-visible value, architectural/risk reduction, downstream-unblocking value, AI-native differentiation, cross-surface/shared-core leverage, and implementation complexity/likely rework.

Rolling-wave planning is not optional flavor: the absence of an already-materialized Epic/Feature/Milestone record is never by itself a reason to conclude no safe work exists. Concluding that requires having actually checked the current-phase roadmap file for unrealized capabilities and weighed reconciling the current Milestone to `achieved` and shaping the next one — not merely exhausting whatever Epic/Feature records already exist. (This project has, once, gotten this specific step wrong in practice — treated "no ready PMO record" as sufficient to stop, when the roadmap itself still named unrealized current-phase capabilities. Do not repeat that shortcut.)

## The dependency-safety check

Apply this whenever a Validating Feature exists and a new Feature is being considered for Active.

Starting the new Feature is safe only when its own execution does not depend on the Validating Feature's pending evidence turning out correct — not merely on its code already existing, and not merely on building against or consuming a subsystem the Validating Feature also touches.

1. Check first whether the Validating Feature carries an open Risk (`docs/project/risks.md`) naming the specific surface still unconfirmed — strong evidence of where to look, not itself a verdict: the new Feature's work touching that named surface is an implementation dependency, and implementation dependency alone does not block.
2. Wait only when a plausible failure of that surface (or, absent a named Risk, a plausible failure of the pending evidence generally) could materially invalidate an assumption the new Feature relies on — an already-locally-validated command/event shape, function signature, lifecycle guarantee, ordering contract, persistence semantic, or other established interface or behavior — making the new Feature's own implementation unsafe or forcing its redesign.
3. When the plausible failure modes instead preserve those assumptions and would need only an internal or platform-specific corrective fix behind them — this project's own risk history (`RSK-002` through `RSK-015`) is almost entirely exactly this shape — proceed: some bounded downstream rework, if such a fix lands after the new Feature has started, is an accepted cost of proceeding, not evidence the check should have blocked it.
4. This check targets a real, specific invalidation risk, not shared codebase or subsystem proximity: proximity or mere consumption, without a plausible invalidating link, does not justify waiting — default to proceeding.
5. **Retroactively**: if the Validating Feature's evidence later fails for a reason implicating its own change, and that resolution turns out to actually invalidate an assumption the (now) Active Feature already built on, pause the Active Feature and reconcile it against the Validating Feature's corrective fix before continuing its implementation. (A Validating Feature's own status transition on evidence failure — `active`/`blocked`, the infrastructure-only-failure exemption — is canonical in `docs/project/format.md`'s State Transitions; this step is about the *other*, concurrently Active Feature.)

## Output

The selected next Epic/Feature with a short rationale citing which priorities and which specific evidence (roadmap entry, Risk ID, architecture Unresolved item, Milestone Outcome) drove the choice — or, when no Feature is both ready and unblocked by a Protected Product Decision, that decision proposed to the user with rationale instead of a selection.

## Out of scope

Does not verify whether recorded state is accurate — that is `state-reconciliation`'s job, assumed already done. Does not adjudicate a lifecycle-phase transition, even when the selection is "the Milestone's Outcome is satisfied, shape the next one" — hand that specific judgment to `lifecycle-review` when a phase exit is actually implicated. Does not turn the selected capability into a fully-shaped Feature record (scope/acceptance criteria/Task decomposition) beyond choosing it — that remains `CLAUDE.md` §7's own Plan step directly. Never introduces numeric scoring, a weighted rubric, or any other artificial-precision comparison mechanism.

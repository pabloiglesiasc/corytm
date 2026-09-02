# Project Plan

## Lifecycle Model

Pre-alpha → Alpha → Beta → Stable.

- **Pre-alpha — build the factory.** Establish repository foundation, governance, project management, engineering foundation, product/architecture baseline, CI, and development workflow. No Corytm production functionality is implemented.
- **Alpha — make Corytm work.** Establish the first real end-to-end product paths, e.g. user → desktop → Python core → Corytm Engine → Runtime → Native Audio Runtime → Tracktion Engine → sound, and user → Dorian → Corytm Engine → Runtime → sound.
- **Beta — make Corytm usable.** Product depth, UX, resiliency, plugins, persistence/recovery, performance, advanced Dorian capabilities, packaging/installers, operational maturity, and — per `docs/product/strategy.md`'s platform-expansion direction — beginning to validate Web/Creator workflows ahead of Mobile, without a rigid scope commitment here.
- **Stable — make Corytm dependable.** Compatibility, migrations, backwards compatibility, crash recovery, release guarantees, security/performance budgets, privacy/legal maturity, updates, support.

## Current Phase: Alpha

Objective: establish Corytm's first real end-to-end product paths — user → desktop → Python core → Corytm Engine → Runtime → Native Audio Runtime → Tracktion Engine → sound, and user → Dorian → Corytm Engine → Runtime → sound.
Exit criteria: Alpha is complete when both paths above are real and demonstrable end-to-end — a user can create or open a project and produce actual sound through the full stack via direct manual editing, and Dorian can perform a real semantic edit through the same governed application path with an observable effect on that sound — without yet claiming the product depth, UX polish, plugin ecosystem, or operational maturity Beta and Stable address.

## Previous Phase: Pre-alpha

Objective was to complete the repository, harness, governance, and PMO foundation. Exit criteria — a fresh Claude Code session, with no conversation history, entering the repository, understanding Corytm and its current state, determining the next approved work, loading the relevant context and procedures, executing that work under repository governance, validating it through the available quality system, synchronizing affected knowledge and project state, and identifying or recommending the next work — was demonstrated in practice by MS-001 (see `docs/project/milestones/MS-001.md`) and confirmed complete when the user approved the transition to Alpha.

## Rolling-Wave Planning

Only the current lifecycle phase, current Milestone, and current Feature get Feature/Task-level detail. Deeper phases and future milestones stay at objective level until they become current. No large upfront Task backlog.

## Milestone Principles

Milestones are transversal outcomes, not hierarchy levels, and are named for what a user or the system can do end-to-end — not for repository structure. Prefer outcomes such as "First Project" or "First Sound" over directory-completion goals such as "Build engine directory." (Illustrative naming examples only.)

## Milestone Overview

Current milestone and work state are tracked in `status.md` and the corresponding Milestone/Epic/Feature/Task records.

## Next-Work Selection Priority

Rolling-wave planning (above) means the PMO tree is not a closed backlog: the absence of an already-materialized Epic, Feature, or Milestone record is never by itself a reason to conclude no work exists. Prefer existing ready PMO work when it is strategically appropriate. When no suitable ready Feature exists, broaden the search to canonical product strategy (`docs/product/strategy.md`, `docs/product/business-model.md`), the current Milestone's own Outcome, architecture/technical state (`docs/technical/architecture.md`, including its Unresolved section), open risks (`docs/project/risks.md`), design direction (`docs/product/design.md`), and demonstrated product gaps — and create the next Epic/Feature just-in-time (`CLAUDE.md` §7) when that evidence supports it, subject to `CLAUDE.md` §5's Protected Decision gate. If the current Milestone's Outcome is already satisfied, or the best next work identified this way no longer belongs naturally inside it, evaluate reconciling that Milestone to `achieved` (`docs/project/format.md`) and shaping the next Milestone's objective, rather than waiting for a pre-existing record. A blocked thread inside the current Milestone does not by itself block unrelated strategic progress elsewhere in that Milestone or beyond it. Concluding no safe work exists is valid only after this broader search — not merely after exhausting already-recorded PMO children.

1. Work required for the current active Milestone
2. Ready work whose dependencies are satisfied
3. Work that unlocks other work
4. Work that reduces material risk or uncertainty
5. The largest coherent vertical increment that safely fits one session (`docs/project/format.md`'s Sizing)

Never by numeric ID order. Never select blocked work. Never select work that requires an unresolved protected decision (`CLAUDE.md` §5). When several Features are reasonable, recommend one with a brief reason.

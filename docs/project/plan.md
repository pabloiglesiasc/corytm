# Project Plan

## Lifecycle Model

Pre-alpha → Alpha → Beta → Stable.

- **Pre-alpha — build the factory.** Establish repository foundation, governance, project management, engineering foundation, product/architecture baseline, CI, and development workflow. No Corytm production functionality is implemented.
- **Alpha — make Corytm work.** Establish the first real end-to-end product paths, e.g. user → desktop → Python core → Corytm Engine → Runtime → Native Audio Runtime → Tracktion Engine → sound, and user → Dorian → Corytm Engine → Runtime → sound. (`docs/product/roadmap/alpha.md` names the concrete Desktop — Alpha capability set this requires.)
- **Beta — make Corytm usable.** Product depth, UX, resiliency, plugins, persistence/recovery, performance, advanced Dorian capabilities, packaging/installers, operational maturity, and — per `docs/product/strategy.md`'s platform-expansion direction — beginning to validate Web/Creator workflows ahead of Mobile, without a rigid scope commitment here. (`docs/product/roadmap/beta.md` names the concrete capability set.)
- **Stable — make Corytm dependable.** Compatibility, migrations, backwards compatibility, crash recovery, release guarantees, security/performance budgets, privacy/legal maturity, updates, support. (`docs/product/roadmap/stable.md` names the concrete capability set.)

## Current Phase: Alpha

Objective: establish Corytm's first real, credible end-to-end product foundation on Desktop — a professional DAW foundation capable of real-time manual editing and playback, and a Dorian agent that performs real semantic edits on that same project through a real Desktop product surface, both grounded in the shared Corytm Engine/Runtime core: user → desktop → Python core → Corytm Engine → Runtime → Native Audio Runtime → Tracktion Engine → sound; and user → Desktop Dorian UI → model → provider-neutral Dorian orchestration → trusted Engine operation → Runtime/native audio → observable/audible result.

Exit criteria: Alpha exits only when every capability `docs/product/roadmap/alpha.md` assigns `Desktop — Alpha` is realized and independently validated (this document's own evidence/quality bar — `docs/project/format.md`'s Evidence Traceability; real, independently-verified CI plus human confirmation where automation cannot reach), together with three conditions the roadmap's capability list alone does not guarantee:

- **Real-time audio is demonstrated, not merely offline rendering.** A deterministic offline render (materializing a project and writing a WAV file) proves the Engine/Runtime/Native Audio Runtime pipeline is wired correctly, but does not by itself satisfy this requirement — Alpha additionally requires genuine real-time audio-device playback (live transport, playhead, monitoring) exercised end to end.
- **The Desktop foundation is credible, not a hello-world proof.** Alpha does not require DAW feature parity with Ableton/FL Studio/etc. (`docs/product/strategy.md` §14), but does require `alpha.md`'s arrangement/editing, audio-clip, and mixer/recording capabilities realized in aggregate — not an isolated Add-Track/Add-Clip proof standing in for the whole.
- **Dorian's Desktop integration is vertical, not backend-only.** A trusted tool boundary and a live model call are necessary but not sufficient: Alpha requires a real Desktop-surfaced Dorian conversational/execution experience matching `alpha.md`'s Dorian — Desktop — Alpha capabilities, not a model/tool proof exercised only through automated tests or a single hardcoded proposal.

Alpha still does not claim Beta/Stable's product depth, UX polish, plugin ecosystem, or operational maturity — `docs/product/roadmap/` names exactly which capabilities those phases add (`beta.md`/`stable.md`), including MIDI and plugin hosting, both explicitly Beta.

## Previous Phase: Pre-alpha

Objective was to complete the repository, harness, governance, and PMO foundation. Exit criteria — a fresh Claude Code session, with no conversation history, entering the repository, understanding Corytm and its current state, determining the next approved work, loading the relevant context and procedures, executing that work under repository governance, validating it through the available quality system, synchronizing affected knowledge and project state, and identifying or recommending the next work — was demonstrated in practice by MS-001 (see `docs/project/milestones/MS-001.md`) and confirmed complete when the user approved the transition to Alpha.

## Rolling-Wave Planning

Only the current lifecycle phase, current Milestone, and current Feature get Feature/Task-level detail. Deeper phases and future milestones stay at objective level until they become current. No large upfront Task backlog.

Beta's and Stable's own Exit criteria will be written the same way Alpha's above now is — anchored to `docs/product/roadmap/`'s own `beta.md`/`stable.md` files plus that phase's own qualitative bar (`docs/product/strategy.md` §14) — once each becomes the current phase. Not written in full now, per this section's own principle. `docs/product/roadmap/`'s `beta.md`/`stable.md` files are the one exception this document makes to "objective level until current": per the user's explicit instruction, roadmap capability entries stay at approximately Feature-sized granularity through Stable even while dormant — only their own detailed scope/acceptance criteria (not their existence or granularity) waits for rolling-wave refinement.

## Milestone Principles

Milestones are transversal outcomes, not hierarchy levels, and are named for what a user or the system can do end-to-end — not for repository structure. Prefer outcomes such as "First Project" or "First Sound" over directory-completion goals such as "Build engine directory." (Illustrative naming examples only.)

## Milestone Overview

Current milestone and work state are tracked in `status.md` and the corresponding Milestone/Epic/Feature/Task records.

## Next-Work Selection Priority

Rolling-wave planning (above) means the PMO tree is not a closed backlog: the absence of an already-materialized Epic, Feature, or Milestone record is never by itself a reason to conclude no work exists. Prefer existing ready PMO work when it is strategically appropriate. When no suitable ready Feature exists, identify unrealized capabilities in `docs/product/roadmap/`'s current-phase file (e.g. `alpha.md` while Alpha is current) assigned to the current lifecycle phase and surface — the roadmap is the canonical answer to *which* capability belongs where, not a pre-created PMO backlog to walk in document order — and weigh them against the current Milestone's own Outcome, canonical product strategy (`docs/product/strategy.md`, `docs/product/business-model.md`), architecture/technical state (`docs/technical/architecture.md`, including its Unresolved section), open risks (`docs/project/risks.md`), design direction (`docs/product/design.md`), dependencies, and product leverage — then create the next Epic/Feature just-in-time (`CLAUDE.md` §7) when that evidence supports it, subject to `CLAUDE.md` §5's Protected Decision gate. Refine a roadmap capability's own terse entry into real scope/acceptance detail only as it approaches implementation, mirroring how Epic/Feature detail is filled in just-in-time — never ahead of need. If the current Milestone's Outcome is already satisfied, or the best next work identified this way no longer belongs naturally inside it, evaluate reconciling that Milestone to `achieved` (`docs/project/format.md`) and shaping the next Milestone's objective, rather than waiting for a pre-existing record. A blocked thread inside the current Milestone does not by itself block unrelated strategic progress elsewhere in that Milestone or beyond it. Concluding no safe work exists is valid only after this broader search — not merely after exhausting already-recorded PMO children, and not merely because the current phase's roadmap file has no more terse rows left to promote without checking whether the phase itself should reconcile toward its own exit.

1. Work required for the current active Milestone
2. Ready work whose dependencies are satisfied
3. Work that unlocks other work
4. Work that reduces material risk or uncertainty
5. The largest coherent vertical increment that safely fits one session (`docs/project/format.md`'s Sizing)

Never by numeric ID order. Never select blocked work. Never select work that requires an unresolved protected decision (`CLAUDE.md` §5). When several Features are reasonable, recommend one with a brief reason.

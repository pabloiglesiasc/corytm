# Corytm Product Strategy

Status: canonical, human-approved product direction — established 2026-09-01. This document is direction, not a finished specification, a roadmap, or a design system; it answers what Corytm is, for whom, across which surfaces, and why, at the product-strategy level `CLAUDE.md` §4 recognizes as canonical. It supersedes `docs/product/overview.md` (deleted; its content is absorbed below). `docs/product/business-model.md` carries the business/economic direction; `docs/product/market-intelligence.md` carries mutable competitive evidence. Neither this document nor its siblings decides implementation — `docs/technical/architecture.md`, accepted ADRs, and `specs/` govern that, and are not overridden by anything here.

Every statement below is either an **Approved Principle** (§17) — accepted, protected under `CLAUDE.md` §5 if it is a Protected Product Decision (§18) — or an explicitly marked **hypothesis/open question** (§19). Do not read illustrative detail elsewhere in this document as approved unless §17 says so.

## 1. Product Category & Thesis

Corytm's canonical category is: **Corytm is an AI-native music creation platform.**

Corytm as a whole is not defined as merely a DAW, merely an AI music generator, merely a Desktop application, or merely a wrapper around external foundation models.

**Corytm Desktop** is the professional agent-native DAW surface of the broader Corytm platform.

The platform-level product thesis: **different interfaces, same musical intelligence.** Corytm provides different levels of musical abstraction for different kinds of users while sharing one canonical musical representation, semantic capability layer, and Dorian intelligence layer.

Conceptually: user intent → Dorian → semantic capabilities → canonical Corytm musical IR/state → platform-specific execution.

## 2. User Segments

Three segments are sufficient until real user evidence justifies refinement — no elaborate persona framework yet.

- **Professional** — music producers, musicians, DJs, sound designers, film/game/media composers, audio engineers, professional and advanced prosumer creators. Primary surface: **Desktop**. Need the lowest abstraction level and greatest degree of deterministic control.
- **Creator** — social-media creators, video creators, streamers, marketers, and others who need music but are not necessarily interested in becoming music producers. Primary surfaces: **Web Studio**, later **Mobile**. Need high abstraction, strong automation/generation, rapid iteration, synchronization with content, and simple export.
- **Intermediate / prosumer** — users who want more control than prompt-to-song generation but not the full complexity of a professional DAW. Primary surface: **Web Studio**.

## 3. Platform Strategy

Corytm is intentionally multi-platform; its three surfaces differ in abstraction level and responsibility, not in the musical semantics underneath them.

### Corytm Desktop — macOS / Windows

Desktop is the principal technical surface during Alpha — the most demanding client of the shared Corytm core, and intended to become the professional agent-native DAW. It may ultimately include full timeline editing, tracks and clips, real-time playback, recording, MIDI, automation, mixing, plugins, routing, advanced audio editing, professional rendering/export, and deep Dorian semantic control. The existing Tracktion Engine + JUCE Native Audio Runtime remains Desktop-specific infrastructure (see `docs/technical/architecture.md`). Desktop is the lowest-abstraction / highest-control Corytm surface.

### Corytm Web

Web contains two conceptually distinct products that may evolve at different times.

**Commercial Web Platform** — expected eventual responsibilities: landing/marketing, product information, releases/downloads, documentation, pricing, authentication, account management, subscription management, billing/payment, user settings, project/account cloud capabilities where needed. Not built now merely because it appears here.

**Corytm Studio** — the intermediate creative surface. Expected direction: Dorian-first interaction, music generation, project library, playback, basic arrangement, basic DAW-like editing, creator workflows, all meaningful Mobile-generation capabilities, substantially less complexity than Desktop.

### Corytm Mobile — Android / iOS

Mobile is creator-first and intentionally high-abstraction. Initial product direction: text-to-music, Dorian-driven iteration, duration/style/mood/energy changes, content-synchronization workflows, simple export and reuse, project continuity with Web/Desktop.

Longer-term possible capabilities include multimodal workflows: video/audio input → multimodal understanding → semantic creative brief → Dorian/music-generation planning → soundtrack, drawing on scene description, timing, sentiment, pacing, dramatic intensity, visual transitions, important frames/events, CTA/reveal timing, and audio/sample context. This is long-term direction, not current implementation scope.

## 4. Technical Sequence versus Commercial Sequence

These are deliberately different questions.

Desktop remains the technical Alpha priority — the most demanding implementation surface, and therefore the best environment for proving the shared musical state, Dorian capability model, real-time runtime, semantic editing, persistence, and professional control.

Corytm does not currently assume Desktop must be the first commercially optimal release. **Current commercial hypothesis** (not an irreversible launch commitment): Web Studio / Creator workflows may offer the stronger initial go-to-market wedge.

Intended broad sequencing, not a rigid release calendar: Desktop technical Alpha → shared-core proof → Web/Creator commercial validation → Mobile after Creator workflows are validated.

## 5. Canonical Cross-Platform Project

A strong strategic principle: Corytm has one canonical musical project/state model across all product surfaces. Mobile, Web, and Desktop are different views and capability subsets of the same underlying Corytm project semantics. A project created on Mobile should ultimately be openable on Web and Desktop without destructive conversion.

A lower-capability platform may hide unsupported data, avoid editing unsupported data, or expose a simplified representation — but must not silently discard valid project state merely because that platform cannot expose or edit it.

Canonical project semantics remain independent from Desktop UI state, Tracktion state, Web UI state, Mobile UI state, and cloud storage representation. This is a corollary of ADR-001 (Corytm Engine owns canonical musical/project state) made explicit at platform scope, not a new architecture decision: ADR-001 never tied canonical ownership to Desktop specifically. It should inform future Engine evolution — see `docs/technical/architecture.md`'s Structural Evolution section.

## 6. Shared Intelligence Architecture

Dorian, Corytm's semantic capability/tool ecosystem, and the canonical Corytm musical IR/state form the shared intelligence layer:

Dorian ↕ semantic capabilities/tools ↕ canonical Corytm musical state ↕ Desktop/Web/Mobile capability profiles.

Dorian is not a Desktop chatbot. Chat is one possible interaction modality. Over time Dorian may receive text, voice, audio, video, image, current project state, selection/context, and platform capability context. Dorian reasons against semantic Corytm capabilities, not UI widgets, as its primary architectural interface — this is the product-strategy statement of the boundary ADR-004 already establishes as binding architecture.

## 7. Platform Capability Profiles

Different platforms are expected to expose different subsets of semantic capabilities. Illustratively: Desktop might support detailed track/clip editing, routing, plugins, automation, MIDI, and advanced mixing; Web may support generation, playback, sections, basic arrangement, gain/editing, and simplified project manipulation; Mobile may initially support generate, regenerate, mood/style/duration, content synchronization, simplified iteration, and export.

Capability profiles are not implemented during this Task. The architecture should remain compatible with this future concept so Dorian can eventually plan only against semantic capabilities available in the active product/platform/plan context.

## 8. Dorian's Strategic Moat

Corytm does not depend for differentiation on exclusive access to a particular frontier LLM. Dorian's long-term value comes primarily from Corytm-owned orchestration, context management, musical semantics, canonical project understanding, capability/tool design, execution planning, execution feedback, project history/context, model routing, permission and capability boundaries, and product-specific agent harness behavior.

Conceptually: Dorian = model intelligence + Corytm orchestration + Corytm tools + Corytm musical context + Corytm execution system. The model itself is replaceable infrastructure wherever feasible.

## 9. Provider-Agnostic Model Strategy

Corytm is provider-agnostic by design. Dorian is eventually expected to support routing across commercial frontier providers, economical hosted models, providers such as OpenAI, Anthropic, Google, Qwen-family deployments or comparable options, open-source models, potentially Corytm-hosted open-source inference, and future specialized models. Exact supported providers remain implementation/product decisions made when justified.

Default routing economic principle: use the lowest-cost model that reliably satisfies the required capability and quality level. Cost optimization must not silently degrade required quality. Routing may eventually consider task complexity, quality requirement, modality, context requirements, latency, availability, cost, user plan, BYOK state, and privacy/security constraints. `docs/technical/architecture.md`'s "Model Routing" section already describes this shape at the architecture level; this section is the product-strategy rationale behind it, not a second decision.

## 10. Allegro / Virtuoso / Maestro

Allegro, Virtuoso, and Maestro represent product-level service/capability classes, not permanent bindings to specific provider model names. Conceptually: Allegro is the economical/fast capability class; Virtuoso is stronger general reasoning/capability; Maestro is the highest-capability or most demanding operations class. Exact behavior and entitlements remain hypotheses to validate. A provider or underlying model can change without forcing Corytm to rename its product tiers or user-facing Dorian experience.

## 11. Generative Audio Strategy

Corytm must not depend on training proprietary generative-music foundation models for the core product to succeed.

**Medium-term direction:** integrate third-party/provider-agnostic generative-audio capabilities when useful for Corytm projects — potentially samples, vocals, stems, loops, instrumental material, track generation, sound design, and other generative musical assets — as semantic parts of the Corytm project/tool ecosystem, not an isolated prompt-to-audio product bolted onto the side.

**Longer-term:** proprietary Corytm audio-generation models may be explored only if Corytm has sufficient market traction, brand strength, profitability/economic justification, capital/data/talent, and strategic reason to own the model layer. This is an optional strategic evolution, not a current dependency or roadmap commitment.

## 12. Audio-to-Project Inference

Corytm should eventually be able to ingest an existing mixed audio file and infer a confidence-aware canonical Corytm project from it. Conceptually: mixed audio → source separation → beat/key/section analysis → musical transcription/semantic understanding → inferred Corytm Project/IR.

The objective is explicitly not to reconstruct the exact original DAW session, plugin chain, routing, automation, effects, or original MIDI — that information is generally not uniquely recoverable from a final mix. The objective is a plausible, editable semantic project hypothesis that may progressively include: inferred stems/tracks; tempo, beat grid, and downbeats; key/harmony; structural sections; clips/timeline; instrument/role annotations; inferred MIDI/note events where technically reliable; and confidence and provenance metadata for inferred facts.

Strategic experience: import existing music → Corytm understands its musical structure → Dorian can reason about and modify it semantically.

This reinforces the already-approved principle (§5) that canonical Corytm project state represents musical meaning independently of how it originated — manual editing, Dorian semantic operations, generative models, MIDI/audio import, and multimodal inference are all legitimate origins of the same canonical representation. Treated as a high-differentiation future opportunity and potential moat (§15), not an Alpha commitment, current roadmap item, or implementation requirement — see §19's open question on whether and when it is pursued.

## 13. Storage and Cloud Principle

The existing local-first Desktop direction is preserved unless a later protected decision explicitly changes it — this is a continuation of ADR-005, not a new decision. Broader platform direction: canonical project semantics remain independent from storage; Desktop remains local-first; optional Corytm Cloud sync/project services may be added when justified; Web and Mobile may necessarily use cloud services for some capabilities; cloud adoption should not force Desktop's canonical project semantics to become cloud-owned. Architecture should enable the MVP without prematurely building generalized cloud infrastructure.

## 14. Product Lifecycle Direction

Full lifecycle Objective/Exit-criteria text is canonical in `docs/project/plan.md`; this section states the product-strategy rationale behind it.

**Alpha** is not "finish a full professional DAW before doing anything else." Alpha's purpose is to prove the shared Corytm product and intelligence foundation using Desktop as the most demanding first execution surface — progressively establishing credible evidence for canonical musical state/IR, semantic editing operations, deterministic project manipulation, Dorian semantic capabilities, project persistence/evolution, runtime projection, real-time audio behavior, agent execution over real product state, usable Desktop interaction, and architectural portability of the shared core. Desktop is the primary Alpha implementation surface, not the entire definition of Corytm. Feature parity with Ableton/FL Studio/etc. is not an Alpha exit criterion.

**Beta / platform expansion** should eventually combine a credible usable Desktop experience, proof of Creator-oriented Web workflows, project/account/cloud foundations where commercially necessary, and commercial distribution foundations — no rigid Beta scope is created by this document. Web Studio should generally validate Creator workflows before committing heavily to Mobile; Mobile follows validated Creator product demand rather than being built merely because it is part of long-term strategy.

**Optional long-term social/community vision** — project sharing, remixing, creator discovery, public projects, community/social capabilities — is optional long-term vision only, not a roadmap commitment. It must not cause Alpha/Beta architecture to prematurely introduce social graphs, feeds, moderation systems, community infrastructure, or public-project architecture, unless later justified independently.

## 15. Strategic Differentiation

Corytm does not assume it competes only with traditional DAWs. Relevant competitive categories include traditional professional DAWs, AI music generators, generative audio workstations, AI-assisted creative tools, and future agentic DAW capabilities.

Strategic differentiation increasingly comes from **agent-native structured music creation and editing over persistent semantic project state**. The intended advantage is not merely "prompt → regenerate audio" but "intent → understand current project → reason over semantic musical objects → execute precise changes → preserve unrelated state → provide professional control when desired." Corytm aspires to a continuous path from high-level intent to low-level professional control.

## 16. Desktop Experience Principles

Absorbed from the superseded `docs/product/overview.md`, scoped to the Desktop surface specifically (not a platform-wide UX mandate):

Frontend quality is strategically important to Corytm Desktop. The product is intended to have a modern, professional interface; a coherent, distinctive Corytm design system; strong usability and accessibility; and specialized music-production interactions rather than a generic dashboard UI. Dorian must not feel like a chatbot in a sidebar on Desktop specifically — user selection and context, Dorian, proposed musical changes, previews and diffs, execution feedback, and the project itself are intended to form one coherent agent-native interaction, not a bolted-on chat panel. This is product principle, not a design specification: no library, component, or visual system is chosen here. Which frontend design-system and component libraries Corytm adopts, and the concrete interaction patterns for agent-native editing (previews, diffs, confirmation flows), remain deliberately open.

## 17. Approved Principles

Unless repository reconciliation reveals a direct contradiction requiring human review, the following are approved:

- Corytm is an AI-native music creation platform.
- Desktop, Web, and Mobile are intended product surfaces.
- The surfaces expose different complexity/abstraction levels.
- They share one canonical Corytm musical project/state model.
- Lower-capability surfaces must not destructively downgrade valid project state.
- Desktop is Alpha's primary technical implementation surface.
- Web/Creator is currently held as the stronger initial commercial-wedge **hypothesis** — approved as the current working hypothesis to plan around, not as an irreversible launch commitment (see §19).
- Dorian is a shared intelligence/orchestration layer, not a Desktop chatbot.
- Corytm's semantic capabilities/tool ecosystem and project semantics are core differentiation.
- Dorian/model infrastructure is provider-agnostic.
- Default routing should seek the cheapest model that reliably meets required quality/capability.
- Allegro/Virtuoso/Maestro are product capability/service classes, not permanent provider-model bindings.
- Third-party/provider-agnostic generative audio precedes any proprietary-model commitment.
- Proprietary generative models are optional future strategy only if business/technical conditions justify them.
- Desktop remains local-first.
- Cloud is introduced where necessary without making canonical project semantics cloud-owned.
- Optional social/community functionality is long-term vision only.
- CPO strategic proposals are encouraged (`CLAUDE.md` §3).
- Protected Product Decisions require explicit human approval (§18; `CLAUDE.md` §5).
- Alpha validates shared core/intelligence through Desktop rather than requiring full traditional-DAW parity.

## 18. Protected Product Decisions

`CLAUDE.md` §5 requires explicit human approval before changing any of the following. Claude may analyze and propose changes to these, but must not silently convert a proposal into approved strategy, PMO direction, or implementation:

- Corytm's product category.
- Target markets.
- Primary user segments.
- Platform commitments — adding or abandoning a platform.
- Platform priority/sequencing at the strategic level.
- Go-to-market strategy.
- Monetization model.
- Subscription architecture.
- Major pricing/entitlement boundaries.
- Major BYOK commercial-policy changes.
- Major capability families.
- Major Dorian product-tier changes.
- Major provider-strategy changes.
- Proprietary-model strategy.
- Legal/commercial rights promises.
- Distribution model.
- Major lifecycle-definition changes.
- Major changes to the shared-project/cross-platform-continuity principle (§5 above).
- Major changes to local-first/cloud strategy (§13 above).
- Abandoning or materially redefining the canonical musical IR/Dorian platform thesis (§1, §6 above).

Routine implementation detail inside an already-approved strategy is not automatically protected. If uncertain whether a proposal is protected, err toward surfacing it for human approval rather than silently changing strategy.

## 19. Open Strategic Questions

Do not silently elevate these to permanent commitments:

- Exact first commercial launch surface.
- Exact timing of Web Studio.
- Exact timing of Mobile.
- Exact provider/model selected for Allegro/Virtuoso/Maestro.
- Exact supported external providers.
- Exact hosted open-source strategy.
- Exact generative-audio providers.
- Whether Corytm ever trains proprietary audio models.
- Detailed social/community product direction.
- Precise Beta scope.
- Whether and when Audio-to-Project Inference (§12) is pursued, and to what fidelity.

Where any existing product doc states one of these as a fixed commitment without human approval, surface the conflict rather than resolving it silently.

## Related decisions

ADR-001 (canonical Python musical model), ADR-002 (process separation), ADR-003 (Tracktion Engine + JUCE), ADR-004 (Dorian's trusted-capability boundary), ADR-005 (local-first). None of these are reopened by this document.

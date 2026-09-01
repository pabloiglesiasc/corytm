# Corytm Technical Architecture

This document captures Corytm's current accepted technical direction: the major system components, their responsibility boundaries, and what remains intentionally undecided. It describes design direction, not implemented behavior — no production functionality exists yet. Statements use "is designed to," "the architecture establishes," or "the intended direction is" rather than describing running behavior.

## System Shape

Corytm's desktop application is designed to consist of three components: a React/TypeScript UI, a Python application core, and a native C++ audio runtime built on Tracktion Engine + JUCE. The UI is packaged and shipped via Tauri 2, which also orchestrates the Python and native-audio process lifecycles. See ADR-006.

## Foundational Law

Python knows what the project means musically. C++ knows how to make it sound. See ADR-001 for the rationale behind this boundary.

## Naming

- **Corytm Engine** (`src/backend/core/modules/engine`) — Corytm's canonical musical/project domain.
- **Runtime** (`src/backend/core/modules/runtime`) — the Python-side synchronization/projection concern between Corytm Engine and the Native Audio Runtime.
- **Native Audio Runtime** (`src/backend/audio`) — the C++ runtime. Avoid calling it "the audio engine" because that would be ambiguous with Corytm Engine and Tracktion Engine; use "Native Audio Runtime" instead.
- **Tracktion Engine** — the third-party technology inside the Native Audio Runtime.

Conceptually: Dorian → Corytm Engine → Runtime → Native Audio Runtime → Tracktion Engine + JUCE.

## Canonical State and Projection

Corytm Engine is designed to own canonical musical/project state — concepts such as Project, Track, Clip, Note, Plugin, and Automation, named here illustratively and not frozen as a schema. Tracktion Engine's Edit is a runtime projection of that canonical state, not a second source of truth. See ADR-001.

## Process Topology

The Python application core and the native C++ audio runtime are designed to run as separate processes. See ADR-002.

## Tracktion Engine + JUCE

Tracktion Engine is designed to supply the DAW-level layer: the Edit, tracks, clips, playback graph, transport, automation, plugin model, rendering, and MIDI-related DAW operations. JUCE is designed to supply the lower-level native foundation that stack uses: audio I/O, MIDI I/O, plugin format/device/OS abstractions, buffers, and VST3/AU hosting infrastructure. Strudel and DawDreamer are not part of Corytm's architecture. See ADR-003.

## Local-First

Corytm's core project editing and local operation are designed to be local-first: local project state and resources are primary, and core local operation does not depend on server-authoritative project state. See ADR-005.

## Human/Dorian Shared Application Path

Human UI actions and Dorian actions are designed to go through the same trusted application/domain capabilities — Dorian is restricted to semantic tools (illustrative only: a tool to read a track's state, a tool to replace a clip's notes) rather than direct native or Tracktion access. The model proposes actions; trusted application code authorizes and executes them. See ADR-004.

## Model Routing

Dorian is designed to route through an agent harness/policy layer to a model router, which selects among the Allegro, Virtuoso, and Maestro tiers before reaching a provider layer. Corytm is intended to remain provider-agnostic at the product/domain level — no provider is selected or configured here.

## Engine Services and Incremental Updates

Corytm Engine is designed to expose semantic editing operations (illustrative only: adding a track, moving a clip) rather than requiring direct manipulation of the canonical model. Edits are intended to project incrementally toward the Native Audio Runtime rather than resending the entire canonical project for each change — commands express intentions, events express facts (illustrative: a command to move a clip producing a "clip moved" event). CQRS, event-sourcing, CommandBus, EventBus, Mediator, or handler infrastructure is not introduced merely because commands and events exist as concepts.

## Python↔C++ Boundary

Python and the native runtime are designed to communicate through a narrow, versioned local protocol: commands and events defined as Protobuf messages under `src/schemas/`, carried over a local loopback-socket transport — not exhaustive bindings to Tracktion Engine. The concrete socket/framing implementation is a replaceable detail, independent of the schema and the application boundary. See ADR-007. `src/schemas/proof.proto` proves the C++ (CMake-vendored) and Python (uv-managed) codegen pipeline end to end with one illustrative message (FT-008/TK-009). `src/schemas/project.proto` (EP-005) carries the first real, if deliberately minimal, product message definitions: `Project`/`AudioTrack`/`AudioClip` (timing only — no MIDI, plugins, or automation yet) and a `MaterializeProjectCommand`/`ProjectRenderedEvent` pair proving one command/event round trip end to end, including real Tracktion Engine materialization and an offline render. This remains a deliberately narrow slice, not the full product schema — most real command/event message definitions (and the concrete Corytm Engine domain model beyond this minimal slice) remain open (see Unresolved).

## Dependency Direction

Dorian is intended to depend on Engine and Runtime capabilities. There are no dependency cycles: Runtime never depends on Dorian. Whether Runtime consumes Engine events without importing the full Engine model is an open future design detail, not settled here.

## Source Tree Direction

The conceptual source layout separates frontend, backend core (with engine/dorian/runtime modules), and native audio under `src/`. This is direction only — no source directory is materialized by this step.

## Unresolved

The following remain deliberately open, not settled by this document: the persistence implementation; cloud/sync architecture; provider mappings behind Allegro/Virtuoso/Maestro; frontend design-system, component, state-management, and rendering choices; and the great majority of the concrete protocol/schema messages a real product needs (EP-005's `project.proto` resolves only a first, minimal one-track/one-clip slice of this, not the general case).

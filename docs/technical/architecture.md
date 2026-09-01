# Corytm Technical Architecture

This document captures Corytm's current accepted technical direction: the major system components, their responsibility boundaries, and what remains intentionally undecided. It describes design direction, not implemented behavior — no production functionality exists yet. Statements use "is designed to," "the architecture establishes," or "the intended direction is" rather than describing running behavior.

## System Shape

Corytm's desktop application is designed to consist of three components: a React/TypeScript UI, a Python application core, and a native C++ audio runtime built on Tracktion Engine + JUCE. The UI is packaged and shipped via Tauri 2, which also orchestrates the Python and native-audio process lifecycles. See ADR-006.

## Foundational Law

Python knows what the project means musically. C++ knows how to make it sound. See ADR-001 for the rationale behind this boundary.

## Naming

- **Corytm Engine** (`src/backend/core/src/corytm/engine`) — Corytm's canonical musical/project domain.
- **Runtime** (`src/backend/core/src/corytm/runtime`) — the Python-side synchronization/projection concern between Corytm Engine and the Native Audio Runtime.
- **Native Audio Runtime** (`src/backend/audio`) — the C++ runtime. Avoid calling it "the audio engine" because that would be ambiguous with Corytm Engine and Tracktion Engine; use "Native Audio Runtime" instead.
- **Tracktion Engine** — the third-party technology inside the Native Audio Runtime.

Conceptually: Dorian → Corytm Engine → Runtime → Native Audio Runtime → Tracktion Engine + JUCE.

## Canonical State and Projection

Corytm Engine is designed to own canonical musical/project state — concepts such as Project, Track, Clip, Note, Plugin, and Automation, named here illustratively and not frozen as a schema. Tracktion Engine's Edit is a runtime projection of that canonical state, not a second source of truth. See ADR-001. Canonical Corytm Engine (and, as they are introduced, Runtime and Dorian application-facing) models are Pydantic models, not dataclasses or other plain structures — invariants are enforced explicitly at construction/validation, including transitively through nested models. See ADR-008.

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

## Python Backend Package Layout

`src/backend/core` is a real, installable Python package rooted at `corytm` (`src/backend/core/src/corytm/`, built by `hatchling`), not a bare script directory. `uv run`/`uv sync` build and install it in editable mode automatically, so `corytm`'s subpackages resolve the same way regardless of the caller's current working directory and without manually setting `PYTHONPATH`. The application entry point is the `corytm` console script (`[project.scripts]`), invocable as `uv run --project src/backend/core corytm` from anywhere, or plain `uv run corytm` from inside `src/backend/core`. An import crossing one of this document's named ownership boundaries (Corytm Engine, Runtime, Native Audio Runtime, and, once introduced, Dorian) is an absolute, package-qualified import (`corytm.engine.*`, `corytm.runtime.*`); an import between tightly-coupled sibling modules inside the same subpackage may be relative. See ADR-009.

## Native Audio Runtime Source Layout

`src/backend/audio/` separates its production surface from its proof/ctest executables by location, not merely by CMake target type: shippable libraries and their headers (for example `materializer.h`/`.cpp`, `wire_codec.h`/`.cpp`, `project_spec.h`) and the one production executable (`native_runtime.cpp`) live flat at the directory root; one-off proof/ctest executables that exist to validate a mechanism rather than ship it (for example `toolchain_proof.cpp`, `materializer_proof.cpp`) live under `src/backend/audio/tests/`. A production library that needs its public header visible to a test under `tests/` exposes it via `target_include_directories(... PUBLIC ...)` in `CMakeLists.txt` rather than a relative include path. This convention was adopted 2026-09-01, after EP-005 grew the directory to 11 files with no prior governing rule for the distinction.

## Dependency Direction

Dorian is intended to depend on Engine and Runtime capabilities. There are no dependency cycles: Runtime never depends on Dorian. Whether Runtime consumes Engine events without importing the full Engine model is an open future design detail, not settled here.

## Source Tree Direction

The conceptual source layout separates frontend, backend core (with engine/dorian/runtime modules), and native audio under `src/`. This is direction only — no source directory is materialized by this step.

## Structural Evolution

Corytm remains domain-oriented. A module stays flat while its responsibilities are genuinely homogeneous; today's flatness in Engine and Runtime is a consequence of small scope, not a permanent architectural target. As demonstrated, distinct responsibilities emerge within a module, it evolves toward explicit internal ownership boundaries — illustratively, models, services, repositories, adapters/clients, tools, providers, and module-owned tests, drawn from only where those concepts genuinely apply. Restructuring happens when a directory accumulates real heterogeneity, before it grows into a large undifferentiated folder — never merely to resemble this target vocabulary in advance, and never by scaffolding empty or ceremonial directories ahead of the responsibilities that would justify them. This section states direction, not a mandate: `CLAUDE.md` §8's anti-premature-abstraction rule and this document's own authority ordering still govern the actual timing of any restructuring.

Per-area growth direction:

- **Engine** — today's compact canonical models (`Project`/`AudioTrack`/`AudioClip`) may remain as-is. Editing/command behavior, undo/history, persistence boundaries, repositories, or orchestration emerging as real, distinct responsibilities is the trigger to split into explicit models/services/repositories/adapters.
- **Runtime** — keep projection, session, and transport responsibilities clear, as already named in this document's Naming section. Separate models, services, clients/adapters, or lifecycle/orchestration concerns once they become materially distinct from each other, not merely once the vocabulary is available.
- **Dorian** — not yet started. When Dorian product work begins, its module should be able to grow toward explicit separation of models, services/orchestration, semantic tools/capabilities, providers/model routing, repositories/state, and adapters where justified. None of this is scaffolded in advance of that work.
- **Native Audio Runtime** — preserve the production-root/`tests/` separation established in "Native Audio Runtime Source Layout" above. Evolve further toward clearer public-header/source/internal boundaries only when API ownership or implementation scale makes that useful; no ceremonial `include`/`src` split before then.
- **Schemas** (`src/schemas/`) — stay flat while few contracts exist. Introduce domain/version grouping only when multiple event/runtime/API schema families make flat organization materially unclear.
- **Tests** — preserve colocated unit tests for module ownership. Cross-component, integration, and end-to-end tests stay in the dedicated cross-component home (`src/backend/core/tests/` for the Python core) only when they genuinely cross module boundaries.

## Unresolved

The following remain deliberately open, not settled by this document: the persistence implementation; cloud/sync architecture; provider mappings behind Allegro/Virtuoso/Maestro; frontend design-system, component, state-management, and rendering choices; and the great majority of the concrete protocol/schema messages a real product needs (EP-005's `project.proto` resolves only a first, minimal one-track/one-clip slice of this, not the general case).

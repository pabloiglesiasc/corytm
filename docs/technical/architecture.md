# Corytm Technical Architecture

This document captures Corytm's current accepted technical direction: the major system components, their responsibility boundaries, and what remains intentionally undecided. It describes design direction, not implemented behavior — no production functionality exists yet. Statements use "is designed to," "the architecture establishes," or "the intended direction is" rather than describing running behavior.

## System Shape

This document describes Corytm Desktop's architecture specifically — one surface of the broader Corytm platform (`docs/product/strategy.md`). Corytm's desktop application is designed to consist of three components: a React/TypeScript UI, a Python application core, and a native C++ audio runtime built on Tracktion Engine + JUCE. The UI is packaged and shipped via Tauri 2, which also orchestrates the Python and native-audio process lifecycles. See ADR-006.

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

Human UI actions and Dorian actions are designed to go through the same trusted application/domain capabilities — Dorian is restricted to semantic tools rather than direct native or Tracktion access. The model proposes actions; trusted application code authorizes and executes them. See ADR-004. `corytm.dorian.tools` (EP-008) makes this real for the first time: `MoveClipProposal` is the validated input boundary a model's proposed action must pass before anything executes, and `move_clip` is the only path through which a proposal is authorized and executed — reusing Corytm Engine's `with_clip_moved` operation and EP-006's live native session unchanged, not a new edit mechanism. No model/provider is wired up yet; the proposal is still constructed directly in tests, standing in for what a model would eventually emit.

## Model Routing

Dorian is designed to route through an agent harness/policy layer to a model router, which selects among the Allegro, Virtuoso, and Maestro tiers before reaching a provider layer. Corytm is intended to remain provider-agnostic at the product/domain level — no provider is selected or configured here.

## Engine Services and Incremental Updates

Corytm Engine is designed to expose semantic editing operations (illustrative only: adding a track, moving a clip) rather than requiring direct manipulation of the canonical model. Edits are intended to project incrementally toward the Native Audio Runtime rather than resending the entire canonical project for each change — commands express intentions, events express facts (illustrative: a command to move a clip producing a "clip moved" event). CQRS, event-sourcing, CommandBus, EventBus, Mediator, or handler infrastructure is not introduced merely because commands and events exist as concepts.

## Python↔C++ Boundary

Python and the native runtime are designed to communicate through a narrow, versioned local protocol: commands and events defined as Protobuf messages under `src/schemas/`, carried over a local loopback-socket transport — not exhaustive bindings to Tracktion Engine. The concrete socket/framing implementation is a replaceable detail, independent of the schema and the application boundary. See ADR-007. `src/schemas/proof.proto` proves the C++ (CMake-vendored) and Python (uv-managed) codegen pipeline end to end with one illustrative message (FT-008/TK-009). `src/schemas/project.proto` (EP-005) carries the first real, if deliberately minimal, product message definitions: `Project`/`AudioTrack`/`AudioClip` (timing only — no MIDI, plugins, or automation yet) and a `MaterializeProjectCommand`/`ProjectRenderedEvent` pair proving one command/event round trip end to end, including real Tracktion Engine materialization and an offline render. EP-006 (TK-018) adds a second pair, `MoveClipCommand`/`ClipMovedEvent`, and a minimal `Command`/`Event` oneof envelope sized to exactly these two known command/event types — the `native_runtime` process now keeps its materialized `Edit` alive across a long-lived connection and accepts a sequence of commands against it, rather than exiting after exactly one. This remains a deliberately narrow slice, not the full product schema — most real command/event message definitions (and the concrete Corytm Engine domain model beyond this minimal slice) remain open (see Unresolved).

## Desktop↔Python Boundary

Tauri's Rust core and the Python application core communicate through a second, independent instance of the same protocol discipline as the Python↔C++ boundary above — a narrow, versioned Protobuf command/event contract carried over a local loopback-socket transport — deliberately not sharing a socket, port, secret, or schema/envelope with the Python↔Native Audio Runtime transport, so either boundary's schema, port, secret, or concrete framing implementation can change independently. The Python core process (already spawned by Tauri via its sidecar mechanism, ADR-006/FT-010) opens this second listener itself and passes its port and a random per-launch secret to Rust over the same stdout lifecycle channel that already carries the `READY` signal; Rust connects and authenticates before any command traffic is accepted, symmetric to how the Native Audio Runtime authenticates to Python today. Sidecar stdio itself stays lifecycle-only (readiness, this handshake line, shutdown) and never carries domain commands or events. Python core remains the sole authority over the Native Audio Runtime: Rust never connects to it directly, and every Desktop-originated edit is authorized and executed by Python core through Corytm Engine's existing operations, the same governed path Dorian's tools use (ADR-004). See ADR-010.

## Local Project Persistence

A Corytm project is durably represented as a single local JSON file: a versioned envelope (`schema_version`, independent of `project.proto`'s own wire-protocol versioning) wrapping a JSON payload that currently mirrors the canonical Engine `Project` model's own shape (today produced via Pydantic's `model_dump`/`model_validate` — the current implementation mechanism, not itself the permanent contract). Corytm Engine (`corytm.engine.persistence`) is the sole reader and writer of this file's content — Rust/Tauri never parses or serializes project data; it only resolves a filesystem path via a native OS file dialog and passes that path to Python core over the existing Desktop↔Python channel (ADR-010), which loads or saves the project and, for Open, re-materializes it through the already-proven Runtime/Native Audio Runtime path. No project-bundle/directory format exists yet: `AudioClip` carries no external resource reference today, so there is nothing else to bundle. Alpha project files carry no backward-compatibility guarantee yet — `schema_version` distinguishes format revisions, but migration/support policy is deliberately unresolved (Beta). See ADR-011.

## Python Backend Package Layout

`src/backend/core` is a real, installable Python package rooted at `corytm` (`src/backend/core/src/corytm/`, built by `hatchling`), not a bare script directory. `uv run`/`uv sync` build and install it in editable mode automatically, so `corytm`'s subpackages resolve the same way regardless of the caller's current working directory and without manually setting `PYTHONPATH`. The application entry point is the `corytm` console script (`[project.scripts]`), invocable as `uv run --project src/backend/core corytm` from anywhere, or plain `uv run corytm` from inside `src/backend/core`. An import crossing one of this document's named ownership boundaries (Corytm Engine, Runtime, Native Audio Runtime, and, once introduced, Dorian) is an absolute, package-qualified import (`corytm.engine.*`, `corytm.runtime.*`); an import between tightly-coupled sibling modules inside the same subpackage may be relative. See ADR-009.

## Native Audio Runtime Source Layout

`src/backend/audio/` separates its production surface from its proof/ctest executables by location, not merely by CMake target type: shippable libraries and their headers (for example `materializer.h`/`.cpp`, `wire_codec.h`/`.cpp`, `project_spec.h`) and the one production executable (`native_runtime.cpp`) live flat at the directory root; one-off proof/ctest executables that exist to validate a mechanism rather than ship it (for example `toolchain_proof.cpp`, `materializer_proof.cpp`) live under `src/backend/audio/tests/`. A production library that needs its public header visible to a test under `tests/` exposes it via `target_include_directories(... PUBLIC ...)` in `CMakeLists.txt` rather than a relative include path. This convention was adopted 2026-09-01, after EP-005 grew the directory to 11 files with no prior governing rule for the distinction.

## Dependency Direction

Dorian is intended to depend on Engine and Runtime capabilities. There are no dependency cycles: Runtime never depends on Dorian. Whether Runtime consumes Engine events without importing the full Engine model is an open future design detail, not settled here.

## Source Tree Direction

The conceptual source layout separates frontend, backend core (with engine/dorian/runtime modules), and native audio under `src/`. This is direction only — no source directory is materialized by this step.

## Structural Evolution

Corytm remains domain-oriented. Per `docs/product/strategy.md`'s Canonical Cross-Platform Project principle, Corytm Engine's canonical model is intended to remain platform-independent — usable by Web/Mobile capability profiles later, not Desktop-specific — even though only Desktop consumes it today; this is forward guidance for future modeling choices, not a restructuring trigger by itself. A module stays flat while its responsibilities are genuinely homogeneous; today's flatness in Engine and Runtime is a consequence of small scope, not a permanent architectural target. As demonstrated, distinct responsibilities emerge within a module, it evolves toward explicit internal ownership boundaries — illustratively, models, services, repositories, adapters/clients, tools, providers, and module-owned tests, drawn from only where those concepts genuinely apply. Restructuring happens when a directory accumulates real heterogeneity, before it grows into a large undifferentiated folder — never merely to resemble this target vocabulary in advance, and never by scaffolding empty or ceremonial directories ahead of the responsibilities that would justify them. This section states direction, not a mandate: `CLAUDE.md` §8's anti-premature-abstraction rule and this document's own authority ordering still govern the actual timing of any restructuring.

Per-area growth direction:

- **Engine** — today's compact canonical models (`Project`/`AudioTrack`/`AudioClip`) may remain as-is. Editing/command behavior, undo/history, persistence boundaries, repositories, or orchestration emerging as real, distinct responsibilities is the trigger to split into explicit models/services/repositories/adapters.
- **Runtime** — keep projection, session, and transport responsibilities clear, as already named in this document's Naming section. Separate models, services, clients/adapters, or lifecycle/orchestration concerns once they become materially distinct from each other, not merely once the vocabulary is available.
- **Dorian** — product work has begun (EP-008): its first semantic tool lives flat in `dorian/tools.py`, mirroring Engine/Runtime's own current flatness. It should grow toward explicit separation of models, services/orchestration, semantic tools/capabilities, providers/model routing, repositories/state, and adapters only once those responsibilities become materially distinct from each other, not merely once the vocabulary is available — none of it is scaffolded in advance.
- **Native Audio Runtime** — preserve the production-root/`tests/` separation established in "Native Audio Runtime Source Layout" above. Evolve further toward clearer public-header/source/internal boundaries only when API ownership or implementation scale makes that useful; no ceremonial `include`/`src` split before then.
- **Schemas** (`src/schemas/`) — stay flat while few contracts exist. Introduce domain/version grouping only when multiple event/runtime/API schema families make flat organization materially unclear.
- **Tests** — preserve colocated unit tests for module ownership. Cross-component, integration, and end-to-end tests stay in the dedicated cross-component home (`src/backend/core/tests/` for the Python core) only when they genuinely cross module boundaries.

## Unresolved

The following remain deliberately open, not settled by this document: cloud/sync persistence architecture; formal project-file migration/backward-compatibility policy and any future project-bundle/resource format (ADR-011 resolves only the local single-file JSON storage mechanism, not these); provider mappings behind Allegro/Virtuoso/Maestro; frontend design-system, component, state-management, and rendering choices (visual-identity and design-system-ownership direction is canonical in `docs/product/design.md`; concrete choices remain open here); and the great majority of the concrete protocol/schema messages a real product needs (EP-005's `project.proto` resolves only a first, minimal one-track/one-clip slice of this, not the general case). EP-010 (FT-022) carries the Desktop channel's first real UI-facing domain command: Rust compiles `project.proto` directly (alongside `desktop.proto`) and reuses its `MoveClipCommand`/`ClipMovedEvent` messages by reference over the Desktop channel, per ADR-010 point 1, rather than a new Desktop-owned wrapper — `desktop.proto`'s own `DesktopProofMessage` remains only as a permanent Rust codegen-toolchain proof, no longer what the channel's real round trip carries. Still open: any UI-facing command beyond this one hardcoded move; the actual project creation/opening/saving commands and UI built on ADR-011's now-decided storage mechanism; and any frontend design-system, component, state-management, or rendering choice beyond the minimal function-only trigger FT-022 adds.

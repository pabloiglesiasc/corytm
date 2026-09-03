# Roadmap — Beta

Canonical entries for every capability whose first rollout, on any surface, is Beta. See `README.md` in this directory for reading rules, mutation/authority semantics, Commitment (Committed/Conditional) semantics, and Flags.

Beta combines professional Desktop depth with the Commercial Web Platform (`docs/product/strategy.md` §3/§14) — no rigid Beta scope is fixed by strategy.md itself; this roadmap is what now makes it concrete. Every commercial/monetization capability in the Web section below requires its own Protected Product Decision (`CLAUDE.md` §5, `docs/product/business-model.md` §8) before implementation — listed here as roadmap intent, not pre-approved commercial policy; see `README.md`'s Flags for how many decisions that actually implies.

## Desktop — MIDI & Composition Foundation

- **MIDI canonical track/clip model** — Rollout: Desktop — Beta
- **Piano roll** — Rollout: Desktop — Beta
- **MIDI note editing** — Rollout: Desktop — Beta
- **MIDI recording/input/routing** — Rollout: Desktop — Beta
- **Quantization** — Rollout: Desktop — Beta
- **Velocity/CC editing** — Rollout: Desktop — Beta
- **Groove** — Rollout: Desktop — Beta
- **Clip loop/repeat** — Rollout: Desktop — Beta
- **Fades/crossfades** — Rollout: Desktop — Beta
- **Time-stretching** — Rollout: Desktop — Beta
- **Pitch shifting/transposition** — Rollout: Desktop — Beta
- **Normalize/reverse/consolidate audio** — Rollout: Desktop — Beta
- **Transient snapping** — Rollout: Desktop — Beta
- **Tempo map/time-signature map** — Rollout: Desktop — Beta
- **Song sections** — Rollout: Desktop — Beta
- **Key/scale metadata** — Rollout: Desktop — Beta
- **Chord progression/harmony context** — Rollout: Desktop — Beta

## Desktop — Mixing, Routing & Instruments

- **Automation editing/curves model** — Rollout: Desktop — Beta
- **Automation recording/parameter-capture foundation** — Rollout: Desktop — Beta
- **Send/return buses** — Rollout: Desktop — Beta
- **Groups/folders** — Rollout: Desktop — Beta
- **Routing** — Rollout: Desktop — Beta
- **Master processing chain** — Rollout: Desktop — Beta
- **Built-in gain/EQ/compressor** — Rollout: Desktop — Beta
- **Basic built-in instrument** — Rollout: Desktop — Beta
- **Sampler** — Rollout: Desktop — Beta
- **Drum sequencing** — Rollout: Desktop — Beta
- **Step sequencer/pattern editor** — Rollout: Desktop — Beta
- **Pattern-based composition** — Rollout: Desktop — Beta
- **Scene/clip-launching workflow** — Rollout: Desktop — Beta
- **Arrangement/pattern interoperability** — Rollout: Desktop — Beta

## Desktop — Plugin Hosting

- **Plugin hosting foundation** — Rollout: Desktop — Beta
- **Plugin scanning/validation** — Rollout: Desktop — Beta
- **Plugin parameter/state persistence** — Rollout: Desktop — Beta
- **Plugin automation** — Rollout: Desktop — Beta
- **Plugin crash/recovery basics** — Rollout: Desktop — Beta
- **Missing-plugin recovery** — Rollout: Desktop — Beta

## Desktop — Production Depth & Resilience

- **Freeze/bounce** — Rollout: Desktop — Beta
- **Selection rendering** — Rollout: Desktop — Beta
- **Autosave/crash recovery** — Rollout: Desktop — Beta
- **Migration framework** — Rollout: Desktop — Beta
- **Project resource bundling/portability** — Rollout: Desktop — Beta ⚠ Flag
- **Project templates** — Rollout: Desktop — Beta
- **Recent-project browser** (rich browsing/search, beyond Alpha's basic list) — Rollout: Desktop — Beta
- **Rich keyboard-command/remapping system** — Rollout: Desktop — Beta
- **Context menus** — Rollout: Desktop — Beta
- **Professional inspector** (beyond Alpha's selection-aware foundation) — Rollout: Desktop — Beta
- **Professional transport/control bar** — Rollout: Desktop — Beta
- **Mixer metering** (beyond Alpha's basic surface) — Rollout: Desktop — Beta
- **Performance/realtime-safety hardening** — Rollout: Desktop — Beta
- **Installer/update pipeline** — Rollout: Desktop — Beta
- **Crash diagnostics** — Rollout: Desktop — Beta
- **Take management** — Rollout: Desktop — Beta
- **Comping** — Rollout: Desktop — Beta
- **Punch recording (with pre/post-roll)** (punching in/out at a playhead-driven point, plus the pre/post-roll playback context around it — one recording-transport-timing mechanism) — Rollout: Desktop — Beta
- **Recording-latency compensation** — Rollout: Desktop — Beta

## Dorian — Advanced Capabilities

- **Multi-tool planning** — Rollout: Desktop — Beta
- **Multi-step atomic edits** — Rollout: Desktop — Beta
- **Multi-turn conversational context** — Rollout: Desktop — Beta
- **Previews/diffs** — Rollout: Desktop — Beta
- **Explain/undo last action** — Rollout: Desktop — Beta
- **Semantic song-section understanding** — Rollout: Desktop — Beta
- **MIDI tools** — Rollout: Desktop — Beta
- **Mixer/routing tools** — Rollout: Desktop — Beta
- **Plugin/effect tools** — Rollout: Desktop — Beta
- **Arrangement-level transformations** — Rollout: Desktop — Beta
- **Intent clarification** — Rollout: Desktop — Beta
- **Audition alternatives** — Rollout: Desktop — Beta
- **Provider fallback/recovery** — Rollout: Desktop — Beta
- **Capability-tier abstraction** (real Allegro/Virtuoso/Maestro routing, beyond ADR-013's single-provider Alpha proof) — Rollout: Desktop — Beta
- **Cost/quality/latency routing** — Rollout: Desktop — Beta
- **Inference accounting** — Rollout: Desktop — Beta
- **BYOK configuration** — Rollout: Desktop — Beta ⚠ Flag

## Web — Commercial Platform & Studio

- **Authentication/account recovery** — Rollout: Web — Beta
- **Profile/account settings** — Rollout: Web — Beta
- **Cloud project library** — Rollout: Web — Beta
- **Browser playback** — Rollout: Web — Beta
- **Timeline-lite editing** — Rollout: Web — Beta
- **Web Dorian conversational creation/editing** — Rollout: Web — Beta
- **Responsive Web workspace** — Rollout: Web — Beta
- **Project metadata/library views** — Rollout: Web — Beta
- **Duplicate/archive/delete** — Rollout: Web — Beta
- **Asset upload/download** — Rollout: Web — Beta
- **Cloud render/export** — Rollout: Web — Beta
- **Web keyboard shortcuts** — Rollout: Web — Beta
- **Onboarding/create-first-song flow** — Rollout: Web — Beta

## Web — Generative Audio

- **Text-to-music generation** — Rollout: Web — Beta · Mobile — Stable
- **Prompt-to-full-song generation** — Rollout: Web — Beta
- **Prompt-to-stem generation** — Rollout: Web — Beta
- **Prompt-to-loop/sample generation** — Rollout: Web — Beta
- **Generate continuation from project context** — Rollout: Web — Beta
- **Regenerate selected region** — Rollout: Web — Beta
- **Alternatives/variants** — Rollout: Web — Beta
- **Generation progress/cancellation/retry** — Rollout: Web — Beta
- **Generated asset library/history** — Rollout: Web — Beta
- **Provider-agnostic generative-audio adapter** — Rollout: Web — Beta
- **Generated-audio insertion** — Rollout: Web — Beta
- **Provenance/rights metadata** — Rollout: Web — Beta

## Web — Commercial & Account

- **Subscription plans/entitlements** — Rollout: Web — Beta ⚠ Flag
- **Usage/credit balance** — Rollout: Web — Beta ⚠ Flag
- **Checkout/subscription management** — Rollout: Web — Beta ⚠ Flag
- **Upgrade/downgrade/cancel** — Rollout: Web — Beta ⚠ Flag
- **Billing history/invoices** — Rollout: Web — Beta ⚠ Flag
- **Credit top-ups** — Rollout: Web — Beta ⚠ Flag
- **Storage/project quotas** — Rollout: Web — Beta
- **Usage-limit enforcement** — Rollout: Web — Beta ⚠ Flag
- **Inference/generation COGS instrumentation** — Rollout: Web — Beta
- **Privacy/account-data controls** — Rollout: Web — Beta
- **Account deletion/data export** — Rollout: Web — Beta
- **Commercial error/support feedback** — Rollout: Web — Beta

## Cross-Surface

- **Cross-surface canonical project compatibility proof** — Rollout: Desktop — Beta · Web — Beta
- **Desktop↔Web project portability** — Rollout: Desktop — Beta · Web — Beta

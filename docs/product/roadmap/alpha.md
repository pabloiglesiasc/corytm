# Roadmap — Alpha

Canonical entries for every capability whose first rollout, on any surface, is Alpha. See `README.md` in this directory for reading rules, mutation/authority semantics, Commitment (Committed/Conditional) semantics, and Flags.

Alpha's purpose (`docs/product/strategy.md` §14): prove the shared Corytm product and intelligence foundation using Desktop as the most demanding first execution surface. It is **not** DAW feature parity with Ableton/FL Studio, and it explicitly excludes **MIDI** and **plugin hosting** (both Beta — see `beta.md`). It **is**: real-time audio (not offline rendering alone), a credible Desktop DAW foundation (not an isolated Add-Track/Add-Clip proof), and a vertical Dorian product integration on Desktop (not a backend-only model/tool proof). See `docs/project/plan.md`'s Current Phase section for the full exit-criteria statement this file's Desktop — Alpha entries collectively satisfy.

## Project & Workspace

- **Project create/open/save (local persistence)** — Rollout: Desktop — Alpha · Web — Beta
- **Versioned project format foundation** — Rollout: Desktop — Alpha
- **Dirty/saved state** — Rollout: Desktop — Alpha
- **Project naming/metadata** — Rollout: Desktop — Alpha
- **Recent projects (basic list)** — Rollout: Desktop — Alpha
- **Real Desktop workspace shell** (replacing FT-025's functional scaffold; includes moving the information architecture beyond the current card layout) — Rollout: Desktop — Alpha
- **Arrangement length derived from project content** — Rollout: Desktop — Alpha
- **Resizable workspace/panel foundation** — Rollout: Desktop — Alpha
- **Empty/loading/error workspace states** — Rollout: Desktop — Alpha
- **Non-blocking status/notification feedback** — Rollout: Desktop — Alpha

## Real-Time Audio & Transport

Real-time playback/device output is an Alpha blocker: offline rendering (already proven) does not by itself satisfy this category.

- **Real-time audio-device initialization/output** — Rollout: Desktop — Alpha
- **Live play/stop/pause transport** — Rollout: Desktop — Alpha
- **Playhead and real-time position** — Rollout: Desktop — Alpha
- **Seek/arbitrary playhead positioning** — Rollout: Desktop — Alpha
- **Loop-region playback** — Rollout: Desktop — Alpha
- **Metronome / count-in** (click during playback and before recording — one click-generation mechanism, two triggers) — Rollout: Desktop — Alpha
- **Sample-rate/buffer configuration** — Rollout: Desktop — Alpha
- **Audio-device input/output configuration** — Rollout: Desktop — Alpha
- **Audio-device hot-plug/recovery** — Rollout: Desktop — Alpha
- **Transport state reflected coherently in UI** — Rollout: Desktop — Alpha
- **Master output monitoring** — Rollout: Desktop — Alpha
- **Basic stereo master metering** — Rollout: Desktop — Alpha
- **Clipping indication/peak reset** — Rollout: Desktop — Alpha

## Arrangement & Editing

- **Multi-track project materialization** (native `buildEdit` beyond today's `tracks[0]`-only limitation) — Rollout: Desktop — Alpha
- **Timeline/arrangement workspace** — Rollout: Desktop — Alpha
- **Add/delete/rename/reorder tracks** — Rollout: Desktop — Alpha
- **Add/delete/duplicate clips** — Rollout: Desktop — Alpha
- **Move clips freely** (arbitrary placement, beyond today's auto-append-only) — Rollout: Desktop — Alpha
- **Trim/resize clips** — Rollout: Desktop — Alpha
- **Split clips** — Rollout: Desktop — Alpha
- **Multi-selection** — Rollout: Desktop — Alpha
- **Marquee/range selection** — Rollout: Desktop — Alpha
- **Copy/cut/paste** — Rollout: Desktop — Alpha
- **Keyboard delete** — Rollout: Desktop — Alpha
- **Duplicate selected objects** — Rollout: Desktop — Alpha
- **Fine keyboard nudge** — Rollout: Desktop — Alpha
- **Undo/redo** — Rollout: Desktop — Alpha
- **Unified undo across manual and Dorian edits** — Rollout: Desktop — Alpha
- **Timeline zoom/navigation** — Rollout: Desktop — Alpha
- **Timeline ruler/time-musical coordinates** — Rollout: Desktop — Alpha
- **Grid/snapping** — Rollout: Desktop — Alpha
- **Tempo/time-signature project settings** — Rollout: Desktop — Alpha
- **Markers/locators foundation** — Rollout: Desktop — Alpha
- **Arrangement loop/range selection** — Rollout: Desktop — Alpha
- **Track/clip naming from workspace** — Rollout: Desktop — Alpha
- **Track/clip color assignment** — Rollout: Desktop — Alpha
- **Selection-aware inspector foundation** — Rollout: Desktop — Alpha
- **Contextual command affordances** — Rollout: Desktop — Alpha

## Audio Clips & Media

- **Real audio-file import** — Rollout: Desktop — Alpha ⚠ Flag
- **Project external-resource references** (a clip pointing at an external audio file) — Rollout: Desktop — Alpha ⚠ Flag
- **Waveform generation/visualization** — Rollout: Desktop — Alpha
- **Drag-and-drop audio into arrangement** — Rollout: Desktop — Alpha
- **Media/file browser foundation** — Rollout: Desktop — Alpha
- **Clip gain** — Rollout: Desktop — Alpha
- **Clip source-offset/slip editing** — Rollout: Desktop — Alpha
- **Missing-media detection/resolution** — Rollout: Desktop — Alpha

## Mixer & Recording

- **Track volume/pan/mute/solo** — Rollout: Desktop — Alpha
- **Basic mixer surface** — Rollout: Desktop — Alpha
- **Track output metering** — Rollout: Desktop — Alpha
- **Track input selection** — Rollout: Desktop — Alpha
- **Record-arm** — Rollout: Desktop — Alpha
- **Input monitoring** — Rollout: Desktop — Alpha
- **Basic audio recording** — Rollout: Desktop — Alpha
- **Render/export project to WAV** (user-facing export command; distinct from the offline-render proof mechanism already used internally) — Rollout: Desktop — Alpha

## Desktop UX & Design System

- **Semantic design tokens** — Rollout: Desktop — Alpha · Web — Beta · Mobile — Stable
- **Dark/light themes** — Rollout: Desktop — Alpha · Web — Beta · Mobile — Stable
- **Corytm component catalog** — Rollout: Desktop — Alpha · Web — Beta · Mobile — Stable
- **Professional application menu/command structure** — Rollout: Desktop — Alpha
- **Keyboard-first navigation/focus** — Rollout: Desktop — Alpha
- **Track/clip visual components** — Rollout: Desktop — Alpha
- **Selection/focus/disabled/loading interaction semantics** — Rollout: Desktop — Alpha

## Dorian

Alpha requires the full vertical path: user → Desktop Dorian UI → model → provider-neutral Dorian orchestration → trusted Engine operation → Runtime/native audio → observable/audible result. Three entries below are enabling/infrastructure capabilities with no surface interaction of their own (provider-agnostic model boundary; low-cost live model semantic-edit execution; trusted proposal validation/execution) — satisfied by backend realization alone, per `README.md`'s realization rule. Every other Dorian capability below is user-facing: its Desktop UI must exist and the full vertical path above must be real for it, not merely proven in automated tests or via a single hardcoded proposal.

- **Provider-agnostic model boundary** — Rollout: Desktop — Alpha
- **Low-cost live model semantic-edit execution** — Rollout: Desktop — Alpha
- **Trusted proposal validation/execution** — Rollout: Desktop — Alpha
- **Desktop Dorian conversational surface** — Rollout: Desktop — Alpha
- **Message history** — Rollout: Desktop — Alpha
- **Contextual project-state awareness** — Rollout: Desktop — Alpha
- **Project inspection/questions** — Rollout: Desktop — Alpha
- **Natural-language clip movement** — Rollout: Desktop — Alpha
- **Natural-language track creation/deletion** — Rollout: Desktop — Alpha
- **Natural-language clip creation/deletion/duplication** — Rollout: Desktop — Alpha
- **Natural-language trim/split/resize** — Rollout: Desktop — Alpha
- **Volume/pan/mute/solo semantic edits** — Rollout: Desktop — Alpha
- **Transport control where semantically appropriate** — Rollout: Desktop — Alpha
- **Visible execution/progress state** — Rollout: Desktop — Alpha
- **Action result/error/refusal/recovery feedback** — Rollout: Desktop — Alpha
- **Undo last Dorian semantic action** — Rollout: Desktop — Alpha

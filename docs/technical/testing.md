# Testing & Validation Policy

This document is Corytm's canonical answer to two questions: which command to run when, and when a suite's last pass stops being valid evidence. It does not restate what a test proves — that lives beside the test itself — and it never lowers the acceptance bar `CLAUDE.md` §6/§7 and `docs/project/format.md`'s Evidence Traceability already set. The standard this policy optimizes for is stated once and applies everywhere below: **the same or stronger confidence, with materially less redundant execution time.**

Adopted 2026-09-03 following a testing-architecture-and-policy review (measured local/CI timings, real command-graph tracing, and a full test inventory of this repository) and its approved implementation (EP-015/FT-028).

## Corytm's five local subsystems

Every quality command in this repository decomposes into five independently invocable Make targets, each owning a distinct toolchain:

| Target | Toolchain | What it validates |
|---|---|---|
| `check-python` | `uv`/pytest/pyright/ruff | Corytm Engine, Runtime, Dorian — domain logic, projection, provider abstractions |
| `check-native` | CMake/ctest | Native Audio Runtime against real JUCE/Tracktion Engine |
| `check-desktop` | Cargo/Tauri | Desktop shell, IPC/ACL, sidecar process lifecycle |
| `check-transport` | pytest (`-m transport`) | Python↔native wire protocol and session lifecycle, against the binary `check-native` produces |
| `check-frontend` | npm/Vite/vitest/oxlint | Frontend build, unit tests, lint |

`make check` aggregates all five and is Corytm's Feature-close/CI guarantee. Nothing in this policy changes what `make check` validates — only when running all five, versus a subset, is the right amount of work for the evidence actually needed.

## The four tiers

**Tier 1 — Inner loop.** After a small change, during TDD. Run only the narrowest command for the subsystem being changed, and skip anything gated behind a slower fidelity than the change needs: `pytest -m "not transport and not live_llm"` (optionally path/`-k`-scoped) for Python; `cmake --build && ctest` for native (no reconfigure unless `CMakeLists.txt` changed); `cargo test` alone for Rust (not the full `npm run tauri build` release/bundle step); `npm run test`/`npm run lint` for frontend (not the full `npm run build`). Never reflexively run `pytest -m transport`, the device-touching `ctest` targets, or `npm run tauri build` here unless the change specifically touches that surface.

**Tier 2 — Affected-subsystem validation.** Once a change within one subsystem stabilizes, or a Task closes. Run that subsystem's own full Make target — its complete local guarantee (lint, type-check, tests together). If the change's own diff touches more than one subsystem's input set (below), run each of those targets — never reflexively all five.

**Tier 3 — Feature-close integration validation.** Before considering a Feature locally complete, before Git handoff. Run every subsystem whose input set (below) has changed since its own last recorded pass in this working tree. `make check` (all five, unconditionally) is reserved for: no prior per-subsystem evidence yet existing in this tree; a change to `Makefile` or `.github/workflows/**`; or a change already known to invalidate three or more subsystems at once (a shared `.proto` schema, for example). Most Features touch one or two subsystems, so Tier 3 is normally a strict subset of `make check`, not `make check` itself.

**Tier 4 — CI / cross-platform / external / manual.** Always required for native/Rust/cross-platform-sensitive Features, never locally substitutable, unaffected by anything above:
- A real macOS + Windows `check` Actions run, independently confirmed against the exact delivery commit (`gh run view`/`gh api`, never the reported job conclusion alone) — this repository's own risk history (`RSK-002` through `RSK-018`) is direct, repeated precedent that a clean local pass does not predict real Windows behavior.
- Human-only manual evidence wherever a Feature's acceptance criteria name it explicitly (real audible playback, real UI click-through in a running app window) — no automated assertion establishes these.
- `live_llm`-marked live-provider evaluations — human-triggered, with a real API key, never part of routine `check-python`/CI (see below).

Tier 4's evidence requirements are unchanged by this document. This policy governs how fast Tiers 1–3 are reached, never what Tier 4 must independently confirm before a Feature reaches `done`.

## Invalidation: the exact rule

A subsystem's most recent local PASS remains valid evidence for the current working tree only while `git status`/`git diff` shows **no** change to that subsystem's input set since that pass. Any change to those inputs — including one made by unrelated work earlier in the same session — invalidates it immediately, regardless of elapsed time. This is deliberately git-diff-based, not a stored hash or timestamp: the input set below is exact, and `git diff` against the commit/working-tree state where a suite last passed answers the question precisely, with no new file format or tool to go stale.

| Subsystem | Invalidated by changes to |
|---|---|
| `check-python` | `src/backend/core/src/corytm/**`, `src/backend/core/tests/**`, `schemas/*.proto`, `pyproject.toml`/`uv.lock` |
| `check-native` | `src/backend/audio/**` (excluding `build/`), `schemas/*.proto` |
| `check-desktop` | its own Rust/frontend inputs, **plus `check-native`'s own input set** — it spawns a real `native_runtime` |
| `check-transport` | **`check-native`'s own input set**, plus `corytm.runtime`/`corytm.engine` and the transport-marked test files |
| `check-frontend` | `src/frontend/desktop/src/**`, `package*.json` |

The cross-subsystem edges (`check-desktop` and `check-transport` are each invalidated by `check-native`'s inputs even when no Rust or Python file changed) are the detail most likely to be silently missed by anything less explicit than this table — a change to `src/backend/audio/**` invalidates all three of `check-native`, `check-desktop`, and `check-transport` at once.

**Where this evidence is recorded:** a Feature's own PMO record already requires Evidence Traceability (`docs/project/format.md`) — which suites passed, against which commit. Recording which subsystems were (re-)validated, and against what working-tree state, in that same record is sufficient; no separate ledger, cache file, or tool is needed or should be built for this (see "Why no automated cache" below).

## Clean-build triggers

| Change | Clean rebuild required? | Why |
|---|---|---|
| `src/backend/audio/CMakeLists.txt` (new/bumped `FetchContent`, compiler flags, C++ standard) | **Yes** | Make's mtime-based reuse has no awareness of toolchain/compiler identity — the same hazard this repository's CI cache key was hardened against (`.claude/memory/native-build-caching.md`) |
| `schemas/*.proto` | No | Every toolchain already declares this correctly (CMake `add_custom_command DEPENDS`, Cargo `rerun-if-changed`, `check-python`'s unconditional protoc step) |
| `Cargo.toml`/`Cargo.lock` (dependency/version changes) | No | Trust Cargo's own lock-hash incrementality |
| `src-tauri/build.rs` itself | **Yes, manually** (`cargo clean` for that crate) | Its `OUT_DIR` caching is keyed on `rerun-if-changed` declarations the script itself controls; a logic change to fetch/verify/extract isn't guaranteed to be re-triggered by its own stated inputs |
| `pyproject.toml`/`uv.lock` | No | `uv` re-resolves automatically; only a Python version pin change warrants `rm -rf .venv` |
| `package.json`/`package-lock.json` | **Only for that change** — a real `npm ci` | The one boundary where a clean-room reinstall earns its cost, rather than paying it unconditionally every run |
| `.github/workflows/check.yml` | No local rebuild, but the real CI run is still required Tier-4 evidence | Orchestration-only, doesn't affect local build correctness |
| Local toolchain change (Xcode/MSVC/rustc/CMake upgrade) | **Yes, by convention** | Outside repo control; mirrors the CI cache's own `IMAGE_OS`/`IMAGE_VERSION` defense |

**CI's role in the clean-build guarantee:** CI performs a from-scratch checkout on every run — it already *is* the periodic clean-room guarantee for cross-platform correctness. Local Feature-close validation staying incremental never weakens required evidence, because a Feature's `done` state already requires the independently-confirmed real CI run regardless of what was validated locally (`CLAUDE.md` §6). Incrementality only changes how fast a session reaches a confident handoff point.

## Local artifact/cache reuse

Prefer each toolchain's own dependency tracking over bespoke caching, in this order of trust: CMake/Make's own mtime-based incremental build (already correct — a no-op rebuild recompiles nothing); Cargo's own `Cargo.lock`-keyed incrementality and build-script `rerun-if-changed` declarations; `uv`'s own lock-based venv resolution; Vite's own dependency pre-bundle cache (`node_modules/.vite`). None of these need supplementing.

The one local gap: `sccache` (Rust + C/C++ compiler cache) is wired into CI (`RUSTC_WRAPPER=sccache`, `CMAKE_C_COMPILER_LAUNCHER`/`CMAKE_CXX_COMPILER_LAUNCHER`) but not into local `make check-native`/`check-desktop`. Local incremental rebuilds already hit zero recompilation on their own, so this adds nothing in steady state — its value is specifically for post-`clean`, post-branch-switch, or first-build scenarios, where it currently helps not at all locally despite being proven safe and effective by CI's own use of it.

## Why no automated test-result cache

An automated fingerprint/ledger that skips a suite based on "nothing important changed" is deliberately not adopted. A correct version requires exhaustively enumerating every real input to a suite — source, tests, schemas, lockfiles, toolchain identity, even runtime environment (`GROQ_API_KEY` presence, audio-device availability) — and this repository's own risk history (`RSK-002` through `RSK-018`) is a long, repeated record of a clean pass not meaning what it was assumed to mean. Automating a skip decision on top of that history, for suites that already cost single-digit-to-tens of seconds, is a worse trade than the time it would save. The git-diff-based invalidation rule above gives the same benefit without inventing a mechanism that can be subtly wrong.

## What this policy does not change

- Every Tier-4 requirement above: real cross-platform CI, real IPC/ACL tests (e.g. the Tauri ACL test that caught `RSK-017`), real process/session-lifecycle tests, real native-runtime/device tests (e.g. `playback_proof`, which caught `RSK-018`), human-only audible/UI evidence, and `live_llm` live-provider evaluations. None of these are ever replaced by a faster or mocked substitute merely because mocks are faster — fidelity is preserved wherever it is material to the guarantee.
- `live_llm`-marked tests are excluded from `check-python`'s default collection (defense in depth alongside the existing `skipif(GROQ_API_KEY)` guard) and remain reachable only via an explicit `pytest -m live_llm` invocation, run by a human with a real key as a Feature's own acceptance step.
- `make check`'s meaning as the Feature-close/CI aggregate is unchanged; this policy governs which of its constituent parts a session chooses to run before reaching for it, not what it validates when run.

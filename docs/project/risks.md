# Risk Register

A risk is something uncertain that may happen. A blocker is something already preventing or affecting work right now — blockers live on the affected work item's own Status/Blocker field, never here.

## Format

`RSK-001` | Description | Likelihood (low/med/high) | Impact (low/med/high) | Status (open/monitoring/materialized/closed) | Mitigation | Related work

## Current Risks

`RSK-001` | Tracktion Engine + JUCE native build/integration across macOS and Windows may prove substantially more difficult or expose platform-specific issues, affecting FT-003/EP-002/Pre-alpha timing | med | med | closed | Materialized once (Windows CI failed under MinGW auto-detection) and was fixed by dropping `-G Ninja` from `check-native` (TK-006). A real GitHub Actions run now passes on both macOS and Windows — the risk this entry tracked (native build/integration proving substantially more difficult or platform-specific) did not hold beyond the one fixed issue; no further platform-specific native build risk is currently open | EP-001, FT-003, EP-002, FT-005, TK-006
`RSK-002` | Adding a Rust/Tauri build toolchain (ADR-006) and Protobuf codegen integrated into both the CMake native build and the uv-managed Python project (ADR-007) — two new cross-platform build-toolchain surfaces at once — may expose macOS/Windows-specific integration issues similar in kind to RSK-001's, affecting EP-004 timing | med | med | monitoring | Rust/Tauri half fully proven on both platforms: `make check` (including `check-desktop`) passes locally from a clean state (TK-008), and a real GitHub Actions `check` run on `e095d54` (the TK-008 commit) independently confirmed via `gh run view 33444480062` passing on both `check (macos-latest)` and `check (windows-latest)` jobs — the Windows leg TK-008 itself could not confirm (`CLAUDE.md` §10 push restriction) is now genuinely closed out, mirroring RSK-001/TK-006's precedent exactly. Protobuf codegen (ADR-007) is the only remaining unproven half — not yet started as of TK-008; keep proving it with deliberately minimal scope before building further Alpha work on top of it | EP-004, FT-007, TK-008, ADR-006, ADR-007

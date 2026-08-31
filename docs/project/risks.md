# Risk Register

A risk is something uncertain that may happen. A blocker is something already preventing or affecting work right now — blockers live on the affected work item's own Status/Blocker field, never here.

## Format

`RSK-001` | Description | Likelihood (low/med/high) | Impact (low/med/high) | Status (open/monitoring/materialized/closed) | Mitigation | Related work

## Current Risks

`RSK-001` | Tracktion Engine + JUCE native build/integration across macOS and Windows may prove substantially more difficult or expose platform-specific issues, affecting FT-003/EP-002/Pre-alpha timing | med | med | materialized | Windows CI run failed as anticipated: CMake's `-G Ninja` auto-detected MinGW instead of MSVC, and JUCE refuses to build under MinGW (TK-006). Fixed by dropping `-G Ninja` so CMake uses its own per-platform default generator (Visual Studio/MSBuild on Windows, sidestepping PATH-based compiler discovery entirely); verified locally on macOS via a clean `make check-all`. Whether MSVC itself compiles Tracktion Engine + JUCE cleanly is still unconfirmed — needs another real Windows CI run | EP-001, FT-003, EP-002, FT-005, TK-006

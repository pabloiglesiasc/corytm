# Risk Register

A risk is something uncertain that may happen. A blocker is something already preventing or affecting work right now — blockers live on the affected work item's own Status/Blocker field, never here.

## Format

`RSK-001` | Description | Likelihood (low/med/high) | Impact (low/med/high) | Status (open/monitoring/materialized/closed) | Mitigation | Related work

## Current Risks

`RSK-001` | Tracktion Engine + JUCE native build/integration across macOS and Windows may prove substantially more difficult or expose platform-specific issues, affecting FT-003/EP-002/Pre-alpha timing | med | med | closed | Materialized once (Windows CI failed under MinGW auto-detection) and was fixed by dropping `-G Ninja` from `check-native` (TK-006). A real GitHub Actions run now passes on both macOS and Windows — the risk this entry tracked (native build/integration proving substantially more difficult or platform-specific) did not hold beyond the one fixed issue; no further platform-specific native build risk is currently open | EP-001, FT-003, EP-002, FT-005, TK-006

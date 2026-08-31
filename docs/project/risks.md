# Risk Register

A risk is something uncertain that may happen. A blocker is something already preventing or affecting work right now — blockers live on the affected work item's own Status/Blocker field, never here.

## Format

`RSK-001` | Description | Likelihood (low/med/high) | Impact (low/med/high) | Status (open/monitoring/materialized/closed) | Mitigation | Related work

## Current Risks

`RSK-001` | Tracktion Engine + JUCE native build/integration across macOS and Windows may prove substantially more difficult or expose platform-specific issues, affecting FT-003/EP-002/Pre-alpha timing | med | med | monitoring | macOS build+link+test proof completed successfully (TK-002), surfacing only routine CMake integration friction, not a fundamental blocker; a CI workflow to validate Windows now exists (TK-005) but has not yet actually run — Windows remains genuinely unvalidated until a push triggers it | EP-001, FT-003, EP-002, FT-005

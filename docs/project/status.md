# Project Status

Last updated: 2026-08-31

**Lifecycle phase:** Pre-alpha
**Active milestone:** MS-001 — Self-Driving Repository
**Active Task:** none — awaiting selection
**Next recommended Task:** none — no further Claude-executable Task exists; EP-002's remaining work is a human pushing the fix and observing whether the Windows leg now passes, which this session cannot perform (git-administration prohibition)
**Blockers:** none

## Recent meaningful progress

FT-004/EP-001 done (root `Makefile` unifying Python/frontend/native checks). FT-005 authored `.github/workflows/check.yml`; a real run showed macOS passing and Windows failing (`error: "MinGW is not supported"` — CMake's `-G Ninja` had auto-detected MinGW instead of MSVC on the Windows runner). TK-006 fixed this by dropping `-G Ninja` from the Makefile's `check-native` target, letting CMake use its own per-platform default generator instead — verified locally on macOS via a fully clean `make check-all`. `RSK-001` moved to `materialized`. FT-005 is done again; EP-002 stays active pending a real Windows CI re-run to confirm the fix.

---
Planning view: `docs/project/plan.md`
Artifact formats: `docs/project/format.md`
Risk register: `docs/project/risks.md`

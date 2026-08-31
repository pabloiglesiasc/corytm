# Project Status

Last updated: 2026-08-31

**Lifecycle phase:** Pre-alpha
**Active milestone:** MS-001 — Self-Driving Repository
**Active Task:** none — awaiting selection
**Next recommended Task:** none — EP-003 (Harness Validation) is ready but has no Features yet; per its own Objective, refining and executing it must be done by a genuinely fresh Claude Code session with no conversation history, not a continuation of a session that already carries this repository's build-out history
**Blockers:** none

## Recent meaningful progress

FT-004/EP-001 done (root `Makefile` unifying Python/frontend/native checks). FT-005/TK-006 diagnosed and fixed a real Windows CI failure (CMake's `-G Ninja` auto-detected MinGW instead of MSVC; fixed by dropping `-G Ninja` so CMake uses its per-platform default generator). A real GitHub Actions run now passes on both macOS and Windows. `RSK-001` closed. EP-002 (Continuous Integration & Platform Validation) is done — its Acceptance criteria (CI running and passing on both platforms) is genuinely satisfied. EP-003 (Harness Validation) is now ready — its only dependency, EP-002, is done.

---
Planning view: `docs/project/plan.md`
Artifact formats: `docs/project/format.md`
Risk register: `docs/project/risks.md`

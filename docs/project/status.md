# Project Status

Last updated: 2026-08-31

**Lifecycle phase:** Pre-alpha
**Active milestone:** MS-001 — Self-Driving Repository
**Active Task:** none — awaiting selection
**Next recommended Task:** none — no further Claude-executable Task exists; EP-002's remaining work is a human pushing the current tree and observing the authored CI workflow's actual run, which this session cannot perform (git-administration prohibition)
**Blockers:** none

## Recent meaningful progress

TK-004 completed; a root `Makefile` (`make check`, `make check-all`) unifies the Python, frontend, and native quality checks, verified from a fully clean state. FT-004 is done, and EP-001 (Engineering Foundation) is done. EP-002 (Continuous Integration & Platform Validation) refined into its first Feature (FT-005); TK-005 authored `.github/workflows/check.yml` (macOS + Windows matrix running `make check`), verified with `actionlint`. FT-005 is done, but EP-002 stays active — its own Acceptance criteria needs an actual observed CI run, not just an authored workflow.

---
Planning view: `docs/project/plan.md`
Artifact formats: `docs/project/format.md`
Risk register: `docs/project/risks.md`

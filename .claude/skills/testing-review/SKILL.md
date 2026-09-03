---
description: Apply Corytm's canonical Testing & Validation Policy (docs/technical/testing.md) whenever tests are added or changed, and whenever a Feature's validation is being planned or closed. Use during Implement/Review when a Task or Feature adds/changes tests, and during Validate/Close when deciding what to run.
---

Ground truth is `docs/technical/testing.md` — consult it directly for the four-tier model, the exact invalidation input-set table, and the clean-build triggers; this skill only sequences how to apply that policy to a specific piece of work, it never restates or reinterprets its content.

## When tests are added or changed

1. **Placement** — does the new test's guarantee belong exclusively to one subsystem (`engine`/`dorian`/`runtime`, or the equivalent native/Rust/frontend boundary), or does it genuinely cross a subsystem/application/process boundary? Place it accordingly (`src/backend/core/tests/{engine,dorian,runtime}/` vs. `.../tests/integration/`, and the existing convention already established for native/Rust/frontend) — inspect what the test actually imports and exercises; never classify by filename alone.
2. **Fidelity** — does this guarantee require a real process, real IPC/ACL, a real native device, or a real external provider, or does a fast, hermetic test already establish it? Reach for the higher-fidelity form only when a faster one genuinely cannot prove the thing at stake — never default to the expensive form out of caution alone, and never substitute a mock merely because it is faster when the fidelity itself is what the test exists to prove.
3. **Complementary vs. duplicate** — before adding a test that resembles an existing one (it also spawns `native_runtime`, also touches the Desktop channel), name the specific guarantee it adds. Two tests paying the same expensive setup cost but proving different things — a Rust test proving real ACL permission, a Python test proving wire-protocol correctness — are complementary; keep both. A new test that would prove nothing an existing one doesn't already cover is duplicate; don't add it.
4. **New dependency edges** — if the new test introduces a cross-subsystem dependency `docs/technical/testing.md`'s invalidation table doesn't yet name (a subsystem newly calling into another, a new shared schema/config file), update that table in the same change.

## When planning or closing a Feature's validation

5. **Tier selection** — during implementation, run only the narrowest Tier 1 command for the subsystem actually being changed. Expand to that subsystem's full Make target (Tier 2) only once the change stabilizes. Reach for `make check` only when Tier 3's own conditions apply (no prior evidence yet exists in this working tree, a change touches `Makefile`/`.github/workflows/**`, or a change is already known to invalidate three or more subsystems at once) — not by default.
6. **Invalidation, not elapsed time** — before treating a subsystem's last local pass as still valid, check `git status`/`git diff` against that subsystem's own input set since that pass, including the cross-subsystem edges (a native-code change invalidates `check-desktop`/`check-transport` too, not only `check-native`). A pass from minutes ago against now-changed inputs is not valid evidence; a pass from earlier against still-unchanged inputs is.
7. **No ritual re-running** — do not run `pytest ...`, then that subsystem's own Make target, then `make check`, when the later commands would only re-execute a suite that already just passed against unchanged code. Run each suite once per invalidation, not once per habit.
8. **Tier 4 stays untouched** — real cross-platform CI (independently confirmed via `gh run view`/`gh api`, never a reported conclusion alone), human-only manual evidence (audible playback, real UI click-through), and `live_llm`-marked live-provider evaluations are never satisfied by anything in Tiers 1–3, regardless of how much local evidence exists. Confirm these are still named in the Feature's own acceptance criteria and Evidence field before Close.

## Output

For a placement/fidelity question: a one-line decision with its reasoning. For Feature validation planning: the specific commands to run (or the already-valid evidence to rely on instead) and why, naming which subsystems' inputs actually changed. This feeds directly into the Feature's own Implement/Validate/Close steps (`CLAUDE.md` §7) — this skill decides what to run, it does not itself execute or replace that validation.

## Out of scope

Do not restate `docs/technical/testing.md`'s four-tier model, invalidation table, or clean-build triggers here — reference it. Do not invent a test-result cache, fingerprint, or ledger mechanism — `docs/technical/testing.md` explicitly rejects one; use the exact git-diff-based invalidation check instead. Do not lower fidelity (substitute a mock, skip a `transport`/`live_llm`/human-evidence requirement, or narrow a Feature's acceptance criteria) to make validation faster — this skill never trades confidence for speed, only removes redundant repetition of evidence that already exists.

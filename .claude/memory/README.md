# Memory

`.claude/memory/` holds useful but provisional operational context — retained learning that may help a future session before it's mature enough for a durable canonical artifact. This file documents the mechanism; it holds no actual memory yet.

## What memory is / is not

- Memory is context, not command: non-authoritative, incubating, revisable, removable. A future session must never treat memory as settled truth merely because it exists.
- Memory vs. PMO: PMO (`docs/project/`) is current, tracked project state — phase, active Task, milestone, blockers, risks. Memory never restates any of it; it may only record a distinct observation that isn't yet a PMO fact.
- Memory vs. docs: docs describe verified current reality. Memory may hold an unverified technical/product caveat pending confirmation.
- Memory vs. specs: specs are accepted normative truth. Memory may note that intended behavior is unclear — never that a requirement is settled.
- Memory vs. decisions: ADRs are accepted, historical rationale. Memory may note a recurring pattern that might justify a formal decision — never the decision itself.
- Memory vs. skills: skills are distilled reusable procedures. Memory may hold raw observations that are evidence a skill is warranted, but is never a substitute for one and is not a mandatory step before a skill can exist.
- Memory vs. conversation history: the repository never depends on chat history. Only the repository-facing operational meaning of something discovered in conversation is eligible, filtered through the normal capture threshold below — never a wholesale summary, never "the user said X."

Never in memory: current Task status, roadmap, next work, risk-register entries, normative behavior, accepted rationale, current technical/product documentation, a reusable procedure, a permanent coding convention, a chat transcript, a session diary, a changelog, a chronological log, raw chain-of-thought, generic notes, or a dumping ground for unclassifiable information. Sensitive information — secrets, credentials, tokens, private personal information, machine-specific sensitive values, account identifiers — is never retained here, applying `CLAUDE.md`'s existing repository-wide security rule rather than establishing a new one.

## Capture threshold

```
observation
    ↓
already mature enough for its canonical home?
├── yes → write directly there (docs/spec/decision/skill/PMO) — never memory, not even briefly
└── no
     ↓
actively part of a current Task's/PMO's own unresolved context?
├── yes → stays there — not memory
└── no
     ↓
concrete future value?
├── yes → memory (provisional incubation)
└── no → discard
```

Default is forget. An observation earns memory only when it's likely to help a future session, has no stronger *current* home, and forgetting it would plausibly cause rediscovery cost, repeated confusion, or an avoidable mistake. Memory incubates evidence that isn't ready for its destination yet — it never delays a promotion that's actually earned, and it never substitutes for the PMO/Task-context holding pattern that already exists for unresolved work.

## Writing a memory entry

Every retained entry must be grounded in a concrete evidence anchor — an actual observation, event, result, or encountered behavior, with its subject named plainly in the sentence. Inference or suspicion may appear only attached to that anchor, explicitly hedged ("may," "appears to," "suspected") — never as a standalone entry, never written as settled fact. A future verification step is included only when there's a concrete next check; omit it otherwise. No rigid template, no frontmatter, no timestamps unless chronology genuinely matters, no confidence scores, IDs, or status fields.

## Organization

No file exists until real content justifies it. When one does, it's named for its actual topic — never for a generic category like state, lessons, issues, observations, or memory itself. Entries group semantically within a file, not chronologically; never one file per session or date. No ID scheme unless real future volume demonstrates a need for it.

## Discovery

Progressive context loading applies, no separate mechanism: `CLAUDE.md` → `status.md` → the current Task → its declared references (which may point to a relevant memory file) → relevant memory only. Claude may also identify relevant memory during PLAN without a prior reference. No fresh session reads all memory, and there is no global preload, registry, index, search system, or vector store.

## Maintenance and deletion

Refine memory in place from a small demonstrated update; Git owns the history, so stale text is deleted outright, never preserved as an archive or historical note. Deletion is a core, encouraged behavior: memory is forgotten when stale, disproven, redundant, promoted, obvious from a canonical artifact, irrelevant, or too vague to be actionable. At Task SYNC/CLOSE, Claude assesses whether a new observation deserves memory, existing memory went stale, or something should be promoted or consolidated — "no memory change required" is a valid outcome needing no ceremonial edit.

## Promotion

Promotion moves the durable meaning to its canonical home, then removes the redundant memory — never both copies kept, no promotion workflow engine:

- Verified current reality → docs.
- Accepted normative behavior → a SPEC.
- Accepted durable rationale → an ADR.
- A distilled reusable procedure → a skill.
- Actual current project state, a real risk, or a blocker → PMO (`docs/project/risks.md`, or the affected work item itself).

Only a genuinely distinct, still-unresolved observation may remain after promotion; references are fine, duplication is not.

## Authority

If memory conflicts with `CLAUDE.md`, an accepted spec, an accepted decision, current Task acceptance criteria, or current code/tests where those govern, the higher-authority source wins outright — the memory is corrected, promoted, or deleted, never treated as evidence strong enough to override it. If two memory entries conflict, investigate the underlying evidence, keep the uncertainty explicit while genuinely unresolved, consolidate once resolved, and delete whichever side is disproven. Contradictory memory is never preserved as history.

## Current state

Eight memory entries exist, each grounded in a real event encountered during native-build, CI, and desktop-shell operational work: `cmake-windows-generator.md`, `github-actions-windows-runner.md`, `tracktion-engine-cmake-integration.md`, `tauri-dmg-stale-mount.md`, `cargo-path-missing-in-tool-shell.md`, `protobuf-cmake-windows-crt-and-build-surface.md`, `protobuf-generated-code-cxx-standard-abi.md`, and `native-build-third-party-warnings.md`. Their content is not summarized here — per this file's own Discovery section, a session finds them progressively, through the current Task's declared references or by identifying relevance during PLAN, not through an index in this file.

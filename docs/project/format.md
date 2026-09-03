# PMO Artifact Format

Canonical reference for Corytm's Milestone, Epic, Feature, Task, and Risk records. Read before authoring or transitioning any of these.

## Identifiers

Immutable, sequential within type, never encoding hierarchy: `MS-001`, `EP-001`, `FT-001`, `TK-001`, `RSK-001`. Filenames are ID-only once files exist (e.g. `epics/EP-001.md`); titles live inside the file, not the filename.

## Status Vocabulary

- Milestone: `planned / active / achieved / cancelled` (no "ready" state — a Milestone isn't executed, its constituent work is).
- Epic / Task: `planned / ready / active / blocked / done / cancelled`.
- Feature: `planned / ready / active / validating / blocked / done / cancelled` — `validating` sits between `active` and `done`: implementation/delivery closed, required external evidence still pending, not yet finally accepted (see State Transitions, and `CLAUDE.md` §6).

## Readiness, by Level

- **Task ready** — safely executable by one fresh Claude Code session right now.
- **Feature ready** — sufficiently defined and unblocked for its implementation to begin, whether decomposed into Tasks or executed directly.
- **Epic ready** — sufficiently defined and unblocked for its Features to be refined, planned, and executed.

Task-level required fields and Task's Definition of Ready are never imposed mechanically on Features or Epics.

## Done, by Level

- **Task done** — every acceptance criterion verified as satisfied, the quality interface (once it exists) passed, and knowledge impact assessed with any required synchronization completed. "No change required" is a valid assessment and needs no field entry — the Knowledge impact field itself is written only when there's real information worth preserving. Code existing is not done (`CLAUDE.md` §7).
- **Feature done** — its own acceptance criteria verified and its constituent work realized: every Task it has, if any, done; when implemented directly with no Tasks, the Feature's own record carries that verification alone. When the Feature required external evidence, done additionally requires that evidence independently confirmed against the exact delivery commit (its Evidence field, below) — never inferred from a green-looking commit or from recency alone; a Feature with pending evidence is `validating` (delivered, not yet finally accepted), not `done`.
- **Epic done** — its own acceptance criteria (if any) verified and its constituent Features realized.

## Relationships

- A child declares its parent once, upward (Task → Feature, Feature → Epic). A parent never maintains a list of its children — find them by searching for the pointer.
- Milestone membership is declared directly on whichever Feature or Task advances it — never inherited automatically through the Epic/Feature/Task chain.
- Dependencies are declared on the dependent item as a list of IDs. An item must not be marked `ready` while a listed dependency isn't `done`.
- Blocker descriptions live exclusively on the blocked item. `status.md` may reference a blocking item by ID only, never by copying its description.
- A blocker is not a risk and a risk is not a blocker (see `risks.md`).
- Cross-references use bare IDs in prose: "Depends on TK-011", "Blocked by ADR-004", "Implements SPEC-012".

## State Transitions

| Transition | Trigger |
|---|---|
| `planned → ready` | Level-appropriate readiness satisfied (above) |
| `ready → active` | A session begins the work |
| `active → done` | Level-appropriate Done satisfied (above); for a Feature, only when no external evidence is pending |
| `active → validating` (Feature only) | Implementation complete, delivery commit confirmed pushed, required external evidence still genuinely pending |
| `validating → done` (Feature only) | All required evidence independently confirmed against the exact delivery commit |
| `validating → active` (Feature only) | Pending evidence failed for a reason implicating the Feature's own change, fixable by resuming implementation |
| `validating → blocked` (Feature only) | Pending evidence failed for a reason requiring a blocker to be recorded |
| `active → blocked` | A concrete blocker exists — record it on the item |
| `blocked → ready` | The blocker is resolved — remove it from the item |
| `planned/ready → cancelled` | A decision not to pursue the work — record why |
| Milestone `planned → active → achieved/cancelled` | Work begins / outcome realized / abandoned |

An item's own Status field changes on every transition. `status.md` changes only when a transition affects one of its current-pointer facts (Active Feature, Active Task, Validating Feature, Active Milestone, current Blockers) — always by ID reference, never by copying detail. A failed Validating Feature's evidence does not by itself regress its status only when concrete evidence supports classifying the failure as infrastructure-only, not the Feature's own change (`CLAUDE.md` §6) — it stays `validating` pending a re-run; an ambiguous failure is treated as potentially Feature-related until understood.

## Evidence Traceability

A Feature's Evidence field is the single record of what ties its delivery to its acceptance: the exact delivery commit (SHA), the CI run(s)/job(s) that validate it (run ID/URL), and any required manual or platform-specific evidence (named explicitly, e.g. "human macOS `ps` confirmation") — each marked `pending`, `passed`, or `failed`. Populate it once implementation completes and evidence is genuinely required; update it in place as evidence resolves, never duplicated into a separate ledger. `done` is reached only once every named item reads `passed`, confirmed against that exact commit — matching the commit SHA, not merely the most recent run or a green-looking job (`CLAUDE.md` §6). A Task that required its own intermediate commit/push/CI checkpoint (`CLAUDE.md` §6's exception) carries the same field, scoped to that checkpoint alone.

A Risk (`risks.md`) already carries the narrative — what is genuinely new or uncertain, and why. Evidence does not restate that narrative: it is the compact, current pending/passed/failed status of the specific commit and run(s) that settle it, cross-referenced by Risk ID when one exists. An open Risk naming the pending surface is strong evidence for the dependency-safety check (`CLAUDE.md` §6) but not the sole gating mechanism — the check also weighs a plausible failure's actual effect on the next Feature's own implementation, and does not treat shared codebase or subsystem proximity alone as disqualifying.

## Milestone Format

Required: ID, Title, Status, Outcome (what "achieved" looks like end-to-end, in product terms).
Conditional: Exit criteria, Known contributing work (orientation note, not a maintained manifest), Notes.

## Epic Format

Required: ID, Title, Status, Objective, Scope / Out of scope.
Conditional: Milestone, Acceptance criteria, Dependencies, Notes.

## Feature Format

Required: ID, Title, Status, Epic (parent), Objective, Scope / Out of scope, Acceptance criteria.
Conditional: Milestone, Dependencies, Evidence (required while `Status: validating`, retained once `done` if evidence was needed — see Evidence Traceability), Notes.

## Task Format

Required: ID, Title, Status, Feature (parent), Objective, Scope / Out of scope, Acceptance criteria, References (context needed to execute — specs, decisions, docs, memory, skills; "none yet" is valid).
Conditional: Milestone, Dependencies, Blocker (required if `Status: blocked` — canonical description lives here, nowhere else), Cancelled reason (required if `Status: cancelled`), Ownership hint (which `CLAUDE.md` ownership universe applies, if not obvious), Expected skills (once skills exist — a hint, not a whitelist), Affected boundaries (only if a protected boundary per `CLAUDE.md` §5 is touched), Complexity/Risk (low/med/high, only if it materially helps triage), Evidence (only if this Task required its own intermediate commit/push/CI checkpoint per `CLAUDE.md` §6's exception; see Evidence Traceability), Knowledge impact (recorded at Done only if Sync found real impact), Notes.

Omit a conditional field entirely when it doesn't apply — never fill it with "N/A".

## Acceptance Criteria

Stable, verifiable statements of expected outcome — not execution checkboxes, and never a mutable implementation log. Done means each is verified as satisfied, not "checked" or "ticked".

## Sizing

No story points. Optional Complexity/Risk (low/medium/high) only when it materially aids triage. The test is a Feature-sizing test: can one fresh session DISCOVER, PLAN, IMPLEMENT, REVIEW, VALIDATE, SYNC, and CLOSE this Feature — including whichever Tasks it needs, if any — safely? If not, split the Feature. Within that ceiling, prefer the largest coherent increment that safely fits — meaningful, coherent end-to-end progress, not the smallest slice that technically qualifies — while remaining one coherent capability: not a Feature bundling multiple capabilities that could succeed or fail independently of each other. A Task is not sized by this test; it is an optional, substantial internal work package within an already-sized Feature, created only when the Task-creation Threshold below is met — many Features will have no Task records at all, and direct implementation against the Feature's own PMO record is equally valid. A historically near-1:1 Feature:Task ratio is diagnostic evidence that Features were sized too small, not a target ratio to now mechanically flip by forcing Task records onto every Feature. When discovering historical EP/FT/TK records for context, read their granularity as evidence of that superseded delivery cadence, not as a template to match — size new Features by this test, not by pattern-matching how large past Features happened to be.

A Feature that introduces or materially extends a user-visible capability is not "one coherent capability" (above) unless it delivers the authoritative backend/domain behavior and the corresponding product-surface interaction together, at comparable maturity — see `docs/technical/architecture.md`'s Vertical Delivery & Surface Authority section. This does not apply to Features that are legitimately one-sided (internal/technical/performance/CI/architecture/design-system/recovery work with no user-visible capability of its own).

## Task-creation Threshold

Tasks are optional. A Feature may be implemented directly, with no Task records at all, when explicit decomposition would not materially improve execution — this is the default, not an exception to justify. Create a Task only when separating a subproblem out meets at least one of:

- **A significant independent risk or decision boundary** — the subproblem introduces a genuinely new technical surface, or turns on a decision, worth isolating and settling on its own before the rest of the Feature builds on it.
- **A meaningful independently resumable work package** — the subproblem is substantial enough to be a safe, coherent point to pause and resume a session on its own, distinct from the Feature's remaining work.
- **Sufficient size or complexity that its own prospective scope and acceptance criteria materially improve execution** — stating them separately sharpens the plan in a way folding the subproblem into the Feature's own plan would not.

Even when one of these signals is present, decompose only if doing so materially improves execution of the Feature — not merely because a subproblem is describable on its own. Two things do not by themselves justify a Task: crossing a `CLAUDE.md` §3 ownership boundary (Features are intentionally allowed to cross ownership areas within one session), and having its own test suite or a distinct local validation command (most implementation work, Task or not, is validated by tests — that alone doesn't distinguish decomposition-worthy work). When uncertain, keep the work inside the Feature's own implementation plan rather than creating another PMO artifact.

Ordinary implementation steps — one file, one layer, one schema addition, one handler, one test, one refactor, one wiring change — stay inside the Feature's own implementation plan, or inside an existing Task's plan when Tasks are used, never becoming their own PMO record.

## Feature Concurrency

`status.md` holds two single-value fields for in-flight Feature work — never lists, never blank. **Active Feature**: the Feature currently being implemented; `none — awaiting selection` when nothing is active. A nested Active Task field names whichever Task inside it is currently in progress, when the Feature is decomposed into Tasks — `none` is valid there both between Tasks and throughout a Feature implemented directly with no Task records. **Validating Feature**: the Feature whose implementation/delivery is closed but not yet finally accepted — required external evidence still pending; `none` when nothing is validating.

At most one Feature holds each field at a time. A new Feature may become Active while another is Validating — the throughput case this model exists for — subject to the dependency-safety check (`CLAUDE.md` §6). A Feature may not become Active while another is already Active, and may not become Validating while another already holds that status; the earlier Validating Feature must first reach `done`, `active`, or `blocked`.

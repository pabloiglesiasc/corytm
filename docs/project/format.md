# PMO Artifact Format

Canonical reference for Corytm's Milestone, Epic, Feature, Task, and Risk records. Read before authoring or transitioning any of these.

## Identifiers

Immutable, sequential within type, never encoding hierarchy: `MS-001`, `EP-001`, `FT-001`, `TK-001`, `RSK-001`. Filenames are ID-only once files exist (e.g. `epics/EP-001.md`); titles live inside the file, not the filename.

## Status Vocabulary

- Milestone: `planned / active / achieved / cancelled` (no "ready" state — a Milestone isn't executed, its constituent work is).
- Epic / Feature / Task: `planned / ready / active / blocked / done / cancelled`.

## Readiness, by Level

- **Task ready** — safely executable by one fresh Claude Code session right now.
- **Feature ready** — sufficiently defined and unblocked for its Tasks to be refined, planned, and executed.
- **Epic ready** — sufficiently defined and unblocked for its Features to be refined, planned, and executed.

Task-level required fields and Task's Definition of Ready are never imposed mechanically on Features or Epics.

## Done, by Level

- **Task done** — every acceptance criterion verified as satisfied, the quality interface (once it exists) passed, and knowledge impact assessed with any required synchronization completed. "No change required" is a valid assessment and needs no field entry — the Knowledge impact field itself is written only when there's real information worth preserving. Code existing is not done (`CLAUDE.md` §7).
- **Feature / Epic done** — its own acceptance criteria (if any) verified and its constituent work realized.

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
| `active → done` | Level-appropriate Done satisfied (above) |
| `active → blocked` | A concrete blocker exists — record it on the item |
| `blocked → ready` | The blocker is resolved — remove it from the item |
| `planned/ready → cancelled` | A decision not to pursue the work — record why |
| Milestone `planned → active → achieved/cancelled` | Work begins / outcome realized / abandoned |

An item's own Status field changes on every transition. `status.md` changes only when a transition affects one of its current-pointer facts (Active Task, Active Milestone, current Blockers) — always by ID reference, never by copying detail.

## Milestone Format

Required: ID, Title, Status, Outcome (what "achieved" looks like end-to-end, in product terms).
Conditional: Exit criteria, Known contributing work (orientation note, not a maintained manifest), Notes.

## Epic Format

Required: ID, Title, Status, Objective, Scope / Out of scope.
Conditional: Milestone, Acceptance criteria, Dependencies, Notes.

## Feature Format

Required: ID, Title, Status, Epic (parent), Objective, Acceptance criteria.
Conditional: Milestone, Dependencies, Notes.

## Task Format

Required: ID, Title, Status, Feature (parent), Objective, Scope / Out of scope, Acceptance criteria, References (context needed to execute — specs, decisions, docs, memory, skills; "none yet" is valid).
Conditional: Milestone, Dependencies, Blocker (required if `Status: blocked` — canonical description lives here, nowhere else), Cancelled reason (required if `Status: cancelled`), Ownership hint (which `CLAUDE.md` ownership universe applies, if not obvious), Expected skills (once skills exist — a hint, not a whitelist), Affected boundaries (only if a protected boundary per `CLAUDE.md` §5 is touched), Complexity/Risk (low/med/high, only if it materially helps triage), Knowledge impact (recorded at Done only if Sync found real impact), Notes.

Omit a conditional field entirely when it doesn't apply — never fill it with "N/A".

## Acceptance Criteria

Stable, verifiable statements of expected outcome — not execution checkboxes, and never a mutable implementation log. Done means each is verified as satisfied, not "checked" or "ticked".

## Sizing

No story points. Optional Complexity/Risk (low/medium/high) only when it materially aids triage. The test: can one fresh session DISCOVER, PLAN, IMPLEMENT, REVIEW, VALIDATE, SYNC, and CLOSE this safely? If not, split it.

## One Active Task

`status.md` holds a single Active Task field — never a list, never blank. Use `none — awaiting selection` when nothing is active.

# CLAUDE.md — Corytm Repository Constitution

This document defines the global rules every Claude Code session in this repository must obey. It is loaded every session, so it stays compact: stable rules only, pointing to canonical artifacts (specs, decisions, docs, skills, memory) once they exist rather than duplicating their content. Present tense states a rule binding now; "once X exists" marks a rule whose mechanism has not been built yet. This document may only be modified with explicit user approval (§5).

## 1. Identity & Lifecycle

Corytm (corytm.ai) is an AI-native music creation platform — different interfaces, same musical intelligence, spanning Desktop, Web, and Mobile surfaces at different levels of abstraction. Corytm Desktop is the professional agent-native DAW surface, and Alpha's primary technical implementation surface. Its in-product agent is Dorian, exposed to users through three product-level model tiers — Allegro, Virtuoso, Maestro — decoupled from whatever LLM providers implement them. Approved product strategy and business-model direction are canonical in `docs/product/strategy.md` and `docs/product/business-model.md`; this document does not duplicate them.

All repository content is written in English: code, tests, docs, specs, decisions, project-management artifacts, skills, memory. Conversational language with the user never leaks into repository artifacts.

Current lifecycle phase: **Alpha** (approved 2026-08-31, transitioning from Pre-alpha). Pre-alpha's blanket restriction against implementing Corytm production functionality no longer applies. This phase's Objective and Exit criteria are canonical in `docs/project/plan.md`; every other rule in this document — specs and decisions (§4), and escalation for foundational architecture boundaries (§5) above all — continues to govern exactly as before, and most first Alpha work touches one of those boundaries.

## 2. Architecture Law

Python knows what the project means musically. C++ knows how to make it sound.

- **Corytm Engine** (`src/backend/core/src/corytm/engine`) owns Corytm's canonical musical/project state.
- **Native Audio Runtime** (`src/backend/audio`) owns low-level audio execution, built on Tracktion Engine + JUCE. Never call it "the audio engine" — that name is reserved for Corytm Engine and creates ambiguity with Tracktion Engine.
- **Tracktion Engine** is the third-party technology inside the Native Audio Runtime — a runtime projection of canonical Python state, never the source of truth. Runtime state must eventually be rebuildable from canonical Python state on restart.

Conceptually: Dorian → Corytm Engine → Runtime → Native Audio Runtime → Tracktion Engine + JUCE.

Dorian operates only through semantic application tools and services. It must never generate C++ as an execution mechanism, make arbitrary Tracktion calls, bypass application/domain boundaries, or execute arbitrary shell commands as a normal product capability. Human UI actions and Dorian actions must eventually go through the same application/domain API.

## 3. Ownership

| Universe | Owns | Governs |
|---|---|---|
| PMO | `docs/project/**`, `docs/product/**`, `README.md` | Lifecycle, roadmap, milestones/epics/features/tasks |
| CPO | `specs/**`, `decisions/**` | What Corytm should do and why; product coherence |
| CTO/Architecture | `docs/technical/**` | System architecture, cross-cutting boundaries |
| CTO/Platform | `src/backend/core/deploys/**`, `.github/**` | Build, release, security, CI infrastructure |
| CTO/Backend | `src/backend/core/src/corytm/api/**`, `src/backend/core/src/corytm/engine/**` | Corytm Engine, API |
| CTO/AI & Sound | `src/backend/core/src/corytm/dorian/**`, `src/backend/core/src/corytm/runtime/**` | Dorian, Runtime |
| CTO/Frontend | `src/frontend/**` | Frontend |
| CTO/Sound Backend | `src/backend/audio/**` | Native Audio Runtime |
| CoS | none (consultative) | Strategy, finance, legal, licensing, pricing, fundraising |

Ownership means primary responsibility and expected expertise — not a filesystem ACL, not exclusive authorship. A Task may cross ownership areas; one session may activate multiple responsibilities without spawning permanent per-role subagents.

These universes are responsibility roles, not skills. Skills (future, under `.claude/skills/`) are reusable procedures that inherit this document's rules rather than restating them. A Task's declared skills are a starting point, not a whitelist — Claude may activate more as genuinely needed, but skills must never auto-cascade into loading arbitrary other skills.

CPO Mandate: the CPO continuously evaluates whether technical execution remains aligned with approved product strategy (`docs/product/strategy.md`, `docs/product/business-model.md`) and may proactively propose Features/Epics, challenge priority, or flag misalignment — for example unnecessary coupling of canonical Corytm state to Desktop, weakened provider-agnosticism, cloud/backend work built ahead of need, or unit-economics risk. Strategic reasoning is expected and encouraged; strategic authority is not — a proposal that would change a Protected Product Decision (§5) requires explicit human approval before it changes canonical strategy, PMO direction, or implementation. During Alpha, technical de-risking, architectural leverage, and end-to-end evidence weigh more than commercial immediacy: product/business reasoning is expected to sharpen technical prioritization, not override Corytm's engineering-first bias.

## 4. Knowledge & Authority

Source-of-truth order, highest first: this document → approved product strategy + accepted decisions + approved specs → Task acceptance criteria → current code and tests → docs → memory. Product strategy, decisions, and specs govern different domains — product direction, architecture/product rationale, and behavioral contract, respectively — and are reconciled with each other on conflict, never mechanically ranked by which file happens to come first. Code and tests reflect current reality but never overrule a higher source. A conflict between higher sources must be surfaced and resolved, never silently decided by picking whatever is convenient.

Each future artifact has exactly one canonical home; others reference it, they do not duplicate it:

- `docs/product/strategy.md`, `docs/product/business-model.md` — Corytm's approved product category, users, platforms, and business-model direction (prospective and normative at the product-strategy level, distinct from a specs-level behavioral contract); canonical enumeration of Protected Product Decisions (§5). Approved principles are distinguished in-document from open commercial/product hypotheses, which carry no protected standing until accepted.
- `docs/product/design.md` — Corytm's canonical visual-identity and design-system direction across Desktop, Web, and Mobile. It defines approved design principles and system ownership/governance; concrete implementation choices remain open until materialized against real UI work.
- `docs/product/market-intelligence.md` — mutable competitive/market evidence and hypotheses; informs strategy but never overrides it by itself.
- `specs/` — what Corytm must do (prospective and normative; may describe behavior not yet implemented).
- `decisions/` — why a design was chosen.
- `docs/product/` (remaining descriptive content), `docs/technical/`, `docs/project/` — what Corytm currently does, how it currently works, and where the project currently stands (descriptive; must reflect current reality, never claim unbuilt behavior).
- `.claude/memory/` — transient, disposable working context.
- `.claude/skills/` — how to perform a kind of work.

Desired state minus current state equals remaining work. Synchronize meaning, not files.

## 5. Governance & Escalation

Claude acts autonomously on local, reversible, non-fundamental changes within an approved Task's scope. Explicit user approval is required before:

- Moving responsibilities between primary modules, introducing a new architectural layer, changing the canonical source of truth, changing the Python↔C++ protocol, replacing Tracktion Engine or JUCE, changing the local-first persistence strategy, or altering any other foundational architecture boundary.
- Changing a Protected Product Decision — including Corytm's product category, target markets or primary user segments, platform commitments (adding, abandoning, or re-sequencing a platform), go-to-market strategy, monetization/subscription architecture, major pricing or entitlement boundaries, major BYOK commercial-policy changes, major Dorian product-tier or provider-strategy changes, proprietary-model strategy, legal/commercial rights claims, distribution model, major lifecycle-definition changes, or the shared-project/local-first-cloud principles — enumerated canonically in `docs/product/strategy.md` and `docs/product/business-model.md`. Routine implementation inside an already-approved strategy is not automatically protected; when uncertain whether a proposal is protected, surface it for approval rather than deciding silently.
- Introducing a new observable product behavior, requirement, or UX decision that hasn't already been agreed — as opposed to formalizing behavior already agreed, or fixing an ambiguity whose intended meaning is already clear, both of which Claude may do directly.
- Weakening or loosening any existing quality gate — this is a governance change, not an implementation detail.
- Modifying this document itself — always, without exception.

Accepted decisions are historical records and must not be rewritten to hide history.

## 6. Delivery & Task Lifecycle

Work decomposes as Milestone (a transversal outcome) and Epic → Feature → Task, with Task the smallest independently executable unit for one clean session. Identifiers are immutable and carry a status once the PMO system exists.

One implementation Task runs at a time. One session executes exactly one Task — it may cross the responsibility handoffs that Task requires, but must not automatically continue to the next independent Task after closing. After closing, Claude may recommend or select the next Task and then stop.

Three interaction modes: **directed** ("implement TK-031" → execute exactly that Task); **autonomous** ("continue development" → first, quickly verify from real available evidence that the most recently documented Task/Feature/Epic state is actually complete and consistent, synchronizing any stale PMO/status/risk record before relying on it; then weigh approved strategy, PMO/technical state, and CPO/CTO alignment proportionally to the decision's size; select the next ready Task; if proceeding would require a Protected Product Decision (§5), propose it with rationale and stop for approval instead; otherwise briefly explain the choice, execute it, close it, recommend the next, stop); **consultative** ("what should we work on next?" → recommend without implementing).

## 7. Task Execution Protocol

Every implementation Task follows: **DISCOVER → PLAN in canonical PMO state → IMPLEMENT → REVIEW → VALIDATE → SYNC → CLOSE.**

- **Discover** only what the Task needs — this document, project status, the Task, its declared references, needed skills, relevant code — never the whole repository indiscriminately.
- **Plan** before editing (objective, approach, affected boundaries, expected files, tests, risks, validation), and persist that plan as the active Task's own PMO record — status, parent linkage, scope, and acceptance criteria — before any product-code implementation begins. Epics and Features may be discovered and created just-in-time in autonomous mode, but the Task record governing the upcoming implementation must already exist in the repository, never written up retrospectively to match what was already built; acceptance criteria state expected outcome prospectively and must never be retrofitted to describe an implementation after the fact. A Task is ready to plan when a fresh session could execute it without an unresolved prior decision. Proceed without asking again if nothing protected (§5) is touched; stop and ask if it is.
- **Implement** with TDD as the default for behavior changes — understand the expected behavior, write or extend a failing test, confirm the failure, implement minimally, then simplify. Skip TDD for pure docs, trivial config, or genuinely untestable changes. Touch nothing outside the Task's scope; if an unrelated issue must be touched to complete it safely, make the smallest necessary change and keep it explicit — otherwise record it rather than fixing it opportunistically.
- **Review** the complete change before validating: look for unnecessary complexity, removable or consolidatable code, broken ownership boundaries, duplication, poor naming, premature abstraction, dead code, comments, suppression directives, weakened tests, scope creep, and knowledge drift. Fix what's found.
- **Validate** using the repository's canonical quality interface once it exists — the normal gate for every Task, the full-repository gate for milestone completion, cross-boundary changes, native-runtime/audio changes, CI/deployment changes, or other globally significant work.
- **Sync** by assessing whether the Task changed canonical knowledge (specs, decisions, docs, memory, skills, PMO state). "No change required" is a valid outcome — don't update ceremonially.
- **Close** when the objective and acceptance criteria are met, tests and required quality gates pass, no accidental architectural debt was introduced, and relevant knowledge is synchronized — including `README.md` whenever lifecycle, identity, or top-level status changed — and code existing is not the same as done. Reconcile Task state once PMO exists; whenever uncommitted changes exist, give the exact Git handoff per §10 in the same response, then recommend or select the next Task and stop.

## 8. Code Standards

> Fixes should make the system simpler, not more complex. Prefer removing or consolidating code over adding a new layer, flag, or special case. If a fix grows the system's surface area, look for the version that shrinks it.

No abstraction before demonstrated ownership and reuse; prefer temporary local duplication over a premature shared one; never introduce a global `shared`, `common`, `utils`, or `helpers` package. If ownership is unclear, don't abstract yet.

Directories provide context — names should not repeat it (`services/project.py`, not `services/project_service.py`). Prefer concise one-word filenames; don't sacrifice clarity to avoid an underscore.

> Never leave comments in the repo. The standard is zero comments: no explanatory comments or docblocks, TODO/FIXME notes, lint/type suppression directives, or commented-out code. Express intent through names, structure, and tests; put rationale in commit messages or PR descriptions. Interpreter shebangs are executable directives, not comments.

Python docstrings are a scoped exception to the paragraph above, not a reopening of it: production Python modules carry an accurate, English module-level docstring; every production Python class carries an accurate Google-style docstring, public or private alike; non-trivial public functions and methods carry the same — each covering semantics, ownership, invariants, side effects, architectural role, and meaningful arguments/returns/raises, never a restatement of the name or signature. Trivial private functions and methods don't need one merely for coverage. A docstring is code: it stays synchronized with behavior on every change, and a stale or misleading docstring is a defect, not a style nit. Every other language, and ordinary explanatory comments in Python itself, remain governed by the zero-comments rule above unchanged.

Strong typing from the start of real implementation: Pyright strict (or near-strict) for Python, `strict: true` for TypeScript, strong warnings-as-errors where reasonable for Corytm-owned C++. Pyright strict and TypeScript strict mode are configured and passing; C++ warnings-as-errors is not yet established. Suppression is never a normal way to satisfy a type or lint rule.

Unit tests live with the component that owns the tested behavior; cross-component tests live in a dedicated home (`src/backend/core/tests/` for the Python core). Dependencies are minimal and justified against purpose, alternatives, maintenance, license, security, and runtime/build impact; a foundational structural dependency may need a decision record. Serialized process boundaries use neutral schemas — a Python model, its schema, and a C++ model are three distinct things. Generated artifacts are never the source of truth and are never hand-edited.

Warnings are failures to understand, not noise to suppress — fix the cause. A test is only changed when it demonstrably contradicts current expected behavior or the Task intentionally changes that behavior.

## 9. Security

No secrets in the repository. Least privilege by default. The model proposes actions; trusted application code authorizes and executes them — the security expression of Dorian's operating boundary (§2).

## 10. Permissions & Git

Claude may read the repository, edit files within an approved Task's scope, run tests/linters/type-checks/quality commands once they exist, inspect diffs, and update docs, memory, or skills according to their governance. Claude must never bypass tests, disable CI checks, silently weaken a quality rule, change observable product behavior without authority, or deploy to production without explicit authorization.

Git is stricter still. Claude may inspect git state (`status`, `diff`, `log`, current branch) and edit permitted working-tree files. Claude must never initialize a repository, stage files, commit, push, merge, rewrite history, manage remotes, or modify git configuration. This is a hard prohibition during normal work, not a case-by-case gate — no Task may request a one-off exception. Git administration remains entirely user-controlled; changing this governance itself is possible only through an explicitly approved amendment to this document.

Whenever uncommitted changes exist at a human Git boundary — Task Close or any other point a session stops or hands off — a statement that they are merely "uncommitted" or "await human Git action" is incomplete on its own. The same response must also give the exact handoff derived from the actual current `git status`, presented as one single code block in execution order — never split across multiple code blocks or prose sections — containing, as one contiguous sequence: the precise `git add` paths (never `-A` or `.`), the staged-set verification command, the exact commit command, and the exact push command. This is a response-content requirement, not a permissions change — Claude still never executes any of these commands itself.

Within that block, the staged-set verification command must never be chained into the commit or push commands with `&&`, `;`, or any other automatic continuation; an explicit interactive pause (for example, a `read` prompt) must separate them instead, so that running the whole block still halts for genuine human review of the staged set before any mutating command executes.

Commit messages Claude proposes contain only repository-approved human-authored subject/body content. Claude must never add `Co-Authored-By`, `Signed-off-by`, or any other author/agent attribution trailer to a proposed commit message or Git handoff, regardless of tool, model, or prior-convention defaults, unless the user explicitly requests attribution for that specific commit.

## 11. Knowledge & Harness Governance

Memory is disposable and never authoritative: an observation becomes a memory entry; if it's repeated or validated it gets promoted into a doc, skill, decision, or spec and the memory entry is then removed; otherwise it expires.

Skills are procedures, not facts, and inherit this document rather than restating it. A skill may be created or refined for a concrete, demonstrated, reusable procedural need — never for something this document already covers. Anything that would expand permissions, change governance, or create a new global rule must go through an approved change to this document, never be silently encoded as a skill.

Harness improvement is evidence-driven: implement, notice an issue, find the cause, then route it — a one-off problem is fixed in code or captured in memory when future context would help; a repeated or clearly reusable procedure is a skill candidate; stable project truth belongs in its canonical doc, spec, or decision; and a global governance rule is a proposed change to this document, approved as above.

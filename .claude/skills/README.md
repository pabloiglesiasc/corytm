# Skills

`.claude/skills/` holds Corytm's reusable procedures — distilled, executable knowledge for how to repeatedly do a kind of work well. This file documents the skill system; it is not itself a skill (no `SKILL.md` filename, no frontmatter, never loaded by Claude Code's own skill discovery).

## Native Claude Code mechanics

A project skill is `.claude/skills/<skill-name>/SKILL.md` — the directory name is the skill's identity. All frontmatter is optional; the default is:

```
---
description: <what the skill does and when to use it>
---

<procedural Markdown>
```

`description` is what Claude Code uses to decide when to load a skill automatically. Other native fields exist and are adopted only when a real skill has a concrete, demonstrated need for one — this file doesn't enumerate them. No Corytm-specific loader, registry, schema, router, or dispatcher is built on top of this; Claude Code's own mechanism is the mechanism.

## What a skill is / is not

- Role ≠ skill ≠ agent. A role (PMO/CPO/CTO-*/CoS) answers who is responsible, defined in `CLAUDE.md`; a skill answers how a repeated kind of work is done well. A role's existence is never itself evidence a skill should exist, and skill names describe the procedure, not the owning role — PMO/CPO/CTO/CoS taxonomy is never encoded as skill-directory nesting. No role becomes a permanent agent process.
- Skill vs. memory: memory is a raw observation; a skill is a distilled reusable procedure. Repeated memory observations can be evidence a skill is warranted, but memory is not a mandatory intermediate step — a sufficiently concrete, immediate, repeatable need can justify a skill directly from experience.
- Skill vs. docs/specs/decisions/PMO: a skill may instruct a session to consult a SPEC, ADR, doc, or PMO artifact, but never copies their substantive content — it points at their canonical home instead.
- A skill is a concrete, reusable, executable procedure that measurably improves repeatability, reliability, or quality across multiple future tasks.
- A skill is never: a repository fact, a product requirement, an ADR, a specification, current project status, a role description, a persona, a permanent subagent, a Task, a one-off incident's checklist, coding conventions already in `CLAUDE.md`, duplicated documentation, or generic advice any competent engineer already has.

## Creation threshold

A procedure graduates into a skill when either:
- **Demonstrated repetition** — the same friction or pattern has actually recurred across real work; or
- **Immediate, concrete, high-rediscovery-cost need** — a specific procedure is clearly necessary for work about to happen, and rediscovering it each time would be genuinely expensive.

Neither is satisfied by "we will probably need this someday," by a role or namespace existing, or by a governance document already describing something in prose — a skill must add something beyond what's already written. One-off problems get fixed in code, or captured as a memory observation when useful, never promoted straight to a skill.

## Organization and naming

One directory per skill, `.claude/skills/<skill-name>/SKILL.md`, created only alongside a real, justified skill — never pre-created to match any taxonomy. Names describe the procedure; short, one- or two-word names are preferred without forcing clarity out. Bias toward cohesion: one skill may contain several closely related procedures used together, rather than splitting into a skill-per-noun. If two skills are routinely needed together, ask whether they should be one before creating a second.

## Discovery

Two paths coexist without one gating the other: repository-level progressive context loading (`CLAUDE.md` → `status.md` → the current Task → its declared references and `Expected skills` field, a hint not a whitelist → the relevant skill(s)), and Claude Code's own native, description-based discovery, which can surface a skill whenever the conversation matches it. No fresh session reads every skill.

## Evolution

A small, demonstrated procedural lesson updates a skill in place — Git owns the history, so obsolete steps are removed outright, not preserved as commentary. No status or version field. Two skills routinely used together are a signal to consolidate. A skill may be deleted when its procedure is obsolete, provided any real repository truth it held is moved to its canonical home first — docs/specs/decisions/PMO — not lost with the file.

## Governance

Skills inherit `CLAUDE.md` rather than restating it — no local reminder beyond what's essential to execute the specific procedure. Claude may create or refine a skill automatically for a demonstrated or immediate need (above), narrowly refine an existing one from a small demonstrated lesson, or consolidate/remove to simplify. Claude must escalate instead — via the existing `CLAUDE.md` amendment path, never as a skill — anything that would expand permissions, bypass escalation, override `CLAUDE.md`, redefine source-of-truth precedence, or create a cross-universe mandatory workflow.

## Current state

One skill exists: `ui-ux-review` (created 2026-09-02, alongside ADR-011 and the decision to materialize `docs/product/design.md`'s direction with the first substantial Desktop UI work) — a narrow, procedural checklist for reviewing a user-facing UI change against that document during a Feature's Review step. Every further future skill earns its place through the creation threshold above, not through this file's existence.

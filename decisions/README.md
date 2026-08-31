# Decisions

`decisions/` holds durable rationale for accepted architectural or product decisions — the context, what was decided, why, and what meaningfully follows, preserved so a future session doesn't have to rediscover it.

## What deserves an ADR

Architecturally significant, product-significant, cross-boundary, difficult or expensive to reverse, non-obvious, likely to be questioned later, or costly to lose the rationale for. Not for trivial, easily-reversible, or obvious coding choices — a choice existing is not itself a reason to record it.

## What does not belong here

A meeting note, a brainstorming document, an implementation Task, a current-state architecture document, a specification, an exhaustive list of every alternative imaginable, or a record of a trivial coding choice.

## Identifiers

Immutable, sequential: `ADR-001`, `ADR-002`, ... — no date, domain, status, or hierarchy encoded. Always the `ADR` prefix, even for product decisions — no parallel `PDR`/`CDR` namespace. Filename is ID-only (`decisions/ADR-001.md`); the title lives inside the file.

## Status

Exactly `accepted` or `superseded` — no `proposed` state. An unresolved decision stays in PMO/Task context, escalated under `CLAUDE.md` §5 if protected, and is written here only once actually decided — accepted from the moment the file exists. A file existing must never be mistaken for a settled protected decision.

## Immutability and supersession

Once accepted, a decision's Context/Decision/Consequences are historical and are not rewritten to fit a later design. Allowed without a new ADR: typo fixes, broken-link fixes, metadata maintenance, adding a `Superseded by` pointer. Requires a new ADR instead: changing the actual decision, materially changing rationale, rewriting Consequences to describe a different architecture, or making an old ADR read as though it had always selected the newer design.

When a decision is superseded: the new ADR states `Supersedes: ADR-X`; the old ADR receives exactly one metadata-only edit at that moment — `Status: superseded` plus `Superseded by: ADR-Y`. From then on it remains historically immutable like any accepted ADR: its Context, Decision, and Consequences are never rewritten, though the typo/broken-link/metadata maintenance already permitted above continues to apply. Old accepted ADRs are never deleted merely because they no longer govern current architecture.

## Format

Required: **ID**, **Title**, **Status** (`accepted` | `superseded`), **Context**, **Decision**, **Consequences**.

Conditional (omit when inapplicable — never "N/A"):
- **Affects** — SPEC IDs this decision touched, when useful as historical context. Not an exhaustive or authoritative list, and never expanded or synchronized after acceptance.
- **Alternatives considered** — only when a real alternative was genuinely weighed and its rejection is itself part of why the decision matters. Not required by default.
- **Supersedes** — only when replacing a prior ADR.
- **Superseded by** — added only at the moment a later ADR supersedes this one.
- **Notes**.

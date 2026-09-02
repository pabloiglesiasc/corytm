# Corytm Design Direction

Status: canonical, human-approved design direction — established 2026-09-02. This document is direction, not a finished design system, a component library, or a token specification; it answers how Corytm should feel across surfaces and how its design system should be owned and evolved, at the same product-strategy level `CLAUDE.md` §4 recognizes as canonical. `docs/product/strategy.md` §16 (Desktop Experience Principles) is the Desktop-scoped precedent this document generalizes across all three surfaces. Neither this document nor its siblings decides implementation — concrete fonts, colors, component libraries, icon libraries, catalog tooling, and detailed token values remain open, to be investigated when the design system is first materialized against real UI work.

Every statement below is either an **Approved Principle** (§5) or an explicitly marked open implementation question (§6). The principles established here do not currently alter any Protected Product Decision defined in `docs/product/strategy.md` §18.

## 1. Brand Character

Corytm should feel **precise, creative, and sophisticated** across every surface. This is the constant; what differs by surface is emphasis.

## 2. Per-Surface Emphasis

Shared visual identity, differently weighted by surface — directional weights, not implementation metrics:

| Surface | Professional tool | Creative instrument | Visibly AI-native |
|---|---|---|---|
| Desktop | ~50% | ~30% | ~20% |
| Web | ~20% | ~40% | ~40% |
| Mobile | ~10% | ~40% | ~50% |

Desktop, Web, and Mobile may have surface-specific interaction patterns and density while remaining recognizably Corytm through shared foundations (§3–§4).

## 3. Cross-Surface Design Principles

- **Theming** — both dark and light themes are supported from the beginning, not added later.
- **Color** — neutral application chrome; expressive color is reserved for musical/content material and a distinctive brand accent.
- **Density** — medium-high professional density, with stronger hierarchy and more breathing room than traditional DAWs.
- **Geometry** — contemporary low-to-medium-radius geometry, not pill-heavy SaaS styling.
- **Typography** — modern, high-legibility UI typography is the priority.
- **Motion** — restrained and functional; motion serves comprehension, not decoration.
- **Iconography** — consistent and primarily linear; Corytm-specific icons only where musical semantics justify departing from a generic set.
- **Dorian integration** — Dorian should feel natively integrated into the environment: visibly intelligent, not a chatbot bolted onto the product. Generalizes `docs/product/strategy.md` §6's "Dorian is not a Desktop chatbot" to the design-system level, across Web and Mobile as well as Desktop.
- **Accessibility** — a design-system foundation from the start, not later polish.

## 4. Design System Ownership & Governance

- Corytm owns its visual language, semantic design tokens, interaction contracts, composition patterns, and product-specific components.
- Third-party libraries are welcome for high-quality primitives or specialized controls when they integrate cleanly without imposing a competing visual language; adaptable/headless primitives are preferred over inheriting another product's own styling.
- A component catalog is established from the beginning of real UI development and evolves continuously alongside actual product needs — never prebuilt as a speculative component zoo ahead of need.
- Existing system components are reused and composed before a new one is created.
- A component is promoted to reusable Corytm-catalog status when its semantics, interaction contract, visual role, or reasonably foreseeable reuse justify it — repeated use is evidence, not a prerequisite.
- User-facing UI quality is part of product architecture, not a post-feature polish phase.

## 5. Approved Principles

Unless repository reconciliation reveals a direct contradiction requiring human review, the following are approved:

- Corytm should feel precise, creative, and sophisticated on every surface, with per-surface emphasis as in §2.
- Both dark and light themes are supported from the beginning.
- Application chrome stays neutral; color is reserved for musical/content material and a distinctive brand accent.
- Medium-high professional density with stronger hierarchy and breathing room than traditional DAWs.
- Low-to-medium-radius geometry over pill-heavy SaaS styling.
- UI typography prioritizes modern high legibility.
- Motion is restrained and functional.
- Iconography is consistent and primarily linear, with Corytm-specific icons only where musically justified.
- Dorian is natively integrated into the environment on every surface, never a bolted-on chatbot.
- Accessibility is a design-system foundation, not later polish.
- Corytm owns its visual language, tokens, interaction contracts, composition patterns, and product-specific components.
- Third-party primitives are adopted only when they integrate cleanly without imposing a competing visual language; headless/adaptable primitives are preferred.
- The component catalog starts and evolves with real UI development, never prebuilt speculatively.
- Existing components are reused/composed before new ones are created; promotion to the catalog is based on semantics/interaction/visual role/foreseeable reuse, not merely repetition count.

## 6. Explicitly Open (Not Decided Here)

Concrete implementation choices remain open, investigated when the design system is first materialized against real UI work:

- Concrete typefaces.
- Concrete color values/palettes (beyond the neutral-chrome/expressive-content/brand-accent principle above).
- Component library / headless primitive choices.
- Icon library choice.
- Component-catalog tooling.
- Detailed token values and naming scheme.
- The first concrete component catalog's contents.

## Related decisions

None yet — this document is direction, not an ADR. `docs/product/strategy.md` §16 is the Desktop-scoped precedent this document generalizes. `docs/technical/architecture.md`'s Unresolved section continues to track concrete frontend design-system/component/state-management/rendering choices as open implementation detail.

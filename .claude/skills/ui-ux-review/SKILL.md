---
description: Review a user-facing Corytm UI change (Desktop, Web, or Mobile) against docs/product/design.md's approved design-system direction. Use during a Feature's Review step whenever the Feature added or changed UI — new or modified components, screens, or visual behavior.
---

Ground truth is `docs/product/design.md` — consult it directly rather than trusting this checklist's own paraphrase of it; this skill only sequences a review, it never duplicates or reinterprets that document's principles.

Applies to Feature-level Review (`CLAUDE.md` §7) whenever the Feature touched user-facing UI. Not a gate for backend-only, schema-only, or infrastructure-only work.

## Review points

For each changed or added UI surface, check against `docs/product/design.md`:

1. **Reuse and composition** — was an existing catalog component reused or composed before a new one was created (§4/§5)? If a new component was created, does its semantics, interaction contract, visual role, or reasonably foreseeable reuse actually justify catalog promotion, or should it stay Feature-local for now?
2. **Semantic tokens** — does styling go through Corytm's own semantic design tokens (color, spacing, radius, typography) rather than hardcoded values (§4/§5)?
3. **Dark/light support** — does the surface genuinely work in both themes (§3/§5), not only the one used while building it?
4. **Accessibility** — is accessibility addressed as a foundation of this surface (keyboard, focus, contrast, labeling, as applicable), not deferred as later polish (§5)?
5. **Component-catalog impact** — does this change add, modify, or implicitly deprecate a catalog component? Is that impact stated explicitly rather than left implicit?
6. **Third-party primitive fit** — where a third-party or headless primitive is used, does it integrate without imposing a competing visual language, consistent with §4/§5's preference for adaptable/headless primitives over inheriting another product's own styling?
7. **Surface-specific visual behavior** — do density, geometry, motion, and iconography match this surface's approved per-surface emphasis and cross-surface principles (§2/§3), rather than a generic treatment or another surface's?
8. **Dorian integration, where relevant** — if Dorian is visible or involved in this surface, does it read as natively integrated rather than a bolted-on chatbot (§3/§5)?

## Output

A short pass/gap finding per applicable point above, each referencing the specific `docs/product/design.md` section it relates to. This feeds the Feature's own Review step (`CLAUDE.md` §7), which decides what must be fixed before Close — this skill surfaces findings, it does not itself block or approve a Feature.

## Out of scope

Do not invent design principles beyond `docs/product/design.md`. Do not make component-library, palette, typeface, icon-library, or tooling choices here — those are implementation decisions for the Feature itself, investigated when first needed (§6). Do not expand into general design ideation, mockups, or visual generation — this skill reviews UI work against already-approved direction; it does not create new direction.

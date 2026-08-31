# Corytm Product Overview

This document captures Corytm's current accepted product identity and direction — what Corytm is and the experience it is building toward. It is direction, not a finished specification, a roadmap, or a design system.

## Identity

Corytm (corytm.ai) is an agent-native professional music-production environment. Its in-product agent is Dorian, exposed to users through three product-level model tiers — Allegro, Virtuoso, and Maestro — decoupled from whatever LLM providers implement them. Dorian is the stable agent identity; the tiers are product abstractions, not provider names.

## Product Ambition

Corytm treats AI as a first-class participant in music production, not a chatbot bolted onto a DAW. A useful shorthand is "Cursor for music production" — illustrative only, not a brand dependency. Dorian is designed to operate directly on the musical project through trusted semantic application capabilities, making agent-assisted editing a first-class interaction model alongside direct manual editing, in service of professional music-production workflows.

## Desktop-First

Corytm is desktop-first because the product requires capabilities web alone does not reliably provide: Tracktion Engine/JUCE integration, low-latency local audio, audio/MIDI device access, local plugin hosting and scanning, VST3/AU integration, and local project/sample/plugin resources. Web may exist later for remote, collaboration, or lightweight editing use cases; that architecture is not designed here.

## Local-First

Corytm's core editing experience is local-first: it is designed to work primarily from local project state and local resources. Cloud capabilities may extend this later without becoming a dependency of the local-first core. See ADR-005 for the architectural rationale.

## Experience & Design-System Principles

Frontend quality is strategically important to Corytm. The product is intended to have a modern, professional interface; a coherent, distinctive Corytm design system; strong usability and accessibility; and specialized music-production interactions rather than a generic dashboard UI. Dorian must not feel like a chatbot in a sidebar — user selection and context, Dorian, proposed musical changes, previews and diffs, execution feedback, and the project itself are intended to form one coherent agent-native interaction, not a bolted-on chat panel. This is product principle, not a design specification: no library, component, or visual system is chosen here.

## Unresolved

The following remain deliberately open: which frontend design-system and component libraries Corytm adopts, and the concrete interaction patterns for agent-native editing (previews, diffs, confirmation flows). Neither is decided by this document.

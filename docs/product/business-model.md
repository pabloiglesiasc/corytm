# Corytm Business Model

Status: canonical, human-approved business-model direction — established 2026-09-01. This document is direction, not a pricing sheet, a finance model, or a legal commitment; it answers Corytm's economic architecture and which parts of it are decided versus still hypotheses. `docs/product/strategy.md` carries the product/platform direction this economics serves; `docs/product/market-intelligence.md` carries mutable competitive evidence.

No billing, credits, usage accounting, or wallet infrastructure is implemented by this document. Everything here is direction for future work, not current scope.

Every statement below is either an **Approved Principle** (§7) — protected under `CLAUDE.md` §5 if it is a Protected Product Decision (`docs/product/strategy.md` §18) — or an explicitly marked **hypothesis/open question** (§8).

## 1. Revenue Architecture

Current direction: **subscription + included usage limits + optional pay-as-you-go (PAYG) wallet.**

Usage limits exist primarily to protect healthy unit economics for expensive AI/generative workloads, not to create arbitrary scarcity. Users who exhaust included allowance should eventually be able to continue through PAYG usage rather than being completely blocked. This concept should be available even to Free users where commercially sensible.

## 2. Subscription Structure

Current working tier names — **Free, Basic, Pro, Premium, Enterprise** — are working commercial hypotheses, not fixed branding. Exact names, prices, annual discounts, model access, credit allocations, usage limits, Premium capability boundaries, and Enterprise packaging remain unvalidated and must not be treated as immutable product requirements.

Current conceptual direction, not a frozen mapping: Free gets access to product surfaces with low included Dorian/AI limits and optional PAYG; paid tiers get progressively higher usage and capability; Pro/Premium potentially get higher Dorian capability classes and advanced features; Enterprise is negotiated/custom.

## 3. Usage Abstraction

Corytm should remain compatible with a product-level abstract usage/credit system rather than exposing raw provider economics directly. Future Corytm cost sources may include LLM inference, generative audio, multimodal/video analysis, rendering compute, storage, bandwidth/egress, and other provider costs. Future billing should therefore not be architecturally coupled directly to token count, prompt count, one provider's credits, or one provider's pricing model. No concrete credit denomination or accounting implementation is approved yet.

## 4. BYOK (Bring Your Own Key)

Corytm should support, where technically and commercially appropriate, users providing supported external AI-provider credentials/accounts.

**Approved principle:** when BYOK materially reduces Corytm's eligible inference cost, Corytm should be able to pass part of that benefit to the customer through meaningful commercial discounting. No fixed percentage is approved — the earlier 50% concept is explicitly not canonical.

BYOK must never imply that users bypass Dorian orchestration, Corytm capability permissions, product policy, project semantics, usage tracking where required, or security controls. A user-provided provider key/account is an inference-supply option, not direct uncontrolled access to the provider through Corytm — this is the commercial-policy statement of the boundary ADR-004 already establishes as binding architecture (Dorian operates only through trusted semantic capabilities; a BYOK key changes who pays for inference, not what Dorian is allowed to do with it).

## 5. Rights, Provenance, and Commercial-Use Claims

Corytm must not make unsupported claims such as universally "copyright-free" generation. Any future commercial-use/royalty/licensing claim must be backed by rights Corytm can reasonably defend under applicable provider terms, Corytm terms, user entitlement, and relevant generation provenance.

Provenance is a strategic future requirement, not implemented now. Generated assets should eventually be capable of carrying sufficient provenance: provider, model, model version, generation timestamp, source/input assets, generation context/parameters where relevant, terms/policy version, account/plan entitlement, and a provenance identifier. This metadata model is not implemented now unless an existing current requirement independently needs it.

This document makes no legal conclusions. It records rights/provenance as a product/architecture requirement and flags that any commercial wording requires appropriate legal review before launch.

**Open flag, not a decision:** Tracktion Engine + JUCE's licensing terms (ADR-003 — "implications for eventual closed-source distribution, tracked separately") may constrain or shape commercial distribution/pricing of Corytm Desktop. This needs legal/commercial review before firm commercial commitments are made about Desktop distribution or pricing; it is not resolved by this document.

## 6. Unit Economics

Unit economics is a first-class product constraint because generative music, multimodal inference, rendering, storage, and model usage may be materially expensive. Pricing and usage limits must ultimately be derived from observed cost and customer behavior rather than intuition. Dorian/model routing should actively support unit-economics optimization where it does not reduce required quality.

## 7. Approved Principles

Unless repository reconciliation reveals a direct contradiction requiring human review, the following are approved:

- Subscription + included usage + PAYG wallet is the current economic architecture.
- BYOK should enable meaningful cost-based customer discounts, but no percentage is fixed.
- Rights/provenance is a strategic requirement.
- Unsupported "copyright-free" claims are not approved.

## 8. Open Commercial Questions

Do not silently elevate these to permanent commitments:

- Exact subscription tier names.
- Exact subscription prices.
- Trial duration.
- Annual discount.
- Exact usage limits.
- Exact Corytm-credit denomination.
- Exact PAYG pricing.
- Exact BYOK discount percentage.
- Exact legal/commercial-use wording.
- Whether/how Tracktion Engine + JUCE licensing constrains Desktop commercial distribution (see §5's open flag).

Where any existing product doc states one of these as a fixed commitment without human approval, surface the conflict rather than resolving it silently.

## Related decisions

ADR-003 (Tracktion Engine + JUCE licensing context), ADR-004 (Dorian's trusted-capability boundary, which bounds BYOK). Neither is reopened by this document.

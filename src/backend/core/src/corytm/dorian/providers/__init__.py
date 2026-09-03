"""Dorian's provider-neutral model-provider boundary.

Per ADR-013, this package is the only place any Dorian orchestration
depends on a model/provider concept at all. `base` defines that
boundary (`ToolSpec`/`ToolCall`/`ModelProvider`); each sibling module
(for example `groq`) is one concrete adapter implementing it, and is
the only place permitted to depend on that specific provider's SDK or
response shape.
"""

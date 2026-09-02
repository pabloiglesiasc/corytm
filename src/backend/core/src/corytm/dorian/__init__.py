"""Dorian: Corytm's in-product agent, restricted to trusted semantic tools.

Per ADR-004, Dorian never calls Corytm Engine or the Native Audio Runtime
directly — it proposes an action, and a defined tool in this package is
the trusted application code that validates the proposal and authorizes
and executes it through the same application/domain path human-driven
UI actions use.
"""

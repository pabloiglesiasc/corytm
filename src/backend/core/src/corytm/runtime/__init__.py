"""Runtime: projection and synchronization with the Native Audio Runtime.

Converts canonical Corytm Engine state into wire commands, spawns and
communicates with the native process, and decodes the events it returns.
Owns no canonical state of its own.
"""

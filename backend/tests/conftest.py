"""
Shared test configuration for CosmoTarot.

Unit tests:        No database fixtures needed (pure business logic).
Integration tests: PostgreSQL fixtures in tests/integration/conftest.py.
Contract tests:    No database fixtures needed (mock AI boundary).

NOTE: Per CLAUDE.md rule — "No SQLite for testing. Ever."
      Database fixtures live in tests/integration/conftest.py (PostgreSQL only).
"""

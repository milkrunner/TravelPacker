"""Pytest configuration for NikNotes tests."""

import os

# Ensure a deterministic Flask secret key is present during tests
os.environ.setdefault("FLASK_SECRET_KEY", "test-secret-key")

# Disable CSRF protection for testing
os.environ.setdefault("WTF_CSRF_ENABLED", "False")

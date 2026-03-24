"""pytest configuration and fixtures."""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest markers."""
    config.addinivalue_line("markers", "docker: marks tests that require Docker to run")

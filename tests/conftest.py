"""Pytest configuration and shared fixtures for OpenLore."""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest


@pytest.fixture
def temp_dir():
    """Provide an isolated temporary directory for test storage."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)

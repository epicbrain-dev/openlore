"""Test suite for OpenLore."""

from __future__ import annotations

import warnings

# Filter internal third-party library deprecation warnings during test execution
warnings.filterwarnings("ignore", category=DeprecationWarning, module="rdflib")
warnings.filterwarnings("ignore", message=".*NotOpenSSLWarning.*")

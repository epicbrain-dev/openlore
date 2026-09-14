"""Configuration management for OpenLore."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class OpenLoreConfig:
    """Global configuration settings for OpenLore."""

    cas_root: Path = field(default_factory=lambda: Path(os.getenv("OPENLORE_CAS_ROOT", "/data/openlore/cas")))
    kafka_bootstrap_servers: str = field(
        default_factory=lambda: os.getenv("OPENLORE_KAFKA_SERVERS", "localhost:9092")
    )
    triplestore_endpoint: str = field(
        default_factory=lambda: os.getenv("OPENLORE_TRIPLESTORE_URL", "http://localhost:3030/openlore")
    )
    opa_endpoint: str = field(
        default_factory=lambda: os.getenv("OPENLORE_OPA_URL", "http://localhost:8181/v1/data/openlore/royalties")
    )
    temporal_endpoint: str = field(
        default_factory=lambda: os.getenv("OPENLORE_TEMPORAL_URL", "localhost:7233")
    )
    default_timeline: str = "prime-canon"
    partner_enclave_enabled: bool = True


_config_instance: OpenLoreConfig | None = None


def get_config() -> OpenLoreConfig:
    """Retrieve the singleton OpenLore configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = OpenLoreConfig()
    return _config_instance

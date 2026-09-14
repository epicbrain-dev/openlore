"""Configuration management for OpenLore."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class OpenLoreConfig:
    """Global configuration settings for OpenLore across Development, Staging, and Production."""

    environment: str = field(
        default_factory=lambda: os.getenv("OPENLORE_ENV", "development").lower()
    )
    
    # 1. Content-Addressed Storage (CAS)
    cas_backend: str = field(
        default_factory=lambda: os.getenv("OPENLORE_CAS_BACKEND", "filesystem").lower()
    )
    cas_root: Path = field(
        default_factory=lambda: Path(os.getenv("OPENLORE_CAS_ROOT", "/data/openlore/cas"))
    )
    s3_endpoint_url: str = field(
        default_factory=lambda: os.getenv("OPENLORE_S3_ENDPOINT_URL", "http://localhost:9000")
    )
    s3_bucket_name: str = field(
        default_factory=lambda: os.getenv("OPENLORE_S3_BUCKET_NAME", "openlore-cas")
    )
    s3_region: str = field(
        default_factory=lambda: os.getenv("OPENLORE_S3_REGION", "us-east-1")
    )
    s3_access_key: str = field(
        default_factory=lambda: os.getenv("OPENLORE_S3_ACCESS_KEY", "openloreadmin")
    )
    s3_secret_key: str = field(
        default_factory=lambda: os.getenv("OPENLORE_S3_SECRET_KEY", "openloresecurepassword2026")
    )

    # 2. Central Production Catalog & Database
    catalog_backend: str = field(
        default_factory=lambda: os.getenv("OPENLORE_CATALOG_BACKEND", "json").lower()
    )
    database_url: str = field(
        default_factory=lambda: os.getenv("OPENLORE_DATABASE_URL", "sqlite:///data/openlore/catalog.db")
    )

    # 3. Distributed Messaging & Microservices
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

    # 4. Security & Governance
    auth_enabled: bool = field(
        default_factory=lambda: os.getenv("OPENLORE_AUTH_ENABLED", "false").lower() in ("true", "1", "yes")
    )
    auth_secret: str = field(
        default_factory=lambda: os.getenv("OPENLORE_AUTH_SECRET", "openlore-enterprise-master-key-2026")
    )

    # 5. Narrative & Enclave
    default_timeline: str = "prime-canon"
    partner_enclave_enabled: bool = True

    @property
    def is_staging(self) -> bool:
        """Check if active deployment is in the staging profile."""
        return self.environment == "staging"

    @property
    def is_production(self) -> bool:
        """Check if active deployment is in the production profile."""
        return self.environment == "production"


_config_instance: OpenLoreConfig | None = None


def get_config(reload: bool = False) -> OpenLoreConfig:
    """Retrieve the singleton OpenLore configuration instance."""
    global _config_instance
    if _config_instance is None or reload:
        _config_instance = OpenLoreConfig()
    return _config_instance


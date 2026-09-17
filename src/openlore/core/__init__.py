"""Core Foundation & Asset Storage Architecture for OpenLore."""

from __future__ import annotations

from openlore.core.cas import CASObject, ContentAddressedStorage
from openlore.core.path_safety import (
    get_default_safe_roots,
    is_safe_path,
    sanitize_filename,
    validate_safe_path,
)
from openlore.core.stage import StageCompositionManager, UsdStageReference
from openlore.core.transaction import (
    PropertyDelta,
    TransactionalEdit,
    TransactionManager,
    TransactionSession,
)

__all__ = [
    "CASObject",
    "ContentAddressedStorage",
    "StageCompositionManager",
    "UsdStageReference",
    "PropertyDelta",
    "TransactionalEdit",
    "TransactionManager",
    "TransactionSession",
    "validate_safe_path",
    "is_safe_path",
    "get_default_safe_roots",
    "sanitize_filename",
]

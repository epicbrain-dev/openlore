"""One-click Technical Director (TD) promotion interface with optimistic locking."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from pxr import Usd
    HAS_PXR = True
except ImportError:
    HAS_PXR = False

from openlore.exceptions import StagePromotionError
from openlore.partner.linter import InboundLintResult


@dataclass
class PromotionLock:
    """Represents an active optimistic promotion lock on a production stage."""

    stage_uri: str
    td_user: str
    lock_token: str
    target_timeline: str
    acquired_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class StagePromotionGate:
    """Enforces optimistic locking and background validation before stage promotion."""

    def __init__(self) -> None:
        self._active_locks: Dict[str, PromotionLock] = {}

    def is_locked(self, stage_uri: str) -> bool:
        """Check if a stage currently has an active promotion lock."""
        return stage_uri in self._active_locks

    def get_lock(self, stage_uri: str) -> Optional[PromotionLock]:
        """Get the current lock on a stage."""
        return self._active_locks.get(stage_uri)

    def acquire_promotion_lock(
        self,
        stage_uri: str,
        td_user: str,
        target_timeline: str = "prime-canon",
    ) -> str:
        """Acquire optimistic lock preventing conflicting merges."""
        if stage_uri in self._active_locks:
            existing = self._active_locks[stage_uri]
            raise StagePromotionError(
                f"Optimistic lock conflict: Stage '{stage_uri}' is currently locked by '{existing.td_user}' "
                f"since {existing.acquired_at.isoformat()}."
            )

        token = uuid.uuid4().hex
        lock = PromotionLock(
            stage_uri=stage_uri,
            td_user=td_user,
            lock_token=token,
            target_timeline=target_timeline,
        )
        self._active_locks[stage_uri] = lock
        return token

    def release_lock(self, stage_uri: str, lock_token: str) -> bool:
        """Release an optimistic promotion lock using the authorized token."""
        if stage_uri in self._active_locks:
            if self._active_locks[stage_uri].lock_token == lock_token:
                del self._active_locks[stage_uri]
                return True
        return False

    def promote_to_production(
        self,
        stage_uri: str,
        deliverable_path: Path,
        production_stage_path: Path,
        lint_result: InboundLintResult,
        lock_token: str,
        narrative_validator: Any = None,
        graph_client: Any = None,
    ) -> bool:
        """Promote quarantined contractor stage into production canon."""
        # 1. Verify lock authority
        if stage_uri not in self._active_locks or self._active_locks[stage_uri].lock_token != lock_token:
            raise StagePromotionError("Promotion rejected: Invalid or expired promotion lock token.")

        # 2. Verify pre-flight linting gate
        if not lint_result.passed:
            raise StagePromotionError(
                f"Promotion rejected: Inbound linting failed with {len(lint_result.hierarchy_errors)} hierarchy errors, "
                f"{len(lint_result.polycount_violations)} polycount violations, and {len(lint_result.namespace_violations)} namespace errors."
            )

        # 3. Verify narrative continuity gate
        if narrative_validator and graph_client:
            lock = self._active_locks[stage_uri]
            narrative_validator.assert_valid(graph_client.dataset, timeline_uri=lock.target_timeline)

        # 4. Perform atomic sublayer promotion into production USD stage
        prod_path = Path(production_stage_path)
        deliv_path = Path(deliverable_path)

        if HAS_PXR and prod_path.is_file():
            prod_stage = Usd.Stage.Open(str(prod_path))
            root_layer = prod_stage.GetRootLayer()
            rel_or_abs = str(deliv_path)
            if rel_or_abs not in root_layer.subLayerPaths:
                root_layer.subLayerPaths.append(rel_or_abs)
                root_layer.Save()

        # 5. Release lock upon successful promotion
        self.release_lock(stage_uri, lock_token)
        return True

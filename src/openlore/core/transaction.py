"""Transactional Edit Manager isolating lightweight metadata from binary payloads."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from openlore.core.cas import CASObject
from openlore.core.stage import StageCompositionManager, UsdStageReference


@dataclass
class PropertyDelta:
    """Individual property or attribute change on a Prim path."""

    prim_path: str
    property_name: str
    old_value: Any
    new_value: Any
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prim_path": self.prim_path,
            "property_name": self.property_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> PropertyDelta:
        return cls(
            prim_path=d["prim_path"],
            property_name=d["property_name"],
            old_value=d.get("old_value"),
            new_value=d.get("new_value"),
            timestamp=datetime.fromisoformat(d["timestamp"]) if "timestamp" in d else datetime.now(timezone.utc),
        )


@dataclass
class TransactionalEdit:
    """Atomic lightweight edit commit to an OpenUSD scene stage."""

    commit_id: str
    stage_uri: str
    author: str
    message: str
    timestamp: datetime
    parent_commit_id: Optional[str] = None
    deltas: List[PropertyDelta] = field(default_factory=list)
    referenced_cas_hashes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "commit_id": self.commit_id,
            "stage_uri": self.stage_uri,
            "author": self.author,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "parent_commit_id": self.parent_commit_id,
            "deltas": [delta.to_dict() for delta in self.deltas],
            "referenced_cas_hashes": self.referenced_cas_hashes,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> TransactionalEdit:
        return cls(
            commit_id=d["commit_id"],
            stage_uri=d["stage_uri"],
            author=d["author"],
            message=d["message"],
            timestamp=datetime.fromisoformat(d["timestamp"]),
            parent_commit_id=d.get("parent_commit_id"),
            deltas=[PropertyDelta.from_dict(delta) for delta in d.get("deltas", [])],
            referenced_cas_hashes=d.get("referenced_cas_hashes", []),
        )


class TransactionSession:
    """In-memory active transactional session for staging edits."""

    def __init__(
        self,
        stage_ref: UsdStageReference,
        author: str,
        stage_manager: StageCompositionManager,
        commits_dir: Path,
        parent_commit_id: Optional[str] = None,
    ) -> None:
        self.stage_ref = stage_ref
        self.author = author
        self.stage_manager = stage_manager
        self.commits_dir = commits_dir
        self.parent_commit_id = parent_commit_id
        self._staged_deltas: List[PropertyDelta] = []
        self._referenced_cas_hashes: set[str] = set()

    def set_property(self, prim_path: str, property_name: str, new_value: Any, old_value: Any = None) -> None:
        """Stage a property modification on a Prim."""
        delta = PropertyDelta(
            prim_path=prim_path,
            property_name=property_name,
            old_value=old_value,
            new_value=new_value,
        )
        self._staged_deltas.append(delta)

    def attach_cas_payload(
        self,
        prim_path: str,
        attribute_name: str,
        cas_object: CASObject,
    ) -> None:
        """Bind an immutable CAS binary object to a Prim and record delta."""
        self.stage_manager.bind_cas_asset(
            stage_ref=self.stage_ref,
            prim_path=prim_path,
            cas_object=cas_object,
            attribute_name=attribute_name,
        )
        self._referenced_cas_hashes.add(cas_object.blake3_hash)
        self._staged_deltas.append(
            PropertyDelta(
                prim_path=prim_path,
                property_name=attribute_name,
                old_value=None,
                new_value=cas_object.blake3_hash,
            )
        )

    def commit(self, message: str) -> TransactionalEdit:
        """Atomically commit all staged deltas and write commit record."""
        now = datetime.now(timezone.utc)

        # Generate deterministic commit ID
        content_for_hash = (
            f"{self.parent_commit_id or ''}:{self.author}:{now.isoformat()}:{message}:"
            f"{','.join(d.prim_path + ':' + d.property_name for d in self._staged_deltas)}"
        )
        commit_id = hashlib.sha1(content_for_hash.encode("utf-8")).hexdigest()

        commit_record = TransactionalEdit(
            commit_id=commit_id,
            stage_uri=self.stage_ref.stage_uri,
            author=self.author,
            message=message,
            timestamp=now,
            parent_commit_id=self.parent_commit_id,
            deltas=list(self._staged_deltas),
            referenced_cas_hashes=sorted(list(self._referenced_cas_hashes)),
        )

        # Persist commit JSON
        self.commits_dir.mkdir(parents=True, exist_ok=True)
        commit_path = self.commits_dir / f"{commit_id}.json"
        commit_path.write_text(json.dumps(commit_record.to_dict(), indent=2), encoding="utf-8")

        # Update HEAD pointer
        head_path = self.commits_dir.parent / "HEAD"
        head_path.write_text(commit_id, encoding="utf-8")

        # Clear staging buffer
        self._staged_deltas.clear()
        self._referenced_cas_hashes.clear()
        self.parent_commit_id = commit_id

        return commit_record

    def rollback(self) -> None:
        """Discard unstaged deltas."""
        self._staged_deltas.clear()
        self._referenced_cas_hashes.clear()


class TransactionManager:
    """Coordinates atomic commits and transactional isolation across stages."""

    def __init__(self, repo_root: Path, stage_manager: StageCompositionManager) -> None:
        self.repo_root = Path(repo_root)
        self.stage_manager = stage_manager
        self.stages_dir = self.repo_root / "stages"
        self.stages_dir.mkdir(parents=True, exist_ok=True)
        self._active_sessions: Dict[str, TransactionSession] = {}

    def _get_stage_meta_dir(self, stage_uri: str) -> Path:
        sanitized = stage_uri.replace("://", "_").replace("/", "_")
        return self.stages_dir / sanitized

    def begin_transaction(self, stage_ref: UsdStageReference, author: str) -> TransactionSession:
        """Begin a new transactional edit session for a stage."""
        stage_meta_dir = self._get_stage_meta_dir(stage_ref.stage_uri)
        commits_dir = stage_meta_dir / "commits"
        commits_dir.mkdir(parents=True, exist_ok=True)

        head_path = stage_meta_dir / "HEAD"
        parent_id = head_path.read_text(encoding="utf-8").strip() if head_path.exists() else None

        session = TransactionSession(
            stage_ref=stage_ref,
            author=author,
            stage_manager=self.stage_manager,
            commits_dir=commits_dir,
            parent_commit_id=parent_id,
        )
        self._active_sessions[stage_ref.stage_uri] = session
        return session

    def get_commit_history(self, stage_uri: str) -> List[TransactionalEdit]:
        """Retrieve the commit history chain starting from HEAD."""
        stage_meta_dir = self._get_stage_meta_dir(stage_uri)
        commits_dir = stage_meta_dir / "commits"
        head_path = stage_meta_dir / "HEAD"

        if not head_path.exists() or not commits_dir.exists():
            return []

        history: List[TransactionalEdit] = []
        current_id: Optional[str] = head_path.read_text(encoding="utf-8").strip()

        while current_id:
            commit_file = commits_dir / f"{current_id}.json"
            if not commit_file.exists():
                break
            data = json.loads(commit_file.read_text(encoding="utf-8"))
            commit = TransactionalEdit.from_dict(data)
            history.append(commit)
            current_id = commit.parent_commit_id

        return history

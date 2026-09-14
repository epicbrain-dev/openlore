"""Central Production Catalog backend interface with JSON and Relational SQL/PostgreSQL drivers."""

from __future__ import annotations

import abc
import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from openlore.config import get_config


class AbstractCatalogBackend(abc.ABC):
    """Abstract interface for storing and querying compiled engine package manifests."""

    @abc.abstractmethod
    def register_build(
        self,
        stage_uri: str,
        build_type: str,
        artifact_path: str,
        cas_hash: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Register a new compiled asset package or point cache in the catalog."""
        pass

    @abc.abstractmethod
    def get_build(self, catalog_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific build record by its catalog ID."""
        pass

    @abc.abstractmethod
    def get_builds_for_stage(self, stage_uri: str) -> List[Dict[str, Any]]:
        """Query all registered builds for a specific OpenUSD stage URI."""
        pass

    @abc.abstractmethod
    def list_all_builds(self) -> List[Dict[str, Any]]:
        """List all builds recorded in this catalog."""
        pass

    @abc.abstractmethod
    def save_catalog(self, file_path: Path) -> None:
        """Export or snapshot catalog records to disk."""
        pass

    @abc.abstractmethod
    def load_catalog(self, file_path: Path) -> None:
        """Import catalog records from a snapshot file."""
        pass


class JsonFileCatalogBackend(AbstractCatalogBackend):
    """Local file-backed in-memory catalog with JSON serialization."""

    def __init__(self) -> None:
        self._records: List[Dict[str, Any]] = []

    def register_build(
        self,
        stage_uri: str,
        build_type: str,
        artifact_path: str,
        cas_hash: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        record = {
            "catalog_id": f"cat-{uuid.uuid4().hex[:10]}",
            "stage_uri": stage_uri,
            "build_type": build_type,
            "artifact_path": str(artifact_path),
            "cas_hash": cas_hash,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }
        self._records.append(record)
        return record

    def get_build(self, catalog_id: str) -> Optional[Dict[str, Any]]:
        for r in self._records:
            if r.get("catalog_id") == catalog_id:
                return r
        return None

    def get_builds_for_stage(self, stage_uri: str) -> List[Dict[str, Any]]:
        return [r for r in self._records if r.get("stage_uri") == stage_uri]

    def list_all_builds(self) -> List[Dict[str, Any]]:
        return list(self._records)

    def save_catalog(self, file_path: Path) -> None:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._records, indent=2), encoding="utf-8")

    def load_catalog(self, file_path: Path) -> None:
        path = Path(file_path)
        if path.is_file():
            self._records = json.loads(path.read_text(encoding="utf-8"))


class RelationalCatalogBackend(AbstractCatalogBackend):
    """ACID Relational SQL Catalog backend (SQLite standard library or PostgreSQL)."""

    def __init__(self, db_url: Optional[str] = None) -> None:
        self.db_url = db_url or get_config().database_url
        self.is_postgres = self.db_url.startswith("postgres://") or self.db_url.startswith("postgresql://")
        self._sqlite_path: Optional[str] = None
        self._mem_conn: Optional[sqlite3.Connection] = None

        if self.is_postgres:
            try:
                import psycopg
            except ImportError:
                self.is_postgres = False
                self._sqlite_path = ":memory:"

        if not self.is_postgres:
            # Parse sqlite URI e.g. sqlite:///path/to/db or sqlite://:memory:
            if self.db_url.startswith("sqlite:///"):
                self._sqlite_path = self.db_url.replace("sqlite:///", "")
                if self._sqlite_path != ":memory:":
                    Path(self._sqlite_path).parent.mkdir(parents=True, exist_ok=True)
            elif not self._sqlite_path:
                self._sqlite_path = ":memory:"

        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        if self.is_postgres:
            import psycopg
            return psycopg.connect(self.db_url)

        if self._sqlite_path == ":memory:":
            if self._mem_conn is None:
                self._mem_conn = sqlite3.connect(":memory:")
                self._mem_conn.row_factory = sqlite3.Row
            return self._mem_conn

        conn = sqlite3.connect(self._sqlite_path or ":memory:")
        conn.row_factory = sqlite3.Row
        return conn

    def _close_conn(self, conn: Any) -> None:
        if self._mem_conn is not None and conn is self._mem_conn:
            return
        try:
            conn.close()
        except Exception:
            pass

    def _init_schema(self) -> None:
        """Create database tables and performance indexes."""
        conn = self._get_connection()
        try:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS openlore_builds (
                        catalog_id TEXT PRIMARY KEY,
                        stage_uri TEXT NOT NULL,
                        build_type TEXT NOT NULL,
                        artifact_path TEXT NOT NULL,
                        cas_hash TEXT NOT NULL,
                        registered_at TEXT NOT NULL,
                        metadata_json TEXT
                    );
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_builds_stage ON openlore_builds(stage_uri);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_builds_hash ON openlore_builds(cas_hash);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_builds_type ON openlore_builds(build_type);")
        finally:
            self._close_conn(conn)

    def register_build(
        self,
        stage_uri: str,
        build_type: str,
        artifact_path: str,
        cas_hash: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        catalog_id = f"cat-{uuid.uuid4().hex[:10]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        meta_json = json.dumps(metadata or {})

        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO openlore_builds 
                    (catalog_id, stage_uri, build_type, artifact_path, cas_hash, registered_at, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (catalog_id, stage_uri, build_type, str(artifact_path), cas_hash, now_iso, meta_json),
                )
        finally:
            self._close_conn(conn)

        return {
            "catalog_id": catalog_id,
            "stage_uri": stage_uri,
            "build_type": build_type,
            "artifact_path": str(artifact_path),
            "cas_hash": cas_hash,
            "registered_at": now_iso,
            "metadata": metadata or {},
        }

    def _row_to_dict(self, row: Any) -> Dict[str, Any]:
        return {
            "catalog_id": row["catalog_id"],
            "stage_uri": row["stage_uri"],
            "build_type": row["build_type"],
            "artifact_path": row["artifact_path"],
            "cas_hash": row["cas_hash"],
            "registered_at": row["registered_at"],
            "metadata": json.loads(row["metadata_json"]) if row["metadata_json"] else {},
        }

    def get_build(self, catalog_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM openlore_builds WHERE catalog_id = ?", (catalog_id,))
            row = cur.fetchone()
            return self._row_to_dict(row) if row else None
        finally:
            self._close_conn(conn)

    def get_builds_for_stage(self, stage_uri: str) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM openlore_builds WHERE stage_uri = ? ORDER BY registered_at DESC", (stage_uri,))
            return [self._row_to_dict(r) for r in cur.fetchall()]
        finally:
            self._close_conn(conn)

    def list_all_builds(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM openlore_builds ORDER BY registered_at DESC")
            return [self._row_to_dict(r) for r in cur.fetchall()]
        finally:
            self._close_conn(conn)

    def save_catalog(self, file_path: Path) -> None:
        records = self.list_all_builds()
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    def load_catalog(self, file_path: Path) -> None:
        path = Path(file_path)
        if not path.is_file():
            return
        records = json.loads(path.read_text(encoding="utf-8"))
        conn = self._get_connection()
        try:
            with conn:
                for r in records:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO openlore_builds 
                        (catalog_id, stage_uri, build_type, artifact_path, cas_hash, registered_at, metadata_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            r["catalog_id"],
                            r["stage_uri"],
                            r["build_type"],
                            r["artifact_path"],
                            r["cas_hash"],
                            r["registered_at"],
                            json.dumps(r.get("metadata", {})),
                        ),
                    )
        finally:
            self._close_conn(conn)

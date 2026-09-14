"""Content-Addressed Storage (CAS) engine using cryptographic BLAKE3 hashes."""

from __future__ import annotations

import os
import stat
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO, Generator, Optional

from openlore.exceptions import CASObjectNotFoundError, HashMismatchError


@dataclass
class CASObject:
    """Represents an immutable content-addressed binary object."""

    blake3_hash: str
    size_bytes: int
    storage_path: Path
    created_at: datetime
    mime_type: str = "application/octet-stream"

    def exists(self) -> bool:
        """Check if the physical file exists on disk."""
        return self.storage_path.is_file()


class ContentAddressedStorage:
    """Storage repository storing heavy binaries indexed by cryptographic BLAKE3 hashes.

    Uses a two-level sharded directory layout:
        storage_root/objects/<hash[0:2]>/<hash[2:4]>/<hash>
    """

    CHUNK_SIZE: int = 65536  # 64 KB chunks for streaming hash calculation

    def __init__(self, storage_root: Path) -> None:
        self.storage_root = Path(storage_root)
        self.objects_dir = self.storage_root / "objects"
        self.tmp_dir = self.storage_root / "tmp"

        self.objects_dir.mkdir(parents=True, exist_ok=True)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    def compute_hash(self, data: bytes | BinaryIO) -> str:
        """Compute the cryptographic BLAKE3 hash (with SHA-256 fallback if blake3 missing)."""
        try:
            import blake3
            hasher = blake3.blake3()
            use_blake3 = True
        except ImportError:
            import hashlib
            hasher = hashlib.sha256()
            use_blake3 = False

        if isinstance(data, (bytes, bytearray, memoryview)):
            hasher.update(data)
        else:
            # Stream/file-like object
            data.seek(0)
            while chunk := data.read(self.CHUNK_SIZE):
                hasher.update(chunk)
            data.seek(0)

        return hasher.hexdigest()

    def _get_shard_path(self, hash_digest: str) -> Path:
        """Get the filesystem path for a given hash digest."""
        if len(hash_digest) < 4:
            return self.objects_dir / hash_digest
        shard1 = hash_digest[:2]
        shard2 = hash_digest[2:4]
        return self.objects_dir / shard1 / shard2 / hash_digest

    def store_bytes(self, data: bytes, mime_type: str = "application/octet-stream") -> CASObject:
        """Store raw bytes into the immutable CAS repository.

        Performs deduplication: if the content already exists, returns the existing CASObject.
        Uses atomic file rename to prevent partial writes.
        """
        hash_digest = self.compute_hash(data)
        target_path = self._get_shard_path(hash_digest)

        # Deduplication check
        if target_path.is_file():
            size = target_path.stat().st_size
            return CASObject(
                blake3_hash=hash_digest,
                size_bytes=size,
                storage_path=target_path,
                created_at=datetime.fromtimestamp(target_path.stat().st_ctime, tz=timezone.utc),
                mime_type=mime_type,
            )

        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write through temporary file
        tmp_filename = f"tmp_{uuid.uuid4().hex}_{hash_digest[:8]}"
        tmp_file_path = self.tmp_dir / tmp_filename

        with open(tmp_file_path, "wb") as f:
            f.write(data)

        # Set read-only permissions for immutability
        os.chmod(tmp_file_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

        # Atomic replace
        os.replace(tmp_file_path, target_path)

        return CASObject(
            blake3_hash=hash_digest,
            size_bytes=len(data),
            storage_path=target_path,
            created_at=datetime.now(timezone.utc),
            mime_type=mime_type,
        )

    def store_file(self, source_path: Path, mime_type: str = "application/octet-stream") -> CASObject:
        """Store a file from disk into the immutable CAS repository with streaming hashing."""
        source = Path(source_path)
        if not source.is_file():
            raise FileNotFoundError(f"Source file does not exist: {source}")

        # Compute hash streaming
        with open(source, "rb") as f:
            hash_digest = self.compute_hash(f)

        target_path = self._get_shard_path(hash_digest)

        # Deduplication check
        if target_path.is_file():
            size = target_path.stat().st_size
            return CASObject(
                blake3_hash=hash_digest,
                size_bytes=size,
                storage_path=target_path,
                created_at=datetime.fromtimestamp(target_path.stat().st_ctime, tz=timezone.utc),
                mime_type=mime_type,
            )

        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Stream copy to tmp file
        tmp_filename = f"tmp_{uuid.uuid4().hex}_{hash_digest[:8]}"
        tmp_file_path = self.tmp_dir / tmp_filename

        total_bytes = 0
        with open(source, "rb") as src, open(tmp_file_path, "wb") as dst:
            while chunk := src.read(self.CHUNK_SIZE):
                dst.write(chunk)
                total_bytes += len(chunk)

        # Set read-only permissions
        os.chmod(tmp_file_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

        # Atomic replace
        os.replace(tmp_file_path, target_path)

        return CASObject(
            blake3_hash=hash_digest,
            size_bytes=total_bytes,
            storage_path=target_path,
            created_at=datetime.now(timezone.utc),
            mime_type=mime_type,
        )

    def retrieve(self, blake3_hash: str) -> CASObject:
        """Retrieve an immutable object metadata by hash.

        Raises:
            CASObjectNotFoundError: If the hash is not stored in this repository.
        """
        target_path = self._get_shard_path(blake3_hash)
        if not target_path.is_file():
            raise CASObjectNotFoundError(f"CAS Object not found for hash: {blake3_hash}")

        stat_info = target_path.stat()
        return CASObject(
            blake3_hash=blake3_hash,
            size_bytes=stat_info.st_size,
            storage_path=target_path,
            created_at=datetime.fromtimestamp(stat_info.st_ctime, tz=timezone.utc),
        )

    def retrieve_bytes(self, blake3_hash: str) -> bytes:
        """Read and return full byte contents of an object."""
        cas_obj = self.retrieve(blake3_hash)
        with open(cas_obj.storage_path, "rb") as f:
            return f.read()

    def retrieve_stream(self, blake3_hash: str, chunk_size: int = CHUNK_SIZE) -> Generator[bytes, None, None]:
        """Stream the contents of a stored object in chunks."""
        cas_obj = self.retrieve(blake3_hash)
        with open(cas_obj.storage_path, "rb") as f:
            while chunk := f.read(chunk_size):
                yield chunk

    def verify_integrity(self, blake3_hash: str, raise_on_error: bool = False) -> bool:
        """Verify the cryptographic checksum integrity of a stored object."""
        try:
            cas_obj = self.retrieve(blake3_hash)
        except CASObjectNotFoundError:
            if raise_on_error:
                raise
            return False

        with open(cas_obj.storage_path, "rb") as f:
            current_digest = self.compute_hash(f)

        is_valid = current_digest == blake3_hash
        if not is_valid and raise_on_error:
            raise HashMismatchError(
                f"Checksum mismatch for object {blake3_hash}: calculated {current_digest}"
            )
        return is_valid

    def exists(self, blake3_hash: str) -> bool:
        """Check if an object with the given hash exists."""
        return self._get_shard_path(blake3_hash).is_file()

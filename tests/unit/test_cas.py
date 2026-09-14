"""Unit tests for Content-Addressed Storage (CAS)."""

from __future__ import annotations

import io
import os
import stat
import tempfile
import unittest
from pathlib import Path

from openlore.core.cas import CASObject, ContentAddressedStorage
from openlore.exceptions import CASObjectNotFoundError, HashMismatchError


class TestCAS(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_path = Path(self.temp_dir.name)
        self.cas = ContentAddressedStorage(self.storage_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_cas_hashing(self) -> None:
        data = b"OpenLore 3D Asset Binary Test"
        digest = self.cas.compute_hash(data)
        self.assertIsInstance(digest, str)
        self.assertEqual(len(digest), 64)

        # Stream hashing matches byte hashing
        stream = io.BytesIO(data)
        stream_digest = self.cas.compute_hash(stream)
        self.assertEqual(digest, stream_digest)

    def test_store_and_retrieve_bytes(self) -> None:
        payload = b"3D Mesh Geometry Buffer: (v 0 1 0, v 1 0 0, v 0 0 1)"
        cas_obj = self.cas.store_bytes(payload, mime_type="model/vnd.usd+mesh")

        self.assertIsInstance(cas_obj, CASObject)
        self.assertEqual(cas_obj.size_bytes, len(payload))
        self.assertTrue(cas_obj.exists())

        # Retrieve and verify contents
        retrieved_bytes = self.cas.retrieve_bytes(cas_obj.blake3_hash)
        self.assertEqual(retrieved_bytes, payload)

        # Retrieve metadata
        meta = self.cas.retrieve(cas_obj.blake3_hash)
        self.assertEqual(meta.blake3_hash, cas_obj.blake3_hash)
        self.assertEqual(meta.size_bytes, len(payload))

    def test_store_file_stream(self) -> None:
        test_file = self.storage_path / "sample_mesh.bin"
        large_data = b"X" * 150000  # > 2 chunks
        test_file.write_bytes(large_data)

        cas_obj = self.cas.store_file(test_file)
        self.assertEqual(cas_obj.size_bytes, 150000)
        self.assertTrue(self.cas.exists(cas_obj.blake3_hash))

        # Stream retrieval
        chunks = list(self.cas.retrieve_stream(cas_obj.blake3_hash, chunk_size=65536))
        self.assertEqual(b"".join(chunks), large_data)

    def test_deduplication(self) -> None:
        payload = b"Identical Shader Cache Data"
        obj1 = self.cas.store_bytes(payload)
        obj2 = self.cas.store_bytes(payload)

        self.assertEqual(obj1.blake3_hash, obj2.blake3_hash)
        self.assertEqual(obj1.storage_path, obj2.storage_path)

    def test_file_immutability(self) -> None:
        payload = b"Immutable Stage Prim Mesh"
        cas_obj = self.cas.store_bytes(payload)

        file_mode = cas_obj.storage_path.stat().st_mode
        # Assert user write bit is turned off
        self.assertEqual(file_mode & stat.S_IWUSR, 0)

    def test_integrity_verification_and_corruption_detection(self) -> None:
        payload = b"Valid Uncorrupted Mesh Data"
        cas_obj = self.cas.store_bytes(payload)

        # Verified intact
        self.assertTrue(self.cas.verify_integrity(cas_obj.blake3_hash))

        # Intentionally corrupt file
        os.chmod(cas_obj.storage_path, stat.S_IWUSR | stat.S_IRUSR)
        with open(cas_obj.storage_path, "wb") as f:
            f.write(b"Tampered Corrupted Mesh Data")

        self.assertFalse(self.cas.verify_integrity(cas_obj.blake3_hash))
        with self.assertRaises(HashMismatchError):
            self.cas.verify_integrity(cas_obj.blake3_hash, raise_on_error=True)

    def test_not_found_raises(self) -> None:
        with self.assertRaises(CASObjectNotFoundError):
            self.cas.retrieve("nonexistent" * 6)

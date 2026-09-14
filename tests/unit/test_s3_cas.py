"""Unit tests for S3 Content-Addressed Storage backend."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from openlore.core.cas import CASObject, ContentAddressedStorage, S3CASBackend


class TestS3CAS(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_dir = Path(self.temp_dir.name)
        self.s3_backend = S3CASBackend(
            bucket_name="openlore-test-bucket",
            endpoint_url="http://localhost:9000",
            region="us-east-1",
            access_key="test-key",
            secret_key="test-secret",
            cache_dir=self.cache_dir,
        )
        self.cas = ContentAddressedStorage(backend=self.s3_backend)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_sigv4_headers(self) -> None:
        headers = self.s3_backend._sign_sigv4("PUT", "/openlore-test-bucket/objects/ab/cd/test", b"hello")
        self.assertIn("Authorization", headers)
        self.assertIn("AWS4-HMAC-SHA256", headers["Authorization"])
        self.assertIn("Credential=test-key/", headers["Authorization"])
        self.assertIn("x-amz-date", headers)
        self.assertIn("x-amz-content-sha256", headers)

    def test_store_and_retrieve_s3_bytes(self) -> None:
        data = b"S3 Immutable USD Geometry Point Cache (v 1.0, 2.0, 3.0)"
        cas_obj = self.cas.store_bytes(data, mime_type="model/vnd.usd")

        self.assertIsInstance(cas_obj, CASObject)
        self.assertEqual(cas_obj.size_bytes, len(data))
        self.assertTrue(self.cas.exists(cas_obj.blake3_hash))

        retrieved = self.cas.retrieve_bytes(cas_obj.blake3_hash)
        self.assertEqual(retrieved, data)

    def test_s3_verify_integrity(self) -> None:
        data = b"Cryptographic Integrity Payload for MinIO Cluster"
        cas_obj = self.cas.store_bytes(data)
        self.assertTrue(self.cas.verify_integrity(cas_obj.blake3_hash))

    def test_s3_streaming(self) -> None:
        large_data = b"StreamingChunk" * 1000
        cas_obj = self.cas.store_bytes(large_data)

        chunks = list(self.cas.retrieve_stream(cas_obj.blake3_hash, chunk_size=1024))
        reconstructed = b"".join(chunks)
        self.assertEqual(reconstructed, large_data)

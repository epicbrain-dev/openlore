"""Unit tests for Relational SQL / PostgreSQL Catalog Backend."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from openlore.compilation.catalog_backend import (
    JsonFileCatalogBackend,
    RelationalCatalogBackend,
)
from openlore.compilation.grid import ProductionCatalog


class TestRelationalCatalog(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_catalog.db"
        self.backend = RelationalCatalogBackend(f"sqlite:///{self.db_path}")
        self.catalog = ProductionCatalog(backend=self.backend)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_register_and_get_build(self) -> None:
        build = self.catalog.register_build(
            stage_uri="openlore://stages/hero_scene.usda",
            build_type="unreal",
            artifact_path="/builds/unreal/hero.pak",
            cas_hash="a" * 64,
            metadata={"lod": "cinematic", "polycount": 125000},
        )
        self.assertIn("catalog_id", build)
        self.assertEqual(build["stage_uri"], "openlore://stages/hero_scene.usda")
        self.assertEqual(build["build_type"], "unreal")

        retrieved = self.catalog.get_build(build["catalog_id"])
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["cas_hash"], "a" * 64)
        self.assertEqual(retrieved["metadata"]["lod"], "cinematic")

    def test_get_builds_for_stage(self) -> None:
        self.catalog.register_build(
            stage_uri="openlore://stages/stage_alpha.usda",
            build_type="unity",
            artifact_path="/builds/unity/alpha.bundle",
            cas_hash="b" * 64,
        )
        self.catalog.register_build(
            stage_uri="openlore://stages/stage_alpha.usda",
            build_type="cinematic-cache",
            artifact_path="/builds/alembic/alpha.abc",
            cas_hash="c" * 64,
        )
        self.catalog.register_build(
            stage_uri="openlore://stages/stage_beta.usda",
            build_type="unreal",
            artifact_path="/builds/unreal/beta.pak",
            cas_hash="d" * 64,
        )

        alpha_builds = self.catalog.get_builds_for_stage("openlore://stages/stage_alpha.usda")
        self.assertEqual(len(alpha_builds), 2)

        beta_builds = self.catalog.get_builds_for_stage("openlore://stages/stage_beta.usda")
        self.assertEqual(len(beta_builds), 1)

    def test_list_all_builds(self) -> None:
        self.catalog.register_build("openlore://stages/1", "unreal", "/p1", "1" * 64)
        self.catalog.register_build("openlore://stages/2", "unity", "/p2", "2" * 64)

        all_builds = self.catalog.list_all_builds()
        self.assertEqual(len(all_builds), 2)

    def test_save_and_load_catalog(self) -> None:
        self.catalog.register_build("openlore://stages/saved", "unreal", "/p_saved", "e" * 64)
        export_file = Path(self.temp_dir.name) / "catalog_export.json"

        self.catalog.save_catalog(export_file)
        self.assertTrue(export_file.is_file())

        new_db_path = Path(self.temp_dir.name) / "new_catalog.db"
        new_backend = RelationalCatalogBackend(f"sqlite:///{new_db_path}")
        new_backend.load_catalog(export_file)

        loaded_builds = new_backend.get_builds_for_stage("openlore://stages/saved")
        self.assertEqual(len(loaded_builds), 1)
        self.assertEqual(loaded_builds[0]["cas_hash"], "e" * 64)

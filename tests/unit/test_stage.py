"""Unit tests for OpenUSD Stage Composition."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from openlore.core.cas import CASObject, ContentAddressedStorage
from openlore.core.stage import StageCompositionManager


class TestStageManager(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
        self.stage_mgr = StageCompositionManager(self.base_path)
        self.cas = ContentAddressedStorage(self.base_path / "cas")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_and_load_stage(self) -> None:
        stage_uri = "openlore://shots/sh01/scene.usda"
        ref = self.stage_mgr.create_stage(stage_uri=stage_uri, default_prim="World")

        self.assertTrue(ref.root_layer_path.is_file())
        self.assertEqual(ref.stage_uri, stage_uri)

        # Reload from disk
        loaded_ref = self.stage_mgr.load_stage(stage_uri=stage_uri)
        self.assertEqual(loaded_ref.root_layer_path, ref.root_layer_path)

    def test_define_prim_and_bind_cas_asset(self) -> None:
        stage_uri = "openlore://assets/robot/robot.usda"
        ref = self.stage_mgr.create_stage(stage_uri=stage_uri, default_prim="Robot")

        # Store binary mesh in CAS
        mesh_bytes = b"USD binary mesh geometry data buffer..."
        cas_obj = self.cas.store_bytes(mesh_bytes, mime_type="model/vnd.usda")

        # Define character Prim and bind CAS asset
        prim_path = "/Robot/Geom/Torso"
        self.stage_mgr.define_prim(ref, prim_path, prim_type="Mesh")
        self.stage_mgr.bind_cas_asset(ref, prim_path, cas_obj, attribute_name="openlore:assetHash")

        # Read back asset hash
        retrieved_hash = self.stage_mgr.get_cas_asset_hash(ref, prim_path, attribute_name="openlore:assetHash")
        self.assertEqual(retrieved_hash, cas_obj.blake3_hash)

    def test_add_sublayer_composition(self) -> None:
        root_uri = "openlore://shots/shot010.usda"
        root_ref = self.stage_mgr.create_stage(stage_uri=root_uri)

        layers_dir = self.base_path / "layers"
        layers_dir.mkdir(parents=True, exist_ok=True)

        sub_a_path = layers_dir / "fx.usda"
        sub_b_path = layers_dir / "lighting.usda"

        self.stage_mgr.create_stage(stage_uri="openlore://shots/layers/fx.usda", relative_path="layers/fx.usda")
        self.stage_mgr.create_stage(stage_uri="openlore://shots/layers/lighting.usda", relative_path="layers/lighting.usda")

        self.stage_mgr.add_sublayer(root_ref, str(sub_a_path))
        self.stage_mgr.add_sublayer(root_ref, str(sub_b_path))

        self.assertIn(str(sub_a_path), root_ref.sublayers)
        self.assertIn(str(sub_b_path), root_ref.sublayers)
        self.assertEqual(root_ref.sublayers[-1], str(sub_b_path))

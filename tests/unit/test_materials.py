"""Unit tests for MaterialX Translation and UsdSkel Dynamic Rigging."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pxr import Usd

from openlore.materials.materialx import MaterialXTranslator, SurfaceAppearance
from openlore.materials.rigging import DynamicRigManager, VariantRigType


class TestMaterialsAndRigging(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
        self.mtlx_path = Path("./schemas/materialx/standard_surface.mtlx")
        self.translator = MaterialXTranslator()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_materialx_parsing(self) -> None:
        appearance = self.translator.parse_document(self.mtlx_path)
        self.assertIsInstance(appearance, SurfaceAppearance)
        self.assertEqual(appearance.material_name, "SR_robot_armor")
        self.assertEqual(appearance.base, 1.0)
        self.assertAlmostEqual(appearance.metalness, 0.9, places=2)
        self.assertAlmostEqual(appearance.roughness, 0.25, places=2)
        self.assertEqual(len(appearance.base_color), 3)
        self.assertAlmostEqual(appearance.base_color[0], 0.7, places=2)

    def test_unreal_hlsl_shader_export(self) -> None:
        appearance = self.translator.parse_document(self.mtlx_path)
        hlsl = self.translator.export_to_unreal_shader(appearance)

        self.assertIn("FOpenLoreMaterialInput", hlsl)
        self.assertIn("GetSR_robot_armorParameters", hlsl)
        self.assertIn("Mat.Metallic      = 0.9000f", hlsl)
        self.assertIn("Mat.Roughness     = 0.2500f", hlsl)

    def test_cinematic_osl_shader_export(self) -> None:
        appearance = self.translator.parse_document(self.mtlx_path)
        osl = self.translator.export_to_cinematic_osl(appearance)

        self.assertIn("surface SR_robot_armor_osl", osl)
        self.assertIn("output closure color Ci = 0", osl)
        self.assertIn("oren_nayar", osl)
        self.assertIn("microfacet", osl)

    def test_usd_skel_dual_rig_variant_switching(self) -> None:
        stage_path = self.base_path / "character_stage.usda"
        stage = Usd.Stage.CreateNew(str(stage_path))

        rig_mgr = DynamicRigManager(stage)
        prim_path = "/World/Characters/Hero"

        test_cache_hash = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
        test_joints = ["root", "pelvis", "spine", "head"]
        test_capsules = [
            {"name": "Torso", "radius": 0.3, "height": 0.7},
            {"name": "Head", "radius": 0.15, "height": 0.2},
        ]

        # 1. Setup dual rig
        rig_mgr.setup_dual_rig(
            prim_path=prim_path,
            joints=test_joints,
            collision_capsules=test_capsules,
            point_cache_hash=test_cache_hash,
        )

        # Default variant should be cinematic_cache
        self.assertEqual(rig_mgr.get_active_variant(prim_path), VariantRigType.CINEMATIC_BAKED_CACHE)
        meta_cinematic = rig_mgr.get_rig_metadata(prim_path)
        self.assertEqual(meta_cinematic["point_cache_hash"], test_cache_hash)

        # 2. Switch to interactive game collision variant
        rig_mgr.set_active_variant(prim_path, VariantRigType.INTERACTIVE_GAME_COLLISION)
        self.assertEqual(rig_mgr.get_active_variant(prim_path), VariantRigType.INTERACTIVE_GAME_COLLISION)

        meta_game = rig_mgr.get_rig_metadata(prim_path)
        self.assertEqual(meta_game["active_variant"], "game_collision")
        self.assertEqual(meta_game["joints"], test_joints)

        # 3. Switch back to cinematic cache
        rig_mgr.set_active_variant(prim_path, VariantRigType.CINEMATIC_BAKED_CACHE)
        self.assertEqual(rig_mgr.get_active_variant(prim_path), VariantRigType.CINEMATIC_BAKED_CACHE)

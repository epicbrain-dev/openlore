"""Unit tests for Automated Downstream Compilation Grid, Real-Time Compilers, and Shot Baker."""

from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from pxr import Gf, Usd, UsdGeom

from openlore.compilation.engine_package import EnginePackageCompiler
from openlore.compilation.grid import (
    CompilationJobStatus,
    ProductionCatalog,
    WorkerGridDispatcher,
)
from openlore.compilation.shot_baker import OfflineShotBaker


class TestCompilationGrid(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)

        # Create a test OpenUSD stage with a mesh and collision capsule
        self.stage_path = self.base_path / "test_stage.usda"
        stage = Usd.Stage.CreateNew(str(self.stage_path))
        xform = UsdGeom.Xform.Define(stage, "/World")
        stage.SetDefaultPrim(xform.GetPrim())

        mesh = UsdGeom.Mesh.Define(stage, "/World/HeroMesh")
        mesh.GetPointsAttr().Set([
            Gf.Vec3f(0, 0, 0),
            Gf.Vec3f(1, 0, 0),
            Gf.Vec3f(1, 1, 0),
            Gf.Vec3f(0, 1, 0),
        ])
        mesh.GetFaceVertexCountsAttr().Set([4])
        mesh.GetFaceVertexIndicesAttr().Set([0, 1, 2, 3])

        # Define collision capsule
        UsdGeom.Capsule.Define(stage, "/World/HeroCollision")

        stage.GetRootLayer().Save()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_engine_package_compiler_unsupported_engine(self) -> None:
        with self.assertRaises(ValueError):
            EnginePackageCompiler(target_engine="godot")

    def test_engine_package_compiler_missing_stage(self) -> None:
        compiler = EnginePackageCompiler(target_engine="unreal")
        with self.assertRaises(FileNotFoundError):
            compiler.compile_package(self.base_path / "absent.usda", self.base_path / "out")

    def test_engine_package_compiler_unreal(self) -> None:
        compiler = EnginePackageCompiler(target_engine="unreal")
        out_dir = self.base_path / "unreal_out"
        pkg_path = compiler.compile_package(self.stage_path, out_dir, package_name="HeroAsset")

        self.assertTrue(pkg_path.is_file())
        self.assertEqual(pkg_path.name, "HeroAsset_unreal.pak")

        # Verify companion manifest
        manifest_path = out_dir / "HeroAsset_unreal_manifest.json"
        self.assertTrue(manifest_path.is_file())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["target_engine"], "unreal")
        self.assertEqual(manifest["total_meshes"], 1)
        self.assertEqual(manifest["total_collision_prims"], 1)
        self.assertTrue(len(manifest["package_hash"]) > 0)

        # Inspect ZIP / PAK archive contents
        with zipfile.ZipFile(pkg_path, "r") as zf:
            namelist = zf.namelist()
            self.assertIn("Content/content_manifest.json", namelist)
            self.assertIn("Content/Meshes/HeroMesh.uasset", namelist)
            self.assertIn("Content/Collision/PhysicsAsset.uasset", namelist)

    def test_engine_package_compiler_unity(self) -> None:
        compiler = EnginePackageCompiler(target_engine="unity")
        out_dir = self.base_path / "unity_out"
        pkg_path = compiler.compile_package(self.stage_path, out_dir, package_name="HeroAsset")

        self.assertTrue(pkg_path.is_file())
        self.assertEqual(pkg_path.name, "HeroAsset_unity.unitypackage")

        # Verify companion manifest
        manifest_path = out_dir / "HeroAsset_unity_manifest.json"
        self.assertTrue(manifest_path.is_file())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["target_engine"], "unity")
        self.assertEqual(manifest["total_meshes"], 1)

        # Inspect unitypackage contents
        with zipfile.ZipFile(pkg_path, "r") as zf:
            namelist = zf.namelist()
            self.assertIn("Assets/OpenLore/content_manifest.json", namelist)
            self.assertIn("Assets/OpenLore/Prefabs/HeroMesh.prefab", namelist)
            self.assertIn("Assets/OpenLore/Scenes/HeroAsset_Scene.unity", namelist)

    def test_offline_shot_baker(self) -> None:
        baker = OfflineShotBaker(fps=24.0)
        out_dir = self.base_path / "baker_out"

        # Invalid frame sequence raises ValueError
        with self.assertRaises(ValueError):
            baker.bake_cache(self.stage_path, start_frame=10, end_frame=5, output_dir=out_dir)

        # Missing stage raises FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            baker.bake_cache(self.base_path / "absent.usda", 1, 24, out_dir)

        # Bake shot 1 to 10
        cache_file = baker.bake_cache(
            usd_stage_path=self.stage_path,
            start_frame=1,
            end_frame=10,
            output_dir=out_dir,
            shot_name="shot_sq01_0010",
        )
        self.assertTrue(cache_file.is_file())

        # Verify cache manifest
        manifest_file = out_dir / "shot_sq01_0010_cache_manifest.json"
        self.assertTrue(manifest_file.is_file())
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        self.assertEqual(manifest["start_frame"], 1)
        self.assertEqual(manifest["end_frame"], 10)
        self.assertEqual(manifest["total_frames"], 10)
        self.assertEqual(manifest["fps"], 24.0)
        self.assertTrue(len(manifest["cache_hash"]) > 0)

        # Inspect baked OpenUSD stage
        baked_stage = Usd.Stage.Open(str(cache_file))
        self.assertEqual(baked_stage.GetStartTimeCode(), 1)
        self.assertEqual(baked_stage.GetEndTimeCode(), 10)
        self.assertEqual(baked_stage.GetTimeCodesPerSecond(), 24.0)

        baked_mesh_prim = baked_stage.GetPrimAtPath("/BakedShot/HeroMesh")
        self.assertTrue(baked_mesh_prim.IsValid())
        baked_mesh = UsdGeom.Mesh(baked_mesh_prim)

        # Verify time-sampled points and extent attributes exist at frame 1 and 10
        points_attr = baked_mesh.GetPointsAttr()
        self.assertIsNotNone(points_attr.Get(Usd.TimeCode(1)))
        self.assertIsNotNone(points_attr.Get(Usd.TimeCode(10)))
        self.assertEqual(len(points_attr.Get(Usd.TimeCode(1))), 4)

        extent_attr = baked_mesh.GetExtentAttr()
        self.assertIsNotNone(extent_attr.Get(Usd.TimeCode(1)))
        self.assertIsNotNone(extent_attr.Get(Usd.TimeCode(10)))

    def test_worker_grid_dispatcher_full_pipeline(self) -> None:
        catalog = ProductionCatalog()
        dispatcher = WorkerGridDispatcher(
            temporal_endpoint="localhost:7233",
            argo_namespace="openlore-grid",
            catalog=catalog,
        )
        out_dir = self.base_path / "grid_builds"

        workflow_id = dispatcher.trigger_compilation_workflow(
            stage_uri="openlore://stages/hero_scene.usda",
            target_engines=["unreal", "unity", "cinematic-cache"],
            stage_path=self.stage_path,
            output_dir=out_dir,
            shot_name="shot_hero_intro",
        )

        status = dispatcher.get_job_status(workflow_id)
        self.assertEqual(status["status"], CompilationJobStatus.COMPLETED.value)
        self.assertEqual(status["stage_uri"], "openlore://stages/hero_scene.usda")

        # Verify activities
        activities = status["activities"]
        self.assertEqual(activities["validate_stage"]["status"], "COMPLETED")
        self.assertEqual(activities["compile_unreal"]["status"], "COMPLETED")
        self.assertEqual(activities["compile_unity"]["status"], "COMPLETED")
        self.assertEqual(activities["bake_shot_point_cache"]["status"], "COMPLETED")
        self.assertEqual(activities["register_catalog"]["status"], "COMPLETED")

        # Verify registered artifacts
        artifacts = status["artifacts"]
        self.assertIn("unreal", artifacts)
        self.assertIn("unity", artifacts)
        self.assertIn("cinematic_cache", artifacts)

        # Verify production catalog entries
        builds = catalog.get_builds_for_stage("openlore://stages/hero_scene.usda")
        self.assertEqual(len(builds), 3)
        build_types = {b["build_type"] for b in builds}
        self.assertIn("game_package_unreal", build_types)
        self.assertIn("game_package_unity", build_types)
        self.assertIn("cinematic_point_cache", build_types)

    def test_worker_grid_dispatcher_unknown_and_failed_jobs(self) -> None:
        dispatcher = WorkerGridDispatcher()
        unknown_status = dispatcher.get_job_status("nonexistent-id")
        self.assertEqual(unknown_status["status"], "UNKNOWN")

        # Missing stage triggers job failure
        with self.assertRaises(FileNotFoundError):
            dispatcher.trigger_compilation_workflow(
                stage_uri="openlore://stages/missing.usda",
                target_engines=["unreal"],
                stage_path=self.base_path / "missing_stage.usda",
            )

    def test_argo_workflow_spec_generation(self) -> None:
        dispatcher = WorkerGridDispatcher(argo_namespace="custom-openlore-grid")
        spec = dispatcher.generate_argo_workflow_spec(
            stage_uri="openlore://stages/scene_01.usda",
            target_engines=["unreal", "unity", "cinematic-cache"],
        )

        self.assertEqual(spec["apiVersion"], "argoproj.io/v1alpha1")
        self.assertEqual(spec["kind"], "Workflow")
        self.assertEqual(spec["metadata"]["namespace"], "custom-openlore-grid")

        dag_tasks = spec["spec"]["templates"][0]["dag"]["tasks"]
        task_names = [t["name"] for t in dag_tasks]
        self.assertIn("fetch-stage", task_names)
        self.assertIn("compile-unreal-package", task_names)
        self.assertIn("compile-unity-package", task_names)
        self.assertIn("bake-point-caches", task_names)
        self.assertIn("register-production-catalog", task_names)

        # Test YAML generation
        yaml_str = dispatcher.generate_argo_workflow_yaml(
            stage_uri="openlore://stages/scene_01.usda",
            target_engines=["unreal"],
        )
        self.assertIn("argoproj.io/v1alpha1", yaml_str)

        # Test submit simulation
        execution_id = dispatcher.submit_argo_workflow(spec)
        self.assertTrue(execution_id.startswith("argo-openlore-compilation-"))

    def test_production_catalog_persistence(self) -> None:
        catalog = ProductionCatalog()
        catalog.register_build(
            stage_uri="openlore://stages/asset_01.usda",
            build_type="game_package_unreal",
            artifact_path="/builds/asset_01.pak",
            cas_hash="abc123hash",
        )
        catalog.register_build(
            stage_uri="openlore://stages/asset_02.usda",
            build_type="cinematic_point_cache",
            artifact_path="/builds/asset_02.usdc",
            cas_hash="def456hash",
        )

        catalog_file = self.base_path / "catalog.json"
        catalog.save_catalog(catalog_file)
        self.assertTrue(catalog_file.is_file())

        new_catalog = ProductionCatalog()
        new_catalog.load_catalog(catalog_file)
        self.assertEqual(len(new_catalog.list_all_builds()), 2)
        self.assertEqual(len(new_catalog.get_builds_for_stage("openlore://stages/asset_01.usda")), 1)


if __name__ == "__main__":
    unittest.main()

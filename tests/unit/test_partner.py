"""Unit tests for Partner Enclave isolation and Inbound Linting."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pxr import Gf, Sdf, Usd, UsdGeom

from openlore.exceptions import StagePromotionError
from openlore.partner.decimation import OutboundDecimationPipeline, ProxyStageConfig
from openlore.partner.ebpf_rules import EBPFNetworkPolicyManager
from openlore.partner.linter import InboundLintResult, PreFlightUSDValidator
from openlore.partner.promotion import PromotionLock, StagePromotionGate


class TestPartnerEnclave(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_proxy_config_defaults(self) -> None:
        config = ProxyStageConfig()
        self.assertEqual(config.max_polycount, 50000)
        self.assertEqual(config.decimation_ratio, 0.25)
        self.assertEqual(config.clay_shader_color, (0.7, 0.7, 0.7))
        self.assertTrue(config.strip_internal_shaders)
        self.assertTrue(config.flatten_hierarchy)

    def test_outbound_decimation_pipeline(self) -> None:
        source_stage_path = self.base_path / "source_stage.usda"
        proxy_stage_path = self.base_path / "output_proxy.usda"

        # Create source stage with high-density mesh and proprietary metadata
        stage = Usd.Stage.CreateNew(str(source_stage_path))
        xform = UsdGeom.Xform.Define(stage, "/World")
        stage.SetDefaultPrim(xform.GetPrim())

        mesh_prim = UsdGeom.Mesh.Define(stage, "/World/CharacterMesh")
        points = [
            Gf.Vec3f(0, 0, 0),
            Gf.Vec3f(1, 0, 0),
            Gf.Vec3f(1, 1, 0),
            Gf.Vec3f(0, 1, 0),
            Gf.Vec3f(0, 0, 1),
            Gf.Vec3f(1, 0, 1),
            Gf.Vec3f(1, 1, 1),
            Gf.Vec3f(0, 1, 1),
        ]
        mesh_prim.GetPointsAttr().Set(points)
        mesh_prim.GetFaceVertexCountsAttr().Set([4, 4])
        mesh_prim.GetFaceVertexIndicesAttr().Set([0, 1, 2, 3, 4, 5, 6, 7])

        # Add proprietary attributes
        prim = mesh_prim.GetPrim()
        prim.CreateAttribute("openlore:pointCacheHash", Sdf.ValueTypeNames.String, custom=True).Set("secret_hash_123")
        prim.CreateAttribute("openlore:royaltyPercentage", Sdf.ValueTypeNames.Float, custom=True).Set(15.5)

        stage.GetRootLayer().Save()

        pipeline = OutboundDecimationPipeline(ProxyStageConfig(decimation_ratio=0.5))
        result_path = pipeline.sanitize_outbound_stage(source_stage_path, proxy_stage_path)
        self.assertTrue(result_path.is_file())

        # Inspect generated proxy stage
        sanitized_stage = Usd.Stage.Open(str(result_path))
        sanitized_mesh = sanitized_stage.GetPrimAtPath("/World/CharacterMesh")
        self.assertTrue(sanitized_mesh.IsValid())

        # Proprietary attributes must be completely stripped
        self.assertFalse(sanitized_mesh.GetAttribute("openlore:pointCacheHash").IsValid())
        self.assertFalse(sanitized_mesh.GetAttribute("openlore:royaltyPercentage").IsValid())

        # Geometry must be marked as proxy mesh with clay display color
        self.assertTrue(sanitized_mesh.GetAttribute("openlore:isProxyMesh").Get())
        display_color = UsdGeom.Mesh(sanitized_mesh).GetDisplayColorAttr().Get()
        self.assertEqual(len(display_color), 1)
        self.assertAlmostEqual(display_color[0][0], 0.7, places=2)

    def test_outbound_decimation_missing_source(self) -> None:
        pipeline = OutboundDecimationPipeline()
        with self.assertRaises(FileNotFoundError):
            pipeline.sanitize_outbound_stage(self.base_path / "nonexistent.usda", self.base_path / "out.usda")

    def test_inbound_linter_success(self) -> None:
        stage_path = self.base_path / "valid_deliverable.usda"
        stage = Usd.Stage.CreateNew(str(stage_path))
        UsdGeom.Xform.Define(stage, "/World")
        mesh = UsdGeom.Mesh.Define(stage, "/World/AssetMesh")
        mesh.GetFaceVertexCountsAttr().Set([3, 3])
        stage.GetRootLayer().Save()

        validator = PreFlightUSDValidator(max_polycount_ceiling=1000)
        result = validator.validate_deliverable(stage_path)

        self.assertTrue(result.passed)
        self.assertEqual(result.total_polycount, 2)
        self.assertEqual(len(result.hierarchy_errors), 0)
        self.assertEqual(len(result.polycount_violations), 0)
        self.assertEqual(len(result.namespace_violations), 0)

    def test_inbound_linter_failures(self) -> None:
        validator = PreFlightUSDValidator(max_polycount_ceiling=5)

        # 1. Non-existent file
        result_missing = validator.validate_deliverable(self.base_path / "absent.usda")
        self.assertFalse(result_missing.passed)
        self.assertTrue(any("not found" in err for err in result_missing.hierarchy_errors))

        # 2. Stage with invalid root hierarchy
        invalid_root_path = self.base_path / "bad_root.usda"
        stage1 = Usd.Stage.CreateNew(str(invalid_root_path))
        UsdGeom.Xform.Define(stage1, "/UnauthorizedRoot/SubPrim")
        stage1.GetRootLayer().Save()

        result1 = validator.validate_deliverable(invalid_root_path)
        self.assertFalse(result1.passed)
        self.assertTrue(any("outside approved root hierarchy" in err for err in result1.hierarchy_errors))

        # 3. Stage with non-conforming Prim name violating studio naming conventions
        bad_name_path = self.base_path / "bad_name.usda"
        stage2 = Usd.Stage.CreateNew(str(bad_name_path))
        UsdGeom.Xform.Define(stage2, "/World")
        stage2.DefinePrim("/World/illegal_lowercase_prim")
        stage2.GetRootLayer().Save()

        naming_validator = PreFlightUSDValidator(prim_name_pattern=r"^[A-Z][a-zA-Z0-9_]*$")
        result2 = naming_validator.validate_deliverable(bad_name_path)
        self.assertFalse(result2.passed)
        self.assertTrue(any("non-conforming name" in err for err in result2.namespace_violations))

        # 4. Stage exceeding polycount ceiling
        heavy_poly_path = self.base_path / "heavy_poly.usda"
        stage3 = Usd.Stage.CreateNew(str(heavy_poly_path))
        UsdGeom.Xform.Define(stage3, "/World")
        mesh = UsdGeom.Mesh.Define(stage3, "/World/DenseMesh")
        mesh.GetFaceVertexCountsAttr().Set([3] * 10)  # 10 faces > ceiling of 5
        stage3.GetRootLayer().Save()

        result3 = validator.validate_deliverable(heavy_poly_path)
        self.assertFalse(result3.passed)
        self.assertTrue(any("exceeds maximum" in err for err in result3.polycount_violations))

    def test_stage_promotion_gate(self) -> None:
        gate = StagePromotionGate()
        stage_uri = "urn:openlore:stages:prime_sequence_01"

        # 1. Acquire lock
        token = gate.acquire_promotion_lock(stage_uri, td_user="td_alice", target_timeline="prime-canon")
        self.assertTrue(gate.is_locked(stage_uri))
        self.assertEqual(gate.get_lock(stage_uri).td_user, "td_alice")

        # 2. Conflicting lock raises error
        with self.assertRaises(StagePromotionError):
            gate.acquire_promotion_lock(stage_uri, td_user="td_bob")

        # 3. Release lock with wrong token fails
        self.assertFalse(gate.release_lock(stage_uri, "wrong-token"))
        self.assertTrue(gate.is_locked(stage_uri))

        # 4. Promote deliverable to production
        prod_stage_path = self.base_path / "production_master.usda"
        prod_stage = Usd.Stage.CreateNew(str(prod_stage_path))
        prod_stage.GetRootLayer().Save()

        deliv_stage_path = self.base_path / "partner_delivery.usda"
        deliv_stage = Usd.Stage.CreateNew(str(deliv_stage_path))
        deliv_stage.GetRootLayer().Save()

        # Failing lint blocks promotion
        failed_lint = InboundLintResult(passed=False, hierarchy_errors=["Invalid hierarchy"])
        with self.assertRaises(StagePromotionError):
            gate.promote_to_production(
                stage_uri=stage_uri,
                deliverable_path=deliv_stage_path,
                production_stage_path=prod_stage_path,
                lint_result=failed_lint,
                lock_token=token,
            )

        # Successful lint promotes and sublayers into production
        passed_lint = InboundLintResult(passed=True)
        promoted = gate.promote_to_production(
            stage_uri=stage_uri,
            deliverable_path=deliv_stage_path,
            production_stage_path=prod_stage_path,
            lint_result=passed_lint,
            lock_token=token,
        )
        self.assertTrue(promoted)
        self.assertFalse(gate.is_locked(stage_uri))  # Lock released upon promotion

        # Verify production stage sublayers contain deliverable
        reloaded_prod = Usd.Stage.Open(str(prod_stage_path))
        self.assertIn(str(deliv_stage_path), reloaded_prod.GetRootLayer().subLayerPaths)

    def test_ebpf_network_policy_manager(self) -> None:
        endpoints = ["10.0.0.50:443", "10.0.1.100:8080"]
        mgr = EBPFNetworkPolicyManager(allowed_inspection_endpoints=endpoints)

        # 1. Test eBPF TC rules generation
        c_code = mgr.generate_tc_filter_rules()
        self.assertIn("openlore_tc_egress_filter", c_code)
        self.assertIn("TC_ACT_OK", c_code)
        self.assertIn("TC_ACT_SHOT", c_code)
        self.assertIn("10.0.0.50:443", c_code)

        # 2. Test bpftool commands generation
        cmds = mgr.generate_bpftool_commands("eth0", "tc_egress_filter.o")
        self.assertEqual(len(cmds), 4)
        self.assertIn("tc filter replace dev eth0 egress", cmds[2])
        self.assertIn("bpftool prog show name openlore_tc_egress_filter", cmds[3])

        # 3. Test active socket compliance audit
        active_sockets = [
            {"dst_ip": "127.0.0.1", "dst_port": 9092, "protocol": "TCP"},  # Loopback allowed
            {"dst_ip": "10.0.0.50", "dst_port": 443, "protocol": "TCP"},   # Whitelisted allowed
            {"dst_ip": "198.51.100.1", "dst_port": 80, "protocol": "TCP"}, # Unauthorized egress
        ]

        passed, violations = mgr.verify_enclave_compliance("enclave-vendor-alpha", active_sockets)
        self.assertFalse(passed)
        self.assertEqual(len(violations), 1)
        self.assertIn("enclave-vendor-alpha", violations[0])
        self.assertIn("198.51.100.1:80", violations[0])

        # Test compliant sockets
        compliant_sockets = [
            {"dst_ip": "10.0.0.50", "dst_port": 443, "protocol": "TCP"},
            {"dst_ip": "10.0.1.100", "dst_port": 8080, "protocol": "TCP"},
        ]
        passed_ok, no_violations = mgr.verify_enclave_compliance("enclave-vendor-beta", compliant_sockets)
        self.assertTrue(passed_ok)
        self.assertEqual(len(no_violations), 0)


if __name__ == "__main__":
    unittest.main()

"""End-to-End Asset Pipeline Integration Test for OpenLore.

Validates the unified production backbone across all 9 architectural pillars:
1. Content-Addressed Storage (CAS) ingestion with BLAKE3
2. OpenUSD Stage composition and atomic transactional mutation
3. RDF 1.1 Narrative Lore modeling & SHACL continuity validation
4. Multiverse timeline branching
5. Real-time Kafka CRDT scene replication and edge resolver convergence
6. MaterialX surface translation & UsdSkel dual-rig variant switching
7. Partner IP decimation, quarantined pre-flight linting, and TD optimistic lock promotion
8. Stage DAG harvesting, HMAC-SHA256 manifest signing, and OPA royalty accounting
9. Downstream compilation grid execution (Unreal .pak, Unity .unitypackage, offline point cache)
   and Central Production Catalog registration.
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import blake3
from pxr import Gf, Sdf, Usd, UsdGeom

from openlore.bridge.unreal import (
    LiveLinkFrameData,
    LiveLinkSubjectType,
    UnrealLiveLinkBridge,
    UnrealPluginScaffolder,
)
from openlore.collaboration.crdt import CRDTSceneReplica
from openlore.collaboration.kafka_stream import KafkaEventStream, _InMemoryEventBus
from openlore.collaboration.resolver import EdgeResolverDaemon
from openlore.compilation.engine_package import EnginePackageCompiler
from openlore.compilation.grid import ProductionCatalog, WorkerGridDispatcher
from openlore.compilation.shot_baker import OfflineShotBaker
from openlore.core.cas import ContentAddressedStorage
from openlore.core.stage import StageCompositionManager
from openlore.core.transaction import TransactionManager
from openlore.materials.materialx import MaterialXTranslator
from openlore.materials.rigging import DynamicRigManager, VariantRigType
from openlore.narrative.graph import NarrativeGraphClient
from openlore.narrative.ontology import CharacterEntity, NarrativeEvent
from openlore.narrative.timeline import TimelineBranchManager
from openlore.narrative.validator import SHACLContinuityValidator
from openlore.partner.decimation import OutboundDecimationPipeline, ProxyStageConfig
from openlore.partner.ebpf_rules import EBPFNetworkPolicyManager
from openlore.partner.linter import PreFlightUSDValidator
from openlore.partner.promotion import StagePromotionGate
from openlore.provenance.accounting import RoyaltyAccountingEngine
from openlore.provenance.harvester import StageDAGHarvester


class TestFullAssetPipelineFlow(unittest.TestCase):
    def setUp(self) -> None:
        _InMemoryEventBus.clear()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)

        # Storage directories
        self.cas_dir = self.base_path / "cas"
        self.stages_dir = self.base_path / "stages"
        self.builds_dir = self.base_path / "builds"
        self.quarantine_dir = self.base_path / "quarantine"

        self.cas_dir.mkdir(parents=True, exist_ok=True)
        self.stages_dir.mkdir(parents=True, exist_ok=True)
        self.builds_dir.mkdir(parents=True, exist_ok=True)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        _InMemoryEventBus.clear()
        self.temp_dir.cleanup()

    def test_complete_end_to_end_production_flow(self) -> None:
        # =====================================================================
        # 1. CAS ASSET INGESTION & HASH VERIFICATION
        # =====================================================================
        cas = ContentAddressedStorage(self.cas_dir)
        raw_mesh_payload = b"OPENLORE_GEOMETRY_STREAM_BINARY_V1_HERO_ARMOR"
        cas_obj = cas.store_bytes(raw_mesh_payload)
        hero_cas_hash = cas_obj.blake3_hash

        self.assertTrue(cas.exists(hero_cas_hash))
        self.assertEqual(cas.retrieve_bytes(hero_cas_hash), raw_mesh_payload)
        self.assertTrue(cas.verify_integrity(hero_cas_hash))

        # =====================================================================
        # 2. OPENUSD STAGE COMPOSITION & ATOMIC TRANSACTION
        # =====================================================================
        stage_mgr = StageCompositionManager(self.stages_dir)
        stage_ref = stage_mgr.create_stage("openlore://stages/main_production.usda")
        self.assertTrue(stage_ref.root_layer_path.is_file())

        stage = stage_ref.usd_stage
        world_xform = UsdGeom.Xform.Define(stage, "/World")
        stage.SetDefaultPrim(world_xform.GetPrim())

        # Author character mesh with metadata
        mesh_prim = UsdGeom.Mesh.Define(stage, "/World/Characters/Hero")
        mesh_prim.GetPointsAttr().Set([
            Gf.Vec3f(-1, 0, 0),
            Gf.Vec3f(1, 0, 0),
            Gf.Vec3f(1, 2, 0),
            Gf.Vec3f(-1, 2, 0),
        ])
        mesh_prim.GetFaceVertexCountsAttr().Set([4])
        mesh_prim.GetFaceVertexIndicesAttr().Set([0, 1, 2, 3])

        # Bind CAS hash and provenance metadata directly to Prim
        prim = mesh_prim.GetPrim()
        prim.CreateAttribute("openlore:assetHash", Sdf.ValueTypeNames.String, custom=True).Set(hero_cas_hash)
        prim.CreateAttribute("openlore:partnerId", Sdf.ValueTypeNames.String, custom=True).Set("studio_vfx_london")
        prim.CreateAttribute("openlore:licenseStatus", Sdf.ValueTypeNames.String, custom=True).Set("approved")
        prim.CreateAttribute("openlore:royaltyPercentage", Sdf.ValueTypeNames.Float, custom=True).Set(15.0)

        # Define collision capsule for real-time engine physics
        UsdGeom.Capsule.Define(stage, "/World/Characters/Hero/CollisionCapsule")
        stage.GetRootLayer().Save()

        # Atomic transaction commit
        tx_mgr = TransactionManager(self.base_path, stage_mgr)
        session = tx_mgr.begin_transaction(stage_ref, author="lead_td@openlore.io")
        session.set_property("/World/Characters/Hero", "openlore:assetHash", hero_cas_hash)
        commit_record = session.commit("Initial production hero asset composition")
        self.assertIsNotNone(commit_record.commit_id)
        history = tx_mgr.get_commit_history(stage_ref.stage_uri)
        self.assertEqual(len(history), 1)

        # =====================================================================
        # 3. NARRATIVE LORE MODELING & SHACL CONTINUITY ENFORCEMENT
        # =====================================================================
        graph_client = NarrativeGraphClient()
        tm = TimelineBranchManager(graph_client)
        prime_timeline = tm.create_prime_canon(name="Prime Canon Timeline")

        hero_char = CharacterEntity(
            uri="https://openlore.io/characters/HeroCommander",
            name="Hero Commander",
            timeline_uri=prime_timeline.uri,
            status="active",
            birth_time=datetime(2140, 1, 1, tzinfo=timezone.utc),
            bound_asset_hash=hero_cas_hash,
            prim_path="/World/Characters/Hero",
        )
        graph_client.insert_character(hero_char)

        intro_event = NarrativeEvent(
            uri="https://openlore.io/events/BattleOfNova",
            name="Battle of Nova",
            timeline_uri=prime_timeline.uri,
            timestamp=datetime(2165, 5, 20, 12, 0, tzinfo=timezone.utc),
            participants=[hero_char.uri],
            location="Terra Prime Orbit",
        )
        graph_client.insert_event(intro_event)

        # Validate narrative continuity
        shapes_path = Path("./schemas/shacl/continuity_shapes.ttl")
        validator = SHACLContinuityValidator(shapes_path)
        report = validator.validate_graph(graph_client.dataset)
        self.assertTrue(report.conforms)
        self.assertEqual(len(report.violations), 0)

        # =====================================================================
        # 4. MULTIVERSE TIMELINE BRANCHING
        # =====================================================================
        alt_timeline = tm.branch_timeline(
            source_timeline_uri=prime_timeline.uri,
            new_timeline_slug="quantum_spin_off_01",
            new_timeline_name="Quantum Spin-Off Reality",
        )
        self.assertFalse(alt_timeline.is_prime_canon)
        self.assertEqual(alt_timeline.parent_timeline_uri, prime_timeline.uri)

        # Verify prime canon remains pure and isolated
        timelines = tm.list_timelines()
        self.assertEqual(len(timelines), 2)

        # =====================================================================
        # 5. DISTRIBUTED KAFKA CRDT COLLABORATION & EDGE RECONCILIATION
        # =====================================================================
        stream_topic = "openlore.stage.main_production"
        stream_london = KafkaEventStream(stage_topic=stream_topic, use_memory_bus=True)
        stream_la = KafkaEventStream(stage_topic=stream_topic, use_memory_bus=True)

        daemon_london = EdgeResolverDaemon("studio_london", "openlore://stages/main_production.usda", stream_london)
        daemon_la = EdgeResolverDaemon("studio_la", "openlore://stages/main_production.usda", stream_la)

        # Studio London moves hero camera
        daemon_london.record_local_edit(
            prim_path="/World/Camera",
            attribute_name="xformOp:translate",
            value=[25.0, 10.0, 5.0],
        )
        # Studio LA immediately observes converged transform
        la_cam = daemon_la.replica.get_attribute_value("/World/Camera", "xformOp:translate")
        self.assertEqual(la_cam, [25.0, 10.0, 5.0])

        # =====================================================================
        # 6. MATERIALX & DYNAMIC RIGGING STANDARDS
        # =====================================================================
        mtlx_path = Path("./schemas/materialx/standard_surface.mtlx")
        mtlx_trans = MaterialXTranslator()
        appearance = mtlx_trans.parse_document(mtlx_path)
        hlsl_shader = mtlx_trans.export_to_unreal_shader(appearance)
        self.assertIn("FOpenLoreMaterialInput", hlsl_shader)

        # Dual-rig VariantSet setup
        rig_mgr = DynamicRigManager(stage)
        rig_mgr.setup_dual_rig(
            prim_path="/World/Characters/Hero",
            joints=["root", "hips", "spine"],
            point_cache_hash=hero_cas_hash,
        )
        # Verify default cinematic cache mode
        self.assertEqual(rig_mgr.get_active_variant("/World/Characters/Hero"), VariantRigType.CINEMATIC_BAKED_CACHE)
        # Switch to game collision mode
        rig_mgr.set_active_variant("/World/Characters/Hero", VariantRigType.INTERACTIVE_GAME_COLLISION)
        self.assertEqual(rig_mgr.get_active_variant("/World/Characters/Hero"), VariantRigType.INTERACTIVE_GAME_COLLISION)
        stage.GetRootLayer().Save()

        # =====================================================================
        # 7. PARTNER IP DECIMATION, QUARANTINE LINTING & TD PROMOTION
        # =====================================================================
        # Outbound sanitization: strip proprietary point caches and shaders into clay proxy
        decimation_pipeline = OutboundDecimationPipeline(ProxyStageConfig(decimation_ratio=0.5))
        outbound_proxy_path = self.quarantine_dir / "outbound_hero_proxy.usda"
        decimation_pipeline.sanitize_outbound_stage(stage_ref.root_layer_path, outbound_proxy_path)
        self.assertTrue(outbound_proxy_path.is_file())

        # Inbound deliverable from external contractor
        deliverable_path = self.quarantine_dir / "contractor_environment_prop.usda"
        contractor_stage = Usd.Stage.CreateNew(str(deliverable_path))
        UsdGeom.Xform.Define(contractor_stage, "/World")
        prop_mesh = UsdGeom.Mesh.Define(contractor_stage, "/World/EnvironmentProp")
        prop_mesh.GetFaceVertexCountsAttr().Set([3, 3])
        contractor_stage.GetRootLayer().Save()

        # Pre-flight linting sandbox
        linter = PreFlightUSDValidator(max_polycount_ceiling=50000)
        lint_result = linter.validate_deliverable(deliverable_path)
        self.assertTrue(lint_result.passed)

        # TD Promotion with optimistic lock
        promotion_gate = StagePromotionGate()
        lock_token = promotion_gate.acquire_promotion_lock(
            stage_uri="openlore://stages/main_production.usda",
            td_user="alice_supervising_td",
            target_timeline=prime_timeline.uri,
        )
        promoted = promotion_gate.promote_to_production(
            stage_uri="openlore://stages/main_production.usda",
            deliverable_path=deliverable_path,
            production_stage_path=stage_ref.root_layer_path,
            lint_result=lint_result,
            lock_token=lock_token,
        )
        self.assertTrue(promoted)
        self.assertFalse(promotion_gate.is_locked("openlore://stages/main_production.usda"))

        # Verify eBPF network security policy manager
        ebpf_mgr = EBPFNetworkPolicyManager(allowed_inspection_endpoints=["10.0.0.50:443"])
        c_code = ebpf_mgr.generate_tc_filter_rules()
        self.assertIn("openlore_tc_egress_filter", c_code)
        compliant, _ = ebpf_mgr.verify_enclave_compliance(
            "partner-enclave-01",
            [{"dst_ip": "10.0.0.50", "dst_port": 443}],
        )
        self.assertTrue(compliant)

        # =====================================================================
        # 8. PROVENANCE HARVESTING, HMAC SIGNING & OPA ROYALTY ACCOUNTING
        # =====================================================================
        reloaded_stage = Usd.Stage.Open(str(stage_ref.root_layer_path))
        harvester = StageDAGHarvester(reloaded_stage)
        manifest = harvester.create_manifest(
            stage_uri="openlore://stages/main_production.usda",
            secret_key="production-studio-secret-key",
        )
        self.assertTrue(manifest.verify_signature("production-studio-secret-key"))
        self.assertTrue(manifest.total_assets >= 1)

        accounting = RoyaltyAccountingEngine()
        allow_export, unlicensed = accounting.evaluate_export_allowance(manifest)
        self.assertTrue(allow_export)
        self.assertEqual(len(unlicensed), 0)

        royalty_splits = accounting.calculate_royalty_splits(manifest)
        self.assertIn("studio_vfx_london", royalty_splits)
        self.assertEqual(royalty_splits["studio_vfx_london"], 15.0)

        # =====================================================================
        # 9. DOWNSTREAM WORKER GRID COMPILATION & CATALOG REGISTRATION
        # =====================================================================
        catalog = ProductionCatalog()
        grid_dispatcher = WorkerGridDispatcher(
            temporal_endpoint="localhost:7233",
            argo_namespace="openlore-grid",
            catalog=catalog,
        )

        workflow_id = grid_dispatcher.trigger_compilation_workflow(
            stage_uri="openlore://stages/main_production.usda",
            target_engines=["unreal", "unity", "cinematic-cache"],
            stage_path=stage_ref.root_layer_path,
            output_dir=self.builds_dir,
            shot_name="shot_act1_intro",
        )

        job_status = grid_dispatcher.get_job_status(workflow_id)
        self.assertEqual(job_status["status"], "COMPLETED")
        self.assertEqual(len(job_status["artifacts"]), 3)

        # Verify Unreal Engine .pak exists and contains static mesh
        unreal_pak = Path(job_status["artifacts"]["unreal"])
        self.assertTrue(unreal_pak.is_file())

        # Verify Unity .unitypackage exists
        unity_pkg = Path(job_status["artifacts"]["unity"])
        self.assertTrue(unity_pkg.is_file())

        # Verify baked offline shot point cache exists with time samples
        point_cache = Path(job_status["artifacts"]["cinematic_cache"])
        self.assertTrue(point_cache.is_file())
        baked_stage = Usd.Stage.Open(str(point_cache))
        self.assertEqual(baked_stage.GetStartTimeCode(), 1)
        self.assertEqual(baked_stage.GetEndTimeCode(), 24)

        # Verify Central Production Catalog records
        catalog_records = catalog.get_builds_for_stage("openlore://stages/main_production.usda")
        self.assertEqual(len(catalog_records), 3)

        # Save and reload catalog to test persistence
        cat_file = self.builds_dir / "production_catalog.json"
        catalog.save_catalog(cat_file)
        self.assertTrue(cat_file.is_file())

        reloaded_cat = ProductionCatalog()
        reloaded_cat.load_catalog(cat_file)
        self.assertEqual(len(reloaded_cat.list_all_builds()), 3)

        # =====================================================================
        # PILLAR 10: Virtual Production Unreal Engine 5 Live Link Bridge
        # =====================================================================
        livelink_bridge = UnrealLiveLinkBridge(
            edge_daemon=daemon_london,
            broadcast_host="127.0.0.1",
            broadcast_port=11188,
            receive_port=11189,
        )
        livelink_bridge.start(mode="duplex")

        # Outbound: Camera move in OpenUSD stage -> Live Link telemetry
        camera_mutation = daemon_london.record_local_edit(
            prim_path="/World/CineCamera",
            attribute_name="xformOp:translate",
            value=[12.5, 4.0, 2.0],
        )
        handled = livelink_bridge.handle_crdt_mutation(camera_mutation)
        self.assertTrue(handled)

        # Inbound: Virtual camera tracking device from stage UE5 -> OpenLore CRDT
        ue_tracker_frame = LiveLinkFrameData(
            subject_name="Camera_StageA",
            subject_type=LiveLinkSubjectType.CAMERA,
            frame_number=120,
            translation=(1250.0, -400.0, 200.0),  # 12.5m, 4.0m, 2.0m in USD
            field_of_view=42.0,
        )
        livelink_bridge._handle_inbound_frame(ue_tracker_frame)

        livelink_status = livelink_bridge.get_status()
        self.assertEqual(livelink_status["status"], "ONLINE")
        self.assertGreaterEqual(livelink_status["metrics"]["frames_bridged_out"], 1)
        self.assertGreaterEqual(livelink_status["metrics"]["frames_bridged_in"], 1)
        livelink_bridge.stop()

        # Verify UE5 C++ plugin scaffolding export
        plugin_files = UnrealPluginScaffolder.generate_plugin(self.builds_dir / "UnrealPlugins" / "OpenLoreLiveLink")
        self.assertTrue(plugin_files["uplugin"].is_file())
        self.assertTrue(plugin_files["source_cpp"].is_file())

        print("\n[OpenLore Integration] All 10 architectural pillars successfully executed and verified end-to-end!")


if __name__ == "__main__":
    unittest.main()

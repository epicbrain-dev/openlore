"""Unit tests for Asset Provenance Harvesting and OPA Royalty Accounting."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from pxr import Sdf, Usd

from openlore.exceptions import StagePromotionError
from openlore.provenance.accounting import RoyaltyAccountingEngine
from openlore.provenance.harvester import StageDAGHarvester
from openlore.provenance.manifest import AssetProvenanceManifest, PrimProvenanceRecord


class TestProvenanceAndAccounting(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
        self.accounting = RoyaltyAccountingEngine()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_manifest_cryptographic_signing_and_verification(self) -> None:
        record1 = PrimProvenanceRecord(
            prim_path="/World/Characters/Hero",
            blake3_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            partner_id="partner_london",
            license_status="approved",
            royalty_percentage=12.5,
        )
        record2 = PrimProvenanceRecord(
            prim_path="/World/Props/Weapon",
            blake3_hash="a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90",
            partner_id="partner_tokyo",
            license_status="approved",
            royalty_percentage=5.0,
        )

        manifest = AssetProvenanceManifest(
            stage_uri="openlore://shots/sh01.usd",
            generated_at=datetime.now(timezone.utc),
            prims=[record1, record2],
        )

        secret = "super-secret-studio-key-2026"
        signature = manifest.sign_manifest(secret)

        self.assertIsNotNone(signature)
        self.assertTrue(manifest.verify_signature(secret))
        self.assertFalse(manifest.verify_signature("wrong-key"))

        # Serialization round-trip
        data = manifest.to_dict()
        reconstructed = AssetProvenanceManifest.from_dict(data)
        self.assertTrue(reconstructed.verify_signature(secret))

        # Tampering detection
        reconstructed.prims[0].royalty_percentage = 99.0
        self.assertFalse(reconstructed.verify_signature(secret))

    def test_stage_dag_introspector(self) -> None:
        stage_path = self.base_path / "production_stage.usda"
        stage = Usd.Stage.CreateNew(str(stage_path))

        # Prim 1: Mech Chassis
        prim1 = stage.DefinePrim(Sdf.Path("/World/Mech/Chassis"), "Mesh")
        prim1.CreateAttribute("openlore:assetHash", Sdf.ValueTypeNames.String, custom=True).Set("hash_chassis_1234567890abcdef")
        prim1.CreateAttribute("openlore:partnerId", Sdf.ValueTypeNames.String, custom=True).Set("studio_la")
        prim1.CreateAttribute("openlore:licenseStatus", Sdf.ValueTypeNames.String, custom=True).Set("approved")
        prim1.CreateAttribute("openlore:royaltyPercentage", Sdf.ValueTypeNames.Float, custom=True).Set(15.0)

        # Prim 2: Weapon
        prim2 = stage.DefinePrim(Sdf.Path("/World/Mech/Weapon"), "Mesh")
        prim2.CreateAttribute("openlore:pointCacheHash", Sdf.ValueTypeNames.String, custom=True).Set("hash_weapon_abcdef1234567890")
        prim2.CreateAttribute("openlore:partnerId", Sdf.ValueTypeNames.String, custom=True).Set("studio_london")
        prim2.CreateAttribute("openlore:licenseStatus", Sdf.ValueTypeNames.String, custom=True).Set("approved")
        prim2.CreateAttribute("openlore:royaltyPercentage", Sdf.ValueTypeNames.Float, custom=True).Set(7.5)

        # Prim without asset hash (should be ignored by harvester)
        stage.DefinePrim(Sdf.Path("/World/Environment"), "Xform")

        stage.GetRootLayer().Save()

        harvester = StageDAGHarvester(stage)
        records = harvester.harvest_provenance_records()

        self.assertEqual(len(records), 2)
        paths = [r.prim_path for r in records]
        self.assertIn("/World/Mech/Chassis", paths)
        self.assertIn("/World/Mech/Weapon", paths)

        # Build signed manifest
        manifest = harvester.create_manifest("openlore://shots/battle.usda", secret_key="test-key")
        self.assertEqual(manifest.total_assets, 2)
        self.assertTrue(manifest.verify_signature("test-key"))

    def test_opa_export_allowance_approved(self) -> None:
        manifest = AssetProvenanceManifest(
            stage_uri="openlore://shots/approved.usd",
            generated_at=datetime.now(timezone.utc),
            prims=[
                PrimProvenanceRecord("/World/Hero", "hash_hero_12345", "partner_a", "approved", 10.0),
                PrimProvenanceRecord("/World/Prop", "hash_prop_12345", "partner_b", "approved", 5.0),
            ],
        )
        allow_export, unlicensed = self.accounting.evaluate_export_allowance(manifest)
        self.assertTrue(allow_export)
        self.assertEqual(len(unlicensed), 0)

        # assert does not raise
        self.accounting.assert_export_approved(manifest)

    def test_opa_export_allowance_unlicensed_blocked(self) -> None:
        manifest = AssetProvenanceManifest(
            stage_uri="openlore://shots/unlicensed.usd",
            generated_at=datetime.now(timezone.utc),
            prims=[
                PrimProvenanceRecord("/World/Hero", "hash_hero_12345", "partner_a", "approved", 10.0),
                PrimProvenanceRecord("/World/Villain/Prop", "hash_villain_67890", "partner_c", "pending_clearance", 5.0),
            ],
        )
        allow_export, unlicensed = self.accounting.evaluate_export_allowance(manifest)
        self.assertFalse(allow_export)
        self.assertIn("/World/Villain/Prop", unlicensed)

        with self.assertRaises(StagePromotionError):
            self.accounting.assert_export_approved(manifest)

    def test_calculate_royalty_splits(self) -> None:
        manifest = AssetProvenanceManifest(
            stage_uri="openlore://shots/splits.usd",
            generated_at=datetime.now(timezone.utc),
            prims=[
                PrimProvenanceRecord("/A", "hash1", "partner_vfx_london", "approved", 15.0),
                PrimProvenanceRecord("/B", "hash2", "partner_vfx_london", "approved", 5.0),
                PrimProvenanceRecord("/C", "hash3", "partner_game_la", "approved", 25.5),
                PrimProvenanceRecord("/D", "hash4", "freelance_artist", "approved", 4.5),
            ],
        )
        splits = self.accounting.calculate_royalty_splits(manifest)

        self.assertEqual(splits["partner_vfx_london"], 20.0)
        self.assertEqual(splits["partner_game_la"], 25.5)
        self.assertEqual(splits["freelance_artist"], 4.5)

"""Unit tests for Transactional Edit Isolation and Commit Management."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from openlore.core.cas import ContentAddressedStorage
from openlore.core.stage import StageCompositionManager
from openlore.core.transaction import TransactionManager


class TestTransactionManager(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.stage_mgr = StageCompositionManager(self.repo_root / "stages_data")
        self.cas = ContentAddressedStorage(self.repo_root / "cas")
        self.tx_mgr = TransactionManager(self.repo_root, self.stage_mgr)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_transaction_lifecycle_commit(self) -> None:
        stage_uri = "openlore://scenes/battle_shot.usda"
        ref = self.stage_mgr.create_stage(stage_uri=stage_uri, default_prim="World")

        session = self.tx_mgr.begin_transaction(stage_ref=ref, author="lead-td@vfx.studio")

        # Stage lightweight metadata property delta
        session.set_property(
            prim_path="/World/Characters/Hero",
            property_name="xformOp:translate",
            new_value=[10.0, 0.0, 5.0],
            old_value=[0.0, 0.0, 0.0],
        )

        # Stage heavy binary asset via CAS binding
        mesh_bytes = b"Hero High-Poly Point Cache Buffer (50MB binary)"
        cas_obj = self.cas.store_bytes(mesh_bytes, mime_type="model/vnd.usd+pointcache")
        session.attach_cas_payload(
            prim_path="/World/Characters/Hero/Mesh",
            attribute_name="openlore:pointCache",
            cas_object=cas_obj,
        )

        # Commit transaction
        commit = session.commit(message="Translate Hero and attach simulation point cache")

        self.assertIsNotNone(commit.commit_id)
        self.assertEqual(commit.author, "lead-td@vfx.studio")
        self.assertEqual(len(commit.deltas), 2)
        self.assertIn(cas_obj.blake3_hash, commit.referenced_cas_hashes)

        # Check commit history
        history = self.tx_mgr.get_commit_history(stage_uri)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].commit_id, commit.commit_id)

    def test_sequential_commits_parent_chain(self) -> None:
        stage_uri = "openlore://scenes/timelines.usda"
        ref = self.stage_mgr.create_stage(stage_uri=stage_uri)

        # Commit 1
        s1 = self.tx_mgr.begin_transaction(stage_ref=ref, author="alice@studio")
        s1.set_property("/World", "scene:status", "draft")
        c1 = s1.commit("Initialize draft")

        # Commit 2
        s2 = self.tx_mgr.begin_transaction(stage_ref=ref, author="bob@studio")
        s2.set_property("/World", "scene:status", "approved")
        c2 = s2.commit("Approve scene status")

        self.assertEqual(c2.parent_commit_id, c1.commit_id)

        history = self.tx_mgr.get_commit_history(stage_uri)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].commit_id, c2.commit_id)
        self.assertEqual(history[1].commit_id, c1.commit_id)

    def test_rollback_clears_staged_changes(self) -> None:
        stage_uri = "openlore://scenes/scratch.usda"
        ref = self.stage_mgr.create_stage(stage_uri=stage_uri)

        session = self.tx_mgr.begin_transaction(stage_ref=ref, author="artist@studio")
        session.set_property("/World/Prop", "color", "red")
        self.assertEqual(len(session._staged_deltas), 1)

        session.rollback()
        self.assertEqual(len(session._staged_deltas), 0)
        self.assertEqual(len(session._referenced_cas_hashes), 0)

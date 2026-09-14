"""Integration test for Edge Resolver Daemon shadow buffering and causal convergence."""

from __future__ import annotations

import unittest

from openlore.collaboration.crdt import CRDTPartialMutation
from openlore.collaboration.kafka_stream import KafkaEventStream, _InMemoryEventBus
from openlore.collaboration.resolver import EdgeResolverDaemon


class TestResolverConvergence(unittest.TestCase):
    def setUp(self) -> None:
        _InMemoryEventBus.clear()
        self.topic = "openlore.stage.volcano_battle"
        self.stage_uri = "openlore://scenes/volcano_battle.usda"

        # Initialize event stream
        self.stream_la = KafkaEventStream(stage_topic=self.topic, use_memory_bus=True)
        self.stream_london = KafkaEventStream(stage_topic=self.topic, use_memory_bus=True)

        # Initialize edge resolver daemons for both studios
        self.daemon_la = EdgeResolverDaemon(
            studio_id="studio_la",
            stage_uri=self.stage_uri,
            event_stream=self.stream_la,
        )
        self.daemon_london = EdgeResolverDaemon(
            studio_id="studio_london",
            stage_uri=self.stage_uri,
            event_stream=self.stream_london,
        )

    def tearDown(self) -> None:
        _InMemoryEventBus.clear()

    def test_live_online_synchronization(self) -> None:
        # Studio LA modifies camera position on the LED volume soundstage
        self.daemon_la.record_local_edit(
            prim_path="/World/Camera",
            attribute_name="xformOp:translate",
            value=[10.0, 5.0, 2.0],
        )

        # Studio London replica immediately reflects the modification
        london_cam = self.daemon_london.replica.get_attribute_value("/World/Camera", "xformOp:translate")
        self.assertEqual(london_cam, [10.0, 5.0, 2.0])

    def test_severance_shadow_buffering_and_reconnection_convergence(self) -> None:
        # 1. Sever London studio network connection
        self.daemon_london.set_connectivity(online=False)
        self.assertFalse(self.daemon_london.is_online)

        # 2. Studio London records multiple edits while offline
        self.daemon_london.record_local_edit(
            prim_path="/World/Hero",
            attribute_name="visibility",
            value="inherited",
        )
        self.daemon_london.record_local_edit(
            prim_path="/World/Hero",
            attribute_name="xformOp:translate",
            value=[100.0, 0.0, 50.0],
        )
        self.daemon_london.record_local_edit(
            prim_path="/World/Hero/Mesh",
            attribute_name="material:binding",
            value="openlore://materials/hero_armor.mtlx",
        )

        # Verify edits buffered in shadow storage
        self.assertEqual(self.daemon_london.shadow_buffer_size, 3)

        # Verify Studio LA has NOT received them yet
        self.assertIsNone(self.daemon_la.replica.get_attribute_value("/World/Hero", "visibility"))

        # 3. Meanwhile, Studio LA independently edits Villain and Environment props
        self.daemon_la.record_local_edit(
            prim_path="/World/Villain",
            attribute_name="xformOp:translate",
            value=[-50.0, 0.0, 20.0],
        )
        self.daemon_la.record_local_edit(
            prim_path="/World/Environment/Lighting",
            attribute_name="inputs:intensity",
            value=2500.0,
        )

        # 4. Network restored! Studio London reconnects
        self.daemon_london.set_connectivity(online=True)

        # Shadow buffer should be automatically flushed and emptied
        self.assertEqual(self.daemon_london.shadow_buffer_size, 0)

        # 5. Verify DETERMINISTIC CAUSAL CONVERGENCE across both studios
        # Both studios must possess identical attribute values
        la_hero_pos = self.daemon_la.replica.get_attribute_value("/World/Hero", "xformOp:translate")
        london_hero_pos = self.daemon_london.replica.get_attribute_value("/World/Hero", "xformOp:translate")
        self.assertEqual(la_hero_pos, [100.0, 0.0, 50.0])
        self.assertEqual(london_hero_pos, [100.0, 0.0, 50.0])

        la_villain_pos = self.daemon_la.replica.get_attribute_value("/World/Villain", "xformOp:translate")
        london_villain_pos = self.daemon_london.replica.get_attribute_value("/World/Villain", "xformOp:translate")
        self.assertEqual(la_villain_pos, [-50.0, 0.0, 20.0])
        self.assertEqual(london_villain_pos, [-50.0, 0.0, 20.0])

        la_light = self.daemon_la.replica.get_attribute_value("/World/Environment/Lighting", "inputs:intensity")
        london_light = self.daemon_london.replica.get_attribute_value("/World/Environment/Lighting", "inputs:intensity")
        self.assertEqual(la_light, 2500.0)
        self.assertEqual(london_light, 2500.0)

"""Unit tests for Unreal Engine 5 Live Link Bridge, Stream Provider, and Receiver."""

from __future__ import annotations

import socket
import time
import unittest
from datetime import datetime, timezone

from openlore.bridge.unreal.bridge import UnrealLiveLinkBridge
from openlore.bridge.unreal.protocol import (
    CoordinateConverter,
    LiveLinkFrameData,
    LiveLinkStaticData,
    LiveLinkSubjectType,
)
from openlore.bridge.unreal.provider import LiveLinkStreamProvider
from openlore.bridge.unreal.receiver import LiveLinkStreamReceiver
from openlore.collaboration.crdt import CRDTPartialMutation
from openlore.collaboration.kafka_stream import KafkaEventStream
from openlore.collaboration.resolver import EdgeResolverDaemon
from openlore.collaboration.vector_clock import VectorClock


def get_free_port() -> int:
    """Find an available ephemeral UDP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestLiveLinkBridge(unittest.TestCase):
    def test_udp_provider_receiver_loopback(self) -> None:
        port = get_free_port()
        receiver = LiveLinkStreamReceiver(bind_host="127.0.0.1", port=port)
        provider = LiveLinkStreamProvider(host="127.0.0.1", port=port)

        received_frames: list[LiveLinkFrameData] = []
        receiver.on_frame(lambda f: received_frames.append(f))

        receiver.start()
        time.sleep(0.05)

        try:
            static_data = LiveLinkStaticData(
                subject_name="TestCam",
                subject_type=LiveLinkSubjectType.CAMERA,
            )
            frame_data = LiveLinkFrameData(
                subject_name="TestCam",
                subject_type=LiveLinkSubjectType.CAMERA,
                frame_number=1,
                translation=(250.0, -100.0, 175.0),
                field_of_view=55.0,
            )

            provider.register_subject(static_data, frame_data)
            provider.broadcast_frame("TestCam", wire_format="json")

            # Wait for packet dispatch
            deadline = time.time() + 1.0
            while not received_frames and time.time() < deadline:
                time.sleep(0.02)

            self.assertGreaterEqual(len(received_frames), 1)
            got = received_frames[0]
            self.assertEqual(got.subject_name, "TestCam")
            self.assertAlmostEqual(got.translation[0], 250.0)
            self.assertAlmostEqual(got.translation[1], -100.0)
            self.assertAlmostEqual(got.field_of_view, 55.0)

        finally:
            receiver.stop()
            provider.close()

    def test_outbound_crdt_sync_to_livelink(self) -> None:
        port = get_free_port()
        bridge = UnrealLiveLinkBridge(
            broadcast_host="127.0.0.1",
            broadcast_port=port,
            receive_port=get_free_port(),
        )

        try:
            bridge.start(mode="broadcast")

            # Simulate artist edit in OpenUSD stage at (2.5m, -1.0m, 1.8m)
            mutation = CRDTPartialMutation(
                mutation_id="mut_001",
                stage_uri="openlore://stages/root.usda",
                prim_path="/World/CineCamera",
                attribute_name="xformOp:translate",
                value=[2.5, -1.0, 1.8],
                clock=VectorClock({"studio_ldn": 1}),
                origin_studio="studio_ldn",
                timestamp=datetime.now(timezone.utc),
            )

            handled = bridge.handle_crdt_mutation(mutation)
            self.assertTrue(handled)

            # Check that provider frame was updated with Unreal coordinates (cm, left-handed)
            # 2.5m * 100 = 250cm, -(-1.0m) * 100 = 100cm, 1.8m * 100 = 180cm
            frame = bridge.provider._subjects_frame.get("Camera_StageA")
            self.assertIsNotNone(frame)
            self.assertAlmostEqual(frame.translation[0], 250.0)
            self.assertAlmostEqual(frame.translation[1], 100.0)
            self.assertAlmostEqual(frame.translation[2], 180.0)

            status = bridge.get_status()
            self.assertEqual(status["mode"], "broadcast")
            self.assertGreaterEqual(status["metrics"]["frames_bridged_out"], 1)

        finally:
            bridge.stop()

    def test_inbound_livelink_sync_to_edge_resolver(self) -> None:
        port_rx = get_free_port()
        port_tx = get_free_port()

        event_stream = KafkaEventStream(stage_topic="livelink_test", use_memory_bus=True)
        daemon = EdgeResolverDaemon(
            studio_id="studio_vfx_london",
            stage_uri="openlore://stages/root.usda",
            event_stream=event_stream,
        )

        bridge = UnrealLiveLinkBridge(
            edge_daemon=daemon,
            broadcast_host="127.0.0.1",
            broadcast_port=port_tx,
            receive_port=port_rx,
            studio_id="UE5-VP-STAGE-01",
        )

        try:
            bridge.start(mode="duplex")

            # Simulate incoming Live Link frame from virtual camera tracker in UE5:
            # Position: (500cm, 200cm, 150cm) -> should convert to (5.0m, -2.0m, 1.5m) in USD
            inbound_frame = LiveLinkFrameData(
                subject_name="Camera_StageA",
                subject_type=LiveLinkSubjectType.CAMERA,
                frame_number=88,
                translation=(500.0, 200.0, 150.0),
                rotation=(0.0, 0.0, 0.0, 1.0),
                field_of_view=40.0,
            )

            bridge._handle_inbound_frame(inbound_frame)

            # Check that daemon received edits
            trans_val = daemon.replica.get_attribute_value("/World/CineCamera", "xformOp:translate")
            self.assertIsNotNone(trans_val)
            self.assertAlmostEqual(trans_val[0], 5.0)
            self.assertAlmostEqual(trans_val[1], -2.0)
            self.assertAlmostEqual(trans_val[2], 1.5)

            status = bridge.get_status()
            self.assertEqual(status["metrics"]["frames_bridged_in"], 1)

        finally:
            bridge.stop()


if __name__ == "__main__":
    unittest.main()

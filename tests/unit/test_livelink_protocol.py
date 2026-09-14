"""Unit tests for Unreal Engine 5 Live Link protocol, schemas, and coordinate conversion."""

from __future__ import annotations

import unittest
from openlore.bridge.unreal.protocol import (
    CoordinateConverter,
    LiveLinkFrameData,
    LiveLinkPacket,
    LiveLinkStaticData,
    LiveLinkSubjectType,
)
from openlore.exceptions import LiveLinkBridgeError


class TestLiveLinkProtocol(unittest.TestCase):
    def test_coordinate_conversion_position_zup(self) -> None:
        # 1m forward, 2m left, 3m up in Right-Handed USD Z-up
        pos_usd = (1.0, 2.0, 3.0)
        pos_ue = CoordinateConverter.usd_to_unreal_position(pos_usd, up_axis="Z", meters_per_unit=1.0)
        # Should be: 100cm forward (X), -200cm right (Y), 300cm up (Z)
        self.assertAlmostEqual(pos_ue[0], 100.0)
        self.assertAlmostEqual(pos_ue[1], -200.0)
        self.assertAlmostEqual(pos_ue[2], 300.0)

        # Roundtrip back to USD
        roundtrip_usd = CoordinateConverter.unreal_to_usd_position(pos_ue, up_axis="Z", meters_per_unit=1.0)
        self.assertAlmostEqual(roundtrip_usd[0], pos_usd[0])
        self.assertAlmostEqual(roundtrip_usd[1], pos_usd[1])
        self.assertAlmostEqual(roundtrip_usd[2], pos_usd[2])

    def test_coordinate_conversion_position_yup(self) -> None:
        pos_usd = (1.0, 2.0, 3.0)
        pos_ue = CoordinateConverter.usd_to_unreal_position(pos_usd, up_axis="Y", meters_per_unit=1.0)
        self.assertAlmostEqual(pos_ue[0], 300.0)
        self.assertAlmostEqual(pos_ue[1], 100.0)
        self.assertAlmostEqual(pos_ue[2], 200.0)

    def test_quaternion_and_euler_roundtrip(self) -> None:
        roll, pitch, yaw = 10.0, 25.0, -45.0
        quat = CoordinateConverter.euler_to_quaternion(roll, pitch, yaw)
        euler_out = CoordinateConverter.quaternion_to_euler(quat)

        self.assertAlmostEqual(euler_out[0], roll, places=4)
        self.assertAlmostEqual(euler_out[1], pitch, places=4)
        self.assertAlmostEqual(euler_out[2], yaw, places=4)

    def test_quaternion_chirality_flip(self) -> None:
        quat_usd = (0.1, 0.2, 0.3, 0.9)
        quat_ue = CoordinateConverter.usd_to_unreal_quaternion(quat_usd, up_axis="Z")
        self.assertAlmostEqual(quat_ue[0], 0.1)
        self.assertAlmostEqual(quat_ue[1], -0.2)
        self.assertAlmostEqual(quat_ue[2], 0.3)
        self.assertAlmostEqual(quat_ue[3], -0.9)

        roundtrip = CoordinateConverter.unreal_to_usd_quaternion(quat_ue, up_axis="Z")
        self.assertAlmostEqual(roundtrip[0], quat_usd[0])
        self.assertAlmostEqual(roundtrip[1], quat_usd[1])
        self.assertAlmostEqual(roundtrip[2], quat_usd[2])
        self.assertAlmostEqual(roundtrip[3], quat_usd[3])

    def test_static_data_serialization(self) -> None:
        static = LiveLinkStaticData(
            subject_name="Camera_StageA",
            subject_type=LiveLinkSubjectType.CAMERA,
            filmback_width=36.0,
            filmback_height=24.0,
        )
        d = static.to_dict()
        self.assertEqual(d["type"], "StaticData")
        self.assertEqual(d["subject_name"], "Camera_StageA")
        self.assertEqual(d["role"], "Camera")

        restored = LiveLinkStaticData.from_dict(d)
        self.assertEqual(restored.subject_name, static.subject_name)
        self.assertEqual(restored.subject_type, LiveLinkSubjectType.CAMERA)
        self.assertEqual(restored.filmback_width, 36.0)

    def test_frame_data_json_roundtrip(self) -> None:
        frame = LiveLinkFrameData(
            subject_name="Camera_StageA",
            subject_type=LiveLinkSubjectType.CAMERA,
            frame_number=100,
            translation=(150.0, -250.0, 180.0),
            rotation=(0.0, 0.0, 0.0, 1.0),
            field_of_view=45.0,
            focal_length=35.0,
            aperture=1.8,
            focus_distance=850.0,
        )
        encoded = LiveLinkPacket.encode_json(frame)
        decoded = LiveLinkPacket.decode_json(encoded)
        self.assertIsInstance(decoded, LiveLinkFrameData)
        self.assertEqual(decoded.subject_name, "Camera_StageA")
        self.assertEqual(decoded.frame_number, 100)
        self.assertAlmostEqual(decoded.translation[0], 150.0)
        self.assertAlmostEqual(decoded.translation[1], -250.0)
        self.assertAlmostEqual(decoded.focal_length, 35.0)

    def test_frame_data_binary_roundtrip(self) -> None:
        frame = LiveLinkFrameData(
            subject_name="Hero_Character",
            subject_type=LiveLinkSubjectType.TRANSFORM,
            frame_number=42,
            translation=(50.5, 120.25, -30.75),
            rotation=(0.1, 0.2, 0.3, 0.9),
            scale=(1.0, 1.0, 1.0),
            field_of_view=60.0,
            focal_length=24.0,
            aperture=2.8,
            focus_distance=500.0,
        )
        bin_payload = LiveLinkPacket.encode_binary(frame)
        self.assertTrue(bin_payload.startswith(b"OLLK"))

        restored = LiveLinkPacket.decode_binary(bin_payload)
        self.assertEqual(restored.subject_name, "Hero_Character")
        self.assertEqual(restored.frame_number, 42)
        self.assertAlmostEqual(restored.translation[0], 50.5, places=2)
        self.assertAlmostEqual(restored.translation[1], 120.25, places=2)
        self.assertAlmostEqual(restored.translation[2], -30.75, places=2)

    def test_corrupt_packet_handling(self) -> None:
        with self.assertRaises(LiveLinkBridgeError):
            LiveLinkPacket.decode_json(b"not json")

        with self.assertRaises(LiveLinkBridgeError):
            LiveLinkPacket.decode_binary(b"FAIL_HEADER_DATA")


if __name__ == "__main__":
    unittest.main()

"""Unreal Engine 5 Live Link protocol definition, schemas, and coordinate conversion."""

from __future__ import annotations

import json
import math
import struct
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from openlore.exceptions import LiveLinkBridgeError

MAGIC_BINARY_HEADER = b"OLLK"
PROTOCOL_VERSION = 1


class LiveLinkSubjectType(str, Enum):
    """Supported Unreal Engine Live Link subject roles."""

    TRANSFORM = "Transform"
    CAMERA = "Camera"
    ANIMATION = "Animation"


class CoordinateConverter:
    """Coordinate space conversion between OpenUSD (Right-Handed) and Unreal Engine 5 (Left-Handed)."""

    @staticmethod
    def usd_to_unreal_position(
        pos_usd: Tuple[float, float, float],
        up_axis: str = "Z",
        meters_per_unit: float = 1.0,
    ) -> Tuple[float, float, float]:
        """Convert OpenUSD translation (meters) to Unreal Engine 5 translation (centimeters, Left-Handed)."""
        scale_to_cm = meters_per_unit * 100.0
        x, y, z = pos_usd
        if up_axis.upper() == "Y":
            # USD Y-Up: X-Right, Y-Up, Z-Out -> UE5 Z-Up: X-Forward, Y-Right, Z-Up
            return (z * scale_to_cm, x * scale_to_cm, y * scale_to_cm)
        # USD Z-Up (standard OpenLore stage): X-Forward, Y-Left, Z-Up
        # UE5 Z-Up: X-Forward, Y-Right, Z-Up
        return (x * scale_to_cm, -y * scale_to_cm, z * scale_to_cm)

    @staticmethod
    def unreal_to_usd_position(
        pos_ue: Tuple[float, float, float],
        up_axis: str = "Z",
        meters_per_unit: float = 1.0,
    ) -> Tuple[float, float, float]:
        """Convert Unreal Engine 5 translation (centimeters, Left-Handed) to OpenUSD translation (meters)."""
        scale_to_m = 1.0 / (meters_per_unit * 100.0)
        x, y, z = pos_ue
        if up_axis.upper() == "Y":
            return (y * scale_to_m, z * scale_to_m, x * scale_to_m)
        return (x * scale_to_m, -y * scale_to_m, z * scale_to_m)

    @staticmethod
    def usd_to_unreal_quaternion(
        quat_usd: Tuple[float, float, float, float],
        up_axis: str = "Z",
    ) -> Tuple[float, float, float, float]:
        """Convert OpenUSD right-handed quaternion (X, Y, Z, W) to Unreal Engine left-handed quaternion (X, Y, Z, W)."""
        x, y, z, w = quat_usd
        if up_axis.upper() == "Y":
            # Chirality swap for Y-up to Z-up
            return (z, x, y, -w)
        # Chirality flip across Y axis: invert Y and W
        return (x, -y, z, -w)

    @staticmethod
    def unreal_to_usd_quaternion(
        quat_ue: Tuple[float, float, float, float],
        up_axis: str = "Z",
    ) -> Tuple[float, float, float, float]:
        """Convert Unreal Engine left-handed quaternion (X, Y, Z, W) to OpenUSD right-handed quaternion (X, Y, Z, W)."""
        x, y, z, w = quat_ue
        if up_axis.upper() == "Y":
            return (y, z, x, -w)
        return (x, -y, z, -w)

    @staticmethod
    def euler_to_quaternion(roll_deg: float, pitch_deg: float, yaw_deg: float) -> Tuple[float, float, float, float]:
        """Convert Euler angles (degrees) to unit quaternion (X, Y, Z, W)."""
        roll = math.radians(roll_deg)
        pitch = math.radians(pitch_deg)
        yaw = math.radians(yaw_deg)

        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)

        w = cr * cp * cy + sr * sp * sy
        x = sr * cp * cy - cr * sp * sy
        y = cr * sp * cy + sr * cp * sy
        z = cr * cp * sy - sr * sp * cy

        norm = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
        return (x / norm, y / norm, z / norm, w / norm)

    @staticmethod
    def quaternion_to_euler(quat: Tuple[float, float, float, float]) -> Tuple[float, float, float]:
        """Convert quaternion (X, Y, Z, W) to Euler angles in degrees (Roll, Pitch, Yaw)."""
        x, y, z, w = quat

        # Roll (X-axis rotation)
        sinr_cosp = 2.0 * (w * x + y * z)
        cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        # Pitch (Y-axis rotation)
        sinp = 2.0 * (w * y - z * x)
        if abs(sinp) >= 1.0:
            pitch = math.copysign(math.pi / 2.0, sinp)
        else:
            pitch = math.asin(sinp)

        # Yaw (Z-axis rotation)
        siny_cosp = 2.0 * (w * z + x * y)
        cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        return (math.degrees(roll), math.degrees(pitch), math.degrees(yaw))


@dataclass
class LiveLinkStaticData:
    """Static schema definition for a Live Link subject in Unreal Engine."""

    subject_name: str
    subject_type: LiveLinkSubjectType = LiveLinkSubjectType.CAMERA
    property_names: List[str] = field(default_factory=list)
    bone_names: List[str] = field(default_factory=list)
    bone_parents: List[int] = field(default_factory=list)
    filmback_width: float = 36.0  # 35mm full-frame width in mm
    filmback_height: float = 24.0  # 35mm full-frame height in mm
    is_focal_length_supported: bool = True
    is_aperture_supported: bool = True
    is_focus_distance_supported: bool = True
    is_field_of_view_supported: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize static schema to JSON-compatible dictionary."""
        base: Dict[str, Any] = {
            "version": PROTOCOL_VERSION,
            "type": "StaticData",
            "subject_name": self.subject_name,
            "role": self.subject_type.value,
            "property_names": self.property_names,
        }
        if self.subject_type == LiveLinkSubjectType.CAMERA:
            base["camera_static_data"] = {
                "filmback_width": self.filmback_width,
                "filmback_height": self.filmback_height,
                "is_focal_length_supported": self.is_focal_length_supported,
                "is_aperture_supported": self.is_aperture_supported,
                "is_focus_distance_supported": self.is_focus_distance_supported,
                "is_field_of_view_supported": self.is_field_of_view_supported,
            }
        elif self.subject_type == LiveLinkSubjectType.ANIMATION:
            base["skeleton_static_data"] = {
                "bone_names": self.bone_names,
                "bone_parents": self.bone_parents,
            }
        return base

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LiveLinkStaticData:
        """Deserialize static schema from dictionary."""
        subject_type = LiveLinkSubjectType(data.get("role", LiveLinkSubjectType.TRANSFORM.value))
        cam_data = data.get("camera_static_data", {})
        skel_data = data.get("skeleton_static_data", {})
        return cls(
            subject_name=data["subject_name"],
            subject_type=subject_type,
            property_names=data.get("property_names", []),
            bone_names=skel_data.get("bone_names", []),
            bone_parents=skel_data.get("bone_parents", []),
            filmback_width=cam_data.get("filmback_width", 36.0),
            filmback_height=cam_data.get("filmback_height", 24.0),
            is_focal_length_supported=cam_data.get("is_focal_length_supported", True),
            is_aperture_supported=cam_data.get("is_aperture_supported", True),
            is_focus_distance_supported=cam_data.get("is_focus_distance_supported", True),
            is_field_of_view_supported=cam_data.get("is_field_of_view_supported", True),
        )


@dataclass
class LiveLinkFrameData:
    """Per-frame snapshot data broadcast to Unreal Engine Live Link."""

    subject_name: str
    subject_type: LiveLinkSubjectType = LiveLinkSubjectType.CAMERA
    timestamp: float = field(default_factory=time.time)
    frame_number: int = 0
    timecode: str = "00:00:00:00"
    translation: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # X, Y, Z in cm
    rotation: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)  # Quaternion (X, Y, Z, W)
    scale: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    field_of_view: float = 39.6  # degrees
    focal_length: float = 50.0  # mm
    aperture: float = 2.8  # f-stop
    focus_distance: float = 1000.0  # cm
    property_values: List[float] = field(default_factory=list)
    bone_transforms: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize frame snapshot to JSON-compatible dictionary."""
        euler = CoordinateConverter.quaternion_to_euler(self.rotation)
        base: Dict[str, Any] = {
            "version": PROTOCOL_VERSION,
            "type": "FrameData",
            "subject_name": self.subject_name,
            "role": self.subject_type.value,
            "timestamp": self.timestamp,
            "frame_number": self.frame_number,
            "timecode": self.timecode,
            "transform": {
                "translation": list(self.translation),
                "rotation": list(self.rotation),
                "rotation_euler": {
                    "roll": euler[0],
                    "pitch": euler[1],
                    "yaw": euler[2],
                },
                "scale": list(self.scale),
            },
            "property_values": self.property_values,
            "metadata": self.metadata,
        }
        if self.subject_type == LiveLinkSubjectType.CAMERA:
            base["camera_frame_data"] = {
                "field_of_view": self.field_of_view,
                "focal_length": self.focal_length,
                "aperture": self.aperture,
                "focus_distance": self.focus_distance,
            }
        elif self.subject_type == LiveLinkSubjectType.ANIMATION:
            base["skeleton_frame_data"] = {
                "bone_transforms": self.bone_transforms,
            }
        return base

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LiveLinkFrameData:
        """Deserialize frame snapshot from dictionary."""
        subject_type = LiveLinkSubjectType(data.get("role", LiveLinkSubjectType.TRANSFORM.value))
        tf = data.get("transform", {})
        cam = data.get("camera_frame_data", {})
        skel = data.get("skeleton_frame_data", {})

        trans = tuple(tf.get("translation", [0.0, 0.0, 0.0]))
        rot = tuple(tf.get("rotation", [0.0, 0.0, 0.0, 1.0]))
        scale = tuple(tf.get("scale", [1.0, 1.0, 1.0]))

        return cls(
            subject_name=data["subject_name"],
            subject_type=subject_type,
            timestamp=data.get("timestamp", time.time()),
            frame_number=data.get("frame_number", 0),
            timecode=data.get("timecode", "00:00:00:00"),
            translation=trans,  # type: ignore[arg-type]
            rotation=rot,  # type: ignore[arg-type]
            scale=scale,  # type: ignore[arg-type]
            field_of_view=cam.get("field_of_view", 39.6),
            focal_length=cam.get("focal_length", 50.0),
            aperture=cam.get("aperture", 2.8),
            focus_distance=cam.get("focus_distance", 1000.0),
            property_values=data.get("property_values", []),
            bone_transforms=skel.get("bone_transforms", []),
            metadata=data.get("metadata", {}),
        )


class LiveLinkPacket:
    """Packet serialization and deserialization for JSON and Binary UDP protocols."""

    @staticmethod
    def encode_json(data: Union[LiveLinkStaticData, LiveLinkFrameData]) -> bytes:
        """Serialize static or frame schema to UTF-8 encoded JSON bytes."""
        return json.dumps(data.to_dict()).encode("utf-8")

    @staticmethod
    def decode_json(payload: bytes) -> Union[LiveLinkStaticData, LiveLinkFrameData]:
        """Decode UTF-8 JSON packet into structured static or frame data."""
        try:
            parsed = json.loads(payload.decode("utf-8"))
            packet_type = parsed.get("type")
            if packet_type == "StaticData":
                return LiveLinkStaticData.from_dict(parsed)
            if packet_type == "FrameData":
                return LiveLinkFrameData.from_dict(parsed)
            raise LiveLinkBridgeError(f"Unknown Live Link packet type: '{packet_type}'")
        except Exception as exc:
            raise LiveLinkBridgeError(f"Malformed Live Link JSON packet: {exc}") from exc

    @staticmethod
    def encode_binary(frame: LiveLinkFrameData) -> bytes:
        """Serialize frame data into compact binary format.
        
        Header:
            4 bytes: 'OLLK' (Magic Header)
            1 byte:  Version (1)
            1 byte:  Subject Type (0=Transform, 1=Camera, 2=Animation)
            2 bytes: Subject name length (N)
            N bytes: Subject name ASCII
            8 bytes: Timestamp (double float64)
            4 bytes: Frame number (uint32)
            12 bytes: Translation (3 x float32)
            16 bytes: Rotation (4 x float32 Quaternion X, Y, Z, W)
            12 bytes: Scale (3 x float32)
            16 bytes: Camera parameters (4 x float32: FOV, FocalLength, Aperture, FocusDistance)
        """
        role_id = 0
        if frame.subject_type == LiveLinkSubjectType.CAMERA:
            role_id = 1
        elif frame.subject_type == LiveLinkSubjectType.ANIMATION:
            role_id = 2

        name_bytes = frame.subject_name.encode("utf-8")
        header = struct.pack("!4sBBH", MAGIC_BINARY_HEADER, PROTOCOL_VERSION, role_id, len(name_bytes))
        body = struct.pack(
            "!dI3f4f3f4f",
            frame.timestamp,
            frame.frame_number,
            frame.translation[0],
            frame.translation[1],
            frame.translation[2],
            frame.rotation[0],
            frame.rotation[1],
            frame.rotation[2],
            frame.rotation[3],
            frame.scale[0],
            frame.scale[1],
            frame.scale[2],
            frame.field_of_view,
            frame.focal_length,
            frame.aperture,
            frame.focus_distance,
        )
        return header + name_bytes + body

    @staticmethod
    def decode_binary(payload: bytes) -> LiveLinkFrameData:
        """Decode compact binary frame packet into LiveLinkFrameData."""
        if len(payload) < 8:
            raise LiveLinkBridgeError("Binary packet too short for header")

        magic, version, role_id, name_len = struct.unpack("!4sBBH", payload[:8])
        if magic != MAGIC_BINARY_HEADER:
            raise LiveLinkBridgeError(f"Invalid magic header: {magic!r}")

        body_fmt = "!dI3f4f3f4f"
        body_size = struct.calcsize(body_fmt)
        offset = 8 + name_len
        if len(payload) < offset + body_size:
            raise LiveLinkBridgeError("Binary packet payload truncated")

        subject_name = payload[8:offset].decode("utf-8")
        role = LiveLinkSubjectType.TRANSFORM
        if role_id == 1:
            role = LiveLinkSubjectType.CAMERA
        elif role_id == 2:
            role = LiveLinkSubjectType.ANIMATION

        (
            ts,
            frame_num,
            tx,
            ty,
            tz,
            rx,
            ry,
            rz,
            rw,
            sx,
            sy,
            sz,
            fov,
            focal_len,
            aperture,
            focus_dist,
        ) = struct.unpack(body_fmt, payload[offset : offset + body_size])

        return LiveLinkFrameData(
            subject_name=subject_name,
            subject_type=role,
            timestamp=ts,
            frame_number=frame_num,
            translation=(tx, ty, tz),
            rotation=(rx, ry, rz, rw),
            scale=(sx, sy, sz),
            field_of_view=fov,
            focal_length=focal_len,
            aperture=aperture,
            focus_distance=focus_dist,
        )

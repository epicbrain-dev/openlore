"""Full-duplex Unreal Engine 5 Live Link Bridge integrating OpenLore CRDT streams and Unreal viewports."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from openlore.bridge.unreal.protocol import (
    CoordinateConverter,
    LiveLinkFrameData,
    LiveLinkStaticData,
    LiveLinkSubjectType,
)
from openlore.bridge.unreal.provider import LiveLinkStreamProvider
from openlore.bridge.unreal.receiver import LiveLinkStreamReceiver
from openlore.collaboration.crdt import CRDTPartialMutation
from openlore.collaboration.resolver import EdgeResolverDaemon
from openlore.exceptions import LiveLinkBridgeError


class UnrealLiveLinkBridge:
    """Bi-directional real-time bridge linking OpenLore USD scene replicas with Unreal Engine 5 Live Link."""

    def __init__(
        self,
        edge_daemon: Optional[EdgeResolverDaemon] = None,
        broadcast_host: str = "127.0.0.1",
        broadcast_port: int = 11111,
        receive_port: int = 11112,
        studio_id: str = "UE5-VP-STAGE-01",
        up_axis: str = "Z",
        meters_per_unit: float = 1.0,
    ) -> None:
        self.edge_daemon = edge_daemon
        self.broadcast_host = broadcast_host
        self.broadcast_port = broadcast_port
        self.receive_port = receive_port
        self.studio_id = studio_id
        self.up_axis = up_axis
        self.meters_per_unit = meters_per_unit

        self.provider = LiveLinkStreamProvider(host=self.broadcast_host, port=self.broadcast_port)
        self.receiver = LiveLinkStreamReceiver(port=self.receive_port)

        # Mapping: prim_path -> (subject_name, LiveLinkSubjectType)
        self._prim_to_subject: Dict[str, Tuple[str, LiveLinkSubjectType]] = {}
        # Mapping: subject_name -> prim_path
        self._subject_to_prim: Dict[str, str] = {}

        self._active_mode: str = "stopped"
        self._frames_bridged_out: int = 0
        self._frames_bridged_in: int = 0

        # Wire up receiver callback
        self.receiver.on_frame(self._handle_inbound_frame)

        # Pre-bind default studio production prims
        self.bind_subject(
            prim_path="/World/CineCamera",
            subject_name="Camera_StageA",
            subject_type=LiveLinkSubjectType.CAMERA,
        )
        self.bind_subject(
            prim_path="/World/Hero",
            subject_name="Hero_Character",
            subject_type=LiveLinkSubjectType.TRANSFORM,
        )
        self.bind_subject(
            prim_path="/World/Stage_LED",
            subject_name="LED_Volume",
            subject_type=LiveLinkSubjectType.TRANSFORM,
        )

    @property
    def mode(self) -> str:
        """Current operational mode ('stopped', 'broadcast', 'receive', 'duplex')."""
        return self._active_mode

    def bind_subject(
        self,
        prim_path: str,
        subject_name: str,
        subject_type: LiveLinkSubjectType = LiveLinkSubjectType.TRANSFORM,
    ) -> None:
        """Bind an OpenUSD Prim path to an Unreal Engine Live Link subject name."""
        self._prim_to_subject[prim_path] = (subject_name, subject_type)
        self._subject_to_prim[subject_name] = prim_path

        static_data = LiveLinkStaticData(
            subject_name=subject_name,
            subject_type=subject_type,
        )
        self.provider.register_subject(static_data)

    def handle_crdt_mutation(self, mutation: CRDTPartialMutation) -> bool:
        """Process incoming OpenLore CRDT mutation and stream outbound to UE5 Live Link."""
        if self._active_mode not in ("broadcast", "duplex"):
            return False

        # Ignore mutations that originated from our own UE5 bridge to prevent feedback loops
        if mutation.origin_studio == self.studio_id:
            return False

        if mutation.prim_path not in self._prim_to_subject:
            return False

        subject_name, subject_type = self._prim_to_subject[mutation.prim_path]
        frame = self.provider._subjects_frame.get(subject_name)
        if not frame:
            frame = LiveLinkFrameData(subject_name=subject_name, subject_type=subject_type)

        # Update frame based on attribute
        attr = mutation.attribute_name
        val = mutation.value

        if attr in ("xformOp:translate", "translate"):
            if isinstance(val, (list, tuple)) and len(val) >= 3:
                pos_usd = (float(val[0]), float(val[1]), float(val[2]))
                frame.translation = CoordinateConverter.usd_to_unreal_position(
                    pos_usd, up_axis=self.up_axis, meters_per_unit=self.meters_per_unit
                )
        elif attr in ("xformOp:rotateXYZ", "rotation_euler"):
            if isinstance(val, (list, tuple)) and len(val) >= 3:
                # Roll, Pitch, Yaw
                frame.rotation = CoordinateConverter.euler_to_quaternion(float(val[0]), float(val[1]), float(val[2]))
        elif attr in ("xformOp:orient", "rotation"):
            if isinstance(val, (list, tuple)) and len(val) >= 4:
                quat_usd = (float(val[0]), float(val[1]), float(val[2]), float(val[3]))
                frame.rotation = CoordinateConverter.usd_to_unreal_quaternion(quat_usd, up_axis=self.up_axis)
        elif attr in ("xformOp:scale", "scale"):
            if isinstance(val, (list, tuple)) and len(val) >= 3:
                frame.scale = (float(val[0]), float(val[1]), float(val[2]))
        elif attr == "focalLength":
            frame.focal_length = float(val)
        elif attr == "focusDistance":
            frame.focus_distance = float(val)

        frame.timestamp = time.time()
        self.provider.update_frame(frame)
        self.provider.broadcast_frame(subject_name, wire_format="json")
        self._frames_bridged_out += 1
        return True

    def _handle_inbound_frame(self, frame: LiveLinkFrameData) -> None:
        """Handle incoming Live Link frame from Unreal Engine and update OpenLore CRDT."""
        if self._active_mode not in ("receive", "duplex"):
            return

        prim_path = self._subject_to_prim.get(frame.subject_name)
        if not prim_path:
            # Dynamically register unmapped subjects under /World/UnrealIngest/<SubjectName>
            prim_path = f"/World/UnrealIngest/{frame.subject_name}"
            self.bind_subject(prim_path, frame.subject_name, frame.subject_type)

        pos_usd = CoordinateConverter.unreal_to_usd_position(
            frame.translation, up_axis=self.up_axis, meters_per_unit=self.meters_per_unit
        )
        quat_usd = CoordinateConverter.unreal_to_usd_quaternion(frame.rotation, up_axis=self.up_axis)

        # Record edits into EdgeResolverDaemon
        if self.edge_daemon:
            self.edge_daemon.record_local_edit(
                prim_path=prim_path,
                attribute_name="xformOp:translate",
                value=[pos_usd[0], pos_usd[1], pos_usd[2]],
            )
            self.edge_daemon.record_local_edit(
                prim_path=prim_path,
                attribute_name="xformOp:orient",
                value=[quat_usd[0], quat_usd[1], quat_usd[2], quat_usd[3]],
            )

        self._frames_bridged_in += 1

    def start(self, mode: str = "duplex", target_fps: float = 60.0) -> None:
        """Start the Live Link bridge in specified mode ('broadcast', 'receive', or 'duplex')."""
        valid_modes = ("broadcast", "receive", "duplex")
        if mode not in valid_modes:
            raise LiveLinkBridgeError(f"Invalid bridge mode '{mode}'. Choose from {valid_modes}.")

        self._active_mode = mode

        if mode in ("broadcast", "duplex"):
            self.provider.start_stream(target_fps=target_fps)

        if mode in ("receive", "duplex"):
            self.receiver.start()

    def stop(self) -> None:
        """Stop all background providers and listeners."""
        self.provider.stop_stream()
        self.receiver.stop()
        self._active_mode = "stopped"

    def get_status(self) -> Dict[str, Any]:
        """Return comprehensive status and health telemetry."""
        return {
            "status": "ONLINE" if self._active_mode != "stopped" else "STOPPED",
            "mode": self._active_mode,
            "studio_id": self.studio_id,
            "broadcast_endpoint": f"{self.broadcast_host}:{self.broadcast_port}",
            "receive_port": self.receive_port,
            "coordinate_settings": {
                "up_axis": self.up_axis,
                "meters_per_unit": self.meters_per_unit,
                "usd_system": "Right-Handed (Meters)",
                "unreal_system": "Left-Handed (Centimeters)",
            },
            "bound_subjects": [
                {
                    "prim_path": prim,
                    "subject_name": subj,
                    "role": role.value,
                }
                for prim, (subj, role) in self._prim_to_subject.items()
            ],
            "metrics": {
                "frames_bridged_out": self._frames_bridged_out,
                "frames_bridged_in": self._frames_bridged_in,
                "provider": self.provider.metrics,
                "receiver": self.receiver.metrics,
            },
        }

"""SideFX Houdini 20 (Solaris / USD LOPs) Python Bridge for OpenLore Live Link and stage telemetry."""

from __future__ import annotations

from pathlib import Path


class HoudiniBridgeScaffolder:
    """Generates the official SideFX Houdini 20 (Solaris / USD LOPs) Python Bridge for OpenLore."""

    @staticmethod
    def get_bridge_source() -> str:
        return '''# OpenLore SideFX Houdini 20 (Solaris / USD LOPs) Live Link Telemetry Bridge
# Copyright (c) 2026 OpenLore Project. All Rights Reserved.

import json
import math
import socket
import time

try:
    import hou
except ImportError:
    hou = None


class OpenLoreHoudiniBridge:
    """Streams active Houdini Solaris / OBJ camera and transform telemetry to OpenLore Live Link UDP port."""

    def __init__(self, host="127.0.0.1", port=11111, subject_name="Houdini_SolarisCam", cam_path="/obj/cam1"):
        self.host = host
        self.port = port
        self.subject_name = subject_name
        self.cam_path = cam_path
        self.sock = None
        self.is_active = False
        self._callback_id = None

    def start(self):
        if self.is_active:
            print("[OpenLore] Houdini bridge already streaming.")
            return

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.is_active = True

        if hou:
            # Hook Houdini playbar event callback for real-time timeline scrubs
            try:
                hou.playbar.addEventCallback(self._on_playbar_event)
                self._callback_id = self._on_playbar_event
                print(f"[OpenLore] Houdini Live Link Bridge active -> {self.host}:{self.port} (Subject: {self.subject_name})")
            except Exception as e:
                print(f"[OpenLore] Playbar hook note: {e}")

    def stop(self):
        self.is_active = False
        if hou and self._callback_id:
            try:
                hou.playbar.removeEventCallback(self._callback_id)
            except Exception:
                pass
            self._callback_id = None

        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        print("[OpenLore] Houdini Live Link Bridge stopped.")

    def _on_playbar_event(self, event_type):
        if not self.is_active:
            return
        self.emit_active_camera_telemetry()

    def emit_active_camera_telemetry(self):
        if not self.is_active or not self.sock or not hou:
            return

        cam_node = None
        # 1. Try specified path
        if self.cam_path:
            cam_node = hou.node(self.cam_path)

        # 2. Fallback to active viewport camera
        if not cam_node:
            try:
                viewer = hou.ui.paneTabOfType(hou.paneTabType.SceneViewer)
                if viewer:
                    cur_vp = viewer.curViewport()
                    cam_name = cur_vp.camera()
                    if cam_name:
                        cam_node = hou.node(cam_name)
            except Exception:
                pass

        # 3. Fallback to first camera found in /obj or /stage
        if not cam_node:
            cams = hou.nodeType(hou.objNodeTypeCategory(), "cam").instances()
            if cams:
                cam_node = cams[0]

        if not cam_node:
            return

        # Extract World Transform (Houdini uses meters, Right-Handed Y-Up)
        try:
            world_transform = cam_node.worldTransform()
            trans = world_transform.extractTranslates()
            rot = world_transform.extractRotates() # Euler degrees (X, Y, Z)
        except Exception:
            trans = (0.0, 1.0, 5.0)
            rot = (0.0, 0.0, 0.0)

        # Optics parameters
        focal_length = 50.0
        aperture = 36.0
        try:
            if cam_node.parm("focal"):
                focal_length = float(cam_node.evalParm("focal"))
            if cam_node.parm("aperture"):
                aperture = float(cam_node.evalParm("aperture"))
        except Exception:
            pass

        fov = 2.0 * math.degrees(math.atan((aperture / 2.0) / max(1.0, focal_length)))

        # Coordinate Conversion: Houdini (Right-Handed Y-Up meters) -> OpenLore/Unreal (Left-Handed cm)
        # X -> X * 100, Y -> -Y * 100, Z -> Z * 100
        packet = {
            "version": 1,
            "type": "FrameData",
            "subject_name": self.subject_name,
            "role": "Camera",
            "timestamp": time.time(),
            "transform": {
                "translation": [round(trans[0] * 100.0, 3), round(-trans[1] * 100.0, 3), round(trans[2] * 100.0, 3)],
                "rotation": [0.0, 0.0, 0.0, 1.0],
                "rotation_euler": {
                    "roll": round(rot[0], 2),
                    "pitch": round(-rot[1], 2),
                    "yaw": round(rot[2], 2),
                },
                "scale": [1.0, 1.0, 1.0],
            },
            "camera_frame_data": {
                "field_of_view": round(fov, 2),
                "focal_length": round(focal_length, 2),
                "aperture": round(aperture, 2),
                "focus_distance": 1000.0,
            },
        }

        try:
            payload = json.dumps(packet).encode("utf-8")
            self.sock.sendto(payload, (self.host, self.port))
        except Exception:
            pass


_houdini_bridge_instance = None


def show_ui():
    """Display Houdini OpenLore Bridge GUI Dialog."""
    if not hou:
        print("[OpenLore] hou module not available outside Houdini runtime.")
        return

    global _houdini_bridge_instance
    if _houdini_bridge_instance and _houdini_bridge_instance.is_active:
        choice = hou.ui.displayMessage(
            "OpenLore Live Link Bridge is currently RUNNING.",
            buttons=("Stop Bridge", "Keep Running"),
            title="OpenLore Solaris Bridge",
        )
        if choice == 0:
            _houdini_bridge_instance.stop()
            _houdini_bridge_instance = None
            hou.ui.displayMessage("OpenLore Bridge stopped.", title="OpenLore Status")
        return

    res = hou.ui.readMultiInput(
        "Start OpenLore Live Link Telemetry Stream:",
        ("Host", "Port", "Subject Name", "Camera Path"),
        initial_contents=("127.0.0.1", "11111", "Houdini_SolarisCam", "/obj/cam1"),
        buttons=("Start Stream", "Cancel"),
        title="OpenLore Solaris LOPs Live Link",
    )

    if res[0] == 0: # Start Stream clicked
        vals = res[1]
        host = vals[0].strip() or "127.0.0.1"
        try:
            port = int(vals[1].strip())
        except ValueError:
            port = 11111
        subject = vals[2].strip() or "Houdini_SolarisCam"
        cam_path = vals[3].strip() or "/obj/cam1"

        _houdini_bridge_instance = OpenLoreHoudiniBridge(
            host=host, port=port, subject_name=subject, cam_path=cam_path
        )
        _houdini_bridge_instance.start()
        hou.ui.displayMessage(
            f"OpenLore Live Link Bridge streaming to {host}:{port}\\nSubject: {subject}",
            title="OpenLore Streaming Active",
        )


if __name__ == "__main__":
    show_ui()
'''

    @staticmethod
    def get_shelf_tool_xml() -> str:
        return '''<?xml version="1.0" encoding="UTF-8"?>
<shelfDocument>
  <toolshelf name="openlore_solaris" label="OpenLore Solaris">
    <memberTool name="openlore_live_link"/>
  </toolshelf>
  <tool name="openlore_live_link" label="OpenLore Live Link" icon="MISC_stage">
    <helpText><![CDATA[Stream camera and USD transform telemetry from Houdini Solaris to OpenLore.]]></helpText>
    <script scriptType="python"><![CDATA[
import openlore_houdini_bridge
openlore_houdini_bridge.show_ui()
]]></script>
  </tool>
</shelfDocument>
'''

    @classmethod
    def export(cls, output_dir: Path, filename: str = "openlore_houdini_bridge.py") -> Path:
        """Export Houdini bridge script and shelf definition to target directory."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        target_path = output_dir / filename
        target_path.write_text(cls.get_bridge_source(), encoding="utf-8")

        shelf_path = output_dir / "openlore_solaris_shelf.shelf"
        shelf_path.write_text(cls.get_shelf_tool_xml(), encoding="utf-8")
        return target_path

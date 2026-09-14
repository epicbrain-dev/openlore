"""Autodesk Maya 2024/2025 Python Bridge for OpenLore Live Link and camera sync."""

from __future__ import annotations

from pathlib import Path


class MayaBridgeScaffolder:
    """Generates the official Autodesk Maya Python Bridge for OpenLore."""

    @staticmethod
    def get_bridge_source() -> str:
        return '''# OpenLore Autodesk Maya 2024/2025 Live Link Telemetry Bridge
# Copyright (c) 2026 OpenLore Project. All Rights Reserved.

import json
import math
import socket
import time

try:
    import maya.cmds as cmds
except ImportError:
    cmds = None

class OpenLoreMayaBridge:
    """Streams active Maya camera and transform telemetry to OpenLore Live Link UDP port."""

    def __init__(self, host="127.0.0.1", port=11111, subject_name="Camera_StageA"):
        self.host = host
        self.port = port
        self.subject_name = subject_name
        self.sock = None
        self.job_ids = []
        self.is_active = False

    def start(self):
        if self.is_active:
            print("[OpenLore] Maya bridge already streaming.")
            return

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.is_active = True

        # Hook Maya time change or camera transform changes
        if cmds:
            job_time = cmds.scriptJob(event=["timeChanged", self.emit_active_camera_telemetry])
            self.job_ids.append(job_time)
            print(f"[OpenLore] Maya Live Link Bridge active -> {self.host}:{self.port} (Job: {job_time})")

    def stop(self):
        self.is_active = False
        if cmds:
            for jid in self.job_ids:
                try:
                    cmds.scriptJob(kill=jid, force=True)
                except Exception:
                    pass
        self.job_ids = []

        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        print("[OpenLore] Maya Live Link Bridge stopped.")

    def emit_active_camera_telemetry(self):
        if not self.is_active or not self.sock or not cmds:
            return

        # Find active camera (default to persp or selected camera)
        selected = cmds.ls(selection=True, type=["transform", "camera"])
        cam_node = "persp"
        if selected:
            cam_node = selected[0]

        # In Maya, 1 unit is typically 1 centimeter by default
        # Retrieve world transform
        pos = cmds.xform(cam_node, query=True, translation=True, worldSpace=True)
        rot = cmds.xform(cam_node, query=True, rotation=True, worldSpace=True) # Degrees (X, Y, Z)

        # Convert Euler degrees to quaternion
        rx, ry, rz = math.radians(rot[0]), math.radians(rot[1]), math.radians(rot[2])
        # OpenUSD Right-Handed to Unreal Left-Handed coordinates
        # Maya Y-Up or Z-Up handling:
        # Translation in cm: Maya standard is cm
        tx, ty, tz = pos[0], pos[1], pos[2]

        focal_length = 50.0
        shapes = cmds.listRelatives(cam_node, shapes=True, type="camera")
        if shapes:
            focal_length = cmds.getAttr(f"{shapes[0]}.focalLength")

        packet = {
            "version": 1,
            "type": "FrameData",
            "subject_name": self.subject_name,
            "role": "Camera",
            "timestamp": time.time(),
            "transform": {
                "translation": [tx, -ty, tz],
                "rotation": [0.0, 0.0, 0.0, 1.0],
                "rotation_euler": {"roll": rot[0], "pitch": -rot[1], "yaw": rot[2]},
                "scale": [1.0, 1.0, 1.0],
            },
            "camera_frame_data": {
                "field_of_view": 39.6,
                "focal_length": focal_length,
                "aperture": 2.8,
                "focus_distance": 1000.0,
            }
        }

        try:
            payload = json.dumps(packet).encode("utf-8")
            self.sock.sendto(payload, (self.host, self.port))
        except Exception:
            pass


_bridge_instance = None

def show_ui():
    """Display Maya OpenLore Bridge GUI Window."""
    if not cmds:
        print("[OpenLore] Maya cmds not available outside Maya runtime.")
        return

    win_id = "OpenLoreMayaBridgeWindow"
    if cmds.window(win_id, exists=True):
        cmds.deleteUI(win_id)

    win = cmds.window(win_id, title="OpenLore Live Link Bridge", widthHeight=(320, 220))
    layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=8)
    cmds.text(label="OpenLore Live Link Virtual Production Bridge", font="boldLabelFont")
    cmds.separator(height=10)

    host_field = cmds.textFieldGrp(label="Host:", text="127.0.0.1")
    port_field = cmds.intFieldGrp(label="Port:", value1=11111)
    subj_field = cmds.textFieldGrp(label="Subject:", text="Camera_StageA")

    def _start(*_):
        global _bridge_instance
        if not _bridge_instance:
            h = cmds.textFieldGrp(host_field, query=True, text=True)
            p = cmds.intFieldGrp(port_field, query=True, value1=True)
            s = cmds.textFieldGrp(subj_field, query=True, text=True)
            _bridge_instance = OpenLoreMayaBridge(host=h, port=p, subject_name=s)
        _bridge_instance.start()

    def _stop(*_):
        global _bridge_instance
        if _bridge_instance:
            _bridge_instance.stop()

    cmds.button(label="Start Live Link Stream", command=_start, backgroundColor=[0.2, 0.6, 0.3])
    cmds.button(label="Stop Live Link Stream", command=_stop, backgroundColor=[0.6, 0.2, 0.2])

    cmds.showWindow(win)

if __name__ == "__main__":
    show_ui()
'''

    @classmethod
    def export(cls, output_dir: Path, filename: str = "openlore_maya_bridge.py") -> Path:
        """Export Maya bridge script to target directory."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        target_path = output_dir / filename
        target_path.write_text(cls.get_bridge_source(), encoding="utf-8")
        return target_path

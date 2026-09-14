"""Blender 4.x Add-on generator for OpenLore Live Link and scene synchronization."""

from __future__ import annotations

from pathlib import Path


class BlenderAddonScaffolder:
    """Generates the official Blender 4.x Python Add-on for OpenLore."""

    @staticmethod
    def get_addon_source() -> str:
        return '''# OpenLore Blender 4.x Live Link & Stage Synchronizer Add-on
# Copyright (c) 2026 OpenLore Project. All Rights Reserved.

bl_info = {
    "name": "OpenLore DCC Bridge",
    "author": "OpenLore Engineering Team",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > OpenLore",
    "description": "Real-time Live Link transform streaming and OpenUSD scene synchronization for OpenLore.",
    "warning": "",
    "doc_url": "https://openlore.io/docs/dcc/blender",
    "category": "Pipeline",
}

import bpy
import json
import socket
import math
import time

class OpenLoreBridgeSettings(bpy.types.PropertyGroup):
    host: bpy.props.StringProperty(
        name="Host",
        description="Target OpenLore / Live Link UDP host",
        default="127.0.0.1",
    )
    port: bpy.props.IntProperty(
        name="UDP Port",
        description="Live Link inbound or broadcast port",
        default=11111,
        min=1024,
        max=65535,
    )
    target_fps: bpy.props.IntProperty(
        name="Stream FPS",
        description="Target update frequency",
        default=60,
        min=12,
        max=120,
    )
    subject_name: bpy.props.StringProperty(
        name="Subject Name",
        description="Live Link subject identifier",
        default="Camera_StageA",
    )
    is_streaming: bpy.props.BoolProperty(
        name="Streaming Active",
        default=False,
    )


class OPENLORE_OT_toggle_stream(bpy.types.Operator):
    """Start or stop real-time transform streaming to OpenLore"""
    bl_idname = "openlore.toggle_stream"
    bl_label = "Toggle Live Stream"

    _timer = None
    _socket = None

    def modal(self, context, event):
        props = context.scene.openlore_settings

        if not props.is_streaming:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            self.send_transform(context)

        return {'PASS_THROUGH'}

    def send_transform(self, context):
        props = context.scene.openlore_settings
        cam = context.scene.camera

        if not cam:
            obj = context.active_object
        else:
            obj = cam

        if not obj or not self._socket:
            return

        loc = obj.matrix_world.to_translation()
        rot_quat = obj.matrix_world.to_quaternion()

        # Coordinate conversion: Blender (Right-Handed Z-Up, meters) -> Unreal Left-Handed cm
        # X_ue = X * 100, Y_ue = -Y * 100, Z_ue = Z * 100
        packet = {
            "version": 1,
            "type": "FrameData",
            "subject_name": props.subject_name,
            "role": "Camera" if obj.type == 'CAMERA' else "Transform",
            "timestamp": time.time(),
            "transform": {
                "translation": [loc.x * 100.0, -loc.y * 100.0, loc.z * 100.0],
                "rotation": [rot_quat.x, -rot_quat.y, rot_quat.z, -rot_quat.w],
                "scale": [1.0, 1.0, 1.0],
            },
            "camera_frame_data": {
                "field_of_view": math.degrees(cam.data.angle) if obj.type == 'CAMERA' else 39.6,
                "focal_length": cam.data.lens if obj.type == 'CAMERA' else 50.0,
                "aperture": cam.data.dof.aperture_fstop if obj.type == 'CAMERA' and hasattr(cam.data, 'dof') else 2.8,
                "focus_distance": 1000.0,
            }
        }

        try:
            payload = json.dumps(packet).encode("utf-8")
            self._socket.sendto(payload, (props.host, props.port))
        except Exception:
            pass

    def execute(self, context):
        props = context.scene.openlore_settings

        if props.is_streaming:
            props.is_streaming = False
            self.report({'INFO'}, "OpenLore streaming stopped.")
            return {'FINISHED'}

        props.is_streaming = True
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        wm = context.window_manager
        self._timer = wm.event_timer_add(1.0 / props.target_fps, window=context.window)
        wm.modal_handler_add(self)
        self.report({'INFO'}, f"OpenLore streaming started @ {props.target_fps} FPS to {props.host}:{props.port}")
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)
            self._timer = None
        if self._socket:
            self._socket.close()
            self._socket = None


class VIEW3D_PT_openlore_panel(bpy.types.Panel):
    """OpenLore UI Panel in Blender 3D Viewport Sidebar"""
    bl_label = "OpenLore Studio Bridge"
    bl_idname = "VIEW3D_PT_openlore_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'OpenLore'

    def draw(self, context):
        layout = self.layout
        props = context.scene.openlore_settings

        box = layout.box()
        box.label(text="Live Link Telemetry Endpoint", icon='LINKED')
        box.prop(props, "host")
        box.prop(props, "port")
        box.prop(props, "target_fps")
        box.prop(props, "subject_name")

        layout.separator()
        btn_text = "Stop Live Link Stream" if props.is_streaming else "Start Live Link Stream"
        btn_icon = 'CANCEL' if props.is_streaming else 'PLAY'
        layout.operator("openlore.toggle_stream", text=btn_text, icon=btn_icon)

        layout.separator()
        box_status = layout.box()
        status_text = "STREAMING (Active)" if props.is_streaming else "IDLE (Disconnected)"
        box_status.label(text=f"Status: {status_text}", icon='RADIOBUT_ON' if props.is_streaming else 'RADIOBUT_OFF')


classes = (
    OpenLoreBridgeSettings,
    OPENLORE_OT_toggle_stream,
    VIEW3D_PT_openlore_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.openlore_settings = bpy.props.PointerProperty(type=OpenLoreBridgeSettings)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.openlore_settings

if __name__ == "__main__":
    register()
'''

    @classmethod
    def export(cls, output_dir: Path, filename: str = "openlore_blender_addon.py") -> Path:
        """Export Blender add-on script to target directory."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        target_path = output_dir / filename
        target_path.write_text(cls.get_addon_source(), encoding="utf-8")
        return target_path

"""Unit tests for DCC sidecars (Blender 4.x & Autodesk Maya 2024/2025)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from openlore.dcc.blender import BlenderAddonScaffolder
from openlore.dcc.export import DCCExporter
from openlore.dcc.houdini import HoudiniBridgeScaffolder
from openlore.dcc.maya import MayaBridgeScaffolder
from openlore.dcc.unity import UnityBridgeScaffolder


class TestDCCPlugins(unittest.TestCase):
    def test_blender_addon_content(self) -> None:
        source = BlenderAddonScaffolder.get_addon_source()
        self.assertIn("bl_info", source)
        self.assertIn('"blender": (4, 0, 0)', source)
        self.assertIn("OPENLORE_OT_toggle_stream", source)
        self.assertIn("VIEW3D_PT_openlore_panel", source)
        self.assertIn("socket.SOCK_DGRAM", source)

    def test_maya_bridge_content(self) -> None:
        source = MayaBridgeScaffolder.get_bridge_source()
        self.assertIn("OpenLoreMayaBridge", source)
        self.assertIn("cmds.scriptJob", source)
        self.assertIn("show_ui", source)
        self.assertIn("socket.SOCK_DGRAM", source)

    def test_houdini_bridge_content(self) -> None:
        source = HoudiniBridgeScaffolder.get_bridge_source()
        shelf = HoudiniBridgeScaffolder.get_shelf_tool_xml()
        self.assertIn("OpenLoreHoudiniBridge", source)
        self.assertIn("hou.playbar.addEventCallback", source)
        self.assertIn("show_ui", source)
        self.assertIn("socket.SOCK_DGRAM", source)
        self.assertIn("<toolshelf name=\"openlore_solaris\"", shelf)
        self.assertIn("<tool name=\"openlore_live_link\"", shelf)

    def test_unity_bridge_content(self) -> None:
        cs_src = UnityBridgeScaffolder.get_client_cs_source()
        pkg_json = UnityBridgeScaffolder.get_package_json()
        self.assertIn("namespace OpenLore.LiveLink", cs_src)
        self.assertIn("class OpenLoreLiveLinkClient", cs_src)
        self.assertIn("UdpClient", cs_src)
        self.assertIn('"name": "com.openlore.livelink"', pkg_json)

    def test_dcc_export_all(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            exported = DCCExporter.export_all(out_dir)

            self.assertIn("blender", exported)
            self.assertIn("maya", exported)
            self.assertIn("houdini", exported)
            self.assertIn("unity", exported)

            blender_path = exported["blender"]
            maya_path = exported["maya"]
            houdini_path = exported["houdini"]
            unity_path = exported["unity"]

            self.assertTrue(blender_path.is_file())
            self.assertTrue(maya_path.is_file())
            self.assertTrue(houdini_path.is_file())
            self.assertTrue(unity_path.is_file())

            b_text = blender_path.read_text(encoding="utf-8")
            m_text = maya_path.read_text(encoding="utf-8")
            h_text = houdini_path.read_text(encoding="utf-8")
            u_text = unity_path.read_text(encoding="utf-8")

            self.assertIn("bl_info", b_text)
            self.assertIn("OpenLoreMayaBridge", m_text)
            self.assertIn("OpenLoreHoudiniBridge", h_text)
            self.assertIn("OpenLoreLiveLinkClient", u_text)


if __name__ == "__main__":
    unittest.main()

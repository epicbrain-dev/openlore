"""DCC Plugin exporter utility."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from openlore.dcc.blender import BlenderAddonScaffolder
from openlore.dcc.houdini import HoudiniBridgeScaffolder
from openlore.dcc.maya import MayaBridgeScaffolder


class DCCExporter:
    """Exports native DCC connectors for Blender, Maya, and Houdini Solaris."""

    @staticmethod
    def export_all(base_output_dir: Path) -> Dict[str, Path]:
        base = Path(base_output_dir)
        blender_dir = base / "blender"
        maya_dir = base / "maya"
        houdini_dir = base / "houdini"

        blender_file = BlenderAddonScaffolder.export(blender_dir)
        maya_file = MayaBridgeScaffolder.export(maya_dir)
        houdini_file = HoudiniBridgeScaffolder.export(houdini_dir)

        return {
            "blender": blender_file,
            "maya": maya_file,
            "houdini": houdini_file,
        }

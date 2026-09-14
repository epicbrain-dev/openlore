"""DCC Plugin exporter utility."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from openlore.dcc.blender import BlenderAddonScaffolder
from openlore.dcc.maya import MayaBridgeScaffolder


class DCCExporter:
    """Exports native DCC connectors for Blender and Maya."""

    @staticmethod
    def export_all(base_output_dir: Path) -> Dict[str, Path]:
        base = Path(base_output_dir)
        blender_dir = base / "blender"
        maya_dir = base / "maya"

        blender_file = BlenderAddonScaffolder.export(blender_dir)
        maya_file = MayaBridgeScaffolder.export(maya_dir)

        return {
            "blender": blender_file,
            "maya": maya_file,
        }

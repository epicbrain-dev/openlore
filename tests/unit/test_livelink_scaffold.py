"""Unit tests for Unreal Engine 5 plugin scaffolding."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from openlore.bridge.unreal.plugin_scaffold import UnrealPluginScaffolder


class TestUnrealPluginScaffolder(unittest.TestCase):
    def test_plugin_generation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "MyCustomLiveLink"
            files = UnrealPluginScaffolder.generate_plugin(out_path, plugin_name="MyCustomLiveLink")

            self.assertIn("uplugin", files)
            self.assertIn("build_cs", files)
            self.assertIn("source_h", files)
            self.assertIn("source_cpp", files)
            self.assertIn("py_script", files)
            self.assertIn("readme", files)

            # Check .uplugin file
            uplugin_text = files["uplugin"].read_text(encoding="utf-8")
            self.assertIn('"FriendlyName": "OpenLore Live Link"', uplugin_text)
            self.assertIn('"Name": "MyCustomLiveLink"', uplugin_text)
            self.assertIn('"Name": "LiveLink"', uplugin_text)

            # Check C++ source
            cpp_text = files["source_cpp"].read_text(encoding="utf-8")
            self.assertIn("FOpenLoreLiveLinkSource", cpp_text)
            self.assertIn("PushSubjectFrameData_AnyThread", cpp_text)

            # Check Build.cs
            build_cs_text = files["build_cs"].read_text(encoding="utf-8")
            self.assertIn("LiveLinkInterface", build_cs_text)


if __name__ == "__main__":
    unittest.main()

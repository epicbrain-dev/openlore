"""Unit tests for the OpenLore command-line interface (CLI)."""

from __future__ import annotations

import io
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from openlore.cli.main import main


class TestOpenLoreCLI(unittest.TestCase):
    """Verifies that all OpenLore CLI subcommands execute cleanly."""

    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="openlore_cli_test_"))
        self.cas_dir = self.temp_dir / "cas"
        self.test_graph_file = self.temp_dir / "graph.trig"
        source_graph = Path("./data/lore/graph.trig")
        if source_graph.is_file():
            shutil.copyfile(source_graph, self.test_graph_file)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        # Clean up any test stages created during testing
        for p in Path("./stages").glob("test_cli_*.usd*"):
            try:
                p.unlink()
            except Exception:
                pass

    def _run_cli(self, args: list[str]) -> tuple[int, str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            exit_code = main(args)
        return exit_code, buf.getvalue()

    def test_cli_help(self) -> None:
        exit_code, out = self._run_cli([])
        self.assertEqual(exit_code, 0)
        self.assertIn("OpenLore: Git for 3D worlds", out)

    def test_cli_auth_token_minting(self) -> None:
        exit_code, out = self._run_cli(["auth", "--sub", "lead_td", "--role", "td", "--days", "7"])
        self.assertEqual(exit_code, 0)
        self.assertIn("Generated Bearer Token for 'lead_td'", out)
        self.assertIn("Authorization: Bearer", out)

    def test_cli_stage_create_and_list(self) -> None:
        stage_uri = "openlore://stages/test_cli_hero.usda"
        exit_code, out = self._run_cli(["stage", "create", "--uri", stage_uri, "--format", "usda"])
        self.assertEqual(exit_code, 0)
        self.assertIn("Created OpenUSD stage", out)

        exit_code, list_out = self._run_cli(["stage", "list"])
        self.assertEqual(exit_code, 0)
        self.assertIn("test_cli_hero.usda", list_out)

    def test_cli_stage_inspect(self) -> None:
        stage_uri = "openlore://stages/test_cli_inspect.usda"
        self._run_cli(["stage", "create", "--uri", stage_uri])
        exit_code, out = self._run_cli(["stage", "inspect", "--uri", stage_uri])
        self.assertEqual(exit_code, 0)
        self.assertIn("Stage: openlore://stages/test_cli_inspect.usda", out)

    def test_cli_lore_commands(self) -> None:
        graph_arg = str(self.test_graph_file)

        # 1. lore list
        exit_code, list_out = self._run_cli(["lore", "list", "--graph-path", graph_arg])
        self.assertEqual(exit_code, 0)
        self.assertIn("Active Timelines", list_out)

        # 2. lore branch
        exit_code, branch_out = self._run_cli([
            "lore", "branch",
            "--graph-path", graph_arg,
            "--timeline", "https://openlore.io/timelines/prime-canon",
            "--new-slug", "cli_alt_universe",
            "--new-name", "CLI Alternate Universe",
        ])
        self.assertEqual(exit_code, 0)
        self.assertIn("Successfully branched timeline", branch_out)

        # 3. lore verify
        exit_code, verify_out = self._run_cli(["lore", "verify", "--graph-path", graph_arg])
        self.assertEqual(exit_code, 0)
        self.assertIn("SHACL & Lifecycle validation PASSED", verify_out)

    def test_cli_catalog_and_daemon(self) -> None:
        exit_code, cat_out = self._run_cli(["catalog", "list"])
        self.assertEqual(exit_code, 0)
        self.assertIn("OpenLore Production Catalog", cat_out)

        exit_code, daemon_out = self._run_cli(["daemon", "status"])
        self.assertEqual(exit_code, 0)
        self.assertIn("Edge Resolver Daemon:", daemon_out)

    def test_cli_dcc_export(self) -> None:
        out_path = self.temp_dir / "dcc_out"
        exit_code, out = self._run_cli(["dcc", "blender", "--output-dir", str(out_path)])
        self.assertEqual(exit_code, 0)
        self.assertIn("Exported Blender", out)
        self.assertTrue((out_path / "blender" / "openlore_blender_addon.py").is_file())

    def test_cli_livelink_export_plugin(self) -> None:
        plugin_path = self.temp_dir / "ue5_plugin"
        exit_code, out = self._run_cli(["livelink", "export-plugin", "--output-dir", str(plugin_path), "--name", "TestPlugin"])
        self.assertEqual(exit_code, 0)
        self.assertIn("Generated UE5 C++ Plugin", out)
        self.assertTrue((plugin_path / "TestPlugin.uplugin").is_file())

    def test_cli_partner_lint(self) -> None:
        # Create dummy USDA deliverable
        dummy_file = self.temp_dir / "partner_test.usda"
        dummy_file.write_text('#usda 1.0\ndef Xform "World" {}\n', encoding="utf-8")
        exit_code, out = self._run_cli(["partner", "lint", "--deliverable", str(dummy_file)])
        self.assertEqual(exit_code, 0)
        self.assertIn("OpenLore Quarantine Linting", out)


    def test_cli_doctor(self) -> None:
        exit_code, out = self._run_cli(["doctor"])
        self.assertEqual(exit_code, 0)
        self.assertIn("OpenLore System Health & Environment Doctor", out)
        self.assertIn("Operating System:", out)


if __name__ == "__main__":
    unittest.main()


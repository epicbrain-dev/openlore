"""Unit tests for Distributed GPU Render Farm Dispatcher (AWS Deadline & ASWF OpenCue)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from openlore.cli.main import main as cli_main
from openlore.compilation.farm import (
    FarmJobConfig,
    FarmScheduler,
    RenderEngine,
    RenderFarmDispatcher,
)
from openlore.compilation.grid import WorkerGridDispatcher


class TestRenderFarmDispatcher(unittest.TestCase):
    """Test suite validating render farm job generation, scheduling specs, and CLI dispatch."""

    def setUp(self) -> None:
        self.config = FarmJobConfig(
            job_name="shot_01_hero_comp",
            stage_uri="openlore://stages/root.usda",
            renderer=RenderEngine.KARMA,
            start_frame=101,
            end_frame=150,
            chunk_size=5,
            output_dir="./renders/shot_01",
            camera="/World/Cameras/HeroCamera",
            resolution=(3840, 2160),
            priority=80,
            gpu_required=True,
            memory_mb=32768,
        )

    def test_renderer_command_generation(self) -> None:
        # 1. Karma
        self.config.renderer = RenderEngine.KARMA
        karma_cmd = RenderFarmDispatcher.get_renderer_command(self.config)
        self.assertIn("husk", karma_cmd)
        self.assertIn("--delegate BRAY_HdKarmaXPU", karma_cmd)
        self.assertIn("--res 3840 2160", karma_cmd)

        # 2. Arnold
        self.config.renderer = RenderEngine.ARNOLD
        arnold_cmd = RenderFarmDispatcher.get_renderer_command(self.config)
        self.assertIn("kick", arnold_cmd)
        self.assertIn("-res 3840 2160", arnold_cmd)

        # 3. RenderMan
        self.config.renderer = RenderEngine.RENDERMAN
        prman_cmd = RenderFarmDispatcher.get_renderer_command(self.config)
        self.assertIn("prman", prman_cmd)
        self.assertIn("-camera /World/Cameras/HeroCamera", prman_cmd)

        # 4. usdrecord fallback
        self.config.renderer = RenderEngine.USD_RECORD
        rec_cmd = RenderFarmDispatcher.get_renderer_command(self.config)
        self.assertIn("usdrecord", rec_cmd)

    def test_deadline_bundle_generation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "deadline_job"
            bundle = RenderFarmDispatcher.generate_deadline_bundle(self.config, bundle_dir)

            self.assertTrue(bundle["job_info"].exists())
            self.assertTrue(bundle["plugin_info"].exists())

            job_info = bundle["job_info"].read_text(encoding="utf-8")
            self.assertIn("Plugin=CommandLine", job_info)
            self.assertIn("Name=shot_01_hero_comp", job_info)
            self.assertIn("Frames=101-150", job_info)
            self.assertIn("ChunkSize=5", job_info)
            self.assertIn("Priority=80", job_info)
            self.assertIn("OutputDirectory0=./renders/shot_01", job_info)

            plugin_info = bundle["plugin_info"].read_text(encoding="utf-8")
            self.assertIn("Executable=husk", plugin_info)
            self.assertIn("--delegate BRAY_HdKarmaXPU", plugin_info)

    def test_opencue_outline_generation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            outline_path = Path(temp_dir) / "opencue.xml"
            xml_text = RenderFarmDispatcher.generate_opencue_outline(self.config, outline_path)

            self.assertTrue(outline_path.exists())
            self.assertIn('job name="shot_01_hero_comp"', xml_text)
            self.assertIn("<range>101-150</range>", xml_text)
            self.assertIn("<chunk>5</chunk>", xml_text)
            self.assertIn("<memory>32768MB</memory>", xml_text)
            self.assertIn("<gpu>1</gpu>", xml_text)
            self.assertIn("husk", xml_text)

    def test_submit_job_dry_run(self) -> None:
        deadline_res = RenderFarmDispatcher.submit_job(
            self.config, scheduler=FarmScheduler.DEADLINE, dry_run=True
        )
        self.assertEqual(deadline_res["status"], "SUBMITTED")
        self.assertEqual(deadline_res["scheduler"], "deadline")
        self.assertTrue(deadline_res["dry_run"])
        self.assertIn("deadlinecommand", deadline_res["command"])

        opencue_res = RenderFarmDispatcher.submit_job(
            self.config, scheduler=FarmScheduler.OPENCUE, dry_run=True
        )
        self.assertEqual(opencue_res["status"], "SUBMITTED")
        self.assertEqual(opencue_res["scheduler"], "opencue")
        self.assertTrue(opencue_res["dry_run"])
        self.assertIn("cueadmin", opencue_res["command"])

    def test_worker_grid_dispatcher_farm_integration(self) -> None:
        dispatcher = WorkerGridDispatcher()
        with tempfile.TemporaryDirectory() as temp_dir:
            wf_id = dispatcher.dispatch_compilation_workflow(
                stage_uri="openlore://stages/root.usda",
                target_engines=["deadline", "opencue"],
                output_dir=Path(temp_dir),
                shot_name="shot_02",
            )
            status = dispatcher.get_job_status(wf_id)
            self.assertEqual(status["status"], "COMPLETED")
            self.assertIn("dispatch_farm_deadline", status["activities"])
            self.assertIn("dispatch_farm_opencue", status["activities"])
            self.assertIn("farm_deadline", status["artifacts"])
            self.assertIn("farm_opencue", status["artifacts"])

    def test_cli_farm_submission(self) -> None:
        exit_code = cli_main([
            "farm",
            "submit",
            "--stage", "openlore://stages/test_farm.usda",
            "--scheduler", "deadline",
            "--renderer", "karma",
            "--start-frame", "1",
            "--end-frame", "12",
            "--chunk-size", "4",
            "--job-name", "cli_test_job",
        ])
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()

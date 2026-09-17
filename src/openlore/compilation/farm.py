"""Distributed GPU Render Farm Dispatcher for AWS Deadline and ASWF OpenCue."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from openlore.exceptions import CompilationError


class FarmScheduler(str, Enum):
    """Supported render farm scheduling orchestrators."""

    DEADLINE = "deadline"
    OPENCUE = "opencue"


class RenderEngine(str, Enum):
    """Supported offline cinematic rendering backends."""

    KARMA = "karma"
    ARNOLD = "arnold"
    RENDERMAN = "renderman"
    USD_RECORD = "usdrecord"


@dataclass
class FarmJobConfig:
    """Render job configuration parameters."""

    job_name: str
    stage_uri: str
    renderer: RenderEngine = RenderEngine.KARMA
    start_frame: int = 1
    end_frame: int = 24
    chunk_size: int = 5
    output_dir: str = "./renders"
    camera: str = "/World/Camera"
    resolution: tuple[int, int] = (1920, 1080)
    priority: int = 50
    gpu_required: bool = True
    memory_mb: int = 16384
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_name": self.job_name,
            "stage_uri": self.stage_uri,
            "renderer": self.renderer.value,
            "start_frame": self.start_frame,
            "end_frame": self.end_frame,
            "chunk_size": self.chunk_size,
            "output_dir": self.output_dir,
            "camera": self.camera,
            "resolution": list(self.resolution),
            "priority": self.priority,
            "gpu_required": self.gpu_required,
            "memory_mb": self.memory_mb,
            "tags": self.tags,
        }


class RenderFarmDispatcher:
    """Dispatches OpenUSD stage rendering workflows to enterprise GPU farm schedulers."""

    @staticmethod
    def get_renderer_command(config: FarmJobConfig, frame_placeholder: str = "<FRAME>") -> str:
        """Construct the CLI invocation string for the requested render engine."""
        width, height = config.resolution
        out_pattern = f"{config.output_dir}/{config.job_name}.{frame_placeholder}.exr"

        if config.renderer == RenderEngine.KARMA:
            # SideFX Husk Karma Hydra Render Delegate
            return (
                f"husk --usd-input {config.stage_uri} --output {out_pattern} "
                f"--frame {frame_placeholder} --camera {config.camera} "
                f"--res {width} {height} --delegate BRAY_HdKarmaXPU"
            )
        elif config.renderer == RenderEngine.ARNOLD:
            # Autodesk Arnold Kick USD Driver
            return (
                f"kick -i {config.stage_uri} -o {out_pattern} "
                f"-frame {frame_placeholder} -cam {config.camera} "
                f"-res {width} {height} -dw -v 2"
            )
        elif config.renderer == RenderEngine.RENDERMAN:
            # Pixar RenderMan prman
            return (
                f"prman -usd {config.stage_uri} -o {out_pattern} "
                f"-frame {frame_placeholder} -camera {config.camera} "
                f"-res {width} {height}"
            )
        else:
            # Fallback Pixar usdrecord
            return (
                f"usdrecord --camera {config.camera} --frames {frame_placeholder}:{frame_placeholder} "
                f"--imageWidth {width} {config.stage_uri} {out_pattern}"
            )

    @classmethod
    def generate_deadline_bundle(cls, config: FarmJobConfig, bundle_dir: Path) -> Dict[str, Path]:
        """Generate AWS Deadline Job Info and Plugin Info specification files."""
        bundle_dir.mkdir(parents=True, exist_ok=True)
        job_info_path = bundle_dir / "job_info.job"
        plugin_info_path = bundle_dir / "plugin_info.job"

        job_info_lines = [
            f"Plugin=CommandLine",
            f"Name={config.job_name}",
            f"Comment=OpenLore Automated USD Render Job",
            f"Department=Lighting",
            f"Frames={config.start_frame}-{config.end_frame}",
            f"ChunkSize={config.chunk_size}",
            f"Priority={config.priority}",
            f"OutputDirectory0={config.output_dir}",
            f"InitialStatus=Active",
        ]
        if config.gpu_required:
            job_info_lines.append("IsInterruptible=True")
            job_info_lines.append("ConcurrentTasks=1")

        cmd = cls.get_renderer_command(config, frame_placeholder="<STARTFRAME>")
        cmd_parts = cmd.split(" ", 1)
        executable = cmd_parts[0]
        arguments = cmd_parts[1] if len(cmd_parts) > 1 else ""

        plugin_info_lines = [
            f"Executable={executable}",
            f"Arguments={arguments}",
            f"ShellExecute=False",
            f"SingleFramesOnly=False",
        ]

        job_info_path.write_text("\n".join(job_info_lines) + "\n", encoding="utf-8")
        plugin_info_path.write_text("\n".join(plugin_info_lines) + "\n", encoding="utf-8")

        return {
            "job_info": job_info_path,
            "plugin_info": plugin_info_path,
        }

    @classmethod
    def generate_opencue_outline(cls, config: FarmJobConfig, output_path: Path) -> str:
        """Generate Academy Software Foundation (ASWF) OpenCue job outline XML."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = cls.get_renderer_command(config, frame_placeholder="#FRAME#")

        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<!DOCTYPE spec SYSTEM "outline.dtd">',
            f'<spec>',
            f'  <job name="{config.job_name}">',
            f'    <env>',
            f'      <key name="OPENLORE_RENDER_NODE">1</key>',
            f'    </env>',
            f'    <layer name="render_layer" type="Render">',
            f'      <cmd>{cmd}</cmd>',
            f'      <range>{config.start_frame}-{config.end_frame}</range>',
            f'      <chunk>{config.chunk_size}</chunk>',
            f'      <cores>4.0</cores>',
            f'      <memory>{config.memory_mb}MB</memory>',
        ]
        if config.gpu_required:
            xml_lines.append(f'      <gpu>1</gpu>')

        xml_lines.extend([
            f'    </layer>',
            f'  </job>',
            f'</spec>',
        ])

        xml_content = "\n".join(xml_lines) + "\n"
        output_path.write_text(xml_content, encoding="utf-8")
        return xml_content

    @classmethod
    def submit_job(
        cls,
        config: FarmJobConfig,
        scheduler: FarmScheduler = FarmScheduler.DEADLINE,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """Submit job to the target render farm scheduler (or simulate dry-run)."""
        job_id = f"{scheduler.value}-{config.job_name}-{uuid.uuid4().hex[:8]}"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            if scheduler == FarmScheduler.DEADLINE:
                bundle = cls.generate_deadline_bundle(config, temp_path)
                cmd = ["deadlinecommand", str(bundle["job_info"]), str(bundle["plugin_info"])]
            else:
                outline_path = temp_path / "opencue_outline.xml"
                cls.generate_opencue_outline(config, outline_path)
                cmd = ["cueadmin", "-create", str(outline_path)]

            if dry_run or not shutil.which(cmd[0]):
                return {
                    "status": "SUBMITTED",
                    "job_id": job_id,
                    "scheduler": scheduler.value,
                    "renderer": config.renderer.value,
                    "dry_run": True,
                    "command": " ".join(cmd),
                    "frames": f"{config.start_frame}-{config.end_frame}",
                    "chunk_size": config.chunk_size,
                    "output_dir": config.output_dir,
                }

            try:
                proc = subprocess.run(cmd, capture_stdout=True, text=True, check=True)
                return {
                    "status": "SUBMITTED",
                    "job_id": job_id,
                    "scheduler": scheduler.value,
                    "dry_run": False,
                    "output": proc.stdout,
                }
            except subprocess.CalledProcessError as exc:
                raise CompilationError(f"Failed to submit job to {scheduler.value}: {exc.stderr}") from exc

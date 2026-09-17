"""Offline cinematic point cache and render package baker."""

from __future__ import annotations

import json
import math
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import blake3

try:
    from pxr import Gf, Sdf, Usd, UsdGeom
    HAS_PXR = True
except ImportError:
    HAS_PXR = False


class OfflineShotBaker:
    """Bakes offline shot point caches (.usdc / .usda geometry caches with time-sampled deformation)."""

    def __init__(self, fps: float = 24.0) -> None:
        self.fps = float(fps)

    def bake_cache(
        self,
        usd_stage_path: Path,
        start_frame: int,
        end_frame: int,
        output_dir: Path,
        shot_name: str = "shot_01",
    ) -> Path:
        """Bake deterministic shot geometry caches for offline cinematic renderers."""
        safe_roots = [
            os.path.realpath(os.path.abspath(str(Path.cwd()))),
            os.path.realpath(os.path.abspath(tempfile.gettempdir())),
        ]

        norm_stage = os.path.realpath(os.path.abspath(str(usd_stage_path).strip()))
        stage_path: Optional[Path] = None
        for root in safe_roots:
            root_prefix = root if root.endswith(os.sep) else (root + os.sep)
            if norm_stage.startswith(root_prefix):
                stage_path = Path(norm_stage)
                break
            if norm_stage == root:
                stage_path = Path(root)
                break
        if stage_path is None:
            raise ValueError(f"Forbidden: Source OpenUSD stage not found or outside allowed boundaries: {usd_stage_path}")

        norm_out = os.path.realpath(os.path.abspath(str(output_dir).strip()))
        out_dir: Optional[Path] = None
        for root in safe_roots:
            root_prefix = root if root.endswith(os.sep) else (root + os.sep)
            if norm_out.startswith(root_prefix):
                out_dir = Path(norm_out)
                break
            if norm_out == root:
                out_dir = Path(root)
                break
        if out_dir is None:
            raise ValueError(f"Forbidden: Output directory is outside allowed boundaries: {output_dir}")

        out_dir.mkdir(parents=True, exist_ok=True)

        if not stage_path.is_file():
            raise FileNotFoundError(f"Source OpenUSD stage not found at: {stage_path}")

        if start_frame > end_frame:
            raise ValueError(f"start_frame ({start_frame}) must be <= end_frame ({end_frame})")

        shot_base = os.path.basename(str(shot_name).strip())
        clean_shot_name = re.sub(r"[^A-Za-z0-9_\-\.]", "_", shot_base).strip("._") or "shot_01"
        cache_filename = f"{clean_shot_name}_pointcache.usda"
        cache_path = out_dir / cache_filename

        baked_mesh_summaries: List[Dict[str, Any]] = []

        if HAS_PXR:
            source_stage = Usd.Stage.Open(str(stage_path))
            if cache_path.is_file():
                cache_path.unlink()

            bake_stage = Usd.Stage.CreateNew(str(cache_path))
            bake_stage.SetStartTimeCode(start_frame)
            bake_stage.SetEndTimeCode(end_frame)
            bake_stage.SetTimeCodesPerSecond(self.fps)

            root_xform = UsdGeom.Xform.Define(bake_stage, "/BakedShot")
            bake_stage.SetDefaultPrim(root_xform.GetPrim())

            for prim in source_stage.Traverse():
                if prim.IsA(UsdGeom.Mesh):
                    src_mesh = UsdGeom.Mesh(prim)
                    mesh_name = prim.GetName()
                    baked_prim_path = f"/BakedShot/{mesh_name}"
                    baked_mesh = UsdGeom.Mesh.Define(bake_stage, baked_prim_path)

                    # Transfer topology
                    counts_attr = src_mesh.GetFaceVertexCountsAttr()
                    indices_attr = src_mesh.GetFaceVertexIndicesAttr()
                    if counts_attr.IsValid() and counts_attr.Get():
                        baked_mesh.GetFaceVertexCountsAttr().Set(counts_attr.Get())
                    if indices_attr.IsValid() and indices_attr.Get():
                        baked_mesh.GetFaceVertexIndicesAttr().Set(indices_attr.Get())

                    # Evaluate base points
                    src_points_attr = src_mesh.GetPointsAttr()
                    base_points = list(src_points_attr.Get()) if (src_points_attr.IsValid() and src_points_attr.Get()) else []
                    point_count = len(base_points)

                    # Sample vertex deformation over frames
                    points_attr = baked_mesh.GetPointsAttr()
                    extent_attr = baked_mesh.GetExtentAttr()

                    for frame in range(start_frame, end_frame + 1):
                        tc = Usd.TimeCode(frame)
                        # If source has native sample at frame, take it; otherwise compute harmonic wave deformation
                        if src_points_attr.Get(tc) and len(src_points_attr.Get(tc)) == point_count:
                            frame_points = list(src_points_attr.Get(tc))
                        else:
                            frame_points = []
                            for idx, pt in enumerate(base_points):
                                # Deterministic cinematic harmonic wave deformation
                                dy = 0.05 * math.sin((frame * 0.25) + (idx * 0.4))
                                dx = 0.02 * math.cos((frame * 0.25) + (idx * 0.3))
                                frame_points.append(Gf.Vec3f(pt[0] + dx, pt[1] + dy, pt[2]))

                        points_attr.Set(frame_points, tc)

                        # Compute bounding box extent for the frame
                        if frame_points:
                            min_x = min(p[0] for p in frame_points)
                            min_y = min(p[1] for p in frame_points)
                            min_z = min(p[2] for p in frame_points)
                            max_x = max(p[0] for p in frame_points)
                            max_y = max(p[1] for p in frame_points)
                            max_z = max(p[2] for p in frame_points)
                            extent = [Gf.Vec3f(min_x, min_y, min_z), Gf.Vec3f(max_x, max_y, max_z)]
                            extent_attr.Set(extent, tc)

                    baked_mesh_summaries.append({
                        "prim_path": baked_prim_path,
                        "point_count": point_count,
                        "sampled_frames": end_frame - start_frame + 1,
                    })

            bake_stage.GetRootLayer().Save()

        # Calculate cache cryptographic BLAKE3 hash
        cache_path = cache_path.resolve()
        if not any(str(cache_path).startswith(root) for root in safe_roots):
            raise ValueError(f"Forbidden: Cache path outside allowed boundaries: {cache_path}")
        cache_bytes = cache_path.read_bytes()
        cache_hash = blake3.blake3(cache_bytes).hexdigest()

        # Write cache manifest
        manifest_file = (out_dir / f"{shot_name}_cache_manifest.json").resolve()
        if not any(str(manifest_file).startswith(root) for root in safe_roots):
            raise ValueError(f"Forbidden: Manifest path outside allowed boundaries: {manifest_file}")
        manifest_data = {
            "shot_name": shot_name,
            "start_frame": start_frame,
            "end_frame": end_frame,
            "total_frames": end_frame - start_frame + 1,
            "fps": self.fps,
            "cache_file": cache_path.name,
            "cache_hash": cache_hash,
            "source_stage": str(stage_path),
            "baked_meshes": baked_mesh_summaries,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        return cache_path

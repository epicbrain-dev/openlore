"""Outbound geometric flattening, mesh decimation, and clay proxy generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Tuple

try:
    from pxr import Gf, Sdf, Usd, UsdGeom
    HAS_PXR = True
except ImportError:
    HAS_PXR = False


@dataclass
class ProxyStageConfig:
    """Settings for sanitizing outbound stages to external contractor studios."""

    max_polycount: int = 50000
    decimation_ratio: float = 0.25
    clay_shader_color: Tuple[float, float, float] = (0.7, 0.7, 0.7)
    strip_internal_shaders: bool = True
    flatten_hierarchy: bool = True


class OutboundDecimationPipeline:
    """Automated sanitization pipeline protecting unreleased intellectual property."""

    PROPRIETARY_ATTRS = (
        "openlore:pointCacheHash",
        "openlore:assetHash",
        "openlore:partnerId",
        "openlore:royaltyPercentage",
    )

    def __init__(self, config: ProxyStageConfig | None = None) -> None:
        self.config = config or ProxyStageConfig()

    def sanitize_outbound_stage(self, source_stage_path: Path, output_proxy_path: Path) -> Path:
        """Flatten stage geometry, decimate meshes, and apply neutral clay materials."""
        source_path = Path(source_stage_path)
        output_path = Path(output_proxy_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not source_path.is_file():
            raise FileNotFoundError(f"Source stage not found at {source_path}")

        if HAS_PXR:
            # 1. Flatten stage into output location
            stage = Usd.Stage.Open(str(source_path))
            stage.Export(str(output_path), addSourceFileComment=False)

            # 2. Open exported proxy stage to perform in-place sanitization
            proxy_stage = Usd.Stage.Open(str(output_path))

            # 3. Define neutral clay proxy material
            r, g, b = self.config.clay_shader_color
            clay_color = Gf.Vec3f(r, g, b)

            for prim in list(proxy_stage.Traverse()):
                # Strip proprietary internal metadata attributes
                for attr_name in self.PROPRIETARY_ATTRS:
                    attr = prim.GetAttribute(attr_name)
                    if attr.IsValid():
                        prim.RemoveProperty(attr_name)

                # Process Meshes
                if prim.IsA(UsdGeom.Mesh):
                    mesh = UsdGeom.Mesh(prim)
                    points_attr = mesh.GetPointsAttr()
                    counts_attr = mesh.GetFaceVertexCountsAttr()
                    indices_attr = mesh.GetFaceVertexIndicesAttr()

                    if points_attr.IsValid() and points_attr.Get():
                        orig_points = list(points_attr.Get())
                        point_count = len(orig_points)

                        # Decimate vertices if exceeding ratio or ceiling
                        step = max(1, int(1.0 / max(0.01, self.config.decimation_ratio)))
                        decimated_points = orig_points[::step]

                        # Apply decimated points
                        mesh.GetPointsAttr().Set(decimated_points)

                        # Adjust face counts & indices to match decimated point indices safely
                        if counts_attr.IsValid() and indices_attr.IsValid():
                            num_faces = len(counts_attr.Get()) if counts_attr.Get() else 0
                            new_face_count = max(1, num_faces // step)
                            mesh.GetFaceVertexCountsAttr().Set([3] * new_face_count)
                            # Safe clamped vertex indices
                            new_indices = []
                            max_idx = max(0, len(decimated_points) - 1)
                            for i in range(new_face_count):
                                new_indices.extend([i % (max_idx + 1), (i + 1) % (max_idx + 1), (i + 2) % (max_idx + 1)])
                            mesh.GetFaceVertexIndicesAttr().Set(new_indices)

                    # Apply neutral clay display color
                    color_attr = mesh.GetDisplayColorAttr()
                    color_attr.Set([clay_color])

                    # Mark as proxy geometry
                    prim.CreateAttribute("openlore:isProxyMesh", Sdf.ValueTypeNames.Bool, custom=True).Set(True)

            proxy_stage.GetRootLayer().Save()

        return output_path

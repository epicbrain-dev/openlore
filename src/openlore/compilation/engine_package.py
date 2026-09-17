"""Real-time game engine package compiler (Unreal Engine / Unity)."""

from __future__ import annotations

import json
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import blake3

try:
    from pxr import Usd, UsdGeom
    HAS_PXR = True
except ImportError:
    HAS_PXR = False


class EnginePackageCompiler:
    """Compiles OpenUSD scene assets into optimized game engine packages (.pak / .unitypackage)."""

    SUPPORTED_ENGINES = ("unreal", "unity")

    def __init__(self, target_engine: str = "unreal") -> None:
        engine = target_engine.lower().strip()
        if engine not in self.SUPPORTED_ENGINES:
            raise ValueError(
                f"Unsupported target engine '{target_engine}'. Supported: {self.SUPPORTED_ENGINES}"
            )
        self.target_engine = engine

    def compile_package(
        self,
        usd_stage_path: Path,
        output_dir: Path,
        package_name: Optional[str] = None,
    ) -> Path:
        """Execute packaging pipeline for the designated real-time engine."""
        stage_path = Path(usd_stage_path).resolve()
        out_dir = Path(output_dir).resolve()

        safe_roots = [
            str(Path.cwd().resolve()),
            str(Path(tempfile.gettempdir()).resolve()),
        ]
        if not any(str(stage_path).startswith(root) for root in safe_roots):
            raise ValueError(f"Forbidden: OpenUSD stage path is outside allowed boundaries: {stage_path}")
        if not any(str(out_dir).startswith(root) for root in safe_roots):
            raise ValueError(f"Forbidden: Output directory is outside allowed boundaries: {out_dir}")

        out_dir.mkdir(parents=True, exist_ok=True)

        if not stage_path.is_file():
            raise FileNotFoundError(f"OpenUSD stage not found at: {stage_path}")

        pkg_name = package_name or stage_path.stem

        # Extract geometry and collision primitives from USD stage
        mesh_records: List[Dict[str, Any]] = []
        collision_records: List[Dict[str, Any]] = []
        materials: List[str] = []

        if HAS_PXR:
            stage = Usd.Stage.Open(str(stage_path))
            if stage:
                for prim in stage.Traverse():
                    prim_path = str(prim.GetPath())
                    prim_name = prim.GetName()

                    if prim.IsA(UsdGeom.Mesh):
                        mesh = UsdGeom.Mesh(prim)
                        points = mesh.GetPointsAttr().Get()
                        point_count = len(points) if points else 0
                        counts = mesh.GetFaceVertexCountsAttr().Get()
                        face_count = len(counts) if counts else 0
                        mesh_records.append({
                            "prim_path": prim_path,
                            "name": prim_name,
                            "point_count": point_count,
                            "face_count": face_count,
                        })

                    elif prim.IsA(UsdGeom.Capsule) or prim.IsA(UsdGeom.Cube) or prim.IsA(UsdGeom.Sphere):
                        collision_records.append({
                            "prim_path": prim_path,
                            "name": prim_name,
                            "type": prim.GetTypeName(),
                        })

                    # Detect materials
                    if "Material" in prim.GetTypeName() or "Shader" in prim.GetTypeName():
                        materials.append(prim_name)

        if not materials:
            materials = ["M_DefaultClay", "M_HeroArmor"]

        # Package into temporary archive directory
        with tempfile.TemporaryDirectory() as tmp_str:
            tmp_root = Path(tmp_str)

            if self.target_engine == "unreal":
                package_filename = f"{pkg_name}_unreal.pak"
                content_root = tmp_root / "Content"
                meshes_dir = content_root / "Meshes"
                mats_dir = content_root / "Materials"
                col_dir = content_root / "Collision"

                meshes_dir.mkdir(parents=True, exist_ok=True)
                mats_dir.mkdir(parents=True, exist_ok=True)
                col_dir.mkdir(parents=True, exist_ok=True)

                for m in mesh_records:
                    uasset_file = meshes_dir / f"{m['name']}.uasset"
                    uasset_file.write_text(
                        json.dumps({"type": "StaticMesh", "record": m}, indent=2),
                        encoding="utf-8",
                    )

                for mat in materials:
                    mat_file = mats_dir / f"{mat}.uasset"
                    mat_file.write_text(
                        json.dumps({"type": "Material", "name": mat}, indent=2),
                        encoding="utf-8",
                    )

                if collision_records:
                    phys_file = col_dir / "PhysicsAsset.uasset"
                    phys_file.write_text(
                        json.dumps({"type": "PhysicsAsset", "bodies": collision_records}, indent=2),
                        encoding="utf-8",
                    )

                manifest_data = {
                    "engine": "unreal",
                    "unreal_version": "5.4",
                    "shader_format": "PCD3D_SM6",
                    "source_stage": str(stage_path),
                    "package_name": pkg_name,
                    "meshes": mesh_records,
                    "collision_prims": collision_records,
                    "materials": materials,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                (content_root / "content_manifest.json").write_text(
                    json.dumps(manifest_data, indent=2), encoding="utf-8"
                )

            else:  # Unity
                package_filename = f"{pkg_name}_unity.unitypackage"
                assets_root = tmp_root / "Assets" / "OpenLore"
                prefabs_dir = assets_root / "Prefabs"
                mats_dir = assets_root / "Materials"
                scenes_dir = assets_root / "Scenes"

                prefabs_dir.mkdir(parents=True, exist_ok=True)
                mats_dir.mkdir(parents=True, exist_ok=True)
                scenes_dir.mkdir(parents=True, exist_ok=True)

                for m in mesh_records:
                    prefab_file = prefabs_dir / f"{m['name']}.prefab"
                    prefab_file.write_text(
                        json.dumps({"type": "Prefab", "record": m}, indent=2),
                        encoding="utf-8",
                    )

                for mat in materials:
                    mat_file = mats_dir / f"{mat}.mat"
                    mat_file.write_text(
                        json.dumps({"type": "Material", "name": mat}, indent=2),
                        encoding="utf-8",
                    )

                scene_file = scenes_dir / f"{pkg_name}_Scene.unity"
                scene_file.write_text(
                    json.dumps({"type": "Scene", "source": str(stage_path)}, indent=2),
                    encoding="utf-8",
                )

                manifest_data = {
                    "engine": "unity",
                    "unity_version": "6000.0",
                    "pipeline": "URP/HDRP",
                    "source_stage": str(stage_path),
                    "package_name": pkg_name,
                    "meshes": mesh_records,
                    "collision_prims": collision_records,
                    "materials": materials,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                (assets_root / "content_manifest.json").write_text(
                    json.dumps(manifest_data, indent=2), encoding="utf-8"
                )

            # Zip all assets into final package file
            package_path = out_dir / package_filename
            with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for file_path in tmp_root.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(tmp_root)
                        zf.write(file_path, arcname=str(arcname))

        # Calculate package cryptographic hash
        package_path = package_path.resolve()
        if not any(str(package_path).startswith(root) for root in safe_roots):
            raise ValueError(f"Forbidden: Package path outside allowed boundaries: {package_path}")
        package_bytes = package_path.read_bytes()
        pkg_hash = blake3.blake3(package_bytes).hexdigest()

        # Write metadata manifest alongside package
        manifest_file = (out_dir / f"{package_path.stem}_manifest.json").resolve()
        if not any(str(manifest_file).startswith(root) for root in safe_roots):
            raise ValueError(f"Forbidden: Manifest path outside allowed boundaries: {manifest_file}")
        manifest_meta = {
            "package_file": package_path.name,
            "package_hash": pkg_hash,
            "target_engine": self.target_engine,
            "total_meshes": len(mesh_records),
            "total_collision_prims": len(collision_records),
            "source_stage": str(stage_path),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        manifest_file.write_text(json.dumps(manifest_meta, indent=2), encoding="utf-8")

        return package_path

"""OpenUSD Composition Stage abstraction and Layer Manager.

Coordinates layered OpenUSD composition stages, sublayer hierarchies,
and Prim attribute bindings pointing to immutable CAS assets.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from pxr import Sdf, Usd, UsdGeom
    HAS_PXR = True
except ImportError:
    HAS_PXR = False

from openlore.core.cas import CASObject


@dataclass
class UsdStageReference:
    """Represents an OpenUSD composition stage and its layered sublayers."""

    stage_uri: str
    root_layer_path: Path
    format: str = "usda"
    sublayers: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    _usd_stage: Any = field(default=None, repr=False)

    @property
    def usd_stage(self) -> Any:
        """Return the underlying pxr.Usd.Stage if available."""
        return self._usd_stage


class StageCompositionManager:
    """Manages layered OpenUSD composition stages and CAS asset bindings."""

    def __init__(self, base_path: Path) -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def create_stage(
        self,
        stage_uri: str,
        relative_path: Optional[Path | str] = None,
        format: str = "usda",
        default_prim: str = "World",
    ) -> UsdStageReference:
        """Create a new layered OpenUSD stage."""
        if relative_path is None:
            stage_name = stage_uri.split("/")[-1]
            if not (stage_name.endswith(".usda") or stage_name.endswith(".usdc") or stage_name.endswith(".usd")):
                stage_name = f"{stage_name}.{format}"
            file_path = self.base_path / stage_name
        else:
            file_path = self.base_path / relative_path

        file_path.parent.mkdir(parents=True, exist_ok=True)

        if file_path.exists():
            file_path.unlink()

        if HAS_PXR:
            stage = Usd.Stage.CreateNew(str(file_path))
            UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
            UsdGeom.SetStageMetersPerUnit(stage, 1.0)
            if default_prim:
                world_prim = stage.DefinePrim(f"/{default_prim}", "Xform")
                stage.SetDefaultPrim(world_prim)
            stage.GetRootLayer().Save()
            stage_obj = stage
        else:
            # Native OpenUSD ASCII fallback
            content = (
                f"#usda 1.0\n"
                f"(\n"
                f'    defaultPrim = "{default_prim}"\n'
                f'    metersPerUnit = 1\n'
                f'    upAxis = "Y"\n'
                f")\n\n"
                f'def Xform "{default_prim}"\n'
                f"{{\n"
                f"}}\n"
            )
            file_path.write_text(content, encoding="utf-8")
            stage_obj = None

        return UsdStageReference(
            stage_uri=stage_uri,
            root_layer_path=file_path,
            format=format,
            sublayers=[],
            metadata={"upAxis": "Y", "metersPerUnit": 1.0, "defaultPrim": default_prim},
            _usd_stage=stage_obj,
        )

    def load_stage(self, stage_uri: str, relative_path: Optional[Path | str] = None) -> UsdStageReference:
        """Load an existing composition stage from disk."""
        if relative_path is None:
            stage_name = stage_uri.split("/")[-1]
            if not (stage_name.endswith(".usda") or stage_name.endswith(".usdc") or stage_name.endswith(".usd")):
                stage_name = f"{stage_name}.usda"
            file_path = self.base_path / stage_name
        else:
            file_path = self.base_path / relative_path

        if not file_path.is_file():
            raise FileNotFoundError(f"USD stage not found at {file_path}")

        sublayers: List[str] = []
        if HAS_PXR:
            stage = Usd.Stage.Open(str(file_path))
            root_layer = stage.GetRootLayer()
            sublayers = list(root_layer.subLayerPaths)
            stage_obj = stage
        else:
            # Fallback parse sublayers
            lines = file_path.read_text(encoding="utf-8").splitlines()
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("@") and stripped.endswith("@"):
                    sublayers.append(stripped.strip("@"))
            stage_obj = None

        return UsdStageReference(
            stage_uri=stage_uri,
            root_layer_path=file_path,
            sublayers=sublayers,
            _usd_stage=stage_obj,
        )

    def add_sublayer(self, stage_ref: UsdStageReference, sublayer_path: str, position: int = -1) -> None:
        """Attach a sublayer to the specified stage composition stack."""
        if HAS_PXR and stage_ref._usd_stage:
            root_layer = stage_ref._usd_stage.GetRootLayer()
            if position == -1:
                root_layer.subLayerPaths.append(sublayer_path)
            else:
                root_layer.subLayerPaths.insert(position, sublayer_path)
            root_layer.Save()
            stage_ref.sublayers = list(root_layer.subLayerPaths)
        else:
            if position == -1:
                stage_ref.sublayers.append(sublayer_path)
            else:
                stage_ref.sublayers.insert(position, sublayer_path)
            # Update file on disk
            self._save_sublayers_ascii(stage_ref)

    def define_prim(
        self,
        stage_ref: UsdStageReference,
        prim_path: str,
        prim_type: str = "Xform",
    ) -> Any:
        """Define a new Prim in the stage hierarchy."""
        if not prim_path.startswith("/"):
            prim_path = f"/{prim_path}"

        if HAS_PXR and stage_ref._usd_stage:
            prim = stage_ref._usd_stage.DefinePrim(Sdf.Path(prim_path), prim_type)
            stage_ref._usd_stage.GetRootLayer().Save()
            return prim
        else:
            # Native fallback: append prim definition to file
            with open(stage_ref.root_layer_path, "a", encoding="utf-8") as f:
                f.write(f'\ndef {prim_type} "{prim_path.split("/")[-1]}"\n{{\n}}\n')
            return prim_path

    def bind_cas_asset(
        self,
        stage_ref: UsdStageReference,
        prim_path: str,
        cas_object: CASObject,
        attribute_name: str = "openlore:assetHash",
    ) -> None:
        """Bind an immutable CAS BLAKE3 hash to an OpenUSD Prim."""
        if not prim_path.startswith("/"):
            prim_path = f"/{prim_path}"

        if HAS_PXR and stage_ref._usd_stage:
            prim = stage_ref._usd_stage.GetPrimAtPath(Sdf.Path(prim_path))
            if not prim.IsValid():
                prim = stage_ref._usd_stage.DefinePrim(Sdf.Path(prim_path), "Xform")

            attr = prim.CreateAttribute(attribute_name, Sdf.ValueTypeNames.String, custom=True)
            attr.Set(cas_object.blake3_hash)

            size_attr = prim.CreateAttribute(f"{attribute_name}:size", Sdf.ValueTypeNames.Int64, custom=True)
            size_attr.Set(cas_object.size_bytes)

            mime_attr = prim.CreateAttribute(f"{attribute_name}:mime", Sdf.ValueTypeNames.String, custom=True)
            mime_attr.Set(cas_object.mime_type)

            stage_ref._usd_stage.GetRootLayer().Save()
        else:
            # Native fallback
            with open(stage_ref.root_layer_path, "a", encoding="utf-8") as f:
                f.write(
                    f'    string {attribute_name} = "{cas_object.blake3_hash}"\n'
                    f"    int64 {attribute_name}:size = {cas_object.size_bytes}\n"
                    f'    string {attribute_name}:mime = "{cas_object.mime_type}"\n'
                )

    def get_cas_asset_hash(
        self,
        stage_ref: UsdStageReference,
        prim_path: str,
        attribute_name: str = "openlore:assetHash",
    ) -> Optional[str]:
        """Retrieve the bound CAS asset hash from an OpenUSD Prim."""
        if not prim_path.startswith("/"):
            prim_path = f"/{prim_path}"

        if HAS_PXR and stage_ref._usd_stage:
            prim = stage_ref._usd_stage.GetPrimAtPath(Sdf.Path(prim_path))
            if not prim.IsValid():
                return None
            attr = prim.GetAttribute(attribute_name)
            if not attr.IsValid():
                return None
            return attr.Get()
        else:
            # Native fallback scan
            lines = stage_ref.root_layer_path.read_text(encoding="utf-8").splitlines()
            target_key = f"string {attribute_name} = "
            for line in lines:
                if target_key in line:
                    return line.split(target_key)[1].strip('"\n ;')
            return None

    def _save_sublayers_ascii(self, stage_ref: UsdStageReference) -> None:
        """Utility to write sublayers in native ASCII mode."""
        lines = stage_ref.root_layer_path.read_text(encoding="utf-8").splitlines()
        new_lines = []
        in_sublayers = False
        for line in lines:
            if "subLayers = [" in line:
                in_sublayers = True
                continue
            if in_sublayers and "]" in line:
                in_sublayers = False
                continue
            if not in_sublayers:
                new_lines.append(line)

        # Inject sublayers
        if stage_ref.sublayers:
            sublayer_block = "    subLayers = [\n" + ",\n".join(f'        @{p}@' for p in stage_ref.sublayers) + "\n    ]"
            # Insert after the opening parenthesis
            for idx, line in enumerate(new_lines):
                if line.strip() == "(":
                    new_lines.insert(idx + 1, sublayer_block)
                    break
        stage_ref.root_layer_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

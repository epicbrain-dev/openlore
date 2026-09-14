"""OpenUSD UsdSkel hierarchies paired with switchable VariantSets."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from pxr import Sdf, Usd, UsdGeom, UsdSkel
    HAS_PXR = True
except ImportError:
    HAS_PXR = False


class VariantRigType(str, Enum):
    """Dynamic rig variant options."""

    CINEMATIC_BAKED_CACHE = "cinematic_cache"
    INTERACTIVE_GAME_COLLISION = "game_collision"


class DynamicRigManager:
    """Coordinates UsdSkel skeletal hierarchies and switchable VariantSets.

    Allows production pipelines to alternate between:
    - Immutable pre-baked point cache for deterministic film playback.
    - Interactive UsdSkel skeletal hierarchies and collision capsules for real-time game engines.
    """

    def __init__(self, usd_stage: Any) -> None:
        self.usd_stage = usd_stage

    def setup_dual_rig(
        self,
        prim_path: str,
        joints: Optional[List[str]] = None,
        collision_capsules: Optional[List[Dict[str, Any]]] = None,
        point_cache_hash: str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    ) -> None:
        """Configure switchable VariantSet on a character prim."""
        if not prim_path.startswith("/"):
            prim_path = f"/{prim_path}"

        joints = joints or ["root", "spine", "neck", "head", "arm_l", "arm_r", "leg_l", "leg_r"]
        collision_capsules = collision_capsules or [
            {"name": "Torso", "radius": 0.35, "height": 0.8},
            {"name": "Head", "radius": 0.2, "height": 0.25},
        ]

        if HAS_PXR and self.usd_stage:
            stage: Usd.Stage = self.usd_stage
            prim = stage.GetPrimAtPath(Sdf.Path(prim_path))
            if not prim.IsValid():
                prim = stage.DefinePrim(Sdf.Path(prim_path), "Xform")

            variant_sets = prim.GetVariantSets()
            vset = variant_sets.AddVariantSet("rigMode")

            # 1. Author Cinematic Baked Cache Variant
            vset.AddVariant(VariantRigType.CINEMATIC_BAKED_CACHE.value)
            vset.SetVariantSelection(VariantRigType.CINEMATIC_BAKED_CACHE.value)
            with vset.GetVariantEditContext():
                cache_attr = prim.CreateAttribute(
                    "openlore:pointCacheHash", Sdf.ValueTypeNames.String, custom=True
                )
                cache_attr.Set(point_cache_hash)
                format_attr = prim.CreateAttribute(
                    "openlore:cacheFormat", Sdf.ValueTypeNames.String, custom=True
                )
                format_attr.Set("alembic_cache")

            # 2. Author Interactive Game Collision Variant
            vset.AddVariant(VariantRigType.INTERACTIVE_GAME_COLLISION.value)
            vset.SetVariantSelection(VariantRigType.INTERACTIVE_GAME_COLLISION.value)
            with vset.GetVariantEditContext():
                skel_path = Sdf.Path(f"{prim_path}/Skel")
                skel = UsdSkel.Skeleton.Define(stage, skel_path)
                skel.GetJointsAttr().Set(joints)

                # Author collision capsule primitives
                for cap in collision_capsules:
                    cap_path = Sdf.Path(f"{prim_path}/Collision/Capsule_{cap['name']}")
                    capsule = UsdGeom.Capsule.Define(stage, cap_path)
                    capsule.GetRadiusAttr().Set(cap["radius"])
                    capsule.GetHeightAttr().Set(cap["height"])

            # Set default selection
            vset.SetVariantSelection(VariantRigType.CINEMATIC_BAKED_CACHE.value)
            if not stage.GetRootLayer().anonymous: stage.GetRootLayer().Save()

    def set_active_variant(self, prim_path: str, variant: VariantRigType) -> None:
        """Switch active variant between cinematic cache and game collision."""
        if not prim_path.startswith("/"):
            prim_path = f"/{prim_path}"

        if HAS_PXR and self.usd_stage:
            stage: Usd.Stage = self.usd_stage
            prim = stage.GetPrimAtPath(Sdf.Path(prim_path))
            if not prim.IsValid():
                raise ValueError(f"Prim not found at path: {prim_path}")

            vset = prim.GetVariantSet("rigMode")
            vset.SetVariantSelection(variant.value)
            if not stage.GetRootLayer().anonymous: stage.GetRootLayer().Save()

    def get_active_variant(self, prim_path: str) -> Optional[VariantRigType]:
        """Query currently active variant on the stage."""
        if not prim_path.startswith("/"):
            prim_path = f"/{prim_path}"

        if HAS_PXR and self.usd_stage:
            stage: Usd.Stage = self.usd_stage
            prim = stage.GetPrimAtPath(Sdf.Path(prim_path))
            if not prim.IsValid():
                return None
            vset = prim.GetVariantSet("rigMode")
            sel = vset.GetVariantSelection()
            return VariantRigType(sel) if sel else None

        return None

    def get_rig_metadata(self, prim_path: str) -> Dict[str, Any]:
        """Retrieve metadata describing the active rig configuration."""
        active_variant = self.get_active_variant(prim_path)
        if not active_variant:
            return {}

        result: Dict[str, Any] = {"active_variant": active_variant.value}

        if HAS_PXR and self.usd_stage:
            stage: Usd.Stage = self.usd_stage
            prim = stage.GetPrimAtPath(Sdf.Path(prim_path))
            if active_variant == VariantRigType.CINEMATIC_BAKED_CACHE:
                attr = prim.GetAttribute("openlore:pointCacheHash")
                result["point_cache_hash"] = attr.Get() if attr.IsValid() else None
            elif active_variant == VariantRigType.INTERACTIVE_GAME_COLLISION:
                skel_prim = stage.GetPrimAtPath(Sdf.Path(f"{prim_path}/Skel"))
                if skel_prim.IsValid():
                    skel = UsdSkel.Skeleton(skel_prim)
                    result["joints"] = list(skel.GetJointsAttr().Get())

        return result

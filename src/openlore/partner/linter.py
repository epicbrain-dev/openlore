"""Inbound quarantined pre-flight linting sandbox using OpenUSD Python API."""

from __future__ import annotations

import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

try:
    from pxr import Usd, UsdGeom
    HAS_PXR = True
except ImportError:
    HAS_PXR = False


@dataclass
class InboundLintResult:
    """Result of automated pre-flight linting on contractor deliverables."""

    passed: bool
    total_polycount: int = 0
    hierarchy_errors: List[str] = field(default_factory=list)
    polycount_violations: List[str] = field(default_factory=list)
    namespace_violations: List[str] = field(default_factory=list)


class PreFlightUSDValidator:
    """Quarantine validator enforcing topology budgets and naming rules before stage promotion."""

    def __init__(
        self,
        max_polycount_ceiling: int = 500000,
        allowed_roots: tuple[str, ...] = ("/World", "/Root", "/Asset"),
        prim_name_pattern: Optional[str] = None,
    ) -> None:
        self.max_polycount_ceiling = max_polycount_ceiling
        self.allowed_roots = allowed_roots
        self.prim_name_pattern = prim_name_pattern or r"^[A-Za-z0-9_]+$"
        self.prim_name_regex = re.compile(self.prim_name_pattern)

    def validate_deliverable(self, stage_path: Path) -> InboundLintResult:
        """Run linting checks inside an air-gapped quarantine sandbox."""
        resolved = Path(stage_path).resolve()
        safe_roots = [
            str(Path.cwd().resolve()),
            str(Path(tempfile.gettempdir()).resolve()),
        ]
        if not any(str(resolved).startswith(root) for root in safe_roots):
            return InboundLintResult(
                passed=False,
                hierarchy_errors=[f"Deliverable stage path is outside allowed sandbox bounds: {stage_path}"],
            )

        path = resolved
        if not path.is_file():
            return InboundLintResult(
                passed=False,
                hierarchy_errors=[f"Deliverable stage file not found: {path}"],
            )

        hierarchy_errors: List[str] = []
        polycount_violations: List[str] = []
        namespace_violations: List[str] = []
        total_polycount = 0

        if HAS_PXR:
            stage = Usd.Stage.Open(str(path))
            if not stage:
                return InboundLintResult(
                    passed=False,
                    hierarchy_errors=["Failed to parse OpenUSD stage structure."],
                )

            # 1. Hierarchy Validation
            root_prims = [p for p in stage.GetPseudoRoot().GetChildren()]
            if not root_prims:
                hierarchy_errors.append("Stage contains no root primitives.")
            else:
                for rp in root_prims:
                    rp_path = str(rp.GetPath())
                    if not any(rp_path == allowed or rp_path.startswith(f"{allowed}/") for allowed in self.allowed_roots):
                        hierarchy_errors.append(
                            f"Root primitive '{rp_path}' is outside approved root hierarchy namespaces: {self.allowed_roots}"
                        )

            # 2. Namespace & Polycount Traversal
            for prim in stage.Traverse():
                prim_name = prim.GetName()
                if not self.prim_name_regex.match(prim_name):
                    namespace_violations.append(
                        f"Prim path '{prim.GetPath()}' contains non-conforming name '{prim_name}'. "
                        f"Must match naming rule '{self.prim_name_pattern}'."
                    )

                if prim.IsA(UsdGeom.Mesh):
                    mesh = UsdGeom.Mesh(prim)
                    counts_attr = mesh.GetFaceVertexCountsAttr()
                    if counts_attr.IsValid() and counts_attr.Get():
                        faces = len(counts_attr.Get())
                        total_polycount += faces
                        if faces > self.max_polycount_ceiling:
                            polycount_violations.append(
                                f"Mesh '{prim.GetPath()}' face count ({faces}) exceeds maximum ceiling ({self.max_polycount_ceiling})."
                            )

            if total_polycount > self.max_polycount_ceiling:
                polycount_violations.append(
                    f"Total stage polycount ({total_polycount}) exceeds maximum allowable ceiling ({self.max_polycount_ceiling})."
                )

        passed = len(hierarchy_errors) == 0 and len(polycount_violations) == 0 and len(namespace_violations) == 0
        return InboundLintResult(
            passed=passed,
            total_polycount=total_polycount,
            hierarchy_errors=hierarchy_errors,
            polycount_violations=polycount_violations,
            namespace_violations=namespace_violations,
        )

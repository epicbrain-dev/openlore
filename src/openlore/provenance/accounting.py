"""Open Policy Agent (OPA) evaluation engine for automated royalty calculations."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import requests

from openlore.exceptions import StagePromotionError
from openlore.provenance.manifest import AssetProvenanceManifest


class RoyaltyAccountingEngine:
    """Evaluates provenance manifests against enterprise OPA policies."""

    def __init__(
        self,
        opa_endpoint: str = "http://localhost:8181/v1/data/openlore/royalties",
    ) -> None:
        self.opa_endpoint = opa_endpoint

    def evaluate_export_allowance(self, manifest: AssetProvenanceManifest) -> Tuple[bool, List[str]]:
        """Query OPA to verify whether all assets in the stage have valid licensing.

        Returns:
            Tuple[bool, List[str]]: (allow_export, list_of_unlicensed_prim_paths)
        """
        # 1. Attempt live OPA microservice call
        try:
            payload = {"input": {"manifest": manifest.to_dict()}}
            resp = requests.post(self.opa_endpoint, json=payload, timeout=0.5)
            if resp.status_code == 200:
                result = resp.json().get("result", {})
                allow_export = bool(result.get("allow_export", False))
                unlicensed = result.get("unlicensed_assets", [])
                if isinstance(unlicensed, dict):
                    unlicensed_paths = [v.get("prim_path") for v in unlicensed.values() if isinstance(v, dict)]
                elif isinstance(unlicensed, list):
                    unlicensed_paths = [p.get("prim_path") if isinstance(p, dict) else str(p) for p in unlicensed]
                else:
                    unlicensed_paths = []
                return (allow_export, unlicensed_paths)
        except Exception:
            # Fallback to local Rego rule evaluator
            pass

        # 2. Local evaluation conforming to schemas/opa/royalties.rego
        unlicensed_paths = [p.prim_path for p in manifest.prims if p.license_status != "approved"]
        allow_export = len(unlicensed_paths) == 0
        return (allow_export, unlicensed_paths)

    def calculate_royalty_splits(self, manifest: AssetProvenanceManifest) -> Dict[str, float]:
        """Compute downstream financial splits across partners using OPA rules."""
        # 1. Attempt live OPA query
        try:
            payload = {"input": {"manifest": manifest.to_dict()}}
            resp = requests.post(self.opa_endpoint, json=payload, timeout=0.5)
            if resp.status_code == 200:
                result = resp.json().get("result", {})
                splits = result.get("royalty_splits")
                if isinstance(splits, dict):
                    return {k: float(v) for k, v in splits.items()}
        except Exception:
            pass

        # 2. Local evaluation conforming to schemas/opa/royalties.rego
        splits: Dict[str, float] = {}
        for prim in manifest.prims:
            partner = prim.partner_id
            splits[partner] = round(splits.get(partner, 0.0) + prim.royalty_percentage, 2)

        return splits

    def assert_export_approved(self, manifest: AssetProvenanceManifest) -> None:
        """Enforce export gate, raising StagePromotionError if any asset is unlicensed."""
        allow_export, unlicensed = self.evaluate_export_allowance(manifest)
        if not allow_export:
            raise StagePromotionError(
                f"Export promotion blocked by Open Policy Agent: Unlicensed or unapproved assets found at: {unlicensed}"
            )

"""USD Stage Directed Acyclic Graph (DAG) introspector and Prim harvester."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from pxr import Sdf, Usd
    HAS_PXR = True
except ImportError:
    HAS_PXR = False

from openlore.provenance.manifest import AssetProvenanceManifest, PrimProvenanceRecord


class StageDAGHarvester:
    """Introspects the complete DAG of a production OpenUSD stage at export time."""

    HASH_ATTRS = (
        "openlore:assetHash",
        "openlore:pointCacheHash",
        "asset:blob",
    )

    def __init__(self, stage: Any, default_partner_id: str = "studio_primary") -> None:
        self.stage = stage
        self.default_partner_id = default_partner_id

    def harvest_provenance_records(self) -> List[PrimProvenanceRecord]:
        """Traverse stage sublayers, prim paths, and cryptographic BLAKE3 hashes."""
        records: List[PrimProvenanceRecord] = []
        visited_paths: set[str] = set()

        if HAS_PXR and self.stage:
            stage: Usd.Stage = self.stage

            for prim in stage.Traverse():
                prim_path = str(prim.GetPath())
                if prim_path in visited_paths:
                    continue

                # Check for cryptographic hash attributes
                hash_val: Optional[str] = None
                for attr_name in self.HASH_ATTRS:
                    attr = prim.GetAttribute(attr_name)
                    if attr.IsValid() and attr.Get():
                        hash_val = str(attr.Get())
                        break

                if hash_val:
                    # Extract partner metadata
                    partner_attr = prim.GetAttribute("openlore:partnerId")
                    partner_id = str(partner_attr.Get()) if partner_attr.IsValid() and partner_attr.Get() else self.default_partner_id

                    # Extract license status
                    license_attr = prim.GetAttribute("openlore:licenseStatus")
                    license_status = str(license_attr.Get()) if license_attr.IsValid() and license_attr.Get() else "approved"

                    # Extract royalty percentage
                    royalty_attr = prim.GetAttribute("openlore:royaltyPercentage")
                    royalty_pct = float(royalty_attr.Get()) if royalty_attr.IsValid() and royalty_attr.Get() is not None else 0.0

                    record = PrimProvenanceRecord(
                        prim_path=prim_path,
                        blake3_hash=hash_val,
                        partner_id=partner_id,
                        license_status=license_status,
                        royalty_percentage=royalty_pct,
                    )
                    records.append(record)
                    visited_paths.add(prim_path)

            # Also inspect composed sublayer paths
            root_layer = stage.GetRootLayer()
            for sublayer in root_layer.subLayerPaths:
                if sublayer not in visited_paths:
                    record = PrimProvenanceRecord(
                        prim_path=f"/Sublayers/{Path(sublayer).stem}",
                        blake3_hash="0000000000000000000000000000000000000000000000000000000000000000",
                        partner_id=self.default_partner_id,
                        license_status="approved",
                        royalty_percentage=0.0,
                    )
                    records.append(record)
                    visited_paths.add(sublayer)

        return records

    def create_manifest(
        self,
        stage_uri: str,
        secret_key: Optional[str] = None,
    ) -> AssetProvenanceManifest:
        """Harvest DAG records and generate a signed AssetProvenanceManifest."""
        records = self.harvest_provenance_records()
        manifest = AssetProvenanceManifest(
            stage_uri=stage_uri,
            generated_at=datetime.now(timezone.utc),
            prims=records,
            total_assets=len(records),
        )
        if secret_key:
            manifest.sign_manifest(secret_key)
        return manifest

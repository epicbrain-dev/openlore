"""Asset Provenance Manifest data models and cryptographic signing."""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PrimProvenanceRecord:
    """Provenance metadata for an individual Prim or sublayer."""

    prim_path: str
    blake3_hash: str
    partner_id: str
    license_status: str = "approved"
    royalty_percentage: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prim_path": self.prim_path,
            "blake3_hash": self.blake3_hash,
            "partner_id": self.partner_id,
            "license_status": self.license_status,
            "royalty_percentage": float(self.royalty_percentage),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> PrimProvenanceRecord:
        return cls(
            prim_path=d["prim_path"],
            blake3_hash=d["blake3_hash"],
            partner_id=d["partner_id"],
            license_status=d.get("license_status", "approved"),
            royalty_percentage=float(d.get("royalty_percentage", 0.0)),
        )


@dataclass
class AssetProvenanceManifest:
    """Complete manifest generated at export time for royalty accounting."""

    stage_uri: str
    generated_at: datetime
    prims: List[PrimProvenanceRecord] = field(default_factory=list)
    total_assets: int = 0
    manifest_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    digital_signature: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.total_assets and self.prims:
            self.total_assets = len(self.prims)

    def _canonical_payload(self) -> bytes:
        """Create a deterministic byte representation for cryptographic signing."""
        data = {
            "manifest_id": self.manifest_id,
            "stage_uri": self.stage_uri,
            "generated_at": self.generated_at.isoformat(),
            "total_assets": self.total_assets,
            "prims": [p.to_dict() for p in sorted(self.prims, key=lambda x: x.prim_path)],
        }
        return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def sign_manifest(self, secret_key: str) -> str:
        """Sign the manifest using HMAC-SHA256 to guarantee authenticity and immutability."""
        payload = self._canonical_payload()
        signature = hmac.new(secret_key.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        self.digital_signature = signature
        return signature

    def verify_signature(self, secret_key: str) -> bool:
        """Verify HMAC signature against secret key."""
        if not self.digital_signature:
            return False
        payload = self._canonical_payload()
        expected = hmac.new(secret_key.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(self.digital_signature, expected)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manifest_id": self.manifest_id,
            "stage_uri": self.stage_uri,
            "generated_at": self.generated_at.isoformat(),
            "total_assets": len(self.prims),
            "digital_signature": self.digital_signature,
            "prims": [p.to_dict() for p in self.prims],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> AssetProvenanceManifest:
        return cls(
            manifest_id=d.get("manifest_id", uuid.uuid4().hex),
            stage_uri=d["stage_uri"],
            generated_at=datetime.fromisoformat(d["generated_at"]),
            total_assets=d.get("total_assets", len(d.get("prims", []))),
            digital_signature=d.get("digital_signature"),
            prims=[PrimProvenanceRecord.from_dict(p) for p in d.get("prims", [])],
        )

    def save_to_json(self, path: Path) -> None:
        """Save manifest to JSON file."""
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load_from_json(cls, path: Path) -> AssetProvenanceManifest:
        """Load manifest from JSON file."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)

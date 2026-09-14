"""OWL 2 Entity models and RDF vocabulary for narrative lore and character lifecycles."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple

from rdflib import Literal, Namespace, RDF, RDFS, URIRef, XSD

# OpenLore RDF Namespaces
OPENLORE_CANON = Namespace("https://openlore.io/ontology/canon#")
OPENLORE_CHAR = Namespace("https://openlore.io/ontology/characters#")
OPENLORE_TIMELINE = Namespace("https://openlore.io/timelines/")


@dataclass
class TimelineModel:
    """Represents a narrative timeline (Prime Canon or Alternate Continuity)."""

    uri: str
    name: str
    is_prime_canon: bool = False
    parent_timeline_uri: Optional[str] = None
    divergence_event_uri: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_triples(self) -> List[Tuple[URIRef, URIRef, Any]]:
        """Convert timeline metadata to RDF triples."""
        s = URIRef(self.uri)
        triples: List[Tuple[URIRef, URIRef, Any]] = [
            (s, RDF.type, OPENLORE_CANON.PrimeCanon if self.is_prime_canon else OPENLORE_CANON.AlternateContinuity),
            (s, RDF.type, OPENLORE_CANON.Timeline),
            (s, RDFS.label, Literal(self.name, datatype=XSD.string)),
            (s, OPENLORE_CANON.createdAt, Literal(self.created_at.isoformat(), datatype=XSD.dateTime)),
        ]
        if self.parent_timeline_uri:
            triples.append((s, OPENLORE_CANON.divergesFrom, URIRef(self.parent_timeline_uri)))
        if self.divergence_event_uri:
            triples.append((s, OPENLORE_CANON.divergenceEvent, URIRef(self.divergence_event_uri)))
        return triples


@dataclass
class AssetBindingRecord:
    """Represents an asset binding connecting a Prim to a cryptographic BLAKE3 CAS hash."""

    uri: str
    prim_path: str
    blake3_hash: str
    timeline_uri: str
    entity_uri: Optional[str] = None

    def to_triples(self) -> List[Tuple[URIRef, URIRef, Any]]:
        s = URIRef(self.uri)
        triples: List[Tuple[URIRef, URIRef, Any]] = [
            (s, RDF.type, OPENLORE_CANON.AssetBinding),
            (s, OPENLORE_CANON.hasTimeline, URIRef(self.timeline_uri)),
            (s, OPENLORE_CANON.primPath, Literal(self.prim_path, datatype=XSD.string)),
            (s, OPENLORE_CANON.hasBlake3Hash, Literal(self.blake3_hash, datatype=XSD.string)),
        ]
        if self.entity_uri:
            triples.append((URIRef(self.entity_uri), OPENLORE_CANON.boundAsset, s))
        return triples


@dataclass
class NarrativeEntity:
    """Base entity inside the narrative lore graph."""

    uri: str
    name: str
    timeline_uri: str
    bound_asset_hash: Optional[str] = None
    prim_path: Optional[str] = None

    def to_triples(self) -> List[Tuple[URIRef, URIRef, Any]]:
        s = URIRef(self.uri)
        triples: List[Tuple[URIRef, URIRef, Any]] = [
            (s, RDF.type, OPENLORE_CANON.NarrativeEntity),
            (s, OPENLORE_CANON.hasTimeline, URIRef(self.timeline_uri)),
            (s, OPENLORE_CANON.name, Literal(self.name, datatype=XSD.string)),
            (s, RDFS.label, Literal(self.name, datatype=XSD.string)),
        ]
        if self.bound_asset_hash and self.prim_path:
            binding_uri = f"{self.uri}/binding"
            binding = AssetBindingRecord(
                uri=binding_uri,
                prim_path=self.prim_path,
                blake3_hash=self.bound_asset_hash,
                timeline_uri=self.timeline_uri,
                entity_uri=self.uri,
            )
            triples.extend(binding.to_triples())
        return triples


@dataclass
class CharacterEntity(NarrativeEntity):
    """Character model with spatiotemporal lifecycle bounds."""

    status: str = "active"
    birth_time: Optional[datetime] = None
    death_time: Optional[datetime] = None

    def to_triples(self) -> List[Tuple[URIRef, URIRef, Any]]:
        triples = super().to_triples()
        s = URIRef(self.uri)
        triples.append((s, RDF.type, OPENLORE_CANON.Character))
        triples.append((s, OPENLORE_CHAR.status, Literal(self.status, datatype=XSD.string)))

        if self.birth_time:
            triples.append((s, OPENLORE_CHAR.birthTime, Literal(self.birth_time.isoformat(), datatype=XSD.dateTime)))
        if self.death_time:
            triples.append((s, OPENLORE_CHAR.deathTime, Literal(self.death_time.isoformat(), datatype=XSD.dateTime)))
        return triples


@dataclass
class NarrativeEvent:
    """Historical or story event bound to a spatiotemporal timeline."""

    uri: str
    name: str
    timeline_uri: str
    timestamp: datetime
    participants: List[str] = field(default_factory=list)
    location: Optional[str] = None
    causes: List[str] = field(default_factory=list)
    diverges_at: Optional[str] = None

    def to_triples(self) -> List[Tuple[URIRef, URIRef, Any]]:
        s = URIRef(self.uri)
        triples: List[Tuple[URIRef, URIRef, Any]] = [
            (s, RDF.type, OPENLORE_CANON.NarrativeEvent),
            (s, OPENLORE_CANON.hasTimeline, URIRef(self.timeline_uri)),
            (s, OPENLORE_CANON.name, Literal(self.name, datatype=XSD.string)),
            (s, OPENLORE_CANON.timestamp, Literal(self.timestamp.isoformat(), datatype=XSD.dateTime)),
        ]
        for participant_uri in self.participants:
            triples.append((s, OPENLORE_CANON.hasParticipant, URIRef(participant_uri)))

        if self.location:
            triples.append((s, OPENLORE_CANON.location, Literal(self.location, datatype=XSD.string)))

        for cause_uri in self.causes:
            triples.append((s, OPENLORE_CANON.causes, URIRef(cause_uri)))

        if self.diverges_at:
            triples.append((s, OPENLORE_CANON.divergesAt, URIRef(self.diverges_at)))

        return triples

"""Narrative Ontology & Continuity Enforcement for OpenLore."""

from __future__ import annotations

from openlore.narrative.graph import NarrativeGraphClient
from openlore.narrative.ontology import (
    AssetBindingRecord,
    CharacterEntity,
    NarrativeEntity,
    NarrativeEvent,
    OPENLORE_CANON,
    OPENLORE_CHAR,
    OPENLORE_TIMELINE,
    TimelineModel,
)
from openlore.narrative.timeline import TimelineBranchManager
from openlore.narrative.validator import SHACLContinuityValidator, ValidationReport

__all__ = [
    "NarrativeGraphClient",
    "NarrativeEntity",
    "CharacterEntity",
    "NarrativeEvent",
    "AssetBindingRecord",
    "TimelineModel",
    "TimelineBranchManager",
    "SHACLContinuityValidator",
    "ValidationReport",
    "OPENLORE_CANON",
    "OPENLORE_CHAR",
    "OPENLORE_TIMELINE",
]

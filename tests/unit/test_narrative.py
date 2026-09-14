"""Unit tests for Narrative Ontology, SHACL Validation, and Timeline Branching."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from openlore.exceptions import ContinuityViolationError
from openlore.narrative.graph import NarrativeGraphClient
from openlore.narrative.ontology import (
    AssetBindingRecord,
    CharacterEntity,
    NarrativeEvent,
    TimelineModel,
)
from openlore.narrative.timeline import TimelineBranchManager
from openlore.narrative.validator import SHACLContinuityValidator


class TestNarrativeOntology(unittest.TestCase):
    def setUp(self) -> None:
        self.shapes_path = Path("./schemas/shacl/continuity_shapes.ttl")
        self.validator = SHACLContinuityValidator(self.shapes_path)
        self.graph_client = NarrativeGraphClient()
        self.timeline_mgr = TimelineBranchManager(self.graph_client)

    def test_timeline_model_creation(self) -> None:
        prime = self.timeline_mgr.create_prime_canon(
            timeline_uri="https://openlore.io/timelines/prime",
            name="Prime Canon",
        )
        self.assertTrue(prime.is_prime_canon)
        self.assertIsNone(prime.parent_timeline_uri)

        timelines = self.timeline_mgr.list_timelines()
        self.assertEqual(len(timelines), 1)
        self.assertEqual(timelines[0].uri, prime.uri)

    def test_insert_entities_and_sparql_query(self) -> None:
        prime = self.timeline_mgr.create_prime_canon()

        char = CharacterEntity(
            uri="https://openlore.io/characters/elara",
            name="Elara Vance",
            timeline_uri=prime.uri,
            status="active",
            birth_time=datetime(2140, 5, 12, tzinfo=timezone.utc),
            bound_asset_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            prim_path="/World/Characters/Elara",
        )
        self.graph_client.insert_character(char)

        event = NarrativeEvent(
            uri="https://openlore.io/events/battle_of_veridia",
            name="Battle of Veridia",
            timeline_uri=prime.uri,
            timestamp=datetime(2165, 10, 4, 14, 0, tzinfo=timezone.utc),
            participants=[char.uri],
            location="Veridia Prime Sector 4",
        )
        self.graph_client.insert_event(event)

        # Query lifecycles via SPARQL
        lifecycles = self.graph_client.get_character_lifecycles(prime.uri)
        self.assertEqual(len(lifecycles), 1)
        self.assertEqual(lifecycles[0]["name"], "Elara Vance")
        self.assertEqual(lifecycles[0]["status"], "active")

        # Query events via SPARQL
        events = self.graph_client.get_timeline_events(prime.uri)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["name"], "Battle of Veridia")

    def test_shacl_validation_passes_valid_lore(self) -> None:
        prime = self.timeline_mgr.create_prime_canon()
        char = CharacterEntity(
            uri="https://openlore.io/characters/koren",
            name="Commander Koren",
            timeline_uri=prime.uri,
            status="active",
            birth_time=datetime(2130, 1, 1, tzinfo=timezone.utc),
            bound_asset_hash="a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90",
            prim_path="/World/Characters/Koren",
        )
        self.graph_client.insert_character(char)

        event = NarrativeEvent(
            uri="https://openlore.io/events/station_breach",
            name="Station Breach",
            timeline_uri=prime.uri,
            timestamp=datetime(2155, 6, 15, tzinfo=timezone.utc),
            participants=[char.uri],
        )
        self.graph_client.insert_event(event)

        # Validate graph
        context = self.graph_client.get_timeline_context(prime.uri)
        report = self.validator.validate_graph(context)
        self.assertTrue(report.conforms, f"Validation failed with: {report.violations}")

    def test_shacl_validation_fails_invalid_asset_hash(self) -> None:
        prime = self.timeline_mgr.create_prime_canon()
        invalid_binding = AssetBindingRecord(
            uri="https://openlore.io/bindings/invalid_01",
            prim_path="/World/Characters/Villain",
            blake3_hash="invalid_hash_not_64_hex",  # Invalid BLAKE3 hash
            timeline_uri=prime.uri,
        )
        context = self.graph_client.get_timeline_context(prime.uri)
        for s, p, o in invalid_binding.to_triples():
            context.add((s, p, o))

        report = self.validator.validate_graph(context)
        self.assertFalse(report.conforms)
        self.assertTrue(any("BLAKE3" in v or "pattern" in v.lower() or "Constraint" in v for v in report.violations))

        with self.assertRaises(ContinuityViolationError):
            self.validator.assert_valid(context)

    def test_lifecycle_temporal_violation_detection(self) -> None:
        prime = self.timeline_mgr.create_prime_canon()
        char = CharacterEntity(
            uri="https://openlore.io/characters/mortal_hero",
            name="Mortal Hero",
            timeline_uri=prime.uri,
            status="deceased",
            birth_time=datetime(2100, 1, 1, tzinfo=timezone.utc),
            death_time=datetime(2150, 1, 1, tzinfo=timezone.utc),
        )
        self.graph_client.insert_character(char)

        # Event occurs in 2160 (10 years AFTER death)
        posthumous_event = NarrativeEvent(
            uri="https://openlore.io/events/ghost_mission",
            name="Impossible Mission",
            timeline_uri=prime.uri,
            timestamp=datetime(2160, 6, 1, tzinfo=timezone.utc),
            participants=[char.uri],
        )
        self.graph_client.insert_event(posthumous_event)

        context = self.graph_client.get_timeline_context(prime.uri)
        report = self.validator.validate_graph(context)
        self.assertFalse(report.conforms)
        self.assertTrue(any("occurs after death" in v for v in report.violations))

    def test_timeline_branching_multiverse_isolation(self) -> None:
        prime = self.timeline_mgr.create_prime_canon()
        char_prime = CharacterEntity(
            uri="https://openlore.io/characters/original_hero",
            name="Original Hero",
            timeline_uri=prime.uri,
            status="active",
        )
        self.graph_client.insert_character(char_prime)

        # Branch into alternate continuity (spin-off)
        alt_branch = self.timeline_mgr.branch_timeline(
            source_timeline_uri=prime.uri,
            new_timeline_slug="alternate_timeline_omega",
            new_timeline_name="Timeline Omega Spin-off",
        )

        # Add spin-off character to alternate branch ONLY
        spinoff_char = CharacterEntity(
            uri="https://openlore.io/characters/cyber_clone",
            name="Cyber Clone",
            timeline_uri=alt_branch.uri,
            status="active",
        )
        self.graph_client.insert_character(spinoff_char)

        # Verify spin-off character exists in alternate branch
        alt_characters = self.graph_client.get_character_lifecycles(alt_branch.uri)
        alt_names = [c["name"] for c in alt_characters]
        self.assertIn("Cyber Clone", alt_names)

        # STRICT MULTIVERSE ISOLATION: verify spin-off character does NOT exist in Prime Canon
        prime_characters = self.graph_client.get_character_lifecycles(prime.uri)
        prime_names = [c["name"] for c in prime_characters]
        self.assertNotIn("Cyber Clone", prime_names)
        self.assertIn("Original Hero", prime_names)

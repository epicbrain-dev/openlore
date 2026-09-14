"""Unit tests for SPARQL Graph RAG Narrative Assistant."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from openlore.narrative.graph import NarrativeGraphClient
from openlore.narrative.ontology import (
    CharacterEntity,
    NarrativeEvent,
    TimelineModel,
)
from openlore.narrative.rag import GraphRAGNarrativeAssistant


class TestGraphRAGNarrativeAssistant(unittest.TestCase):
    def setUp(self) -> None:
        self.client = NarrativeGraphClient()
        self.timeline_uri = "https://openlore.io/timelines/prime-canon"
        self.timeline = TimelineModel(
            uri=self.timeline_uri,
            name="Prime Canon Timeline",
            is_prime_canon=True,
        )
        self.client.insert_timeline(self.timeline)

        # Character 1: Hero Commander (born 2140-01-01, active)
        self.hero = CharacterEntity(
            uri="https://openlore.io/characters/HeroCommander",
            name="Hero Commander",
            timeline_uri=self.timeline_uri,
            status="Active",
            birth_time=datetime(2140, 1, 1, tzinfo=timezone.utc),
            death_time=None,
        )
        self.client.insert_character(self.hero)

        # Character 2: Fallen Knight (born 2100-01-01, died 2130-01-01)
        self.knight = CharacterEntity(
            uri="https://openlore.io/characters/FallenKnight",
            name="Fallen Knight",
            timeline_uri=self.timeline_uri,
            status="Deceased",
            birth_time=datetime(2100, 1, 1, tzinfo=timezone.utc),
            death_time=datetime(2130, 1, 1, tzinfo=timezone.utc),
        )
        self.client.insert_character(self.knight)

        # Event: Battle of Nova in 2145 (Hero Commander participates)
        self.event1 = NarrativeEvent(
            uri="https://openlore.io/events/BattleOfNova",
            name="Battle of Nova",
            timeline_uri=self.timeline_uri,
            timestamp=datetime(2145, 6, 1, tzinfo=timezone.utc),
            location="Nova Prime",
            participants=[self.hero.uri],
        )
        self.client.insert_event(self.event1)

        self.assistant = GraphRAGNarrativeAssistant(graph_client=self.client)

    def test_query_characters(self) -> None:
        resp = self.assistant.query("What characters are in Prime Canon?")
        self.assertIn("Hero Commander", resp.answer)
        self.assertIn("Fallen Knight", resp.answer)
        self.assertEqual(resp.continuity_status, "CANON_VALID")
        self.assertTrue(len(resp.retrieved_triples) >= 2)
        self.assertTrue(len(resp.reasoning_path) > 0)

    def test_query_events(self) -> None:
        resp = self.assistant.query("What events take place?")
        self.assertIn("Battle of Nova", resp.answer)
        self.assertEqual(resp.continuity_status, "CANON_VALID")

    def test_canon_audit_consistent(self) -> None:
        resp = self.assistant.query("Audit timeline for temporal paradoxes")
        self.assertEqual(resp.continuity_status, "CANON_VALID")
        self.assertEqual(len(resp.violations), 0)
        self.assertIn("Audit Complete", resp.answer)

    def test_canon_audit_detects_post_mortem_violation(self) -> None:
        # Create an impossible event where Fallen Knight (died 2130) participates in 2150
        paradox_event = NarrativeEvent(
            uri="https://openlore.io/events/GhostBattle",
            name="Ghost Battle",
            timeline_uri=self.timeline_uri,
            timestamp=datetime(2150, 1, 1, tzinfo=timezone.utc),
            location="Dark Nebula",
            participants=[self.knight.uri],
        )
        self.client.insert_event(paradox_event)

        resp = self.assistant.query("Check continuity and audit timeline for violations")
        self.assertEqual(resp.continuity_status, "CONTRADICTION_DETECTED")
        self.assertTrue(len(resp.violations) >= 1)
        self.assertTrue(any("Post-Mortem Participation" in v for v in resp.violations))
        self.assertIn("Fallen Knight", resp.answer)

    def test_query_timelines(self) -> None:
        resp = self.assistant.query("List all timelines and branches")
        self.assertIn("Prime Canon", resp.answer)
        self.assertEqual(resp.continuity_status, "CANON_VALID")

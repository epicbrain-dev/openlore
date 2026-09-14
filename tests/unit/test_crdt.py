"""Unit tests for Vector Clocks, Sparse CRDTs, and Kafka Event Streaming."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from openlore.collaboration.crdt import (
    CRDTPartialMutation,
    CRDTSceneReplica,
    LWWRegister,
    ORSet,
)
from openlore.collaboration.kafka_stream import KafkaEventStream
from openlore.collaboration.vector_clock import VectorClock
from openlore.exceptions import SecurityPolicyError


class TestVectorClock(unittest.TestCase):
    def test_vector_clock_causality_and_merge(self) -> None:
        v1 = VectorClock()
        v1.increment("london_studio")
        self.assertEqual(v1.get("london_studio"), 1)

        v2 = VectorClock()
        v2.increment("la_studio")

        # Concurrency
        self.assertTrue(v1.is_concurrent(v2))
        self.assertFalse(v1.dominates(v2))
        self.assertFalse(v2.dominates(v1))

        # Merging
        merged = v1.merge(v2)
        self.assertEqual(merged.get("london_studio"), 1)
        self.assertEqual(merged.get("la_studio"), 1)

        # Domination
        self.assertTrue(merged.dominates(v1))
        self.assertTrue(merged.dominates(v2))
        self.assertFalse(v1.dominates(merged))

    def test_vector_clock_serialization(self) -> None:
        v = VectorClock({"london": 3, "la": 5, "tokyo": 2})
        d = v.to_dict()
        v_copy = VectorClock.from_dict(d)
        self.assertTrue(v.equals(v_copy))


class TestCRDT(unittest.TestCase):
    def test_lww_register_causal_update(self) -> None:
        c1 = VectorClock({"london": 1})
        t1 = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
        reg = LWWRegister(value="red", clock=c1, timestamp=t1, origin_studio="london")

        # Causal successor
        c2 = VectorClock({"london": 2})
        t2 = datetime(2026, 1, 1, 10, 5, tzinfo=timezone.utc)
        updated = reg.update(new_value="blue", new_clock=c2, new_timestamp=t2, new_studio="london")
        self.assertTrue(updated)
        self.assertEqual(reg.value, "blue")

        # Causal obsolete update should be rejected
        c_old = VectorClock({"london": 1})
        rejected = reg.update(new_value="green", new_clock=c_old, new_timestamp=t1, new_studio="london")
        self.assertFalse(rejected)
        self.assertEqual(reg.value, "blue")

    def test_lww_register_concurrent_tie_breaking(self) -> None:
        c_london = VectorClock({"london": 1, "la": 0})
        t_london = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        reg = LWWRegister(value=10.0, clock=c_london, timestamp=t_london, origin_studio="london")

        # Concurrent update from LA with newer timestamp wins
        c_la = VectorClock({"london": 0, "la": 1})
        t_la_newer = datetime(2026, 1, 1, 12, 1, tzinfo=timezone.utc)
        updated = reg.update(new_value=25.0, new_clock=c_la, new_timestamp=t_la_newer, new_studio="la")
        self.assertTrue(updated)
        self.assertEqual(reg.value, 25.0)

        # Concurrent update from Tokyo with identical timestamp: lexicographical studio ID wins
        c_tokyo = VectorClock({"tokyo": 1})
        # "tokyo" > "la" alphabetically -> tokyo wins
        updated_tokyo = reg.update(new_value=50.0, new_clock=c_tokyo, new_timestamp=t_la_newer, new_studio="tokyo")
        self.assertTrue(updated_tokyo)
        self.assertEqual(reg.value, 50.0)

    def test_or_set_add_remove_and_merge(self) -> None:
        s1: ORSet[str] = ORSet()
        s2: ORSet[str] = ORSet()

        s1.add("mesh_lod0")
        s1.add("mesh_lod1")

        s2.add("mesh_lod2")

        # Merge sets
        s1.merge(s2)
        self.assertEqual(s1.read(), {"mesh_lod0", "mesh_lod1", "mesh_lod2"})

        # Remove from set
        s1.remove("mesh_lod1")
        self.assertEqual(s1.read(), {"mesh_lod0", "mesh_lod2"})


class TestKafkaStream(unittest.TestCase):
    def test_kafka_stream_publish_and_subscribe(self) -> None:
        stream = KafkaEventStream(stage_topic="test.topic.mutations", use_memory_bus=True)

        received_mutations: list[CRDTPartialMutation] = []
        stream.subscribe(lambda m: received_mutations.append(m))

        mut = CRDTPartialMutation(
            mutation_id="mut_001",
            stage_uri="openlore://stages/hero.usda",
            prim_path="/World/Hero",
            attribute_name="xformOp:translate",
            value=[1.0, 2.0, 3.0],
            clock=VectorClock({"studio_a": 1}),
            origin_studio="studio_a",
        )

        stream.publish_mutation(mut)
        self.assertEqual(len(received_mutations), 1)
        self.assertEqual(received_mutations[0].mutation_id, "mut_001")
        self.assertEqual(received_mutations[0].value, [1.0, 2.0, 3.0])

    def test_heavy_binary_payload_rejection(self) -> None:
        stream = KafkaEventStream(stage_topic="test.topic.rejection", use_memory_bus=True)

        # Attempt to inject raw 100KB binary buffer directly into event stream
        heavy_binary = b"RAW_3D_POINT_CACHE_DATA..." * 5000  # ~130 KB
        illegal_mutation = CRDTPartialMutation(
            mutation_id="mut_illegal",
            stage_uri="openlore://stages/hero.usda",
            prim_path="/World/Hero/HeavyMesh",
            attribute_name="points",
            value=heavy_binary,
            clock=VectorClock({"studio_a": 1}),
            origin_studio="studio_a",
        )

        with self.assertRaises(SecurityPolicyError):
            stream.publish_mutation(illegal_mutation)

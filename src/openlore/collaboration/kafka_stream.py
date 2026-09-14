"""Apache Kafka append-only event stream producer and consumer with binary filtering."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional

from openlore.collaboration.crdt import CRDTPartialMutation
from openlore.exceptions import SecurityPolicyError

try:
    from confluent_kafka import Consumer, KafkaError, Producer
    HAS_CONFLUENT = True
except ImportError:
    HAS_CONFLUENT = False


class _InMemoryEventBus:
    """Shared in-memory broadcast bus for offline simulation and isolated testing."""

    _topics: Dict[str, List[Callable[[CRDTPartialMutation], None]]] = defaultdict(list)
    _history: Dict[str, List[CRDTPartialMutation]] = defaultdict(list)

    @classmethod
    def publish(cls, topic: str, mutation: CRDTPartialMutation) -> None:
        cls._history[topic].append(mutation)
        for listener in list(cls._topics[topic]):
            listener(mutation)

    @classmethod
    def subscribe(cls, topic: str, listener: Callable[[CRDTPartialMutation], None]) -> None:
        cls._topics[topic].append(listener)

    @classmethod
    def clear(cls, topic: Optional[str] = None) -> None:
        if topic:
            cls._topics[topic].clear()
            cls._history[topic].clear()
        else:
            cls._topics.clear()
            cls._history.clear()


class KafkaEventStream:
    """Handles event streaming for collaborative USD scene mutations.

    Enforces that large binary assets (meshes, point caches) NEVER enter the event stream.
    Only sparse CRDT attribute updates and BLAKE3 hash references are permitted.
    """

    MAX_PAYLOAD_BYTES: int = 65536  # 64 KB ceiling

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        stage_topic: str = "openlore.stage.mutations",
        use_memory_bus: bool = False,
    ) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.stage_topic = stage_topic
        self.use_memory_bus = use_memory_bus or not HAS_CONFLUENT
        self._producer: Optional[Any] = None
        self._consumer: Optional[Any] = None
        self._subscribers: List[Callable[[CRDTPartialMutation], None]] = []

        if not self.use_memory_bus and HAS_CONFLUENT:
            try:
                self._producer = Producer({"bootstrap.servers": self.bootstrap_servers})
            except Exception:
                # Fallback to in-memory bus if broker is unreachable
                self.use_memory_bus = True

    def _enforce_payload_policy(self, mutation: CRDTPartialMutation) -> None:
        """Reject binary payloads that exceed the 64KB threshold."""
        val = mutation.value
        size = 0
        if isinstance(val, (bytes, bytearray, memoryview)):
            size = len(val)
        elif isinstance(val, str):
            size = len(val.encode("utf-8"))
        elif isinstance(val, (list, dict)):
            size = len(json.dumps(val).encode("utf-8"))

        if size > self.MAX_PAYLOAD_BYTES:
            raise SecurityPolicyError(
                f"Binary payload size ({size} bytes) exceeds maximum allowable threshold ({self.MAX_PAYLOAD_BYTES} bytes). "
                f"Heavy geometry and point caches must be stored in CAS and referenced via BLAKE3 hash."
            )

    def publish_mutation(self, mutation: CRDTPartialMutation) -> None:
        """Publish a sparse CRDT scene mutation to the event stream."""
        self._enforce_payload_policy(mutation)

        if self.use_memory_bus:
            _InMemoryEventBus.publish(self.stage_topic, mutation)
            return

        if self._producer:
            payload = json.dumps(mutation.to_dict()).encode("utf-8")
            key = f"{mutation.stage_uri}:{mutation.prim_path}".encode("utf-8")
            self._producer.produce(self.stage_topic, key=key, value=payload)
            self._producer.poll(0)

    def subscribe(self, on_mutation_received: Callable[[CRDTPartialMutation], None]) -> None:
        """Subscribe to the stage event stream."""
        self._subscribers.append(on_mutation_received)
        if self.use_memory_bus:
            _InMemoryEventBus.subscribe(self.stage_topic, on_mutation_received)

    def flush(self, timeout: float = 1.0) -> None:
        """Flush outstanding messages."""
        if self._producer:
            self._producer.flush(timeout)

    def close(self) -> None:
        """Close producer and consumer connections."""
        self.flush()
        self._subscribers.clear()

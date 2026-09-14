"""Edge Resolver daemon with shadow buffering and causal state convergence."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

from openlore.collaboration.crdt import CRDTPartialMutation, CRDTSceneReplica
from openlore.collaboration.kafka_stream import KafkaEventStream
from openlore.collaboration.vector_clock import VectorClock


class EdgeResolverDaemon:
    """Local edge resolver managing shadow buffering during studio network severances."""

    def __init__(
        self,
        studio_id: str,
        stage_uri: str,
        event_stream: KafkaEventStream,
    ) -> None:
        self.studio_id = studio_id
        self.stage_uri = stage_uri
        self.event_stream = event_stream
        self.local_clock = VectorClock({self.studio_id: 0})
        self.replica = CRDTSceneReplica(stage_uri=self.stage_uri)
        self._shadow_buffer: List[CRDTPartialMutation] = []
        self._is_online: bool = True

        # Subscribe to remote modifications
        self.event_stream.subscribe(self.handle_remote_mutation)

    @property
    def is_online(self) -> bool:
        """Check current network connectivity state."""
        return self._is_online

    @property
    def shadow_buffer_size(self) -> int:
        """Number of uncommitted edits waiting in local shadow buffer."""
        return len(self._shadow_buffer)

    def set_connectivity(self, online: bool) -> None:
        """Switch connectivity state and trigger automatic causal convergence upon reconnect."""
        was_offline = not self._is_online
        self._is_online = online
        if was_offline and self._is_online and self._shadow_buffer:
            self.reconcile_causal_convergence()

    def record_local_edit(
        self,
        prim_path: str,
        attribute_name: str,
        value: Any,
    ) -> CRDTPartialMutation:
        """Record a local artist edit. Buffers in shadow storage if offline."""
        self.local_clock.increment(self.studio_id)

        mutation = CRDTPartialMutation(
            mutation_id=uuid.uuid4().hex,
            stage_uri=self.stage_uri,
            prim_path=prim_path,
            attribute_name=attribute_name,
            value=value,
            clock=self.local_clock.copy(),
            origin_studio=self.studio_id,
            timestamp=datetime.now(timezone.utc),
        )

        # Apply locally immediately for optimistic interactive feedback
        self.replica.apply_mutation(mutation)

        if self._is_online:
            self.event_stream.publish_mutation(mutation)
        else:
            self._shadow_buffer.append(mutation)

        return mutation

    def handle_remote_mutation(self, mutation: CRDTPartialMutation) -> bool:
        """Handle incoming mutation from a remote studio."""
        # Ignore self-published events
        if mutation.origin_studio == self.studio_id:
            return False

        # Merge remote clock to advance local causal state
        self.local_clock = self.local_clock.merge(mutation.clock)

        # Apply to local replica using deterministic CRDT rules
        return self.replica.apply_mutation(mutation)

    def reconcile_causal_convergence(self) -> int:
        """Flush local shadow buffer to event stream and converge causal state."""
        count = len(self._shadow_buffer)
        if count == 0:
            return 0

        # Publish all buffered mutations in causal order
        for mutation in self._shadow_buffer:
            self.event_stream.publish_mutation(mutation)

        self._shadow_buffer.clear()
        return count

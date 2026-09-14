"""Conflict-Free Replicated Data Types (CRDTs) for sparse scene mutations."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, Set, Tuple, TypeVar

from openlore.collaboration.vector_clock import VectorClock

T = TypeVar("T")


@dataclass
class CRDTPartialMutation:
    """Sparse replicated edit representing a single USD prim attribute change."""

    mutation_id: str
    stage_uri: str
    prim_path: str
    attribute_name: str
    value: Any
    clock: VectorClock
    origin_studio: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize mutation to JSON-compatible dictionary."""
        return {
            "mutation_id": self.mutation_id,
            "stage_uri": self.stage_uri,
            "prim_path": self.prim_path,
            "attribute_name": self.attribute_name,
            "value": self.value,
            "clock": self.clock.to_dict(),
            "origin_studio": self.origin_studio,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CRDTPartialMutation:
        """Deserialize mutation from dictionary."""
        return cls(
            mutation_id=data["mutation_id"],
            stage_uri=data["stage_uri"],
            prim_path=data["prim_path"],
            attribute_name=data["attribute_name"],
            value=data["value"],
            clock=VectorClock.from_dict(data["clock"]),
            origin_studio=data["origin_studio"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


@dataclass
class LWWRegister(Generic[T]):
    """Last-Write-Wins Register backed by a Vector Clock and deterministic tie-breaking.

    Precedence order:
        1. Causal dominance (VectorClock.dominates).
        2. Timestamp (newer wall-clock wins if concurrent).
        3. Lexicographical studio node ID tie-breaker if timestamps collide.
    """

    value: T
    clock: VectorClock
    timestamp: datetime
    origin_studio: str

    def update(
        self,
        new_value: T,
        new_clock: VectorClock,
        new_timestamp: datetime,
        new_studio: str,
    ) -> bool:
        """Attempt to update register value based on deterministic CRDT causal rules."""
        wins = False

        if new_clock.dominates(self.clock):
            wins = True
        elif self.clock.dominates(new_clock):
            wins = False
        else:
            # Concurrent edit conflict
            if new_timestamp > self.timestamp:
                wins = True
            elif new_timestamp < self.timestamp:
                wins = False
            else:
                # Timestamps equal: deterministic studio ID tie-breaker
                wins = new_studio > self.origin_studio

        # Always merge clocks to preserve causal context
        self.clock = self.clock.merge(new_clock)

        if wins:
            self.value = new_value
            self.timestamp = new_timestamp
            self.origin_studio = new_studio
            return True

        return False


class ORSet(Generic[T]):
    """Observed-Remove Set (OR-Set) allowing concurrent element addition and deletion."""

    def __init__(self) -> None:
        # Maps element to set of unique addition tokens
        self._entries: Dict[T, Set[str]] = {}

    def add(self, element: T) -> str:
        """Add an element generating a unique observation token."""
        token = uuid.uuid4().hex
        if element not in self._entries:
            self._entries[element] = set()
        self._entries[element].add(token)
        return token

    def remove(self, element: T) -> None:
        """Remove element by clearing all currently observed tokens."""
        if element in self._entries:
            self._entries[element].clear()

    def read(self) -> Set[T]:
        """Read active elements with at least one observed token."""
        return {elem for elem, tokens in self._entries.items() if len(tokens) > 0}

    def merge(self, other: ORSet[T]) -> None:
        """Merge with another OR-Set by taking union of observed tokens."""
        for elem, tokens in other._entries.items():
            if elem not in self._entries:
                self._entries[elem] = set()
            self._entries[elem].update(tokens)


class CRDTSceneReplica:
    """Local replica managing OpenUSD scene prim attributes via CRDT registers."""

    def __init__(self, stage_uri: str) -> None:
        self.stage_uri = stage_uri
        # prim_path -> attribute_name -> LWWRegister
        self._attributes: Dict[str, Dict[str, LWWRegister[Any]]] = {}

    def apply_mutation(self, mutation: CRDTPartialMutation) -> bool:
        """Apply an incoming CRDT mutation. Returns True if attribute value changed."""
        if mutation.prim_path not in self._attributes:
            self._attributes[mutation.prim_path] = {}

        prim_attrs = self._attributes[mutation.prim_path]

        if mutation.attribute_name not in prim_attrs:
            prim_attrs[mutation.attribute_name] = LWWRegister(
                value=mutation.value,
                clock=mutation.clock.copy(),
                timestamp=mutation.timestamp,
                origin_studio=mutation.origin_studio,
            )
            return True

        register = prim_attrs[mutation.attribute_name]
        return register.update(
            new_value=mutation.value,
            new_clock=mutation.clock,
            new_timestamp=mutation.timestamp,
            new_studio=mutation.origin_studio,
        )

    def get_attribute_value(self, prim_path: str, attribute_name: str) -> Any:
        """Retrieve the current resolved value of an attribute."""
        prim_attrs = self._attributes.get(prim_path)
        if prim_attrs and attribute_name in prim_attrs:
            return prim_attrs[attribute_name].value
        return None

    def get_all_attributes(self, prim_path: str) -> Dict[str, Any]:
        """Get all resolved attributes for a Prim."""
        prim_attrs = self._attributes.get(prim_path, {})
        return {k: reg.value for k, reg in prim_attrs.items()}

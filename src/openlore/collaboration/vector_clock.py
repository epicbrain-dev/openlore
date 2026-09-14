"""Vector Clocks for deterministic causal ordering across distributed studios."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class VectorClock:
    """Vector clock representation across distributed studio nodes."""

    clock_map: Dict[str, int] = field(default_factory=dict)

    def get(self, node_id: str) -> int:
        """Get the counter for a given studio node."""
        return self.clock_map.get(node_id, 0)

    def increment(self, node_id: str) -> None:
        """Increment the counter for a specific studio node."""
        self.clock_map[node_id] = self.get(node_id) + 1

    def merge(self, other: VectorClock) -> VectorClock:
        """Merge this clock with another vector clock taking pairwise maximums."""
        all_keys = set(self.clock_map.keys()).union(other.clock_map.keys())
        merged = {k: max(self.get(k), other.get(k)) for k in all_keys}
        return VectorClock(clock_map=merged)

    def dominates(self, other: VectorClock) -> bool:
        """Check if this clock strictly causally dominates (is newer than) another clock.

        A clock A dominates B iff for all nodes k, A[k] >= B[k], and for at least one node j, A[j] > B[j].
        """
        all_keys = set(self.clock_map.keys()).union(other.clock_map.keys())
        greater_or_equal = all(self.get(k) >= other.get(k) for k in all_keys)
        strictly_greater = any(self.get(k) > other.get(k) for k in all_keys)
        return greater_or_equal and strictly_greater

    def is_concurrent(self, other: VectorClock) -> bool:
        """Check if two clocks are concurrent (neither causally dominates the other)."""
        if self.equals(other):
            return False
        return not self.dominates(other) and not other.dominates(self)

    def equals(self, other: VectorClock) -> bool:
        """Check if two vector clocks have identical counts across all nodes."""
        all_keys = set(self.clock_map.keys()).union(other.clock_map.keys())
        return all(self.get(k) == other.get(k) for k in all_keys)

    def copy(self) -> VectorClock:
        """Create a deep copy of this vector clock."""
        return VectorClock(clock_map=dict(self.clock_map))

    def to_dict(self) -> Dict[str, int]:
        """Serialize to dictionary."""
        return dict(self.clock_map)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> VectorClock:
        """Deserialize from dictionary."""
        return cls(clock_map={str(k): int(v) for k, v in data.items()})

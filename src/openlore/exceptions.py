"""Domain exceptions for the OpenLore platform."""

from __future__ import annotations


class OpenLoreError(Exception):
    """Base exception for all OpenLore errors."""


class CASObjectNotFoundError(OpenLoreError):
    """Raised when an object cannot be located in the Content-Addressed Storage repository."""


class HashMismatchError(OpenLoreError):
    """Raised when cryptographic BLAKE3 checksum verification fails."""


class ContinuityViolationError(OpenLoreError):
    """Raised when an edit violates narrative OWL 2 constraints or SHACL rules."""


class CausalOrderingError(OpenLoreError):
    """Raised when vector clocks or CRDT event ordering encounters a causal divergence."""


class StagePromotionError(OpenLoreError):
    """Raised when stage promotion fails pre-flight linting or optimistic locking gates."""


class SecurityPolicyError(OpenLoreError):
    """Raised when an action violates eBPF or partner isolation enclaves."""


class LiveLinkBridgeError(OpenLoreError):
    """Raised when Unreal Engine Live Link connection, encoding, or handshake fails."""

"""Security utilities for path validation and sanitization against CWE-22 path traversal."""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import Iterable, Optional


def get_default_safe_roots() -> list[str]:
    """Return default canonical directory boundaries for safe file operations."""
    roots = [
        os.path.realpath(os.path.abspath(str(Path.cwd()))),
        os.path.realpath(os.path.abspath(tempfile.gettempdir())),
    ]
    return roots


def validate_safe_path(
    untrusted_path: str | Path,
    allowed_roots: Optional[Iterable[str | Path]] = None,
) -> Path:
    """Normalize and validate a path against allowed root boundaries to prevent path traversal (CWE-22).

    Canonicalizes the path via os.path.realpath(os.path.abspath(...)) and verifies that the resulting
    path is strictly contained within at least one allowed root directory.

    Raises ValueError if untrusted_path escapes allowed boundaries or is empty.
    """
    raw_str = str(untrusted_path).strip()
    if not raw_str:
        raise ValueError("Forbidden: Empty path provided")

    # Step 1: Normalization (triggers CodeQL OsPathRealpathCall / OsPathAbspathCall)
    norm_path = os.path.realpath(os.path.abspath(raw_str))

    # Step 2: Build canonical root prefix list with explicit directory separators
    roots = list(allowed_roots) if allowed_roots is not None else get_default_safe_roots()

    for root in roots:
        root_str = os.path.realpath(os.path.abspath(str(root)))
        root_prefix = root_str if root_str.endswith(os.sep) else (root_str + os.sep)
        # Direct startswith check provides CodeQL SafeAccessCheck barrier guard
        if norm_path.startswith(root_prefix):
            return Path(norm_path)
        if norm_path == root_str:
            return Path(root_str)

    raise ValueError(
        f"Forbidden: Path traversal detected or path outside allowed boundaries: {untrusted_path}"
    )


def is_safe_path(
    untrusted_path: str | Path,
    allowed_roots: Optional[Iterable[str | Path]] = None,
) -> bool:
    """Check if untrusted_path resolves safely within allowed boundaries without throwing."""
    try:
        validate_safe_path(untrusted_path, allowed_roots)
        return True
    except (ValueError, TypeError):
        return False


def sanitize_filename(name: str, fallback: str = "asset") -> str:
    """Sanitize a filename stem to prevent path injection via manipulated names."""
    trimmed = str(name).strip().rstrip("/\\")
    base = os.path.basename(trimmed)
    clean = re.sub(r"[^A-Za-z0-9_\-\.]", "_", base).strip("._")
    return clean if clean else fallback

"""Unit tests for path safety and CWE-22 path traversal prevention."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from openlore.core.path_safety import (
    get_default_safe_roots,
    is_safe_path,
    sanitize_filename,
    validate_safe_path,
)


class TestPathSafety(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name).resolve()
        self.allowed_roots = [
            str(self.base_dir),
            str(Path.cwd().resolve()),
        ]

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_valid_contained_path(self) -> None:
        sub_file = self.base_dir / "assets" / "character.usda"
        sub_file.parent.mkdir(parents=True, exist_ok=True)
        sub_file.touch()

        validated = validate_safe_path(sub_file, allowed_roots=self.allowed_roots)
        self.assertEqual(validated, sub_file)
        self.assertTrue(is_safe_path(sub_file, allowed_roots=self.allowed_roots))

    def test_valid_root_directory(self) -> None:
        validated = validate_safe_path(self.base_dir, allowed_roots=self.allowed_roots)
        self.assertEqual(validated, self.base_dir)

    def test_reject_dot_dot_traversal(self) -> None:
        traversal_path = self.base_dir / ".." / ".." / "etc" / "passwd"
        with self.assertRaises(ValueError) as ctx:
            validate_safe_path(traversal_path, allowed_roots=[str(self.base_dir)])
        self.assertIn("Forbidden", str(ctx.exception))
        self.assertFalse(is_safe_path(traversal_path, allowed_roots=[str(self.base_dir)]))

    def test_reject_absolute_path_outside_roots(self) -> None:
        system_path = "/etc/shadow"
        with self.assertRaises(ValueError) as ctx:
            validate_safe_path(system_path, allowed_roots=[str(self.base_dir)])
        self.assertIn("Forbidden", str(ctx.exception))
        self.assertFalse(is_safe_path(system_path, allowed_roots=[str(self.base_dir)]))

    def test_reject_partial_path_traversal_prefix_bypass(self) -> None:
        # If allowed root is /tmp/dir, /tmp/dir_evil must be rejected!
        allowed = self.base_dir / "secure_zone"
        allowed.mkdir(parents=True, exist_ok=True)

        evil_path = self.base_dir / "secure_zone_unauthorized" / "leak.txt"
        with self.assertRaises(ValueError):
            validate_safe_path(evil_path, allowed_roots=[str(allowed)])
        self.assertFalse(is_safe_path(evil_path, allowed_roots=[str(allowed)]))

    def test_reject_empty_path(self) -> None:
        with self.assertRaises(ValueError):
            validate_safe_path("", allowed_roots=self.allowed_roots)
        self.assertFalse(is_safe_path("", allowed_roots=self.allowed_roots))

    def test_default_safe_roots(self) -> None:
        roots = get_default_safe_roots()
        self.assertTrue(len(roots) >= 2)
        self.assertIn(os.path.realpath(os.path.abspath(str(Path.cwd()))), roots)

    def test_sanitize_filename(self) -> None:
        self.assertEqual(sanitize_filename("valid_name_01.usda"), "valid_name_01.usda")
        self.assertEqual(sanitize_filename("../../etc/passwd"), "passwd")
        self.assertEqual(sanitize_filename("shot_01;rm -rf /"), "shot_01_rm_-rf")
        self.assertEqual(sanitize_filename(""), "asset")


if __name__ == "__main__":
    unittest.main()

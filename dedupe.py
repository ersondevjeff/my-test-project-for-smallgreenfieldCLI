#!/usr/bin/env python3
"""CLI tool to find duplicate files in a folder by SHA-256 hash."""

import argparse
import hashlib
import os
import sys
import unittest
import tempfile
from collections import defaultdict


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def find_duplicates(folder: str) -> dict[str, list[str]]:
    """Return a mapping of sha256 -> [paths] for hashes with more than one file."""
    buckets: dict[str, list[str]] = defaultdict(list)
    for dirpath, _, filenames in os.walk(folder):
        for name in filenames:
            path = os.path.join(dirpath, name)
            try:
                buckets[sha256(path)].append(path)
            except OSError:
                pass
    return {h: paths for h, paths in buckets.items() if len(paths) > 1}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Find duplicate files by SHA-256.")
    parser.add_argument("folder", help="Folder to scan")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List duplicates without deleting anything (default behaviour; flag is for explicitness)",
    )
    args = parser.parse_args(argv)

    if not os.path.isdir(args.folder):
        print(f"Error: '{args.folder}' is not a directory", file=sys.stderr)
        return 1

    duplicates = find_duplicates(args.folder)

    if not duplicates:
        print("No duplicate files found.")
        return 0

    for digest, paths in duplicates.items():
        print(f"\nSHA-256: {digest}")
        for p in paths:
            print(f"  {p}")

    if args.dry_run:
        print("\n[dry-run] No files were deleted.")

    return 0


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDedupe(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _write(self, name: str, content: bytes) -> str:
        path = os.path.join(self.tmp, name)
        with open(path, "wb") as f:
            f.write(content)
        return path

    def test_no_duplicates(self):
        self._write("a.txt", b"hello")
        self._write("b.txt", b"world")
        self.assertEqual(find_duplicates(self.tmp), {})

    def test_detects_duplicates(self):
        self._write("a.txt", b"same")
        self._write("b.txt", b"same")
        self._write("c.txt", b"different")
        result = find_duplicates(self.tmp)
        self.assertEqual(len(result), 1)
        paths = list(result.values())[0]
        self.assertEqual(len(paths), 2)

    def test_three_way_duplicate(self):
        for name in ("x.txt", "y.txt", "z.txt"):
            self._write(name, b"triple")
        result = find_duplicates(self.tmp)
        self.assertEqual(len(result), 1)
        self.assertEqual(len(list(result.values())[0]), 3)

    def test_empty_folder(self):
        self.assertEqual(find_duplicates(self.tmp), {})

    def test_dry_run_flag_accepted(self):
        self._write("p.txt", b"dup")
        self._write("q.txt", b"dup")
        rc = main([self.tmp, "--dry-run"])
        self.assertEqual(rc, 0)

    def test_missing_folder_returns_error(self):
        rc = main(["/nonexistent/path/xyz"])
        self.assertEqual(rc, 1)

    def test_specified_test_folder(self):
        """Smoke-test against the repo's own test/ directory."""
        folder = os.path.join(os.path.dirname(__file__), "test")
        if os.path.isdir(folder):
            result = find_duplicates(folder)
            self.assertIsInstance(result, dict)


if __name__ == "__main__":
    sys.exit(main())

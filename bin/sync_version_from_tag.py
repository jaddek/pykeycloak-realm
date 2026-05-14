#!/usr/bin/env python3
"""Sync pyproject.toml project version from a git tag (e.g. v1.2.3)."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

VERSION_LINE_RE = re.compile(r'^(version\s*=\s*")([^"]+)(")\s*$', re.MULTILINE)
SEMVER_TAG_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tag",
        default=os.environ.get("GITHUB_REF_NAME", "").strip(),
        help="Release tag in format vX.Y.Z. Defaults to GITHUB_REF_NAME.",
    )
    parser.add_argument(
        "--file",
        default="pyproject.toml",
        help="Path to pyproject.toml file.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tag = args.tag
    match = SEMVER_TAG_RE.fullmatch(tag)

    if not match:
        print(f"Skipping version sync, tag is not semver release tag: {tag!r}")
        return 0

    target_version = ".".join(match.groups())
    pyproject_path = Path(args.file)
    content = pyproject_path.read_text(encoding="utf-8")

    line_match = VERSION_LINE_RE.search(content)
    if not line_match:
        print('Could not find `version = "..."` in pyproject.toml', file=sys.stderr)
        return 1

    current_version = line_match.group(2)
    if current_version == target_version:
        print(f"Version already set to {target_version}")
        return 0

    updated = VERSION_LINE_RE.sub(rf"\g<1>{target_version}\g<3>", content, count=1)
    pyproject_path.write_text(updated, encoding="utf-8")
    print(f"Updated project version: {current_version} -> {target_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

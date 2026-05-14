#!/usr/bin/env python3
"""Fail when SBOM contains disallowed licenses."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

DEFAULT_DENY = {
    "GPL-1.0",
    "GPL-1.0-only",
    "GPL-1.0-or-later",
    "GPL-2.0",
    "GPL-2.0-only",
    "GPL-2.0-or-later",
    "GPL-3.0",
    "GPL-3.0-only",
    "GPL-3.0-or-later",
    "AGPL-1.0",
    "AGPL-1.0-only",
    "AGPL-1.0-or-later",
    "AGPL-3.0",
    "AGPL-3.0-only",
    "AGPL-3.0-or-later",
    "LGPL-2.0",
    "LGPL-2.0-only",
    "LGPL-2.0-or-later",
    "LGPL-2.1",
    "LGPL-2.1-only",
    "LGPL-2.1-or-later",
    "LGPL-3.0",
    "LGPL-3.0-only",
    "LGPL-3.0-or-later",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sbom", required=True, help="Path to CycloneDX JSON SBOM")
    parser.add_argument(
        "--policy",
        default=".license-policy.toml",
        help="Path to policy TOML file with `deny = [..]`.",
    )
    parser.add_argument(
        "--deny",
        nargs="*",
        default=None,
        help="SPDX license ids to disallow",
    )
    return parser.parse_args()


def extract_component_licenses(component: dict) -> list[str]:
    result: list[str] = []
    for entry in component.get("licenses", []):
        license_obj = entry.get("license") or {}
        license_id = license_obj.get("id")
        if license_id:
            result.append(license_id)
    return result


def load_deny_from_policy(policy_path: Path) -> set[str]:
    if not policy_path.exists():
        return set(DEFAULT_DENY)

    data = tomllib.loads(policy_path.read_text(encoding="utf-8"))
    deny = data.get("deny", [])
    if not isinstance(deny, list) or not all(isinstance(x, str) for x in deny):
        print(
            "Invalid policy format: `deny` must be a list of strings.", file=sys.stderr
        )
        raise SystemExit(2)
    return set(deny)


def main() -> int:
    args = parse_args()
    sbom_path = Path(args.sbom)
    data = json.loads(sbom_path.read_text(encoding="utf-8"))

    deny = set(args.deny) if args.deny else load_deny_from_policy(Path(args.policy))
    violations: list[tuple[str, str]] = []

    for component in data.get("components", []):
        name = component.get("name", "<unknown>")
        version = component.get("version", "<unknown>")
        identity = f"{name}@{version}"
        for license_id in extract_component_licenses(component):
            if license_id in deny:
                violations.append((identity, license_id))

    if not violations:
        print("SBOM license policy check passed.")
        return 0

    print("Disallowed licenses found in SBOM:", file=sys.stderr)
    for identity, license_id in violations:
        print(f"- {identity}: {license_id}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

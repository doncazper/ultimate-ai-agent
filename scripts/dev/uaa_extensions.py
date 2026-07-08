#!/usr/bin/env python3
"""Inspect UAA extension ecosystem metadata.

This CLI exposes the same Python-core read model used by the Control Center
extension catalog route. It does not install, import, execute, enable, or
fetch extension packages.
"""

from __future__ import annotations

import argparse
import json
import sys

from ultimate_ai_agent.core.extension_catalog import (
    build_default_extension_install_disabled_posture,
    build_default_inspectable_extension_catalog,
    build_default_skill_bundle_proposal_posture,
    build_default_skill_write_approval_gate,
)


def inspect_catalog() -> dict[str, object]:
    catalog = build_default_inspectable_extension_catalog()
    return catalog.model_dump(mode="json")


def inspect_skill_write_gate() -> dict[str, object]:
    gate = build_default_skill_write_approval_gate()
    return gate.model_dump(mode="json")


def inspect_skill_bundles() -> dict[str, object]:
    posture = build_default_skill_bundle_proposal_posture()
    return posture.model_dump(mode="json")


def inspect_install_disabled_posture() -> dict[str, object]:
    posture = build_default_extension_install_disabled_posture()
    return posture.model_dump(mode="json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "inspect-catalog",
        help="Print read-only extension catalog metadata as safe-ref JSON.",
    )
    subparsers.add_parser(
        "inspect-skill-write-gate",
        help="Print staged skill-write approval gate metadata as safe-ref JSON.",
    )
    subparsers.add_parser(
        "inspect-skill-bundles",
        help="Print proposal-only skill bundle posture as safe-ref JSON.",
    )
    subparsers.add_parser(
        "inspect-install-disabled-posture",
        help="Print extension install-disabled posture as safe-ref JSON.",
    )
    args = parser.parse_args(argv)

    if args.command == "inspect-catalog":
        print(json.dumps(inspect_catalog(), indent=2, sort_keys=True))
        return 0
    if args.command == "inspect-skill-write-gate":
        print(json.dumps(inspect_skill_write_gate(), indent=2, sort_keys=True))
        return 0
    if args.command == "inspect-skill-bundles":
        print(json.dumps(inspect_skill_bundles(), indent=2, sort_keys=True))
        return 0
    if args.command == "inspect-install-disabled-posture":
        print(json.dumps(inspect_install_disabled_posture(), indent=2, sort_keys=True))
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

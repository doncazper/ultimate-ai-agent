#!/usr/bin/env python3
"""Validate and classify tags for the active macOS product line."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "packaging" / "macos" / "release-policy.json"
POLICY_SCHEMA = "uaa.macos.release-policy.v1"


def classify_tag(
    tag: str,
    *,
    requested_channel: str = "auto",
    policy_path: Path = POLICY_PATH,
) -> str:
    value = json.loads(policy_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != POLICY_SCHEMA:
        raise ValueError("macOS release policy schema is invalid")
    retired = value.get("retired_tag_patterns")
    if not isinstance(retired, list) or not all(
        isinstance(pattern, str) for pattern in retired
    ):
        raise ValueError("macOS release retired-tag policy is invalid")
    if any(re.match(pattern, tag) for pattern in retired):
        raise ValueError("historical audit tag is not eligible for current distribution")
    stable_pattern = value.get("stable_tag_pattern")
    dev_pattern = value.get("dev_tag_pattern")
    if not isinstance(stable_pattern, str) or not isinstance(dev_pattern, str):
        raise ValueError("macOS release channel patterns are invalid")
    if re.fullmatch(stable_pattern, tag):
        classified = "stable"
    elif re.fullmatch(dev_pattern, tag):
        classified = "dev"
    else:
        raise ValueError("tag is outside the active macOS release policy")
    if requested_channel not in {"auto", "stable", "dev"}:
        raise ValueError("requested channel must be auto, stable, or dev")
    if requested_channel != "auto" and requested_channel != classified:
        raise ValueError("requested channel conflicts with the tag policy")
    return classified


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify an active macOS release tag")
    parser.add_argument("--tag", required=True)
    parser.add_argument(
        "--channel",
        choices=["auto", "stable", "dev"],
        default="auto",
    )
    parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    args = parser.parse_args()
    try:
        classified = classify_tag(
            args.tag,
            requested_channel=args.channel,
            policy_path=args.policy,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"blocked: {exc}")
        return 1
    print(classified)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

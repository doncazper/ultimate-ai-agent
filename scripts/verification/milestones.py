from __future__ import annotations

from typing import Any

from .repo import load_json

MILESTONE_STATUS_MANIFEST = "docs/verification/milestone_status_manifest.json"


def milestone_status_manifest() -> dict[str, Any]:
    return load_json(MILESTONE_STATUS_MANIFEST)


def milestone_entry(milestone_id: str) -> dict[str, Any]:
    manifest = milestone_status_manifest()
    for entry in manifest.get("milestones", []):
        if entry.get("id") == milestone_id:
            return entry
    raise KeyError(f"milestone not found: {milestone_id}")

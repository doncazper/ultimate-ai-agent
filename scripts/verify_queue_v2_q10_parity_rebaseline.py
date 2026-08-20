#!/usr/bin/env python3
"""Verify Queue-of-Record V2 Q10 parity rebaseline evidence."""

from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEDGER_REF = (
    "reports/parity_gap_closure/2026-08-20-hermes-openclaw-parity-rebaseline.json"
)
REPORT_REF = (
    "reports/parity_gap_closure/2026-08-20-hermes-openclaw-parity-rebaseline.md"
)
LEDGER = ROOT / LEDGER_REF
REPORT = ROOT / REPORT_REF
QUEUE_MANIFEST = ROOT / "docs/roadmap/UAA_DEVELOPER_QUEUE_V2_MANIFEST.json"
SUCCESS = "Queue V2 Q10 Hermes/OpenClaw parity rebaseline verified"

EXPECTED_SCHEMA = "uaa-queue-v2-q10-parity-rebaseline.v1"
EXPECTED_BASE_REVISION = "eaa89916c5b2198bb48d63219b59e3f2b07cbbc8"
EXPECTED_SOURCE_REVISIONS = {
    "hermes": "4a5b6dd4512a10c3c18da3e5b9e5c7fb681cbfbb",
    "openclaw": "15f33d9edc697cf879cce48e3a5f1f64e6493981",
}
EXPECTED_REPOSITORIES = {
    "hermes": "https://github.com/NousResearch/hermes-agent",
    "openclaw": "https://github.com/openclaw/openclaw",
}
EXPECTED_GAPS = tuple(f"Q10-G{number:02d}" for number in range(1, 19))
EXPECTED_DISPOSITIONS = {
    "Q10-G01": "intentionally_exclude",
    "Q10-G02": "close",
    "Q10-G03": "close",
    "Q10-G04": "close",
    "Q10-G05": "defer",
    "Q10-G06": "defer",
    "Q10-G07": "defer",
    "Q10-G08": "defer",
    "Q10-G09": "intentionally_exclude",
    "Q10-G10": "close",
    "Q10-G11": "intentionally_exclude",
    "Q10-G12": "intentionally_exclude",
    "Q10-G13": "intentionally_exclude",
    "Q10-G14": "close",
    "Q10-G15": "close",
    "Q10-G16": "intentionally_exclude",
    "Q10-G17": "close",
    "Q10-G18": "defer",
}
EXPECTED_OWNERS = {
    "Q10-G01": {"owner-ref:none-intentional"},
    "Q10-G02": {"queue-item-ref:Q12", "queue-item-ref:Q13"},
    "Q10-G03": {"queue-item-ref:Q12", "queue-item-ref:Q21"},
    "Q10-G04": {"queue-item-ref:Q18"},
    "Q10-G05": {"queue-item-ref:Q29"},
    "Q10-G06": {
        "queue-item-ref:Q16",
        "queue-item-ref:Q23",
        "authority-gate-ref:background-autonomy-scoped",
    },
    "Q10-G07": {"queue-item-ref:Q20"},
    "Q10-G08": {"queue-item-ref:Q23"},
    "Q10-G09": {"owner-ref:none-intentional"},
    "Q10-G10": {"queue-item-ref:Q22"},
    "Q10-G11": {"owner-ref:none-intentional"},
    "Q10-G12": {"owner-ref:none-intentional"},
    "Q10-G13": {"owner-ref:none-intentional"},
    "Q10-G14": {"queue-item-ref:Q11"},
    "Q10-G15": {"queue-item-ref:Q16", "queue-item-ref:Q21"},
    "Q10-G16": {"owner-ref:none-intentional"},
    "Q10-G17": {"queue-item-ref:Q14", "queue-item-ref:Q17"},
    "Q10-G18": {"queue-item-ref:Q30"},
}
ALLOWED_DISPOSITIONS = {"close", "defer", "intentionally_exclude"}
ALLOWED_UAA_STATES = {
    "implemented",
    "partial",
    "planned",
    "blocked",
    "intentionally_absent",
}
EXPECTED_AUTHORITY_NON_GRANTS = {
    "runtime model or broad provider calls",
    "live unrestricted web or browser execution",
    "connector writes or broad message sends",
    "unrestricted shell or remote execution",
    "plugin runtime import or unreviewed skill installation",
    "background autonomy or standing execution authority",
    "public beta, public release, production readiness, or production authority",
}
RAW_LOCAL_PATH = re.compile(r"(?:file://|/Users/|/home/|[A-Za-z]:\\)")
HEX_40 = re.compile(r"^[0-9a-f]{40}$")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _repo_path(ref: str) -> Path | None:
    pure = PurePosixPath(ref)
    if pure.is_absolute() or ".." in pure.parts or "\\" in ref:
        return None
    candidate = ROOT.joinpath(*pure.parts)
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(ROOT.resolve())
    except (FileNotFoundError, RuntimeError, ValueError):
        return None
    return resolved


def _queue_items() -> dict[str, dict[str, Any]]:
    payload = _load_json(QUEUE_MANIFEST)
    return {item["item_id"]: item for item in payload["items"]}


def verify(
    *,
    payload: dict[str, Any] | None = None,
    report_text: str | None = None,
    check_refs: bool = True,
) -> list[str]:
    failures: list[str] = []
    data = payload if payload is not None else _load_json(LEDGER)
    markdown = (
        report_text if report_text is not None else REPORT.read_text(encoding="utf-8")
    )

    if data.get("schema_version") != EXPECTED_SCHEMA:
        failures.append("schema version drifted")
    if data.get("report_ref") != REPORT_REF:
        failures.append("report ref drifted")

    inventory = data.get("inventory_base", {})
    if inventory.get("revision") != EXPECTED_BASE_REVISION:
        failures.append("UAA inventory-base revision drifted")
    if inventory.get("observed_date") != "2026-08-20":
        failures.append("inventory date drifted")

    sources = data.get("comparison_sources", [])
    source_by_id = {
        source.get("source_id"): source
        for source in sources
        if isinstance(source, dict)
    }
    if set(source_by_id) != set(EXPECTED_SOURCE_REVISIONS):
        failures.append("comparison source set drifted")
    for source_id, revision in EXPECTED_SOURCE_REVISIONS.items():
        source = source_by_id.get(source_id, {})
        if source.get("revision") != revision or not HEX_40.fullmatch(
            str(source.get("revision", ""))
        ):
            failures.append(f"{source_id} source revision drifted")
        if source.get("repository_url") != EXPECTED_REPOSITORIES[source_id]:
            failures.append(f"{source_id} repository URL drifted")
        evidence_paths = source.get("evidence_paths", [])
        if not isinstance(evidence_paths, list) or not evidence_paths:
            failures.append(f"{source_id} has no evidence path allowlist")
        elif len(evidence_paths) != len(set(evidence_paths)):
            failures.append(f"{source_id} evidence paths are duplicated")
        for path in evidence_paths:
            pure = PurePosixPath(str(path))
            if pure.is_absolute() or ".." in pure.parts or "\\" in str(path):
                failures.append(f"{source_id} evidence path is unsafe: {path}")

    if set(data.get("allowed_dispositions", [])) != ALLOWED_DISPOSITIONS:
        failures.append("allowed dispositions drifted")

    rows = data.get("gap_rows", [])
    ids = [row.get("gap_id") for row in rows if isinstance(row, dict)]
    if tuple(ids) != EXPECTED_GAPS:
        failures.append("gap ledger must contain Q10-G01 through Q10-G18 exactly once")

    queue_items = _queue_items() if check_refs else {}
    disposition_counts = {key: 0 for key in ALLOWED_DISPOSITIONS}
    for row in rows:
        if not isinstance(row, dict):
            failures.append("gap row is not an object")
            continue
        gap_id = str(row.get("gap_id", ""))
        disposition = row.get("disposition")
        if disposition not in ALLOWED_DISPOSITIONS:
            failures.append(f"{gap_id} has invalid disposition")
        else:
            disposition_counts[disposition] += 1
        if EXPECTED_DISPOSITIONS.get(gap_id) != disposition:
            failures.append(f"{gap_id} disposition drifted")
        if row.get("uaa_state") not in ALLOWED_UAA_STATES:
            failures.append(f"{gap_id} has invalid UAA state")
        for field in ("capability", "gap_summary"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                failures.append(f"{gap_id} is missing {field}")

        owners = row.get("owner_refs", [])
        if set(owners) != EXPECTED_OWNERS.get(gap_id, set()):
            failures.append(f"{gap_id} owner routing drifted")
        if disposition == "intentionally_exclude" and owners != [
            "owner-ref:none-intentional"
        ]:
            failures.append(f"{gap_id} intentional exclusion must have no queue owner")
        if disposition in {"close", "defer"} and not any(
            str(owner).startswith(("queue-item-ref:", "authority-gate-ref:"))
            for owner in owners
        ):
            failures.append(f"{gap_id} lacks a later owner or authority gate")
        for owner in owners:
            if not str(owner).startswith("queue-item-ref:"):
                continue
            item_id = str(owner).split(":", 1)[1]
            item = queue_items.get(item_id)
            if check_refs and item is None:
                failures.append(f"{gap_id} references missing queue owner {item_id}")
            elif check_refs and int(item["queue_order"]) <= 10:
                failures.append(f"{gap_id} routes backward to {item_id}")

        source_refs = row.get("source_refs", [])
        if not source_refs or not any(
            str(ref).startswith("hermes:") for ref in source_refs
        ):
            failures.append(f"{gap_id} lacks Hermes current-source evidence")
        if not source_refs or not any(
            str(ref).startswith("openclaw:") for ref in source_refs
        ):
            failures.append(f"{gap_id} lacks OpenClaw current-source evidence")
        for source_ref in source_refs:
            source_id, separator, path = str(source_ref).partition(":")
            source = source_by_id.get(source_id)
            if (
                not separator
                or source is None
                or path not in source.get("evidence_paths", [])
            ):
                failures.append(f"{gap_id} has unpinned source ref: {source_ref}")
            if source_ref not in markdown:
                failures.append(
                    f"{gap_id} source ref missing from report: {source_ref}"
                )

        evidence_refs = row.get("uaa_evidence_refs", [])
        if not evidence_refs:
            failures.append(f"{gap_id} lacks UAA evidence refs")
        for evidence_ref in evidence_refs:
            if check_refs and _repo_path(str(evidence_ref)) is None:
                failures.append(
                    f"{gap_id} UAA evidence ref is missing or unsafe: {evidence_ref}"
                )
        if evidence_refs and not any(
            str(evidence_ref) in markdown for evidence_ref in evidence_refs
        ):
            failures.append(f"{gap_id} lacks UAA evidence in the report")

        boundary_refs = row.get("boundary_refs", [])
        if not boundary_refs:
            failures.append(f"{gap_id} lacks a boundary ref")
        if markdown.count(f"`{gap_id}`") != 1:
            failures.append(f"{gap_id} must appear exactly once in the report ledger")

    if disposition_counts != {
        "close": 7,
        "defer": 5,
        "intentionally_exclude": 6,
    }:
        failures.append("disposition totals drifted")

    if set(data.get("authority_non_grants", [])) != EXPECTED_AUTHORITY_NON_GRANTS:
        failures.append("authority non-grants drifted")
    trigger = str(data.get("rebaseline_trigger", ""))
    if "before Q31" not in trigger or "do not reopen Q10" not in trigger:
        failures.append("finite rebaseline trigger drifted")

    combined = json.dumps(data, sort_keys=True) + "\n" + markdown
    if RAW_LOCAL_PATH.search(combined):
        failures.append("parity rebaseline contains a raw local path")
    for required in (
        EXPECTED_BASE_REVISION,
        EXPECTED_SOURCE_REVISIONS["hermes"],
        EXPECTED_SOURCE_REVISIONS["openclaw"],
        "7 `close`, 5 `defer`, and 6",
        "no runtime authority grant",
        "Q10 does not fix any gap",
    ):
        if required not in markdown:
            failures.append(f"report is missing required truth: {required}")

    return failures


def main() -> int:
    failures = verify()
    if failures:
        print("Queue V2 Q10 parity rebaseline verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(SUCCESS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Verify release-facing artifacts contain only redacted safe summaries.

This verifier is repo-local and deterministic. It scans scoped docs, generated
reports, and optional frontend build output for raw/private material and unsafe
release claims without echoing the offending content.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
SECURITY_REDACTION_SCHEMA_VERSION = "uaa_security_redaction_artifact_scan.v1"
SECURITY_REDACTION_TASK_REF = "UAA-P1-055"
DEFAULT_SCOPES = (
    "SECURITY.md",
    "docs/security",
    "docs/production/RELEASE_VERIFICATION_LANES.md",
    "docs/production/RELEASE_EVIDENCE_PACKET.md",
    "docs/production/RELEASE_EVIDENCE_PACKET_TEMPLATE.json",
    "docs/production/RELEASE_LATENCY_BASELINE_HARNESS.md",
    "docs/kanban/current_board.md",
    "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
    "docs/control_center/PRODUCT_LANGUAGE_RULES.md",
    "docs/control_center/ROUTE_STATUS_MANIFEST.md",
    "reports/foundation_gate",
    "reports/performance",
    "apps/control-center/dist",
)
TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".txt",
    ".yaml",
    ".yml",
}
SKIPPED_PATH_FRAGMENTS = (
    "/.git/",
    "/__pycache__/",
    "/node_modules/",
)


@dataclass(frozen=True)
class SecurityRedactionFinding:
    rel_path: str
    line: int
    category: str
    evidence_hash: str
    safe_message: str


LINE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "raw_prompt_content",
        re.compile(r"(?i)\braw\s+prompt\s*:\s*\S+"),
    ),
    (
        "raw_response_content",
        re.compile(r"(?i)\braw\s+response\s*:\s*\S+"),
    ),
    (
        "raw_provider_payload_content",
        re.compile(r"(?i)\braw\s+provider\s+payload\s*:\s*\S+"),
    ),
    (
        "raw_path_material",
        re.compile(
            r"(?i)(?:/users/[a-z0-9._-]+/|/home/[a-z0-9._-]+/|[a-z]:\\users\\[^\\\s]+\\)"
        ),
    ),
    (
        "raw_log_material",
        re.compile(
            r"(?i)(?:\braw\s+log\s*:\s*\S+|traceback \(most recent call last\))"
        ),
    ),
    (
        "username_material",
        re.compile(r"(?i)\busername\s*:\s*[^\s`]+"),
    ),
    (
        "hostname_material",
        re.compile(r"(?i)\bhostname\s*:\s*[^\s`]+"),
    ),
    (
        "serial_material",
        re.compile(r"(?i)\bserial(?:\s+number)?\s*:\s*[^\s`]+"),
    ),
    (
        "environment_dump_material",
        re.compile(r"(?i)\benvironment\s+dump\s*:\s*\S+"),
    ),
    (
        "secret_like_material",
        re.compile(
            r"(?i)\b(?:api[_-]?key|client[_-]?secret|auth[_-]?token|password|secret|token)\b"
            r"\s*[=:]\s*['\"]?[a-z0-9_./:+\-]{12,}['\"]?"
        ),
    ),
    (
        "bearer_token_material",
        re.compile(r"(?i)\bauthorization\s*:\s*bearer\s+[a-z0-9._~+/=\-]{12,}"),
    ),
    (
        "private_key_material",
        re.compile(r"(?i)-{5}begin [a-z0-9 ]*private key-{5}"),
    ),
    (
        "standalone_token_material",
        re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b|\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    ),
)

UNSAFE_CLAIM_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "public_distribution_claim",
        re.compile(r"(?i)\bpublic distribution is (?:available|ready|enabled)\b"),
    ),
    (
        "public_release_claim",
        re.compile(r"(?i)\bpublic release is (?:available|ready|enabled)\b"),
    ),
    (
        "public_beta_claim",
        re.compile(r"(?i)\bpublic beta is (?:available|ready|enabled)\b"),
    ),
    (
        "signed_release_claim",
        re.compile(r"(?i)\bsigned (?:installer|release) is (?:ready|available)\b"),
    ),
    (
        "external_audit_claim",
        re.compile(r"(?i)\bexternal audit (?:completed|passed|approved)\b"),
    ),
    (
        "production_authority_claim",
        re.compile(
            r"(?i)\b(?:(?<!no )production authority is granted|grants production authority now)\b"
        ),
    ),
    (
        "production_readiness_claim",
        re.compile(r"(?i)\b(?:is production[- ]ready|production ready now)\b"),
    ),
)


def _safe_hash(rel_path: str, line_number: int, category: str, line: str) -> str:
    digest = hashlib.sha256(
        f"{rel_path}:{line_number}:{category}:{line}".encode("utf-8")
    ).hexdigest()
    return f"sha256:{digest[:16]}"


def _finding(
    *,
    rel_path: str,
    line_number: int,
    category: str,
    line: str,
) -> SecurityRedactionFinding:
    return SecurityRedactionFinding(
        rel_path=rel_path,
        line=line_number,
        category=category,
        evidence_hash=_safe_hash(rel_path, line_number, category, line),
        safe_message=(
            f"{rel_path}:{line_number} contains {category}; "
            "offending content redacted"
        ),
    )


def _is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES


def _iter_scope_files(root: Path, scopes: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for scope in scopes:
        candidate = root / scope
        if not candidate.exists():
            continue
        if candidate.is_file():
            files.append(candidate)
            continue
        for path in candidate.rglob("*"):
            rel = path.relative_to(root).as_posix()
            rel_with_slashes = f"/{rel}/" if path.is_dir() else f"/{rel}"
            if any(fragment in rel_with_slashes for fragment in SKIPPED_PATH_FRAGMENTS):
                continue
            if path.is_file() and _is_text_file(path):
                files.append(path)
    return sorted(set(files), key=lambda path: path.relative_to(root).as_posix())


def scan_text(rel_path: str, text: str) -> list[SecurityRedactionFinding]:
    findings: list[SecurityRedactionFinding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for category, pattern in (*LINE_PATTERNS, *UNSAFE_CLAIM_PATTERNS):
            if pattern.search(line):
                findings.append(
                    _finding(
                        rel_path=rel_path,
                        line_number=line_number,
                        category=category,
                        line=line,
                    )
                )
    return findings


def scan_file(root: Path, path: Path) -> list[SecurityRedactionFinding]:
    rel_path = path.relative_to(root).as_posix()
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="ignore")
    return scan_text(rel_path, text)


def validate_security_redaction_artifacts(
    root: Path = ROOT,
    scopes: Iterable[str] = DEFAULT_SCOPES,
) -> list[SecurityRedactionFinding]:
    root = root.resolve()
    findings: list[SecurityRedactionFinding] = []
    for path in _iter_scope_files(root, scopes):
        findings.extend(scan_file(root, path))
    return findings


def build_scan_report(
    *,
    root: Path = ROOT,
    scopes: Iterable[str] = DEFAULT_SCOPES,
) -> dict[str, object]:
    scanned_files = _iter_scope_files(root.resolve(), scopes)
    findings = validate_security_redaction_artifacts(root=root, scopes=scopes)
    categories = sorted({finding.category for finding in findings})
    return {
        "schema_version": SECURITY_REDACTION_SCHEMA_VERSION,
        "task_ref": SECURITY_REDACTION_TASK_REF,
        "status": "failed" if findings else "passed",
        "scope_refs": list(scopes),
        "scanned_file_count": len(scanned_files),
        "finding_count": len(findings),
        "finding_categories": categories,
        "findings": [asdict(finding) for finding in findings],
        "report_safety": {
            "raw_prompt_included": False,
            "raw_response_included": False,
            "raw_provider_payload_included": False,
            "raw_path_included": False,
            "raw_log_included": False,
            "username_included": False,
            "hostname_included": False,
            "serial_included": False,
            "environment_dump_included": False,
            "credential_material_included": False,
            "offending_content_echoed": False,
        },
        "non_goals": [
            "does not execute release lane commands",
            "does not add external audit scanning",
            "does not upload artifacts",
            "does not claim public distribution, signed release, public beta, or production readiness",
        ],
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify release-facing artifacts and safe summaries are redacted.",
    )
    parser.add_argument(
        "--root",
        default=str(ROOT),
        help="Repository root to scan. Default: current repository.",
    )
    parser.add_argument(
        "--scope",
        action="append",
        dest="scopes",
        help="Repo-relative file or directory scope. May be repeated.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    root = Path(args.root)
    scopes = tuple(args.scopes) if args.scopes else DEFAULT_SCOPES
    report = build_scan_report(root=root, scopes=scopes)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Ultimate AI Agent security/redaction artifact scan")
        print(f"Schema: {report['schema_version']}")
        print(f"Task: {report['task_ref']}")
        print(f"Status: {report['status']}")
        print(f"Scanned files: {report['scanned_file_count']}")
        print(f"Findings: {report['finding_count']}")
        for finding in report["findings"]:  # type: ignore[index]
            print(
                "- {safe_message} [{evidence_hash}]".format(
                    safe_message=finding["safe_message"],
                    evidence_hash=finding["evidence_hash"],
                )
            )
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())

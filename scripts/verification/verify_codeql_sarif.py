#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


HIGH_SEVERITY_THRESHOLD = 7.0


def high_severity_findings(root: Path) -> list[str]:
    findings: list[str] = []
    sarif_files = sorted(root.rglob("*.sarif"))
    if not sarif_files:
        return ["CODEQL_SARIF_MISSING"]
    for sarif_file in sarif_files:
        payload = json.loads(sarif_file.read_text(encoding="utf-8"))
        for run in payload.get("runs", []):
            rules = {
                str(rule.get("id")): rule
                for rule in run.get("tool", {}).get("driver", {}).get("rules", [])
                if isinstance(rule, dict)
            }
            for result in run.get("results", []):
                if not isinstance(result, dict):
                    continue
                rule_id = str(result.get("ruleId", "unknown"))
                properties = rules.get(rule_id, {}).get("properties", {})
                try:
                    configured_severity = properties.get("security-severity")
                    severity = (
                        float(configured_severity)
                        if configured_severity is not None
                        else {"error": 10.0, "warning": 5.0}.get(
                            str(result.get("level", "none")), 0.0
                        )
                    )
                except (TypeError, ValueError):
                    severity = 0.0
                if severity >= HIGH_SEVERITY_THRESHOLD:
                    findings.append(f"CODEQL_HIGH_SEVERITY:{rule_id}:{severity:g}")
    return findings


def main() -> int:
    if len(sys.argv) != 2:
        print("CODEQL_SARIF_DIRECTORY_REQUIRED")
        return 2
    findings = high_severity_findings(Path(sys.argv[1]))
    if findings:
        print("\n".join(findings))
        return 1
    print("CodeQL SARIF gate passed with no high-severity findings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

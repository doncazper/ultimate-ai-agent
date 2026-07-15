#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def _validate(path: Path, label: str) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("bomFormat") != "CycloneDX":
        raise ValueError(f"{label} SBOM is not CycloneDX JSON")
    components = payload.get("components")
    if not isinstance(components, list) or not components:
        raise ValueError(f"{label} SBOM has no components")
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python-sbom", type=Path, required=True)
    parser.add_argument("--control-center-sbom", type=Path, required=True)
    parser.add_argument("--summary-file", type=Path, required=True)
    args = parser.parse_args()
    python_hash = _validate(args.python_sbom, "Python")
    control_center_hash = _validate(args.control_center_sbom, "Control Center")
    with args.summary_file.open("a", encoding="utf-8") as handle:
        handle.write("## Supply-chain evidence\n\n")
        handle.write(f"- Python SBOM: `{python_hash}`\n")
        handle.write(f"- Control Center SBOM: `{control_center_hash}`\n")
        handle.write(
            "- Raw dependency payloads were not copied into repository evidence.\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

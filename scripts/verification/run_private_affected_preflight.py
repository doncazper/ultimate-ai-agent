#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FULL_COMMAND_REF = "command-ref:verification:full-local-gate"


def _selector(base_ref: str, *, execute: bool) -> subprocess.CompletedProcess[str]:
    argv = [
        sys.executable,
        "scripts/verification/changed_path_selector.py",
        "--base-ref",
        base_ref,
        "--tier",
        "affected",
    ]
    argv.append("--execute" if execute else "--json")
    return subprocess.run(
        argv,
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL if execute else subprocess.PIPE,
        stderr=subprocess.DEVNULL if execute else subprocess.PIPE,
        text=True,
        timeout=900,
    )


def run(base_ref: str) -> int:
    inspected = _selector(base_ref, execute=False)
    if inspected.returncode != 0:
        print("Affected preflight: fail closed to canonical full merge gate")
        return 0
    try:
        payload = json.loads(inspected.stdout)
    except json.JSONDecodeError:
        print("Affected preflight: fail closed to canonical full merge gate")
        return 0
    command_refs = payload.get("selected_command_refs", [])
    if not isinstance(command_refs, list) or FULL_COMMAND_REF in command_refs:
        print("Affected preflight: canonical full merge gate required")
        return 0
    completed = _selector(base_ref, execute=True)
    print(
        "Affected preflight: "
        + ("pass" if completed.returncode == 0 else "deterministic failure")
    )
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run affected checks without duplicating a selected full merge gate."
    )
    parser.add_argument("--base-ref", default="origin/main")
    args = parser.parse_args(argv)
    return run(args.base_ref)


if __name__ == "__main__":
    raise SystemExit(main())

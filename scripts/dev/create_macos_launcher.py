#!/usr/bin/env python3
"""Create a clickable macOS .command launcher for local development."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


def _load_launcher():
    launcher_path = Path(__file__).resolve().parent / "uaa_launcher.py"
    spec = importlib.util.spec_from_file_location("uaa_launcher", launcher_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load uaa_launcher.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Ultimate AI Agent.command")
    parser.add_argument("--target", choices=["repo", "desktop"], default="repo")
    args = parser.parse_args()
    launcher = _load_launcher()
    output = launcher.create_macos_launcher(launcher.repo_root(), args.target)
    print(f"Created macOS launcher: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

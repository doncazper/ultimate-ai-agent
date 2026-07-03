#!/usr/bin/env python3
from __future__ import annotations

import plistlib
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.build_local_macos_app_bundle_proof import (  # noqa: E402
    APP_NAME,
    EXECUTABLE_NAME,
    FORBIDDEN_LAUNCHER_FRAGMENTS,
    build_local_macos_app_bundle_proof,
    validate_summary,
)


def verify() -> list[str]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="uaa-local-macos-app-proof-") as temp_dir:
        output_root = Path(temp_dir)
        summary = build_local_macos_app_bundle_proof(output_root)
        failures.extend(validate_summary(summary))
        bundle_root = output_root / f"{APP_NAME}.app"
        executable = bundle_root / "Contents" / "MacOS" / EXECUTABLE_NAME
        info_plist = bundle_root / "Contents" / "Info.plist"
        boundary_readme = bundle_root / "Contents" / "Resources" / "README.txt"
        for path, label in [
            (bundle_root, "bundle root"),
            (executable, "launcher executable"),
            (info_plist, "Info.plist"),
            (boundary_readme, "boundary readme"),
        ]:
            if not path.exists():
                failures.append(f"local macOS app proof missing {label}")
        if executable.exists():
            launcher = executable.read_text(encoding="utf-8")
            if "./scripts/dev/uaa trial-boot" not in launcher:
                failures.append("local macOS app proof launcher does not target trial-boot")
            for fragment in FORBIDDEN_LAUNCHER_FRAGMENTS:
                if fragment.lower() in launcher.lower():
                    failures.append(f"local macOS app proof launcher contains forbidden {fragment!r}")
        if info_plist.exists():
            with info_plist.open("rb") as handle:
                plist = plistlib.load(handle)
            if plist.get("UAADistributionClaimsAllowed") is not False:
                failures.append("local macOS app proof plist must deny distribution claims")
            boundary = str(plist.get("UAAAuthorityBoundary", "")).lower()
            for required in ["local-only", "not signed", "not notarized", "not public"]:
                if required not in boundary:
                    failures.append(f"local macOS app proof plist missing {required!r}")
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("OK: Local unsigned macOS app bundle proof is safe and current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

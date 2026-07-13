from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from pathlib import Path


def _attempt(callback) -> str:
    try:
        callback()
    except Exception:
        return "denied"
    return "allowed"


def main() -> int:
    probe = sys.argv[1] if len(sys.argv) == 2 else "invalid"
    probes = {
        "network_ipv4": lambda: socket.socket(socket.AF_INET, socket.SOCK_STREAM),
        "network_ipv6": lambda: socket.socket(socket.AF_INET6, socket.SOCK_STREAM),
        "network_unix": lambda: socket.socket(socket.AF_UNIX, socket.SOCK_STREAM),
        "host_home": lambda: list(Path("/Users").iterdir()),
        "host_private": lambda: list(Path("/private").iterdir()),
        "root_write": lambda: Path("/uaa-write-probe").write_text(
            "denied", encoding="utf-8"
        ),
        "tmp_write": lambda: Path("/tmp/uaa-write-probe").write_text(
            "bounded", encoding="utf-8"
        ),
        "subprocess": lambda: subprocess.run(
            [sys.executable, "-c", "pass"], check=True
        ),
    }
    if probe == "environment":
        safe_keys = {
            "HOME",
            "HOSTNAME",
            "LANG",
            "PATH",
            "PYTHONDONTWRITEBYTECODE",
            "PYTHONHASHSEED",
            "PYTHONNOUSERSITE",
        }
        status = "denied" if set(os.environ).issubset(safe_keys) else "allowed"
    elif probe == "shell_binary":
        status = "allowed" if Path("/bin/sh").exists() else "denied"
    elif probe == "package_manager":
        candidates = (
            Path("/sbin/apk"),
            Path("/usr/bin/apt"),
            Path("/usr/bin/pip"),
            Path("/usr/local/bin/pip"),
            Path("/usr/local/bin/pip3"),
            Path("/usr/local/lib/python3.13/ensurepip"),
            Path("/usr/local/lib/python3.13/site-packages/pip"),
        )
        status = "allowed" if any(path.exists() for path in candidates) else "denied"
    elif probe == "launcher_inventory":
        launchers = sorted(path.name for path in Path("/usr/local/bin").iterdir())
        status = "denied" if launchers == ["python3.13"] else "allowed"
    elif probe == "credential_paths":
        candidates = (Path("/root/.ssh"), Path("/root/.aws"), Path("/Users"))
        status = "allowed" if any(path.exists() for path in candidates) else "denied"
    elif probe in probes:
        status = _attempt(probes[probe])
    else:
        status = "invalid"
    print(
        json.dumps(
            {"probe": probe, "status": status}, sort_keys=True, separators=(",", ":")
        )
    )
    return 0 if status in {"denied", "invalid"} or probe == "tmp_write" else 4


if __name__ == "__main__":
    raise SystemExit(main())

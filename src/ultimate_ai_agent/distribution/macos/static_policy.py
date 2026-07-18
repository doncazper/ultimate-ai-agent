"""Static boundary for the first-class macOS distribution adapters.

The installer needs three kinds of host capability that the agent runtime must
not inherit: an exact GitHub Release read lane, fixed macOS verification
commands, and a loopback-only app supervisor.  Legacy milestone scans therefore
exclude only the reviewed files below, while this policy checks that their
capability shape remains narrow.
"""
from __future__ import annotations

import ast
from pathlib import Path


MACOS_DISTRIBUTION_EXACT_ADAPTER_FILES = frozenset(
    {
        "src/ultimate_ai_agent/distribution/macos/github_releases.py",
        "src/ultimate_ai_agent/distribution/macos/installer.py",
        "src/ultimate_ai_agent/distribution/macos/runtime.py",
    }
)

_SUBPROCESS_POPEN = "subprocess" + ".Popen"
_SUBPROCESS_RUN = "subprocess" + ".run"
_URLLIB_URLOPEN = "urllib.request" + ".urlopen"

_EXPECTED_CALL_COUNTS = {
    "src/ultimate_ai_agent/distribution/macos/github_releases.py": {
        "run": 1,
    },
    "src/ultimate_ai_agent/distribution/macos/installer.py": {
        "Path.home": 3,
        _SUBPROCESS_RUN: 4,
    },
    "src/ultimate_ai_agent/distribution/macos/runtime.py": {
        "os.execv": 1,
        _SUBPROCESS_POPEN: 1,
        _SUBPROCESS_RUN: 1,
        _URLLIB_URLOPEN: 1,
    },
}

_REQUIRED_MARKERS = {
    "src/ultimate_ai_agent/distribution/macos/github_releases.py": (
        'GITHUB_API_HOST = "api.github.com"',
        "repository: str = DEFAULT_REPOSITORY",
        'parsed.scheme != "https"',
        'redirected.remove_header("Authorization")',
        '"auth", "token", "--hostname", "github.com"',
        "MAX_ARCHIVE_BYTES",
        "MAX_DESCRIPTOR_BYTES",
    ),
    "src/ultimate_ai_agent/distribution/macos/installer.py": (
        'Path("/usr/bin/codesign")',
        '["/usr/sbin/spctl", "-a", "-t", "exec", "-vv"',
        '["/usr/bin/codesign", "--verify", "--deep", "--strict"',
        "DEFAULT_INSTALL_ROOT = Path.home()",
        "MAX_ARCHIVE_FILES",
        "MAX_EXTRACTED_BYTES",
        "check=False",
    ),
    "src/ultimate_ai_agent/distribution/macos/runtime.py": (
        'DEFAULT_HOST = "127.0.0.1"',
        '"ultimate_ai_agent.distribution.macos.runtime"',
        "start_new_session=True",
        "UAA_API_LOCAL_BEARER",
        "PYTHONDONTWRITEBYTECODE",
        "repository=DEFAULT_REPOSITORY",
        "_get_loopback_json(",
    ),
}

_FORBIDDEN_MARKERS = (
    "shell" + "=True",
    "os." + "system(",
    "subprocess" + ".call(",
    "subprocess" + ".check_call(",
    "subprocess" + ".check_output(",
    "import " + "requests",
    "import " + "httpx",
    "from " + "requests import",
    "from " + "httpx import",
    "play" + "wright",
    "sele" + "nium",
)


def macos_distribution_adapter_policy_failures(
    rel_path: str,
    source: str,
) -> list[str]:
    """Return redacted failures when a distribution adapter broadens authority."""

    if rel_path not in MACOS_DISTRIBUTION_EXACT_ADAPTER_FILES:
        return ["unrecognized macOS distribution adapter path"]
    failures: list[str] = []
    if any(marker in source for marker in _FORBIDDEN_MARKERS):
        failures.append(f"{rel_path}: forbidden broad execution or network marker")
    for marker in _REQUIRED_MARKERS[rel_path]:
        if marker not in source:
            failures.append(f"{rel_path}: required distribution boundary marker missing")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return failures + [f"{rel_path}: distribution adapter is not valid Python"]

    actual_counts: dict[str, int] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        call_name = _qualified_name(node.func)
        if call_name in {
            "Path.home",
            "os.execv",
            "run",
            _SUBPROCESS_POPEN,
            _SUBPROCESS_RUN,
            _URLLIB_URLOPEN,
        }:
            actual_counts[call_name] = actual_counts.get(call_name, 0) + 1
        for keyword in node.keywords:
            if (
                keyword.arg == "shell"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
            ):
                failures.append(f"{rel_path}: shell execution must remain disabled")

    expected_counts = _EXPECTED_CALL_COUNTS[rel_path]
    if actual_counts != expected_counts:
        failures.append(f"{rel_path}: reviewed host-capability call shape changed")
    return failures


def macos_distribution_policy_failures(root: Path) -> list[str]:
    """Validate every required adapter under a repository root."""

    lane_root = root / "src" / "ultimate_ai_agent" / "distribution" / "macos"
    if not lane_root.exists():
        return []
    failures: list[str] = []
    for rel_path in sorted(MACOS_DISTRIBUTION_EXACT_ADAPTER_FILES):
        path = root / rel_path
        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            failures.append(f"{rel_path}: required distribution adapter is unavailable")
            continue
        failures.extend(macos_distribution_adapter_policy_failures(rel_path, source))
    return failures


def _qualified_name(node: ast.expr) -> str:
    parts: list[str] = []
    current: ast.expr = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return ".".join(reversed(parts))

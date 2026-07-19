"""Static boundary for the first-class macOS distribution adapters.

The installer needs three kinds of host capability that the agent runtime must
not inherit: an exact GitHub Release read lane, fixed macOS verification
commands, and a loopback-only app supervisor.  Legacy milestone scans therefore
route only reviewed fragments from the exact files below through this policy;
the files themselves remain visible to every unrelated scan.
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

_SOCKET_DOT = "socket" + "."
_SOCKET_SOCKET = _SOCKET_DOT + "socket"
_IMPORT_SUBPROCESS = "import " + "subprocess"
_FROM_SUBPROCESS_IMPORT = "from " + "subprocess import"
_HTTP_PREFIX = "http" + "://"
_HTTPS_PREFIX = "https" + "://"
_OS_SYSTEM = "os." + "system("
_POPEN_FRAGMENT = "po" + "pen("
_SUBPROCESS_DOT = "subprocess" + "."
_SUBPROCESS_POPEN = _SUBPROCESS_DOT + "Popen"
_SUBPROCESS_RUN = _SUBPROCESS_DOT + "run"
_URLLIB_URLOPEN = "urllib.request" + ".urlopen"
_HOST_CALL_PREFIXES = (
    "Path.",
    "os.",
    _SOCKET_DOT,
    _SUBPROCESS_DOT,
    "sys.",
    "urllib.",
    "webbrowser.",
    "root.",
)
_DYNAMIC_CALL_NAMES = frozenset(
    {
        "__import__",
        "builtins.__import__",
        "compile",
        "delattr",
        "eval",
        "exec",
        "globals",
        "importlib.import_module",
        "locals",
        "setattr",
        "vars",
    }
)

_EXPECTED_CALL_COUNTS = {
    "src/ultimate_ai_agent/distribution/macos/github_releases.py": {
        "Path": 4,
        "os.access": 1,
        "run": 1,
        "self.opener.open": 2,
        "urllib.parse.urlparse": 2,
        "urllib.request.Request": 1,
        "urllib.request.build_opener": 1,
    },
    "src/ultimate_ai_agent/distribution/macos/installer.py": {
        "Path": 13,
        "Path.home": 3,
        "os.access": 2,
        "os.replace": 7,
        "root.joinpath": 1,
        "root.resolve": 1,
        "root.rglob": 1,
        _SUBPROCESS_RUN: 4,
    },
    "src/ultimate_ai_agent/distribution/macos/runtime.py": {
        "Path": 2,
        "getattr": 2,
        "os.environ.get": 1,
        "os.environ.items": 1,
        "os.execv": 1,
        "os.kill": 4,
        "os.replace": 2,
        _SOCKET_SOCKET: 1,
        _SUBPROCESS_POPEN: 1,
        _SUBPROCESS_RUN: 1,
        "urllib.parse.quote": 1,
        "urllib.request.Request": 1,
        _URLLIB_URLOPEN: 1,
        "webbrowser.open": 2,
    },
}

_ALLOWED_EXTERNAL_ATTRIBUTES = {
    "src/ultimate_ai_agent/distribution/macos/github_releases.py": {
        "os.X_OK",
        "os.access",
        "os.environ",
        _SUBPROCESS_DOT + "CompletedProcess",
        _SUBPROCESS_DOT + "SubprocessError",
        _SUBPROCESS_RUN,
        "urllib.error",
        "urllib.error.HTTPError",
        "urllib.error.URLError",
        "urllib.parse",
        "urllib.parse.urlparse",
        "urllib.request",
        "urllib.request.HTTPRedirectHandler",
        "urllib.request.OpenerDirector",
        "urllib.request.Request",
        "urllib.request.build_opener",
    },
    "src/ultimate_ai_agent/distribution/macos/installer.py": {
        "os.W_OK",
        "os.X_OK",
        "os.access",
        "os.environ",
        "os.replace",
        "Path.home",
        _SUBPROCESS_DOT + "DEVNULL",
        _SUBPROCESS_RUN,
    },
    "src/ultimate_ai_agent/distribution/macos/runtime.py": {
        "os.environ",
        "os.environ.get",
        "os.environ.items",
        "os.execv",
        "os.kill",
        "os.replace",
        "sys.executable",
        _SOCKET_DOT + "AF_INET",
        _SOCKET_DOT + "SOCK_STREAM",
        _SOCKET_SOCKET,
        _SUBPROCESS_DOT + "DEVNULL",
        _SUBPROCESS_POPEN,
        _SUBPROCESS_RUN,
        "urllib.error",
        "urllib.error.URLError",
        "urllib.parse",
        "urllib.parse.quote",
        "urllib.request",
        "urllib.request.Request",
        _URLLIB_URLOPEN,
        "webbrowser.open",
    },
}

_EXPECTED_HOST_IMPORTS = {
    "src/ultimate_ai_agent/distribution/macos/github_releases.py": {
        "os",
        "subprocess",
        "urllib.error",
        "urllib.parse",
        "urllib.request",
    },
    "src/ultimate_ai_agent/distribution/macos/installer.py": {
        "os",
        "subprocess",
    },
    "src/ultimate_ai_agent/distribution/macos/runtime.py": {
        "os",
        "socket",
        "subprocess",
        "sys",
        "urllib.error",
        "urllib.parse",
        "urllib.request",
        "webbrowser",
    },
}
_HOST_MODULE_NAMES = frozenset(
    {
        "builtins",
        "importlib",
        "os",
        "socket",
        "subprocess",
        "sys",
        "urllib",
        "webbrowser",
    }
)

_ALLOWED_URL_LINES = {
    "src/ultimate_ai_agent/distribution/macos/github_releases.py": {
        'f"' + _HTTPS_PREFIX + '{GITHUB_API_HOST}/repos/{self.repository}/releases"',
        'f"'
        + _HTTPS_PREFIX
        + '{GITHUB_API_HOST}/repos/{self.repository}/releases/assets/"',
    },
    "src/ultimate_ai_agent/distribution/macos/installer.py": set(),
    "src/ultimate_ai_agent/distribution/macos/runtime.py": {
        'f"' + _HTTP_PREFIX + '{DEFAULT_HOST}:{port}/uaa-runtime-identity",',
        'return f"' + _HTTP_PREFIX + '{DEFAULT_HOST}:{port}/"',
        "\"connect-src 'self' "
        + _HTTP_PREFIX
        + "localhost:* "
        + _HTTP_PREFIX
        + '127.0.0.1:* "',
        '"'
        + _HTTP_PREFIX
        + "[::1]:*; script-src 'self'; style-src 'self' 'unsafe-inline'\"",
    },
}

_SHELL_SCAN_FRAGMENTS = frozenset(
    {
        _IMPORT_SUBPROCESS,
        _FROM_SUBPROCESS_IMPORT,
        _OS_SYSTEM,
        _POPEN_FRAGMENT,
        "subprocess",
        _SUBPROCESS_DOT,
        _SUBPROCESS_POPEN + "(",
        _SUBPROCESS_RUN + "(",
    }
)
_NETWORK_SCAN_FRAGMENTS = {
    "src/ultimate_ai_agent/distribution/macos/github_releases.py": frozenset(
        {
            _HTTP_PREFIX,
            _HTTPS_PREFIX,
            "import urllib.request",
            "from urllib import error",
            "from urllib import request",
            "urllib.request",
            _URLLIB_URLOPEN,
            _URLLIB_URLOPEN + "(",
        }
    ),
    "src/ultimate_ai_agent/distribution/macos/installer.py": frozenset(),
    "src/ultimate_ai_agent/distribution/macos/runtime.py": frozenset(
        {
            _HTTP_PREFIX,
            _HTTPS_PREFIX,
            "import urllib.request",
            "from urllib import error",
            "from urllib import request",
            _SOCKET_DOT,
            "urllib.request",
            _URLLIB_URLOPEN,
            _URLLIB_URLOPEN + "(",
            "webbrowser.open",
        }
    ),
}
_FILESYSTEM_SCAN_FRAGMENTS = {
    "src/ultimate_ai_agent/distribution/macos/github_releases.py": frozenset(),
    "src/ultimate_ai_agent/distribution/macos/installer.py": frozenset(
        {
            '.rglob("*")',
            ".rglob('*')",
            "Path.home(",
        }
    ),
    "src/ultimate_ai_agent/distribution/macos/runtime.py": frozenset(),
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
            failures.append(
                f"{rel_path}: required distribution boundary marker missing"
            )
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return failures + [f"{rel_path}: distribution adapter is not valid Python"]

    actual_host_imports: set[str] = set()
    parent_by_node = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for imported in node.names:
                if imported.name.split(".", maxsplit=1)[0] in _HOST_MODULE_NAMES:
                    actual_host_imports.add(imported.name)
                    if imported.asname is not None:
                        failures.append(f"{rel_path}: host-capability import alias denied")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.split(".", maxsplit=1)[0] in _HOST_MODULE_NAMES:
                failures.append(f"{rel_path}: host-capability from-import denied")
        elif (
            isinstance(node, ast.Name)
            and node.id in _HOST_MODULE_NAMES
            and not isinstance(parent_by_node.get(node), ast.Attribute)
        ):
            failures.append(f"{rel_path}: indirect host-capability access denied")
    if actual_host_imports != _EXPECTED_HOST_IMPORTS[rel_path]:
        failures.append(f"{rel_path}: reviewed host-capability imports changed")

    allowed_attributes = _ALLOWED_EXTERNAL_ATTRIBUTES[rel_path]
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        attribute_name = _qualified_name(node)
        if (
            attribute_name.startswith(
                (
                    "os.",
                    "Path.",
                    _SOCKET_DOT,
                    _SUBPROCESS_DOT,
                    "sys.",
                    "urllib.error",
                    "urllib.parse",
                    "urllib.request",
                    "webbrowser.",
                )
            )
            and attribute_name not in allowed_attributes
        ):
            failures.append(f"{rel_path}: unreviewed host-capability attribute")

    actual_counts: dict[str, int] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        call_name = _qualified_name(node.func)
        if (
            call_name in {"Path", "getattr", "run", "self.opener.open"}
            or call_name.startswith(_HOST_CALL_PREFIXES)
        ):
            actual_counts[call_name] = actual_counts.get(call_name, 0) + 1
        if call_name in _DYNAMIC_CALL_NAMES:
            failures.append(f"{rel_path}: dynamic host-capability access denied")
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
    allowed_url_lines = _ALLOWED_URL_LINES[rel_path]
    for line in source.splitlines():
        stripped = line.strip()
        if (_HTTP_PREFIX in stripped or _HTTPS_PREFIX in stripped) and (
            stripped not in allowed_url_lines
        ):
            failures.append(f"{rel_path}: unreviewed network endpoint marker")
    return failures


def macos_distribution_static_fragment_allowed(
    rel_path: str,
    source: str,
    fragment: str,
) -> bool:
    """Allow one reviewed scan fragment without exempting the adapter file."""

    if (
        rel_path not in MACOS_DISTRIBUTION_EXACT_ADAPTER_FILES
        or fragment not in source
        or macos_distribution_adapter_policy_failures(rel_path, source)
    ):
        return False
    return (
        fragment in _SHELL_SCAN_FRAGMENTS
        or fragment in _NETWORK_SCAN_FRAGMENTS[rel_path]
        or fragment in _FILESYSTEM_SCAN_FRAGMENTS[rel_path]
    )


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

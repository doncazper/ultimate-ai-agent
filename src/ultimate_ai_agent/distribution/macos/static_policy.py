"""Static boundary for the first-class macOS distribution adapters.

The installer needs three kinds of host capability that the agent runtime must
not inherit: an exact GitHub Release read lane, fixed macOS verification
commands, and a loopback-only app supervisor.  Legacy milestone scans therefore
route only reviewed fragments from the exact files below through this policy;
the files themselves remain visible to every unrelated scan.
"""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path


MACOS_DISTRIBUTION_EXACT_ADAPTER_FILES = frozenset(
    {
        "src/ultimate_ai_agent/distribution/macos/github_releases.py",
        "src/ultimate_ai_agent/distribution/macos/installer.py",
        "src/ultimate_ai_agent/distribution/macos/runtime.py",
    }
)
_EXPECTED_SOURCE_SHA256 = {
    "src/ultimate_ai_agent/distribution/macos/github_releases.py": (
        "d61e6b1adab449d8849ecb97632ec680514531d2097be7d8bf870bd0bf86a606"
    ),
    "src/ultimate_ai_agent/distribution/macos/installer.py": (
        "80b9327640c46e4d8b0622126cdca711596397d1a2f6d22da773526feadaf1ed"
    ),
    "src/ultimate_ai_agent/distribution/macos/runtime.py": (
        "cdf91f507b674185e07e481bf48c452fd491067784a7ee62b72cb018b35e7004"
    ),
}

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
    "fcntl.",
    "os.",
    "platform.",
    "plistlib.",
    "shutil.",
    "signal.",
    _SOCKET_DOT,
    "stat.",
    _SUBPROCESS_DOT,
    "sys.",
    "tarfile.",
    "tempfile.",
    "time.",
    "urllib.",
    "webbrowser.",
    "root.",
)
_SENSITIVE_FILESYSTEM_METHODS = frozenset(
    {
        "chmod",
        "exists",
        "glob",
        "is_dir",
        "is_file",
        "iterdir",
        "joinpath",
        "mkdir",
        "open",
        "read_bytes",
        "read_text",
        "relative_to",
        "rename",
        "replace",
        "resolve",
        "rglob",
        "rmdir",
        "stat",
        "symlink_to",
        "unlink",
        "write_bytes",
        "write_text",
    }
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
        "open",
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
        "shutil.which": 1,
        "urllib.parse.urlparse": 2,
        "urllib.request.Request": 1,
        "urllib.request.build_opener": 1,
    },
    "src/ultimate_ai_agent/distribution/macos/installer.py": {
        "Path": 13,
        "Path.home": 3,
        "fcntl.flock": 2,
        "os.access": 2,
        "os.replace": 7,
        "plistlib.load": 1,
        "root.joinpath": 1,
        "root.resolve": 1,
        "root.rglob": 1,
        "shutil.copytree": 1,
        "shutil.rmtree": 8,
        "stat.S_IMODE": 2,
        _SUBPROCESS_RUN: 4,
        "tarfile.open": 1,
        "tempfile.TemporaryDirectory": 1,
        "time.time": 1,
    },
    "src/ultimate_ai_agent/distribution/macos/runtime.py": {
        "Path": 2,
        "getattr": 2,
        "os.environ.get": 1,
        "os.environ.items": 1,
        "os.execv": 1,
        "os.kill": 4,
        "os.replace": 2,
        "platform.system": 1,
        _SOCKET_SOCKET: 1,
        _SUBPROCESS_POPEN: 1,
        _SUBPROCESS_RUN: 1,
        "tempfile.TemporaryDirectory": 1,
        "time.monotonic": 4,
        "time.sleep": 2,
        "urllib.parse.quote": 1,
        "urllib.request.Request": 1,
        _URLLIB_URLOPEN: 1,
        "webbrowser.open": 2,
    },
}

_EXPECTED_FILESYSTEM_METHOD_COUNTS = {
    "src/ultimate_ai_agent/distribution/macos/github_releases.py": {
        "exists": 1,
        "is_file": 1,
        "mkdir": 1,
        "open": 3,
        "replace": 1,
        "unlink": 4,
    },
    "src/ultimate_ai_agent/distribution/macos/installer.py": {
        "chmod": 5,
        "exists": 14,
        "is_dir": 3,
        "is_file": 9,
        "iterdir": 1,
        "joinpath": 2,
        "mkdir": 14,
        "open": 4,
        "read_bytes": 1,
        "read_text": 6,
        "relative_to": 3,
        "replace": 8,
        "resolve": 4,
        "rglob": 1,
        "stat": 6,
        "symlink_to": 1,
        "unlink": 7,
        "write_bytes": 1,
        "write_text": 2,
    },
    "src/ultimate_ai_agent/distribution/macos/runtime.py": {
        "chmod": 2,
        "is_dir": 1,
        "is_file": 5,
        "mkdir": 4,
        "open": 2,
        "read_bytes": 1,
        "read_text": 2,
        "replace": 3,
        "unlink": 5,
        "write_text": 2,
    },
}

_ALLOWED_EXTERNAL_ATTRIBUTES = {
    "src/ultimate_ai_agent/distribution/macos/github_releases.py": {
        "os.X_OK",
        "os.access",
        "os.environ",
        "shutil.which",
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
        "fcntl.LOCK_EX",
        "fcntl.LOCK_NB",
        "fcntl.LOCK_UN",
        "fcntl.flock",
        "os.W_OK",
        "os.X_OK",
        "os.access",
        "os.environ",
        "os.replace",
        "Path.home",
        "plistlib.InvalidFileException",
        "plistlib.load",
        "shutil.copytree",
        "shutil.rmtree",
        "stat.S_IMODE",
        _SUBPROCESS_DOT + "DEVNULL",
        _SUBPROCESS_RUN,
        "tarfile.TarError",
        "tarfile.open",
        "tempfile.TemporaryDirectory",
        "time.time",
    },
    "src/ultimate_ai_agent/distribution/macos/runtime.py": {
        "os.environ",
        "os.environ.get",
        "os.environ.items",
        "os.execv",
        "os.kill",
        "os.replace",
        "platform.system",
        "signal.SIGKILL",
        "signal.SIGTERM",
        "sys.executable",
        _SOCKET_DOT + "AF_INET",
        _SOCKET_DOT + "SOCK_STREAM",
        _SOCKET_SOCKET,
        _SUBPROCESS_DOT + "DEVNULL",
        _SUBPROCESS_POPEN,
        _SUBPROCESS_RUN,
        "tempfile.TemporaryDirectory",
        "time.monotonic",
        "time.sleep",
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
        "shutil",
        "subprocess",
        "urllib.error",
        "urllib.parse",
        "urllib.request",
    },
    "src/ultimate_ai_agent/distribution/macos/installer.py": {
        "fcntl",
        "os",
        "plistlib",
        "shutil",
        "stat",
        "subprocess",
        "tarfile",
        "tempfile",
        "time",
    },
    "src/ultimate_ai_agent/distribution/macos/runtime.py": {
        "os",
        "platform",
        "signal",
        "socket",
        "subprocess",
        "sys",
        "tempfile",
        "time",
        "urllib.error",
        "urllib.parse",
        "urllib.request",
        "webbrowser",
    },
}
_HOST_MODULE_NAMES = frozenset(
    {
        "builtins",
        "fcntl",
        "importlib",
        "os",
        "platform",
        "plistlib",
        "shutil",
        "signal",
        "socket",
        "stat",
        "subprocess",
        "sys",
        "tarfile",
        "tempfile",
        "time",
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
    source_sha256 = hashlib.sha256(source.encode("utf-8")).hexdigest()
    if source_sha256 != _EXPECTED_SOURCE_SHA256[rel_path]:
        failures.append(f"{rel_path}: reviewed adapter source digest changed")
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
                    "fcntl.",
                    "platform.",
                    "plistlib.",
                    "shutil.",
                    "signal.",
                    _SOCKET_DOT,
                    "stat.",
                    _SUBPROCESS_DOT,
                    "sys.",
                    "tarfile.",
                    "tempfile.",
                    "time.",
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
    actual_filesystem_method_counts: dict[str, int] = {}
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
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in _SENSITIVE_FILESYSTEM_METHODS
        ):
            method_name = node.func.attr
            actual_filesystem_method_counts[method_name] = (
                actual_filesystem_method_counts.get(method_name, 0) + 1
            )
        for keyword in node.keywords:
            if keyword.arg == "shell" and not (
                isinstance(keyword.value, ast.Constant)
                and keyword.value.value is False
            ):
                failures.append(
                    f"{rel_path}: shell execution must remain literal-false"
                )

    expected_counts = _EXPECTED_CALL_COUNTS[rel_path]
    if actual_counts != expected_counts:
        failures.append(f"{rel_path}: reviewed host-capability call shape changed")
    if (
        actual_filesystem_method_counts
        != _EXPECTED_FILESYSTEM_METHOD_COUNTS[rel_path]
    ):
        failures.append(f"{rel_path}: reviewed filesystem method shape changed")
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

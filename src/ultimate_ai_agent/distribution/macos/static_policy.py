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
import json
from pathlib import Path


MACOS_DISTRIBUTION_EXACT_ADAPTER_FILES = frozenset(
    {
        "src/ultimate_ai_agent/distribution/macos/github_releases.py",
        "src/ultimate_ai_agent/distribution/macos/installer.py",
        "src/ultimate_ai_agent/distribution/macos/runtime.py",
    }
)
_EXPECTED_SOURCE_SHA256 = {
    "src/ultimate_ai_agent/distribution/macos/github_releases.py": "d61e6b1adab449d8849ecb97632ec680514531d2097be7d8bf870bd0bf86a606",
    "src/ultimate_ai_agent/distribution/macos/installer.py": "031038be4899c6afbec59321ae153a852f8a8ee54fc37f406e030e74a015353d",
    "src/ultimate_ai_agent/distribution/macos/runtime.py": "f52c4bdd0f40bcc2040bf16cab319fb3dd161955f32039f697f68747924a5d44",
}

# Runtime imports use this exact stdlib-only dependency closure. These files
# receive no adapter fragment exemptions. Raw bytes and executable AST shapes
# are independently pinned; the transport filter also has a closed source shape.
MACOS_DISTRIBUTION_EXACT_DEPENDENCY_FILES = frozenset(
    {
        'src/ultimate_ai_agent/__init__.py',
        'src/ultimate_ai_agent/core/finance_managed_profile.py',
        'src/ultimate_ai_agent/core/private_path_security.py',
        "src/ultimate_ai_agent/core/__init__.py",
        "src/ultimate_ai_agent/core/finance_startup.py",
    }
)
_EXPECTED_DEPENDENCY_SHA256 = {
    "src/ultimate_ai_agent/__init__.py": "7842fb134bd253ce7b9cbe80b73a76fcdf5732fc4a03f416f128927bb83cde4e",
    "src/ultimate_ai_agent/core/__init__.py": "471b6cc8feea1f27f0eb6b46f7251209d7801999c40bf87217d3701b2632380e",
    "src/ultimate_ai_agent/core/finance_managed_profile.py": "5f13d90dd74c740bc96d1f870d9e7f55c9152c8e1c55b9532727ecc51d093eca",
    "src/ultimate_ai_agent/core/finance_startup.py": "76f7848c23960fef863881d60f53757ec2096d24aa15af4c4d6b95c11b3643b2",
    "src/ultimate_ai_agent/core/private_path_security.py": "c955b455e2d6a38f20bc0fcdefe7c4c9b35170cf583938dc6fc7d37f12d3a868",
}

# Independently pin executable AST shapes as well as raw bytes. Updating only
# a source digest cannot admit changed behavior in the larger stdlib closure.
_EXPECTED_DEPENDENCY_AST_SHA256 = {
    "src/ultimate_ai_agent/__init__.py": "4b669d3ae271d50bfd171cd1687d3c3bf257890909e7cbe64bf18118806610bc",
    "src/ultimate_ai_agent/core/finance_managed_profile.py": "bd028127f34d61187f1d380e8ddee29360364b0ddeb4f4d1f25b0210cabfdb86",
    "src/ultimate_ai_agent/core/private_path_security.py": "af0c04b882996374baedbc358fbf856aff43773f6599e095e233a58154f83031",
}
_REVIEWED_FINANCE_STARTUP_IMPLEMENTATION = r'''
from __future__ import annotations
from collections.abc import Mapping
from dataclasses import replace
import hashlib
import json
from ultimate_ai_agent.core.finance_managed_profile import FINANCE_CONFIGURATION_ENV_NAMES, FINANCE_EXPLICIT_ENV_NAMES, FINANCE_WORKSPACE_DISABLE_ENV as FINANCE_WORKSPACE_DISABLE_ENV, FINANCE_WORKSPACE_HELPER_DIGEST_ENV as FINANCE_WORKSPACE_HELPER_DIGEST_ENV, FINANCE_WORKSPACE_HELPER_ENV as FINANCE_WORKSPACE_HELPER_ENV, FINANCE_WORKSPACE_REPOSITORY_ENV as FINANCE_WORKSPACE_REPOSITORY_ENV, FinanceConfigurationResolution, FinanceManagedLayout, resolve_finance_configuration
FINANCE_STARTUP_MODE_ENV = 'UAA_FINANCE_STARTUP_MODE'
FINANCE_STARTUP_ENV_NAMES = (*FINANCE_CONFIGURATION_ENV_NAMES, FINANCE_STARTUP_MODE_ENV)
FINANCE_STARTUP_METADATA_KEY = 'finance_startup_configuration_ref'
_IDENTITY_DOMAIN = b'uaa:finance-startup-configuration:v2\x00'

def finance_startup_environment(environ: Mapping[str, str]) -> dict[str, str]:
    return {name: environ[name] for name in FINANCE_STARTUP_ENV_NAMES if name in environ}

def capture_finance_startup_environment(environ: Mapping[str, str], layout: FinanceManagedLayout | None=None) -> dict[str, str]:
    resolution = resolve_finance_configuration(environ, layout)
    snapshot = dict(resolution.effective_environment)
    snapshot[FINANCE_STARTUP_MODE_ENV] = resolution.mode
    return snapshot

def consume_finance_startup_environment(environ: Mapping[str, str], layout: FinanceManagedLayout | None=None) -> FinanceConfigurationResolution:
    if FINANCE_STARTUP_MODE_ENV not in environ:
        return resolve_finance_configuration(environ, layout)
    mode = environ[FINANCE_STARTUP_MODE_ENV]
    effective = tuple(((name, environ[name]) for name in FINANCE_CONFIGURATION_ENV_NAMES if name in environ))
    if mode == 'absent' and (not any((name in environ for name in FINANCE_EXPLICIT_ENV_NAMES))):
        return FinanceConfigurationResolution(mode='absent', effective_environment=effective, repository_dir=None, helper_path=None, helper_sha256=None, profile_ref=None, state_ref=None, error_code=None)
    if mode in {'explicit', 'managed'} and all((name in environ for name in FINANCE_EXPLICIT_ENV_NAMES)):
        resolution = resolve_finance_configuration(dict(effective), layout)
        if resolution.mode == 'explicit':
            return replace(resolution, mode=mode)
        return resolution
    return FinanceConfigurationResolution(mode='invalid', effective_environment=effective, repository_dir=None, helper_path=None, helper_sha256=None, profile_ref=None, state_ref=None, error_code='FIN003_MANAGED_STARTUP_MODE_INVALID')

def finance_startup_configuration_ref(environ: Mapping[str, str]) -> str:
    encoded = json.dumps(finance_startup_environment(environ), sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')
    digest = hashlib.sha256(_IDENTITY_DOMAIN + encoded).hexdigest()
    return f'configuration-ref:finance-startup:sha256:{digest}'

def finance_startup_configuration_matches(recorded_ref: object, environ: Mapping[str, str]) -> bool:
    return isinstance(recorded_ref, str) and recorded_ref == finance_startup_configuration_ref(environ)
'''

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
        "lstat",
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
        "os.close": 4,
        "os.fstat": 6,
        "os.getuid": 2,
        "os.listdir": 3,
        "os.lseek": 1,
        "os.open": 2,
        "os.read": 2,
        "os.readlink": 2,
        "os.replace": 7,
        "os.stat": 6,
        "plistlib.load": 1,
        "plistlib.loads": 1,
        "root.joinpath": 1,
        "root.resolve": 1,
        "root.rglob": 1,
        "shutil.copytree": 1,
        "shutil.rmtree": 8,
        "stat.S_IMODE": 4,
        "stat.S_ISLNK": 1,
        _SUBPROCESS_DOT + 'Popen': 1,
        _SUBPROCESS_DOT + 'run': 4,
        "tarfile.open": 1,
        "tempfile.TemporaryDirectory": 1,
        "time.monotonic": 3,
        "time.time": 1,
    },
    "src/ultimate_ai_agent/distribution/macos/runtime.py": {
        "Path": 2,
        "Path.cwd": 1,
        "getattr": 2,
        "os.close": 1,
        "os.environ.get": 1,
        "os.environ.items": 1,
        "os.execv": 1,
        "os.fstat": 3,
        "os.getuid": 1,
        "os.kill": 4,
        "os.open": 3,
        "os.read": 1,
        "os.replace": 2,
        "os.stat": 4,
        "platform.system": 1,
        _SOCKET_DOT + 'socket': 1,
        "stat.S_ISDIR": 1,
        _SUBPROCESS_DOT + 'Popen': 1,
        _SUBPROCESS_DOT + 'run': 1,
        "tempfile.TemporaryDirectory": 1,
        "time.monotonic": 6,
        "time.sleep": 3,
        "urllib.parse.quote": 1,
        "urllib.request.Request": 1,
        "urllib.request.urlopen": 1,
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
        "open": 6,
        "read_bytes": 1,
        "read_text": 6,
        "relative_to": 3,
        "replace": 8,
        "resolve": 4,
        "rglob": 1,
        "stat": 12,
        "symlink_to": 1,
        "unlink": 7,
        "write_bytes": 1,
        "write_text": 2,
    },
    "src/ultimate_ai_agent/distribution/macos/runtime.py": {
        "chmod": 2,
        "is_dir": 1,
        "is_file": 5,
        "lstat": 1,
        "mkdir": 4,
        "open": 5,
        "read_bytes": 1,
        "read_text": 2,
        "replace": 3,
        "resolve": 2,
        "stat": 4,
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
        _SUBPROCESS_DOT + 'CompletedProcess',
        _SUBPROCESS_DOT + 'SubprocessError',
        _SUBPROCESS_DOT + 'run',
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
        "Path.home",
        "fcntl.LOCK_EX",
        "fcntl.LOCK_NB",
        "fcntl.LOCK_UN",
        "fcntl.flock",
        "os.O_CLOEXEC",
        "os.O_DIRECTORY",
        "os.O_NOFOLLOW",
        "os.O_NONBLOCK",
        "os.O_RDONLY",
        "os.SEEK_SET",
        "os.W_OK",
        "os.X_OK",
        "os.access",
        "os.close",
        "os.environ",
        "os.fstat",
        "os.getuid",
        "os.listdir",
        "os.lseek",
        "os.open",
        "os.read",
        "os.readlink",
        "os.replace",
        "os.stat",
        "os.stat_result",
        "plistlib.InvalidFileException",
        "plistlib.load",
        "plistlib.loads",
        "shutil.copytree",
        "shutil.rmtree",
        "stat.S_IMODE",
        "stat.S_ISDIR",
        "stat.S_ISLNK",
        "stat.S_ISREG",
        "stat.S_IXUSR",
        _SUBPROCESS_DOT + 'DEVNULL',
        _SUBPROCESS_DOT + 'PIPE',
        _SUBPROCESS_DOT + 'Popen',
        _SUBPROCESS_DOT + 'STDOUT',
        _SUBPROCESS_DOT + 'SubprocessError',
        _SUBPROCESS_DOT + 'run',
        "tarfile.TarError",
        "tarfile.open",
        "tempfile.TemporaryDirectory",
        "time.monotonic",
        "time.time",
    },
    "src/ultimate_ai_agent/distribution/macos/runtime.py": {
        "Path.cwd",
        "os.O_CLOEXEC",
        "os.O_DIRECTORY",
        "os.O_NOFOLLOW",
        "os.O_NONBLOCK",
        "os.O_RDONLY",
        "os.close",
        "os.environ",
        "os.environ.get",
        "os.environ.items",
        "os.execv",
        "os.fstat",
        "os.getuid",
        "os.kill",
        "os.open",
        "os.read",
        "os.replace",
        "os.stat",
        "os.stat_result",
        "os.supports_dir_fd",
        "os.supports_follow_symlinks",
        "platform.system",
        "signal.SIGKILL",
        "signal.SIGTERM",
        _SOCKET_DOT + 'AF_INET',
        _SOCKET_DOT + 'SOCK_STREAM',
        _SOCKET_DOT + 'socket',
        "stat.S_ISDIR",
        "stat.S_ISVTX",
        _SUBPROCESS_DOT + 'DEVNULL',
        _SUBPROCESS_DOT + 'Popen',
        _SUBPROCESS_DOT + 'run',
        "sys.executable",
        "tempfile.TemporaryDirectory",
        "time.monotonic",
        "time.sleep",
        "urllib.error",
        "urllib.error.URLError",
        "urllib.parse",
        "urllib.parse.quote",
        "urllib.request",
        "urllib.request.Request",
        "urllib.request.urlopen",
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
        "stat",
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
    """Validate every required adapter and its exact delegated dependencies."""

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
    for rel_path in sorted(MACOS_DISTRIBUTION_EXACT_DEPENDENCY_FILES):
        try:
            source = (root / rel_path).read_bytes().decode("utf-8")
        except (OSError, UnicodeError):
            failures.append(f"{rel_path}: required distribution dependency is unavailable")
            continue
        failures.extend(_distribution_dependency_policy_failures(rel_path, source))
    return failures


def _dependency_ast_shape(node: object) -> object:
    """Version-neutral AST shape; only empty Python 3.12 type parameters elide.

    Nonempty type parameters and all other executable fields remain bound.
    Source-byte pins independently retain every byte, including docstrings.
    """

    if isinstance(node, ast.AST):
        return [type(node).__name__, [
            [name, _dependency_ast_shape(value)]
            for name, value in ast.iter_fields(node)
            if not (name == "type_params" and value == [])
        ]]
    if isinstance(node, list):
        return [_dependency_ast_shape(value) for value in node]
    if isinstance(node, bytes):
        return ["bytes", node.hex()]
    if isinstance(node, float):
        return ["float", node.hex()]
    if isinstance(node, complex):
        return ["complex", node.real.hex(), node.imag.hex()]
    if node is Ellipsis:
        return ["ellipsis"]
    return node


def _dependency_ast_sha256(tree: ast.AST) -> str:
    encoded = json.dumps(
        _dependency_ast_shape(tree), ensure_ascii=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _distribution_dependency_policy_failures(rel_path: str, source: str) -> list[str]:
    failures: list[str] = []
    source_sha256 = hashlib.sha256(source.encode("utf-8")).hexdigest()
    if source_sha256 != _EXPECTED_DEPENDENCY_SHA256[rel_path]:
        failures.append(f"{rel_path}: reviewed dependency source digest changed")
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return failures + [f"{rel_path}: distribution dependency is not valid Python"]

    # Ignore only literal module/function docstrings. All executable statements,
    # imports, annotations, defaults, decorators, calls and payload selection
    # remain part of the closed shape, independent of the source digest pin.
    for node in ast.walk(tree):
        if (
            isinstance(node, (ast.Module, ast.FunctionDef))
            and ast.get_docstring(node) is not None
        ):
            node.body.pop(0)
    reviewed_source = (
        _REVIEWED_FINANCE_STARTUP_IMPLEMENTATION
        if rel_path.endswith("/finance_startup.py")
        else ""
    )
    shape = ast.dump(tree, include_attributes=False)
    if rel_path in _EXPECTED_DEPENDENCY_AST_SHA256:
        matches = _dependency_ast_sha256(tree) == _EXPECTED_DEPENDENCY_AST_SHA256[rel_path]
    else:
        matches = shape == ast.dump(ast.parse(reviewed_source), include_attributes=False)
    if not matches:
        failures.append(f"{rel_path}: reviewed dependency implementation changed")
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

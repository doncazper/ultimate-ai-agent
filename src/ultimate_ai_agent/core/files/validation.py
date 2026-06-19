from pathlib import PurePosixPath
from urllib.parse import unquote

from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


BLOCKED_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
}

BLOCKED_SUFFIXES = (".pem", ".key", ".p12", ".pfx")
GLOB_META_CHARS = frozenset("*?[]{}")
MAX_RELATIVE_PATH_LENGTH = 512


def normalize_relative_path(path: str) -> str:
    if not path or not path.strip():
        raise ValueError("File path cannot be empty.")
    if len(path) > MAX_RELATIVE_PATH_LENGTH:
        raise ValueError("File path is too long.")
    if "\\" in path:
        raise ValueError("Backslash file paths are rejected.")
    if any(char in path for char in GLOB_META_CHARS):
        raise ValueError("Glob-style file paths are rejected.")
    if contains_obvious_secret({"path": path}):
        raise ValueError("Secret-like file paths are rejected.")
    decoded = unquote(path)
    if decoded != path and (".." in decoded or "/" in decoded or "\\" in decoded or decoded.startswith("~")):
        raise ValueError("Encoded unsafe file paths are rejected.")
    if path.startswith("/") or PurePosixPath(path).is_absolute():
        raise ValueError("absolute file paths are rejected by default.")
    if path.startswith("~"):
        raise ValueError("Home-relative file paths are rejected.")
    normalized = PurePosixPath(path)
    if any(part == ".." for part in normalized.parts):
        raise ValueError("Path traversal is rejected.")
    if any(part in ("", ".") for part in normalized.parts):
        normalized = PurePosixPath(*[part for part in normalized.parts if part not in ("", ".")])
    parts = normalized.parts
    if parts and len(parts[0]) >= 2 and parts[0][1] == ":":
        raise ValueError("Drive-qualified file paths are rejected.")
    if any(part.startswith(".") for part in parts):
        raise ValueError("Blocked hidden file path segments are rejected.")
    return str(normalized)


def is_blocked_file_path(path: str) -> bool:
    normalized = normalize_relative_path(path)
    parts = PurePosixPath(normalized).parts
    name = parts[-1].lower() if parts else normalized.lower()
    return name in BLOCKED_FILE_NAMES or name.endswith(BLOCKED_SUFFIXES) or ".ssh" in [part.lower() for part in parts]


def validate_safe_file_path(path: str) -> str:
    normalized = normalize_relative_path(path)
    if is_blocked_file_path(normalized):
        raise ValueError("Blocked credential-like file path.")
    return normalized


def file_content_contains_secret(content: str) -> bool:
    return contains_obvious_secret({"content": content})

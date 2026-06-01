from pydantic import ValidationError

from ultimate_ai_agent.core.files import FileKind, FileRef, FileSensitivity


def test_file_ref_rejects_absolute_path():
    try:
        FileRef(
            file_ref="file_abs",
            path="/tmp/outside.txt",
            kind=FileKind.artifact,
            sensitivity=FileSensitivity.project_private,
        )
    except ValidationError as exc:
        assert "absolute" in str(exc).lower()
    else:
        raise AssertionError("Expected absolute path validation failure")


def test_file_ref_rejects_traversal_path():
    try:
        FileRef(
            file_ref="file_traversal",
            path="../secret.txt",
            kind=FileKind.artifact,
            sensitivity=FileSensitivity.project_private,
        )
    except ValidationError as exc:
        assert "traversal" in str(exc).lower()
    else:
        raise AssertionError("Expected traversal validation failure")


def test_file_ref_rejects_secret_like_path():
    try:
        FileRef(
            file_ref="file_env",
            path=".env",
            kind=FileKind.artifact,
            sensitivity=FileSensitivity.credential_secret,
        )
    except ValidationError as exc:
        assert "blocked" in str(exc).lower()
    else:
        raise AssertionError("Expected blocked secret path validation failure")

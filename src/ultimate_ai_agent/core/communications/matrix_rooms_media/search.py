from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import stat
from dataclasses import dataclass
from pathlib import Path

from ultimate_ai_agent.core.communications.matrix_sync.cache import (
    MatrixCacheCryptoBackend,
)
from ultimate_ai_agent.core.execution.validation import validate_execution_ref

from .contracts import stable_matrix_rooms_media_ref


_MAGIC = b"UAA-MATRIX-SEARCH-V1\x00"
_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{1,63}")
_MAX_INDEX_BYTES = 2 * 1024 * 1024
_MAX_DOCUMENTS = 10_000
_MAX_DOCUMENT_BODY_BYTES = 16 * 1024
_MAX_TOTAL_BODY_BYTES = 4 * 1024 * 1024
_MAX_QUERY_BYTES = 4 * 1024
_MAX_ALLOWED_ROOMS = 256
_MAX_TOKENS_PER_DOCUMENT = 256


class MatrixEncryptedSearchError(RuntimeError):
    pass


@dataclass(frozen=True)
class MatrixSearchDocument:
    room_ref: str
    event_ref: str
    body: str


class MatrixEncryptedSearchIndex:
    """Encrypted HMAC-token index; raw bodies and queries are never persisted."""

    def __init__(
        self,
        *,
        root: Path,
        crypto_backend: MatrixCacheCryptoBackend,
        key_item_ref: str,
        key_version_ref: str,
        token_key: bytes,
    ) -> None:
        if len(token_key) != 32:
            raise ValueError("MATRIX_SEARCH_TOKEN_KEY_INVALID")
        if not root.is_absolute() or root == Path(root.anchor):
            raise ValueError("MATRIX_SEARCH_ROOT_UNSAFE")
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = os.lstat(root)
        if (
            not stat.S_ISDIR(info.st_mode)
            or stat.S_ISLNK(info.st_mode)
            or info.st_uid != os.geteuid()
        ):
            raise ValueError("MATRIX_SEARCH_ROOT_UNSAFE")
        os.chmod(root, 0o700)
        info = os.lstat(root)
        self._root = root
        self._root_identity = (info.st_dev, info.st_ino)
        self._crypto_backend = crypto_backend
        self._key_item_ref = key_item_ref
        self._key_version_ref = key_version_ref
        self._token_key = bytes(token_key)
        self.binding_ref = stable_matrix_rooms_media_ref(
            "search-index-binding-ref:matrix",
            {"key_item_ref": key_item_ref, "key_version_ref": key_version_ref},
        )

    def _verify_root(self) -> None:
        try:
            info = os.lstat(self._root)
        except OSError as exc:
            raise MatrixEncryptedSearchError(
                "MATRIX_SEARCH_ROOT_SUBSTITUTION_DENIED"
            ) from exc
        if (
            not stat.S_ISDIR(info.st_mode)
            or stat.S_ISLNK(info.st_mode)
            or info.st_uid != os.geteuid()
            or info.st_mode & 0o077
            or (info.st_dev, info.st_ino) != self._root_identity
        ):
            raise MatrixEncryptedSearchError("MATRIX_SEARCH_ROOT_SUBSTITUTION_DENIED")

    def _open_root(self) -> int:
        try:
            descriptor = os.open(
                self._root,
                os.O_RDONLY
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0),
            )
        except OSError as exc:
            raise MatrixEncryptedSearchError(
                "MATRIX_SEARCH_ROOT_SUBSTITUTION_DENIED"
            ) from exc
        try:
            info = os.fstat(descriptor)
        except OSError as exc:
            os.close(descriptor)
            raise MatrixEncryptedSearchError(
                "MATRIX_SEARCH_ROOT_SUBSTITUTION_DENIED"
            ) from exc
        if (
            not stat.S_ISDIR(info.st_mode)
            or info.st_uid != os.geteuid()
            or info.st_mode & 0o077
            or (info.st_dev, info.st_ino) != self._root_identity
        ):
            os.close(descriptor)
            raise MatrixEncryptedSearchError("MATRIX_SEARCH_ROOT_SUBSTITUTION_DENIED")
        return descriptor

    @staticmethod
    def _name(index_ref: str) -> str:
        return f"{hashlib.sha256(index_ref.encode()).hexdigest()}.uaamxsearch"

    def _token(self, value: str) -> str:
        return hmac.new(
            self._token_key, value.casefold().encode(), hashlib.sha256
        ).hexdigest()

    def rebuild(
        self,
        *,
        index_ref: str,
        account_ref: str,
        generation_ref: str,
        documents: tuple[MatrixSearchDocument, ...],
        allowed_room_refs: frozenset[str],
        max_documents: int = 10_000,
    ) -> str:
        if not 1 <= max_documents <= _MAX_DOCUMENTS or len(documents) > max_documents:
            raise MatrixEncryptedSearchError("MATRIX_SEARCH_DOCUMENT_LIMIT_EXCEEDED")
        if not 1 <= len(allowed_room_refs) <= _MAX_ALLOWED_ROOMS:
            raise MatrixEncryptedSearchError("MATRIX_SEARCH_ROOM_LIMIT_INVALID")
        try:
            for value in (index_ref, account_ref, generation_ref, *allowed_room_refs):
                validate_execution_ref(value, "matrix_search_rebuild_ref")
        except ValueError as exc:
            raise MatrixEncryptedSearchError("MATRIX_SEARCH_REF_INVALID") from exc
        entries: list[dict[str, object]] = []
        seen_events: set[str] = set()
        total_body_bytes = 0
        for document in documents:
            if document.room_ref not in allowed_room_refs:
                raise MatrixEncryptedSearchError(
                    "MATRIX_SEARCH_CROSS_ROOM_INDEX_DENIED"
                )
            if document.event_ref in seen_events:
                raise MatrixEncryptedSearchError("MATRIX_SEARCH_DUPLICATE_EVENT_DENIED")
            try:
                validate_execution_ref(document.event_ref, "matrix_search_event_ref")
            except ValueError as exc:
                raise MatrixEncryptedSearchError("MATRIX_SEARCH_REF_INVALID") from exc
            body_bytes = len(document.body.encode("utf-8"))
            total_body_bytes += body_bytes
            if (
                body_bytes > _MAX_DOCUMENT_BODY_BYTES
                or total_body_bytes > _MAX_TOTAL_BODY_BYTES
            ):
                raise MatrixEncryptedSearchError("MATRIX_SEARCH_CONTENT_LIMIT_EXCEEDED")
            seen_events.add(document.event_ref)
            tokens = sorted(
                {self._token(token) for token in _TOKEN_RE.findall(document.body)}
            )
            if len(tokens) > _MAX_TOKENS_PER_DOCUMENT:
                raise MatrixEncryptedSearchError("MATRIX_SEARCH_TOKEN_LIMIT_EXCEEDED")
            entries.append(
                {
                    "room_ref": document.room_ref,
                    "event_ref": document.event_ref,
                    "tokens": tokens,
                }
            )
        state = {
            "schema_ref": "search-index-schema-ref:matrix:encrypted-hmac-v1",
            "index_ref": index_ref,
            "account_ref": account_ref,
            "generation_ref": generation_ref,
            "entries": entries,
            "raw_content_included": False,
        }
        plaintext = json.dumps(state, sort_keys=True, separators=(",", ":")).encode()
        if len(plaintext) > _MAX_INDEX_BYTES - 1024:
            raise MatrixEncryptedSearchError("MATRIX_SEARCH_INDEX_SIZE_EXCEEDED")
        aad = f"{index_ref}\0{account_ref}\0{self._key_version_ref}".encode()
        ciphertext = _MAGIC + self._crypto_backend.encrypt(
            key_item_ref=self._key_item_ref,
            key_version_ref=self._key_version_ref,
            plaintext=plaintext,
            aad=aad,
        )
        root_fd = self._open_root()
        name = self._name(index_ref)
        stage_name = f"{name}.stage-{secrets.token_hex(8)}"
        try:
            fd = os.open(
                stage_name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                0o600,
                dir_fd=root_fd,
            )
            try:
                _write_all(fd, ciphertext)
                os.fsync(fd)
            finally:
                os.close(fd)
            os.replace(
                stage_name,
                name,
                src_dir_fd=root_fd,
                dst_dir_fd=root_fd,
            )
            os.fsync(root_fd)
        except OSError as exc:
            raise MatrixEncryptedSearchError(
                "MATRIX_SEARCH_INDEX_WRITE_FAILED"
            ) from exc
        finally:
            try:
                os.unlink(stage_name, dir_fd=root_fd)
            except FileNotFoundError:
                pass
            except OSError as exc:
                raise MatrixEncryptedSearchError(
                    "MATRIX_SEARCH_STAGE_CLEANUP_FAILED"
                ) from exc
            finally:
                os.close(root_fd)
        return stable_matrix_rooms_media_ref(
            "receipt-ref:matrix-search:rebuild",
            {
                "index_ref": index_ref,
                "generation_ref": generation_ref,
                "document_count": len(entries),
            },
        )

    def search(
        self,
        *,
        index_ref: str,
        account_ref: str,
        query: str,
        allowed_room_refs: frozenset[str],
        exact_room_ref: str | None,
        max_results: int,
    ) -> tuple[str, ...]:
        if not 1 <= max_results <= 100:
            raise MatrixEncryptedSearchError("MATRIX_SEARCH_RESULT_LIMIT_INVALID")
        if len(query.encode("utf-8")) > _MAX_QUERY_BYTES:
            raise MatrixEncryptedSearchError("MATRIX_SEARCH_QUERY_LIMIT_EXCEEDED")
        if not 1 <= len(allowed_room_refs) <= _MAX_ALLOWED_ROOMS:
            raise MatrixEncryptedSearchError("MATRIX_SEARCH_ROOM_LIMIT_INVALID")
        if exact_room_ref is not None and exact_room_ref not in allowed_room_refs:
            raise MatrixEncryptedSearchError("MATRIX_SEARCH_ROOM_SCOPE_DENIED")
        query_tokens = {self._token(token) for token in _TOKEN_RE.findall(query)}
        if not query_tokens:
            return ()
        state = self._read(index_ref=index_ref, account_ref=account_ref)
        results: list[str] = []
        for entry in state["entries"]:
            room_ref = entry["room_ref"]
            if room_ref not in allowed_room_refs:
                raise MatrixEncryptedSearchError(
                    "MATRIX_SEARCH_CROSS_ROOM_INDEX_DENIED"
                )
            if exact_room_ref is not None and room_ref != exact_room_ref:
                continue
            if query_tokens <= set(entry["tokens"]):
                results.append(entry["event_ref"])
                if len(results) == max_results:
                    break
        return tuple(results)

    def purge(self, *, index_ref: str) -> str:
        root_fd = self._open_root()
        name = self._name(index_ref)
        try:
            try:
                info = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
                if (
                    not stat.S_ISREG(info.st_mode)
                    or stat.S_ISLNK(info.st_mode)
                    or info.st_nlink != 1
                    or info.st_uid != os.geteuid()
                    or info.st_mode & 0o077
                ):
                    raise MatrixEncryptedSearchError(
                        "MATRIX_SEARCH_PATH_SUBSTITUTION_DENIED"
                    )
                os.unlink(name, dir_fd=root_fd)
                os.fsync(root_fd)
            except FileNotFoundError:
                pass
            except OSError as exc:
                raise MatrixEncryptedSearchError("MATRIX_SEARCH_PURGE_FAILED") from exc
            try:
                os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise MatrixEncryptedSearchError("MATRIX_SEARCH_INCOMPLETE_CLEANUP")
        finally:
            os.close(root_fd)
        return stable_matrix_rooms_media_ref(
            "receipt-ref:matrix-search:purge",
            {"index_ref": index_ref, "path_absent": True},
        )

    def _read(self, *, index_ref: str, account_ref: str) -> dict[str, object]:
        root_fd = self._open_root()
        try:
            fd = os.open(
                self._name(index_ref),
                os.O_RDONLY
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_NONBLOCK", 0),
                dir_fd=root_fd,
            )
        except OSError as exc:
            os.close(root_fd)
            raise MatrixEncryptedSearchError("MATRIX_SEARCH_INDEX_UNAVAILABLE") from exc
        try:
            info = os.fstat(fd)
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_nlink != 1
                or info.st_uid != os.geteuid()
                or info.st_mode & 0o077
                or info.st_size > _MAX_INDEX_BYTES
            ):
                raise MatrixEncryptedSearchError("MATRIX_SEARCH_INDEX_INVALID")
            ciphertext = _read_bounded(fd)
        finally:
            os.close(fd)
            os.close(root_fd)
        if not ciphertext.startswith(_MAGIC):
            raise MatrixEncryptedSearchError("MATRIX_SEARCH_INDEX_INVALID")
        aad = f"{index_ref}\0{account_ref}\0{self._key_version_ref}".encode()
        try:
            plaintext = self._crypto_backend.decrypt(
                key_item_ref=self._key_item_ref,
                key_version_ref=self._key_version_ref,
                ciphertext=ciphertext[len(_MAGIC) :],
                aad=aad,
            )
            state = json.loads(plaintext)
        except Exception as exc:
            raise MatrixEncryptedSearchError(
                "MATRIX_SEARCH_INDEX_INTEGRITY_FAILED"
            ) from exc
        if not _valid_state(state):
            raise MatrixEncryptedSearchError("MATRIX_SEARCH_INDEX_INVALID")
        if (
            state.get("index_ref") != index_ref
            or state.get("account_ref") != account_ref
        ):
            raise MatrixEncryptedSearchError("MATRIX_SEARCH_INDEX_SCOPE_MISMATCH")
        return state


def _valid_state(value: object) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "schema_ref",
        "index_ref",
        "account_ref",
        "generation_ref",
        "entries",
        "raw_content_included",
    }:
        return False
    entries = value.get("entries")
    if (
        value.get("schema_ref") != "search-index-schema-ref:matrix:encrypted-hmac-v1"
        or value.get("raw_content_included") is not False
        or not isinstance(value.get("index_ref"), str)
        or not isinstance(value.get("account_ref"), str)
        or not isinstance(value.get("generation_ref"), str)
        or not isinstance(entries, list)
        or len(entries) > _MAX_DOCUMENTS
    ):
        return False
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {
            "room_ref",
            "event_ref",
            "tokens",
        }:
            return False
        tokens = entry.get("tokens")
        if (
            not isinstance(entry.get("room_ref"), str)
            or not isinstance(entry.get("event_ref"), str)
            or not isinstance(tokens, list)
            or len(tokens) > _MAX_TOKENS_PER_DOCUMENT
            or any(
                not isinstance(token, str)
                or len(token) != 64
                or any(character not in "0123456789abcdef" for character in token)
                for token in tokens
            )
        ):
            return False
        try:
            validate_execution_ref(entry["room_ref"], "matrix_search_room_ref")
            validate_execution_ref(entry["event_ref"], "matrix_search_event_ref")
        except ValueError:
            return False
    return True


def _write_all(descriptor: int, payload: bytes) -> None:
    offset = 0
    while offset < len(payload):
        written = os.write(descriptor, payload[offset:])
        if written <= 0:
            raise OSError("matrix search write failed")
        offset += written


def _read_bounded(descriptor: int) -> bytes:
    payload = bytearray()
    try:
        while len(payload) <= _MAX_INDEX_BYTES:
            chunk = os.read(
                descriptor,
                min(8192, _MAX_INDEX_BYTES + 1 - len(payload)),
            )
            if not chunk:
                break
            payload.extend(chunk)
    except OSError as exc:
        raise MatrixEncryptedSearchError("MATRIX_SEARCH_INDEX_INVALID") from exc
    if len(payload) > _MAX_INDEX_BYTES:
        raise MatrixEncryptedSearchError("MATRIX_SEARCH_INDEX_INVALID")
    return bytes(payload)


__all__ = [
    "MatrixEncryptedSearchError",
    "MatrixEncryptedSearchIndex",
    "MatrixSearchDocument",
]

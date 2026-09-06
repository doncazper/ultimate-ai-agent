#!/usr/bin/env python3
from __future__ import annotations

# ruff: noqa: E402 - the built-in-only isolation bootstrap must run first

# Exact provenance must start before normal ``site`` startup can execute an
# ambient ``.pth`` file or ``sitecustomize`` module.  An already-started unsafe
# process cannot safely choose the interpreter for a self-reexec, so callers
# must supply isolation at process creation.
import sys as _foundation_bootstrap_sys

_FOUNDATION_BOOTSTRAP_SAFE = bool(
    _foundation_bootstrap_sys.flags.isolated
    and _foundation_bootstrap_sys.flags.no_site
)
if __name__ == "__main__" and not _FOUNDATION_BOOTSTRAP_SAFE:
    raise SystemExit(
        "Foundation Gate entrypoint requires python -I -B -S"
    )

import argparse
import ctypes
import errno
import hashlib
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import sysconfig
import tempfile
import time
import warnings
from ctypes import wintypes
from pathlib import Path

warnings.filterwarnings(
    "ignore",
    message=r"Using `httpx` with `starlette\.testclient` is deprecated.*",
    category=Warning,
)

ROOT = Path(__file__).resolve().parent.parent


_GIT_READ_CONFIG = (
    "-c",
    "core.fsmonitor=false",
    "-c",
    "core.untrackedCache=false",
    "-c",
    "core.trustctime=true",
    "-c",
    "core.checkStat=default",
    "-c",
    "core.ignoreStat=false",
    "-c",
    f"core.hooksPath={os.devnull}",
    "-c",
    f"core.attributesFile={os.devnull}",
)


def _sanitized_git_environment() -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("GIT_")
    }
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return environment


def _require_raw_clean_worktree(
    repository_root: Path,
    *,
    git_command: str,
    git_environment: dict[str, str],
) -> str:
    """Compare raw worktree bytes and modes with HEAD without Git conversions."""

    def run(*arguments: str, input_bytes: bytes | None = None) -> bytes:
        completed = subprocess.run(
            [
                git_command,
                "--no-replace-objects",
                *_GIT_READ_CONFIG,
                "-c",
                f"core.worktree={repository_root.resolve()}",
                f"--work-tree={repository_root.resolve()}",
                *arguments,
            ],
            cwd=repository_root,
            check=True,
            capture_output=True,
            env=git_environment,
            input=input_bytes,
        )
        return completed.stdout

    def records(payload: bytes, *, purpose: str) -> list[bytes]:
        if len(payload) > 16 * 1024 * 1024 or (payload and not payload.endswith(b"\0")):
            raise RuntimeError(f"Foundation Gate {purpose} is invalid")
        values = payload[:-1].split(b"\0") if payload else []
        if len(values) > 20_000 or any(not value for value in values):
            raise RuntimeError(f"Foundation Gate {purpose} is invalid")
        return values

    revision = run("rev-parse", "HEAD").decode("ascii", errors="strict").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise RuntimeError("Foundation Gate repository revision is invalid")
    object_format = (
        run("rev-parse", "--show-object-format")
        .decode("ascii", errors="strict")
        .strip()
    )
    if object_format not in {"sha1", "sha256"}:
        raise RuntimeError("Foundation Gate Git object format is invalid")

    try:
        run("config", "--local", "--get", "extensions.partialClone")
    except subprocess.CalledProcessError as exc:
        if exc.returncode != 1:
            raise RuntimeError("Foundation Gate Git tree census is invalid") from exc
    else:
        raise RuntimeError("Foundation Gate Git tree census is invalid")
    try:
        promisor_configuration = run(
            "config",
            "--local",
            "--type=bool",
            "--get-regexp",
            r"^remote\..*\.promisor$",
        )
    except subprocess.CalledProcessError as exc:
        if exc.returncode != 1:
            raise RuntimeError("Foundation Gate Git tree census is invalid") from exc
    else:
        try:
            promisor_lines = promisor_configuration.decode(
                "utf-8", errors="strict"
            ).splitlines()
            promisor_values = tuple(
                line.rsplit(maxsplit=1)[1] for line in promisor_lines
            )
        except (UnicodeDecodeError, IndexError) as exc:
            raise RuntimeError("Foundation Gate Git tree census is invalid") from exc
        if (
            not promisor_lines
            or len(promisor_configuration) > 64 * 1024
            or len(promisor_lines) > 256
            or any(value not in {"true", "false"} for value in promisor_values)
            or "true" in promisor_values
        ):
            raise RuntimeError("Foundation Gate Git tree census is invalid")

    tree_entries: dict[bytes, tuple[bytes, bytes, int]] = {}
    for record in records(
        run("ls-tree", "-rlz", "--full-tree", revision),
        purpose="Git tree census",
    ):
        try:
            metadata, path = record.split(b"\t", 1)
            mode, object_type, object_id, size_value = metadata.split(b" ", 3)
            size = int(size_value)
        except (TypeError, ValueError) as exc:
            raise RuntimeError("Foundation Gate Git tree census is invalid") from exc
        components = path.split(b"/")
        if (
            object_type != b"blob"
            or mode not in {b"100644", b"100755", b"120000"}
            or not re.fullmatch(rb"[0-9a-f]{40}|[0-9a-f]{64}", object_id)
            or size < 0
            or size > 64 * 1024 * 1024
            or path.startswith(b"/")
            or any(component in {b"", b".", b".."} for component in components)
            or path in tree_entries
        ):
            raise RuntimeError("Foundation Gate Git tree census is invalid")
        if mode == b"120000":
            raise RuntimeError(
                "Foundation Gate exact provenance rejects tracked symlinks"
            )
        tree_entries[path] = (mode, object_id, size)
    if sum(size for _mode, _object_id, size in tree_entries.values()) > 1024**3:
        raise RuntimeError("Foundation Gate Git tree census is invalid")

    index_entries: dict[bytes, tuple[bytes, bytes]] = {}
    for record in records(run("ls-files", "--stage", "-z"), purpose="Git index census"):
        try:
            metadata, path = record.split(b"\t", 1)
            mode, object_id, stage = metadata.split(b" ", 2)
        except ValueError as exc:
            raise RuntimeError("Foundation Gate Git index census is invalid") from exc
        if (
            stage != b"0"
            or not re.fullmatch(rb"[0-9a-f]{40}|[0-9a-f]{64}", object_id)
            or path in index_entries
        ):
            raise RuntimeError("Foundation Gate Git index census is invalid")
        index_entries[path] = (mode, object_id)
    if {
        path: (mode, object_id)
        for path, (mode, object_id, _size) in tree_entries.items()
    } != index_entries:
        raise RuntimeError(
            "Foundation Gate revision provenance requires a clean worktree"
        )

    for path, (mode, object_id, expected_size) in tree_entries.items():
        components = [os.fsdecode(component) for component in path.split(b"/")]
        parent = repository_root
        try:
            for component in components[:-1]:
                parent = parent / component
                if not stat.S_ISDIR(os.lstat(parent).st_mode):
                    raise RuntimeError(
                        "Foundation Gate repository worktree path is invalid"
                    )
            target = parent / components[-1]
            before = os.lstat(target)
            if not stat.S_ISREG(before.st_mode) or before.st_size != expected_size:
                raise RuntimeError(
                    "Foundation Gate revision provenance requires a clean worktree"
                )
            if os.name == "posix" and bool(before.st_mode & stat.S_IXUSR) != (
                mode == b"100755"
            ):
                raise RuntimeError(
                    "Foundation Gate revision provenance requires a clean worktree"
                )
            raw_object_id = (
                run("hash-object", "--no-filters", "--", os.fsdecode(path))
                .decode("ascii", errors="strict")
                .strip()
            )
            after = os.lstat(target)
        except FileNotFoundError as exc:
            raise RuntimeError(
                "Foundation Gate revision provenance requires a clean worktree"
            ) from exc
        except OSError as exc:
            raise RuntimeError(
                "Foundation Gate repository worktree path is invalid"
            ) from exc
        if (
            not os.path.samestat(before, after)
            or before.st_size != after.st_size
            or before.st_mtime_ns != after.st_mtime_ns
            or before.st_ctime_ns != after.st_ctime_ns
            or raw_object_id.encode("ascii") != object_id
        ):
            raise RuntimeError(
                "Foundation Gate revision provenance requires a clean worktree"
            )

    if records(
        run(
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
        ),
        purpose="untracked-path census",
    ):
        raise RuntimeError(
            "Foundation Gate revision provenance requires a clean worktree"
        )
    if run("rev-parse", "HEAD").decode("ascii", errors="strict").strip() != revision:
        raise RuntimeError("Foundation Gate repository revision drift")
    return revision


def _index_has_hidden_worktree_entries(
    repository_root: Path,
    *,
    git_command: str,
    git_environment: dict[str, str],
) -> bool:
    entries = subprocess.run(
        [
            git_command,
            "--no-replace-objects",
            *_GIT_READ_CONFIG,
            "-c",
            f"core.worktree={repository_root.resolve()}",
            f"--work-tree={repository_root.resolve()}",
            "ls-files",
            "-v",
            "-z",
        ],
        cwd=repository_root,
        check=True,
        capture_output=True,
        env=git_environment,
    ).stdout.split(b"\0")
    return any(
        entry
        and (entry[:1] in {b"S", b"s"} or (entry[:1].isalpha() and entry[:1].islower()))
        for entry in entries
    )


class _WindowsAclSizeInformation(ctypes.Structure):
    _fields_ = (
        ("AceCount", wintypes.DWORD),
        ("AclBytesInUse", wintypes.DWORD),
        ("AclBytesFree", wintypes.DWORD),
    )


class _WindowsAceHeader(ctypes.Structure):
    _fields_ = (
        ("AceType", ctypes.c_ubyte),
        ("AceFlags", ctypes.c_ubyte),
        ("AceSize", wintypes.WORD),
    )


class _WindowsSidAndAttributes(ctypes.Structure):
    _fields_ = (("Sid", ctypes.c_void_p), ("Attributes", wintypes.DWORD))


class _WindowsTokenUser(ctypes.Structure):
    _fields_ = (("User", _WindowsSidAndAttributes),)


_WINDOWS_DANGEROUS_DIRECTORY_RIGHTS = (
    0x00000002  # FILE_ADD_FILE
    | 0x00000004  # FILE_ADD_SUBDIRECTORY
    | 0x00000010  # FILE_WRITE_EA
    | 0x00000040  # FILE_DELETE_CHILD
    | 0x00000100  # FILE_WRITE_ATTRIBUTES
    | 0x00010000  # DELETE
    | 0x00040000  # WRITE_DAC
    | 0x00080000  # WRITE_OWNER
    | 0x10000000  # GENERIC_ALL
    | 0x40000000  # GENERIC_WRITE
)
_WINDOWS_ALLOW_ACE_TYPES = frozenset({0, 5, 9, 11})


def _windows_parent_acl_grant_is_unsafe(
    *, ace_type: int, access_mask: int, trustee_is_trusted: bool
) -> bool:
    """Return whether one parent ACE grants dangerous authority to a stranger."""

    return (
        ace_type in _WINDOWS_ALLOW_ACE_TYPES
        and not trustee_is_trusted
        and bool(access_mask & _WINDOWS_DANGEROUS_DIRECTORY_RIGHTS)
    )


def _windows_error(message: str) -> RuntimeError:
    return RuntimeError(f"{message} (winerror={ctypes.get_last_error()})")


def _configure_windows_acl_apis(advapi: object, kernel: object) -> None:
    advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = (  # type: ignore[attr-defined]
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(wintypes.DWORD),
    )
    advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype = wintypes.BOOL  # type: ignore[attr-defined]
    advapi.GetSecurityDescriptorDacl.argtypes = (  # type: ignore[attr-defined]
        ctypes.c_void_p,
        ctypes.POINTER(wintypes.BOOL),
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(wintypes.BOOL),
    )
    advapi.GetSecurityDescriptorDacl.restype = wintypes.BOOL  # type: ignore[attr-defined]
    advapi.SetNamedSecurityInfoW.argtypes = (  # type: ignore[attr-defined]
        wintypes.LPWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
    )
    advapi.SetNamedSecurityInfoW.restype = wintypes.DWORD  # type: ignore[attr-defined]
    advapi.OpenProcessToken.argtypes = (  # type: ignore[attr-defined]
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE),
    )
    advapi.OpenProcessToken.restype = wintypes.BOOL  # type: ignore[attr-defined]
    advapi.GetTokenInformation.argtypes = (  # type: ignore[attr-defined]
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    )
    advapi.GetTokenInformation.restype = wintypes.BOOL  # type: ignore[attr-defined]
    advapi.GetNamedSecurityInfoW.argtypes = (  # type: ignore[attr-defined]
        wintypes.LPWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_void_p),
    )
    advapi.GetNamedSecurityInfoW.restype = wintypes.DWORD  # type: ignore[attr-defined]
    advapi.EqualSid.argtypes = (ctypes.c_void_p, ctypes.c_void_p)  # type: ignore[attr-defined]
    advapi.EqualSid.restype = wintypes.BOOL  # type: ignore[attr-defined]
    advapi.GetSecurityDescriptorControl.argtypes = (  # type: ignore[attr-defined]
        ctypes.c_void_p,
        ctypes.POINTER(wintypes.WORD),
        ctypes.POINTER(wintypes.DWORD),
    )
    advapi.GetSecurityDescriptorControl.restype = wintypes.BOOL  # type: ignore[attr-defined]
    advapi.ConvertStringSidToSidW.argtypes = (  # type: ignore[attr-defined]
        wintypes.LPCWSTR,
        ctypes.POINTER(ctypes.c_void_p),
    )
    advapi.ConvertStringSidToSidW.restype = wintypes.BOOL  # type: ignore[attr-defined]
    advapi.GetAclInformation.argtypes = (  # type: ignore[attr-defined]
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
    )
    advapi.GetAclInformation.restype = wintypes.BOOL  # type: ignore[attr-defined]
    advapi.GetAce.argtypes = (  # type: ignore[attr-defined]
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.c_void_p),
    )
    advapi.GetAce.restype = wintypes.BOOL  # type: ignore[attr-defined]
    kernel.GetCurrentProcess.restype = wintypes.HANDLE  # type: ignore[attr-defined]
    kernel.LocalFree.argtypes = (ctypes.c_void_p,)  # type: ignore[attr-defined]
    kernel.LocalFree.restype = ctypes.c_void_p  # type: ignore[attr-defined]
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)  # type: ignore[attr-defined]
    kernel.CloseHandle.restype = wintypes.BOOL  # type: ignore[attr-defined]


def _apply_windows_private_directory_acl(path: Path) -> None:
    """Replace inherited grants with current-owner/System/admin full control."""

    if os.name != "nt":
        raise RuntimeError("Foundation Gate Windows ACL support is unavailable")
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)  # type: ignore[attr-defined]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
    _configure_windows_acl_apis(advapi, kernel)
    descriptor = ctypes.c_void_p()
    if not advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW(
        "D:P(A;OICI;FA;;;OW)(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)",
        1,
        ctypes.byref(descriptor),
        None,
    ):
        raise _windows_error("Foundation Gate private ACL creation failed")
    try:
        present = wintypes.BOOL()
        defaulted = wintypes.BOOL()
        dacl = ctypes.c_void_p()
        if not advapi.GetSecurityDescriptorDacl(
            descriptor,
            ctypes.byref(present),
            ctypes.byref(dacl),
            ctypes.byref(defaulted),
        ) or not present.value or not dacl.value:
            raise _windows_error("Foundation Gate private ACL creation failed")
        result = advapi.SetNamedSecurityInfoW(
            str(path),
            1,
            0x80000004,
            None,
            None,
            dacl,
            None,
        )
        if result != 0:
            raise RuntimeError(
                f"Foundation Gate private ACL application failed (winerror={result})"
            )
    finally:
        kernel.LocalFree(descriptor)


def _validate_windows_private_directory_acl(path: Path) -> None:
    """Fail closed unless the directory has the exact protected private DACL."""

    if os.name != "nt":
        raise RuntimeError("Foundation Gate Windows ACL support is unavailable")
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)  # type: ignore[attr-defined]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
    _configure_windows_acl_apis(advapi, kernel)
    token = wintypes.HANDLE()
    descriptor = ctypes.c_void_p()
    allowed_sid_handles: list[ctypes.c_void_p] = []
    try:
        if not advapi.OpenProcessToken(
            kernel.GetCurrentProcess(), 0x0008, ctypes.byref(token)
        ):
            raise _windows_error("Foundation Gate private ACL owner lookup failed")
        required = wintypes.DWORD()
        advapi.GetTokenInformation(
            token,
            1,
            None,
            0,
            ctypes.byref(required),
        )
        if not required.value or required.value > 64 * 1024:
            raise _windows_error("Foundation Gate private ACL owner lookup failed")
        token_buffer = ctypes.create_string_buffer(required.value)
        if not advapi.GetTokenInformation(
            token,
            1,
            token_buffer,
            required,
            ctypes.byref(required),
        ):
            raise _windows_error("Foundation Gate private ACL owner lookup failed")
        current_sid = ctypes.cast(
            token_buffer, ctypes.POINTER(_WindowsTokenUser)
        ).contents.User.Sid

        owner = ctypes.c_void_p()
        dacl = ctypes.c_void_p()
        result = advapi.GetNamedSecurityInfoW(
            str(path),
            1,
            0x00000005,
            ctypes.byref(owner),
            None,
            ctypes.byref(dacl),
            None,
            ctypes.byref(descriptor),
        )
        if result != 0 or not owner.value or not dacl.value or not descriptor.value:
            raise RuntimeError(
                f"Foundation Gate private ACL inspection failed (winerror={result})"
            )
        if not advapi.EqualSid(owner, current_sid):
            raise RuntimeError("Foundation Gate private ACL owner is invalid")
        control = wintypes.WORD()
        revision = wintypes.DWORD()
        if not advapi.GetSecurityDescriptorControl(
            descriptor, ctypes.byref(control), ctypes.byref(revision)
        ) or not control.value & 0x1000:
            raise RuntimeError("Foundation Gate private ACL is not protected")

        for sid_text in ("S-1-3-4", "S-1-5-18", "S-1-5-32-544"):
            sid = ctypes.c_void_p()
            if not advapi.ConvertStringSidToSidW(sid_text, ctypes.byref(sid)):
                raise _windows_error("Foundation Gate private ACL SID lookup failed")
            allowed_sid_handles.append(sid)
        information = _WindowsAclSizeInformation()
        if not advapi.GetAclInformation(
            dacl,
            ctypes.byref(information),
            ctypes.sizeof(information),
            2,
        ) or information.AceCount != len(allowed_sid_handles):
            raise RuntimeError("Foundation Gate private ACL grants are invalid")
        observed: set[int] = set()
        for index in range(information.AceCount):
            ace = ctypes.c_void_p()
            if not advapi.GetAce(dacl, index, ctypes.byref(ace)) or not ace.value:
                raise _windows_error("Foundation Gate private ACL grant lookup failed")
            header = ctypes.cast(
                ace, ctypes.POINTER(_WindowsAceHeader)
            ).contents
            mask = ctypes.c_uint32.from_address(ace.value + 4).value
            ace_sid = ctypes.c_void_p(ace.value + 8)
            matches = tuple(
                sid_index
                for sid_index, sid in enumerate(allowed_sid_handles)
                if advapi.EqualSid(ace_sid, sid)
            )
            if (
                header.AceType != 0
                or header.AceFlags != 0x03
                or header.AceSize < 12
                or mask != 0x001F01FF
                or len(matches) != 1
                or matches[0] in observed
            ):
                raise RuntimeError("Foundation Gate private ACL grants are invalid")
            observed.add(matches[0])
        if len(observed) != len(allowed_sid_handles):
            raise RuntimeError("Foundation Gate private ACL grants are invalid")
    finally:
        if descriptor.value:
            kernel.LocalFree(descriptor)
        for sid in allowed_sid_handles:
            kernel.LocalFree(sid)
        if token.value:
            kernel.CloseHandle(token)


def _validate_windows_private_parent_acl(path: Path) -> None:
    """Reject a Windows parent that grants write/delete authority to strangers."""

    if os.name != "nt":
        raise RuntimeError("Foundation Gate Windows ACL support is unavailable")
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)  # type: ignore[attr-defined]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
    _configure_windows_acl_apis(advapi, kernel)
    token = wintypes.HANDLE()
    descriptor = ctypes.c_void_p()
    trusted_sid_handles: list[ctypes.c_void_p] = []
    try:
        if not advapi.OpenProcessToken(
            kernel.GetCurrentProcess(), 0x0008, ctypes.byref(token)
        ):
            raise _windows_error("Foundation Gate parent ACL owner lookup failed")
        required = wintypes.DWORD()
        advapi.GetTokenInformation(token, 1, None, 0, ctypes.byref(required))
        if not required.value or required.value > 64 * 1024:
            raise _windows_error("Foundation Gate parent ACL owner lookup failed")
        token_buffer = ctypes.create_string_buffer(required.value)
        if not advapi.GetTokenInformation(
            token, 1, token_buffer, required, ctypes.byref(required)
        ):
            raise _windows_error("Foundation Gate parent ACL owner lookup failed")
        current_sid = ctypes.cast(
            token_buffer, ctypes.POINTER(_WindowsTokenUser)
        ).contents.User.Sid
        owner = ctypes.c_void_p()
        dacl = ctypes.c_void_p()
        result = advapi.GetNamedSecurityInfoW(
            str(path),
            1,
            0x00000005,
            ctypes.byref(owner),
            None,
            ctypes.byref(dacl),
            None,
            ctypes.byref(descriptor),
        )
        if result != 0 or not owner.value or not dacl.value or not descriptor.value:
            raise RuntimeError(
                f"Foundation Gate parent ACL inspection failed (winerror={result})"
            )
        if not advapi.EqualSid(owner, current_sid):
            raise RuntimeError("Foundation Gate parent ACL owner is invalid")
        for sid_text in (
            "S-1-3-0",  # Creator Owner
            "S-1-3-4",  # Owner Rights
            "S-1-5-18",  # Local System
            "S-1-5-32-544",  # Builtin Administrators
        ):
            sid = ctypes.c_void_p()
            if not advapi.ConvertStringSidToSidW(sid_text, ctypes.byref(sid)):
                raise _windows_error("Foundation Gate parent ACL SID lookup failed")
            trusted_sid_handles.append(sid)
        information = _WindowsAclSizeInformation()
        if (
            not advapi.GetAclInformation(
                dacl,
                ctypes.byref(information),
                ctypes.sizeof(information),
                2,
            )
            or information.AceCount > 1024
        ):
            raise RuntimeError("Foundation Gate parent ACL grants are invalid")
        for index in range(information.AceCount):
            ace = ctypes.c_void_p()
            if not advapi.GetAce(dacl, index, ctypes.byref(ace)) or not ace.value:
                raise _windows_error("Foundation Gate parent ACL grant lookup failed")
            header = ctypes.cast(ace, ctypes.POINTER(_WindowsAceHeader)).contents
            if header.AceSize < 8:
                raise RuntimeError("Foundation Gate parent ACL grants are invalid")
            mask = ctypes.c_uint32.from_address(ace.value + 4).value
            trustee_is_trusted = False
            if header.AceType == 0:
                if header.AceSize < 12:
                    raise RuntimeError("Foundation Gate parent ACL grants are invalid")
                ace_sid = ctypes.c_void_p(ace.value + 8)
                trustee_is_trusted = bool(advapi.EqualSid(ace_sid, current_sid)) or any(
                    advapi.EqualSid(ace_sid, sid) for sid in trusted_sid_handles
                )
            if _windows_parent_acl_grant_is_unsafe(
                ace_type=header.AceType,
                access_mask=mask,
                trustee_is_trusted=trustee_is_trusted,
            ):
                raise RuntimeError("Foundation Gate parent ACL grants are unsafe")
    finally:
        if descriptor.value:
            kernel.LocalFree(descriptor)
        for sid in trusted_sid_handles:
            kernel.LocalFree(sid)
        if token.value:
            kernel.CloseHandle(token)


def _validate_private_directory(path: Path, *, require_empty: bool) -> None:
    metadata = os.lstat(path)
    if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise RuntimeError("Foundation Gate private directory is unsafe")
    if os.name == "posix":
        if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) != 0o700:
            raise RuntimeError("Foundation Gate private directory is unsafe")
    elif os.name == "nt":
        _validate_windows_private_directory_acl(path)
    else:
        raise RuntimeError("Foundation Gate private directory platform is unsupported")
    if require_empty and any(path.iterdir()):
        raise RuntimeError("Foundation Gate private directory is unsafe")


def _harden_private_directory(path: Path, *, require_empty: bool) -> None:
    if os.name == "posix":
        path.chmod(0o700)
    elif os.name == "nt":
        _apply_windows_private_directory_acl(path)
    else:
        raise RuntimeError("Foundation Gate private directory platform is unsupported")
    _validate_private_directory(path, require_empty=require_empty)


def _darwin_extended_acl_tags(descriptor: int) -> tuple[int, ...]:
    if sys.platform != "darwin":
        return ()
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        acl_get_fd_np = libc.acl_get_fd_np
        acl_get_fd_np.argtypes = (ctypes.c_int, ctypes.c_int)
        acl_get_fd_np.restype = ctypes.c_void_p
        acl_get_entry = libc.acl_get_entry
        acl_get_entry.argtypes = (
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_void_p),
        )
        acl_get_entry.restype = ctypes.c_int
        acl_get_tag_type = libc.acl_get_tag_type
        acl_get_tag_type.argtypes = (
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_int),
        )
        acl_get_tag_type.restype = ctypes.c_int
        acl_free = libc.acl_free
        acl_free.argtypes = (ctypes.c_void_p,)
        acl_free.restype = ctypes.c_int
    except (AttributeError, OSError) as exc:
        raise RuntimeError("Foundation Gate import cache ACL cannot be verified") from exc
    ctypes.set_errno(0)
    acl = acl_get_fd_np(descriptor, 0x100)
    if not acl:
        if ctypes.get_errno() == errno.ENOENT:
            return ()
        raise RuntimeError("Foundation Gate import cache ACL cannot be verified")
    try:
        tags: list[int] = []
        for index in range(170):
            ctypes.set_errno(0)
            entry = ctypes.c_void_p()
            entry_selector = 0 if index == 0 else -1
            entry_result = acl_get_entry(acl, entry_selector, ctypes.byref(entry))
            if entry_result == -1 and ctypes.get_errno() == errno.EINVAL and index:
                break
            if entry_result != 0 or entry.value is None:
                raise RuntimeError(
                    "Foundation Gate import cache ACL cannot be verified"
                )
            tag = ctypes.c_int()
            if acl_get_tag_type(entry, ctypes.byref(tag)) != 0:
                raise RuntimeError(
                    "Foundation Gate import cache ACL cannot be verified"
                )
            tags.append(tag.value)
        else:
            raise RuntimeError("Foundation Gate import cache ACL cannot be verified")
    finally:
        free_result = acl_free(acl)
    if free_result != 0:
        raise RuntimeError("Foundation Gate import cache ACL cannot be verified")
    return tuple(tags)


def _require_no_extended_acl_grants_fd(descriptor: int) -> None:
    if any(tag != 2 for tag in _darwin_extended_acl_tags(descriptor)):
        raise RuntimeError("Foundation Gate import cache root is unsafe")


def _validate_posix_temporary_ancestor_chain(path: Path) -> None:
    if not path.is_absolute():
        raise RuntimeError("Foundation Gate import cache root is unsafe")
    nofollow_flag = getattr(os, "O_NOFOLLOW", 0)
    if not nofollow_flag:
        raise RuntimeError("Foundation Gate import cache root is unsafe")
    lexical_components: list[Path] = []
    lexical = Path(path.anchor)
    for part in path.parts[1:]:
        lexical /= part
        lexical_components.append(lexical)
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise RuntimeError("Foundation Gate import cache root is unsafe") from exc
    components = [
        *((component, True) for component in lexical_components),
        *((component, False) for component in (resolved, *resolved.parents)),
    ]
    for component, allow_root_symlink in components:
        descriptor = -1
        try:
            initial = os.lstat(component)
            if stat.S_ISLNK(initial.st_mode):
                if not allow_root_symlink or initial.st_uid != 0:
                    raise RuntimeError("Foundation Gate import cache root is unsafe")
                final = os.lstat(component)
                if not os.path.samestat(initial, final):
                    raise RuntimeError("Foundation Gate import cache root changed")
                continue
            mode = stat.S_IMODE(initial.st_mode)
            if (
                not stat.S_ISDIR(initial.st_mode)
                or initial.st_uid not in {0, os.getuid()}
                or (mode & 0o022 and not mode & stat.S_ISVTX)
            ):
                raise RuntimeError("Foundation Gate import cache root is unsafe")
            descriptor = os.open(
                component,
                os.O_RDONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_DIRECTORY", 0)
                | nofollow_flag,
            )
            opened = os.fstat(descriptor)
            _require_no_extended_acl_grants_fd(descriptor)
            final = os.lstat(component)
            if (
                not os.path.samestat(initial, opened)
                or not os.path.samestat(opened, final)
                or any(
                    getattr(opened, field) != getattr(final, field)
                    for field in ("st_dev", "st_ino", "st_mode", "st_uid")
                )
            ):
                raise RuntimeError("Foundation Gate import cache root changed")
        except OSError as exc:
            raise RuntimeError("Foundation Gate import cache root is unsafe") from exc
        finally:
            if descriptor >= 0:
                os.close(descriptor)


def _prepare_external_import_cache(
    repository_root: Path,
) -> tuple[tempfile.TemporaryDirectory, Path]:
    """Divert Python cache reads before repository modules become importable."""

    unresolved_temporary_root = Path(tempfile.gettempdir())
    if os.name == "posix":
        _validate_posix_temporary_ancestor_chain(unresolved_temporary_root)
    temporary_root = unresolved_temporary_root.resolve()
    try:
        root_metadata = temporary_root.lstat()
    except OSError as exc:
        raise RuntimeError("Foundation Gate import cache root is unavailable") from exc
    if (
        stat.S_ISLNK(root_metadata.st_mode)
        or not stat.S_ISDIR(root_metadata.st_mode)
        or temporary_root.is_relative_to(repository_root.resolve())
    ):
        raise RuntimeError("Foundation Gate import cache root is unsafe")
    if os.name == "posix":
        root_mode = stat.S_IMODE(root_metadata.st_mode)
        if root_metadata.st_uid not in {0, os.getuid()} or (
            root_mode & 0o022 and not root_mode & stat.S_ISVTX
        ):
            raise RuntimeError("Foundation Gate import cache root is unsafe")
    elif os.name == "nt":
        _validate_windows_private_parent_acl(temporary_root)
    else:
        raise RuntimeError("Foundation Gate import cache root is unsafe")
    cache_handle = tempfile.TemporaryDirectory(
        prefix="uaa-foundation-import-cache-",
        dir=temporary_root,
    )
    cache_root = Path(cache_handle.name)
    try:
        _harden_private_directory(cache_root, require_empty=True)
        final_root_metadata = os.lstat(temporary_root)
        if not os.path.samestat(root_metadata, final_root_metadata):
            raise RuntimeError("Foundation Gate import cache root changed")
    except BaseException:
        cache_handle.cleanup()
        raise
    sys.pycache_prefix = str(cache_root)
    sys.dont_write_bytecode = True
    return cache_handle, cache_root


def _require_no_ignored_repository_import_sources(
    repository_root: Path,
    *,
    git_command: str,
    git_environment: dict[str, str],
) -> None:
    """Reject ignored sources reachable from the repository import roots."""

    completed = subprocess.run(
        [
            git_command,
            "--no-replace-objects",
            *_GIT_READ_CONFIG,
            "-c",
            f"core.worktree={repository_root.resolve()}",
            f"--work-tree={repository_root.resolve()}",
            "ls-files",
            "--others",
            "--ignored",
            "--exclude-standard",
            "-z",
            "--",
            ".",
            # A repository-local virtual environment is already active before
            # this module starts and its dot-prefixed name is not importable
            # from ROOT.  Every other ignored repository path is censused.
            ":(top,exclude,glob).venv/**",
            # The pinned uv bootstrap is never appended to sys.path.  It may
            # exist in canonical CI before the Foundation lane starts.
            ":(top,exclude,glob).ci-bootstrap/**",
        ],
        cwd=repository_root,
        check=True,
        capture_output=True,
        env=git_environment,
    )
    payload = completed.stdout
    if len(payload) > 64 * 1024 * 1024 or (payload and not payload.endswith(b"\0")):
        raise RuntimeError("Foundation Gate ignored import census is invalid")
    paths = payload[:-1].split(b"\0") if payload else []
    if len(paths) > 200_000 or any(not path for path in paths):
        raise RuntimeError("Foundation Gate ignored import census is invalid")
    legacy_or_source_suffixes = (
        b".py",
        b".pyc",
        b".pyo",
        b".so",
        b".pyd",
        b".dll",
        b".dylib",
    )
    for path in paths:
        lowered = path.lower()
        components = lowered.split(b"/")
        try:
            metadata = os.lstat(repository_root / os.fsdecode(path))
        except OSError as exc:
            raise RuntimeError(
                "Foundation Gate ignored import census changed"
            ) from exc
        decoded_components = tuple(os.fsdecode(item) for item in path.split(b"/"))
        import_candidates = (decoded_components,)
        if decoded_components[:1] == ("src",):
            import_candidates += (decoded_components[1:],)
        if stat.S_ISLNK(metadata.st_mode) and any(
            candidate
            and all(component.isidentifier() for component in candidate)
            for candidate in import_candidates
        ):
            raise RuntimeError(
                "Foundation Gate repository has ignored symlink import sources"
            )
        if b"__pycache__" in components and lowered.endswith((b".pyc", b".pyo")):
            # The fresh external sys.pycache_prefix makes repository-local
            # cache directories unreachable to every subsequent import.
            continue
        if lowered.endswith(legacy_or_source_suffixes):
            raise RuntimeError(
                "Foundation Gate repository has ignored executable import sources"
            )


def _validate_posix_admin_path(path: Path) -> None:
    for component in (path, *path.parents):
        try:
            metadata = component.stat()
        except OSError as exc:
            raise RuntimeError(
                "Foundation Gate trusted Git lacks OS provenance"
            ) from exc
        if metadata.st_uid != 0 or metadata.st_mode & 0o022:
            raise RuntimeError("Foundation Gate trusted Git lacks OS provenance")


def _validated_windows_system_root() -> Path:
    if os.name != "nt":
        raise RuntimeError("Foundation Gate Windows system root is unavailable")
    value = os.environ.get("SystemRoot")
    if not value or len(value) > 260 or "\x00" in value:
        raise RuntimeError("Foundation Gate Windows system root is unavailable")
    try:
        buffer = ctypes.create_unicode_buffer(32_768)
        length = ctypes.windll.kernel32.GetWindowsDirectoryW(  # type: ignore[attr-defined]
            buffer,
            len(buffer),
        )
        configured = Path(value).resolve(strict=True)
        authoritative = Path(buffer.value).resolve(strict=True)
    except (AttributeError, OSError) as exc:
        raise RuntimeError("Foundation Gate Windows system root is unavailable") from exc
    if length <= 0 or length >= len(buffer) or configured != authoritative:
        raise RuntimeError("Foundation Gate Windows system root is unavailable")
    return authoritative


_WINDOWS_GIT_TRUST_SCRIPT = (
    "$ErrorActionPreference='Stop';"
    "$p=(Get-Item -LiteralPath $args[0] -Force).FullName;"
    "$roots=@("
    "[Environment]::GetFolderPath([Environment+SpecialFolder]::ProgramFiles),"
    "[Environment]::GetFolderPath([Environment+SpecialFolder]::ProgramFilesX86)"
    ")|Where-Object{$_};"
    "$root=$roots|Where-Object{"
    "$prefix=$_.TrimEnd([IO.Path]::DirectorySeparatorChar)+"
    "[IO.Path]::DirectorySeparatorChar;"
    "$p.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)"
    "}|Select-Object -First 1;"
    "if(-not $root){exit 11};"
    "$trusted=@('S-1-5-18','S-1-5-32-544',"
    "'S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464');"
    "$writeMask=([int64][Security.AccessControl.FileSystemRights]::Write -bor "
    "[int64][Security.AccessControl.FileSystemRights]::Delete -bor "
    "[int64][Security.AccessControl.FileSystemRights]::ChangePermissions -bor "
    "[int64][Security.AccessControl.FileSystemRights]::TakeOwnership -bor "
    "[int64][Security.AccessControl.FileSystemRights]::DeleteSubdirectoriesAndFiles);"
    "$q=Get-Item -LiteralPath $p -Force;"
    "while($true){"
    "$acl=Get-Acl -LiteralPath $q.FullName;"
    "$owner=$acl.GetOwner([Security.Principal.SecurityIdentifier]).Value;"
    "if($trusted -notcontains $owner){exit 12};"
    "$rules=$acl.GetAccessRules($true,$true,"
    "[Security.Principal.SecurityIdentifier]);"
    "foreach($ace in $rules){"
    "$applies=($ace.PropagationFlags -band "
    "[Security.AccessControl.PropagationFlags]::InheritOnly) -eq 0;"
    "$writes=([int64]$ace.FileSystemRights -band $writeMask) -ne 0;"
    "if($applies -and $writes -and "
    "$ace.AccessControlType -eq [Security.AccessControl.AccessControlType]::Allow "
    "-and $trusted -notcontains $ace.IdentityReference.Value){exit 13}"
    "};"
    "if([string]::Equals($q.FullName,$root,"
    "[StringComparison]::OrdinalIgnoreCase)){break};"
    "$q=$q.Parent;if($null -eq $q){exit 14}"
    "};"
    "$s=Get-AuthenticodeSignature -LiteralPath $p;"
    "if($s.Status.ToString() -ne 'Valid' -or $null -eq $s.SignerCertificate){"
    "exit 15};"
    "$chain=New-Object Security.Cryptography.X509Certificates.X509Chain;"
    "$chain.ChainPolicy.RevocationMode="
    "[Security.Cryptography.X509Certificates.X509RevocationMode]::NoCheck;"
    "$chain.ChainPolicy.VerificationFlags="
    "[Security.Cryptography.X509Certificates.X509VerificationFlags]::NoFlag;"
    "if(-not $chain.Build($s.SignerCertificate) -or "
    "$chain.ChainElements.Count -lt 1){exit 16};"
    "$signer=$s.SignerCertificate.Thumbprint.ToUpperInvariant();"
    "$anchor=$chain.ChainElements[$chain.ChainElements.Count-1].Certificate."
    "Thumbprint.ToUpperInvariant();"
    "$machineRoots=@(Get-ChildItem -Path Cert:\\LocalMachine\\Root|"
    "ForEach-Object{$_.Thumbprint.ToUpperInvariant()});"
    "if($machineRoots -notcontains $anchor){exit 17};"
    "Write-Output ($signer+' '+$anchor)"
)


def _validated_windows_git_provenance(
    executable: Path,
    powershell: Path,
) -> tuple[str, str]:
    signature = subprocess.run(
        (
            str(powershell),
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            _WINDOWS_GIT_TRUST_SCRIPT,
            str(executable),
        ),
        check=False,
        capture_output=True,
        timeout=30,
    )
    try:
        output = signature.stdout.decode("ascii", errors="strict").strip().split()
    except UnicodeDecodeError as exc:
        raise RuntimeError("Foundation Gate trusted Git lacks OS provenance") from exc
    if (
        signature.returncode != 0
        or len(output) != 2
        or any(re.fullmatch(r"[0-9A-F]{40,64}", value) is None for value in output)
    ):
        raise RuntimeError("Foundation Gate trusted Git lacks OS provenance")
    return output[0].lower(), output[1].lower()


def _trusted_preimport_git() -> str:
    system = platform.system().strip().lower()
    executable_value = (
        "/usr/bin/git"
        if os.name == "posix" and system == "darwin"
        else shutil.which("git")
    )
    if not executable_value:
        raise RuntimeError("Foundation Gate trusted Git is unavailable")
    try:
        executable = Path(executable_value).resolve(strict=True)
        metadata = executable.stat()
    except OSError as exc:
        raise RuntimeError("Foundation Gate trusted Git is unavailable") from exc
    if not stat.S_ISREG(metadata.st_mode) or not os.access(executable, os.X_OK):
        raise RuntimeError("Foundation Gate trusted Git is unsafe")
    if os.name == "posix":
        _validate_posix_admin_path(executable)
        if system == "darwin":
            if executable != Path("/usr/bin/git"):
                raise RuntimeError("Foundation Gate trusted Git lacks OS provenance")
            signature = subprocess.run(
                (
                    "/usr/bin/codesign",
                    "--verify",
                    "--strict",
                    "-R=anchor apple",
                    str(executable),
                ),
                check=False,
                capture_output=True,
                timeout=30,
            )
            if signature.returncode != 0:
                raise RuntimeError("Foundation Gate trusted Git lacks OS provenance")
    elif os.name == "nt":
        system_root = _validated_windows_system_root()
        powershell = (
            system_root / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
        )
        _validated_windows_git_provenance(executable, powershell)
    else:
        raise RuntimeError("Foundation Gate trusted Git platform is unsupported")
    return str(executable)


def _preloaded_repository_module_paths(repository_root: Path) -> tuple[str, ...]:
    """Record repository code that executed before the provenance seal."""

    resolved_root = repository_root.resolve()
    this_module = Path(__file__).resolve()
    observed: set[str] = set()
    for module in tuple(sys.modules.values()):
        module_file = getattr(module, "__file__", None)
        if not isinstance(module_file, str):
            continue
        try:
            path = Path(module_file).resolve()
        except OSError:
            continue
        if path == this_module or not path.is_relative_to(resolved_root):
            continue
        observed.add(path.relative_to(resolved_root).as_posix())
    return tuple(sorted(observed))


def _runtime_dependency_path() -> Path:
    """Locate site-packages without executing any environment ``.pth`` files."""

    executable = Path(sys.executable)
    environment_root = executable.parent.parent
    if (environment_root / "pyvenv.cfg").is_file():
        if os.name == "nt":
            candidate = environment_root / "Lib" / "site-packages"
        else:
            candidate = (
                environment_root
                / "lib"
                / f"python{sys.version_info.major}.{sys.version_info.minor}"
                / "site-packages"
            )
    else:
        candidate = Path(sysconfig.get_path("purelib"))
    try:
        metadata = candidate.lstat()
    except OSError as exc:
        raise RuntimeError(
            "Foundation Gate runtime dependency path is unavailable"
        ) from exc
    if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise RuntimeError("Foundation Gate runtime dependency path is unsafe")
    return candidate


def _authenticated_locked_dependency_path(
    repository_root: Path,
    *,
    revision: str | None,
    git_command: str,
    git_environment: dict[str, str],
) -> Path | None:
    """Authenticate imported dependencies from exact lock-bound wheel bytes."""

    evidence = {
        "complete": os.environ.get("UAA_TAW08_PREFLIGHT_COMPLETE"),
        "digest": os.environ.get("UAA_TAW08_PREFLIGHT_DIGEST"),
        "environment": os.environ.get("UAA_TAW08_ENVIRONMENT_ROOT"),
        "wheelhouse": os.environ.get("UAA_TAW08_LOCKED_WHEELHOUSE"),
        "revision": os.environ.get("UAA_TAW08_LOCKED_CHILD_REVISION"),
    }
    if all(value is None for value in evidence.values()):
        return None
    if revision is None or any(value is None for value in evidence.values()):
        raise RuntimeError("Foundation Gate locked dependency preflight is invalid")
    if evidence["complete"] != "1" or evidence["revision"] != revision:
        raise RuntimeError("Foundation Gate locked dependency preflight is invalid")
    preflight_ref = "scripts/verify_taw08_environment_preflight.py"
    completed = subprocess.run(
        [
            git_command,
            "--no-replace-objects",
            *_GIT_READ_CONFIG,
            "-c",
            f"core.worktree={repository_root.resolve()}",
            f"--work-tree={repository_root.resolve()}",
            "show",
            f"{revision}:{preflight_ref}",
        ],
        cwd=repository_root,
        check=True,
        capture_output=True,
        env=git_environment,
    )
    source = completed.stdout
    expected_digest = "sha256:" + hashlib.sha256(source).hexdigest()
    preflight_path = repository_root / preflight_ref
    raw_preflight_object_id = subprocess.run(
        [
            git_command,
            "--no-replace-objects",
            *_GIT_READ_CONFIG,
            "-c",
            f"core.worktree={repository_root.resolve()}",
            f"--work-tree={repository_root.resolve()}",
            "hash-object",
            "--no-filters",
            "--",
            preflight_ref,
        ],
        cwd=repository_root,
        check=True,
        capture_output=True,
        env=git_environment,
    ).stdout.strip()
    committed_preflight_object_id = subprocess.run(
        [
            git_command,
            "--no-replace-objects",
            *_GIT_READ_CONFIG,
            "-c",
            f"core.worktree={repository_root.resolve()}",
            f"--work-tree={repository_root.resolve()}",
            "rev-parse",
            f"{revision}:{preflight_ref}",
        ],
        cwd=repository_root,
        check=True,
        capture_output=True,
        env=git_environment,
    ).stdout.strip()
    if (
        evidence["digest"] != expected_digest
        or not source
        or len(source) > 1024 * 1024
        or raw_preflight_object_id != committed_preflight_object_id
    ):
        raise RuntimeError("Foundation Gate locked dependency preflight is invalid")
    namespace: dict[str, object] = {
        "__builtins__": __builtins__,
        "__file__": str(preflight_path),
        "__name__": "_uaa_foundation_locked_dependency_preflight",
        "__package__": None,
    }
    try:
        exec(compile(source, str(preflight_path), "exec"), namespace)
        verify_environment = namespace["verify_environment"]
        if not callable(verify_environment):
            raise TypeError("preflight verifier is not callable")
        dependency_path = verify_environment(  # type: ignore[operator]
            repository_root / "scripts" / "run_foundation_gate.py"
        )
    except (KeyError, OSError, TypeError, ValueError) as exc:
        raise RuntimeError(
            "Foundation Gate locked dependency preflight failed"
        ) from exc
    if not isinstance(dependency_path, Path):
        raise RuntimeError("Foundation Gate locked dependency preflight failed")
    return dependency_path.resolve()


def _establish_preimport_repository_posture(
    repository_root: Path,
) -> tuple[str | None, str]:
    """Prove or explicitly withhold clean provenance before repo imports."""

    git_command = _trusted_preimport_git()
    git_environment = _sanitized_git_environment()
    _require_no_ignored_repository_import_sources(
        repository_root,
        git_command=git_command,
        git_environment=git_environment,
    )
    try:
        revision = _require_raw_clean_worktree(
            repository_root,
            git_command=git_command,
            git_environment=git_environment,
        )
    except RuntimeError as exc:
        if str(exc) == (
            "Foundation Gate revision provenance requires a clean worktree"
        ):
            return None, git_command
        raise
    if _index_has_hidden_worktree_entries(
        repository_root,
        git_command=git_command,
        git_environment=git_environment,
    ):
        return None, git_command
    return revision, git_command


_PREIMPORT_REPOSITORY_MODULE_PATHS = _preloaded_repository_module_paths(ROOT)
_FOUNDATION_IMPORT_CACHE_HANDLE: tempfile.TemporaryDirectory | None = None
_FOUNDATION_IMPORT_CACHE: Path | None = None
if _FOUNDATION_BOOTSTRAP_SAFE:
    _FOUNDATION_IMPORT_CACHE_HANDLE, _FOUNDATION_IMPORT_CACHE = (
        _prepare_external_import_cache(ROOT)
    )
# Strict pre-import repository attestation belongs to the executable Gate path.
# Importers use this module's pure helpers and must not execute repository readers
# merely by importing them (which also keeps test-corpus identities bindable).
if __name__ == "__main__":
    _PREIMPORT_CLEAN_REVISION, _PREIMPORT_TRUSTED_GIT_COMMAND = (
        _establish_preimport_repository_posture(ROOT)
    )
else:
    _PREIMPORT_CLEAN_REVISION = None
    _PREIMPORT_TRUSTED_GIT_COMMAND = None


def _require_preimport_trusted_git_command() -> str:
    if _PREIMPORT_TRUSTED_GIT_COMMAND is None:
        raise RuntimeError("Foundation Gate trusted Git is unavailable")
    return _PREIMPORT_TRUSTED_GIT_COMMAND

# The locked TAW wrapper needs only the commit identity to create its detached,
# independently checked candidate.  This narrow bootstrap exits before any
# repository environment dependency is imported and never issues a Gate report.
if __name__ == "__main__" and sys.argv[1:] == ["--preimport-revision-probe"]:
    if (
        not _FOUNDATION_BOOTSTRAP_SAFE
        or _PREIMPORT_REPOSITORY_MODULE_PATHS
        or _PREIMPORT_CLEAN_REVISION is None
    ):
        raise SystemExit("Foundation Gate preimport revision probe failed")
    print(f"git-sha:{_PREIMPORT_CLEAN_REVISION}")
    raise SystemExit(0)

_FOUNDATION_DEPENDENCY_PATH = _runtime_dependency_path()
_FOUNDATION_AUTHENTICATED_DEPENDENCY_PATH = (
    _authenticated_locked_dependency_path(
        ROOT,
        revision=_PREIMPORT_CLEAN_REVISION,
        git_command=_require_preimport_trusted_git_command(),
        git_environment=_sanitized_git_environment(),
    )
    if __name__ == "__main__"
    else None
)
if (
    _FOUNDATION_AUTHENTICATED_DEPENDENCY_PATH is not None
    and _FOUNDATION_AUTHENTICATED_DEPENDENCY_PATH != _FOUNDATION_DEPENDENCY_PATH.resolve()
):
    raise RuntimeError("Foundation Gate runtime dependency path is unauthenticated")
if str(_FOUNDATION_DEPENDENCY_PATH) not in sys.path:
    sys.path.append(str(_FOUNDATION_DEPENDENCY_PATH))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.gate import (  # noqa: E402
    FoundationGateCommandReceipt,
    FoundationGateEvaluator,
    FoundationGateLatencySummary,
    FoundationGateReport,
    FoundationGateReleaseLaneSummary,
    FoundationGateStatus,
)
from ultimate_ai_agent.core.gate.reports import (  # noqa: E402
    foundation_gate_evaluation_provenance_digest,
)
from scripts.verification.verification_github_prerequisites import (  # noqa: E402
    FoundationPrerequisiteManifest,
    load_foundation_prerequisite_manifest,
)


def exact_repository_revision(
    repository_root: Path,
    *,
    git_executable: str | Path = "git",
) -> str:
    git_command = str(git_executable)
    git_environment = _sanitized_git_environment()
    repository_probe = subprocess.run(
        [
            git_command,
            "--no-replace-objects",
            *_GIT_READ_CONFIG,
            "-c",
            f"core.worktree={repository_root.resolve()}",
            f"--work-tree={repository_root.resolve()}",
            "rev-parse",
            "--show-toplevel",
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
        env=git_environment,
    )
    if repository_probe.returncode != 0:
        raise RuntimeError(
            "Foundation Gate exact revision provenance requires the repository root"
        )
    resolved_root = Path(repository_probe.stdout.strip()).resolve()
    if resolved_root != repository_root.resolve():
        raise RuntimeError(
            "Foundation Gate exact revision provenance requires the repository root"
        )
    revision = _require_raw_clean_worktree(
        resolved_root,
        git_command=git_command,
        git_environment=git_environment,
    )
    if resolved_root == ROOT.resolve():
        if not _FOUNDATION_BOOTSTRAP_SAFE:
            raise RuntimeError(
                "Foundation Gate exact provenance requires an isolated no-site process"
            )
        if _PREIMPORT_REPOSITORY_MODULE_PATHS:
            raise RuntimeError(
                "Foundation Gate exact provenance requires a fresh process"
            )
        if _FOUNDATION_AUTHENTICATED_DEPENDENCY_PATH is None:
            raise RuntimeError(
                "Foundation Gate exact provenance requires locked dependencies"
            )
        if _PREIMPORT_CLEAN_REVISION is None:
            raise RuntimeError(
                "Foundation Gate revision provenance requires a clean worktree"
            )
        if revision != _PREIMPORT_CLEAN_REVISION:
            raise RuntimeError("Foundation Gate repository revision drift")
    if _index_has_hidden_worktree_entries(
        resolved_root,
        git_command=git_command,
        git_environment=git_environment,
    ):
        raise RuntimeError(
            "Foundation Gate revision provenance rejects hidden index entries"
        )
    revision_after = subprocess.run(
        [
            git_command,
            "--no-replace-objects",
            *_GIT_READ_CONFIG,
            "-c",
            f"core.worktree={resolved_root}",
            f"--work-tree={resolved_root}",
            "rev-parse",
            "HEAD",
        ],
        cwd=resolved_root,
        check=True,
        capture_output=True,
        text=True,
        env=git_environment,
    ).stdout.strip()
    if revision_after != revision:
        raise RuntimeError("Foundation Gate repository revision drift")
    return f"git-sha:{revision}"


def evaluate_foundation_gate_at_exact_repository_revision(
    repository_root: Path,
    *,
    git_executable: str | Path = "git",
    evaluation_elapsed_ms: list[float] | None = None,
) -> tuple[str, FoundationGateReport]:
    """Run the canonical evaluator and inseparably bind its clean revision."""

    evaluated_revision_ref = exact_repository_revision(
        repository_root,
        git_executable=git_executable,
    )
    evaluator = FoundationGateEvaluator(repository_root)
    warmup_report = evaluator.evaluate()
    evaluation_started = time.perf_counter()
    report = evaluator.evaluate()
    measured_evaluation_ms = round(
        (time.perf_counter() - evaluation_started) * 1000,
        2,
    )
    if (
        str(warmup_report.overall_status) != str(report.overall_status)
        or len(warmup_report.results) != len(report.results)
    ):
        raise RuntimeError("Foundation Gate warmup result drift")
    if (
        exact_repository_revision(
            repository_root,
            git_executable=git_executable,
        )
        != evaluated_revision_ref
    ):
        raise RuntimeError("Foundation Gate revision changed during evaluation")
    bound = report.model_copy(update={"evaluated_revision_ref": evaluated_revision_ref})
    bound = bound.model_copy(
        update={
            "evaluation_provenance_digest_ref": (
                foundation_gate_evaluation_provenance_digest(bound)
            )
        }
    )
    if evaluation_elapsed_ms is not None:
        evaluation_elapsed_ms.append(measured_evaluation_ms)
    return evaluated_revision_ref, bound


def evaluate_foundation_gate_for_repository_state(
    repository_root: Path,
    *,
    require_clean_revision: bool,
    git_executable: str | Path = "git",
    evaluation_elapsed_ms: list[float] | None = None,
) -> tuple[str | None, FoundationGateReport]:
    """Preserve dirty-tree development checks without issuing provenance."""

    try:
        if evaluation_elapsed_ms is None:
            return evaluate_foundation_gate_at_exact_repository_revision(
                repository_root,
                git_executable=git_executable,
            )
        return evaluate_foundation_gate_at_exact_repository_revision(
            repository_root,
            git_executable=git_executable,
            evaluation_elapsed_ms=evaluation_elapsed_ms,
        )
    except RuntimeError as exc:
        if require_clean_revision or str(exc) not in {
            "Foundation Gate revision provenance requires a clean worktree",
            "Foundation Gate exact provenance requires locked dependencies",
        }:
            raise
    evaluation_started = time.perf_counter()
    report = FoundationGateEvaluator(repository_root).evaluate()
    if evaluation_elapsed_ms is not None:
        evaluation_elapsed_ms.append(
            round((time.perf_counter() - evaluation_started) * 1000, 2)
        )
    return None, report


GATE_TESTS = [
    "tests/test_foundation_gate_criteria.py",
    "tests/test_foundation_gate_report.py",
    "tests/test_shadow_replay_m5.py",
    "tests/test_contract_compatibility.py",
    "tests/test_foundation_gate_blocked_modules.py",
    "tests/test_foundation_gate_secret_hygiene.py",
    "tests/test_foundation_gate_receipts.py",
    "tests/test_foundation_gate_rollback.py",
    "tests/test_foundation_gate_truth_evidence.py",
    "tests/test_foundation_gate_api_routes.py",
    "tests/test_model_profiles.py",
    "tests/test_model_routing_policy.py",
    "tests/test_model_router_decisions.py",
    "tests/test_model_router_privacy.py",
    "tests/test_model_router_context_budget.py",
    "tests/test_model_router_no_execution.py",
    "tests/test_cost_budgets.py",
    "tests/test_cost_governor.py",
    "tests/test_resource_governor.py",
    "tests/test_m7_api_routes.py",
    "tests/test_m7_gate_integration.py",
    "tests/test_api_manifest.py",
    "tests/test_openapi_contract.py",
    "tests/test_agents_md_guidance.py",
    "tests/test_m75_gate_integration.py",
    "tests/test_model_runtime_manifests.py",
    "tests/test_model_runtime_requests.py",
    "tests/test_model_runtime_simulator.py",
    "tests/test_model_runtime_no_real_calls.py",
    "tests/test_model_runtime_redaction.py",
    "tests/test_model_runtime_event_metadata.py",
    "tests/test_model_runtime_api_routes.py",
    "tests/test_m8_gate_integration.py",
    "tests/test_approval_requests.py",
    "tests/test_approval_authority.py",
    "tests/test_approval_validation.py",
    "tests/test_approval_expiration.py",
    "tests/test_approval_scope.py",
    "tests/test_approval_receipts.py",
    "tests/test_approval_integration_model_router.py",
    "tests/test_approval_integration_model_runtime.py",
    "tests/test_approval_integration_tool_broker.py",
    "tests/test_approval_integration_kernel.py",
    "tests/test_m85_api_routes.py",
    "tests/test_m85_gate_integration.py",
    "tests/test_local_loopback_endpoint_policy.py",
    "tests/test_local_loopback_transport.py",
    "tests/test_local_loopback_adapter.py",
    "tests/test_local_loopback_approval.py",
    "tests/test_local_loopback_no_remote.py",
    "tests/test_local_loopback_api_routes.py",
    "tests/test_m9_gate_integration.py",
    "tests/test_manual_loopback_smoke_policy.py",
    "tests/test_manual_loopback_smoke_transport.py",
    "tests/test_manual_loopback_smoke_script.py",
    "tests/test_manual_loopback_smoke_api_routes.py",
    "tests/test_m10_gate_integration.py",
    "tests/test_remote_worker_models.py",
    "tests/test_remote_worker_registry.py",
    "tests/test_remote_worker_policy.py",
    "tests/test_remote_worker_transports.py",
    "tests/test_remote_worker_dry_run.py",
    "tests/test_remote_worker_api_routes.py",
    "tests/test_remote_worker_no_network.py",
    "tests/test_remote_worker_gate_integration.py",
]


COMMAND_MODES = {
    "full",
    "legacy-full",
    "targeted-tests",
    "verify-all",
    "report-only",
    "ci-after-verify-all",
    "ci-parallel",
}


def run_command(
    command_ref: str, command_mode: str, args: list[str], safe_summary: str
) -> FoundationGateCommandReceipt:
    print(f"\nRunning: {' '.join(args)}")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    started = time.perf_counter()
    result = subprocess.run(args, cwd=ROOT, env=env, text=True)
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    status = "PASS" if result.returncode == 0 else f"FAIL ({result.returncode})"
    print(f"Command status: {status}")
    return FoundationGateCommandReceipt(
        command_ref=command_ref,
        command_mode=command_mode,
        status="passed" if result.returncode == 0 else "failed",
        satisfied_by="direct",
        safe_summary=safe_summary,
        return_code=result.returncode,
        elapsed_ms=elapsed_ms,
    )


def external_verify_all_receipt(command_mode: str) -> FoundationGateCommandReceipt:
    return FoundationGateCommandReceipt(
        command_ref="command:scripts.verify_all",
        command_mode=command_mode,
        status="satisfied_external",
        satisfied_by="ci-master-verification",
        safe_summary=(
            "Master verification was satisfied by the preceding CI step; "
            "Foundation Gate generated the typed report only."
        ),
    )


def parallel_ci_receipt(
    command_mode: str,
    *,
    prerequisite_path: Path,
    repository_sha: str,
    base_sha: str,
) -> FoundationGateCommandReceipt:
    prerequisite: FoundationPrerequisiteManifest = (
        load_foundation_prerequisite_manifest(
            prerequisite_path,
            ROOT,
            repository_sha,
            base_sha,
        )
    )
    return FoundationGateCommandReceipt(
        command_ref="command:ci.parallel_verification",
        command_mode=command_mode,
        status="satisfied_by_exact_receipts",
        satisfied_by=prerequisite.content_ref,
        safe_summary=(
            "Lint, complete pytest, and static verification were revalidated "
            "from exact-SHA, exact-plan GitHub job receipts; Foundation Gate "
            "generated the typed report without repeating those commands."
        ),
    )


def report_only_receipt(command_mode: str) -> FoundationGateCommandReceipt:
    return FoundationGateCommandReceipt(
        command_ref="command:foundation_gate.typed_report",
        command_mode=command_mode,
        status="report_only",
        satisfied_by="typed-foundation-gate-evaluator",
        safe_summary=(
            "No external verifier commands were run. The typed Foundation Gate "
            "evaluator and latency summary still run local read/probe code; use "
            "--no-write-latest when the latest report files must not be updated."
        ),
    )


def commands_for_mode(command_mode: str) -> list[tuple[str, list[str], str]]:
    if command_mode == "full":
        return [
            (
                "command:scripts.verify_all",
                [sys.executable, "scripts/verify_all.py"],
                "Run the master verifier once; it includes Ruff, pytest, static scans, baseline, skill, and OpenAPI checks.",
            )
        ]
    if command_mode == "legacy-full":
        return [
            (
                "command:foundation_gate.targeted_tests",
                [sys.executable, "-m", "pytest", *GATE_TESTS],
                "Run targeted Foundation Gate tests.",
            ),
            (
                "command:scripts.verify_current_baseline",
                [sys.executable, "scripts/verify_current_baseline.py"],
                "Run current baseline verification.",
            ),
            (
                "command:scripts.verify_skill_package_security_rule",
                [sys.executable, "scripts/verify_skill_package_security_rule.py"],
                "Run skill package security rule verification.",
            ),
            (
                "command:scripts.verify_all",
                [sys.executable, "scripts/verify_all.py"],
                "Run the master verification suite.",
            ),
        ]
    if command_mode == "targeted-tests":
        return [
            (
                "command:foundation_gate.targeted_tests",
                [sys.executable, "-m", "pytest", *GATE_TESTS],
                "Run targeted Foundation Gate tests only.",
            )
        ]
    if command_mode == "verify-all":
        return [
            (
                "command:scripts.verify_all",
                [sys.executable, "scripts/verify_all.py"],
                "Run the master verification suite only.",
            )
        ]
    return []


def build_latency_gate_summary(
    *,
    foundation_gate_report_json: str | None,
    foundation_gate_report_md: str | None,
    write_report: bool = True,
    precomputed_foundation_gate_ms: float | None = None,
    precomputed_foundation_gate_status: str | None = None,
    precomputed_foundation_gate_result_count: int | None = None,
    precomputed_foundation_gate_warmup: int = 0,
) -> FoundationGateLatencySummary:
    from scripts.check_foundation_gate_latency import run_latency_gate_summary

    summary = run_latency_gate_summary(
        foundation_gate_report_json=foundation_gate_report_json,
        foundation_gate_report_md=foundation_gate_report_md,
        write_report=write_report,
        precomputed_foundation_gate_ms=precomputed_foundation_gate_ms,
        precomputed_foundation_gate_status=precomputed_foundation_gate_status,
        precomputed_foundation_gate_result_count=precomputed_foundation_gate_result_count,
        precomputed_foundation_gate_warmup=precomputed_foundation_gate_warmup,
    )
    return FoundationGateLatencySummary.model_validate(summary)


def build_release_lane_summary() -> FoundationGateReleaseLaneSummary:
    from scripts.verify_release_lanes import build_release_lane_manifest

    manifest = build_release_lane_manifest()
    summary = {
        "schema_version": manifest["schema_version"],
        "task_ref": manifest["task_ref"],
        "overall_status": manifest["overall_status"],
        "definition_status": manifest["definition_status"],
        "command_execution_status": manifest["command_execution_status"],
        "lane_count": manifest["lane_count"],
        "lane_ids": [lane["lane_id"] for lane in manifest["lanes"]],
        "status_semantics": manifest["status_semantics"],
        "accepted_failures": manifest["accepted_failures"],
        "validation_failures": manifest["validation_failures"],
        "report_safety": manifest["report_safety"],
        "safe_summary": manifest["safe_summary"],
    }
    return FoundationGateReleaseLaneSummary.model_validate(summary)


def write_markdown_payload(payload: dict, markdown_path: Path) -> None:
    lines = [
        "# Foundation Gate Report",
        "",
        f"- Report: `{payload['report_id']}`",
        f"- Version: `{payload['version']}`",
        f"- Overall status: `{payload['overall_status']}`",
        f"- Summary: {payload['summary']}",
        f"- Next action: {payload['next_recommended_action']}",
        f"- Command mode: `{payload.get('command_mode') or 'none'}`",
        "",
        "## Command Receipts",
        "",
    ]
    if payload.get("command_receipts"):
        for receipt in payload["command_receipts"]:
            lines.append(
                f"- `{receipt['command_ref']}`: `{receipt['status']}` "
                f"via `{receipt['satisfied_by']}` - {receipt['safe_summary']}"
            )
    else:
        lines.append("- No command receipts recorded.")
    latency_gate = payload.get("latency_gate")
    if latency_gate:
        lines.extend(
            [
                "",
                "## Latency Gate",
                "",
                f"- Status: `{latency_gate['status']}`",
                f"- p50/p95 status: `{latency_gate['p50_p95_status']}`",
                f"- Release latency: `{latency_gate['release_latency_status']}`",
                f"- Hot-path profile: `{latency_gate['hot_path_profile_status']}`",
                (
                    "- Foundation Gate latency: "
                    f"best `{latency_gate['foundation_gate_best_ms']}` ms "
                    f"(budget `{latency_gate['foundation_gate_best_budget_ms']}` ms), "
                    f"mean `{latency_gate['foundation_gate_mean_ms']}` ms "
                    f"(budget `{latency_gate['foundation_gate_mean_budget_ms']}` ms)"
                ),
            ]
        )
        if latency_gate.get("foundation_gate_report_json"):
            lines.append(
                f"- Report path: `{latency_gate['foundation_gate_report_json']}`"
            )
        accepted_failures = latency_gate.get("accepted_failures", [])
        lines.append(f"- Accepted failures: `{len(accepted_failures)}`")
        optional_prerequisites = latency_gate.get("optional_prerequisites", [])
        if optional_prerequisites:
            lines.extend(["", "### Optional Prerequisites", ""])
            for result in optional_prerequisites:
                reason_codes = ", ".join(result.get("reason_codes", [])) or "none"
                lines.append(
                    f"- `{result['safe_label']}`: `{result['status']}` ({reason_codes})"
                )
        lines.extend(["", "### Latency Path Results", ""])
        for result in latency_gate.get("path_results", []):
            p95 = result["p95_ms"] if result["p95_ms"] is not None else "not measured"
            p50 = result["p50_ms"] if result["p50_ms"] is not None else "not measured"
            lines.append(
                f"- `{result['safe_label']}`: `{result['status']}` "
                f"p50 `{p50}` ms, p95 `{p95}` ms, budget "
                f"`{result['budget_ms']}` ms, `{result['budget_status']}`"
            )
        if latency_gate.get("failures"):
            lines.extend(["", "### Latency Failures", ""])
            for failure in latency_gate["failures"]:
                lines.append(f"- {failure}")
    release_lanes = payload.get("release_verification_lanes")
    if release_lanes:
        lines.extend(
            [
                "",
                "## Release Verification Lanes",
                "",
                f"- Manifest status: `{release_lanes['overall_status']}`",
                f"- Definition status: `{release_lanes['definition_status']}`",
                f"- Command execution status: `{release_lanes['command_execution_status']}`",
                f"- Lane count: `{release_lanes['lane_count']}`",
                f"- Accepted failures: `{len(release_lanes.get('accepted_failures', []))}`",
                f"- Validation failures: `{len(release_lanes.get('validation_failures', []))}`",
                "- Lanes: "
                + ", ".join(
                    f"`{lane_id}`" for lane_id in release_lanes.get("lane_ids", [])
                ),
            ]
        )
        lines.extend(["", "### Lane Status Semantics", ""])
        for status, meaning in release_lanes.get("status_semantics", {}).items():
            lines.append(f"- `{status}`: {meaning}")
    lines.extend(
        [
            "",
            "## Criteria",
            "",
        ]
    )
    for result in payload["results"]:
        lines.append(
            f"- `{result['criterion_id']}`: `{result['status']}` - {result['safe_message']}"
        )
    write_text_atomic(markdown_path, "\n".join(lines) + "\n")


def write_text_atomic(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def write_json_atomic(path: Path, payload: str) -> None:
    if not payload.strip():
        raise ValueError("Foundation Gate JSON report payload must not be empty.")
    json.loads(payload)
    write_text_atomic(path, payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run M6 Foundation Gate checks.")
    parser.add_argument(
        "--command-mode",
        choices=sorted(COMMAND_MODES),
        default="full",
        help=(
            "Command mode. full runs the master verifier once; legacy-full preserves the old targeted+baseline+skill+verify_all sequence; "
            "report-only skips external verifier commands but still runs local typed evaluator/probe summaries; ci-after-verify-all records an external CI verification receipt; "
            "ci-parallel records verification satisfied by required parallel CI jobs."
        ),
    )
    parser.add_argument(
        "--skip-commands",
        action="store_true",
        help="Legacy alias for --command-mode report-only.",
    )
    parser.add_argument(
        "--no-write-latest",
        action="store_true",
        help="Do not update reports/foundation_gate/latest_* files.",
    )
    parser.add_argument(
        "--output", help="Optional path for an additional JSON report copy."
    )
    parser.add_argument("--ci-prerequisite-manifest")
    parser.add_argument("--ci-prerequisite-sha")
    parser.add_argument("--ci-prerequisite-base-sha")
    parser.add_argument(
        "--require-clean-revision",
        action="store_true",
        help=(
            "Fail unless the report can bind one clean exact Git revision. "
            "TAW-08 receipt issuance always enforces this independently."
        ),
    )
    args = parser.parse_args(argv)

    command_mode = "report-only" if args.skip_commands else args.command_mode
    prerequisite_values = (
        args.ci_prerequisite_manifest,
        args.ci_prerequisite_sha,
        args.ci_prerequisite_base_sha,
    )
    if command_mode == "ci-parallel" and not all(prerequisite_values):
        parser.error(
            "ci-parallel requires an exact prerequisite manifest and repository SHA"
        )
    if command_mode != "ci-parallel" and any(prerequisite_values):
        parser.error("CI prerequisite evidence is limited to ci-parallel mode")
    command_failures = []
    command_receipts: list[FoundationGateCommandReceipt] = []
    if command_mode == "ci-after-verify-all":
        command_receipts.append(external_verify_all_receipt(command_mode))
    elif command_mode == "ci-parallel":
        command_receipts.append(
            parallel_ci_receipt(
                command_mode,
                prerequisite_path=Path(args.ci_prerequisite_manifest),
                repository_sha=args.ci_prerequisite_sha,
                base_sha=args.ci_prerequisite_base_sha,
            )
        )
    elif command_mode == "report-only":
        command_receipts.append(report_only_receipt(command_mode))
    for command_ref, command, safe_summary in commands_for_mode(command_mode):
        receipt = run_command(command_ref, command_mode, command, safe_summary)
        command_receipts.append(receipt)
        if receipt.return_code != 0:
            command_failures.append(command_ref)

    foundation_gate_evaluation_ms: list[float] = []
    _evaluated_revision_ref, report = evaluate_foundation_gate_for_repository_state(
        ROOT,
        require_clean_revision=args.require_clean_revision,
        git_executable=_require_preimport_trusted_git_command(),
        evaluation_elapsed_ms=foundation_gate_evaluation_ms,
    )
    if len(foundation_gate_evaluation_ms) != 1:
        raise RuntimeError("Foundation Gate evaluation latency measurement is invalid")
    foundation_gate_elapsed_ms = foundation_gate_evaluation_ms[0]
    report = report.model_copy(
        update={
            "command_mode": command_mode,
            "command_receipts": command_receipts,
        }
    )
    output_dir = ROOT / "reports" / "foundation_gate"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "latest_foundation_gate_report.json"
    markdown_path = output_dir / "latest_foundation_gate_report.md"
    latency_gate = build_latency_gate_summary(
        foundation_gate_report_json=None
        if args.no_write_latest
        else str(report_path.relative_to(ROOT)),
        foundation_gate_report_md=None
        if args.no_write_latest
        else str(markdown_path.relative_to(ROOT)),
        precomputed_foundation_gate_ms=foundation_gate_elapsed_ms,
        precomputed_foundation_gate_status=str(report.overall_status),
        precomputed_foundation_gate_result_count=len(report.results),
        precomputed_foundation_gate_warmup=(
            1 if _evaluated_revision_ref is not None else 0
        ),
        write_report=not args.no_write_latest,
    )
    report = report.model_copy(
        update={
            "latency_gate": latency_gate,
            "release_verification_lanes": build_release_lane_summary(),
        }
    )
    report_payload = report.model_dump_json(indent=2)
    report_payload_dict = json.loads(report_payload)
    if not args.no_write_latest:
        write_json_atomic(report_path, report_payload)
        write_markdown_payload(report_payload_dict, markdown_path)
    requested_output_path = None
    if args.output:
        requested_output_path = Path(args.output)
        if not requested_output_path.is_absolute():
            requested_output_path = ROOT / requested_output_path
        requested_output_path.parent.mkdir(parents=True, exist_ok=True)
        write_json_atomic(requested_output_path, report_payload)

    print("\n=== Foundation Gate Summary ===")
    print(f"Command mode: {command_mode}")
    if args.no_write_latest:
        print("Report: latest report update skipped")
        print("Markdown: latest markdown update skipped")
    else:
        print(f"Report: {report_path.relative_to(ROOT)}")
        print(f"Markdown: {markdown_path.relative_to(ROOT)}")
    if requested_output_path:
        print("Requested output: custom report copy written")
    print(f"Overall status: {report.overall_status}")
    print(report.summary)
    if report.latency_gate is not None:
        print(f"Latency gate: {report.latency_gate.status}")
        print(f"Latency p50/p95 status: {report.latency_gate.p50_p95_status}")
    if report.release_verification_lanes is not None:
        print(
            f"Release lane definitions: {report.release_verification_lanes.definition_status}"
        )
        print(
            "Release lane command execution: "
            f"{report.release_verification_lanes.command_execution_status}"
        )
        print(f"Release lane count: {report.release_verification_lanes.lane_count}")

    if command_failures:
        print("\nCommand failures:")
        for failure in command_failures:
            print(f"- {failure}")
        return 1

    if report.overall_status != FoundationGateStatus.passed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

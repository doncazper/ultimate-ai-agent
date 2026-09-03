from __future__ import annotations

import ctypes
import errno
import os
import stat
import sys
from pathlib import Path


def require_posix_private_path_support() -> None:
    if os.name != "posix" or not hasattr(os, "getuid"):
        raise ValueError("private path enforcement is unavailable on this platform")


def _darwin_extended_acl_tags(
    descriptor: int,
    *,
    purpose: str,
) -> tuple[int, ...]:
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
        raise ValueError(f"{purpose} access controls cannot be verified") from exc

    ctypes.set_errno(0)
    acl = acl_get_fd_np(descriptor, 0x100)  # ACL_TYPE_EXTENDED
    if not acl:
        if ctypes.get_errno() == errno.ENOENT:
            return ()
        raise ValueError(f"{purpose} access controls cannot be verified")

    try:
        tags: list[int] = []
        for index in range(170):
            ctypes.set_errno(0)
            entry = ctypes.c_void_p()
            entry_selector = 0 if index == 0 else -1  # FIRST, then NEXT
            entry_result = acl_get_entry(acl, entry_selector, ctypes.byref(entry))
            if entry_result == -1 and ctypes.get_errno() == errno.EINVAL and index:
                break
            if entry_result != 0 or entry.value is None:
                raise ValueError(f"{purpose} access controls cannot be verified")
            tag = ctypes.c_int()
            if acl_get_tag_type(entry, ctypes.byref(tag)) != 0:
                raise ValueError(f"{purpose} access controls cannot be verified")
            tags.append(tag.value)
        else:
            raise ValueError(f"{purpose} access controls cannot be verified")
    finally:
        free_result = acl_free(acl)
    if free_result != 0:
        raise ValueError(f"{purpose} access controls cannot be verified")
    return tuple(tags)


def require_no_extended_acl_fd(descriptor: int, *, purpose: str) -> None:
    """Reject macOS extended ACL entries on an already-open private path."""

    if _darwin_extended_acl_tags(descriptor, purpose=purpose):
        raise ValueError(f"{purpose} must not have an extended ACL")


def _require_no_extended_acl_grants_fd(
    descriptor: int,
    *,
    purpose: str,
) -> None:
    tags = _darwin_extended_acl_tags(descriptor, purpose=purpose)
    if any(tag != 2 for tag in tags):  # ACL_EXTENDED_DENY
        raise ValueError(f"{purpose} has unsafe extended ACL grants")


def _private_identity(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_uid,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _require_root_owned_lexical_symlinks(path: Path, *, purpose: str) -> None:
    """Permit only administrator-owned aliases such as macOS /tmp and /var."""

    if not path.is_absolute():
        raise ValueError(f"{purpose} must be absolute")
    nofollow_flag = getattr(os, "O_NOFOLLOW", 0)
    if not nofollow_flag:
        raise ValueError("private path enforcement is unavailable on this platform")
    lexical = Path(path.anchor)
    try:
        for component in path.parent.parts[1:]:
            lexical /= component
            metadata = os.lstat(lexical)
            if stat.S_ISLNK(metadata.st_mode):
                if metadata.st_uid != 0:
                    raise ValueError(
                        f"{purpose} contains an unsafe linked ancestor"
                    )
                continue
            if (
                not stat.S_ISDIR(metadata.st_mode)
                or metadata.st_uid not in {0, os.getuid()}
                or (
                    stat.S_IMODE(metadata.st_mode) & 0o022
                    and not stat.S_IMODE(metadata.st_mode) & stat.S_ISVTX
                )
            ):
                raise ValueError(f"{purpose} has an unsafe lexical ancestor")
            descriptor = os.open(
                lexical,
                os.O_RDONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_DIRECTORY", 0)
                | nofollow_flag,
            )
            try:
                opened = os.fstat(descriptor)
                if not os.path.samestat(metadata, opened):
                    raise ValueError(
                        f"{purpose} lexical ancestor changed during inspection"
                    )
                _require_no_extended_acl_grants_fd(descriptor, purpose=purpose)
                closed_over = os.fstat(descriptor)
                final = os.lstat(lexical)
            finally:
                os.close(descriptor)
            if (
                _private_identity(opened) != _private_identity(closed_over)
                or _private_identity(opened) != _private_identity(final)
                or not os.path.samestat(opened, final)
            ):
                raise ValueError(
                    f"{purpose} lexical ancestor changed during inspection"
                )
    except OSError as exc:
        raise ValueError(f"{purpose} ancestor is unavailable") from exc


def require_safe_private_ancestor_chain(path: Path, *, purpose: str) -> None:
    _require_root_owned_lexical_symlinks(path, purpose=purpose)
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise ValueError(f"{purpose} is unavailable") from exc
    nofollow_flag = getattr(os, "O_NOFOLLOW_ANY", 0) or getattr(
        os, "O_NOFOLLOW", 0
    )
    if not nofollow_flag:
        raise ValueError("private path enforcement is unavailable on this platform")
    ancestor = resolved.parent
    while True:
        descriptor = -1
        try:
            initial = os.lstat(ancestor)
            if (
                not stat.S_ISDIR(initial.st_mode)
                or initial.st_uid not in {0, os.getuid()}
                or (
                    stat.S_IMODE(initial.st_mode) & 0o022
                    and not stat.S_IMODE(initial.st_mode) & stat.S_ISVTX
                )
            ):
                raise ValueError(f"{purpose} has an unsafe ancestor")
            descriptor = os.open(
                ancestor,
                os.O_RDONLY
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_DIRECTORY", 0)
                | nofollow_flag,
            )
            opened = os.fstat(descriptor)
            if not os.path.samestat(initial, opened):
                raise ValueError(f"{purpose} ancestor changed during inspection")
            _require_no_extended_acl_grants_fd(descriptor, purpose=purpose)
            closed_over = os.fstat(descriptor)
            final = os.lstat(ancestor)
        except OSError as exc:
            raise ValueError(f"{purpose} ancestor is unavailable") from exc
        finally:
            if descriptor >= 0:
                os.close(descriptor)
        if (
            _private_identity(opened) != _private_identity(closed_over)
            or _private_identity(opened) != _private_identity(final)
            or not os.path.samestat(opened, final)
        ):
            raise ValueError(f"{purpose} ancestor changed during inspection")
        if ancestor.parent == ancestor:
            break
        ancestor = ancestor.parent


def _require_private_regular_metadata(
    metadata: os.stat_result,
    *,
    purpose: str,
    maximum_bytes: int,
    exact_bytes: int | None,
) -> None:
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) & 0o077
        or metadata.st_nlink != 1
        or metadata.st_size <= 0
        or metadata.st_size > maximum_bytes
        or (exact_bytes is not None and metadata.st_size != exact_bytes)
    ):
        raise ValueError(f"{purpose} must be an owner-only regular file")


def _require_private_tree_metadata(
    metadata: os.stat_result,
    *,
    purpose: str,
) -> None:
    if (
        not (stat.S_ISREG(metadata.st_mode) or stat.S_ISDIR(metadata.st_mode))
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) & 0o077
        or (stat.S_ISREG(metadata.st_mode) and metadata.st_nlink != 1)
    ):
        raise ValueError(f"{purpose} contains an unsafe entry")


def _inspect_private_tree_entry(
    path: Path,
    *,
    purpose: str,
) -> os.stat_result:
    try:
        initial = os.lstat(path)
    except OSError as exc:
        raise ValueError(f"{purpose} is unavailable") from exc
    if stat.S_ISLNK(initial.st_mode):
        raise ValueError(f"{purpose} contains an unsafe entry")
    _require_private_tree_metadata(initial, purpose=purpose)
    nofollow_flag = getattr(os, "O_NOFOLLOW_ANY", 0) or getattr(
        os, "O_NOFOLLOW", 0
    )
    if not nofollow_flag:
        raise ValueError("private path enforcement is unavailable on this platform")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | nofollow_flag
    if stat.S_ISDIR(initial.st_mode):
        flags |= getattr(os, "O_DIRECTORY", 0)
    else:
        flags |= getattr(os, "O_NONBLOCK", 0)
    descriptor = -1
    try:
        descriptor = os.open(path, flags)
        opened = os.fstat(descriptor)
        if not os.path.samestat(initial, opened):
            raise ValueError(f"{purpose} changed during inspection")
        _require_private_tree_metadata(opened, purpose=purpose)
        require_no_extended_acl_fd(descriptor, purpose=purpose)
        closed_over = os.fstat(descriptor)
        final = os.lstat(path)
    except OSError as exc:
        raise ValueError(f"{purpose} is unavailable") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if (
        _private_identity(opened) != _private_identity(closed_over)
        or _private_identity(opened) != _private_identity(final)
        or not os.path.samestat(opened, final)
    ):
        raise ValueError(f"{purpose} changed during inspection")
    return final


def read_private_file(
    path: Path,
    *,
    purpose: str,
    maximum_bytes: int,
    exact_bytes: int | None = None,
) -> tuple[Path, bytes]:
    require_posix_private_path_support()
    if not path.is_absolute() or path.is_symlink():
        raise ValueError(f"{purpose} must be an owner-only regular file")
    require_safe_private_ancestor_chain(path, purpose=purpose)
    try:
        resolved = path.resolve(strict=True)
        initial = os.lstat(resolved)
    except OSError as exc:
        raise ValueError(f"{purpose} is unavailable") from exc
    _require_private_regular_metadata(
        initial,
        purpose=purpose,
        maximum_bytes=maximum_bytes,
        exact_bytes=exact_bytes,
    )
    nofollow_flag = getattr(os, "O_NOFOLLOW_ANY", 0) or getattr(
        os, "O_NOFOLLOW", 0
    )
    if not nofollow_flag:
        raise ValueError("private path enforcement is unavailable on this platform")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
        | nofollow_flag
    )
    descriptor = -1
    try:
        descriptor = os.open(resolved, flags)
        opened = os.fstat(descriptor)
        if not os.path.samestat(initial, opened):
            raise ValueError(f"{purpose} changed during inspection")
        _require_private_regular_metadata(
            opened,
            purpose=purpose,
            maximum_bytes=maximum_bytes,
            exact_bytes=exact_bytes,
        )
        require_no_extended_acl_fd(descriptor, purpose=purpose)
        chunks: list[bytes] = []
        observed_bytes = 0
        while observed_bytes <= maximum_bytes:
            chunk = os.read(descriptor, min(64 * 1024, maximum_bytes + 1 - observed_bytes))
            if not chunk:
                break
            chunks.append(chunk)
            observed_bytes += len(chunk)
        closed_over = os.fstat(descriptor)
        final = os.lstat(resolved)
    except OSError as exc:
        raise ValueError(f"{purpose} is unavailable") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if (
        observed_bytes != opened.st_size
        or observed_bytes > maximum_bytes
        or _private_identity(opened) != _private_identity(closed_over)
        or _private_identity(opened) != _private_identity(final)
        or not os.path.samestat(opened, final)
    ):
        raise ValueError(f"{purpose} changed during inspection")
    content = b"".join(chunks)
    if exact_bytes is not None and len(content) != exact_bytes:
        raise ValueError(f"{purpose} has an invalid size")
    return resolved, content


def require_private_file(
    path: Path,
    *,
    purpose: str,
    maximum_bytes: int,
) -> Path:
    resolved, _content = read_private_file(
        path,
        purpose=purpose,
        maximum_bytes=maximum_bytes,
    )
    return resolved


def require_private_tree(
    path: Path,
    *,
    purpose: str,
    max_entries: int = 1_024,
    require_empty: bool = False,
) -> Path:
    require_posix_private_path_support()
    if not path.is_absolute() or path.is_symlink():
        raise ValueError(f"{purpose} must be absolute and owner-only")
    require_safe_private_ancestor_chain(path, purpose=purpose)
    try:
        resolved = path.resolve(strict=True)
        root_metadata = os.lstat(resolved)
    except OSError as exc:
        raise ValueError(f"{purpose} is unavailable") from exc
    if (
        not stat.S_ISDIR(root_metadata.st_mode)
        or root_metadata.st_uid != os.getuid()
        or stat.S_IMODE(root_metadata.st_mode) & 0o077
    ):
        raise ValueError(f"{purpose} must be owner-only")
    root_identity = _inspect_private_tree_entry(resolved, purpose=purpose)
    observed = 0
    pending = [(resolved, root_identity)]
    while pending:
        directory, expected_identity = pending.pop()
        before_scan = _inspect_private_tree_entry(directory, purpose=purpose)
        if _private_identity(before_scan) != _private_identity(expected_identity):
            raise ValueError(f"{purpose} changed during inspection")
        try:
            children = directory.iterdir()
            for child in children:
                observed += 1
                if observed > max_entries:
                    raise ValueError(f"{purpose} census is too large")
                child_identity = _inspect_private_tree_entry(child, purpose=purpose)
                if stat.S_ISDIR(child_identity.st_mode):
                    pending.append((child, child_identity))
        except OSError as exc:
            raise ValueError(f"{purpose} is unavailable") from exc
        after_scan = _inspect_private_tree_entry(directory, purpose=purpose)
        if _private_identity(before_scan) != _private_identity(after_scan):
            raise ValueError(f"{purpose} changed during inspection")
    if require_empty and observed:
        raise ValueError(f"{purpose} must be empty for a fresh run")
    _inspect_private_tree_entry(resolved, purpose=purpose)
    return resolved

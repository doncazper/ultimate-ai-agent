"""Bounded private transport-recovery storage, never book evidence or authority."""

from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import stat

from ultimate_ai_agent.core.finance.operator_workflow import (
    finance_authority_state_dir,
    finance_authority_state_path,
)
from ultimate_ai_agent.core.finance.repository import FinanceRepository


FINANCE_WORKSPACE_RECOVERY_MAX_BYTES = 128 * 1024


class FinanceWorkspaceRecoveryStore:
    """One last confirmed attempt; previews and inspection never create it.

    The private file contains content-free request/receipt metadata, not ledger
    data. Its integrity checks are not signatures. The workspace revalidates
    its typed binding, and every retry still passes current Core authority.
    """

    def __init__(self, repository_dir: Path) -> None:
        self.repository_dir = repository_dir
        self.directory = finance_authority_state_path(repository_dir)
        self.path = self.directory / "finance_workspace_recovery_v1.json"
        self.lock_path = self.directory / ".finance_workspace_recovery_v1.lock"

    def _directory_exists(self) -> bool:
        for directory in (self.directory.parent, self.directory):
            try:
                info = directory.lstat()
            except FileNotFoundError:
                return False
            if (
                not stat.S_ISDIR(info.st_mode)
                or stat.S_ISLNK(info.st_mode)
                or info.st_uid != os.getuid()
                or info.st_mode & 0o077
            ):
                raise ValueError("FINANCE_WORKSPACE_RECOVERY_DIRECTORY_INVALID")
        return True

    def read(self) -> bytes | None:
        if not self._directory_exists():
            return None
        try:
            info = self.path.lstat()
        except FileNotFoundError:
            return None
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError("FINANCE_WORKSPACE_RECOVERY_FILE_INVALID")
        return FinanceRepository._read_regular(
            self.path, max_bytes=FINANCE_WORKSPACE_RECOVERY_MAX_BYTES
        )

    def write(self, payload: bytes) -> None:
        if len(payload) > FINANCE_WORKSPACE_RECOVERY_MAX_BYTES:
            raise ValueError("FINANCE_WORKSPACE_RECOVERY_CAPACITY_EXCEEDED")
        if not self._directory_exists():
            raise ValueError("FINANCE_WORKSPACE_RECOVERY_DIRECTORY_REQUIRED")
        # Validate a prior target before replacing it, including hard links.
        self.read()
        FinanceRepository._atomic_write(self.path, payload)

    @contextmanager
    def confirmed_attempt(self):
        """Serialize one exact attempt, fail promptly if another is executing."""

        finance_authority_state_dir(self.repository_dir)
        flags = os.O_RDWR | os.O_CREAT | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(self.lock_path, flags, 0o600)
        locked = False
        try:
            info = os.fstat(descriptor)
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_nlink != 1
                or info.st_uid != os.getuid()
                or info.st_mode & 0o077
            ):
                raise ValueError("FINANCE_WORKSPACE_RECOVERY_LOCK_INVALID")
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ValueError("FINANCE_WORKSPACE_RECOVERY_ATTEMPT_BUSY") from None
            locked = True
            linked = self.lock_path.lstat()
            if (linked.st_dev, linked.st_ino) != (info.st_dev, info.st_ino):
                raise ValueError("FINANCE_WORKSPACE_RECOVERY_LOCK_CHANGED")
            yield
        finally:
            if locked:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

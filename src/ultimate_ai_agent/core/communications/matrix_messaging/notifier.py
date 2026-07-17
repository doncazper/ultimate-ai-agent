from __future__ import annotations

import hashlib
import os
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .constants import (
    MATRIX_MESSAGING_NOTIFICATION_DISCLOSURE_REF,
    MATRIX_MESSAGING_NOTIFICATION_POLICY_REF,
    MATRIX_MESSAGING_NOTIFICATION_TARGET_REF,
)
from .contracts import MatrixMessagingCommand, stable_matrix_messaging_ref


_OSASCRIPT = Path("/usr/bin/osascript")
_FIXED_NOTIFICATION_SCRIPT = (
    'display notification "New Matrix activity" with title "UAA Messenger"'
)


class MatrixDesktopNotificationError(RuntimeError):
    pass


@dataclass(frozen=True)
class MatrixDesktopNotificationReceipt:
    receipt_ref: str
    displayed: bool
    content_included: bool = False


class MatrixDesktopNotifier:
    """Exact macOS notification adapter with a fixed, non-content disclosure."""

    def __init__(self, *, executable: Path = _OSASCRIPT) -> None:
        if sys.platform != "darwin":
            raise MatrixDesktopNotificationError(
                "MATRIX_DESKTOP_NOTIFICATION_MACOS_REQUIRED"
            )
        if executable != _OSASCRIPT:
            raise MatrixDesktopNotificationError(
                "MATRIX_DESKTOP_NOTIFICATION_EXECUTABLE_SUBSTITUTION_DENIED"
            )
        info = os.lstat(executable)
        if (
            not stat.S_ISREG(info.st_mode)
            or stat.S_ISLNK(info.st_mode)
            or info.st_uid != 0
            or info.st_mode & 0o022
        ):
            raise MatrixDesktopNotificationError(
                "MATRIX_DESKTOP_NOTIFICATION_EXECUTABLE_INVALID"
            )
        self._executable = executable
        self.binding_ref = stable_matrix_messaging_ref(
            "notification-adapter-binding-ref:matrix-messaging",
            {
                "executable_identity": hashlib.sha256(
                    f"{info.st_dev}:{info.st_ino}:{info.st_size}".encode()
                ).hexdigest(),
                "script_sha256": hashlib.sha256(
                    _FIXED_NOTIFICATION_SCRIPT.encode()
                ).hexdigest(),
                "content_disclosure": False,
            },
        )

    def notify(
        self, command: MatrixMessagingCommand
    ) -> MatrixDesktopNotificationReceipt:
        if (
            command.notification_target_ref
            != MATRIX_MESSAGING_NOTIFICATION_TARGET_REF
            or command.notification_policy_ref
            != MATRIX_MESSAGING_NOTIFICATION_POLICY_REF
            or command.notification_disclosure_ref
            != MATRIX_MESSAGING_NOTIFICATION_DISCLOSURE_REF
            or command.notification_generation_ref is None
            or command.room_ref is None
            or command.event_ref is None
            or command.content_fingerprint_ref is None
        ):
            raise MatrixDesktopNotificationError(
                "MATRIX_DESKTOP_NOTIFICATION_SCOPE_INVALID"
            )
        try:
            completed = subprocess.run(
                [os.fspath(self._executable), "-e", _FIXED_NOTIFICATION_SCRIPT],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
                check=False,
                shell=False,
                start_new_session=True,
                env={"LANG": "C", "LC_ALL": "C", "PATH": "/usr/bin:/bin"},
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise MatrixDesktopNotificationError(
                "MATRIX_DESKTOP_NOTIFICATION_EXECUTION_FAILED"
            ) from exc
        if completed.returncode != 0:
            raise MatrixDesktopNotificationError(
                "MATRIX_DESKTOP_NOTIFICATION_DISPLAY_FAILED"
            )
        return MatrixDesktopNotificationReceipt(
            receipt_ref=stable_matrix_messaging_ref(
                "receipt-ref:matrix-notification:displayed",
                {
                    "request_fingerprint_ref": command.request_fingerprint_ref,
                    "notification_generation_ref": (
                        command.notification_generation_ref
                    ),
                    "notification_target_ref": command.notification_target_ref,
                    "notification_policy_ref": command.notification_policy_ref,
                    "notification_disclosure_ref": (
                        command.notification_disclosure_ref
                    ),
                    "displayed": True,
                },
            ),
            displayed=True,
        )


__all__ = [
    "MatrixDesktopNotificationError",
    "MatrixDesktopNotificationReceipt",
    "MatrixDesktopNotifier",
]

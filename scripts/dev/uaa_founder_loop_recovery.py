#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ultimate_ai_agent.core.storage.founder_loop import DEFAULT_FOUNDER_LOOP_STATE_DIR
from ultimate_ai_agent.core.storage.founder_loop_recovery import (
    FounderLoopRecoveryError,
    create_founder_loop_backup,
    restore_founder_loop_backup,
    verify_founder_loop_backup,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Offline Founder Loop backup, verification, and restore."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    backup = subparsers.add_parser("backup")
    backup.add_argument(
        "--state-dir", type=Path, default=DEFAULT_FOUNDER_LOOP_STATE_DIR
    )
    backup.add_argument("--backup-dir", type=Path, required=True)
    backup.add_argument("--confirm-offline", action="store_true")

    verify = subparsers.add_parser("verify")
    verify.add_argument("--backup-dir", type=Path, required=True)

    restore = subparsers.add_parser("restore")
    restore.add_argument("--backup-dir", type=Path, required=True)
    restore.add_argument("--target-state-dir", type=Path, required=True)
    restore.add_argument("--confirm-offline-restore", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "backup":
            if not args.confirm_offline:
                raise FounderLoopRecoveryError(
                    "FOUNDER_LOOP_OFFLINE_CONFIRMATION_REQUIRED"
                )
            receipt = create_founder_loop_backup(args.state_dir, args.backup_dir)
        elif args.command == "verify":
            receipt = verify_founder_loop_backup(args.backup_dir)
        else:
            if not args.confirm_offline_restore:
                raise FounderLoopRecoveryError(
                    "FOUNDER_LOOP_RESTORE_CONFIRMATION_REQUIRED"
                )
            receipt = restore_founder_loop_backup(
                args.backup_dir,
                args.target_state_dir,
            )
    except FounderLoopRecoveryError as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error_ref": f"error-ref:{str(exc).lower().replace('_', '-')}",
                    "safe_message": "Founder Loop recovery operation failed closed.",
                    "raw_paths_included": False,
                },
                sort_keys=True,
            )
        )
        return 1
    except Exception:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error_ref": "error-ref:founder-loop-recovery-internal-error",
                    "safe_message": "Founder Loop recovery operation failed closed.",
                    "raw_paths_included": False,
                },
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps({"ok": True, "result": receipt}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

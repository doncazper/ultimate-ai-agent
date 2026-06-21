from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


UAA_LOCAL_MODEL_ROOTS_ENV = "UAA_LOCAL_MODEL_ROOTS"


def add_local_model_parser(subparsers: argparse._SubParsersAction[Any]) -> None:
    local_model_parser = subparsers.add_parser(
        "local-model",
        help="Read-only local model inventory inspection.",
    )
    local_model_subparsers = local_model_parser.add_subparsers(dest="local_model_command")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="Emit safe structured JSON.")
    common.add_argument(
        "--root",
        action="append",
        default=None,
        help="Configured local model root to inspect. May be repeated.",
    )
    local_model_subparsers.add_parser("status", parents=[common])
    local_model_subparsers.add_parser("list", parents=[common])
    inspect_parser = local_model_subparsers.add_parser("inspect", parents=[common])
    inspect_parser.add_argument("model_ref")


def command_local_model(root: Path, args: argparse.Namespace) -> int:
    _ensure_src_path(root)
    from ultimate_ai_agent.core.local_model_management.inventory import (
        inspect_local_model_inventory,
        inspect_local_model_ref,
        local_model_inventory_as_json,
    )

    command = args.local_model_command or "status"
    configured_roots = _configured_roots(args)
    if command == "status":
        report = inspect_local_model_inventory(configured_roots)
        if args.json:
            print(local_model_inventory_as_json(report), end="")
            return 0
        print("Ultimate AI Agent local model inventory")
        print(f"status: {report.status}")
        print(f"root_refs: {len(report.roots)}")
        print(f"model_refs: {len(report.models)}")
        print(f"safe_summary: {report.safe_summary}")
        blocked_roots = [item for item in report.roots if item.status == "blocked"]
        if blocked_roots:
            print(f"blocked_root_refs: {len(blocked_roots)}")
        return 0
    if command == "list":
        report = inspect_local_model_inventory(configured_roots)
        if args.json:
            print(local_model_inventory_as_json(report), end="")
            return 0
        if not report.models:
            print("No local model candidate refs found.")
            return 0
        for item in report.models:
            print(
                " ".join(
                    [
                        item.model_ref,
                        f"runtime={item.runtime_family}",
                        f"artifact={item.artifact_kind}",
                        f"status={item.runnable_status}",
                        f"adapter={item.adapter_requirement}",
                        f"size={item.size_bucket}",
                        f"memory={item.memory_posture_bucket}",
                    ]
                )
            )
        return 0
    if command == "inspect":
        item = inspect_local_model_ref(args.model_ref, configured_roots)
        if item is None:
            if args.json:
                print(
                    json.dumps(
                        {
                            "status": "blocked",
                            "reason_code": "model_ref_not_found",
                            "model_ref": args.model_ref,
                        },
                        indent=2,
                        sort_keys=True,
                    )
                )
            else:
                print(f"model_ref: {args.model_ref}")
                print("status: blocked")
                print("reason_code: model_ref_not_found")
            return 1
        if args.json:
            print(json.dumps(item.to_dict(), indent=2, sort_keys=True))
            return 0
        for key, value in item.to_dict().items():
            if isinstance(value, list):
                value = ",".join(value)
            print(f"{key}: {value}")
        return 0
    print(f"Unknown local-model command: {command}")
    return 2


def _configured_roots(args: argparse.Namespace) -> tuple[Path, ...] | None:
    explicit = getattr(args, "root", None)
    values = explicit or _env_roots()
    if not values:
        return None
    return tuple(Path(value).expanduser() for value in values if value.strip())


def _env_roots() -> list[str]:
    raw_value = os.environ.get(UAA_LOCAL_MODEL_ROOTS_ENV, "")
    return [part for part in raw_value.split(os.pathsep) if part.strip()]


def _ensure_src_path(root: Path) -> None:
    src_path = str(root / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

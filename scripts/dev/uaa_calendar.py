#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.control_center.calendar_adoption import (  # noqa: E402
    CalendarAdoptionStore,
)
from ultimate_ai_agent.core.ecosystem.calendar import CalendarView  # noqa: E402


def inspect_adoption(args: argparse.Namespace) -> int:
    view = CalendarAdoptionStore(args.state_dir).read_view(
        view=CalendarView(args.view),
        anchor=(datetime.fromisoformat(args.anchor) if args.anchor else None),
        timezone_name=args.timezone,
    )
    if args.include_private:
        payload = {
            **view.model_dump(mode="json"),
            "private_values_included": True,
            "raw_paths_included": False,
        }
    else:
        payload = {
            "schema_version": "uaa-calendar-adoption-cli-inspection.v1",
            "contract_ref": view.contract_ref,
            "calendar_set_ref": view.calendar_set_ref,
            "status": view.status,
            "revision": view.revision,
            "current_state_ref": view.current_state_ref,
            "calendar_count": len(view.calendars),
            "occurrence_count": len(view.occurrence_items),
            "archived_event_count": len(view.archived_events),
            "conflict_count": len(view.conflict_items),
            "view": view.view,
            "timezone": view.timezone,
            "range_starts_at": view.range_starts_at,
            "range_ends_at": view.range_ends_at,
            "result_ref": view.result_ref,
            "can_undo": view.can_undo,
            "next_safe_action": view.next_safe_action,
            "backend_owned": view.backend_owned,
            "local_only": view.local_only,
            "exact_approval_required": view.exact_approval_required,
            "backup_restore_available": view.backup_restore_available,
            "external_calendar_write_enabled": view.external_calendar_write_enabled,
            "connector_read_enabled": view.connector_read_enabled,
            "connector_write_enabled": view.connector_write_enabled,
            "provider_model_call_enabled": view.provider_model_call_enabled,
            "browser_automation_enabled": view.browser_automation_enabled,
            "shell_subprocess_execution_enabled": (
                view.shell_subprocess_execution_enabled
            ),
            "background_scheduling_enabled": view.background_scheduling_enabled,
            "notification_delivery_enabled": view.notification_delivery_enabled,
            "production_authority_enabled": view.production_authority_enabled,
            "private_values_included": False,
            "raw_paths_included": False,
        }
    print(
        json.dumps(
            payload, indent=2 if args.pretty else None, sort_keys=True, default=str
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect the founder-private local Calendar without changing it."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect = subparsers.add_parser(
        "inspect-adoption", help="Inspect Calendar lifecycle state read-only."
    )
    inspect.add_argument("--state-dir", type=Path, default=None)
    inspect.add_argument(
        "--view", choices=[item.value for item in CalendarView], default="week"
    )
    inspect.add_argument("--anchor", default=None, help="ISO-8601 aware timestamp.")
    inspect.add_argument("--timezone", default="UTC")
    inspect.add_argument("--include-private", action="store_true")
    inspect.add_argument("--pretty", action="store_true")
    inspect.set_defaults(func=inspect_adoption)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

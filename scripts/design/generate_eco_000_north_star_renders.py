#!/usr/bin/env python3
"""Generate deterministic ECO-000 planning-only SVG render concepts."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs/design/ecosystem_north_star/renders"


@dataclass(frozen=True)
class Surface:
    surface_id: str
    filename: str
    active: str
    eyebrow: str
    title: str
    summary: str
    primary: str
    secondary: str
    cards: tuple[tuple[str, str, str], ...]
    width: int = 1440
    height: int = 960


SURFACES = (
    Surface(
        "ECO-TODAY-DESKTOP-DEFAULT",
        "01_ecosystem_today_home.svg",
        "Today",
        "Sunday, July 12 · Private local workspace",
        "A calm plan for today",
        "Five owner-backed items need attention. Nothing runs without review.",
        "Review morning plan",
        "Open sources",
        (
            ("09:30 · Calendar", "Product review", "Local event · current · Calendar owns"),
            ("Task · due today", "Confirm migration fixture counts", "Tasks owns · proposal only"),
            ("CRM follow-up", "Northwind renewal", "CRM owns · exact local edit blocked"),
        ),
    ),
    Surface(
        "ECO-CALENDAR-DESKTOP-WEEK",
        "02_calendar_home.svg",
        "Calendar",
        "Week of July 13 · Local calendars",
        "Calendar",
        "Manual events work first. Account sync remains blocked.",
        "New local event",
        "Resolve conflicts",
        (
            ("Mon 09:00", "Weekly planning", "Work · 45 min"),
            ("Tue 13:30", "Client review", "Linked CRM opportunity · private"),
            ("Thu 16:00", "Focus block", "Linked Task · local projection"),
        ),
    ),
    Surface(
        "ECO-TASKS-DESKTOP-TODAY",
        "03_tasks_home.svg",
        "Tasks",
        "Today · 8 open · 2 waiting",
        "Tasks",
        "Capture, clarify, complete, and undo with local/manual data.",
        "Capture task",
        "Start daily review",
        (
            ("Now", "Draft storage migration acceptance", "Project: Ecosystem · high focus"),
            ("Waiting", "Receive design review", "Dependency visible · no auto-run"),
            ("Later", "Prepare recurrence matrix", "Local task · no calendar write"),
        ),
    ),
    Surface(
        "ECO-BOARDS-DESKTOP-GENERAL",
        "04_boards_home.svg",
        "Boards",
        "Product delivery · 3 lanes · 12 cards",
        "Boards",
        "Cards project canonical subjects; board placement never owns domain state.",
        "New board item",
        "Configure view",
        (
            ("Ready", "Calendar recurrence proof", "Task projection · Tasks owns"),
            ("Doing", "CRM preset acceptance", "Plan-step projection · Plans owns"),
            ("Review", "Render state coverage", "Standalone BoardItem"),
        ),
    ),
    Surface(
        "ECO-CRM-SALES-DESKTOP-HOME",
        "05_crm_sales_home.svg",
        "CRM",
        "Sales workspace · Local records only",
        "Relationship command center",
        "Pipeline, people, meetings, and follow-ups with exact owner links.",
        "Add relationship",
        "Review follow-ups",
        (
            ("Pipeline", "4 opportunities · $180k", "Shared Boards projection"),
            ("Next meeting", "Northwind review · Tue 13:30", "Calendar Event link"),
            ("Follow-up", "Send revised scope", "Proposal only · send blocked"),
        ),
    ),
    Surface(
        "ECO-INBOX-DESKTOP-MULTIAPP-PROPOSAL",
        "06_inbox_source_proposal.svg",
        "Inbox",
        "Selected synthetic source · Content is untrusted",
        "Turn one source into reviewed proposals",
        "Nothing becomes truth or authority until each owner accepts an exact change.",
        "Review 3 proposals",
        "Keep as source only",
        (
            ("Calendar proposal", "Create product review hold", "Not applied · source cited"),
            ("Task proposal", "Prepare revised scope", "Not applied · Tasks owner"),
            ("CRM link proposal", "Relate Northwind opportunity", "Not linked · private scope"),
        ),
    ),
    Surface(
        "ECO-CHANGESET-DESKTOP-REVIEW",
        "07_cross_app_changeset_review.svg",
        "Action Inbox",
        "ChangeSet review · 3 local operations",
        "Review the exact consequences",
        "One readable review; every operation keeps its own scope and precondition.",
        "Approve exact local set",
        "Reject all",
        (
            ("1 · Calendar", "Create local event", "Local atomic · rollback plan ready"),
            ("2 · Tasks", "Create follow-up task", "Depends on 1 · version current"),
            ("3 · CRM", "Link opportunity", "Depends on 1 · no copied Event"),
        ),
    ),
    Surface(
        "ECO-CHANGESET-DESKTOP-PARTIAL",
        "08_partial_failure_compensation.svg",
        "Evidence",
        "Partial completion · External operation failed",
        "Two changes applied. One needs review.",
        "UAA will not call this complete or pretend external work was atomic.",
        "Review safe next action",
        "Open receipts",
        (
            ("Applied", "Local Task created", "Receipt verified · no retry"),
            ("Applied", "CRM link recorded", "Receipt verified · local atomic"),
            ("Failed", "External calendar update", "Recovery required · compensation available"),
        ),
    ),
    Surface(
        "ECO-SEARCH-DESKTOP-PALETTE",
        "09_global_search_command.svg",
        "Search",
        "Global search · Workspace: Work",
        "Search canonical records",
        "Results explain owner, workspace, provenance, privacy, and allowed proposals.",
        "Open selected",
        "Create proposal",
        (
            ("Task", "Migration acceptance checklist", "Tasks · why: title match · current"),
            ("Event", "ECO review", "Calendar · why: date + project link"),
            ("Opportunity", "Northwind renewal", "CRM · private fields hidden"),
        ),
    ),
    Surface(
        "ECO-SETTINGS-DESKTOP-PRIVACY",
        "10_privacy_source_settings.svg",
        "Settings",
        "Privacy and sources · Local profile",
        "Know what is stored and eligible",
        "Configuration and catalog visibility do not grant read, write, or model authority.",
        "Review source policy",
        "Export safe report",
        (
            ("Private Relationships", "Restricted", "No transcripts, wallboard, shared search, or cloud context"),
            ("Calendar source", "Not configured", "Catalog entry only · no account access"),
            ("Local app data", "ECO-001 required", "Encryption dependency unresolved"),
        ),
    ),
    Surface(
        "ECO-TODAY-NARROW-AGENDA",
        "11_narrow_today_agenda_capture.svg",
        "Today",
        "Narrow · Local and private",
        "Today",
        "Agenda, capture, and owner-backed attention without hiding risk.",
        "Capture",
        "Agenda",
        (
            ("09:30", "Product review", "Calendar"),
            ("Now", "Migration checklist", "Tasks"),
            ("Review", "One proposal blocked", "Action Inbox"),
        ),
        width=390,
        height=844,
    ),
    Surface(
        "ECO-ORGANIZER-WALLBOARD-SCHEDULE",
        "12_wallboard_organizer_schedule.svg",
        "Organizer",
        "Wallboard · View only · Private details hidden",
        "Home rhythm",
        "Schedule, routines, and lists with a locked privacy floor.",
        "Lock display",
        "Show today",
        (
            ("07:30", "Morning routine", "3 of 5 complete"),
            ("17:30", "Dinner plan", "Vegetable bowls · local list"),
            ("Tonight", "Household reset", "4 shared chores · identities deferred"),
        ),
        width=1920,
        height=1080,
    ),
)


def _text(x: int, y: int, value: str, size: int, color: str, weight: int = 500) -> str:
    return (
        f'<text x="{x}" y="{y}" font-family="Inter, ui-sans-serif, system-ui" '
        f'font-size="{size}" font-weight="{weight}" fill="{color}">{escape(value)}</text>'
    )


def _render(surface: Surface) -> str:
    narrow = surface.width < 600
    rail = 0 if narrow else 220
    main_x = 24 if narrow else rail + 44
    content_w = surface.width - main_x - (24 if narrow else 44)
    header_y = 28 if narrow else 56
    card_top = 330 if narrow else 330
    card_gap = 18
    card_w = content_w if narrow else (content_w - card_gap * 2) // 3
    card_h = 126 if narrow else 190
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{surface.width}" height="{surface.height}" viewBox="0 0 {surface.width} {surface.height}">',
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#f7f6f1"/><stop offset="1" stop-color="#edf3ef"/></linearGradient><filter id="shadow"><feDropShadow dx="0" dy="8" stdDeviation="18" flood-opacity=".08"/></filter></defs>',
        f'<rect width="{surface.width}" height="{surface.height}" fill="url(#bg)"/>',
    ]
    if not narrow:
        parts.extend(
            [
                f'<rect x="0" y="0" width="{rail}" height="{surface.height}" fill="#17211e"/>',
                _text(28, 48, "UAA", 23, "#f7f6f1", 750),
                _text(28, 75, "Coherent apps · concept", 12, "#a9b8b2", 500),
            ]
        )
        for index, item in enumerate(("Today", "Inbox", "Calendar", "Tasks", "Boards", "Plans", "CRM", "Actions", "Memory", "Evidence", "Settings")):
            y = 132 + index * 45
            if item == surface.active:
                parts.append(f'<rect x="16" y="{y - 27}" width="188" height="36" rx="10" fill="#30483f"/>')
            parts.append(_text(30, y - 3, item, 14, "#f3f6f4" if item == surface.active else "#a9b8b2", 650 if item == surface.active else 500))
        parts.append(_text(28, surface.height - 34, "PLANNING ONLY · ECO-000", 10, "#91a59d", 700))
    if narrow:
        parts.extend(
            [
                _text(main_x, header_y, surface.eyebrow, 11, "#607069", 650),
                '<rect x="24" y="48" width="102" height="28" rx="14" fill="#e1eee8"/>',
                _text(37, 67, "Private", 11, "#245b45", 700),
                '<rect x="136" y="48" width="104" height="28" rx="14" fill="#f3e9d3"/>',
                _text(149, 67, "Review only", 11, "#7a5821", 700),
                _text(main_x, 142, surface.title, 38, "#17211e", 760),
                _text(main_x, 184, "Agenda, capture, and owner-backed attention", 13, "#52625c", 500),
                _text(main_x, 204, "without hiding risk or private scope.", 13, "#52625c", 500),
                f'<rect x="{main_x}" y="{230}" width="138" height="44" rx="12" fill="#1d5b46"/>',
                _text(main_x + 16, 258, surface.primary, 13, "#ffffff", 700),
                f'<rect x="{main_x + 150}" y="230" width="126" height="44" rx="12" fill="#ffffff" stroke="#cfd8d3"/>',
                _text(main_x + 164, 258, surface.secondary, 13, "#29463b", 650),
            ]
        )
    else:
        parts.extend(
            [
                _text(main_x, header_y, surface.eyebrow, 13, "#607069", 650),
                f'<rect x="{surface.width - 430}" y="{header_y - 22}" width="190" height="28" rx="14" fill="#e1eee8"/>',
                _text(surface.width - 416, header_y - 3, "Privacy: workspace-bound", 11, "#245b45", 700),
                f'<rect x="{surface.width - 224}" y="{header_y - 22}" width="180" height="28" rx="14" fill="#f3e9d3"/>',
                _text(surface.width - 210, header_y - 3, "Authority: review only", 11, "#7a5821", 700),
                _text(main_x, 150, surface.title, 48, "#17211e", 760),
                _text(main_x, 194, surface.summary, 17, "#52625c", 500),
                f'<rect x="{main_x}" y="235" width="190" height="44" rx="12" fill="#1d5b46"/>',
                _text(main_x + 16, 263, surface.primary, 13, "#ffffff", 700),
                f'<rect x="{main_x + 204}" y="235" width="170" height="44" rx="12" fill="#ffffff" stroke="#cfd8d3"/>',
                _text(main_x + 220, 263, surface.secondary, 13, "#29463b", 650),
            ]
        )
    for index, (kicker, title, detail) in enumerate(surface.cards):
        x = main_x if narrow else main_x + index * (card_w + card_gap)
        y = card_top + index * (card_h + 14) if narrow else card_top
        parts.extend(
            [
                f'<rect x="{x}" y="{y}" width="{card_w}" height="{card_h}" rx="16" fill="#ffffff" filter="url(#shadow)"/>',
                _text(x + 18, y + 30, kicker.upper(), 11, "#688078", 750),
                _text(x + 18, y + 65, title, 17 if narrow else 21, "#17211e", 700),
                _text(x + 18, y + 94 if narrow else y + 104, detail, 11 if narrow else 13, "#5b6b65", 500),
            ]
        )
        if not narrow:
            parts.append(f'<rect x="{x + 18}" y="{y + 140}" width="{card_w - 36}" height="1" fill="#e7ece9"/>')
            parts.append(_text(x + 18, y + 168, "Inspect owner and evidence →", 12, "#1d5b46", 700))
    footer_y = surface.height - 28
    parts.append(_text(main_x, footer_y, f"{surface.surface_id} · synthetic-medium · DRAFT REVIEWED · not shipped", 10, "#68756f", 650))
    parts.append("</svg>")
    return "".join(parts)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for surface in SURFACES:
        (OUTPUT / surface.filename).write_text(_render(surface), encoding="utf-8")
    print(f"generated {len(SURFACES)} ECO-000 SVG renders")


if __name__ == "__main__":
    main()

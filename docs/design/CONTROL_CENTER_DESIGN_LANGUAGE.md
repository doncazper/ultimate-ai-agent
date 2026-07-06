# Control Center Design Language

Status: Active design governance for v0.19.1. Documentation only.

The Web Control Center is an operational control surface, not a marketing site. It should feel calm, dense, readable, status-first, and built for repeated inspection.

Layout principles:

- dashboard-first, not marketing-first.
- no decorative hero sections.
- no oversized marketing cards.
- no cards nested inside cards.
- no one-note purple or dark-blue palette.
- compact but readable information density.
- status-first layouts for safety, readiness, route, and capability views.
- text must not overlap or overflow on desktop, tablet, or mobile widths.
- stable dimensions should prevent status badges, labels, and loading text from shifting layout.

State language:

- read-only and preview-only surfaces must be obvious.
- planned, disabled, blocked, simulated, dry-run-only, manual-only, and validation-only capabilities must be visually distinct.
- mock fallback must be visibly mock and non-authoritative.
- degraded state must identify which data may be fallback.
- connection state is informational and non-authoritative.
- local backend connected must not imply authority.
- online must not imply production readiness.

Interaction principles:

- controls must use safe, specific action language.
- dangerous words are governed by `docs/design/UI_COPY_AND_ACTION_LANGUAGE.md`.
- UI should not hide dangerous controls in responsive layouts.
- disabled/planned features must not sound available.
- status/risk treatment must use text, not color alone.

This milestone defines governance only. It does not change frontend behavior, styling, dependencies, components, routes, or runtime authority.

North-star visual targets for the contained desktop-app direction live in
`docs/design/control_center_north_star/README.md`, with route coverage in
`docs/design/control_center_north_star/SURFACE_COVERAGE.md` and static shell
rules in `docs/design/control_center_north_star/APP_SHELL_BASELINE.md`. These
renders are design targets only and do not claim shipped UI behavior or new
authority.

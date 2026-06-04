# File Review Surface Readiness

Status: active M34 readiness documentation.
Current through: **v0.38.2**.

M36 is the earliest possible CCC File Review Surface milestone. M34 does not
add this surface.

## Future M36 Display Scope

M36 may display:

- review packet refs.
- redacted preview excerpts.
- redaction summaries.
- redaction verification status.
- safe file refs and root refs.
- review-only decision summaries.
- no-raw-content receipt summaries.
- visibly mock fallback data when live data is unavailable.

## Controls That Must Remain Absent Until Separately Reviewed

M36 must not add:

- raw preview controls.
- file browser or file picker controls.
- upload controls.
- export, download, or copy-raw controls.
- approve/deny persistence controls before M37.
- context proposal controls before M38.
- context injection controls.
- memory write controls.
- execute/run/tool/action controls.
- arbitrary root selector controls.

## Browser Smoke Focus

Future browser smoke review should verify that the surface is visibly
review-only, renders redacted data only, exposes no unsafe controls, preserves
mock-data non-authority labeling, and does not create backend route or endpoint
drift.

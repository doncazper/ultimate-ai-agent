# Product Loop 007 Morning Briefing V1

Status: implemented as a backend-owned local read model.

Product Loop 007 adds `morning_briefing_v1_read_model` to the existing
Morning Briefing read route:

```text
contract-ref:product-loop-007-morning-briefing-v1:v1
```

The read model turns the local daily briefing into a safe operator spine for:

- Today summary refs
- open Action refs
- follow-up refs
- memory review refs
- evidence timeline refs
- repo and workbench status refs
- source-readiness blockers and missing-source refs

This is local read-model posture only. It is safe-ref-only, backend-owned, and
bounded. It adds no connector reads, no connector runtime, no connector writes,
no email/calendar/account fetch, no account auth, no live web, no runtime
model/provider calls, no automatic recommendations, no hidden memory writes,
no memory writes, no context injection, no repo writes, no workbench apply, no
notification delivery, no source refresh, no action execution, no public beta,
no distribution, and no production authority. Missing integrations remain
blocked/readiness states.

Recommendation refs and next-safe-action labels are review candidates only.
They are not automatic recommendations, task creation, source refresh,
connector runtime, model/provider output, or authority to act.

No-authority phrases: no connector reads; no connector runtime; no connector writes; no email/calendar/account fetch; no live web; no runtime model/provider calls; no automatic recommendations; no hidden memory writes; no repo writes; no workbench apply; no shell/subprocess execution; no browser execution; missing integrations remain blocked/readiness states.

The companion CLI inspection path is:

```bash
PYTHONPATH=src .venv/bin/python scripts/inspect_morning_briefing_v1.py
```

Inspection is read-only, safe-ref-only, and redacted. Briefing records must not
include raw prompt content, raw response content, raw provider payload content,
raw provider exchange content, raw local path content, raw log content, account
identifiers, usernames, hostnames, credentials, secrets, cookies, tokens,
serials, or environment dumps. Missing backend read-model data fails closed in
Control Center; React does not backfill Morning Briefing V1 from mock data.

Redaction phrases: account identifiers; usernames; hostnames; credentials; secrets.

## Verification Lane

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_morning_briefing_v1.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_founder_loop_storage_briefing.py tests/test_control_center_founder_loop_api.py tests/test_control_center_api_routes.py
PYTHONPATH=src .venv/bin/python scripts/verify_product_loop_007_morning_briefing_v1.py
```

## Still Blocked

This lane adds no email/calendar/account fetch, no live web, no connector
reads, no connector writes, no connector runtime, no provider/model calls, no
automatic recommendations, no hidden memory writes, no memory writes, no
context injection, no repo writes, no workbench apply, no notification
delivery, no source refresh, no reminders, no scheduler, no action execution,
no shell/subprocess execution, no browser execution, no public beta, no
distribution, and no production authority.

# Product Loop 004 Follow-Up Tracker

Status: implemented as a backend-owned local read model.

Product Loop 004 adds `follow_up_tracker` to the existing Founder Loop read
surfaces for Today, Action Inbox, and Morning Briefing:

```text
contract-ref:product-loop-004-follow-up-tracker:v1
```

The tracker surfaces reviewed local refs for relationship follow-ups, promises,
open loops, pending replies, and deferred decisions. It is a review-only
operator posture over existing Founder Loop and reviewed-memory records. It is
not a reminder engine, message sender, scheduler, connector reader, source
fetcher, automatic task creator, memory writer, model/provider caller, context
injection path, or action-execution path.

The companion CLI inspection path is:

```bash
PYTHONPATH=src .venv/bin/python scripts/inspect_follow_up_tracker.py
```

Inspection is read-only, safe-ref-only, and redacted. Missing email/calendar or
inbox source access appears as blocked/no-source posture instead of fabricated
pending-reply truth.

## Authority Boundary

All follow-up tracker records must keep these flags false:

- reminder scheduler enabled
- message send enabled
- connector read/write enabled
- email/calendar fetch enabled
- automatic task creation enabled
- action execution enabled
- runtime model calls enabled
- hidden memory write authorized
- context injection authorized
- production authority enabled

Every item must expose safe refs, blocked-state refs, evidence or source refs
when available, stale/no-source posture where applicable, and a next safe
operator review action.

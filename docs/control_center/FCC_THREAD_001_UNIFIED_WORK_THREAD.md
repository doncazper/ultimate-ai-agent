# FCC-THREAD-001 Unified Work Thread Read Model

Status: implemented read model, safe refs only.

FCC-THREAD-001 makes the existing Founder Loop product spine easier to inspect
without adding execution authority. Python Agent Core builds
`unified_work_thread_read_model` from existing local Founder Loop state and safe
refs so the operator can follow:

Chat handoff -> Plans -> Action Inbox -> decision receipt -> Evidence ->
Memory Review -> Weekly Review.

## What Is Implemented

- `src/ultimate_ai_agent/core/control_center/unified_work_thread.py` defines the
  backend-owned read model, step model, blocked authority refs, and validation.
- `FounderLoopRepository.today_summary()` exposes
  `unified_work_thread_read_model` through the existing Today summary contract.
- `scripts/dev/uaa_founder_loop.py inspect-work-thread` provides repo-local CLI
  inspection over the same backend-owned state and returns `state_not_found_no_write`
  without creating storage when state is absent.
- Control Center renders a Today panel only when the backend provides a valid
  contract-shaped payload. Unsafe flags, missing blocked refs, and mock-only
  fallback fail closed.
- Frontend normalization requires the exact step order, full blocked authority
  refs, denied authority flags set to false, safe summary fields, and safe ref
  arrays.

## Authority Boundary

No runtime dispatch or execution.
No action execution.
No provider/model calls.
No A2A or MCP runtime dispatch.
No browser automation or live web fetching.
No connector reads or writes.
No email/calendar sends.
No CRM writes or account sync.
No shell/subprocess execution.
No background autonomy.
No memory writes or context injection.
No public beta, public release, or production authority.

The read model is inspectability over local state. It does not add a new API
route, scheduler, provider call, connector runtime, browser lane, memory write,
or Control Center authority boundary.

## Inspection

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_founder_loop.py inspect-work-thread
PYTHONPATH=src .venv/bin/python scripts/verify_fcc_thread_001_unified_work_thread.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_fcc_thread_001_unified_work_thread.py
```

## Evidence

- `src/ultimate_ai_agent/core/control_center/unified_work_thread.py`
- `src/ultimate_ai_agent/core/storage/founder_loop.py`
- `scripts/dev/uaa_founder_loop.py`
- `scripts/verify_fcc_thread_001_unified_work_thread.py`
- `tests/test_fcc_thread_001_unified_work_thread.py`
- `apps/control-center/src/components/FounderLoopPanels.tsx`
- `apps/control-center/src/api/client.ts`
- `apps/control-center/src/api/types.ts`
- `apps/control-center/src/App.test.tsx`

## Remaining Blocked Authority

- Message send/write/archive/delete/label/move behavior.
- Email/calendar/account fetch, send, or sync.
- External CRM/task writes.
- Provider/model invocation.
- Browser/live web execution.
- Shell/subprocess execution.
- Autonomous/background execution.
- Memory write, hidden context injection, and automatic recall-as-truth.
- Public beta, public release, distribution, and production authority.

# Browser Action Dry-Run Authority Boundary

M75 browser action dry-run plans are not authority.

They do not authorize:

- no browser action execution.
- no browser session start.
- no browser navigation execution.
- no browser click execution.
- no form fill execution.
- no screenshot.
- no raw DOM.
- no authenticated browser profile.
- no cookies or credentials.
- no download or upload.
- no remote browser.
- no network interception.
- no network call.
- no model call.
- no tool execution.
- no memory write.
- no context injection.
- no backend route.
- no Control Center control.
- no dependency.
- no production authority.

Approval refs are identifiers, not authority. `approval_test_*` refs are never
runtime authority. Context packs, memory refs, tool-intent refs, task-plan refs,
model refs, runtime refs, OpenWebUI refs, and Control Center refs may explain
planning rationale, but they cannot authorize browser actions.

M76 remains future.

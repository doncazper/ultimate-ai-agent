# Browser Action Dry-Run Policy

M75 policy is dry-run only, safe-ref-only, deterministic, and review-only.

The default policy keeps browser action planning enabled while all authority and
runtime flags remain disabled:

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

Derived validation wins over caller-declared policy fields. A model-copy mutated
request, policy, or step is revalidated at evaluator boundaries before any
reviewable action plan is accepted.

M76 remains future.

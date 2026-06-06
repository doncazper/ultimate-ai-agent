# M74 Browser Observe-Only Adapter

M74 implements the Browser Observe-Only Adapter. The adapter accepts an
explicit injected observation from a caller-controlled test or review harness,
redacts visible text before return, and emits safe refs only.

The adapter is observe-only. It does not start a browser, connect to a browser
session, navigate, click, type, fill forms, capture screenshots, read raw DOM,
use authenticated browser profiles, use cookies or credentials, download or
upload, control a remote browser, intercept browser network traffic, call a
model, execute a tool, write memory, inject context, add a backend route, add a
Control Center control, add a dependency, or grant production authority.

M74 allows:

- injected observation records.
- redacted visible text previews.
- redaction summaries.
- safe target refs and safe URL refs.
- stable reason codes.
- deterministic no-authority decisions.
- evaluator boundaries revalidate safety-critical fields.

M74 denies:

- no browser automation.
- no browser navigation.
- no browser click.
- no form fill.
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

Approval refs, `approval_test_` refs, context refs, memory refs, tool-intent
refs, model-output refs, and arbitrary authority refs are identifiers only.
They cannot authorize browser observe or browser automation.

M75 remains future.

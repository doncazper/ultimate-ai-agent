# M74 Browser Observe-Only Policy

The M74 browser observe-only policy allows only an injected observation to be
converted into a redacted visible text preview with safe refs only.

Required policy properties:

- observe-only.
- injected observation required.
- redaction required.
- safe refs only.
- deterministic validation.
- evaluator boundaries revalidate safety-critical fields.

Denied policy properties:

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

The policy is not a runtime browser permission. It does not authorize a browser
session, browser automation, browser network interception, or any external
action.

M75 remains future.

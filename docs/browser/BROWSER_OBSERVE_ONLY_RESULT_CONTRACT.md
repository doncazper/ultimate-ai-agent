# M74 Browser Observe-Only Result Contract

The M74 result contract returns only safe review metadata from an injected
observation.

Allowed result fields:

- safe output ref.
- safe request ref.
- safe target ref.
- safe URL ref.
- safe title.
- redacted visible text preview.
- redaction summary.
- preview truncation metadata.
- stable reason codes.

Denied result fields:

- no browser automation result.
- no browser navigation result.
- no browser click result.
- no form fill result.
- no screenshot.
- no screenshot bytes.
- no raw DOM.
- no raw absolute URL.
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

Redaction happens before the result object is created. Secret-like values must
not appear in the redacted visible text preview, redaction summary, safe
message, receipt plan, or metadata.

M75 remains future.

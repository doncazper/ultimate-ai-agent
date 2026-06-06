# Browser Automation Contract Review Policy

The M73 browser automation contract review policy is contract-only,
review-only, disabled by default, deterministic, and M74-candidate-only.

The policy keeps every browser runtime switch disabled:

- no browser automation.
- no browser observe.
- no browser navigation.
- no browser click.
- no form fill.
- no screenshot.
- no raw DOM.
- no authenticated browser profile.
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

Policy validation denies positive enablement flags and secret-like metadata.
Request validation denies raw DOM, screenshot bytes, browser profile paths,
cookies or credentials, authority refs, approval refs as authority, and
side-effect claims.

Evaluator boundaries revalidate safety-critical fields and do not trust
constructor validation alone.

M74 remains future.

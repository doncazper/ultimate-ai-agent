# UAA Governed Browser Keychain Helper

This purpose-specific macOS helper stores, probes, and deletes one bounded
credential item under an exact origin-scoped opaque handle. Items use the
device-only, non-synchronizing macOS Keychain class and are accessible only
while the device is unlocked.

The helper accepts bounded JSON over standard input and emits safe refs and
posture flags only. Credential material is accepted only by `store`, is never
returned, and never appears in a helper receipt. `probe` requests attributes
only; it does not resolve credential material. `delete` is idempotent.

This helper does not start a browser, authenticate a site, create cookies,
perform network access, submit a form, grant external-action authority, or
enable a real external target. Python Core must validate the exact registered
operation through PolicyEngine, LocalApprovalAuthority, AuthorityLease,
budget, readiness, deadline, safe-disable, and kill-switch gates before use.

Runtime code invokes only an explicitly installed executable after validating
its file posture and pinned SHA-256 fingerprint. Runtime never builds or
downloads this helper. The source and installer are intentionally excluded
from the Python wheel.

Build locally:

```bash
swift build --package-path tools/macos/governed-browser-keychain-helper -c release
```

The built binary is local output and must not be committed.

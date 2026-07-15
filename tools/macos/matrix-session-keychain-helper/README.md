# UAA Matrix Session Keychain Helper

This macOS-only helper currently exposes a version handshake only. Credential
storage, resolution, interactive authentication, rotation, and deletion fail
closed with `MATRIX_KEYCHAIN_CALLER_AUTH_REQUIRED` until an authenticated,
one-use handoff with a non-caller-controlled executable trust root is proven.
It never reads or writes Keychain material in MSG-MX-005.

The helper does not grant connector, network, browser, or message authority.
The helper does not grant connector, credential, network, browser, or message
authority. Python Core must re-evaluate the exact request-scoped policy, approval,
AuthorityLease, target, deadline, budget, readiness, kill switch, safe-disable,
and idempotency posture before invoking it.

Build locally with:

```bash
swift build --package-path tools/macos/matrix-session-keychain-helper -c release
```

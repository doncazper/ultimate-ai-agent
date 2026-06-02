# Device Permission Lifecycle

Status: M20 contract-only lifecycle documentation.

Future device permission lifecycle:

```text
request
review
approve in future authority layer
receipt
use
revoke
expire
audit
```

All lifecycle steps are future planning only in M20. No runtime permission
request is implemented. No OS permission integration is implemented. No mobile,
desktop, browser, or native permission API is called.

Future permission requests must include purpose, capability kind, risk level,
data classification, requested scope, requested capture mode, consent refs,
receipt refs, redaction policy, retention policy, revocation behavior, and a
safe summary.

Background permissions, standing permissions, passive capture, continuous
capture, and silent capture remain blocked unless a future reviewed milestone
explicitly creates a narrower policy.

## v0.24.1 M20 Hardening Note

v0.24.1 treats one-time, session, and foreground scopes as planned metadata
only. They do not imply implemented runtime permission access. User gesture is
future contract metadata only and cannot imply current capture execution.
OS permission runtime, notification push runtime, background service runtime,
background capture, passive capture, and continuous capture remain blocked.
v0.25.0 implements M21 OpenWebUI Bridge + Chat Shell Integration Contract as
contract/planning/validation only. v0.26.0 implements M22 contract-only, and
M23 is implemented/released by v0.27.0 as manual fixed-prompt local call only.
Device capability permission work remains planned/disabled.

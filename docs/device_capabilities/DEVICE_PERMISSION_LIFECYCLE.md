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

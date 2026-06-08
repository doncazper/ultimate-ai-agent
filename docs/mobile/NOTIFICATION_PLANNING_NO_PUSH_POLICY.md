# Notification Planning No Push Policy

M104 notification planning is contract-only and planning-only.

Required properties:

- safe refs are required for device, message summary, purpose, consent,
  revocation, and audit bindings.
- safe message summaries are required instead of raw notification bodies.
- no push execution is required.
- consent, revocation, and audit bindings are required.

Denied properties:

- no push delivery.
- no notification permission prompt.
- no notification scheduling.
- no background task execution.
- no device token handling.
- no external push provider.
- no raw notification body.
- no backend route.
- no Control Center control.
- no dependency.
- no memory write.
- no context injection.
- no execution.
- no production authority.

Approval refs remain identifiers only and cannot authorize notification
delivery, scheduling, background work, context injection, memory writes,
execution, or production authority.

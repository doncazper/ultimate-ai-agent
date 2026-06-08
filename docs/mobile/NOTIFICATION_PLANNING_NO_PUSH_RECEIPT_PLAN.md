# Notification Planning Receipt Plan

M104 receipts are no-effect receipt plans for governed review.

Allowed receipt fields:

- notification_plan_ref.
- actor_ref.
- safe_device_ref.
- safe_message_summary_ref.
- safe_purpose_ref.
- consent_ref.
- revocation_ref.
- audit_ref.
- reason codes.
- safe summary.

Denied receipt fields:

- raw notification body.
- device token.
- provider credential.
- push provider payload.
- permission prompt result.
- delivery status.
- schedule identifier.
- raw prompt or provider payload.

The receipt plan records no push delivery, no notification scheduling, no
background task execution, no memory write, no context injection, no execution,
and no production authority.

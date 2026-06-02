# Mobile API Planning

Status: Current M19 API planning doc for v0.23.0.

M19 adds no backend API route. OpenAPI path count remains `74`.

Future mobile API contracts must be stable OpenAPI contracts and must remain
metadata-first, receipt-backed, redacted, and auditable. Any future mobile API
must preserve Python Agent Core authority and must not expose execution,
approval execution, sensor access, raw capture payloads, raw prompts, raw
files, raw memory, raw credentials, or secret material.

Forbidden in M19:

- `/mobile/sensors`
- `/mobile/capture`
- `/mobile/approvals/execute`
- `/device-capability-broker`
- mobile runtime dispatch routes
- mobile approval approve/deny routes

M20 Device Capability Broker remains planned/provisional and is required before
any future sensor implementation.

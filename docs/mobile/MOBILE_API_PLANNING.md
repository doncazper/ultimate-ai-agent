# Mobile API Planning

Status: Current M19 API planning doc through v0.23.1.

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

## v0.23.1 Hardening Note

v0.23.1 keeps `/mobile`, `/mobile/sensors`, `/mobile/permissions`,
`/mobile/capture`, `/mobile/approvals/execute`, and Device Capability Broker
routes absent. Contacts and calendar are contract-only planning records, not
API-enabled capabilities. Metadata refs must be secret-free. External sends,
OS permission integration, background services, Android/iOS app code, native
build workflows, and sensor APIs remain absent.

## v0.24.0 M20 Device Capability Broker Contract

v0.24.0 implements M20 Device Capability Broker Contract as contract-only
planning and validation. `/device-capabilities`, `/device-capabilities/execute`,
`/device-capability-broker`, `/mobile/sensors`, `/mobile/capture`, and related
device runtime routes remain absent. OpenAPI path count remains `74`. M20 adds
no backend API route, sensor access, OS permission integration, pairing
runtime, native client, dependency, runtime execution, model/provider call,
remote execution, plugin enablement, or production authority.

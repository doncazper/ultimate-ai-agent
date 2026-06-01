# Local Browser Smoke Readiness

Status: Active for v0.17.2 / Web Control Center verification hardening.

This document defines manual local browser smoke readiness for the Web Control Center shell. It is local-only, optional, non-authoritative, and never part of CI or Foundation Gate browser execution.

Allowed targets:

- local frontend dev server on `localhost`, `127.0.0.1`, or `::1`.
- local frontend preview server on `localhost`, `127.0.0.1`, or `::1`.
- local backend API on `localhost`, `127.0.0.1`, or `::1`.
- static build output served by a local preview command.

Required safety boundaries:

- no authenticated browser profile.
- no Chrome authenticated profile control.
- no Computer Use.
- no external sites.
- no production backend.
- no screenshots with secrets.
- no plugin enablement.
- no native/mobile workflow.
- no model, provider, runtime, remote worker, or mobile sensor execution.
- no production Control Center authority.

Manual local browser smoke checklist:

- dashboard loads.
- runtime readiness panel loads.
- Foundation Gate panel loads.
- API route inventory loads.
- action preview form is labeled preview-only.
- no execute button.
- no plugin enable button.
- no mobile sensor button.
- no remote dispatch button.
- mock data marked mock when backend data is unavailable.
- blocked preview results remain non-authoritative and show no action was executed.

The browser smoke procedure may use Browser plus Build Web Apps only when a future release prompt explicitly asks for local UI verification. Chrome authenticated profile control, Computer Use automation, iOS/macOS build plugins, external SaaS browser services, hosted preview services, production deployments, and screenshots containing secrets remain off-limits.

# Local Prototype Browser Smoke Review

Status: Active for v0.45.0 / M41 - Local Prototype Safety Freeze.

Browser smoke review is local-only. It may open localhost Control Center
surfaces to confirm that review-only screens render, mock/non-authoritative
fallbacks are visibly labeled, redacted summaries remain redacted, and unsafe
controls are absent.

Browser smoke review must not become browser automation execution. It must not
use authenticated browser profiles, cookies, credentials, external SaaS,
analytics SDKs, provider dashboards, production data, remote targets, or mobile
sensors. It must not approve, submit, export, inject context, write memory,
start background workers, enable plugins, run tools, call models, or execute
shell/subprocess commands.

The local prototype remains localhost-only. Any browser review target must be a
relative route, `localhost`, `127.0.0.1`, or loopback IPv6. Non-loopback hosts
and arbitrary caller-selected roots remain outside the prototype boundary.

M42 remains future.

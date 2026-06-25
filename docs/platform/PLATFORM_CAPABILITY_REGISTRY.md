# Platform Capability Registry

The Platform Capability Registry is a contract-first metadata and readiness
surface. It answers what platform bucket is detected, what capability families
could eventually exist on that platform, what is currently configured, and what
remains blocked. It may read Python platform values only to reduce them to safe
OS and architecture buckets. It does not install software, authenticate, probe
sensitive OS state, read calendars or credentials, scan the filesystem, start
services, call providers, or grant runtime authority.

The first contract slice lives in
`ultimate_ai_agent.core.platform_capabilities` and exposes typed Pydantic
models plus `detect_platform_identity()` and
`build_platform_capability_snapshot()`. Platform detection uses safe buckets
only and does not emit raw `platform.system()`, `platform.machine()`, or
`platform.release()` values:

- OS: `macos`, `windows`, `linux`, `wsl`, `unknown`
- architecture: `arm64`, `x86_64`, `other`, `unknown`

Capability families are durable nouns rather than adapter authority:

- `secure_credential_store`
- `notification_delivery`
- `startup_item`
- `local_calendar_metadata`
- `email_account_metadata`
- `conversation_source_metadata`
- `local_model_runtime`
- `control_center_shell`
- `installer_channel`

Default records are non-authorizing. Current contract snapshots may describe
`metadata_only`, `readiness_only`, `blocked`, `planned_disabled`,
`unsupported`, or `not_configured` posture, but a capability record cannot grant
runtime, installer, read, write, credential, service, provider, or production
authority.

macOS remains the lead dogfood platform for executable setup work. Windows is
represented as a first-class platform posture at the metadata and readiness
layer, while executable authority remains blocked until scoped milestones add
exact adapters, approvals, receipts, rollback plans, and tests.

CLI inspection is available with:

```bash
PYTHONPATH=src .venv/bin/python scripts/inspect_platform_capabilities.py
```

The inspection output is safe-ref and summary oriented. It must not contain raw
usernames, hostnames, local paths, environment dumps, logs, credentials, serials,
prompts, responses, provider payloads, or provider exchange content.

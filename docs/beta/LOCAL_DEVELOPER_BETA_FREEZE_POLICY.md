# Local Developer Beta Freeze Policy

The M60 policy is freeze-only and local developer beta only.

Required checklist refs:

- beta-freeze:validation-green
- beta-freeze:docs-current
- beta-freeze:route-stable
- beta-freeze:dependency-stable
- beta-freeze:artifact-clean
- beta-freeze:authority-frozen

The policy denies all authority expansion. It has no public release, no
external distribution, no post-M60 autonomy, no production authority, no
execution, no tool execution, no shell execution, no network tool, no browser
automation, no plugin execution, no mobile sensor access, no remote execution,
no credential handling, no memory write, no context injection, no
model/provider call, no backend route, no Control Center control, and no
dependency.

Policy metadata must be safe review metadata only. Secret-like keys, raw
provider payload references, raw prompt references, private user data, and
credential-like content are denied.

M61+ remains future.

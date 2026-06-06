# Public GitHub Readiness Policy

M59 public GitHub readiness is review-only, contract-only, and local-only.

Allowed:

- checklist refs for docs currentness, secret hygiene, artifact hygiene, route
  boundary, and dependency boundary.
- safe repository, baseline, actor, and artifact refs.
- safe summaries and no-effect receipt plans.

Denied:

- no GitHub push
- no GitHub release
- no wiki automation
- no artifact upload
- no external service
- no credential handling
- no network access
- no backend route
- no Control Center control
- no dependency
- no production authority
- no M60 beta freeze implementation

Secret-like metadata keys and values are denied. Public readiness records must
not contain credentials, cookies, tokens, private keys, raw prompts, raw
provider payloads, private user data, or local-only sensitive files.

M60 remains future.

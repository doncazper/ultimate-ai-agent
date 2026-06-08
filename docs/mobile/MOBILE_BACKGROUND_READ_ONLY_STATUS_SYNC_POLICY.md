# Mobile Background Read-Only Status Sync Policy

M106 status sync records are contract-only, read-only, and safe-ref-only.

Status snapshots may reference reviewed M105 background task plan refs, safe
device refs, safe status refs, safe status summaries, safe observed-at refs,
and audit refs. They must not contain raw status payloads, raw mobile data,
device tokens, credentials, push payloads, or background execution evidence.

Policy validation denies background collection, background execution,
background workers, schedulers, daemons, OS background fetch, OS background
permission prompts, push triggers, device token handling, external services,
network sync, raw status payloads, backend routes, Control Center controls,
dependencies, memory writes, context injection, execution, production
authority, and M107 work.

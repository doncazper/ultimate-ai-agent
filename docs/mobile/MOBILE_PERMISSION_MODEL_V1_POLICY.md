# Mobile Permission Model v1 Policy

The M100 policy is contract-only and disabled by default. The policy requires a
permission taxonomy, explicit consent planning, revocation planning, privacy
copy, and permission audit coverage before any future runtime mobile permission
work can be considered.

Policy invariants:

- sensors remain off.
- no background collection.
- no runtime permission prompts.
- no native permission request.
- no production authority.
- no backend route.
- no dependency.
- no memory write.
- no context injection.
- no execution.

The M100 contracts may name permission categories, but naming a permission is
not authority to request, grant, prompt, collect, store, export, or execute.
Every future permission path must remain exact-scope, actor-bound,
resource-bound, revocable, audited, and reviewed before runtime work begins.

M100 implemented/released Mobile Permission Model v1 as planning/contracts only.
Do not start M101 from this policy.

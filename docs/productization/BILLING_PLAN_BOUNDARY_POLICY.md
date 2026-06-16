# M146 Billing/Plan Boundary Policy

The M146 policy is contract-only, review-only, deterministic, local-only,
safe-ref-only, billing-boundary-only, disabled by default, route-free, and
no-effect.

Allowed evidence is limited to billing boundary refs, plan boundary refs,
entitlement boundary refs, pricing disclosure refs, payment provider boundary
refs, upgrade downgrade policy refs, support refund policy refs, audit refs,
replay refs, revocation refs, kill-switch refs, and no-effect receipt refs.

The policy denies payment processing, checkout runtime, subscription
management, plan enforcement, billing runtime, external billing provider,
account plan runtime, entitlement runtime, pricing runtime, auth runtime, login,
credential handling, connector runtime, plugin marketplace runtime, execution,
backend routes, Control Center controls, dependencies, beta release, and
production authority.

# M146 Authority Boundary

M146 is billing/plan boundary policy authority only. It can validate safe refs
and record a no-effect billing boundary record for review.

M146 must not start payment processing, start checkout runtime, enforce plans,
manage subscriptions, implement billing runtime, start an external billing
provider, start account plan runtime, start entitlement runtime, start pricing
runtime, start auth runtime, perform login, handle credentials, start connector
runtime, start plugin marketplace runtime, execute actions, add backend routes,
add Control Center controls, add dependencies, start beta release, or grant
production authority.

Billing and plan refs remain policy refs only. They do not grant plan
enforcement, account runtime, entitlement runtime, payment provider authority,
or production authority.

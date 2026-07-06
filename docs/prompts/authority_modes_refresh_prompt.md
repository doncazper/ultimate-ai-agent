# Authority Modes Refresh Prompt

Use this prompt to refresh a new thread on the UAA authority-mode strategy
captured from the side conversation.

```text
We need to continue the UAA authority-system redesign.

Important context:
- The side conversation was preserved in:
  docs/strategy/UAA_AUTHORITY_MODES_AND_MISSION_LEASES.md
- Start by reading that file.
- Treat it as the durable capture of the product/architecture direction, not
  as runtime authority by itself.

Core idea:
UAA should move from tiny narrow authority lanes and permanent blocked posture
to operator-selected trust modes plus domain grants plus session/mission
AuthorityLeases.

The target product is governed autonomy:
- receipts;
- audit trails;
- rollback/safe-disable where possible;
- operator-visible kill switch;
- redaction;
- explicit hard limits;
- but real action when the operator grants authority.

Operator modes to preserve:
- Read-only
- Ask before changes
- Approved safe local work
- Full local workspace access
- Full machine access
- Delegated mission / autonomous window

Authority domains to preserve:
- workspace
- files
- shell
- apps
- browser
- system_settings
- calendar
- messages
- email
- contacts
- home_assistant
- shopping_payments
- provider_model_calls
- memory
- cloud_production

Key rule:
Unknown authority is denied. Known authority inside an active lease is allowed.

Policy decisions should become:
- allow
- ask
- deny
- degrade_to_draft

Desired future mission example:
"There is a ticket sale happening on this website. Wait for it to go live and
buy two tickets up to $1000 total including fees."

UAA should eventually be able to do that using browser/app/payment authority
inside a delegated mission lease, while asking or denying if price, item,
merchant, payment method, account change, or target scope deviates.

Files likely needing canon/code updates are listed in:
docs/strategy/UAA_AUTHORITY_MODES_AND_MISSION_LEASES.md

Please inspect the current repo state first. Then propose or implement the next
smallest coherent canon/code step toward AuthorityLease V1. Do not treat the
old tiny-lane system as the final product shape. Preserve safety, receipts,
audit, redaction, and operator visibility, but make the system capable of
operator-granted autonomy.
```

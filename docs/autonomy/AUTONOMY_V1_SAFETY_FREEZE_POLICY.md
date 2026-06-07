# Autonomy v1 Safety Freeze Policy

Autonomy v1 Safety Freeze is a freeze-only and review-only policy milestone.
It confirms the M61-M98 autonomy contracts remain measurable, scoped,
reversible, inspectable, and boring.

The policy keeps all expansion switches denied: no broad unsandboxed autonomy,
no global autonomy switch, no production authority, no shell execution, no
browser action, no network mutation, no plugin execution, no scheduler, no
background worker, no mobile sensor, no memory write, no context injection, no
raw prompt exposure, no raw file export, no full-file read, no backend route,
and no dependency.

M99 is hardening only. It does not authorize execution, recurring runtime,
external plugin behavior, authenticated network/account actions, mobile
permission prompts, or production authority.

M100 remains future.

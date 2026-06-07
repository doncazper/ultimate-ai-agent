# M99 to M100 Boundary

M99 implements Autonomy v1 Safety Freeze as freeze-only and review-only
hardening over M61-M98.

M99 does not implement M100 Mobile Permission Model v1. M100 remains future and
will define mobile permission taxonomy, consent, revocation, privacy copy, and
permission audit documentation without turning on mobile sensors or background
collection.

The boundary requires no broad unsandboxed autonomy, no global autonomy switch,
no production authority, no shell execution, no browser action, no network
mutation, no plugin execution, no scheduler, no background worker, no mobile
sensor, no memory write, no context injection, no raw prompt exposure, no raw
file export, no full-file read, no backend route, and no dependency.

Evaluator boundaries revalidate safety-critical fields before M99 reports are
valid for review.

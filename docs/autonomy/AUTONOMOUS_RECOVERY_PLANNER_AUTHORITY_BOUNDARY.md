# Autonomous Recovery Planner Authority Boundary

M135 creates no runtime recovery authority. It may validate declared safe refs
and produce a no-effect recovery planning decision for review.

Allowed scope:

- safe recovery summary refs
- exact scope refs
- Mode 5 refs
- M134 human checkpoint scheduling decision refs
- M133 supervisor decision refs
- M132 trusted workflow decision refs
- failure signal refs
- recovery trigger refs
- recovery strategy refs
- recovery step refs
- rollback plan refs
- resume plan refs
- checkpoint refs
- human checkpoint refs
- audit, replay, revocation, kill-switch, and no-effect receipt refs

Denied scope: no recovery execution, no retry execution, no resume execution,
no rollback execution, no supervisor runtime, no checkpoint scheduler, no human
checkpoint scheduler, no prompt, no notification delivery, no scheduler, no
background worker, no autonomous actions, no execution, no tool execution, no
shell execution, no network access, no browser automation, no plugin execution,
no connector runtime, no account auth, no model call, no memory write, no
context injection, no backend route, no Control Center control, no dependency,
no beta release, and no production authority.

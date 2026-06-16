# Autonomy Mode 4 Scoped Work Session Authority Boundary

M131 is a local contract boundary for Mode 4 scoped work sessions. It may
validate safe refs, safe summaries, explicit approval bundle refs, policy
decision refs, risk decision refs, audit refs, replay refs, revocation refs,
kill-switch refs, and no-effect receipt plan refs.

M131 must not:

- start a session
- activate a scoped autonomy window
- authorize or perform autonomous actions
- execute tools, shell, commands, subprocesses, network calls, browser actions,
  plugin actions, connector runtime actions, mobile sensor actions, or remote
  work
- read or store raw prompts, raw provider payloads, secrets, credentials,
  cookies, raw connector content, or raw files
- run background workers or schedulers
- write memory or inject context
- add backend routes, Control Center controls, dependencies, beta release, or
  production authority
- implement M132 or trusted recurring workflow authority

All M131 outputs are safe-ref-only, review-only, and no-effect.

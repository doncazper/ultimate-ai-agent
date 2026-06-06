# Command Proposal Receipt Plan

M82 command proposal receipt plans are safe summary only.

Receipt plans may store:

- proposal refs
- command refs
- safe purpose summaries
- safe command labels
- reason codes
- review-only status

Receipt plans must store no raw command, no shell string, no raw prompt, no raw
provider payload, no secret-like metadata, no raw absolute path, and no side
effects.

Receipt plans grant no command execution, no subprocess execution, no shell
execution, no process spawn, no filesystem mutation, no network access, no tool
execution, no browser automation, no plugin execution, no remote execution, no
model call, no memory write, no context injection, no background worker, no
backend route, no Control Center control, no dependency, and no production
authority.

Evaluator boundaries revalidate receipt fields before accepting them for
review.

M83 remains future.

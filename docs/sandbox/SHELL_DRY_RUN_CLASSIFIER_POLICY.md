# Shell Dry-Run Classifier Policy

M83 policy is classifier-only, review-only, deterministic, and local-only. It
accepts an M82 command proposal for review classification only.

Policy requirements:

- M82 command proposal input must already validate.
- prior milestone refs must include M57, M58, M80, M81, and M82.
- classification is safe metadata, not authority.
- safe summary only receipts are required.
- evaluator boundaries revalidate safety-critical fields.

Policy denials:

- no dry-run execution
- no shell string
- no command execution
- no subprocess execution
- no shell execution
- no process spawn
- no filesystem mutation
- no network access
- no tool execution
- no browser automation
- no plugin execution
- no remote execution
- no model call
- no memory write
- no context injection
- no background worker
- no backend route
- no Control Center control
- no dependency
- no production authority

M84 remains future.

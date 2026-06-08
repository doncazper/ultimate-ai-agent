# User/Workspace Identity Model

Status: Checkpoint M112. Contract-only and review-only.

Checkpoint M112 User/Workspace Identity Model records safe user/workspace
identity model refs over the Checkpoint M111 Production Threat Model. It uses
safe refs, user refs, workspace refs, identity boundary refs, audit refs,
replay refs, and a no-effect receipt plan.

M112 is actor-bound, baseline-bound, source-threat-model-bound, audit-bound,
and replay-safe. It verifies that M101-M111 checkpoint refs are accepted before
recording the user/workspace identity model contract.

M112 requires safe refs only. User refs and workspace refs are identifiers for
review and planning; they are not authority, account access, login capability,
workspace root selection, persistent identity storage, or production runtime.

M112 does not consume a product SemVer version. The current product baseline
remains v1.7.2, M112 is tagged as a checkpoint, and M150 remains the
v1.0.0-alpha target. Beta begins later after the alpha UI and supporting
safety/product work are reviewed and promoted.

M112 adds no production authority, no production runtime, no auth runtime, no
login, no session cookie, no credential handling, no persistent identity store,
no account connector, no network access, no model call, no memory write, no
context injection, no execution, no tool execution, no shell execution, no
browser automation, no plugin execution, no mobile sensor, no background
worker, no remote execution, no backend route, no Control Center control, and
no dependency.

M112 explicitly preserves no context injection, no browser automation, and no background worker authority.

M113 remains future.

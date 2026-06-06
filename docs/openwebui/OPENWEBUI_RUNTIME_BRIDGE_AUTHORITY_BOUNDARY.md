# OpenWebUI Runtime Bridge Authority Boundary

M76 does not make OpenWebUI authority. Python Agent Core remains authority.
OpenWebUI is a shell/bridge, not the brain.

The review-only bridge envelope is not execution authority, not model
authority, not memory authority, not context injection authority, not approval
authority, and not production authority. Model output, runtime output,
OpenWebUI output, memory refs, context refs, tool-intent refs, task-plan refs,
and approval refs cannot authorize OpenWebUI runtime behavior.

M76 denies no live OpenWebUI connection, no OpenWebUI runtime call, no provider
call, no model call, no model authority, no tool execution, no memory write, no
context injection, no network call, no credentials or cookies, no raw prompt, no
raw provider payload, no raw content, no backend route, no Control Center
control, no dependency, and no production authority.

approval_test_* is never runtime authority. Evaluator boundaries revalidate
safety-critical fields before a bridge envelope is valid for review.

M77 remains future.

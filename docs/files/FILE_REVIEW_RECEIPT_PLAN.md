# File Review Receipt Plan

Status: active M35 contract documentation.
Current through: **v0.39.1**.

`FileReviewReceiptPlan` records only safe refs for review evidence. It is not a
receipt store and it is not authority.

Receipt plans may include:

- receipt plan ref
- review packet ref
- preview result ref
- redaction summary ref
- approval ref when an exact approval object was evaluated
- safe file/path binding evidence as refs only when needed for review
- safe summary
- metadata refs

Receipt plans must store no raw content, full file content, unredacted preview,
raw absolute path, secrets, private paths, prompt payloads, provider payloads,
or file bytes. Receipt plans perform no context injection, memory writes,
export, execution, file mutation, network call, model call, or backend route
mutation.

M36 remains planned/provisional. M37 remains planned/provisional. M38 remains
planned/provisional.

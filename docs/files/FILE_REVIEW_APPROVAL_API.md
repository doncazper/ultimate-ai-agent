# File Review Approval API

Status: active M37 API documentation.
Release: v0.41.0 / M37 - Review Approval Capture, Review-Only Persistence.

M37 adds exactly one backend route:

```text
POST /files/review/approvals/capture
```

This route captures a safe review-only approval or denial record for a redacted
file review packet. It accepts only typed safe refs and safe metadata. It
returns a redacted decision envelope with `execution_authorized=False` and
`execution_performed=False`.

The route does not read raw files, return raw file content, return full-file
content, expose raw absolute paths, export files, propose context, inject
context, write memory, execute tools, or perform file mutation outside the
review approval store.

No other file-review backend mutation route is added in M37. M38 remains
planned/provisional.

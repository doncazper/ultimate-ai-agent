# Mobile Permission Model v1 Audit

M100 defines a permission audit plan for the mobile permission taxonomy,
consent model, revocation model, and privacy copy.

The audit plan requires redacted receipts and safe summaries only. It stores no
raw mobile sensor payload, no raw prompt/provider payload, no credentials, no
cookies, and no production data.

Audit invariants:

- permission refs are safe refs.
- redacted receipt is required.
- no raw payload.
- no mobile sensor payload.
- no background collection.
- no production authority.
- no runtime permission prompts.
- no native permission request.
- no backend route.
- no dependency.

M100 implemented/released permission audit contracts only. Do not start M101
from the audit plan.

# Redacted Observability Export Policy

M55 Redacted Observability Export is redacted-only and contract-only. It may
prepare safe local export bundles for review, but it must not perform external
delivery.

Required policy:

- redacted-only data.
- contract-only export planning.
- safe refs and summaries only.
- no external SaaS.
- no network delivery.
- no raw prompts.
- no raw provider payloads.
- no raw private content.
- no secrets.
- no forensic trace export.
- no model call.
- no memory write.
- no context injection.
- no backend route.
- no Control Center control.
- no dependency.
- no production authority.

Any model_copy-mutated request or policy that enables these blocked capabilities
must be revalidated and denied at evaluator boundaries.

M56 remains future.

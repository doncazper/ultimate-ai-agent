# M166 Production Authority Gate

M166 is the first local model production-readiness lane checkpoint that can
record production authority granted after reviewed live evidence is supplied.

The grant is exact-scope-bound to the M160-M165 local llama.cpp model layer and
requires reviewed live evidence for live install/run tests, OpenWebUI E2E
tests, security review, packaging, operational rollback, and load tests.
Generated fixture evidence may validate contract shape, but it must not grant
production authority.

The release gate is revocable, replay-safe, audit-bound, rollback-bound,
localhost-only, safe-ref-only, and redacted summary only. It rejects failed
evidence, missing evidence, blocker refs, raw prompts, raw responses, raw
provider payloads, credentials, raw paths, raw logs, environment dumps,
non-loopback network use, OpenWebUI agent-brain authority, tools/functions,
streaming, backend route additions, Control Center control additions, and
unreviewed dependencies.

When all required evidence is green and explicitly reviewed, the gate records
production authority granted, production runtime authorized, go-live
authorized, production deployment authorized, and traffic routing authorized
for the local model layer only.

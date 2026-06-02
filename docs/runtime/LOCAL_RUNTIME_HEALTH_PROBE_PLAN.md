# Local Runtime Health Probe Plan

Status: Active M22 contract documentation for v0.26.0. Contract-only.

M22 defines a future health probe plan contract without performing a health probe.

The plan records that:

- probe allowed now is false.
- probe performed is false.
- network call performed is false.
- command executed is false.
- user content sent is false.
- no model was called.
- no runtime was activated.
- no endpoint was contacted.

The health probe plan is not readiness evidence. It does not inspect local runtimes, execute commands, call endpoints, parse runtime output, read user prompts, or load model metadata from a live service.

M23 is implemented/released by v0.27.0 as a separate manual fixed-prompt local
call path and does not authorize health probes.

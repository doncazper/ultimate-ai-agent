# Foundation Gate Implementation Plan v1.2.0-alpha

v1.2.0-alpha adds Foundation Gate coverage for the contract-only Orchestration
Efficiency Layer and aligns the M150 alpha target baseline.

Gate coverage:
- Orchestration efficiency contracts exist as strict safe-ref-only Pydantic
  models with secret-like metadata rejection.
- Hard model-routing filters remain ahead of latency, cost, cache, and quality
  scoring.
- Preview decisions expose redacted ledger/observability summaries only and do
  not include raw prompts, raw private content, provider payloads, forensic
  traces, or secrets.
- Cacheability plans store only safe refs, hashes, predicted token metadata,
  and invalidation reason codes.
- Unknown paid cost remains approval-required, critical mode requires verifier
  planning, and premium/critical selection requires explicit reason codes.
- Static safety checks deny provider SDK imports, network clients, browser
  automation, subprocess/shell imports, backend route additions, dependency
  additions, memory writes, context injection, external observability export,
  production authority, and live model execution in this layer.

Historical note: at the M150/v1.2.0-alpha acceptance point, M151 remained
future. Later reviewed post-M150 checkpoints accepted M151-M167; current
Operator Runtime Excellence work starts at M168 and does not change this
Foundation Gate plan's v1.2.0-alpha scope.

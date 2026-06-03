# Evidence Claim Checker

Status: Active for v0.29.1 / M25.

The Evidence Claim Checker validates a claim against a provided evidence chain.
It does not discover evidence, crawl files, read arbitrary files, call tools,
call LLMs, call providers, perform web search, perform external verification,
or write memory.

Inputs must be structured refs, safe summaries, redaction status, source kind,
evidence strength, and optional event/receipt/memory refs. Outputs are
validation decisions only. A verification decision is not action approval and
cannot execute actions.

Unknown and arbitrary refs are denied. Explicit `TruthSourceKind.unknown`
evidence cannot produce `evidence_supported` or `verified_by_primary_source`.
Claims cannot self-verify.

Raw prompts, raw model outputs, raw files, raw transcripts, secrets,
credentials, private keys, and unredacted sensitive content are forbidden.

# Sandboxed Echo/No-Op Command Receipt Plan

M84 receipts store safe summary only metadata for the sandboxed echo/no-op
command. Receipts may include safe refs, stable reason codes, safe echo text,
and no-effect status.

Receipts must not store raw command, shell string, raw output, raw prompt,
provider payload, secret-like content, filesystem content, network content, tool
output, browser output, model output, memory writes, context injection payloads,
or production authority claims.

Evaluator boundaries revalidate receipt fields so model_copy-mutated raw command,
raw output, shell execution, subprocess execution, process spawn, side effect,
or production authority flags are denied. M85 remains future.

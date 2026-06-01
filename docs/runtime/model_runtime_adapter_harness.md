# Model Runtime Adapter Harness

M8 introduces a simulated model runtime adapter harness.

The harness is allowed to:

- validate runtime adapter manifests
- validate runtime requests and responses
- convert selected model route decisions into simulated runtime requests
- produce deterministic simulated responses
- emit event-compatible metadata

The harness is not allowed to:

- call real models
- import provider SDKs
- call OpenAI-compatible endpoints
- call local runtimes
- tokenize through external libraries or runtime APIs
- call billing APIs
- make network calls
- resolve raw secrets
- persist production runtime data

Future real runtime adapters require a separate milestone, explicit approval authority, secret policy, provider policy, and Foundation Gate criteria.

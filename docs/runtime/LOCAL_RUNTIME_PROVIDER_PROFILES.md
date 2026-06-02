# Local Runtime Provider Profiles

Status: Active M22 contract documentation for v0.26.0. Contract-only.

M22 provider profiles are metadata-only descriptors for future local runtime families:

- Ollama planned profile.
- llama.cpp planned profile.
- MLX planned profile.
- vLLM planned profile.
- LM Studio planned profile.
- OpenAI-compatible local planned profile.
- generic loopback HTTP planned profile.

Every profile is `planned_disabled`. Every profile keeps activation, real model calls, user content, tool calls, memory writes, provider credentials, remote hosts, endpoint probes, runtime package imports, and dependency additions disabled.

No model was called. No runtime was activated. No endpoint was contacted.

Provider profiles are not authority. They do not select models, load weights,
inspect local processes, import runtime packages, call local services, read
secrets, or prove readiness. M23 is implemented/released by v0.27.0 as a
separate manual fixed-prompt local call path and does not authorize runtime
activation.

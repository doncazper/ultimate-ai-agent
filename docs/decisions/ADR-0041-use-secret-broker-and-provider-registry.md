# ADR-0041: Use Secret Broker and Provider Registry

Status: Accepted for foundation v0.5.3

## Context

Weather, news, Reddit, email, and message modules need provider access. Some providers are free/no-key; others require API keys or OAuth. Secrets cannot enter chat, memory, prompts, logs, or source control.

## Decision

Introduce a Secret Broker, credential references, Provider Registry, provider manifests, and normalized provider envelopes before implementing provider-specific integrations.

## Consequences

- Free/no-key providers can be preferred by policy.
- API keys are supported without exposing raw secrets to the LLM.
- Consent and credentials remain separate.
- Provider outputs can be normalized across weather, news, and future modules.

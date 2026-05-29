# 40 — Credentials, Secret Broker, and Provider Registry

Status: Layer-0/1 foundation spec, v0.5.3
Owner: Trust / Integrations

## Core principle

Free/no-key providers first. API keys only when needed. Secrets never enter chat, prompts, memory, logs, canonical files, source control, or user-visible receipts. Provider outputs are normalized before agent use.

## Credential handling

Local development:

```text
.env.example: committed placeholders only
.env.local: ignored real local secrets
environment variables: preferred runtime input
OS keychain: preferred local desktop store later
```

Production/hosted:

```text
User Control Center → Connected Providers → Secret Broker → encrypted secret store/vault
```

## Secret Broker

The Secret Broker is the only component that can resolve a credential reference into a usable secret handle.

```text
Agent / Scanner / Tool
→ Tool Broker
→ Provider Adapter
→ Secret Broker
→ Credential Store
```

The LLM receives credential refs only, never raw values.

## Provider Registry

Every provider must declare:

```text
provider_id
domain
auth_type
cost_class
capabilities
rate_limits
terms/attribution metadata
normalizer
fallback priority
credential requirements
```

## Free-first resolver

Provider selection order:

```text
1. Free no-key provider
2. Free provider requiring key
3. User-connected provider
4. Paid provider within budget
5. Enterprise/self-hosted provider
```

The resolver also considers accuracy, freshness, rate limits, terms, coverage, privacy, and user preference.

## Normalized envelopes

Provider adapters return `provider_result_envelope` with:

```text
provider_id
domain
capability
fetched_at
normalized payload
raw_ref if retained
confidence
freshness_seconds
cost attribution
terms/attribution metadata
warnings
```

## Credential vs consent

Credential availability does not equal permission. Every provider call checks:

```text
credential available?
consent allows this use?
Tool Broker allows this action?
Cost Governor allows this spend?
Event Ledger records the call?
```

## Foundation blocking rule

Do not build provider-specific integrations, scanners, email/message modules, or paid API calls before Secret Broker, Provider Registry, credential references, provider envelopes, consent checks, event redaction, and fallback tests exist.

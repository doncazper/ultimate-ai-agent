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
environment variables: local operator-managed input only, never dumped by UAA
OS keychain or vault adapter: future scoped backend only
```

Production/hosted:

```text
User Control Center → credential refs → Secret Broker → future reviewed vault adapter
```

## Secret Broker

The Secret Broker is the only component that can resolve a credential reference
into a usable secret handle. The current provider credential productionization
layer adds a blocked vault adapter boundary and disabled readiness contracts
only. It does not collect credential material, read environment values, call a
vault/keychain backend, validate provider auth references, or invoke providers.

```text
Agent / Scanner / Tool
→ Tool Broker
→ Provider Adapter
→ Secret Broker
→ Credential Store
```

The LLM receives provider auth references only, never raw values.

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

Credential availability does not equal permission. Before any future provider
call is scoped, it must check:

```text
credential available?
consent allows this use?
Tool Broker allows this action?
Cost Governor allows this spend?
Event Ledger records the call?
```

Current readiness records also require consent refs, policy refs, approval refs,
revocation refs, audit refs, receipt refs, rollback or safe-disable refs, and
rate or budget boundary refs. Validation and invocation remain blocked until a
separate reviewed milestone grants exact network/provider authority.

## Foundation blocking rule

Do not build provider-specific integrations, scanners, email/message modules, or paid API calls before Secret Broker, Provider Registry, credential references, provider envelopes, consent checks, event redaction, and fallback tests exist.

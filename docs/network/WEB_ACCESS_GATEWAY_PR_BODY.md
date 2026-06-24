# PR: M72.5 WebAccessGateway Boundary

## Summary

This PR adds the first safe boundary for hybrid web access in Ultimate AI Agent.

It creates a central `ultimate_ai_agent.core.web_access` package with contracts, deny-by-default policy, normalized audit records, source metadata, static guardrails, and documentation. It intentionally does not add new providers or enable browser execution.

## Why

UAA already has strong pieces for governed web evidence, read-only fetch, browser observe, browser dry-run, low-risk click, and capability policy. The missing piece is a single gateway boundary. Without one, future agents/tools could route around intended policy and audit controls.

## Core decision

Agent-facing public web access must go through:

```python
ultimate_ai_agent.core.web_access
```

Provider integrations and browser/search/scrape runtimes must live behind gateway adapters.

## Files added or changed

```text
AGENTS.md
src/ultimate_ai_agent/core/web_access/__init__.py
src/ultimate_ai_agent/core/web_access/contracts.py
src/ultimate_ai_agent/core/web_access/policy.py
src/ultimate_ai_agent/core/web_access/audit.py
src/ultimate_ai_agent/core/web_access/gateway.py
src/ultimate_ai_agent/core/web_access/adapters.py
src/ultimate_ai_agent/core/web_access/source_registry.py
docs/network/WEB_ACCESS_GATEWAY.md
docs/network/WEB_ACCESS_GATEWAY_PR_BODY.md
docs/network/WEB_ACCESS_GATEWAY_PR_SEQUENCE.md
docs/network/WEB_ACCESS_GATEWAY_DEFINITION_OF_DONE.md
docs/network/WEB_ACCESS_GATEWAY_CODEX_PROMPTS.md
docs/network/WEB_ACCESS_GATEWAY_SECURITY_REVIEW_CHECKLIST.md
prompts/CODEX_REVIEW_AND_INGEST_WEB_ACCESS_GATEWAY_PR.md
tests/test_web_access_gateway.py
tests/test_web_access_static_guards.py
```

## Allowed scope

```text
- WebAccessGateway central boundary
- WebAccess contracts/types
- deny-by-default policy
- governed web evidence wrapper
- normalized WebAccessAuditRecord
- SourceMetadata with content_untrusted=true
- explicit network lanes
- static guard tests against new direct public-web/browser imports
- documented temporary exceptions for existing local-model/model-acquisition/legacy modules
- docs, PR sequence, review checklist, Codex prompts, AGENTS.md guidance
```

## Forbidden scope

```text
- Firecrawl
- Browserbase
- new search/scrape providers
- new Playwright execution
- browser observe runtime expansion
- browser action execution
- M94 low-risk click activation
- form filling
- auth/cookies
- downloads/uploads
- POST/PUT/PATCH/DELETE
- global autonomy toggle
- broad refactor of local model management direct HTTP paths
```

## Test plan

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_web_access_gateway.py tests/test_web_access_static_guards.py
```

Recommended additional checks:

```bash
make doctor
make test
make verify
.venv/bin/python scripts/verify_documentation_integrity.py
```

## Review focus

Reviewers should check:

```text
- Can anything route around the gateway?
- Are temporary exceptions too broad?
- Did browser execution sneak in?
- Are all results audited?
- Is web content untrusted?
- Are static guards enforceable?
- Does AGENTS.md preserve the boundary without granting runtime web authority?
```

## Follow-up sequence

1. API/manifest wording integration.
2. Tool runtime HTTP fetch migration behind gateway.
3. Browser observe behind gateway.
4. Browser dry-run behind gateway.
5. Scoped execution only after approval/audit/revocation/sandboxing exist.

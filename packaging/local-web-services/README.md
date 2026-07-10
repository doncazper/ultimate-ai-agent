# Local Web Services

Status: WEB-HYBRID-002 loopback-only provider packaging

This package reproduces the reviewed local SearXNG and self-hosted Firecrawl
service topology. It does not grant UAA runtime authority. Runtime adapters,
request-scoped policy evaluation, approvals, leases, and receipts arrive in
later accepted WEB-HYBRID phases.

## Safety boundary

- Only SearXNG and Firecrawl API ports are published, both on `127.0.0.1`.
- Valkey, Redis, RabbitMQ, PostgreSQL, and Playwright publish no host ports.
  Playwright has a dedicated outbound network for public-page rendering; its
  API remains reachable only to the Firecrawl stack. No queue administration
  UI is enabled.
- Firecrawl receives its PostgreSQL and Bull/admin values from Compose secret
  files generated under ignored `.uaa/` local state.
- SearXNG receives a generated secret through an ignored generated settings
  file. JSON output is enabled; page count and upstream timeouts are bounded.
- Proxy credentials, webhooks, cloud/model keys, persistent browser profiles,
  authenticated browsing, and interactive browser actions are absent.
- The pinned Playwright service runs its internal SSRF proxy with
  `ALLOW_LOCAL_WEBHOOKS=false`, revalidates navigation/subresource hosts, and
  blocks private/link-local targets. The smoke gate proves the metadata-service
  literal is denied; a formal adversarial DNS-rebinding/network-firewall proof
  remains future hardening.
- The cloud Firecrawl credential is neither mounted nor resolved by this stack.

## Setup and lifecycle

From the repository root:

```bash
.venv/bin/python packaging/local-web-services/scripts/setup_local_state.py
.venv/bin/python packaging/local-web-services/scripts/verify_config.py
docker compose -f packaging/local-web-services/compose.yaml pull
docker compose -f packaging/local-web-services/compose.yaml up -d --wait
.venv/bin/python packaging/local-web-services/scripts/inspect_health.py
.venv/bin/python packaging/local-web-services/scripts/smoke.py
docker compose -f packaging/local-web-services/compose.yaml restart
docker compose -f packaging/local-web-services/compose.yaml up -d --wait
docker compose -f packaging/local-web-services/compose.yaml down
```

The smoke command checks bounded liveness plus the pinned Playwright service's
private/link-local target denial. It does not search public sources, scrape a
public page, spend cloud credits, retain provider responses, or grant authority.

## Backup, upgrade, and rollback

The PostgreSQL state uses a named local Docker volume; transient queues and
caches remain disposable. Before an upgrade, stop the stack and inspect the
proposed upstream release, Compose topology, licenses, multi-architecture image
digests, configuration schema, and capability matrix. Make a separate encrypted
operator-controlled database backup before any volume migration and rehearse
its restore; this package does not claim such a backup exists.

Rollback is exact: run `docker compose down`, restore the prior reviewed
`provider_lock.json` and matching Compose/config files from version control,
then pull and start those pins. `down` preserves named volumes by default; use
`down --volumes` only as an explicit destructive cleanup after operator review.

## Provenance and licenses

`provider_lock.json` is the machine-readable pin and capability boundary. The
Firecrawl source release `v2.9.0` is pinned to its verified commit, while the
official multi-architecture container images are separately pinned by digest.
The API image exposes no release label, so the lock records that provenance
limitation instead of claiming stronger linkage. SearXNG embeds its reviewed
version/revision labels and is pinned by multi-architecture digest.

Firecrawl and SearXNG are AGPL-licensed upstream works. Redis, RabbitMQ, Valkey,
PostgreSQL, and all image/base dependencies retain their respective upstream
licenses. Review source-offer and distribution obligations before distributing
images or modified network services. This local package is not a public
distribution claim.

# ADR-0069: Inbox Owns Encrypted Source Artifacts And Reviewed Proposals

- Status: Accepted for bounded ECO-007 local repository
- Date: 2026-08-21

## Context

The coherent ecosystem needs a source workbench before live connectors are
allowed. Source material may contain private communication content, but Today,
Evidence, Tasks, Calendar, CRM, and Boards must not copy that content or mistake
an untrusted artifact for execution authority. Existing Founder Loop Inbox
surfaces remain compatibility product read models and cannot be silently
replaced.

## Decision

Store manual and synthetic source bindings, artifacts, and threads in the
encrypted ECO-001 data plane under canonical Inbox ownership. Add one exact
repository-only `ecosystem.inbox.apply` authority lane for four Inbox record
kinds. Bind every mutation to exact approval resources and encrypted
idempotent receipts. Keep import plans, safe summaries, result refs, and durable
evidence content-free.

Require one workspace, binding, privacy scope, retention posture, and source
mode on each artifact. Permit only same-workspace entity links and threads made
from existing artifacts on the same binding. Use keyed blind-index terms for
search and exclude archived records. Preserve expiry and retention-candidate
inspection without implementing deletion policy or a background worker.

Represent downstream action only as a reviewed source proposal. A proposal can
name its intended canonical owner and become an ECO-006 Today candidate after
human review, but it never mutates that owner. Keep mutation, target-write, raw
content, and model-authority flags permanently false. Defer cross-app execution
to ECO-008 ChangeSets and separately accepted authority.

Add no connector, account, OAuth, file-read, route, CLI, UI, external write,
send, web/browser, provider/model, subprocess, notification, scheduler, or
background runtime in this decision.

## Consequences

Manual and synthetic source material can be triaged, linked, searched,
retained, and converted into inspectable proposals without creating a second
copy of downstream canonical truth. Workspace and binding validation prevent
cross-context leakage, and generic local-data callers cannot bypass Inbox
domain rules.

Live source acquisition, file import UX, connector reads, product-surface
integration, approved ChangeSet execution, production key/path backends,
public release, and production authority remain separate decisions with their
own acceptance evidence.

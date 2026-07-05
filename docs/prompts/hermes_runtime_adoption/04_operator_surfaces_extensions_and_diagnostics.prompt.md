# Phases 28-36: Operator Surfaces, Extensions, And Diagnostics

These phases make UAA feel like a real operator cockpit while keeping extension
and runtime power behind explicit policy.

## Shared Acceptance For Phases 28-36

- Operator controls must be backed by Python core or API contracts.
- Diagnostics must not expose secrets, paths, raw logs, or provider payloads.
- Extension and MCP surfaces remain metadata/read-only until exact activation
  grants exist.
- UI must distinguish implemented, partial, planned, blocked, mock-only, and
  unavailable states.

## Phase 28: Doctor / Setup Diagnostics

Branch: `codex/hermes-adoption-28-doctor-diagnostics`
Commit: `Add runtime doctor diagnostics posture`

Full-strength: one UAA diagnostic command explains setup, runtime readiness,
providers, tools, secrets, services, authority, and next safe actions.

Repo-safe: add CLI/API read model and Control Center diagnostics panel using
redacted status only.

Blocked / needs authority: installs, service starts, credential writes, and
runtime config mutation.

Exact promotion path: setup action proposals, approval envelope, receipt,
rollback/safe-disable, and proof.

## Phase 29: Gateway / Multi-Surface Session Continuity

Branch: `codex/hermes-adoption-29-session-continuity`
Commit: `Add multi surface session continuity posture`

Full-strength: UAA sessions can be visible across desktop, CLI, future mobile,
and delegated runtimes.

Repo-safe: add session continuity refs, source labels, and conflict/staleness
states.

Blocked / needs authority: external messaging gateway, account sync, connector
writes, and remote sessions.

Exact promotion path: channel identity, authorization, redaction, delivery
receipt, revoke, and audit.

## Phase 30: MCP Catalog With Filtering

Branch: `codex/hermes-adoption-30-mcp-catalog-filtering`
Commit: `Add MCP catalog filtering posture`

Full-strength: UAA can inspect MCP servers and expose only reviewed tool slices.

Repo-safe: add metadata catalog, tool filter contracts, blocked activation
states, and CLI inspection.

Blocked / needs authority: installing MCP servers, running subprocess MCPs,
OAuth login, tool invocation, and connector writes.

Exact promotion path: reviewed server manifest, command allowlist, credential
refs, tool grants, receipts, and safe-disable.

## Phase 31: Background Job Model

Branch: `codex/hermes-adoption-31-background-jobs`
Commit: `Add background job model posture`

Full-strength: UAA can schedule governed local tasks with pause/resume/run now,
proof, receipts, and review.

Repo-safe: add durable job read/proposal models and blocked execution labels.

Blocked / needs authority: autonomous background execution, external delivery,
provider calls, shell, connector writes.

Exact promotion path: exact job type, schedule policy, approval, idempotency,
safe-disable, receipt, and failure handling.

## Phase 32: Subagent Isolation Model

Branch: `codex/hermes-adoption-32-subagent-isolation`
Commit: `Add subagent isolation posture`

Full-strength: UAA delegates work to isolated agent workers with scoped context,
tools, authority, and receipts.

Repo-safe: add subagent role/readiness contracts and compare/review artifacts.

Blocked / needs authority: live subagent dispatch or background fan-out.

Exact promotion path: role contract, context pack, toolset grant, approval,
budget, kill switch, receipt, and proof.

## Phase 33: Worktree-Per-Agent Pattern

Branch: `codex/hermes-adoption-33-worktree-per-agent`
Commit: `Add worktree per agent posture`

Full-strength: coding agents work in isolated branches/worktrees with
checkpoint and rollback proof.

Repo-safe: add read-only worktree posture, branch/lane proposal, and blocked
Git mutation labels.

Blocked / needs authority: git worktree create/delete, branch mutation, file
writes, commits, pushes.

Exact promotion path: exact workspace grant, branch naming, checkpoint, Git
receipt, rollback, and CLI parity.

## Phase 34: LSP Semantic Diagnostics

Branch: `codex/hermes-adoption-34-lsp-diagnostics`
Commit: `Add semantic diagnostics proof posture`

Full-strength: UAA attaches language diagnostics to coding proof after changes.

Repo-safe: add diagnostic evidence contracts and placeholders/read models. Do
not start LSP servers unless already authorized.

Blocked / needs authority: launching language servers, installing deps, shell.

Exact promotion path: allowlisted command/server, cwd jail, timeout, redaction,
diagnostic receipt, and proof link.

## Phase 35: Right Preview Rail

Branch: `codex/hermes-adoption-35-preview-rail`
Commit: `Add operator preview rail posture`

Full-strength: UAA previews files, diffs, artifacts, screenshots, run output,
proof, and delegated runtime events beside chat.

Repo-safe: add preview rail UI backed by safe refs and backend read models.

Blocked / needs authority: live browser automation, raw file display for
sensitive refs, direct runtime payload rendering.

Exact promotion path: source classification, redaction, bounded preview,
operator attach, receipt, and visual tests.

## Phase 36: Slash Command Registry

Branch: `codex/hermes-adoption-36-command-registry`
Commit: `Add governed slash command registry posture`

Full-strength: UAA chat commands are centrally registered, documented,
authority-classified, and CLI/API aligned.

Repo-safe: add command metadata/read models and disabled/blocked command
labels.

Blocked / needs authority: commands that mutate state or invoke runtimes
without exact lanes.

Exact promotion path: command contract, side-effect class, approval policy,
idempotency, receipt, and tests.


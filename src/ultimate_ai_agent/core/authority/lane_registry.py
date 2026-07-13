from __future__ import annotations


def build_existing_lane_authority_mappings():
    from ultimate_ai_agent.core.authority.contracts import (
        AuthorityCapability,
        AuthorityDomain,
        TrustMode,
        _mapping,
    )
    from ultimate_ai_agent.core.authority.memory_lane_registry import (
        build_memory_lane_authority_mappings,
    )

    return [
        _mapping(
            "lane-ref:authority-lease-control-plane",
            "AuthorityLease issue and revoke",
            AuthorityDomain.system_settings,
            AuthorityCapability.write,
            TrustMode.ask_before_changes,
            "implemented_operator_selected_root_control_receipt_required",
            [
                "POST /api/runtime/authority-leases",
                "POST /api/runtime/authority-leases/approve-and-issue",
                "POST /api/runtime/authority-leases/revoke",
            ],
            [
                "scripts/dev/uaa_runtime.py select-authority-mode --approve",
                "scripts/dev/uaa_runtime.py revoke-authority-lease",
            ],
            (
                "Operator-selected trust-mode control plane for issuing or "
                "revoking session/mission AuthorityLease objects. It records "
                "idempotent receipts, audit refs, redaction posture, rollback/"
                "safe-disable refs, and kill-switch visibility; it does not "
                "execute adapters, mint model/provider authority, bypass "
                "unknown-authority denial, or grant unsupported domains."
            ),
        ),
        _mapping(
            "lane-ref:start-here-read",
            "Start Here local loop summary",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_control_center_read_model",
            ["GET /control-center/start-here/summary"],
            ["python scripts/dev/uaa_founder_loop.py inspect-start-here"],
            (
                "Backend-owned Start Here inspection reads safe refs, readiness, "
                "next safe action, and proof refs only; it does not execute work."
            ),
        ),
        _mapping(
            "lane-ref:today-loop-read",
            "Today daily loop",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_control_center_read_model",
            ["GET /control-center/today/summary"],
            ["python scripts/dev/uaa_founder_loop.py inspect"],
            (
                "Backend-owned Today inspection reads local action, memory, "
                "evidence, proof, and run refs only; mutations need separate gates."
            ),
        ),
        _mapping(
            "lane-ref:proof-detail-read",
            "Universal Proof Detail",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_control_center_read_model",
            [
                "GET /control-center/proof/index",
                "GET /control-center/proof/{proof_ref}",
            ],
            ["python scripts/dev/uaa_founder_loop.py inspect-proof"],
            (
                "Proof inspection reads safe proof, receipt, evidence, and "
                "redaction refs only; proof surfaces do not grant action authority."
            ),
        ),
        _mapping(
            "lane-ref:operator-workspace-spine",
            "Operator Workspace Spine",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_control_center_read_model",
            ["GET /control-center/today/summary#operator_workspace_spine"],
            ["python scripts/inspect_operator_workspace_spine.py"],
            (
                "Workspace spine inspection reads safe workspace, Git, preview, "
                "run-log, and handoff posture refs without starting or editing."
            ),
        ),
        _mapping(
            "lane-ref:action-inbox-work-queue",
            "Action Inbox work queue",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_control_center_read_model",
            ["GET /control-center/actions/inbox"],
            ["python scripts/dev/uaa_founder_loop.py inspect-action-work-queue"],
            (
                "Action Inbox queue inspection reads requested, blocked, and "
                "receipt-recorded item refs only; execution requires exact lanes."
            ),
        ),
        _mapping(
            "lane-ref:memory-review-read",
            "Memory Review and loop binding",
            AuthorityDomain.memory,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_control_center_read_model",
            ["GET /control-center/memory/review"],
            [
                "python scripts/dev/uaa_founder_loop.py "
                "inspect-evidence-memory-binding"
            ],
            (
                "Memory Review inspection reads recall candidates and why-shown "
                "safe refs only; memory remains recall, not truth or authority."
            ),
        ),
        _mapping(
            "lane-ref:evidence-timeline-read",
            "Evidence Timeline",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_control_center_read_model",
            ["GET /control-center/evidence/timeline"],
            ["python scripts/dev/uaa_founder_loop.py inspect"],
            (
                "Evidence Timeline inspection reads local safe-ref history linked "
                "to actions, memory, runs, receipts, and proof; it cannot execute."
            ),
        ),
        _mapping(
            "lane-ref:local-draft-proposal",
            "Local drafts and proposals",
            AuthorityDomain.workspace,
            AuthorityCapability.draft,
            TrustMode.read_only,
            "implemented_control_center_draft_proposal",
            [
                "GET /control-center/memory/context-packs",
                "GET /control-center/memory/context-packs/{context_pack_ref}/preview",
            ],
            ["python scripts/dev/uaa_founder_loop.py memory-context-manifest"],
            (
                "Local draft/proposal inspection may prepare review artifacts "
                "inside read-only workspace draft scope; applying or sending is separate."
            ),
        ),
        _mapping(
            "lane-ref:model-slot-posture",
            "Main and auxiliary model slot posture",
            AuthorityDomain.provider_model_calls,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_control_center_model_slot_read_model",
            ["GET /control-center/providers/runtime-control-plane"],
            ["python scripts/inspect_model_provider_control_plane.py"],
            (
                "Model slot posture is read-only routing intent inspection; it "
                "does not call models, switch providers, or trust model output."
            ),
        ),
        _mapping(
            "lane-ref:runtime-virtual-provider-moa-read-model",
            "Runtime virtual provider MoA read model",
            AuthorityDomain.provider_model_calls,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/virtual-provider-moa"],
            ["repo-local-command:uaa-runtime-inspect-virtual-provider-moa"],
            (
                "Virtual provider MoA inspection reads slot, routing, cost, "
                "output-envelope, comparison-proof, and blocked authority refs "
                "under provider_model_calls/read. Live fan-out, provider SDK, "
                "dispatch, hidden prompts, output authority, connector writes, "
                "shell, browser automation, and production remain blocked."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:virtual-provider-moa-live-fanout:not-implemented",
                "adapter-ref:virtual-provider-moa-provider-sdk:not-implemented",
                "adapter-ref:virtual-provider-moa-external-dispatch:not-implemented",
                "adapter-ref:virtual-provider-moa-hidden-prompts:not-implemented",
                "adapter-ref:virtual-provider-moa-output-authority:not-implemented",
                "adapter-ref:virtual-provider-moa-connector-write:not-implemented",
                "adapter-ref:virtual-provider-moa-shell-execution:not-implemented",
                "adapter-ref:virtual-provider-moa-browser-automation:not-implemented",
                "adapter-ref:virtual-provider-moa-production-authority:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:connector-draft-only",
            "Connector draft-only proposals",
            AuthorityDomain.email,
            AuthorityCapability.draft,
            TrustMode.read_only,
            "implemented_control_center_connector_draft_only",
            ["GET /control-center/sources/readiness#connector_draft_proposals"],
            ["python scripts/inspect_connector_draft_proposals.py"],
            (
                "Connector draft-only proposals are local safe-ref review "
                "artifacts; live account sync, sends, and writes remain separate."
            ),
        ),
        _mapping(
            "lane-ref:shell-arbitrary-command-adapter",
            "Arbitrary shell command adapter",
            AuthorityDomain.shell,
            AuthorityCapability.execute,
            TrustMode.full_machine_access_session,
            "planned_unsupported_adapter",
            ["GET /api/runtime/authority-state"],
            ["scripts/dev/uaa_runtime.py inspect-authority-state"],
            (
                "Shell execute is a known authority domain, but arbitrary shell "
                "strings are not implemented; only separately mapped RuntimeGateway "
                "workspace commands may execute under their exact lease gates."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:shell-arbitrary-command:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:apps-local-automation-adapter",
            "Local app automation adapter",
            AuthorityDomain.apps,
            AuthorityCapability.execute,
            TrustMode.full_machine_access_session,
            "planned_unsupported_adapter",
            ["GET /api/runtime/authority-state"],
            ["scripts/dev/uaa_runtime.py inspect-authority-state"],
            (
                "Local app control is modeled as an authority domain, but app "
                "automation adapters are not implemented or callable from leases."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:apps-local-automation:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:issue-tracker-sync",
            "Issue tracker exact sync adapter",
            AuthorityDomain.apps,
            AuthorityCapability.write,
            TrustMode.full_machine_access_session,
            "planned_unsupported_adapter",
            ["external-lane-ref:issue-tracker-sync-exact-approved"],
            ["scripts/dev/uaa_runtime.py inspect-authority-state"],
            (
                "Issue tracker sync is a known Apps/write authority capability, "
                "but no project binding, item write adapter, receipt replay, or "
                "compensating update adapter is implemented."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:issue-tracker-sync:not-implemented",
                "adapter-ref:issue-tracker-compensating-update:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-capability-discovery-read-model",
            "Runtime capability discovery read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/capability-discovery"],
            ["repo-local-command:uaa-runtime-inspect-capability-discovery"],
            (
                "Runtime capability discovery reads static runtime capability, "
                "toolset, blocked-authority, proof, and next-safe-action refs "
                "under Workspace read authority. It does not enable live "
                "discovery, tool invocation, config mutation, browser or "
                "connector work, provider calls, plugin import, raw runtime "
                "payload persistence, or production authority."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:runtime-live-capability-discovery:not-implemented",
                "adapter-ref:runtime-tool-invocation:not-implemented",
                "adapter-ref:runtime-toolset-config-mutation:not-implemented",
                "adapter-ref:runtime-browser-automation:not-implemented",
                "adapter-ref:runtime-connector-write:not-implemented",
                "adapter-ref:runtime-plugin-import:not-implemented",
                "adapter-ref:runtime-production-authority:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-tool-registry-read-model",
            "Runtime tool registry read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/tool-registry"],
            ["repo-local-command:uaa-runtime-inspect-tool-registry"],
            (
                "Runtime tool registry inspection reads static UAA-native and "
                "delegated-reference tool metadata, blocker refs, proof refs, "
                "and next-safe-action refs under Workspace read authority. It "
                "does not enable invocation, execution, remote discovery, web "
                "fetch, provider calls, plugin import, connector writes, raw "
                "tool payload persistence, or production authority."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:runtime-tool-invocation:not-implemented",
                "adapter-ref:runtime-tool-execution:not-implemented",
                "adapter-ref:runtime-tool-remote-discovery:not-implemented",
                "adapter-ref:runtime-tool-web-fetch:not-implemented",
                "adapter-ref:runtime-tool-provider-call:not-implemented",
                "adapter-ref:runtime-tool-plugin-import:not-implemented",
                "adapter-ref:runtime-tool-connector-write:not-implemented",
                "adapter-ref:runtime-tool-raw-payload:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-run-events-read-model",
            "Runtime run events read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/run-events"],
            ["repo-local-command:uaa-runtime-inspect-run-events"],
            (
                "Runtime run/event inspection reads lifecycle mappings, "
                "approval-wait proposal metadata, proof refs, receipt-plan "
                "refs, blocked refs, and safe event refs under Workspace read "
                "authority. It does not create or stop runs, resolve approvals, "
                "stream live events, call providers, execute tools, or persist "
                "raw runtime payloads."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:runtime-run-create:not-implemented",
                "adapter-ref:runtime-run-stop:not-implemented",
                "adapter-ref:runtime-run-approval-resolution:not-implemented",
                "adapter-ref:runtime-run-live-event-stream:not-implemented",
                "adapter-ref:runtime-run-retry-recovery:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-approval-bridge-read-model",
            "Runtime approval bridge read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/approval-bridge"],
            ["repo-local-command:uaa-runtime-inspect-approval-bridge"],
            (
                "Runtime approval bridge inspection reads approval-wait "
                "envelopes, local decision previews, fail-closed timeout "
                "posture, scope validation, proof refs, and blocked refs under "
                "Workspace read authority. It does not send approve, deny, "
                "timeout, or scope-mismatch resolutions, auto-approve, grant "
                "standing authority, or persist raw runtime payloads."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:runtime-approval-resolution-send:not-implemented",
                "adapter-ref:runtime-approval-denial-send:not-implemented",
                "adapter-ref:runtime-approval-timeout-send:not-implemented",
                "adapter-ref:runtime-approval-scope-mismatch-send:not-implemented",
                "adapter-ref:runtime-approval-standing-grant:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-streaming-progress-read-model",
            "Runtime streaming progress read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/streaming-progress"],
            ["repo-local-command:uaa-runtime-inspect-streaming-progress"],
            (
                "Runtime streaming progress inspection reads ordered redacted "
                "event previews, hashes, proof refs, blocked transport refs, "
                "and next safe action refs under Workspace read authority. "
                "Live transport, reconnect, event ingest, tool execution, and "
                "raw material persistence remain blocked."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:runtime-streaming-progress-live-sse:not-implemented",
                "adapter-ref:runtime-streaming-progress-"
                "websocket:not-implemented",
                "adapter-ref:runtime-streaming-progress-reconnect:not-implemented",
                "adapter-ref:runtime-streaming-progress-event-ingest:not-implemented",
                "adapter-ref:runtime-streaming-progress-raw-payload:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-profile-isolation-read-model",
            "Runtime profile isolation read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/profiles"],
            ["repo-local-command:uaa-runtime-inspect-profiles"],
            (
                "Runtime profile inspection reads isolated UAA and delegated "
                "profile refs, scope refs, proof refs, blockers, and next safe "
                "actions under Workspace read authority. Profile mutation, "
                "live activation, tool execution, provider calls, memory "
                "writes, sensitive copy, and cross profile authority remain "
                "blocked."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:runtime-profile-create-delete:not-implemented",
                "adapter-ref:runtime-profile-config-write:not-implemented",
                "adapter-ref:runtime-profile-sensitive-copy:not-implemented",
                "adapter-ref:runtime-profile-default-change:not-implemented",
                "adapter-ref:runtime-profile-live-activation:not-implemented",
                "adapter-ref:runtime-profile-tool-execution:not-implemented",
                "adapter-ref:runtime-profile-provider-call:not-implemented",
                "adapter-ref:runtime-profile-memory-write:not-implemented",
                "adapter-ref:runtime-profile-cross-authority:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-managed-scope-policy-read-model",
            "Runtime managed scope policy read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/managed-scope-policy"],
            ["repo-local-command:uaa-runtime-inspect-managed-scope-policy"],
            (
                "Managed scope policy inspection reads pinned local policy "
                "source refs, precedence, drift warnings, rollback refs, proof "
                "refs, blockers, and next safe actions under Workspace read "
                "authority. System config writes, privileged writes, MDM "
                "delivery, protected material management, and production "
                "enforcement remain blocked."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:managed-scope-system-config-write:not-implemented",
                "adapter-ref:managed-scope-privileged-write:not-implemented",
                "adapter-ref:managed-scope-mdm-delivery:not-implemented",
                "adapter-ref:managed-scope-protected-material:not-implemented",
                "adapter-ref:managed-scope-unsigned-config-override:not-implemented",
                "adapter-ref:managed-scope-production-enforcement:not-implemented",
                "adapter-ref:managed-scope-authority-mint:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-doctor-diagnostics-read-model",
            "Runtime doctor diagnostics read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/doctor-diagnostics"],
            ["repo-local-command:uaa-runtime-inspect-doctor-diagnostics"],
            (
                "Runtime doctor inspection reads setup, runtime, provider, "
                "tool, protected material, service, authority, proof, blocker, "
                "and next safe action refs under Workspace read authority. "
                "Installs, service starts, credential writes, runtime config "
                "mutation, provider payload persistence, and authority minting "
                "remain blocked."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:runtime-doctor-install:not-implemented",
                "adapter-ref:runtime-doctor-service-start:not-implemented",
                "adapter-ref:runtime-doctor-protected-material-write:not-implemented",
                "adapter-ref:runtime-doctor-config-mutation:not-implemented",
                "adapter-ref:runtime-doctor-provider-material-persistence:not-implemented",
                "adapter-ref:runtime-doctor-authority-mint:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-session-continuity-read-model",
            "Runtime session continuity read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/session-continuity"],
            ["repo-local-command:uaa-runtime-inspect-session-continuity"],
            (
                "Session continuity inspection reads session refs, surface "
                "labels, staleness states, conflict states, proof refs, "
                "blockers, and next safe actions under Workspace read "
                "authority. External messaging gateways, account sync, "
                "connector writes, remote sessions, raw turn persistence, "
                "provider material persistence, and authority minting remain "
                "blocked."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:session-continuity-external-message-gateway:not-implemented",
                "adapter-ref:session-continuity-account-sync:not-implemented",
                "adapter-ref:session-continuity-connector-write:not-implemented",
                "adapter-ref:session-continuity-remote-session:not-implemented",
                "adapter-ref:session-continuity-turn-material-persistence:not-implemented",
                "adapter-ref:session-continuity-provider-material-persistence:not-implemented",
                "adapter-ref:session-continuity-authority-mint:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-mcp-catalog-filtering-read-model",
            "Runtime MCP catalog filtering read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/mcp-catalog-filtering"],
            ["repo-local-command:uaa-runtime-inspect-mcp-catalog-filtering"],
            (
                "MCP catalog filtering reads reviewed server metadata, tool "
                "filter states, proof refs, blockers, and next safe actions "
                "under Workspace read authority. Server install, subprocess "
                "runtime, OAuth login, tool invocation, connector writes, raw "
                "manifest persistence, and authority minting remain blocked."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:mcp-catalog-server-install:not-implemented",
                "adapter-ref:mcp-catalog-subprocess-runtime:not-implemented",
                "adapter-ref:mcp-catalog-oauth-login:not-implemented",
                "adapter-ref:mcp-catalog-tool-invocation:not-implemented",
                "adapter-ref:mcp-catalog-connector-write:not-implemented",
                "adapter-ref:mcp-catalog-manifest-persistence:not-implemented",
                "adapter-ref:mcp-catalog-authority-mint:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-usage-cost-analytics-read-model",
            "Runtime usage and cost analytics read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/usage-cost-analytics"],
            ["repo-local-command:uaa-runtime-inspect-usage-cost-analytics"],
            (
                "Runtime usage and cost analytics reads redacted accounting "
                "record refs, bounded usage estimates, proof refs, blockers, "
                "and next safe actions under Workspace read authority. Billing, "
                "provider calls, live price fetches, exports, material "
                "persistence, output authority, and production authority remain "
                "blocked."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:usage-cost-provider-call:not-implemented",
                "adapter-ref:usage-cost-provider-sdk-call:not-implemented",
                "adapter-ref:usage-cost-billing-action:not-implemented",
                "adapter-ref:usage-cost-live-price-fetch:not-implemented",
                "adapter-ref:usage-cost-operator-export:not-implemented",
                "adapter-ref:usage-cost-turn-material-persistence:not-implemented",
                "adapter-ref:usage-cost-provider-material-persistence:not-implemented",
                "adapter-ref:usage-cost-output-authority:not-implemented",
                "adapter-ref:usage-cost-production-authority:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-prompt-stability-tiers-read-model",
            "Runtime prompt stability tiers read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/prompt-stability-tiers"],
            ["repo-local-command:uaa-runtime-inspect-prompt-stability-tiers"],
            (
                "Prompt stability tier inspection reads manifest, hash, cache "
                "policy, proof, blocker, and next safe action refs under "
                "Workspace read authority. Hidden injection, context injection, "
                "model/provider calls, cache writes, material persistence, "
                "output authority, and production authority remain blocked."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:prompt-stability-hidden-injection:not-implemented",
                "adapter-ref:prompt-stability-context-injection:not-implemented",
                "adapter-ref:prompt-stability-model-call:not-implemented",
                "adapter-ref:prompt-stability-provider-sdk-call:not-implemented",
                "adapter-ref:prompt-stability-cache-write:not-implemented",
                "adapter-ref:prompt-stability-turn-material-persistence:not-implemented",
                "adapter-ref:prompt-stability-provider-material-persistence:not-implemented",
                "adapter-ref:prompt-stability-output-authority:not-implemented",
                "adapter-ref:prompt-stability-production-authority:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-context-budget-pressure-read-model",
            "Runtime context budget pressure read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/context-budget-pressure"],
            ["repo-local-command:uaa-runtime-inspect-context-budget-pressure"],
            (
                "Context budget pressure inspection reads budget, warning, "
                "proposal, proof, blocker, and next safe action refs under "
                "Workspace read authority. Hidden compression, context mutation, "
                "model/provider calls, cache writes, material persistence, and "
                "production authority remain blocked."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:context-budget-hidden-compression:not-implemented",
                "adapter-ref:context-budget-automatic-mutation:not-implemented",
                "adapter-ref:context-budget-model-summarization:not-implemented",
                "adapter-ref:context-budget-turn-material-persistence:not-implemented",
                "adapter-ref:context-budget-provider-material-persistence:not-implemented",
                "adapter-ref:context-budget-context-injection:not-implemented",
                "adapter-ref:context-budget-provider-sdk-call:not-implemented",
                "adapter-ref:context-budget-cache-write:not-implemented",
                "adapter-ref:context-budget-production-authority:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-hardline-command-blocklist-read-model",
            "Runtime hardline command blocklist read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/hardline-command-blocklist"],
            ["repo-local-command:uaa-runtime-inspect-hardline-command-blocklist"],
            (
                "Hardline command blocklist inspection reads command-shape "
                "classification, rule, blocker, proof, and next safe action "
                "refs under Workspace read authority. Floor override, command "
                "string bypass, command execution, command material persistence, "
                "and production authority remain blocked."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:runtime-hardline-floor-override:not-implemented",
                "adapter-ref:runtime-command-string-bypass:not-implemented",
                "adapter-ref:runtime-shell-metachar-bypass:not-implemented",
                "adapter-ref:runtime-destructive-command-bypass:not-implemented",
                "adapter-ref:runtime-network-command-bypass:not-implemented",
                "adapter-ref:runtime-git-mutation-bypass:not-implemented",
                "adapter-ref:runtime-package-install-bypass:not-implemented",
                "adapter-ref:runtime-privilege-escalation-bypass:not-implemented",
                "adapter-ref:runtime-command-material-persistence:not-implemented",
                "adapter-ref:runtime-command-output-material-persistence:not-implemented",
                "adapter-ref:runtime-production-command-authority:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-checkpoint-rollback-read-model",
            "Runtime checkpoint rollback read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/checkpoint-rollback"],
            ["repo-local-command:uaa-runtime-inspect-checkpoint-rollback"],
            (
                "Checkpoint rollback inspection reads checkpoint, receipt, "
                "rollback-plan, approval-scope, idempotency, proof, and blocked "
                "authority refs under Workspace read authority. Broad snapshots, "
                "rollback execution, Git mutation, unredacted material "
                "persistence, shell/browser execution, and production authority "
                "remain blocked."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:checkpoint-rollback-broad-snapshot:not-implemented",
                "adapter-ref:checkpoint-rollback-execution-route:not-implemented",
                "adapter-ref:checkpoint-rollback-git-mutation:not-implemented",
                "adapter-ref:checkpoint-rollback-material-persistence:not-implemented",
                "adapter-ref:checkpoint-rollback-path-material:not-implemented",
                "adapter-ref:checkpoint-rollback-shell-execution:not-implemented",
                "adapter-ref:checkpoint-rollback-browser-automation:not-implemented",
                "adapter-ref:checkpoint-rollback-production-authority:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-context-references-read-model",
            "Runtime context references read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/context-references"],
            ["repo-local-command:uaa-runtime-inspect-context-references"],
            (
                "Context reference inspection reads safe refs, previews, budget "
                "estimates, why-included refs, guard posture, proof, and blocked "
                "authority refs under Workspace read authority. Live fetch, "
                "context injection, protected configuration reads, provider "
                "calls, connector writes, shell/browser execution, and production "
                "authority remain blocked."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:context-references-live-url-fetch:not-implemented",
                "adapter-ref:context-references-path-material:not-implemented",
                "adapter-ref:context-references-file-material:not-implemented",
                "adapter-ref:context-references-context-injection:not-implemented",
                "adapter-ref:context-references-protected-config-read:not-implemented",
                "adapter-ref:context-references-provider-call:not-implemented",
                "adapter-ref:context-references-connector-write:not-implemented",
                "adapter-ref:context-references-shell-execution:not-implemented",
                "adapter-ref:context-references-browser-automation:not-implemented",
                "adapter-ref:context-references-production-authority:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-session-lineage-read-model",
            "Runtime session lineage read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/session-lineage"],
            ["repo-local-command:uaa-runtime-inspect-session-lineage"],
            (
                "Session lineage inspection reads parent, child, fork, proof, "
                "reason, retrieval-log, compare-view, and blocked authority refs "
                "under Workspace read authority. Transcript copy, prompt/response "
                "material persistence, hidden context injection, runtime dispatch, "
                "provider calls, shell/browser execution, connector writes, and "
                "production authority remain blocked."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:session-lineage-transcript-copy:not-implemented",
                "adapter-ref:session-lineage-prompt-material:not-implemented",
                "adapter-ref:session-lineage-response-material:not-implemented",
                "adapter-ref:session-lineage-hidden-context-injection:not-implemented",
                "adapter-ref:session-lineage-runtime-dispatch:not-implemented",
                "adapter-ref:session-lineage-provider-call:not-implemented",
                "adapter-ref:session-lineage-shell-execution:not-implemented",
                "adapter-ref:session-lineage-browser-automation:not-implemented",
                "adapter-ref:session-lineage-connector-write:not-implemented",
                "adapter-ref:session-lineage-production-authority:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-session-search-read-model",
            "Runtime session search read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/session-search"],
            ["repo-local-command:uaa-runtime-inspect-session-search"],
            (
                "Session search inspection reads safe refs, summaries, "
                "why-matched refs, attachable context refs, memory-separation "
                "posture, proof, and blocked authority refs under Workspace "
                "read authority. Transcript material, semantic indexing, "
                "context injection, memory writes, action execution, live "
                "fetch, connector writes, and production remain blocked."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:session-search-transcript-material:not-implemented",
                "adapter-ref:session-search-prompt-response-material:not-implemented",
                "adapter-ref:session-search-semantic-provider-call:not-implemented",
                "adapter-ref:session-search-embedding-vector-index:not-implemented",
                "adapter-ref:session-search-context-injection:not-implemented",
                "adapter-ref:session-search-memory-write:not-implemented",
                "adapter-ref:session-search-action-execution:not-implemented",
                "adapter-ref:session-search-live-web-fetch:not-implemented",
                "adapter-ref:session-search-connector-write:not-implemented",
                "adapter-ref:session-search-background-indexing:not-implemented",
                "adapter-ref:session-search-production-authority:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-command-git-status",
            "Git status",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented",
            ["GET /api/runtime/capabilities"],
            ["repo-local-command:uaa-runtime-command-git-status"],
            "Allowed by Read-only with workspace/read when the exact gateway command shape matches.",
        ),
        _mapping(
            "lane-ref:runtime-command-focused-pytest",
            "Focused pytest",
            AuthorityDomain.workspace,
            AuthorityCapability.execute,
            TrustMode.approved_safe_local_work_session,
            "implemented_exact_lease_required",
            ["POST /api/runtime/command/run"],
            ["repo-local-command:uaa-runtime-command-run"],
            "Requires Approved safe local work with workspace/execute plus RuntimeGateway allowlist and receipts.",
        ),
        _mapping(
            "lane-ref:runtime-command-repo-doctor",
            "Repo doctor",
            AuthorityDomain.workspace,
            AuthorityCapability.execute,
            TrustMode.approved_safe_local_work_session,
            "implemented_exact_lease_required",
            ["POST /api/runtime/command/run"],
            ["repo-local-command:uaa-runtime-command-run"],
            "Requires Approved safe local work with workspace/execute plus RuntimeGateway allowlist and receipts.",
        ),
        _mapping(
            "lane-ref:runtime-invocation-record",
            "Runtime invocation record",
            AuthorityDomain.workspace,
            AuthorityCapability.draft,
            TrustMode.read_only,
            "implemented_no_execution_record_only",
            ["POST /api/runtime/invocations"],
            ["repo-local-command:governed-runtime-invocations-list"],
            (
                "Records a redacted RuntimeGateway invocation proposal only; "
                "adapter execution, approval, command execution, model calls, "
                "browser automation, connector writes, and production authority "
                "remain denied unless an AuthorityLease-gated capability is "
                "implemented, approved, and active."
            ),
        ),
        _mapping(
            "lane-ref:runtime-action-inbox-approval-binding",
            "Runtime approval binding",
            AuthorityDomain.workspace,
            AuthorityCapability.execute,
            TrustMode.approved_safe_local_work_session,
            "implemented_exact_approval_binding_lease_evaluated",
            ["POST /api/runtime/invocations/{id}/approve"],
            ["repo-local-command:governed-runtime-action-approve-preflight"],
            (
                "Binds exact Action Inbox approval refs to one RuntimeGateway "
                "command envelope and evaluates workspace/execute lease scope; "
                "approval refs are identifiers only and do not execute work."
            ),
        ),
        _mapping(
            "lane-ref:runtime-action-inbox-approved-execute",
            "Runtime approved execution",
            AuthorityDomain.workspace,
            AuthorityCapability.execute,
            TrustMode.approved_safe_local_work_session,
            "implemented_exact_lease_rechecked_execution",
            ["POST /api/runtime/invocations/{id}/execute"],
            [],
            (
                "Executes only exact approved RuntimeGateway command envelopes "
                "after idempotency, approval refs, active workspace/execute "
                "AuthorityLease recheck, safe-disable, redacted receipts, and "
                "allowlist gates pass."
            ),
        ),
        _mapping(
            "lane-ref:runtime-worktree-implementer-proposal",
            "Runtime worktree implementer proposal",
            AuthorityDomain.workspace,
            AuthorityCapability.draft,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/worktree-per-agent"],
            ["repo-local-command:uaa-runtime-inspect-worktree-per-agent"],
            (
                "Implementer worktree lane is a read-only Workspace draft "
                "proposal for branch/worktree shape. It does not create "
                "worktrees, mutate branches, write files, commit, push, run "
                "shell commands, call providers, or persist path values."
            ),
        ),
        _mapping(
            "lane-ref:runtime-worktree-reviewer-compare",
            "Runtime worktree reviewer compare",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/worktree-per-agent"],
            ["repo-local-command:uaa-runtime-inspect-worktree-per-agent"],
            (
                "Reviewer worktree lane reads safe comparison refs only under "
                "Workspace read authority. Git worktree create/delete, file "
                "mutation, commit, push, shell execution, and path-value "
                "persistence remain blocked."
            ),
        ),
        _mapping(
            "lane-ref:runtime-worktree-verifier-proof",
            "Runtime worktree verifier proof",
            AuthorityDomain.workspace,
            AuthorityCapability.prepare,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/worktree-per-agent"],
            ["repo-local-command:uaa-runtime-inspect-worktree-per-agent"],
            (
                "Verifier worktree lane prepares checkpoint, Git receipt, and "
                "rollback plan refs under Workspace prepare authority. It does "
                "not run Git, shell commands, provider calls, file writes, "
                "commits, pushes, or rollback execution."
            ),
        ),
        _mapping(
            "lane-ref:staged-orchestration-read-model",
            "Staged orchestration read model",
            AuthorityDomain.workspace,
            AuthorityCapability.prepare,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/staged-orchestration"],
            ["repo-local-command:uaa-runtime-inspect-staged-orchestration"],
            (
                "Staged orchestration inspection prepares safe plan, dependency, "
                "checkpoint, receipt-plan, and degraded-handoff refs under "
                "Workspace prepare authority. The read model cannot execute, "
                "mint approvals, call models, run shell commands, automate "
                "browsers, write connectors, or grant production authority."
            ),
        ),
        _mapping(
            "lane-ref:runtime-preview-rail-safe-ref-read-model",
            "Runtime preview rail safe-ref read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/preview-rail"],
            ["repo-local-command:uaa-runtime-inspect-preview-rail"],
            (
                "Preview rail inspection reads safe refs, source "
                "classifications, bounded preview plans, receipt-plan refs, "
                "and proof refs under Workspace read authority. It does not "
                "read raw files, render raw runtime payloads, capture "
                "screenshots, automate browsers, run shell commands, call "
                "providers, or persist raw paths/content."
            ),
        ),
        _mapping(
            "lane-ref:runtime-slash-command-registry-metadata",
            "Runtime slash command registry metadata",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/slash-command-registry"],
            ["repo-local-command:uaa-runtime-inspect-slash-command-registry"],
            (
                "Slash command registry inspection reads command metadata, "
                "side-effect classes, approval/idempotency policies, receipt "
                "plans, and proof refs under Workspace read authority. It does "
                "not enable chat triggers, runtime invocations, state mutation, "
                "shell execution, provider calls, browser automation, connector "
                "writes, or prompt/response material persistence."
            ),
        ),
        _mapping(
            "lane-ref:runtime-result-classification-taxonomy",
            "Runtime result classification taxonomy",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/result-classification"],
            ["repo-local-command:uaa-runtime-inspect-result-classification"],
            (
                "Result classification inspection reads taxonomy labels, "
                "verification statuses, provenance/redaction policies, receipt "
                "requirements, proof bindings, and blocked refs under "
                "Workspace read authority. It does not make tool output truth, "
                "grant action authority, mutate without receipts, persist "
                "output/provider material, or mint Control Center authority."
            ),
        ),
        _mapping(
            "lane-ref:runtime-logging-profile-posture",
            "Runtime logging profile posture",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/logging-profile"],
            ["repo-local-command:uaa-runtime-inspect-logging-profile"],
            (
                "Logging profile inspection reads active profile, retention, "
                "TTL, redaction verifier, proof, safe-disable, and blocked refs "
                "under Workspace read authority. It does not enable verbose "
                "logging, prompt/response/log/provider/path material persistence, "
                "remote telemetry export, background log streams, or Control "
                "Center authority minting."
            ),
        ),
        _mapping(
            "lane-ref:runtime-interrupt-redirect-proposals",
            "Runtime interrupt redirect proposals",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/interrupt-redirect"],
            ["repo-local-command:uaa-runtime-inspect-interrupt-redirect"],
            (
                "Interrupt redirect inspection reads run-control proposal "
                "metadata, approval scopes, idempotency refs, receipt plans, "
                "recovery/proof refs, and blocked refs under Workspace read "
                "authority. It does not post live stops, kill processes, mutate "
                "runtime state, run shell/provider/browser work, write "
                "connectors, or persist runtime/log material."
            ),
        ),
        _mapping(
            "lane-ref:runtime-voice-media-posture-read-model",
            "Runtime voice and media posture read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/voice-media-posture"],
            ["repo-local-command:uaa-runtime-inspect-voice-media-posture"],
            (
                "Voice and media posture inspection reads lane labels, consent, "
                "device-permission, redaction, receipt, proof, safe-disable, "
                "and blocked refs under Workspace read authority. It does not "
                "use microphones, cameras, uploads, transcription, generation, "
                "provider calls, external delivery, media material persistence, "
                "or Control Center authority minting."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:voice-media-microphone:not-implemented",
                "adapter-ref:voice-media-camera:not-implemented",
                "adapter-ref:voice-media-upload:not-implemented",
                "adapter-ref:voice-media-transcription:not-implemented",
                "adapter-ref:voice-media-generation:not-implemented",
                "adapter-ref:voice-media-provider-call:not-implemented",
                "adapter-ref:voice-media-external-delivery:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-messaging-gateway-posture-read-model",
            "Runtime messaging gateway posture read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/messaging-gateway-posture"],
            ["repo-local-command:uaa-runtime-inspect-messaging-gateway-posture"],
            (
                "Messaging gateway posture inspection reads platform, "
                "connector, inbound/outbound, OAuth, webhook, account-sync, "
                "redaction, proof, and blocked refs under Workspace read "
                "authority. It does not enable connector runtime/reads, sends, "
                "OAuth, webhooks, sync, writes, message persistence, or "
                "Control Center authority minting."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:messaging-gateway-email:not-implemented",
                "adapter-ref:messaging-gateway-slack:not-implemented",
                "adapter-ref:messaging-gateway-telegram:not-implemented",
                "adapter-ref:messaging-gateway-sms:not-implemented",
                "adapter-ref:messaging-gateway-discord:not-implemented",
                "adapter-ref:messaging-gateway-webhook:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-remote-execution-posture-read-model",
            "Runtime remote execution posture read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/remote-execution-posture"],
            ["repo-local-command:uaa-runtime-inspect-remote-execution-posture"],
            (
                "Remote execution posture inspection reads backend labels, "
                "workspace boundary, credential policy, network policy, "
                "receipt, budget, rollback, kill-switch, proof, and blocked "
                "refs under Workspace read authority. It does not enable "
                "remote execution, host access, cloud sandboxes, file sync, "
                "protected material access, process control, or credential "
                "persistence."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:remote-execution-local-container:not-implemented",
                "adapter-ref:remote-execution-ssh:not-implemented",
                "adapter-ref:remote-execution-secure-host:not-implemented",
                "adapter-ref:remote-execution-cloud-sandbox:not-implemented",
                "adapter-ref:remote-execution-serverless-worker:not-implemented",
                "adapter-ref:remote-execution-remote-gpu:not-implemented",
                "adapter-ref:remote-execution-file-sync:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-plugin-metadata-posture-read-model",
            "Runtime plugin metadata posture read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/plugin-metadata-posture"],
            ["repo-local-command:uaa-runtime-inspect-plugin-metadata-posture"],
            (
                "Plugin metadata posture inspection reads surface labels, "
                "reviewed manifest, static scan, sandbox, activation grant, "
                "rollback, safe-disable, receipt, proof, and blocked refs. "
                "It does not enable runtime imports, hooks, installs, "
                "marketplace content, plugin code, connector writes, provider "
                "calls, command execution, or raw manifest persistence."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:plugin-runtime-import:not-implemented",
                "adapter-ref:plugin-hook-execution:not-implemented",
                "adapter-ref:plugin-package-install:not-implemented",
                "adapter-ref:plugin-marketplace-content:not-implemented",
                "adapter-ref:plugin-code-execution:not-implemented",
                "adapter-ref:plugin-connector-write:not-implemented",
                "adapter-ref:plugin-provider-call:not-implemented",
                "adapter-ref:plugin-command-execution:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-skill-marketplace-posture-read-model",
            "Runtime skill marketplace posture read model",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_bound_read_model",
            ["GET /api/runtime/skill-marketplace-posture"],
            ["repo-local-command:uaa-runtime-inspect-skill-marketplace-posture"],
            (
                "Skill marketplace posture inspection reads discovery signal, "
                "quarantine, review, adaptation, activation grant, receipt, "
                "proof, and blocked refs under Workspace read authority. It "
                "does not enable external code, marketplace installs, runtime "
                "imports, automatic skill writes, provider calls, browser "
                "automation, connector writes, or raw marketplace persistence."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:skill-marketplace-external-code:not-implemented",
                "adapter-ref:skill-marketplace-direct-install:not-implemented",
                "adapter-ref:skill-marketplace-runtime-import:not-implemented",
                "adapter-ref:skill-marketplace-skill-write:not-implemented",
                "adapter-ref:skill-marketplace-provider-call:not-implemented",
                "adapter-ref:skill-marketplace-browser-automation:not-implemented",
                "adapter-ref:skill-marketplace-connector-write:not-implemented",
                "adapter-ref:skill-marketplace-raw-payload:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:staged-orchestration-approved-runtime-command",
            "Staged orchestration approved runtime command step",
            AuthorityDomain.workspace,
            AuthorityCapability.execute,
            TrustMode.approved_safe_local_work_session,
            "implemented_exact_lease_required_runtime_command_step",
            [
                "GET /api/runtime/staged-orchestration#approved-runtime-command-step",
                "POST /api/runtime/invocations/{id}/execute",
            ],
            ["repo-local-command:uaa-runtime-inspect-staged-orchestration"],
            (
                "A staged approved-runtime-command step requires active "
                "Workspace execute AuthorityLease scope plus exact RuntimeGateway "
                "invocation, Action Inbox approval, idempotency, allowlist, "
                "safe-disable, rollback, redaction, and receipt refs before one "
                "supported utility command may run."
            ),
        ),
        _mapping(
            "lane-ref:runtime-safe-disable",
            "Runtime safe-disable",
            AuthorityDomain.workspace,
            AuthorityCapability.write,
            TrustMode.read_only,
            "implemented_safety_control_no_execution",
            ["POST /api/runtime/safe-disable"],
            ["repo-local-command:governed-runtime-safe-disable"],
            (
                "Records local safe-disable posture as a safety control that can "
                "only reduce runtime authority; it cannot enable execution, mint "
                "approval, call models, run commands, or grant production authority."
            ),
        ),
        _mapping(
            "lane-ref:hermes-interface-chat-exact-cli",
            "Hermes exact CLI chat",
            AuthorityDomain.workspace,
            AuthorityCapability.execute,
            TrustMode.approved_safe_local_work_session,
            "implemented_exact_lease_required_external_runtime",
            ["POST /api/runtime/hermes/chat"],
            ["scripts/dev/uaa_runtime.py hermes-chat"],
            (
                "Requires Approved safe local work with workspace/execute "
                "AuthorityLease scope before UAA discovers or executes the exact "
                "guarded Hermes CLI chat argv; arbitrary args, yolo/oneshot, "
                "tool passthrough, raw persistence, direct memory writes, browser "
                "automation, connector writes, and production authority remain denied."
            ),
        ),
        _mapping(
            "lane-ref:task-decomposition-plan-execute",
            "Task decomposition local plan execution",
            AuthorityDomain.workspace,
            AuthorityCapability.execute,
            TrustMode.approved_safe_local_work_session,
            "implemented_exact_lease_required_local_orchestration",
            ["POST /task-decomposition/plans/execute", "POST /task-decomposition/run"],
            ["repo-local-command:task-decomposition:inspect-run"],
            (
                "Requires Approved safe local work with workspace/execute "
                "AuthorityLease scope before local registered handlers run; "
                "high-risk nodes still require exact LocalApprovalAuthority grants."
            ),
        ),
        _mapping(
            "lane-ref:today-action-envelope-promotion",
            "Today-to-Action envelope promotion",
            AuthorityDomain.workspace,
            AuthorityCapability.draft,
            TrustMode.read_only,
            "implemented_exact_lease_required_proposal_only",
            ["POST /control-center/today/action-envelope"],
            ["scripts/dev/uaa_founder_loop.py promote-action-envelope"],
            (
                "Requires Workspace draft AuthorityLease scope before a Today "
                "item can be promoted into a reviewable Action envelope; action "
                "execution, connector writes, memory writes, shell/browser work, "
                "provider/model calls, and production authority remain denied."
            ),
        ),
        _mapping(
            "lane-ref:work-board-reorder",
            "Work Board reorder",
            AuthorityDomain.workspace,
            AuthorityCapability.write,
            TrustMode.ask_before_changes,
            "implemented_exact_approval_required_mapped",
            ["POST /control-center/work-board/reorder"],
            ["scripts/dev/uaa_work_board.py inspect-reorder-receipt"],
            "Requires Workspace write authority plus exact approval, idempotency, receipts, and rollback refs.",
        ),
        _mapping(
            "lane-ref:work-board-card-create",
            "Work Board card create",
            AuthorityDomain.workspace,
            AuthorityCapability.write,
            TrustMode.ask_before_changes,
            "implemented_exact_approval_required_mapped",
            ["POST /control-center/work-board/cards"],
            ["scripts/dev/uaa_work_board.py inspect-card-create-receipt"],
            "Requires Workspace write authority plus exact approval, idempotency, receipts, and rollback refs.",
        ),
        _mapping(
            "lane-ref:action-inbox-decision-receipts",
            "Action Inbox decision receipts",
            AuthorityDomain.workspace,
            AuthorityCapability.write,
            TrustMode.ask_before_changes,
            "implemented_exact_lease_required_receipt_only",
            [
                "POST /control-center/actions/{action_id}/approve",
                "POST /control-center/actions/{action_id}/edit",
                "POST /control-center/actions/{action_id}/reject",
                "POST /control-center/actions/{action_id}/defer",
            ],
            ["repo-local-command:inspect-action-inbox-decision-lanes"],
            (
                "Requires Workspace write AuthorityLease scope before "
                "approve/edit/reject/defer decision receipt state is recorded; "
                "decision receipts do not execute actions, connector writes, "
                "shell/browser work, memory writes, provider/model calls, or "
                "production authority."
            ),
        ),
        _mapping(
            "lane-ref:action-inbox-local-task-commit",
            "Action Inbox local task commit",
            AuthorityDomain.workspace,
            AuthorityCapability.write,
            TrustMode.ask_before_changes,
            "implemented_exact_approval_required_mapped",
            ["POST /control-center/actions/{action_id}/local-task/commit"],
            ["repo-local-command:inspect-action-inbox-local-task-commit"],
            "Requires Workspace write authority plus exact Action Inbox approval, idempotency, receipts, and safe-disable refs.",
        ),
        *build_memory_lane_authority_mappings(),
        _mapping(
            "lane-ref:memory-context-pack-action-proposal",
            "Memory context-pack internal Action proposal",
            AuthorityDomain.memory,
            AuthorityCapability.draft,
            TrustMode.read_only,
            "implemented_exact_lease_required_proposal_only",
            [
                "POST /control-center/memory/context-packs/{context_pack_ref}/action-proposal"
            ],
            ["scripts/dev/uaa_founder_loop.py memory-context-pack-action-proposal"],
            (
                "Requires Memory draft AuthorityLease scope before reviewed "
                "context-pack refs can create an internal Action proposal receipt; "
                "action execution, runtime context injection, memory write, "
                "connector writes, browser automation, provider/model calls, "
                "and production authority remain denied."
            ),
        ),
        _mapping(
            "lane-ref:crm-local-mutation",
            "CRM local mutation",
            AuthorityDomain.contacts,
            AuthorityCapability.write,
            TrustMode.ask_before_changes,
            "implemented_exact_approval_required_mapped",
            ["POST /control-center/crm/local-mutations"],
            ["repo-local-command:uaa-crm:mutate-local"],
            "Requires Contacts write authority plus exact approval, idempotency, receipts, and rollback refs for local CRM state only.",
        ),
        _mapping(
            "lane-ref:file-review-approval-capture",
            "File Review approval capture",
            AuthorityDomain.files,
            AuthorityCapability.write,
            TrustMode.ask_before_changes,
            "implemented_exact_lease_required_review_only",
            ["POST /files/review" + "/approvals" + "/capture"],
            ["repo-local-command:uaa-runtime-inspect-authority-state"],
            (
                "Requires Files write authority to persist review-only safe refs; "
                "raw file access, context injection, memory writes, export, "
                "execution, patch apply, and rollback execution remain unsupported."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:file-raw-content:not-implemented",
                "adapter-ref:file-patch-apply:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:file-safe-preview",
            "Safe file preview",
            AuthorityDomain.files,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_exact_lease_required_metadata_only",
            ["POST /files/read/preview", "POST /files/tree/preview"],
            ["repo-local-command:uaa-runtime-inspect-authority-state"],
            (
                "Requires Files read authority before safe-root file metadata or "
                "tree previews; raw content and raw paths remain omitted."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:file-raw-content:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:file-write-proposal-diff-preview",
            "File write proposal and diff preview",
            AuthorityDomain.files,
            AuthorityCapability.prepare,
            TrustMode.read_only,
            "implemented_exact_lease_required_proposal_only",
            ["POST /files/write/propose", "POST /files/diff/preview"],
            ["repo-local-command:uaa-runtime-inspect-authority-state"],
            (
                "Requires Files prepare authority before write proposal or "
                "redacted diff preview; patch apply and rollback execution remain "
                "unsupported."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:file-patch-apply:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:source-readiness-email-calendar",
            "Email and calendar metadata readiness",
            AuthorityDomain.email,
            AuthorityCapability.observe,
            TrustMode.read_only,
            "partial_metadata_contract_only",
            ["GET /control-center/sources/readiness"],
            ["repo-local-command:inspect-source-readiness-metadata-contracts"],
            "Read-only mode may show safe metadata contract refs; live account adapters remain unsupported.",
            unsupported_adapter_refs=[
                "adapter-ref:email-live-fetch:not-implemented",
                "adapter-ref:calendar-live-fetch:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:source-readiness-calendar-metadata",
            "Calendar metadata readiness",
            AuthorityDomain.calendar,
            AuthorityCapability.observe,
            TrustMode.read_only,
            "partial_metadata_contract_only",
            ["GET /control-center/sources/readiness"],
            ["repo-local-command:inspect-source-readiness-metadata-contracts"],
            (
                "Calendar authority is limited to safe readiness contract refs; "
                "live calendar fetch, event creation, updates, deletion, and "
                "invites remain unsupported."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:calendar-live-fetch:not-implemented",
                "adapter-ref:calendar-live-write:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:connector-write-low-risk",
            "Connector low-risk send/write adapter",
            AuthorityDomain.email,
            AuthorityCapability.send,
            TrustMode.full_machine_access_session,
            "planned_unsupported_adapter",
            ["connector-lane-ref:low-risk-send-write-exact-approved"],
            ["scripts/dev/uaa_runtime.py inspect-authority-state"],
            (
                "Connector send/write is a known Email/send authority capability, "
                "but live account binding, outbound send, retry, replay, and "
                "compensating-action adapters are not implemented."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:email-live-send:not-implemented",
                "adapter-ref:connector-write-replay:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:messages-live-send-adapter",
            "Messages send adapter",
            AuthorityDomain.messages,
            AuthorityCapability.send,
            TrustMode.delegated_mission_autonomous_window,
            "planned_unsupported_adapter",
            ["GET /api/runtime/authority-state"],
            ["scripts/dev/uaa_runtime.py inspect-authority-state"],
            (
                "Messages send authority is modeled for future missions, but no "
                "iMessage/SMS adapter, account binding, send, archive, or delete "
                "execution is implemented."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:messages-live-send:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:web-evidence-product-slice",
            "Web evidence product slice",
            AuthorityDomain.browser,
            AuthorityCapability.read,
            TrustMode.read_only,
            "implemented_authority_lease_required_gateway_https_get",
            ["POST /control-center/web-evidence/attach"],
            ["scripts/dev/uaa_founder_loop.py attach-web-evidence"],
            (
                "Requires Read-only mode with Browser read AuthorityLease scope, "
                "configured host allowlist, WebAccessGateway HTTPS GET only, bounded "
                "redacted preview, safe refs, and audit/receipt refs; browser actions, "
                "auth/session state, downloads/uploads, mutation methods, provider/model "
                "calls, memory writes, and production authority remain denied."
            ),
        ),
        _mapping(
            "lane-ref:browser-action-adapter",
            "Browser action adapter",
            AuthorityDomain.browser,
            AuthorityCapability.click,
            TrustMode.delegated_mission_autonomous_window,
            "planned_unsupported_adapter",
            ["GET /api/runtime/authority-state"],
            ["scripts/dev/uaa_runtime.py inspect-authority-state"],
            (
                "Browser click and form authority is modeled for delegated missions, "
                "but browser sessions, auth state, clicks, forms, uploads, "
                "downloads, and mutations remain unsupported."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:browser-execution:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:browser-low-risk-action",
            "Browser low-risk action adapter",
            AuthorityDomain.browser,
            AuthorityCapability.click,
            TrustMode.full_machine_access_session,
            "planned_unsupported_adapter",
            ["browser-lane-ref:low-risk-click-exact-approved"],
            ["scripts/dev/uaa_runtime.py inspect-authority-state"],
            (
                "Low-risk browser click authority is a known Browser/click "
                "capability, but browser sessions, page binding, dry-run replay, "
                "clicks, forms, downloads, uploads, and auth state are unsupported."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:browser-low-risk-click:not-implemented",
                "adapter-ref:browser-session-binding:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:provider-credential-validation",
            "Provider credential validation",
            AuthorityDomain.provider_model_calls,
            AuthorityCapability.execute,
            TrustMode.full_machine_access_session,
            "implemented_exact_lease_required_non_invoking_validation",
            ["POST /control-center/providers/credentials/validate"],
            ["scripts/inspect_provider_credential_validation_lane.py"],
            (
                "Requires Full machine access with provider_model_calls/execute "
                "AuthorityLease scope plus exact approval, transient credential "
                "handling, idempotency, redacted receipts, and safe-disable refs; "
                "no model invocation, provider SDK authority, billing authority, "
                "or payload persistence is granted."
            ),
        ),
        _mapping(
            "lane-ref:runtime-local-model-loopback-call",
            "Local loopback model call",
            AuthorityDomain.provider_model_calls,
            AuthorityCapability.execute,
            TrustMode.full_machine_access_session,
            "implemented_exact_lease_required_local_loopback",
            ["POST /api/runtime/local-model/call"],
            ["repo-local-command:uaa-runtime-local-model-call"],
            (
                "Requires Full machine access with provider_model_calls/execute "
                "AuthorityLease scope before local loopback model runtime can run; "
                "model output remains an untrusted proposal, and remote provider "
                "SDK calls, tools/functions, streaming, memory/file writes, connector "
                "writes, browser automation, and production authority remain denied."
            ),
        ),
        _mapping(
            "lane-ref:provider-tiny-exact-approved-invocation",
            "Tiny exact-approved provider invocation",
            AuthorityDomain.provider_model_calls,
            AuthorityCapability.execute,
            TrustMode.full_machine_access_session,
            "implemented_exact_lease_required_provider_cost_governed",
            ["POST /control-center/providers/exact-approved-lanes/tiny"],
            ["scripts/inspect_tiny_provider_invocation_lane.py"],
            (
                "Requires Full machine access with provider_model_calls/execute "
                "AuthorityLease scope plus exact provider/model/policy/cost approval, "
                "idempotency, redacted receipts, and safe-disable refs; no broad "
                "provider router, autonomous calls, billing authority, or payload "
                "persistence is granted."
            ),
        ),
        _mapping(
            "lane-ref:browser-shopping-mission",
            "Browser ticket purchase mission",
            AuthorityDomain.shopping_payments,
            AuthorityCapability.purchase_under_budget,
            TrustMode.delegated_mission_autonomous_window,
            "planned_unsupported_adapter",
            ["GET /api/runtime/authority-state"],
            ["repo-local-command:uaa-runtime-inspect-authority-state"],
            "Requires Delegated mission with Browser and Shopping domains, budget constraints, receipts, and implemented adapters.",
            unsupported_adapter_refs=[
                "adapter-ref:browser-execution:not-implemented",
                "adapter-ref:shopping-payment:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:home-assistant-control-adapter",
            "Home Assistant control adapter",
            AuthorityDomain.home_assistant,
            AuthorityCapability.write,
            TrustMode.delegated_mission_autonomous_window,
            "planned_unsupported_adapter",
            ["GET /api/runtime/authority-state"],
            ["scripts/dev/uaa_runtime.py inspect-authority-state"],
            (
                "Home Assistant control is modeled as a governed domain, but no "
                "device/entity read or write adapter is implemented."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:home-assistant-control:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:background-autonomy-scoped",
            "Scoped background work session",
            AuthorityDomain.apps,
            AuthorityCapability.execute,
            TrustMode.delegated_mission_autonomous_window,
            "planned_unsupported_adapter",
            [
                "GET /api/runtime/background-jobs",
                "GET /api/runtime/authority-state",
                "autonomy-lane-ref:scoped-background-work-session",
            ],
            [
                "repo-local-command:uaa-runtime-inspect-background-jobs",
                "scripts/dev/uaa_runtime.py inspect-authority-state",
            ],
            (
                "Scoped background autonomy is a known delegated Apps/execute "
                "capability, but worker runtime, queue supervisor, checkpoints, "
                "heartbeats, cancellation, replay, and budget enforcement adapters "
                "are not implemented."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:background-worker-runtime:not-implemented",
                "adapter-ref:background-supervisor:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-subagent-isolation-live-dispatch",
            "Runtime subagent live dispatch",
            AuthorityDomain.apps,
            AuthorityCapability.execute,
            TrustMode.delegated_mission_autonomous_window,
            "planned_unsupported_adapter",
            ["GET /api/runtime/subagent-isolation"],
            ["repo-local-command:uaa-runtime-inspect-subagent-isolation"],
            (
                "Subagent live dispatch is modeled as delegated Apps/execute "
                "authority, but no live subagent dispatch, tool-sharing, "
                "cross-agent memory transfer, budgeted fanout, checkpoint, "
                "cancellation, or receipted worker adapter is implemented."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:subagent-live-dispatch:not-implemented",
                "adapter-ref:subagent-tool-sharing:not-implemented",
                "adapter-ref:subagent-memory-transfer:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:runtime-lsp-diagnostics-evidence",
            "Runtime LSP diagnostics evidence",
            AuthorityDomain.workspace,
            AuthorityCapability.read,
            TrustMode.full_local_workspace_session,
            "planned_unsupported_adapter",
            ["GET /api/runtime/lsp-diagnostics"],
            ["repo-local-command:uaa-runtime-inspect-lsp-diagnostics"],
            (
                "Semantic diagnostics are modeled as Full local workspace "
                "read authority, but no allowlisted language-server launch, "
                "cwd jail, file-read adapter, dependency install guard, "
                "timeout, redacted diagnostic extraction, or diagnostic "
                "receipt adapter is implemented."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:lsp-server-launch:not-implemented",
                "adapter-ref:lsp-file-read:not-implemented",
                "adapter-ref:lsp-diagnostic-extraction:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:cloud-production-deploy-adapter",
            "Cloud production deploy adapter",
            AuthorityDomain.cloud_production,
            AuthorityCapability.deploy,
            TrustMode.full_machine_access_session,
            "planned_unsupported_adapter",
            ["GET /api/runtime/authority-state"],
            ["scripts/dev/uaa_runtime.py inspect-authority-state"],
            (
                "Cloud production deploy authority is a known domain, but deploy, "
                "configuration mutation, remote execution, and rollback execution "
                "adapters remain unsupported."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:cloud-production-deploy:not-implemented",
            ],
        ),
        _mapping(
            "lane-ref:production-authority-gate",
            "Production authority gate",
            AuthorityDomain.cloud_production,
            AuthorityCapability.deploy,
            TrustMode.delegated_mission_autonomous_window,
            "planned_unsupported_adapter",
            ["production-lane-ref:authority-readiness-review"],
            ["scripts/dev/uaa_runtime.py inspect-authority-state"],
            (
                "Production deployment is a known Cloud production/deploy "
                "authority capability, but go-live, release, remote execution, "
                "environment mutation, and rollback execution adapters remain "
                "unsupported."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:production-go-live:not-implemented",
                "adapter-ref:production-rollback-execution:not-implemented",
            ],
        ),
    ]

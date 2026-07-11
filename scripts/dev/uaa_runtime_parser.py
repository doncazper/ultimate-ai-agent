from __future__ import annotations

import argparse
from collections.abc import Mapping
from typing import Any


def build_parser(runtime_symbols: Mapping[str, Any]) -> argparse.ArgumentParser:
    parser_globals = globals()
    parser_globals.update(
        {
            name: value
            for name, value in runtime_symbols.items()
            if name != "build_parser" and not (name.startswith("__") and name.endswith("__"))
        }
    )
    parser = argparse.ArgumentParser(
        prog="uaa_runtime",
        description="Inspect governed runtime pilot state through safe refs.",
    )
    parser.add_argument(
        "--state-dir",
        help="Use an explicit local runtime state directory; the value is not echoed.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status", help="Inspect governed runtime status.")
    status.add_argument("--json", action="store_true", help="Emit safe JSON.")
    status.set_defaults(func=_status)

    capabilities = subparsers.add_parser(
        "capabilities",
        help="Inspect governed runtime capabilities.",
    )
    capabilities.add_argument("--json", action="store_true", help="Emit safe JSON.")
    capabilities.set_defaults(func=_capabilities)

    capability_availability = subparsers.add_parser(
        "capability-availability",
        help="Inspect backend-owned capability availability without granting authority.",
    )
    capability_availability.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe capability availability read model as JSON.",
    )
    capability_availability.set_defaults(func=_capability_availability)

    command = subparsers.add_parser(
        "command",
        help="Run governed RuntimeGateway command capabilities.",
    )
    command_subparsers = command.add_subparsers(dest="runtime_command", required=True)
    command_run = command_subparsers.add_parser(
        "run",
        help="Run an exact allowlisted RuntimeGateway command with receipts.",
    )
    command_run.add_argument(
        "intent",
        choices=[intent.value for intent in RuntimeCommandIntent],
        help="Allowlisted RuntimeGateway command intent.",
    )
    command_run.add_argument(
        "--profile",
        default="local-runtime",
        choices=["local-runtime", "operator-approved"],
        help="Requested runtime profile.",
    )
    command_run.add_argument(
        "--mission-ref",
        default=None,
        help="Safe mission ref for mission-scoped authority evaluation.",
    )
    command_run.add_argument(
        "--target-ref",
        action="append",
        help="Safe target ref included in the command request scope.",
    )
    command_run.add_argument(
        "--metadata-ref",
        action="append",
        help="Safe metadata ref included in the command request.",
    )
    command_run.add_argument(
        "--idempotency-ref",
        required=True,
        help="Safe idempotency ref for the command run.",
    )
    command_run.add_argument(
        "--summary",
        required=True,
        help="Safe bounded command summary.",
    )
    command_run.add_argument(
        "--timeout-seconds",
        type=float,
        default=5.0,
        help="Bounded command timeout.",
    )
    command_run.add_argument(
        "--output-byte-limit",
        type=int,
        default=4096,
        help="Bounded output byte limit for redacted summary generation.",
    )
    command_run.add_argument("--json", action="store_true", help="Emit safe JSON.")
    command_run.set_defaults(func=_command_run)

    authority_profile = subparsers.add_parser(
        "authority-profile",
        help="Inspect the Governed Product Pilot authority profile.",
    )
    authority_profile.add_argument(
        "--json", action="store_true", help="Emit safe JSON."
    )
    authority_profile.set_defaults(func=_authority_profile)

    authority_state = subparsers.add_parser(
        "inspect-authority-state",
        help="Inspect AuthorityLease V1 modes, domains, leases, and decisions.",
    )
    authority_state.add_argument("--json", action="store_true", help="Emit safe JSON.")
    authority_state.add_argument(
        "--summary",
        action="store_true",
        help="Print a compact operator-readable authority summary before detailed refs.",
    )
    authority_state.set_defaults(func=_inspect_authority_state)

    authority_lane_catalog = subparsers.add_parser(
        "inspect-authority-lane-catalog",
        help="Inspect Authority Lane Catalog V1 without execution.",
    )
    authority_lane_catalog.add_argument(
        "--json", action="store_true", help="Emit safe JSON."
    )
    authority_lane_catalog.set_defaults(func=_inspect_authority_lane_catalog)

    authority_domain_readiness = subparsers.add_parser(
        "inspect-authority-domain-readiness",
        help="Inspect AuthorityLease domain readiness without execution.",
    )
    authority_domain_readiness.add_argument(
        "--json", action="store_true", help="Emit safe JSON."
    )
    authority_domain_readiness.set_defaults(func=_inspect_authority_domain_readiness)

    authority_preview = subparsers.add_parser(
        "preview-authority-decision",
        help="Preview an AuthorityLease policy decision without execution.",
    )
    authority_preview.add_argument(
        "--action-ref", required=True, help="Safe action ref."
    )
    authority_preview.add_argument(
        "--domain",
        required=True,
        choices=[domain.value for domain in AuthorityDomain],
        help="Authority domain to evaluate.",
    )
    authority_preview.add_argument(
        "--capability",
        required=True,
        choices=[capability.value for capability in AuthorityCapability],
        help="Authority capability to evaluate.",
    )
    authority_preview.add_argument(
        "--summary",
        required=True,
        help="Safe bounded action summary.",
    )
    authority_preview.add_argument(
        "--resource-ref", action="append", help="Safe resource ref."
    )
    authority_preview.add_argument("--route-ref", default=None, help="Route ref.")
    authority_preview.add_argument(
        "--capability-ref",
        default=None,
        help="Authority capability ref for the previewed action.",
    )
    authority_preview.add_argument(
        "--lane-ref",
        default=None,
        help="Legacy lane ref compatibility alias; prefer --capability-ref.",
    )
    authority_preview.add_argument("--adapter-ref", default=None, help="Adapter ref.")
    authority_preview.add_argument(
        "--requested-mode",
        default=None,
        choices=[mode.value for mode in TrustMode],
        help="Requested trust mode for operator copy.",
    )
    authority_preview.add_argument(
        "--draft-fallback-available",
        action="store_true",
        help="Return degrade_to_draft when authority is absent.",
    )
    authority_preview.add_argument(
        "--unsupported-adapter",
        action="store_true",
        help="Mark the requested adapter as unsupported.",
    )
    authority_preview.add_argument(
        "--kill-switch-engaged",
        action="store_true",
        help="Simulate an engaged kill switch.",
    )
    authority_preview.add_argument(
        "--json", action="store_true", help="Emit safe JSON."
    )
    authority_preview.set_defaults(func=_preview_authority_decision)

    mission_plan = subparsers.add_parser(
        "plan-authority-mission",
        help="Plan a mission-scoped AuthorityLease without execution.",
    )
    mission_plan.add_argument("--mission-ref", required=True, help="Safe mission ref.")
    mission_plan.add_argument(
        "--mode",
        default=TrustMode.delegated_mission_autonomous_window.value,
        choices=[mode.value for mode in TrustMode],
        help="Requested trust mode for the mission lease.",
    )
    mission_plan.add_argument(
        "--domain",
        action="append",
        help=(
            "Domain capabilities in domain:capability,capability form. "
            "Omit to preview the mode's implemented default mission scope."
        ),
    )
    mission_plan.add_argument(
        "--reason-ref",
        default="reason-ref:authority-mission-plan-cli",
        help="Safe decision reason ref for the issue draft.",
    )
    mission_plan.add_argument(
        "--duration-minutes",
        type=int,
        default=120,
        help="Mission lease duration in minutes.",
    )
    mission_plan.add_argument(
        "--summary",
        required=True,
        help="Safe bounded mission summary.",
    )
    mission_plan.add_argument("--json", action="store_true", help="Emit safe JSON.")
    mission_plan.set_defaults(func=_plan_authority_mission)

    select_authority = subparsers.add_parser(
        "select-authority-mode",
        help="Issue a session-scoped AuthorityLease for implemented domains.",
    )
    select_authority.add_argument(
        "--mode",
        required=True,
        choices=[mode.value for mode in TrustMode],
        help="Trust mode to request.",
    )
    select_authority.add_argument(
        "--domain",
        action="append",
        help=(
            "Domain capabilities in domain:capability,capability form; omit to "
            "use the backend AuthorityLease mode default scope."
        ),
    )
    select_authority.add_argument(
        "--scope",
        default="session",
        choices=["session", "mission"],
        help="Lease scope.",
    )
    select_authority.add_argument(
        "--reason-ref",
        required=True,
        help="Safe decision reason ref.",
    )
    select_authority.add_argument(
        "--idempotency-ref",
        required=True,
        help="Safe idempotency ref.",
    )
    select_authority.add_argument(
        "--duration-minutes",
        type=int,
        default=60,
        help="Lease duration in minutes.",
    )
    select_authority.add_argument(
        "--mission-ref",
        default=None,
        help="Mission ref when requesting a mission-scoped lease.",
    )
    select_authority.add_argument(
        "--approval-ref",
        default=None,
        help="Safe LocalApprovalAuthority approval ref for authority-increasing leases.",
    )
    select_authority.add_argument(
        "--approve",
        action="store_true",
        help=(
            "Capture an exact local operator approval grant before issuing an "
            "authority-increasing lease."
        ),
    )
    select_authority.add_argument(
        "--approved-by-actor-ref",
        default="operator-ref:local-cli-user",
        help="Safe operator actor ref used when --approve captures the exact grant.",
    )
    select_authority.add_argument(
        "--approval-grant-json",
        action="append",
        help=(
            "Redacted ApprovalGrant JSON used only for exact local validation; "
            "not persisted in authority receipts."
        ),
    )
    select_authority.add_argument(
        "--summary",
        required=True,
        help="Safe bounded operator summary.",
    )
    select_authority.add_argument("--json", action="store_true", help="Emit safe JSON.")
    select_authority.set_defaults(func=_select_authority_mode)

    revoke_authority = subparsers.add_parser(
        "revoke-authority-lease",
        help="Revoke an AuthorityLease and emit a safe receipt.",
    )
    revoke_authority.add_argument("--lease-ref", required=True, help="Lease ref.")
    revoke_authority.add_argument(
        "--reason-ref",
        required=True,
        help="Safe decision reason ref.",
    )
    revoke_authority.add_argument(
        "--idempotency-ref",
        required=True,
        help="Safe idempotency ref.",
    )
    revoke_authority.add_argument(
        "--summary",
        required=True,
        help="Safe bounded operator summary.",
    )
    revoke_authority.add_argument("--json", action="store_true", help="Emit safe JSON.")
    revoke_authority.set_defaults(func=_revoke_authority_lease)

    export_evidence = subparsers.add_parser(
        "export-evidence-envelope",
        help="Export a safe portable evidence envelope for offline inspection.",
    )
    export_evidence.add_argument("--json", action="store_true", help="Emit safe JSON.")
    export_evidence.set_defaults(func=_export_evidence_envelope)

    verify_evidence = subparsers.add_parser(
        "verify-evidence-envelope",
        help="Verify a safe portable evidence envelope offline.",
    )
    evidence_source = verify_evidence.add_mutually_exclusive_group(required=True)
    evidence_source.add_argument(
        "--profile",
        action="store_true",
        help="Verify the current governed product pilot profile envelope.",
    )
    evidence_source.add_argument(
        "--input",
        help="Read an envelope JSON file without echoing the local path.",
    )
    verify_evidence.add_argument("--json", action="store_true", help="Emit safe JSON.")
    verify_evidence.set_defaults(func=_verify_evidence_envelope)

    invocations = subparsers.add_parser(
        "invocations",
        help="Inspect governed runtime invocations.",
    )
    invocation_subparsers = invocations.add_subparsers(
        dest="invocations_command",
        required=True,
    )
    invocations_list = invocation_subparsers.add_parser(
        "list", help="List invocations."
    )
    invocations_list.add_argument("--json", action="store_true", help="Emit safe JSON.")
    invocations_list.set_defaults(func=_invocations_list)
    invocations_show = invocation_subparsers.add_parser("show", help="Show invocation.")
    invocations_show.add_argument("invocation_ref")
    invocations_show.add_argument("--json", action="store_true", help="Emit safe JSON.")
    invocations_show.set_defaults(func=_invocations_show)

    receipts = subparsers.add_parser(
        "receipts",
        help="Inspect governed runtime receipts.",
    )
    receipt_subparsers = receipts.add_subparsers(dest="receipts_command", required=True)
    receipt_show = receipt_subparsers.add_parser("show", help="Show receipt.")
    receipt_show.add_argument("receipt_ref")
    receipt_show.add_argument("--json", action="store_true", help="Emit safe JSON.")
    receipt_show.set_defaults(func=_receipts_show)
    receipt_evidence = receipt_subparsers.add_parser(
        "evidence",
        help="Export signed evidence for a runtime receipt.",
    )
    receipt_evidence.add_argument("receipt_ref")
    receipt_evidence.add_argument("--json", action="store_true", help="Emit safe JSON.")
    receipt_evidence.set_defaults(func=_receipts_evidence)
    receipt_verify_evidence = receipt_subparsers.add_parser(
        "verify-evidence",
        help="Verify a runtime receipt signed evidence envelope without echoing paths.",
    )
    receipt_verify_evidence.add_argument("--input", required=True)
    receipt_verify_evidence.add_argument(
        "--json", action="store_true", help="Emit safe JSON."
    )
    receipt_verify_evidence.set_defaults(func=_receipts_verify_evidence)

    actions = subparsers.add_parser(
        "actions",
        help="Record exact runtime Action Inbox decisions.",
    )
    action_subparsers = actions.add_subparsers(dest="action_decision", required=True)
    for decision in ("approve", "deny"):
        decision_parser = action_subparsers.add_parser(
            decision,
            help=f"Record a runtime Action Inbox {decision} decision.",
        )
        decision_parser.add_argument(
            "approval_selector_ref",
            help=(
                "Approval or invocation safe ref used only to select the exact "
                "backend-owned Action Inbox envelope."
            ),
        )
        decision_parser.add_argument(
            "--idempotency-ref",
            default=None,
            help="Safe idempotency ref for the decision.",
        )
        decision_parser.add_argument(
            "--confirm-exact-runtime-action",
            action="store_true",
            help=(
                "Required for approve after reviewing the exact command "
                "preflight. Approval records a decision only; execution still "
                "requires a RuntimeGateway execute request with active "
                "AuthorityLease scope."
            ),
        )
        decision_parser.add_argument(
            "--json", action="store_true", help="Emit safe JSON."
        )
        decision_parser.set_defaults(func=_action_decision)

    safe_disable = subparsers.add_parser(
        "safe-disable",
        help="Record governed runtime safe-disable posture.",
    )
    safe_disable.add_argument(
        "--idempotency-ref",
        default="idempotency-ref:governed-runtime-cli-safe-disable",
        help="Safe idempotency ref for safe-disable.",
    )
    safe_disable.add_argument(
        "--reason-ref",
        default="reason-ref:governed-runtime-cli-safe-disable",
        help="Safe reason ref for safe-disable.",
    )
    safe_disable.add_argument("--json", action="store_true", help="Emit safe JSON.")
    safe_disable.set_defaults(func=_safe_disable)

    chain = subparsers.add_parser(
        "inspect-turn-run-approval-chain",
        help="Inspect the canonical Turn -> Durable Run -> Approval chain read model.",
    )
    chain.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref read model as JSON for automation.",
    )
    chain.set_defaults(func=_inspect_turn_run_approval_chain)

    staged = subparsers.add_parser(
        "inspect-staged-orchestration",
        help="Inspect the no-effect staged orchestration engine read model.",
    )
    staged.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref staged orchestration read model as JSON.",
    )
    staged.set_defaults(func=_inspect_staged_orchestration)

    role_provider = subparsers.add_parser(
        "inspect-role-provider-evidence",
        help="Inspect advisory role-based model/provider selection evidence.",
    )
    role_provider.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref role evidence read model as JSON.",
    )
    role_provider.set_defaults(func=_inspect_role_provider_evidence)

    delegation = subparsers.add_parser(
        "inspect-delegation-adapter",
        help="Inspect the Hermes runtime delegation adapter readiness contract.",
    )
    delegation.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref delegation adapter read model as JSON.",
    )
    delegation.set_defaults(func=_inspect_delegation_adapter)

    interface_mode = subparsers.add_parser(
        "inspect-interface-mode",
        help="Inspect runtime interface mode over Hermes without UAA agent execution.",
    )
    interface_mode.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref runtime interface mode read model as JSON.",
    )
    interface_mode.set_defaults(func=_inspect_interface_mode)

    hermes_context_pack = subparsers.add_parser(
        "inspect-hermes-context-pack",
        help="Inspect the curated Hermes context pack without exposing raw records.",
    )
    hermes_context_pack.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref Hermes context pack read model as JSON.",
    )
    hermes_context_pack.set_defaults(func=_inspect_hermes_context_pack)

    hermes_chat = subparsers.add_parser(
        "hermes-chat",
        help="Submit an exact governed Hermes chat request with redacted receipt.",
    )
    hermes_chat.add_argument(
        "--mode",
        choices=("shell_guarded", "operator_override"),
        required=True,
        help="Interface mode for the explicit operator-submitted Hermes chat.",
    )
    hermes_chat.add_argument(
        "--query",
        required=True,
        help="Transient Hermes query; it is hashed only and not persisted.",
    )
    hermes_chat.add_argument(
        "--mission-ref",
        default=None,
        help="Optional mission ref for mission-scoped AuthorityLease matching.",
    )
    hermes_chat.add_argument(
        "--idempotency-ref",
        default="idempotency-ref:hermes-chat-cli",
        help="Safe idempotency ref for the Hermes chat receipt.",
    )
    hermes_chat.add_argument(
        "--json",
        action="store_true",
        help="Emit the redacted Hermes chat receipt as JSON.",
    )
    hermes_chat.set_defaults(func=_hermes_chat)

    capability_discovery = subparsers.add_parser(
        "inspect-capability-discovery",
        help="Inspect runtime capability discovery posture without live runtime calls.",
    )
    capability_discovery.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref capability discovery read model as JSON.",
    )
    capability_discovery.set_defaults(func=_inspect_capability_discovery)

    tool_registry = subparsers.add_parser(
        "inspect-tool-registry",
        help="Inspect runtime tool registry availability without invocation.",
    )
    tool_registry.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref runtime tool registry read model as JSON.",
    )
    tool_registry.set_defaults(func=_inspect_tool_registry)

    virtual_provider_moa = subparsers.add_parser(
        "inspect-virtual-provider-moa",
        help="Inspect virtual multi-agent provider presets without fan-out.",
    )
    virtual_provider_moa.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref virtual provider preset read model as JSON.",
    )
    virtual_provider_moa.set_defaults(func=_inspect_virtual_provider_moa)

    usage_cost_analytics = subparsers.add_parser(
        "inspect-usage-cost-analytics",
        help="Inspect redacted runtime usage and cost accounting posture.",
    )
    usage_cost_analytics.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref runtime usage and cost read model as JSON.",
    )
    usage_cost_analytics.set_defaults(func=_inspect_usage_cost_analytics)

    prompt_stability_tiers = subparsers.add_parser(
        "inspect-prompt-stability-tiers",
        help="Inspect read-only prompt/input stability tier posture.",
    )
    prompt_stability_tiers.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref prompt stability tier read model as JSON.",
    )
    prompt_stability_tiers.set_defaults(func=_inspect_prompt_stability_tiers)

    context_budget_pressure = subparsers.add_parser(
        "inspect-context-budget-pressure",
        help="Inspect read-only context budget pressure and compression posture.",
    )
    context_budget_pressure.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref context budget pressure read model as JSON.",
    )
    context_budget_pressure.set_defaults(func=_inspect_context_budget_pressure)

    hardline_command_blocklist = subparsers.add_parser(
        "inspect-hardline-command-blocklist",
        help="Inspect the read-only non-overridable command deny floor.",
    )
    hardline_command_blocklist.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref hardline command blocklist read model as JSON.",
    )
    hardline_command_blocklist.set_defaults(func=_inspect_hardline_command_blocklist)

    managed_scope_policy = subparsers.add_parser(
        "inspect-managed-scope-policy",
        help="Inspect read-only local managed scope policy posture.",
    )
    managed_scope_policy.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref managed scope policy read model as JSON.",
    )
    managed_scope_policy.set_defaults(func=_inspect_managed_scope_policy)

    doctor_diagnostics = subparsers.add_parser(
        "inspect-doctor-diagnostics",
        help="Inspect redacted local runtime doctor diagnostics posture.",
    )
    doctor_diagnostics.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref runtime doctor diagnostics read model as JSON.",
    )
    doctor_diagnostics.set_defaults(func=_inspect_doctor_diagnostics)

    session_continuity = subparsers.add_parser(
        "inspect-session-continuity",
        help="Inspect read-only multi-surface runtime session continuity posture.",
    )
    session_continuity.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref session continuity read model as JSON.",
    )
    session_continuity.set_defaults(func=_inspect_session_continuity)

    mcp_catalog_filtering = subparsers.add_parser(
        "inspect-mcp-catalog-filtering",
        help="Inspect MCP catalog metadata filters without installing or invoking tools.",
    )
    mcp_catalog_filtering.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref MCP catalog filtering read model as JSON.",
    )
    mcp_catalog_filtering.set_defaults(func=_inspect_mcp_catalog_filtering)

    background_jobs = subparsers.add_parser(
        "inspect-background-jobs",
        help="Inspect durable background job proposals without scheduler execution.",
    )
    background_jobs.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref background job posture as JSON.",
    )
    background_jobs.set_defaults(func=_inspect_background_jobs)

    subagent_isolation = subparsers.add_parser(
        "inspect-subagent-isolation",
        help="Inspect subagent role isolation posture without live dispatch.",
    )
    subagent_isolation.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref subagent isolation posture as JSON.",
    )
    subagent_isolation.set_defaults(func=_inspect_subagent_isolation)

    worktree_per_agent = subparsers.add_parser(
        "inspect-worktree-per-agent",
        help="Inspect worktree-per-agent posture without Git or file mutation.",
    )
    worktree_per_agent.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref worktree-per-agent posture as JSON.",
    )
    worktree_per_agent.set_defaults(func=_inspect_worktree_per_agent)

    lsp_diagnostics = subparsers.add_parser(
        "inspect-lsp-diagnostics",
        help="Inspect semantic diagnostic evidence posture without LSP execution.",
    )
    lsp_diagnostics.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref LSP diagnostics posture as JSON.",
    )
    lsp_diagnostics.set_defaults(func=_inspect_lsp_diagnostics)

    preview_rail = subparsers.add_parser(
        "inspect-preview-rail",
        help="Inspect safe-ref preview rail posture without rendering raw payloads.",
    )
    preview_rail.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref preview rail posture as JSON.",
    )
    preview_rail.set_defaults(func=_inspect_preview_rail)

    slash_command_registry = subparsers.add_parser(
        "inspect-slash-command-registry",
        help="Inspect governed slash command metadata without execution.",
    )
    slash_command_registry.add_argument(
        "--json",
        action="store_true",
        help="Emit the governed slash command registry as JSON.",
    )
    slash_command_registry.set_defaults(func=_inspect_slash_command_registry)

    interrupt_redirect = subparsers.add_parser(
        "inspect-interrupt-redirect",
        help="Inspect run-control interrupt and redirect posture without mutation.",
    )
    interrupt_redirect.add_argument(
        "--json",
        action="store_true",
        help="Emit the interrupt/redirect run-control posture as JSON.",
    )
    interrupt_redirect.set_defaults(func=_inspect_interrupt_redirect)

    logging_profile = subparsers.add_parser(
        "inspect-logging-profile",
        help="Inspect governed logging profile posture without toggling verbosity.",
    )
    logging_profile.add_argument(
        "--json",
        action="store_true",
        help="Emit the governed logging profile posture as JSON.",
    )
    logging_profile.set_defaults(func=_inspect_logging_profile)

    result_classification = subparsers.add_parser(
        "inspect-result-classification",
        help="Inspect runtime result taxonomy without promoting output authority.",
    )
    result_classification.add_argument(
        "--json",
        action="store_true",
        help="Emit the runtime result taxonomy as JSON.",
    )
    result_classification.set_defaults(func=_inspect_result_classification)

    voice_media_posture = subparsers.add_parser(
        "inspect-voice-media-posture",
        help="Inspect voice/media runtime posture without media access or generation.",
    )
    voice_media_posture.add_argument(
        "--json",
        action="store_true",
        help="Emit the runtime voice/media posture as JSON.",
    )
    voice_media_posture.set_defaults(func=_inspect_voice_media_posture)

    messaging_gateway_posture = subparsers.add_parser(
        "inspect-messaging-gateway-posture",
        help="Inspect messaging gateway readiness without connector runtime.",
    )
    messaging_gateway_posture.add_argument(
        "--json",
        action="store_true",
        help="Emit the messaging gateway posture as JSON.",
    )
    messaging_gateway_posture.set_defaults(func=_inspect_messaging_gateway_posture)

    remote_execution_posture = subparsers.add_parser(
        "inspect-remote-execution-posture",
        help="Inspect execution backend posture without remote execution.",
    )
    remote_execution_posture.add_argument(
        "--json",
        action="store_true",
        help="Emit the remote execution backend posture as JSON.",
    )
    remote_execution_posture.set_defaults(func=_inspect_remote_execution_posture)

    plugin_metadata_posture = subparsers.add_parser(
        "inspect-plugin-metadata-posture",
        help="Inspect plugin architecture metadata without runtime import.",
    )
    plugin_metadata_posture.add_argument(
        "--json",
        action="store_true",
        help="Emit the plugin metadata posture as JSON.",
    )
    plugin_metadata_posture.set_defaults(func=_inspect_plugin_metadata_posture)

    skill_marketplace_posture = subparsers.add_parser(
        "inspect-skill-marketplace-posture",
        help="Inspect external skill marketplace adoption posture without execution.",
    )
    skill_marketplace_posture.add_argument(
        "--json",
        action="store_true",
        help="Emit the skill marketplace posture as JSON.",
    )
    skill_marketplace_posture.set_defaults(func=_inspect_skill_marketplace_posture)

    session_search = subparsers.add_parser(
        "inspect-session-search",
        help="Inspect safe-ref session/run search separate from durable memory.",
    )
    session_search.add_argument("--query-ref", default=None)
    session_search.add_argument("--limit", type=int, default=20)
    session_search.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref session search read model as JSON.",
    )
    session_search.set_defaults(func=_inspect_session_search)

    session_lineage = subparsers.add_parser(
        "inspect-session-lineage",
        help="Inspect safe-ref session lineage and fork posture without dispatch.",
    )
    session_lineage.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref session lineage read model as JSON.",
    )
    session_lineage.set_defaults(func=_inspect_session_lineage)

    context_references = subparsers.add_parser(
        "inspect-context-references",
        help="Inspect governed context reference preview without live fetch or injection.",
    )
    context_references.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref context reference read model as JSON.",
    )
    context_references.set_defaults(func=_inspect_context_references)

    checkpoint_rollback = subparsers.add_parser(
        "inspect-checkpoint-rollback",
        help="Inspect checkpoint and rollback posture without executing rollback.",
    )
    checkpoint_rollback.add_argument(
        "--json",
        action="store_true",
        help="Emit checkpoint and rollback posture as JSON.",
    )
    checkpoint_rollback.set_defaults(func=_inspect_checkpoint_rollback)

    run_events = subparsers.add_parser(
        "inspect-run-events",
        help="Inspect runtime run/event/approval-wait posture without mutation.",
    )
    run_events.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref runtime run events read model as JSON.",
    )
    run_events.set_defaults(func=_inspect_run_events)

    approval_bridge = subparsers.add_parser(
        "inspect-approval-bridge",
        help="Inspect runtime approval bridge posture without sending decisions.",
    )
    approval_bridge.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref runtime approval bridge read model as JSON.",
    )
    approval_bridge.set_defaults(func=_inspect_approval_bridge)

    streaming_progress = subparsers.add_parser(
        "inspect-streaming-progress",
        help="Inspect redacted runtime streaming progress previews without live transport.",
    )
    streaming_progress.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref runtime streaming progress read model as JSON.",
    )
    streaming_progress.set_defaults(func=_inspect_streaming_progress)

    profiles = subparsers.add_parser(
        "inspect-profiles",
        help="Inspect isolated runtime profile metadata without changing config.",
    )
    profiles.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref runtime profile isolation read model as JSON.",
    )
    profiles.set_defaults(func=_inspect_profiles)

    bridge = subparsers.add_parser(
        "inspect-action-inbox-bridge",
        help="Inspect the runtime Action Inbox execution bridge read model.",
    )
    bridge.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref read model as JSON for automation.",
    )
    bridge.set_defaults(func=_inspect_action_inbox_bridge)

    parity_loop = subparsers.add_parser(
        "inspect-parity-loop",
        help="Inspect the complete runtime parity loop across cockpit, CLI, and API refs.",
    )
    parity_loop.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref parity loop read model as JSON.",
    )
    parity_loop.set_defaults(func=_inspect_parity_loop)
    return parser

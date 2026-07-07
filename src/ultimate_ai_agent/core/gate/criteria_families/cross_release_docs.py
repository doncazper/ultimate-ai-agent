from __future__ import annotations

from typing import Any, Callable

from ultimate_ai_agent.core.gate.enums import FoundationGateCategory


def criteria(build: Callable[..., Any]) -> list[Any]:
    return [
        build(
                    "open_design_governance_docs_present",
                    "Open Design Governance Docs Present",
                    FoundationGateCategory.documentation,
                    "FoundationGateEvaluator.check_open_design_governance_docs_present",
                    "Open Design System and Control Center UI governance docs exist, keep design tooling disabled, define repo-owned source of truth, and protect visual artifacts from secrets.",
                    "Open Design governance docs are missing or imply design tool enablement, design SaaS authority, unsafe visual artifacts, or missing Control Center design links.",
                    "critical",
                ),
        build(
                    "openwebui_ccc_strategy_docs_present",
                    "OpenWebUI CCC Strategy Docs Present",
                    FoundationGateCategory.documentation,
                    "FoundationGateEvaluator.check_openwebui_ccc_strategy_docs_present",
                    "OpenWebUI and CCC strategy docs exist, define OpenWebUI as the chat shell, CCC as the governance/control client family, and keep native clients future-only.",
                    "OpenWebUI/CCC strategy docs are missing or imply OpenWebUI authority bypass, missing Android/macOS/iOS roles, native implementation, sensor access, or native build workflows.",
                    "critical",
                ),
        build(
                    "post_m20_roadmap_projection_present",
                    "Post-M20 Roadmap Projection Present",
                    FoundationGateCategory.documentation,
                    "FoundationGateEvaluator.check_post_m20_roadmap_projection_present",
                    "Post-M20 roadmap projection docs exist, released milestones are marked implemented, future milestone charters remain planned/provisional, and docs do not claim future implementation.",
                    "Post-M20 roadmap projection docs are missing, incomplete, or imply M23-M40 implementation.",
                    "critical",
                ),
        build(
                    "roadmap_milestone_charters_current",
                    "Roadmap Milestone Charters Current",
                    FoundationGateCategory.documentation,
                    "FoundationGateEvaluator.check_roadmap_milestone_charters_current",
                    "Roadmap milestone charter docs exist and resolve M14/M15 sequencing without claiming M14 implementation.",
                    "Roadmap milestone charters are missing or ambiguous.",
                    "critical",
                ),
        build(
                    "documentation_integrity_current",
                    "Documentation Integrity Current",
                    FoundationGateCategory.documentation,
                    "FoundationGateEvaluator.check_documentation_integrity_current",
                    "Documentation index, canonical map, archive entrypoints, active release docs, private mesh docs, mobile planning docs, and active version references are present without unsafe implementation claims.",
                    "Active documentation is missing or claims planned/disabled capabilities are implemented.",
                    "critical",
                ),
        build(
                    "codex_plugin_governance_docs_present",
                    "Codex Plugin Governance Docs Present",
                    FoundationGateCategory.documentation,
                    "FoundationGateEvaluator.check_codex_plugin_governance_docs_present",
                    "Codex plugin inventory, risk policy, canonical governance doc, and enablement backlog are present and keep high-risk plugins disabled/future-only.",
                    "Codex plugin governance docs are missing or imply plugin enablement.",
                    "critical",
                ),
    ]

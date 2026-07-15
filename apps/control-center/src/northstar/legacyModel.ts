import type { IconReference } from "../components/NorthStarIcon";

export const LEGACY_REFERENCE_PREFIX = "/workspace/reference";

export type LegacySurfaceId =
  | "01-today"
  | "02-action-inbox"
  | "03-plans-work-board"
  | "04-trust"
  | "05-evidence-proof"
  | "06-memory"
  | "07-setup"
  | "08-coding"
  | "09-sources-crm-briefing"
  | "10-chat-handoff"
  | "11-start-overview"
  | "12-settings-authority"
  | "13-models"
  | "14-files-context"
  | "15-action-preview"
  | "16-runtime-storage"
  | "17-future-governance"
  | "18-private-trial"
  | "19-operator-loop";

export type LegacyNavPreset = "core" | "setup" | "coding" | "sources" | "chat";

export interface LegacySurfaceDefinition {
  id: LegacySurfaceId;
  number: number;
  label: string;
  title: string;
  subtitle: string;
  activeNav: string;
  icon: IconReference;
  navPreset: LegacyNavPreset;
  path: string;
  render: string;
}

const renderRoot = "docs/design/control_center_north_star/renders";

export const legacySurfaceDefinitions: LegacySurfaceDefinition[] = [
  ["01-today", "Today", "Morning Briefing", "Daily founder loop", "Today", "house", "core", "01_today_command_center.png"],
  ["02-action-inbox", "Action Inbox", "Action Inbox", "Exact approval envelope", "Action Inbox", "inbox", "core", "02_action_inbox_approval_envelope.png"],
  ["03-plans-work-board", "Plans & Work Board", "Q2 Platform Hardening", "Plan outline and governed work board", "Work Board", "table-2", "core", "03_plans_work_board.png"],
  ["04-trust", "Trust", "AuthorityLease Control Center", "Mode, domain, and lease posture", "Trust", "shield-check", "core", "04_trust_authority_lease.png"],
  ["05-evidence-proof", "Evidence & Proof", "Evidence", "Proof detail and receipt ledger", "Evidence", "file-check-2", "core", "05_evidence_proof_receipts.png"],
  ["06-memory", "Memory", "Memory Review", "Recall review and context manifest", "Memory", "brain", "core", "06_memory_review_context_manifest.png"],
  ["07-setup", "Setup", "Setup Assistant & Runtime", "Local readiness and blockers", "Setup", "settings", "setup", "07_setup_runtime_readiness.png"],
  ["08-coding", "Coding", "Governed Code Workbench", "Repo-local proposals, checks, and receipts", "Cockpit", "code-2", "coding", "08_coding_cockpit.png"],
  ["09-sources-crm-briefing", "Sources, CRM & Briefing", "Source Inbox", "Read-only sources and briefing preparation", "Source Inbox", "mail", "sources", "09_source_inbox_crm_briefing_prep.png"],
  ["10-chat-handoff", "Chat & Handoff", "Q2 Roadmap briefing", "Local chat and proposal handoff", "Chat", "message-square", "chat", "10_chat_handoff.png"],
  ["11-start-overview", "Start & Overview", "Start Here", "Setup, route proof, and next step", "Start Here", "home", "core", "11_start_overview_dashboard.png"],
  ["12-settings-authority", "Authority Settings", "Settings", "Authority profiles and controls", "Settings", "settings", "core", "12_settings_authority_profiles.png"],
  ["13-models", "Models", "Models", "Local readiness and provider posture", "Models", "box", "core", "13_models_readiness.png"],
  ["14-files-context", "Files & Context", "File safe-ref inbox", "Redacted review and context proposals", "Files", "folder", "core", "14_files_context_proposals.png"],
  ["15-action-preview", "Action Preview", "Action Preview", "Dry-run, side effects, and preflight", "Action Inbox", "clipboard-check", "core", "15_action_preview_preflight.png"],
  ["16-runtime-storage", "Runtime & Storage", "Runtime", "Health, exact command lanes, and storage", "Runtime", "server", "core", "16_runtime_storage_manual_smoke.png"],
  ["17-future-governance", "Future Governance", "Capability Domains", "Planned and exact-lane requirements", "Remote / Plugins", "workflow", "core", "17_future_domain_governance.png"],
  ["18-private-trial", "Private Trial", "Trial Packet", "Private acceptance ledger", "Trial Packet", "clipboard-list", "core", "18_private_trial_packet.png"],
  ["19-operator-loop", "Operator Loop", "Operator Loop", "Observe, plan, act, prove, remember", "Operator Loop", "refresh-cw", "core", "19_operator_loop.png"],
].map(([id, label, title, subtitle, activeNav, icon, navPreset, render], index) => ({
  id: id as LegacySurfaceId,
  number: index + 1,
  label,
  title,
  subtitle,
  activeNav,
  icon: icon as IconReference,
  navPreset: navPreset as LegacyNavPreset,
  path: `${LEGACY_REFERENCE_PREFIX}/${id}`,
  render: `${renderRoot}/${render}`,
}));

export function isLegacyReferencePath(path: string): boolean {
  return path === LEGACY_REFERENCE_PREFIX || path.startsWith(`${LEGACY_REFERENCE_PREFIX}/`);
}

export function legacySurfaceFromPath(path: string): LegacySurfaceDefinition {
  const segment = path.replace(`${LEGACY_REFERENCE_PREFIX}/`, "").split("/")[0];
  return legacySurfaceDefinitions.find((surface) => surface.id === segment)
    ?? legacySurfaceDefinitions[0];
}

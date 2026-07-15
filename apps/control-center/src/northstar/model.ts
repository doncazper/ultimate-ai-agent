import type { IconReference } from "../components/NorthStarIcon";

export const WORKSPACE_PREFIX = "/workspace";

export type WorkspaceSurfaceId =
  | "today"
  | "communications"
  | "messenger"
  | "work-board"
  | "crm"
  | "calendar"
  | "news"
  | "studio"
  | "knowledge"
  | "activity-trust"
  | "customize"
  | "settings"
  | "developer-tools"
  | "decisions"
  | "onboarding";

export interface WorkspaceNavItem {
  id: WorkspaceSurfaceId;
  label: string;
  icon: IconReference;
  href: string;
  section: "primary" | "supporting" | "utility";
  count?: number;
}

export const workspaceNavItems: WorkspaceNavItem[] = [
  { id: "today", label: "Today", icon: "house", href: `${WORKSPACE_PREFIX}/today`, section: "primary" },
  { id: "communications", label: "Communications", icon: "mail", href: `${WORKSPACE_PREFIX}/communications`, section: "primary", count: 6 },
  { id: "messenger", label: "Messenger", icon: "messages-square", href: `${WORKSPACE_PREFIX}/messenger`, section: "primary", count: 7 },
  { id: "work-board", label: "Work Board", icon: "table-2", href: `${WORKSPACE_PREFIX}/work-board`, section: "primary" },
  { id: "crm", label: "CRM", icon: "users", href: `${WORKSPACE_PREFIX}/crm`, section: "primary" },
  { id: "calendar", label: "Calendar", icon: "calendar-days", href: `${WORKSPACE_PREFIX}/calendar`, section: "primary" },
  { id: "news", label: "News", icon: "newspaper", href: `${WORKSPACE_PREFIX}/news`, section: "primary" },
  { id: "studio", label: "Studio", icon: "sparkles", href: `${WORKSPACE_PREFIX}/studio`, section: "primary" },
  { id: "knowledge", label: "Knowledge", icon: "book-open", href: `${WORKSPACE_PREFIX}/knowledge`, section: "supporting" },
  { id: "activity-trust", label: "Activity & Trust", icon: "shield-check", href: `${WORKSPACE_PREFIX}/activity-trust`, section: "supporting" },
  { id: "customize", label: "Customize", icon: "sliders-horizontal", href: `${WORKSPACE_PREFIX}/customize`, section: "utility" },
  { id: "settings", label: "Settings", icon: "settings", href: `${WORKSPACE_PREFIX}/settings`, section: "utility" },
  { id: "developer-tools", label: "Developer Tools", icon: "code-2", href: `${WORKSPACE_PREFIX}/developer-tools`, section: "utility" },
];

export const workspaceSurfaceLabels: Record<WorkspaceSurfaceId, string> = {
  today: "Today",
  communications: "Communications",
  messenger: "Messenger",
  "work-board": "Work Board",
  crm: "CRM",
  calendar: "Calendar",
  news: "News",
  studio: "Studio",
  knowledge: "Knowledge",
  "activity-trust": "Activity & Trust",
  customize: "Customize",
  settings: "Settings",
  "developer-tools": "Developer Tools",
  decisions: "Review decisions",
  onboarding: "Set up your Control Center",
};

export function isNorthStarPath(path: string): boolean {
  return path === WORKSPACE_PREFIX || path.startsWith(`${WORKSPACE_PREFIX}/`);
}

export function workspaceSurfaceFromPath(path: string): WorkspaceSurfaceId {
  const segment = path.replace(`${WORKSPACE_PREFIX}/`, "").split("/")[0];
  if (segment === "" || segment === WORKSPACE_PREFIX.slice(1)) {
    return "today";
  }
  if (workspaceSurfaceLabels[segment as WorkspaceSurfaceId]) {
    return segment as WorkspaceSurfaceId;
  }
  return "today";
}

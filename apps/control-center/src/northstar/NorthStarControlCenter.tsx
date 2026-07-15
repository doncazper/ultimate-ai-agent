import type { ControlCenterData } from "../api/types";
import { MessengerShell } from "../components/messenger/MessengerShell";
import { NorthStarShell } from "./NorthStarShell";
import { WORKSPACE_PREFIX, workspaceSurfaceFromPath, type WorkspaceSurfaceId } from "./model";
import { CalendarSurface, CommunicationsSurface, CrmSurface, TodaySurface, WorkBoardSurface } from "./PrimarySurfaces";
import { ActivityTrustSurface, CustomizeSurface, DecisionReviewSurface, DeveloperToolsSurface, KnowledgeSurface, NewsSurface, SettingsSurface } from "./SecondarySurfaces";
import { StudioSurface } from "./StudioSurface";
import { OnboardingSurface } from "./OnboardingSurface";
import { LegacyRenderSurface } from "./LegacyRenderSurface";
import { isLegacyReferencePath } from "./legacyModel";
import { Icon } from "./primitives";
import "./northStar.css";

export function NorthStarControlCenter({ activePath, data }: { activePath: string; data: ControlCenterData }) {
  if (isLegacyReferencePath(activePath)) return <LegacyRenderSurface activePath={activePath} data={data} />;
  const surface = workspaceSurfaceFromPath(activePath);
  if (!surface) return <UnknownWorkspaceRoute activePath={activePath} />;
  if (surface === "studio") return <StudioSurface data={data} />;
  if (surface === "messenger") return <MessengerShell />;
  if (surface === "onboarding") return <OnboardingSurface data={data} />;
  return <NorthStarShell activeSurface={surface} data={data}>{renderSurface(surface, data)}</NorthStarShell>;
}

function UnknownWorkspaceRoute({ activePath }: { activePath: string }) {
  return <main className="ns-route-unavailable" role="alert"><Icon name="triangle-alert" size={28} tone="warning" /><h1>Workspace route unavailable</h1><p>No known workspace surface matches this route. No backend state, capability, or authority was inferred.</p><code>{activePath}</code><a className="ns-button primary" href={`${WORKSPACE_PREFIX}/today`}>Open Today</a></main>;
}

function renderSurface(surface: WorkspaceSurfaceId, data: ControlCenterData) {
  switch (surface) {
    case "communications": return <CommunicationsSurface data={data} />;
    case "work-board": return <WorkBoardSurface data={data} />;
    case "crm": return <CrmSurface data={data} />;
    case "calendar": return <CalendarSurface data={data} />;
    case "news": return <NewsSurface data={data} />;
    case "knowledge": return <KnowledgeSurface data={data} />;
    case "activity-trust": return <ActivityTrustSurface data={data} />;
    case "customize": return <CustomizeSurface />;
    case "settings": return <SettingsSurface data={data} />;
    case "developer-tools": return <DeveloperToolsSurface data={data} />;
    case "decisions": return <DecisionReviewSurface data={data} />;
    case "today":
    default: return <TodaySurface data={data} />;
  }
}

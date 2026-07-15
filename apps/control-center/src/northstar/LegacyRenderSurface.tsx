import type { ControlCenterData } from "../api/types";
import {
  LegacyActionInboxSurface,
  LegacyEvidenceProofSurface,
  LegacyPlansWorkBoardSurface,
  LegacyTodaySurface,
  LegacyTrustSurface,
} from "./LegacyCoreSurfaces";
import { LegacyFrame } from "./LegacyFrame";
import {
  LegacyFutureGovernanceSurface,
  LegacyOperatorLoopSurface,
  LegacyPrivateTrialSurface,
  LegacyRuntimeStorageSurface,
} from "./LegacyGovernanceSurfaces";
import { legacySurfaceFromPath, type LegacySurfaceId } from "./legacyModel";
import {
  LegacyActionPreviewSurface,
  LegacyFilesContextSurface,
  LegacyModelsSurface,
  LegacySettingsAuthoritySurface,
  LegacyStartOverviewSurface,
} from "./LegacySystemSurfaces";
import {
  LegacyChatHandoffSurface,
  LegacyCodingSurface,
  LegacyMemorySurface,
  LegacySetupSurface,
  LegacySourcesCrmBriefingSurface,
} from "./LegacyWorkflowSurfaces";
import "./legacySurfaces.css";

export function LegacyRenderSurface({ activePath, data }: { activePath: string; data: ControlCenterData }) {
  const definition = legacySurfaceFromPath(activePath);
  return <LegacyFrame data={data} definition={definition}>{renderLegacySurface(definition.id)}</LegacyFrame>;
}

function renderLegacySurface(surface: LegacySurfaceId) {
  switch (surface) {
    case "02-action-inbox": return <LegacyActionInboxSurface />;
    case "03-plans-work-board": return <LegacyPlansWorkBoardSurface />;
    case "04-trust": return <LegacyTrustSurface />;
    case "05-evidence-proof": return <LegacyEvidenceProofSurface />;
    case "06-memory": return <LegacyMemorySurface />;
    case "07-setup": return <LegacySetupSurface />;
    case "08-coding": return <LegacyCodingSurface />;
    case "09-sources-crm-briefing": return <LegacySourcesCrmBriefingSurface />;
    case "10-chat-handoff": return <LegacyChatHandoffSurface />;
    case "11-start-overview": return <LegacyStartOverviewSurface />;
    case "12-settings-authority": return <LegacySettingsAuthoritySurface />;
    case "13-models": return <LegacyModelsSurface />;
    case "14-files-context": return <LegacyFilesContextSurface />;
    case "15-action-preview": return <LegacyActionPreviewSurface />;
    case "16-runtime-storage": return <LegacyRuntimeStorageSurface />;
    case "17-future-governance": return <LegacyFutureGovernanceSurface />;
    case "18-private-trial": return <LegacyPrivateTrialSurface />;
    case "19-operator-loop": return <LegacyOperatorLoopSurface />;
    case "01-today":
    default: return <LegacyTodaySurface />;
  }
}

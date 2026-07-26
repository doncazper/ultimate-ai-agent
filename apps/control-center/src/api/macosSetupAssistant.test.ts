import { describe, expect, it } from "vitest";
import { mockControlCenterData } from "../mocks/controlCenterData";
import { normalizeMacOSSetupAssistant } from "./macosSetupAssistant";

describe("macOS Setup Assistant normalization provenance", () => {
  it("marks partial backend objects as fallback-derived", () => {
    const normalized = normalizeMacOSSetupAssistant(
      { plan_ref: "setup-plan-ref:partial" },
      mockControlCenterData.macosSetupAssistant,
    );

    expect(normalized.usedFallback).toBe(true);
    expect(normalized.value.steps).toEqual(
      mockControlCenterData.macosSetupAssistant.steps,
    );
  });

  it("marks missing backend payloads as fallback-derived", () => {
    const normalized = normalizeMacOSSetupAssistant(
      undefined,
      mockControlCenterData.macosSetupAssistant,
    );

    expect(normalized.usedFallback).toBe(true);
    expect(normalized.value).toEqual(
      mockControlCenterData.macosSetupAssistant,
    );
  });
});

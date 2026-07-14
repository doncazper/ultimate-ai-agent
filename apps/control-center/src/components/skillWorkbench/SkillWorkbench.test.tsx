import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type {
  RuntimeSkillMarketplaceCatalogEntry,
  RuntimeSkillMarketplacePostureReadModel,
} from "../../api/types";
import { mockControlCenterData } from "../../mocks/controlCenterData";
import { SkillWorkbench } from "./SkillWorkbench";

function entry(
  index: number,
  sourceKind: "clawhub" | "hermes",
): RuntimeSkillMarketplaceCatalogEntry {
  const clawhub = sourceKind === "clawhub";
  const slug = `${sourceKind}-skill-${index}`;
  return {
    skill_ref: `skill-candidate-ref:${sourceKind}:${slug}`,
    source_ref: `source-ref:skill-marketplace:${sourceKind}`,
    source_record_ref: `source-record-ref:${sourceKind}:${slug}`,
    source_kind: sourceKind,
    source_label: clawhub ? "ClawHub" : "Hermes",
    slug,
    display_name: clawhub ? "Source-Ranked Skill" : `Hermes Skill ${index}`,
    safe_summary: clawhub
      ? "A source-ranked metadata record."
      : `Official bundled Hermes metadata record ${index}.`,
    category: clawhub ? "Research" : "Productivity",
    version: "1.0.0",
    license_label: clawhub ? "Not provided" : "MIT",
    source_updated_at: `2026-07-${String(Math.max(1, 13 - index)).padStart(2, "0")}T00:00:00Z`,
    source_rank: clawhub ? 1 : null,
    rank_label: clawhub ? "#1 this week" : "Not provided by source",
    star_count: clawhub ? 42 : null,
    download_count: clawhub ? 1800 : null,
    install_count: clawhub ? 120 : null,
    comment_count: clawhub ? 4 : null,
    average_rating: null,
    rating_count: null,
    source_metadata_only: true,
    review_required: true,
    risk_level: "unknown",
    external_code_imported: false,
    execution_enabled: false,
  };
}

function posture(): RuntimeSkillMarketplacePostureReadModel {
  const entries = [
    entry(1, "clawhub"),
    ...Array.from({ length: 11 }, (_, index) => entry(index + 2, "hermes")),
  ];
  return {
    ...mockControlCenterData.runtimeSkillMarketplacePosture,
    catalog: {
      schema_version: "runtime_skill_marketplace_catalog_snapshot.v1",
      snapshot_ref: "skill-marketplace-catalog-snapshot-ref:test",
      captured_at: "2026-07-13T00:00:00Z",
      sources: [
        {
          source_ref: "source-ref:skill-marketplace:clawhub",
          source_kind: "clawhub",
          display_label: "ClawHub",
          captured_at: "2026-07-13T00:00:00Z",
          source_version_ref: "source-version-ref:clawhub:test",
          record_count: 1,
          rank_signal: "weekly_trending",
          score_signal: "stars",
          live_fetch_performed: false,
          raw_payload_persisted: false,
        },
        {
          source_ref: "source-ref:skill-marketplace:hermes",
          source_kind: "hermes",
          display_label: "Hermes",
          captured_at: "2026-07-13T00:00:00Z",
          source_version_ref: "source-version-ref:hermes:test",
          record_count: 11,
          rank_signal: "not_provided",
          score_signal: "not_provided",
          live_fetch_performed: false,
          raw_payload_persisted: false,
        },
      ],
      entries,
      entry_count: entries.length,
      default_page_size: 25,
      pagination_supported: true,
      metadata_only: true,
      live_marketplace_fetch_performed: false,
      raw_marketplace_payload_persisted: false,
    },
  };
}

describe("SkillWorkbench", () => {
  it("shows source signals without a license column or guessed risk", () => {
    render(<SkillWorkbench authoritative posture={posture()} />);

    expect(
      screen.getByRole("heading", { name: "Skill Workbench" }),
    ).toBeInTheDocument();
    expect(screen.getByText("12 skill ideas")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "List view" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByText("★ 42 stars")).toBeInTheDocument();
    expect(screen.getAllByText("No source rating").length).toBeGreaterThan(0);
    const list = screen.getByLabelText("Skill idea list");
    expect(within(list).queryByText("License")).not.toBeInTheDocument();
    const inspector = screen.getByLabelText("Skill details");
    expect(within(inspector).getByText("License")).toBeInTheDocument();
    expect(screen.queryByText(/low risk/i)).not.toBeInTheDocument();
    expect(screen.getByText("Risk").nextSibling).toHaveTextContent(
      "Not assessed",
    );
    expect(
      screen.getByRole("button", { name: "Adapt for UAA" }),
    ).toBeDisabled();
  });

  it("switches views and filters source-derived records", () => {
    render(<SkillWorkbench authoritative posture={posture()} />);

    fireEvent.click(screen.getByRole("button", { name: "Grid view" }));
    expect(screen.getByLabelText("Skill idea grid")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "List view" }));
    expect(screen.getByLabelText("Skill idea list")).toBeInTheDocument();

    fireEvent.change(screen.getByRole("combobox", { name: "Source" }), {
      target: { value: "clawhub" },
    });
    expect(screen.getByText("1 skill ideas")).toBeInTheDocument();
    expect(screen.getAllByText("Source-Ranked Skill").length).toBeGreaterThan(0);
    expect(screen.queryByText("Hermes Skill 2")).not.toBeInTheDocument();

    fireEvent.change(screen.getByRole("searchbox", { name: "Search skill ideas" }), {
      target: { value: "no matching source record" },
    });
    expect(
      screen.getByText(/No source-derived skill metadata matches/i),
    ).toBeInTheDocument();
  });

  it("paginates dense results and updates the selected inspector", () => {
    render(<SkillWorkbench authoritative posture={posture()} />);

    fireEvent.change(screen.getByRole("combobox", { name: "Rows per page" }), {
      target: { value: "10" },
    });
    expect(screen.getByText("1–10 of 12")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "2" }));
    expect(screen.getByText("11–12 of 12")).toBeInTheDocument();

    const list = screen.getByLabelText("Skill idea list");
    fireEvent.click(within(list).getByRole("button", { name: /Hermes Skill 12/i }));
    const inspector = screen.getByLabelText("Skill details");
    expect(within(inspector).getByRole("heading", { name: "Hermes Skill 12" }))
      .toBeInTheDocument();
    expect(within(inspector).getAllByText("Not provided").length).toBeGreaterThan(
      1,
    );
  });
});

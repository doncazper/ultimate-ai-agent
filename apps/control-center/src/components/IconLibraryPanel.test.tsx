import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ICON_DEFINITIONS } from "../icons/iconRegistry";
import { IconLibraryPanel } from "./IconLibraryPanel";

describe("IconLibraryPanel", () => {
  it("shows the full catalog and changes the selected icon", () => {
    render(<IconLibraryPanel />);
    expect(
      screen.getByText(`${ICON_DEFINITIONS.length} scalable vector icons`, {
        exact: false,
      }),
    ).toBeInTheDocument();
    const shieldButton = screen
      .getByText("Shield Check", {
        selector: ".icon-catalog-grid button > span",
      })
      .closest("button");
    expect(shieldButton).not.toBeNull();
    fireEvent.click(shieldButton!);
    expect(
      screen.getAllByText("shield-check", { selector: "code" }).length,
    ).toBeGreaterThanOrEqual(2);
  });

  it("filters by query and category and exposes an empty state", () => {
    render(<IconLibraryPanel />);
    const search = screen.getByPlaceholderText(
      "Search names, aliases, and keywords",
    );
    fireEvent.change(search, { target: { value: "brain" } });
    expect(screen.getByRole("button", { name: /Brain Circuit/i })).toBeVisible();
    fireEvent.change(search, { target: { value: "not-a-real-icon" } });
    expect(screen.getByText("No icons match this filter")).toBeVisible();
  });

  it("previews the catalog with dark-theme icon tokens", () => {
    const { container } = render(<IconLibraryPanel />);
    fireEvent.click(screen.getByRole("button", { name: "Dark" }));
    expect(container.querySelector(".icon-library")).toHaveAttribute(
      "data-icon-theme",
      "dark",
    );
  });

  it("shows reusable semantic product graphics", () => {
    render(<IconLibraryPanel />);
    expect(screen.getByText("Semantic presets from accepted renders")).toBeVisible();
    expect(screen.getByText("Kill switch")).toBeVisible();
    expect(screen.getByText("Receipt recorded")).toBeVisible();
  });
});

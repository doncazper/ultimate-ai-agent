import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { NorthStarIcon, NorthStarIconBadge } from "./NorthStarIcon";

describe("NorthStarIcon", () => {
  it("renders adjacent-text icons as decorative by default", () => {
    const { container } = render(<NorthStarIcon name="today" />);
    const icon = container.querySelector("svg");
    expect(icon).toHaveAttribute("aria-hidden", "true");
    expect(icon).toHaveAttribute("data-icon-name", "sun");
  });

  it("supports accessible standalone icons, semantic tone, and numeric size", () => {
    render(
      <NorthStarIcon
        decorative={false}
        label="Open evidence"
        name="evidence"
        size={28}
        tone="success"
      />,
    );
    const icon = screen.getByRole("img", { name: "Open evidence" });
    expect(icon).toHaveClass("icon-tone-success");
    expect(icon).toHaveStyle({ "--icon-size": "28px" });
  });

  it("renders soft and solid colored badge variants", () => {
    const { container } = render(
      <>
        <NorthStarIconBadge icon="shield-check" tone="success" />
        <NorthStarIconBadge
          icon="triangle-alert"
          tone="danger"
          variant="solid"
        />
      </>,
    );
    expect(container.querySelector(".icon-badge-soft")).toBeInTheDocument();
    expect(container.querySelector(".icon-badge-solid")).toBeInTheDocument();
  });
});

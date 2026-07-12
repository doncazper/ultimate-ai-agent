import { describe, expect, it } from "vitest";
import {
  ICON_DEFINITIONS,
  ICON_NAMES,
  getIconDefinition,
  resolveIconName,
  searchIconDefinitions,
} from "./iconRegistry";

describe("Control Center icon registry", () => {
  it("provides a large, unique, categorized vector inventory", () => {
    expect(ICON_NAMES.length).toBeGreaterThanOrEqual(200);
    expect(new Set(ICON_NAMES).size).toBe(ICON_NAMES.length);
    expect(ICON_DEFINITIONS).toHaveLength(ICON_NAMES.length);
    for (const definition of ICON_DEFINITIONS) {
      expect(definition.categories.length).toBeGreaterThan(0);
      expect(definition.label.length).toBeGreaterThan(0);
      expect(definition.component).toBeTypeOf("object");
    }
  });

  it("keeps legacy NorthStarIcon names compatible", () => {
    expect(resolveIconName("check-circle")).toBe("circle-check");
    expect(resolveIconName("chat")).toBe("message-square");
    expect(resolveIconName("cube")).toBe("box");
    expect(resolveIconName("gear")).toBe("settings");
    expect(resolveIconName("receipt")).toBe("receipt-text");
    expect(getIconDefinition("today").name).toBe("sun");
  });

  it("searches names, labels, aliases, and categories", () => {
    expect(searchIconDefinitions({ query: "receipt" })).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ name: "receipt-text" }),
      ]),
    );
    expect(
      searchIconDefinitions({ category: "weather" }).map(({ name }) => name),
    ).toEqual(expect.arrayContaining(["cloud-sun", "moon", "sun"]));
    expect(
      searchIconDefinitions({ category: "runtime", query: "brain" }).map(
        ({ name }) => name,
      ),
    ).toEqual(["brain", "brain-circuit"]);
  });
});

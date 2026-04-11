// frontend/lib/__tests__/theme.test.ts
import { describe, it, expect } from "vitest";
import { deriveScheme, type SeedColors } from "../theme";

const EU_BLUE: SeedColors = {
  primary: "#1b4f72",
  accent: "#2a8f9d",
  secondary: "#c9a84c",
};

describe("deriveScheme", () => {
  it("returns all 15 required CSS variable keys", () => {
    const derived = deriveScheme(EU_BLUE, 0.97);
    const expected = [
      "--color-primary", "--color-primary-container",
      "--color-teal", "--color-teal-dim", "--color-teal-container",
      "--color-teal-container-light",
      "--color-gold", "--color-gold-dim", "--color-gold-container",
      "--color-surface-dim", "--color-surface-bright",
      "--color-surface-container", "--color-surface-container-high",
      "--color-surface-container-highest",
      "--color-neutral-light",
    ];
    expect(Object.keys(derived).sort()).toEqual(expected.sort());
  });

  it("passes seeds through unchanged", () => {
    const derived = deriveScheme(EU_BLUE, 0.97);
    expect(derived["--color-primary"]).toBe("#1b4f72");
    expect(derived["--color-teal"]).toBe("#2a8f9d");
    expect(derived["--color-gold"]).toBe("#c9a84c");
  });

  it("surface-bright is always #ffffff", () => {
    expect(deriveScheme(EU_BLUE, 0.97)["--color-surface-bright"]).toBe("#ffffff");
  });

  it("all values are valid #rrggbb hex strings", () => {
    const hex = /^#[0-9a-f]{6}$/;
    const derived = deriveScheme(EU_BLUE, 0.97);
    for (const [key, val] of Object.entries(derived)) {
      expect(val, `${key} should be valid hex`).toMatch(hex);
    }
  });

  it("lower surface_lightness produces a lower lightness surface-dim", () => {
    const light = deriveScheme(EU_BLUE, 0.97);
    const dark = deriveScheme(EU_BLUE, 0.88);
    const parseLightness = (hex: string): number => {
      const r = parseInt(hex.slice(1, 3), 16) / 255;
      const g = parseInt(hex.slice(3, 5), 16) / 255;
      const b = parseInt(hex.slice(5, 7), 16) / 255;
      return (Math.max(r, g, b) + Math.min(r, g, b)) / 2;
    };
    expect(parseLightness(dark["--color-surface-dim"])).toBeLessThan(
      parseLightness(light["--color-surface-dim"])
    );
  });
});

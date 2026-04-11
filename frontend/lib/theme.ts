// frontend/lib/theme.ts

export interface SeedColors {
  primary: string;
  accent: string;
  secondary: string;
}

export type DerivedScheme = Record<string, string>;

function hexToHsl(hex: string): [number, number, number] {
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const l = (max + min) / 2;
  if (max === min) return [0, 0, l];
  const d = max - min;
  const s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
  let h = 0;
  if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
  else if (max === g) h = ((b - r) / d + 2) / 6;
  else h = ((r - g) / d + 4) / 6;
  return [h, s, l];
}

function hslToHex(h: number, s: number, l: number): string {
  const hue2rgb = (p: number, q: number, t: number): number => {
    if (t < 0) t += 1;
    if (t > 1) t -= 1;
    if (t < 1 / 6) return p + (q - p) * 6 * t;
    if (t < 1 / 2) return q;
    if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
    return p;
  };
  const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
  const p = 2 * l - q;
  const r = Math.round(hue2rgb(p, q, h + 1 / 3) * 255);
  const g = Math.round(hue2rgb(p, q, h) * 255);
  const b = Math.round(hue2rgb(p, q, h - 1 / 3) * 255);
  return "#" + [r, g, b].map((v) => v.toString(16).padStart(2, "0")).join("");
}

function deriveColor(hex: string, lightness: number, saturation: number): string {
  const [h] = hexToHsl(hex);
  return hslToHex(h, saturation, lightness);
}

export function deriveScheme(seeds: SeedColors, surfaceLightness: number): DerivedScheme {
  const L = surfaceLightness;
  return {
    "--color-primary": seeds.primary.toLowerCase(),
    "--color-primary-container": deriveColor(seeds.primary, 0.90, 0.30),
    "--color-teal": seeds.accent.toLowerCase(),
    "--color-teal-dim": deriveColor(seeds.accent, 0.12, 1.00),
    "--color-teal-container": deriveColor(seeds.accent, 0.92, 0.40),
    "--color-teal-container-light": deriveColor(seeds.accent, 0.97, 0.15),
    "--color-gold": seeds.secondary.toLowerCase(),
    "--color-gold-dim": deriveColor(seeds.secondary, 0.20, 1.00),
    "--color-gold-container": deriveColor(seeds.secondary, 0.92, 0.60),
    "--color-surface-dim": deriveColor(seeds.primary, L, 0.08),
    "--color-surface-bright": "#ffffff",
    "--color-surface-container": deriveColor(seeds.primary, Math.max(0, L - 0.02), 0.10),
    "--color-surface-container-high": deriveColor(seeds.primary, Math.max(0, L - 0.05), 0.12),
    "--color-surface-container-highest": deriveColor(seeds.primary, Math.max(0, L - 0.08), 0.14),
    "--color-neutral-light": deriveColor(seeds.primary, L, 0.05),
  };
}

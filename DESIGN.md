---
name: Continental Excellence
colors:
  surface: '#f9f9ff'
  surface-dim: '#d3daef'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f1f3ff'
  surface-container: '#e9edff'
  surface-container-high: '#e1e8fd'
  surface-container-highest: '#dce2f7'
  on-surface: '#141b2b'
  on-surface-variant: '#444653'
  inverse-surface: '#293040'
  inverse-on-surface: '#edf0ff'
  outline: '#747684'
  outline-variant: '#c4c5d5'
  surface-tint: '#3557bc'
  primary: '#002068'
  on-primary: '#ffffff'
  primary-container: '#003399'
  on-primary-container: '#8aa4ff'
  inverse-primary: '#b5c4ff'
  secondary: '#745b00'
  on-secondary: '#ffffff'
  secondary-container: '#fecb00'
  on-secondary-container: '#6e5700'
  tertiary: '#24272b'
  on-tertiary: '#ffffff'
  tertiary-container: '#3a3d40'
  on-tertiary-container: '#a5a8ab'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dce1ff'
  primary-fixed-dim: '#b5c4ff'
  on-primary-fixed: '#00164e'
  on-primary-fixed-variant: '#153ea3'
  secondary-fixed: '#ffe08b'
  secondary-fixed-dim: '#f1c100'
  on-secondary-fixed: '#241a00'
  on-secondary-fixed-variant: '#584400'
  tertiary-fixed: '#e0e2e6'
  tertiary-fixed-dim: '#c4c7ca'
  on-tertiary-fixed: '#191c1f'
  on-tertiary-fixed-variant: '#44474a'
  background: '#f9f9ff'
  on-background: '#141b2b'
  surface-variant: '#dce2f7'
typography:
  display-xl:
    fontFamily: manrope
    fontSize: 48px
    fontWeight: '800'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: manrope
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: manrope
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-caps:
    fontFamily: inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  document-text:
    fontFamily: inter
    fontSize: 11pt
    fontWeight: '400'
    lineHeight: '1.5'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 24px
  lg: 48px
  xl: 80px
  container-max: 1280px
  gutter: 24px
---

## Brand & Style

This design system establishes a premium, authoritative presence for AI-driven career advancement. It balances the institutional reliability of European administrative aesthetics with the cutting-edge fluidity of modern SaaS. The brand personality is "The Diplomatic Strategist": poised, high-achieving, and meticulous.

The design style is **Modern Corporate Glassmorphism**. It utilizes semi-transparent surfaces and frosted-glass backdrops to signify the "intelligence" layer of the AI, while maintaining a rigorous underlying grid for document integrity. The UI evokes a sense of "prestige" through generous whitespace and high-fidelity lighting effects, ensuring that the user feels they are using a high-stakes professional tool rather than a casual editor.

## Colors

The palette is anchored in **EU Navy (#003399)**, providing a foundation of trust and institutional gravity. **Sophisticated Gold (#FFCC00)** is used sparingly as a high-value accent for "premium" features, AI-generated suggestions, and primary calls to action.

To maintain document readability, the "Paper" background is kept pure white or exceptionally light gray, while the UI chrome utilizes varying degrees of translucency. The system supports **Thematic Variants**:
- **Standard:** Navy and Gold dominance.
- **French:** Incorporates Tricolour accents (Deep Blue and Carmine Red) for localized appeal.
- **Swiss:** Shifts to a strictly monochromatic palette with heavy emphasis on red-and-white functional signaling.

## Typography

This design system employs a dual-font strategy. **Manrope** is used for headlines to provide a modern, refined, and slightly geometric character that feels architectural. **Inter** is utilized for body text and functional labels due to its exceptional legibility and neutral, systematic tone.

For the CV generation experience, the system prioritizes "Document-Standard" sizing (11pt/12pt) within the editor to ensure the user has a 1:1 mental model of the final printed product. High-contrast ratios (WCAG AAA) are enforced for all text on the primary navy background and the white paper surfaces.

## Layout & Spacing

The layout philosophy follows a **Precision Grid** model. It uses a 12-column system for dashboard views and a specialized 2-column "Sidebar-Editor" layout for the CV builder. 

- **The Swiss Variant** adopts a strict "High-Precision" grid with visible or implied hairline dividers and ultra-consistent 24px increments.
- **Generous Whitespace:** Margins are intentionally large (48px+) to prevent the dense CV data from feeling overwhelming.
- **Responsive Behavior:** On smaller viewports, the CV preview moves into a secondary tab, while the input fields maintain a single-column focus to reduce cognitive load.

## Elevation & Depth

Visual hierarchy is established through **Tonal Glassmorphism**. 

- **Surface 0 (Background):** Solid, neutral off-white or deep navy.
- **Surface 1 (Cards/Panels):** Semi-transparent white (90% opacity) with a 20px backdrop blur and a thin 1px border.
- **Surface 2 (Floating Modals/Popovers):** Transparent gold or navy tints with high-fidelity, diffused shadows (Blur: 40px, Spread: -10px, Opacity: 15%).

Shadows are "ambient" rather than directional, making elements appear to glow or float naturally above the workspace. In the 'Swiss' variant, elevation is conveyed solely through hairline borders and color shifts rather than blurs or shadows.

## Shapes

The design system uses a **Rounded (Level 2)** shape language to soften the corporate edge of the Navy/Gold palette. 
- **Standard Elements:** 0.5rem (8px) border radius for inputs and small cards.
- **Large Containers:** 1rem (16px) for the main editor panels.
- **Interactive Triggers:** Pill-shaped (2rem+) for primary buttons to create "eye-candy" click targets that stand out against the rectilinear grid of the document.

## Components

### Premium Interactive Elements
- **Buttons:** Primary buttons utilize a subtle gold-to-yellow gradient with a shimmer effect on hover. Secondary buttons use a "Glass" style—transparent with a navy border.
- **AI-Cards:** Cards containing AI suggestions feature a "Light Leak" border effect, using a subtle gradient that rotates slowly to indicate active "intelligence."
- **Input Fields:** High-contrast fields with 1px solid borders that transition to a 2px Gold glow upon focus.

### Progress & Flow
- **The Step-Indicator:** A horizontal "Liquid" bar. Completed steps turn Navy; the active step is highlighted in Gold with a pulsing glow.
- **Readability Toggle:** A floating action button that allows users to toggle between "Edit Mode" (UI focused) and "Review Mode" (Focus solely on the document).

### Document Preview
- The CV preview component must sit on a "Shadow Pedestal," appearing as a physical piece of paper floating above a dark navy workspace to emphasize its importance.
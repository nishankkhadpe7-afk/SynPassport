---
name: Terminal Precision
colors:
  surface: '#0a141f'
  surface-dim: '#0a141f'
  surface-bright: '#303a46'
  surface-container-lowest: '#050f19'
  surface-container-low: '#131c27'
  surface-container: '#17202b'
  surface-container-high: '#212b36'
  surface-container-highest: '#2c3641'
  on-surface: '#d9e3f3'
  on-surface-variant: '#bacac5'
  inverse-surface: '#d9e3f3'
  inverse-on-surface: '#27313d'
  outline: '#859490'
  outline-variant: '#3c4a46'
  surface-tint: '#3cddc7'
  primary: '#57f1db'
  on-primary: '#003731'
  primary-container: '#2dd4bf'
  on-primary-container: '#00574d'
  inverse-primary: '#006b5f'
  secondary: '#9ecafe'
  on-secondary: '#003257'
  secondary-container: '#144976'
  on-secondary-container: '#8db9ec'
  tertiary: '#5df3b6'
  on-tertiary: '#003825'
  tertiary-container: '#39d69c'
  on-tertiary-container: '#00583c'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#62fae3'
  primary-fixed-dim: '#3cddc7'
  on-primary-fixed: '#00201c'
  on-primary-fixed-variant: '#005047'
  secondary-fixed: '#d1e4ff'
  secondary-fixed-dim: '#9ecafe'
  on-secondary-fixed: '#001d35'
  on-secondary-fixed-variant: '#144976'
  tertiary-fixed: '#68fcbf'
  tertiary-fixed-dim: '#45dfa4'
  on-tertiary-fixed: '#002114'
  on-tertiary-fixed-variant: '#005137'
  background: '#0a141f'
  on-background: '#d9e3f3'
  surface-variant: '#2c3641'
typography:
  headline-xl:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Geist
    fontSize: 18px
    fontWeight: '500'
    lineHeight: 24px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: 0em
  body-md:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0em
  body-sm:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.01em
  mono-lg:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: -0.01em
  mono-md:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0em
  mono-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 14px
    letterSpacing: 0.02em
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '500'
    lineHeight: 12px
    letterSpacing: 0.08em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-desktop: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
  space-2xl: 3rem
---

## Brand & Style
The design system embodies absolute operational clarity, engineered for high-stakes verification environments, audits, and cryptographic telemetry. Its brand identity prioritizes uncompromising legibility, deterministic structure, and zero-latency visual parsing. The aesthetic is strictly flat and technical—rejecting decorative ornamentation, synthetic depth, glows, and soft lighting in favor of hairline precision and disciplined solid planes.

The target audience includes security analysts, compliance auditors, and systems engineers who require maximum signal with minimal cognitive overhead. The system evokes a clinical, authoritative, and unflinching atmosphere. Every visual element exists to convey verifiable data: nothing is approximate, nothing is blurred, and no gradient softens the boundaries between states.

## Colors
The palette operates strictly within high-contrast dark mode, built exclusively on flat, solid hex values. Gradients, glows, radial fades, and ambient drop-color spills are prohibited across all UI surfaces, buttons, visual accents, and data representations. 

### Palette Architecture
- **Background (`#0A0C0F`)**: Deepest substrate level for overall screen canvas.
- **Surface (`#11151A`)**: Structural panels, containers, and data grids.
- **Surface Raised (`#171C23`)**: Hover states, popovers, active panel rows, and modular drawer panels.
- **Border (`#232A33`)**: Structural 1px hairline delimiters; the sole mechanism for separating nested planes.
- **Text Primary (`#E6EAF0`)**: Core metrics, critical headers, and primary content.
- **Text Secondary (`#8B95A3`)**: Metadata, labels, and secondary interface descriptions.
- **Text Muted (`#566171`)**: Disabled text, timestamps, and column headers.
- **Accent (`#2DD4BF`)**: Flat teal reserved for interactive primary controls, links, active tab rules, and keyboard focus states.

### Verification States
- **Verdict Pass (`#34D399`)**: Confirmed attestations, passing test suites, and cryptographic integrity. Solid flat fill.
- **Verdict Warning (`#F59E0B`)**: Non-blocking discrepancies, warnings, or threshold degradations.
- **Verdict Fail (`#F87171`)**: Policy violations, failed proofs, or critical errors.
- **Verdict Insufficient (`#7BA7D9`)**: Missing signals or inconclusive audit results. Rendered exclusively with a solid `#7BA7D9` glyph or a 1px dashed outline of `#7BA7D9` over solid backgrounds.

Violet, purple, indigo, magenta, and pink hues are strictly excluded from the design system across all product contexts.

## Typography
Typographic pairing uses **Geist** for natural-reading structure and interface copy, combined with **JetBrains Mono** for all operational parameters.

- **Geist**: Utilized for view headers, section labels, instructional copy, operational tables, and dialogue copy. It provides crisp geometry without geometric distortion.
- **JetBrains Mono**: Mandatory for all hash strings, cryptographic signatures, addresses, timestamp counters, operational counts, raw telemetry, and uppercase category labels (`label-caps`). Numbers in tables must always utilize tabular figures (`tnum`).

## Layout & Spacing
The layout adheres to a fixed-canvas or fluid-column 12-column layout built upon a rigorous 4px baseline rhythm. Density is calibrated for information-heavy monitoring: content must prioritize visual economy over excessive dead space.

- **Breakpoints**: 
  - Mobile: `< 768px` (4 columns, `margin`: 1rem, `gutter`: 1rem)
  - Tablet: `768px - 1024px` (8 columns, `margin`: 1.5rem, `gutter`: 1rem)
  - Desktop: `> 1024px` (12 columns, `margin-desktop`: 2rem, `gutter-desktop`: 1.5rem)
- **Rhythm & Structure**: Component padding and gaps adhere strictly to the `space-*` scale. Multi-column data layouts collapse cleanly to single-column blocks on mobile breakpoints without altering internal data hierarchy.

## Elevation & Depth
Elevation is achieved exclusively through **tonal planar shifts and structural hairline borders**. 

- **No Shadows**: Drop shadows, inner shadows, and soft ambient diffusions (`box-shadow`) are completely prohibited.
- **No Glows**: Neon edge effects, filter blurs, bloom rings, and saturated light projections are disallowed.
- **Hairline Borders**: Depth is rendered using solid 1px borders in `#232A33`. 
- **Z-Index Tiers**:
  - Base View Canvas: Solid `#0A0C0F`
  - Inset Cards, Data Panels, Table Rows: Solid `#11151A` with a 1px solid `#232A33` boundary.
  - Floating Layers (Dropdowns, Dialogs, Tooltips): Solid `#171C23` with a 1px solid `#232A33` boundary. Modals do not utilize soft shadow drop-offs; they overlay the lower view with a solid 80% opacity `#0A0C0F` flat veil.

## Shapes
Shapes emphasize compact structural density through a restrained "Soft" (`1`) curvature model:
- Inputs, standard buttons, badges, chips: `0.25rem` (4px).
- Structural containers, modals, table shells: `0.5rem` (8px).
- Nested inner panels: `0.25rem` (4px).

Pill shapes, circular aesthetic accents, and fully rounded tags are prohibited. Checkboxes and radios maintain precise, crisp edges (`2px` radius for checkboxes, native circular rings for radios).

## Components

### Buttons
- **Primary**: Solid flat `#2DD4BF` background, `#0A0C0F` bold text. No gradients. Hover state is an unshifted solid `#26bfae`. Active state is `#1fa394`. Focus state adds an offset 1px solid `#2DD4BF` hairline ring with a 2px gap.
- **Secondary**: Solid `#171C23` background, 1px solid `#232A33` border, `#E6EAF0` text. Hover changes background to `#232A33`.
- **Destructive**: Solid flat `#F87171` background, `#0A0C0F` text.
- **Ghost/Outline**: Transparent background, 1px solid `#232A33` border, `#8B95A3` text. Hover: `#11151A` background, `#E6EAF0` text.

### Chips & Badges
- Text strictly set in `JetBrains Mono` (`label-caps` or `mono-sm`). Height: 20px or 24px.
- **Pass**: Solid `#11151A` background, 1px solid `#34D399` border, `#34D399` text.
- **Warning**: Solid `#11151A` background, 1px solid `#F59E0B` border, `#F59E0B` text.
- **Fail**: Solid `#11151A` background, 1px solid `#F87171` border, `#F87171` text.
- **Insufficient Evidence**: Solid `#11151A` background, 1px dashed `#7BA7D9` border, `#7BA7D9` text.

### Input Fields
- Solid `#11151A` background, 1px solid `#232A33` border, `#E6EAF0` text. Height: 36px.
- Placeholder text in `#566171`.
- Focused state: Border changes to 1px solid `#2DD4BF`. No outer glow, bloom, or box-shadow.

### Checkboxes & Radios
- Size: 16px × 16px. Background: Solid `#0A0C0F`, 1px solid `#232A33`.
- Checked State: Solid `#2DD4BF` fill with a sharp `#0A0C0F` checkmark.

### Cards & Panels
- Background: Solid `#11151A`, border: 1px solid `#232A33`, border-radius: 8px.
- Internal headers are delimited with a bottom 1px solid `#232A33` rule. No drop shadows.

### Tables & Data Lists
- Headers: Background `#0A0C0F`, text `#566171`, uppercase `JetBrains Mono` (`label-caps`), border-bottom: 1px solid `#232A33`.
- Rows: Background `#11151A`, alternating or uniform with 1px border-bottom `#232A33`. Hover row background: Solid `#171C23`.
- Numerical/Data values: Always rendered in `JetBrains Mono` (`mono-md` or `mono-sm`).

### Charts & Telemetry Visualizations
- Fills: Strictly flat fills using only `#2DD4BF`, `#7BA7D9`, `#F59E0B`, `#232A33`, and `#8B95A3`. Area charts must use solid opacity fills with zero vertical alpha gradients.
- Gridlines: 1px hairline solid `#232A33`.
- Crosshairs/Markers: Crisp 1px solid lines in `#8B95A3` or `#2DD4BF`. No glowing anchor points.
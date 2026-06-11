# Audette Brand Specifications

Extracted from the official Audette Brand Guidelines (v3, Aug 2021).
Use these specs for all report HTML/CSS styling. If the user wants a non-Audette
branded report, ask them for their brand colors and fonts — but default to these.

A copy of the full brand guidelines PDF is stored in the skill's `assets/` folder
for visual reference.

## Colors

**Primary palette** — Black, White, Purple, and Hot Pink are the core brand colors.

| Name | Hex | CMYK | Usage |
|------|-----|------|-------|
| Hot Pink | `#EB03AD` | 13, 79, 0, 0 | Primary accent. Headers on black bg, highlights, callout borders, CTA buttons |
| Purple | `#7700FF` | 81, 75, 0, 0 | Secondary accent. Headers, subheaders, chart accent |
| Black | `#000000` | 0, 0, 0, 100 | Primary text, header bars, backgrounds |
| White | `#FFFFFF` | 0, 0, 0, 0 | Page background, text on dark backgrounds |

**Secondary palette** — Pink, Teal, and Concrete for lighter/supporting roles.

| Name | Hex | CMYK | Usage |
|------|-----|------|-------|
| Pink | `#FAEDEB` | 2, 8, 5, 0 | Light background, soft callout fills, table alt rows |
| Teal | `#CCFAE5` | 23, 0, 16, 0 | Light background accents, positive-signal fills |
| Concrete | `#E3E5DE` | 13, 6, 12, 0 | Neutral background, table alt rows, divider areas |

## Color application rules (for reports on white backgrounds)

Per the brand guidelines (section 2.2):
- **Headers (h1, h2):** Use black, hot pink, or purple
- **Subheaders (h3):** Use black, purple, or hot pink
- **Body copy:** Use black. For callouts/highlights, use hot pink
- **Table headers:** Black background with white text
- **Alternating table rows:** White / Pink (`#FAEDEB`) or White / Concrete (`#E3E5DE`)

## Typography

**Harmonia Sans** is the official Audette brand font for all applications.

| Element | Font | Weight | Style notes |
|---------|------|--------|-------------|
| H1 (report title) | Harmonia Sans Bold | 700 | Large, sentence case. Significantly larger than H2 |
| H2 (section headings) | Harmonia Sans Bold | 700 | Bold headlines |
| H3 (sub-subheadings) | Harmonia Sans Bold | 700 | All caps, letter-spacing: 1.4px |
| Body text | Nimbus Sans Regular | 400 | General copy and large bodies of text |
| Captions / footnotes | Nimbus Sans Regular | 400 | Smaller size, descriptive text |
| Buttons / CTAs | Harmonia Sans Bold | 700 | Optimal readability |

**Web fallback:** Harmonia Sans is a commercial font. For HTML/PDF rendering where
Harmonia Sans isn't installed, use this fallback chain:

```css
/* Headers */
font-family: 'Harmonia Sans', 'DM Sans', 'Inter', sans-serif;

/* Body */
font-family: 'Nimbus Sans', 'Helvetica Neue', 'Arial', sans-serif;
```

Import DM Sans from Google Fonts as the closest free alternative for headers:
```html
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap" rel="stylesheet">
```

## Text formatting rules

From the brand guidelines (section 2.4):
- **All text is left-aligned.** Centre alignment should only be used if left alignment
  isn't favorable (rare in reports)
- H1 is deliberately much larger than H2 to create visual hierarchy
- H3 uses all-caps with letter-spacing to differentiate from H2
- Keep body copy informative and neutral; show personality in headers and captions

## Page layout

- **Page size:** Letter (8.5" x 11")
- **Margins:** 0.75" all sides
- **Header bar:** Black (`#000000`) full-width bar with "Audette" brandmark in white,
  report title below in white, date right-aligned
- **Footer:** Centered page number, "Confidential — Prepared by Audette" in muted text
- **Section spacing:** 24px between sections

## Tables

- **Header row:** Black (`#000000`) background, white text, bold (Harmonia Sans Bold)
- **Alternating rows:** White / Pink (`#FAEDEB`)
- **Cell padding:** 8px 12px
- **Borders:** 1px Concrete (`#E3E5DE`) between rows
- **No outer border**

## Callout boxes

For key findings, recommendations, or alerts:

```css
.callout {
  background: #FAEDEB;           /* Pink - soft highlight */
  border-left: 4px solid #EB03AD; /* Hot Pink accent */
  padding: 16px;
  margin: 16px 0;
  border-radius: 0;              /* Sharp corners per brand */
}
.callout-positive {
  background: #CCFAE5;           /* Teal - positive signal */
  border-left-color: #000000;
}
.callout-warning {
  background: #FAEDEB;
  border-left-color: #7700FF;    /* Purple */
}
```

## Logo

The Audette brandmark uses a distinctive I/O emblem (inspired by digital input/output).
- The emblem consists of a vertical bar and a filled circle
- Use the text "Audette" in the header, styled in Harmonia Sans Bold (or DM Sans Bold
  as fallback), white on black
- When a logo file is added to `assets/logo.png`, the render script will embed it
- Minimum size for the brandmark: 65px width on screen, 1 inch in print

## Brand voice (for report writing)

The brand guidelines (section 1.6) define the Audette voice as:
- **Techy but not Bland** — speak like Google, Tesla, or Apple. Modern, advanced,
  yet relatable and concise.
- **Exciting but not Excited** — the visual brand is bold (colors, fonts); balance
  that with a neutral, professional writing tone. No all-caps or excessive punctuation.
- **Smart but not Scholarly** — informative and neutral for body text, but feel free
  to show personality in headers and callouts. Think Apple's concise, informative style.

**Tagline:** Transform your Entire Portfolio to Carbon Neutral, 10x faster.

## Charts and data viz

If reports include charts (from the UI elements guide, section 2.6):
- Use the brand color sequence: Black, Hot Pink, Purple, then Concrete, Teal, Pink
- Donut/ring charts (not pie charts) for proportions
- Bar charts with brand colors
- White background, no chart border
- Grid lines in Concrete, light
- Font: Harmonia Sans / DM Sans for labels

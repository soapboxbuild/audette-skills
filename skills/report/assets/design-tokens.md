# Audette Report Design Tokens

Reference for all visual styling across report types.

## Colors

| Token | Hex | Use |
|-------|-----|-----|
| `--color-primary` | `#066ECC` | Primary brand, links, electricity |
| `--color-accent-green` | `#00BC98` | Positive outcomes, savings, reductions |
| `--color-accent-purple` | `#7700FF` | Financial projections, cash flow |
| `--color-accent-orange` | `#F7931E` | Natural gas, combustion, warnings |
| `--color-danger` | `#CC303C` | Baseline (no action), penalties, risk |
| `--color-text` | `#1a1a1a` | Body text |
| `--color-muted` | `#666666` | Secondary text, subtitles |
| `--color-light` | `#999999` | Dates, captions |
| `--color-border` | `#e5e5e5` | Table borders, dividers |
| `--color-bg-light` | `#f8f9fa` | Table alternating rows, callout backgrounds |

## Typography

- **Font:** DM Sans (Google Fonts)
- **Body:** 11pt / 1.6 line height
- **H1 (cover):** 32pt, weight 700
- **H2 (section):** 18pt, weight 700
- **H3 (subsection):** 13pt, weight 500
- **Table headers:** 9pt, uppercase, letter-spacing 0.05em

## Layout

- **Page size:** Letter (8.5in × 11in)
- **Margins (print):** 0.75in all sides
- **Container max-width:** 8.5in
- **Content padding:** 1in
- **Cover padding:** 2in top, 1in sides

## Charts (Chart.js)

- **Font:** DM Sans (match body)
- **Grid lines:** `#e5e5e5`, 1px
- **Legend:** bottom, 12pt
- **Tooltips:** dark background, white text
- **Border radius on bars:** 4px

## Print

- `@page { margin: 0.75in; size: letter; }`
- Hide `.no-print` elements
- `page-break-before: always` on `.page-break`
- Avoid breaks after H2, inside tables

---
name: report
description: >
  Generate professional building performance reports as self-contained HTML artifacts.
  Agent gathers data from Audette MCP, writes a complete HTML report inline with CSS
  and system fonts (no external dependencies), presents it as an artifact, iterates
  until approved, then saves via save_file. Supports decarbonization roadmaps, BPS
  compliance summaries, acquisition due diligence (RSRA), and portfolio summaries.
  Triggers on: "generate a report", "create a roadmap", "show me the compliance status",
  "prepare a DD summary", "build a portfolio overview", "export to PDF/PPTX/Excel".
version: 2.0.0
requires:
  - audette-mcp
---

# Audette Report Generator

Generate professional, client-ready reports from Audette building data. The output is
a self-contained HTML artifact — no Paged.js, no external CDN, no template engine.

For sustainability-specific acquisition analysis (RSRA), see the `rapid-sustainability-risk`
skill, which provides detailed underwriting guidance. This skill handles the general
report-writing flow for any Audette report type.

---

## Pre-flight

Call `switch_customer_account` with the Audette customer account UID from the system prompt
before any MCP calls. If no UID is available, call `list_customer_accounts` and ask.

---

## Step 1: Classify Report Type

If not clear from context, ask:

> "Which report would you like?
> 1. Decarbonization Roadmap — retrofit plan, emissions trajectory, financial projections
> 2. BPS Compliance Summary — applicable regulations, penalty exposure, path to compliance
> 3. Rapid Sustainability Risk Assessment (RSRA) — acquisition due diligence
> 4. Portfolio Summary — overview of multiple buildings"

For building-level reports, identify the target building from the system prompt or call
`list_buildings`.

---

## Step 2: Gather Data

Call the relevant Audette MCP tools for the report type. Key tools by report type:

- **Decarb Roadmap**: `get_building`, `get_carbon_emissions`, `get_retrofit_measures`,
  `get_financial_projections`, `get_incentive_programs`
- **BPS Compliance**: `get_building`, `get_carbon_emissions`, `get_bps_regulations`,
  `get_compliance_trajectory`
- **RSRA**: `get_building`, `get_carbon_emissions`, `get_energy_consumption`,
  `get_retrofit_measures` — see `rapid-sustainability-risk` skill for full guidance
- **Portfolio Summary**: `list_buildings`, `get_carbon_emissions` for each building

If a tool returns no data for a required section, note the gap — render a callout in
that section rather than omitting it or fabricating values. Never invent numbers.

---

## Step 3: Generate HTML Report

Write a **complete, self-contained HTML file**:

- Inline all CSS in a `<style>` block — no external stylesheets
- Use system fonts: `font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`
- No external CDN dependencies (no Chart.js CDN, no Google Fonts)
- For charts, use inline SVG or HTML/CSS bar charts
- All figures come directly from MCP responses — no placeholders or fabricated values
- Missing fields render as `—`
- Include a print-to-PDF button (`.no-print` class, top-right corner):
  `<button class="no-print" onclick="window.print()">Save as PDF</button>`
- The file must render correctly when opened directly in a browser

Design conventions:
- Dark navy header (`#0F1923`) with white text
- Green accent (`#52B788`) for highlights, signal indicators, call-to-action elements
- Clean white body with subtle gray borders (`#E5E7EB`)
- Section cards with light background (`#F9FAFB`)
- Professional typography: 14px body, 11px labels, 20-28px headings

---

## Step 4: Present and Iterate

Call `create_artifact` with the HTML content so it opens in the preview pane.

Ask:
> "Here's the [report type] for [building name]. Does this look right, or would you like any changes?"

**Cosmetic changes** (colors, layout, wording) → regenerate without re-fetching MCP data.
**New sections or different data scope** → fetch additional data, then regenerate.

Keep iterating until the user explicitly approves.

---

## Step 5: Save

When approved, call `save_file` with:
- `name`: `{asset-slug}-{template}.html` — e.g. `prose-frontier-rsra.html`
  (always lowercase, always a hyphen before the extension)
- `folder`: `"Reports"`
- `mime_type`: `"text/html"`

One `save_file` call per report. Do not also save a .txt summary.

---

## Step 6: Export (Optional)

If the user wants a PDF, PPTX, or Excel export, use the scripts in `scripts/`:

| Format | Script | Notes |
|--------|--------|-------|
| PDF | `scripts/export_pdf.py` (primary) or `scripts/export_pdf.js` (fallback) | Playwright-based; requires Chromium |
| PPTX | `scripts/build_pptx.py` | Requires python-pptx (auto-installs) |
| Excel | `scripts/build_xlsx.py` | Requires openpyxl (auto-installs) |

Run with `python scripts/export_pdf.py --input <path-to-html> --output <path>.pdf`.
Run with `python scripts/build_pptx.py --template rsra --data <path>.json --output <path>.pptx`.

---

## Rules

- Always call `switch_customer_account` before MCP calls
- Never fabricate numbers — every figure must come from MCP
- Always iterate until the user approves before saving
- HTML must be completely self-contained (no external file references)
- Cosmetic revisions do not require re-fetching MCP data

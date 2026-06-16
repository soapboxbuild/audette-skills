---
name: report
description: >
  [DEPRECATED — use soapbox-report instead] Generate professional building performance reports as interactive HTML artifacts.
  Iterates with the user until the output is approved, then saves the result as an
  example for future reports. Supports decarbonization roadmaps, BPS compliance
  summaries, acquisition due diligence, and portfolio summaries. Triggers on:
  "generate a report", "create a roadmap", "show me the compliance status",
  "prepare a DD summary", "build a portfolio overview".
version: 1.0.0
requires:
  - audette-mcp
---

## Deprecated

This skill has been superseded by the centralized `soapbox-report` plugin and its `report-renderer` subagent. Use that instead for all new report generation.

Replacement template names in `soapbox-report`:

| Report Type | Template Name |
|---|---|
| Decarbonization roadmap / retrofit plan | `retrofit-plan` |
| BPS compliance summary | `bps-compliance` |
| Acquisition due diligence / RSRA | `rsra` |
| Portfolio summary / Scope 3 inventory | `portfolio-summary` |
| GRESB submission | `gresb-submission` |
| TCFD / climate disclosure | `crrem-assessment` |

To dispatch via `soapbox-report`, pass `{ "template": "<name>", "data": { ... } }` to the `report-renderer` subagent.

---

# Audette Report Generator

Generate professional HTML reports from Audette building data. Iterate until the user
approves, then save the output as an example for future use.

**Required:** Audette MCP

---

## Template Library

Reports are driven by a template library at `assets/templates/`. Each report type has:

```
assets/templates/<type>/
  manifest.md          ← MCP tools needed, sections, formatting rules
  examples/            ← rendered HTML examples (shipped + user-saved)
    01-standard.html
    <YYYY-MM-DD>-<name>.html
```

The `manifest.md` tells you what data to fetch and what to produce.
The `examples/` files are complete rendered reports — use them as style references, not as fill-in-the-blank templates.

Available types:

| Type | Manifest |
|------|---------|
| `decarb-roadmap` | `assets/templates/decarb-roadmap/manifest.md` |
| `bps-compliance` | `assets/templates/bps-compliance/manifest.md` |

New types can be added by dropping a folder with a `manifest.md` — no skill changes needed.

---

## Pre-flight

Call `switch_customer_account` with the Audette customer account UID from the system prompt.
This is required before any Audette write operations — omitting it causes HTTP 401.

If no account UID is in the system prompt, call `list_customer_accounts` and ask the user to select one.

## Step 1: Classify Report Type

If the type is not clear from context, ask:

> "Which report would you like?
> 1. Decarbonization Roadmap — retrofit plan, emissions trajectory, financial projections
> 2. BPS Compliance Summary — applicable regulations, penalty exposure, path to compliance
> 3. Acquisition Due Diligence — building assessment for property acquisition
> 4. Portfolio Summary — overview of multiple buildings"

For building-level reports, identify the target building from the system prompt (`Audette building UID`) or call `list_buildings` to find it by name or address.

---

## Step 3: Select Example

Scan `assets/templates/<type>/examples/` for available example files. List them with their
dates and names:

> "I found these examples for [report type]:
>
> 1. `01-standard.html` — shipped example, full report
> 2. `2026-06-15-parkview-towers.html` — approved 2026-06-15
> 3. Start fresh (no example reference)
>
> Which should I base this on?"

If no examples exist yet, skip the question and proceed fresh using the manifest only.

If the user selects an example, read that file. Use it as the style and structure reference —
understand the layout, visual choices, and section order. Do not copy its data.

---

## Step 4: Load Data from Audette MCP

Read `assets/templates/<type>/manifest.md`. Call each listed MCP tool and extract the
key fields documented in the manifest.

If a tool returns no data for a required section, note it — you will add a data gap
callout in that section rather than omitting it or fabricating values.

Optional: ask if the user has a client logo. Accept a local file path, read it, and
convert to a base64 data URL for inline embedding.

---

## Step 5: Generate Report

Write a complete, self-contained HTML file:

- Follow the section order from the manifest
- Use the selected example as a style reference (colors, typography, layout, chart style)
- Use `assets/design-tokens.md` for all color and typography values
- Embed Chart.js from CDN: `https://cdn.jsdelivr.net/npm/chart.js`
- All charts use real data from the MCP response — no placeholder values
- Missing fields render as `—`; add a data gap callout (see `assets/components/data-gap-callout.html`) when a critical section is affected
- Embed all assets inline (logo as base64, styles in `<style>` tags) — the file must be self-contained
- Include a `.no-print` save button in the top-right corner with instructions to use File → Print → Save as PDF

The HTML should be complete and renderable — no `{{placeholders}}` remaining.

---

## Step 6: Iteration Loop

Present the report as an artifact. Ask:

> "Here's the [report type] for [building name]. Does this look right, or would you like any changes?"

**If the user requests changes:**

- Cosmetic changes (colors, fonts, layout, wording) → regenerate without re-fetching MCP data
- New sections or different data scope → fetch additional data as needed, then regenerate
- Apply feedback cumulatively — each iteration builds on the last version

Keep iterating until the user explicitly approves.

---

## Step 7: Save Example

When the user approves, ask:

> "Save this as an example for future [report type] reports? It will appear as an option next time."

If yes, ask for a short name (e.g. "parkview-towers", "minimal-layout", "full-incentives"):

> "What should I call it? (e.g. 'parkview-towers')"

Save the approved HTML to:
```
assets/templates/<type>/examples/<YYYY-MM-DD>-<name>.html
```

Update the manifest's examples table to include the new entry.

Confirm:
> "Saved as `assets/templates/decarb-roadmap/examples/2026-06-15-parkview-towers.html`. It will appear as an option the next time you generate a [report type]."

---

## Rules

- Always call `switch_customer_account` before any MCP calls
- Never fabricate numbers — every figure must come from an MCP tool response
- Always ask which example to use before generating (when examples exist)
- Always iterate until the user approves — do not save without approval
- Always save after approval — ask even if the user doesn't explicitly request it
- The HTML file must be completely self-contained (no external file references except CDN)
- Cosmetic revisions do not require re-fetching MCP data
- New examples do not modify the manifest's MCP tools or sections — they only extend the examples table

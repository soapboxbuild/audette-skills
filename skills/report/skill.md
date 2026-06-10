---
name: report
description: >
  Generate structured reports as interactive HTML artifacts. Supports decarbonization
  roadmaps, BPS compliance summaries, acquisition due diligence, and portfolio summaries.
  Reports include embedded Chart.js visualizations and can be saved as PDF via browser
  print. Use when the user wants a report, analysis, or presentation for a building or
  portfolio. Triggers on: "generate a report", "create a roadmap", "show me the compliance
  status", "prepare a DD summary", "build a portfolio overview".
version: 1.0.0
requires:
  - audette-mcp
---

# Audette Report Generator

Generate professional building performance and decarbonization reports as self-contained
HTML artifacts with interactive Chart.js visualizations. Users save as PDF via File → Print
→ Save as PDF.

**Required:** Audette MCP

---

## Report Types

| ID | Name | Primary tools |
|----|------|--------------|
| `decarb-roadmap` | Decarbonization Roadmap | `get_building_model_report`, `run_measure_design_analysis` |
| `bps-compliance` | BPS Compliance Summary | `run_compliance_analysis`, `get_building_model_details` |
| `acquisition-dd` | Acquisition Due Diligence | `run_finance_analysis`, `get_building_model_report` |
| `portfolio-summary` | Portfolio Summary | `list_buildings`, `get_building_model_details` (per building) |

---

## Step 1: Pre-flight

Read `.audette-config.json`. If missing, tell the user to run `workspace-setup` first.

Call `switch_customer_account` with `audette_account.uid`.

---

## Step 2: Classify and Gather

If the report type is not clear from context, ask:

> "Which report would you like?
> 1. Decarbonization Roadmap — retrofit recommendations and emissions trajectory
> 2. BPS Compliance Summary — building performance standard compliance and penalty projections
> 3. Acquisition Due Diligence — building assessment for property acquisition
> 4. Portfolio Summary — overview of multiple buildings"

**For building-level reports**, identify the target building from `buildings[]` in config or ask.
Note the `building_model_uid`.

**Optional for all types:** Ask if the user has a client logo to embed in the cover page.
Accept a local file path. If provided, read the file and convert to a base64 data URL:
`data:image/png;base64,<base64_content>`. Embed inline so the HTML is self-contained.

---

## Step 3: Load Data from Audette MCP

### Decarbonization Roadmap

Call in sequence:

1. `get_building_model_details` → building name, address, GFA, archetype, year built
2. `get_reported_carbon_reduction_plan` → primary plan with all measures, plan-level financials
3. `get_building_model_report` → full baseline energy/emissions data, yearly projections, scope breakdown
4. `run_measure_design_analysis` → 3 additional measures not in the current plan (surface in an "Other Opportunities" section)

**Key fields to extract from the plan:**
- Each measure: name, capex, annual savings, payback, carbon reduction, implementation year
- Plan totals: total capex, total annual savings, NPV, IRR, simple payback
- Baseline: total emissions (tCO2e), scope 1 and scope 2 breakdown, total energy (kWh), EUI, annual energy cost
- Yearly emissions trajectory: baseline trajectory and post-retrofit trajectory (from the report data)

### BPS Compliance Summary

1. `get_building_model_details` → name, address, GFA, archetype
2. `run_compliance_analysis` → applicable regulations, compliance status per regulation, penalty exposure, recommended fixes, citations

**Key fields:**
- Each regulation: name, jurisdiction, applicable status, current compliance status, penalty if non-compliant, lowest-cost fix
- Overall risk: total potential penalty exposure, highest-priority gap

### Acquisition Due Diligence

1. `get_building_model_details` → building info
2. `get_building_model_report` → baseline performance, systems, plans
3. `run_finance_analysis` → capital rate, interest rate, rent price context
4. `run_compliance_analysis` → compliance risk summary
5. `run_incentive_capital_analysis` → available capex incentives

**Key fields:**
- Baseline EUI vs. building type benchmark
- Top 3 retrofit opportunities by payback
- Compliance risks and penalty exposure
- Available incentives and rebates

### Portfolio Summary

1. `list_buildings` → all buildings in the account
2. For each building: `get_building_model_details` and `get_reported_carbon_reduction_plan`

**Key fields per building:** name, address, archetype, GFA, baseline EUI, baseline emissions, plan total capex, carbon reduction potential.

---

## Step 4: Generate the Report

### Decarbonization Roadmap

Use the template at `assets/templates/decarbonization-roadmap.html`. It uses `{{placeholder}}` syntax for variables and `{{#each array}}...{{/each}}` for loops.

Replace every placeholder with extracted data. Use these rules:

- Numbers: format with commas (e.g. `18,420`); emissions to 1 decimal; financials to nearest dollar
- Missing values: render as `—` (em dash), not "N/A" or null
- All units inline with values: "18,420 kWh", "94.2 tCO2e", "$2,341"

**Chart data:** Each chart placeholder (e.g. `{{emissions_chart_data}}`) expects a JSON string representing a Chart.js dataset object. Build the objects from the extracted data and inject as `JSON.stringify(chartObject)`.

**Emissions doughnut:** `labels: ['Scope 1 (Natural Gas)', 'Scope 2 (Electricity)']`, `data: [scope1, scope2]`, colors `#F7931E` and `#066ECC`.

**Measures bar:** One bar per measure, `data: carbon_reduction_per_measure`, color `#00BC98`.

**Emissions trajectory line:** Two datasets — baseline (red `#CC303C`) and with-measures (green `#00BC98`), year-by-year from the report data.

**Cash flow line:** Cumulative cash flow starting at `-total_capex`, increasing by `annual_savings` per year, color `#7700FF`.

**After replacement:** Verify that no `{{` or `}}` remain in the output. If any do, a placeholder was missed.

### BPS Compliance Summary and other types

No HTML template exists yet. Generate clean inline HTML following the same visual style as the roadmap template: DM Sans font, Audette color palette (`#066ECC`, `#00BC98`, `#7700FF`, `#F7931E`), letter size with 0.75in margins.

Include: cover page, compliance status table (regulation → status → penalty → fix), risk summary, and citations from `run_compliance_analysis`.

---

## Step 5: Return as Artifact

Return the HTML as an artifact. Add a note:

> **To save as PDF:** File → Print → Save as PDF. Recommended: Letter size, 0.75in margins.

---

## Error Handling

**Building not modelled yet**
> [Building name] doesn't have a complete model in Audette yet. Run `audette-equipment-survey` and `audette-energy-data` first, then generate the report.

**Plan not found**
> No carbon reduction plan found for this building. The model may still be processing after a recent equipment survey or utility data submission. Wait a few minutes and try again.

**Missing data fields**
Don't fabricate. Render the field as `—` and add a callout box:
> **Data gap:** [field] was not available from the Audette model. This affects [section]. To complete this section, [action].

---

## Rules

- Always call `switch_customer_account` before any MCP calls
- Never fabricate numbers — every figure must come from an MCP tool response
- Always verify no `{{...}}` placeholders remain before returning the artifact
- Use `get_reported_carbon_reduction_plan` (not `get_carbon_reduction_plan_by_id`) as the default plan fetch unless the user requests a specific plan
- For the decarb roadmap, always call `run_measure_design_analysis` and include the 3 additional opportunities
- Round appropriately: energy to nearest 1 kWh, emissions to 0.1 tCO2e, costs to nearest $1
- Embed logos as base64 data URLs — no external file:// references, which break when the HTML is moved

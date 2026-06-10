# Decarbonization Roadmap — Template Manifest

## Purpose

A full building decarbonization analysis: baseline performance, recommended retrofit
measures, implementation timeline, financial projections, and emissions trajectory.

Primary audience: asset managers, property owners, sustainability consultants.

---

## MCP Tools

Call in this order:

| Tool | What it provides |
|------|-----------------|
| `get_building_model_details` | Building name, address, GFA, archetype, year built |
| `get_reported_carbon_reduction_plan` | All measures with capex, savings, payback, carbon impact; plan-level NPV/IRR |
| `get_building_model_report` | Baseline energy (kWh), EUI, energy cost, scope 1/2 emissions breakdown, yearly trajectories |
| `run_measure_design_analysis` | 3 additional measures not in the current plan |

---

## Sections

| # | Section | Data source | Required |
|---|---------|-------------|----------|
| 1 | Cover page | Building details + report date + optional logo | Yes |
| 2 | Highlights grid | Plan totals + baseline emissions | Yes |
| 3 | Executive summary | Auto-generated prose from data | Yes |
| 4 | Baseline assessment | EUI, scope breakdown, energy cost | Yes |
| 5 | Recommended measures | Measures table + bar chart | Yes |
| 6 | Implementation timeline | Measures with years | If years available |
| 7 | Financial projection | Cumulative cash flow chart | Yes |
| 8 | Emissions trajectory | Baseline vs. retrofit line chart | Yes |
| 9 | Other opportunities | run_measure_design_analysis results | Yes |

---

## Key Data Fields

**Building:**
- `name`, `address`, `gfa_sqft`, `archetype`, `year_built`

**Baseline (from report):**
- `baseline_energy_kwh`, `baseline_eui`, `baseline_cost_usd`
- `scope1_emissions_tco2e`, `scope2_emissions_tco2e`
- `baseline_trajectory[]` — year-by-year emissions without action

**Plan (from reported carbon reduction plan):**
- `measures[]` — each: `name`, `capex`, `annual_savings`, `payback_years`, `carbon_reduction_tco2e`, `implementation_year`
- `total_capex`, `total_annual_savings`, `npv`, `irr`, `simple_payback`
- `retrofit_trajectory[]` — year-by-year emissions with all measures

---

## Formatting Rules

- Energy: nearest whole kWh, with comma separator (e.g. `18,420 kWh`)
- Emissions: 1 decimal place + `tCO2e` (e.g. `94.2 tCO2e`)
- Costs: nearest dollar, `$` prefix, comma separator (e.g. `$2,341`)
- Payback: 1 decimal place + `yr` (e.g. `7.3 yr`)
- EUI: 1 decimal + `kWh/sqft/yr`
- Percentages: 1 decimal + `%`
- Missing fields: render as `—` (em dash), add data gap callout if critical
- No em dashes in prose, no exclamation points, no emojis

---

## Chart Specifications

**Emissions by scope (doughnut):** Scope 1 = `#F7931E`, Scope 2 = `#066ECC`

**Measures carbon reduction (horizontal bar):** `#00BC98`, one bar per measure, sorted by carbon reduction descending

**Emissions trajectory (line):** Baseline = `#CC303C` dashed, With measures = `#00BC98` solid; x-axis = years, y-axis = tCO2e

**Cumulative cash flow (line):** `#7700FF` with fill; starts at `-total_capex`, adds `annual_savings` per year; zero line highlighted

---

## Examples

See `examples/` directory. When generating, ask the user which example to reference.
Examples ship with this plugin; user-saved examples accumulate here over time.

| File | Description |
|------|-------------|
| `01-standard.html` | Full report, all sections, chart-heavy |

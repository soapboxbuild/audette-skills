---
name: egc-compliance-v2
description: >
  Generate a Green Communities EGC 5.1a ASHRAE 90.1-2016 performance-path compliance
  analysis. Produces a 4-page print-quality PDF report AND a filled BPS Excel template.
  Runs 3 EnergyPlus simulations (As-Built calibrated to Audette actuals, Code Minimum
  per 90.1-2016, Retrofit with Audette plan ECMs). Solar PV shown supplementally —
  it does NOT affect the compliance verdict. Use for EGC 5.1a submissions or
  pre-application compliance checks.
  Triggers on: "EGC compliance", "Green Communities compliance", "90.1 compliance",
  "run energy code analysis", "compliance report for [building]", "BPS template".
version: 2.0.0
requires:
  - audette-mcp
supersedes: egc-compliance
---

# EGC Compliance v2

Produce a Green Communities EGC 5.1a ASHRAE 90.1-2016 performance-path compliance report.

**Required:** Audette MCP, EnergyPlus 24.1.0, Node.js + Playwright (for PDF)  
**Outputs:** 4-page Letter PDF + filled BPS 5-1a Excel template

> **v2 vs. v1:** This skill uses ASHRAE 90.1-**2016** (EGC requirement), matplotlib charts
> (not Chart.js), and table-based HTML layout for reliable Playwright printing. The prior
> `egc-compliance` skill used 90.1-2022 and Chart.js — both incorrect for EGC submissions.

---

## Prerequisites

Install Python dependencies:
```bash
pip install openpyxl matplotlib numpy jinja2 --break-system-packages
npx playwright install chromium
```

Verify EnergyPlus:
```bash
energyplus --version  # must be 24.x
```

---

## Step 1: Get Building Data from Audette

Call `switch_customer_account` with the account UID from `.audette-config.json`.

Get the building UID from config or ask the user. Then call:
- `get_building_model_report(building_model_uid=<uid>)` → baseline EUI, utility actuals, geometry
- `get_building_model_details(building_model_uid=<uid>)` → address, climate zone, systems

Extract:
- GFA (ft²), stories, climate zone (e.g. "5A"), city/state
- Utility actuals: electric kWh/yr and gas therms/yr (convert gas: × 29.3 → kWh)
- As-built systems: HVAC type/fuel/efficiency, DHW fuel/efficiency, envelope U-factors, lighting LPD

---

## Step 2: Resolve ECM Plans

Call `list_building_plans(building_model_uid=<uid>)` to list all plans.

Identify:
1. **Published/reported plan** (`is_reported: true`) — contains near-term ECMs with user costs
2. **Audette Recommendations plan** (search by name) — contains Solar PV and full roadmap

Call `get_carbon_reduction_plan_by_id` for each. Merge measures: published plan wins for
duplicates; Recommendations plan adds Solar PV (typically absent from published plan).

For each measure extract: `measure_cost` (total installed), `annual_savings_kwh`,
`user_provided_cost` (bool — mark cost as "est." if false).

---

## Step 3: Run Simulations

Execute the main script:

```bash
cd skills/egc-compliance-v2
python egc_compliance_v2.py \
  --building-uid <uid> \
  --output-dir <project-folder>/reports
```

This runs 3 EnergyPlus scenarios:

| Scenario | Description | Key difference |
|----------|-------------|---------------|
| `as_built` | Calibrated to Audette utility actuals | Actual systems + calibrated infiltration/plug loads |
| `code_min` | 90.1-2016 prescriptive minimum | DHW EF=0.82, PTAC EER=12.0, 90.1-2016 envelope |
| `retrofit` | As-built + Audette plan ECMs | ECM efficiencies applied |

**Calibration:** The as-built model adjusts infiltration ACH (primary) and plug loads W/ft²
(secondary) until simulated site energy matches Audette actuals within ±3%.

**Critical:** `code_min` DHW efficiency must be **EF=0.82** regardless of as-built value.
This is the most impactful correctness issue from prior work.

---

## Step 4: Compliance Verdict

```
PASS if as_built EUI ≤ code_min EUI
```

Solar PV is shown in a supplemental "informational" row only. It does NOT affect the verdict.

---

## Step 5: Outputs

The script produces in `<output-dir>/`:

| File | Description |
|------|-------------|
| `{slug}_EGC_Compliance_Report.pdf` | 4-page Letter PDF (see layout below) |
| `5-1a_BPS_{slug}_filled.xlsx` | Green Communities BPS template filled |
| `{slug}_as_built.idf` | Calibrated EnergyPlus IDF for auditor |
| `{slug}_code_min.idf` | 90.1-2016 code-min IDF for auditor |
| `{slug}_retrofit.idf` | Retrofit scenario IDF |
| `calibration_log.json` | Calibration convergence details |

---

## PDF Layout (4 pages)

**Page 1:** Header + Project Info + Compliance Verdict (PASS/FAIL box) + EUI comparison table
+ EUI bar chart

**Page 2:** As-built vs. code-min systems table + End-use stacked bar chart + Energy breakdown table

**Page 3:** ECM table (measure, year, savings kWh/yr, cost, payback) — solar labeled informational

**Page 4:** Methodology (EnergyPlus version, weather file, model type, calibration results,
key assumptions) + Certification block with signature lines

---

## BPS Excel Template

Filled cells in the Green Communities 5-1a template:
- B12: Prebuild Baseline EUI = **Code-Min EUI** (kBtu/ft²·yr)
- B13: Prebuild Proposed EUI = **As-Built EUI** (kBtu/ft²·yr)
- B14: Postbuild Proposed EUI = **Retrofit EUI** (gross, NO solar)

Conversion: 1 kWh/ft²·yr = 3.41214 kBtu/ft²·yr

---

## Important Rules

1. **90.1-2016 not 2022** — EGC 5.1a mandates 2016; using 2022 gives wrong code-min thresholds
2. **Solar is informational** — never enter net-solar EUI in the BPS template or compliance verdict
3. **DHW code-min must be EF=0.82** — do not inherit as-built efficiency
4. **matplotlib only for charts** — Chart.js does not render in Playwright headless print
5. **Table layout only in HTML** — CSS flex/grid breaks in Chromium print mode
6. **All images base64-embedded** — file:// URIs break in Playwright headless

---

## Test Case: Emanuel Village

Building UID: `7625eb73-16c7-436e-a7be-131674d3ff60`

Expected results:
- As-Built EUI: **16.65 kWh/ft²·yr** (56.8 kBtu/ft²·yr)
- Code-Min EUI: **17.16 kWh/ft²·yr** (58.5 kBtu/ft²·yr)
- Retrofit EUI: **15.70 kWh/ft²·yr** gross (no solar)
- Verdict: **PASS** (margin: +0.51 kWh/ft²·yr, +3.0%)
- Solar: 250,000 kWh/yr generation, $740,000 cost (informational)

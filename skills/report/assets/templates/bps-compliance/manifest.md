# BPS Compliance Summary — Template Manifest

## Purpose

Regulatory compliance analysis for a building: which building performance standards apply,
current compliance status, penalty exposure, and path to compliance.

Primary audience: asset managers, compliance officers, lenders.

---

## MCP Tools

| Tool | What it provides |
|------|-----------------|
| `get_building_model_details` | Building name, address, GFA, archetype, jurisdiction |
| `run_compliance_analysis` | Applicable regulations, compliance status per regulation, penalty exposure, recommended fixes, citations |
| `get_reported_carbon_reduction_plan` | Measures that address compliance gaps (optional, for "path to compliance" section) |

---

## Sections

| # | Section | Data source | Required |
|---|---------|-------------|----------|
| 1 | Cover page | Building details + report date | Yes |
| 2 | Compliance overview | Summary status across all regulations | Yes |
| 3 | Regulation detail table | Per-regulation: name, status, limit, current performance, gap, penalty | Yes |
| 4 | Penalty exposure | Total potential annual fines, timeline | Yes |
| 5 | Path to compliance | Measures from plan that close compliance gaps | If plan available |
| 6 | Citations | Sources from run_compliance_analysis | Yes |

---

## Formatting Rules

Same as decarb-roadmap plus:
- Compliance status colors: Compliant = `#00BC98`, Non-compliant = `#CC303C`, At risk = `#F7931E`
- Penalties: annual figure + cumulative to 2030 and 2050
- Regulation names: bold, full official name first use then short form

---

## Examples

No shipped examples yet. First user-approved output will become `01-standard.html`.

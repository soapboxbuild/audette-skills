# File Categorization Patterns

This reference defines how files are categorized in the project timeline.

## Meeting Notes

**Patterns:**
- Filename contains: `meeting`, `notes`, `agenda`, `minutes`
- Examples:
  - `meeting-2026-05-31.pdf`
  - `project-notes-2026-05.docx`
  - `agenda-facilities-team.pdf`
  - `meeting-minutes-HVAC-discussion.txt`

**Category:** Meetings
**Extraction:** Parse for action items, attendees, decisions

---

## Contracts and Agreements

**Patterns:**
- Filename contains: `contract`, `agreement`, `signed`, `executed`
- Examples:
  - `signed-construction-contract.pdf`
  - `service-agreement-HVAC.pdf`
  - `executed-lease.pdf`

**Category:** Documents
**Type:** contract

---

## Reports and Assessments

**Patterns:**
- Filename contains: `report`, `assessment`, `analysis`, `study`
- Examples:
  - `energy-assessment-report.pdf`
  - `building-analysis-2026.pdf`
  - `feasibility-study.docx`

**Category:** Documents  
**Type:** report

---

## Utility Bills and Energy Data

**Patterns:**
- Filename contains: `utility`, `bill`, `energy`, `electric`, `gas`
- Examples:
  - `utility-bills-Q1-2026.xlsx`
  - `electric-bill-march.pdf`
  - `gas-usage-2025.csv`

**Category:** Documents
**Type:** utility

---

## Default (Other Documents)

**Patterns:**
- Any file not matching above patterns

**Category:** Documents
**Type:** document

---
name: full-asset-onboarding
description: >
  End-to-end onboarding of a new property into Audette: workspace setup, building
  creation, energy data compilation, equipment survey, and final report. Use when
  the user wants to onboard a new asset from scratch or when they say "do the full
  onboarding for [property]". Requires Audette MCP and property documents in the
  project folder.
---

# Full Asset Onboarding

Complete end-to-end onboarding for a new property. Runs each skill in sequence,
pausing for user confirmation between steps.

## Prerequisites

- Audette MCP connected
- Property documents in the project folder (PCNA, utility bills, etc.)
- `workspace-setup` not yet run (or user wants a fresh start)

## Steps

1. **workspace-setup** — initialize the project, link Audette account, cache building list
2. **audette-create-building** — extract property details from documents, create building in Audette
3. **audette-energy-data** — extract utility bill data, validate 12-month coverage, compile CSV
4. **audette-equipment-survey** — extract equipment details from PCNA/CNA, submit survey to Audette
5. **report** — generate final carbon reduction / decarbonization report

After each step, pause and confirm with the user before proceeding:
> "Step N complete. Ready to proceed to [next step]?"

If any step fails, surface the error clearly and ask the user whether to skip, retry, or stop.

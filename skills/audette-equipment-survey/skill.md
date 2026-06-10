---
name: audette-equipment-survey
description: >
  Extracts building equipment data from project documents (PCNA, CNA, iAuditor reports,
  equipment survey forms) and submits a structured equipment survey to Audette, triggering
  re-modelling of the building's carbon reduction plan. Use whenever the user wants to fill
  out an equipment survey, add equipment data to a building in Audette, submit HVAC details,
  or update building systems. Triggers on: "add equipment data for [property]", "fill in the
  equipment survey", "submit HVAC info to Audette", "update [property]'s systems",
  "extract equipment from the PCNA". Also use proactively when the user shares a PCNA, CNA,
  or iAuditor report and a building already exists in Audette for that property.
version: 1.0.0
requires:
  - audette-mcp
---

# Audette Equipment Survey

Read property documents, extract building equipment details, map to Audette's schema,
confirm with the user, and submit — triggering a fresh model run.

**Required:** Audette MCP

---

## Step 1: Pre-flight

Read `.audette-config.json`. If missing, tell the user to run `workspace-setup` first.

Call `switch_customer_account` with `audette_account.uid`.

Identify the target building from `buildings[]` by name, or ask the user. Note the `building_model_uid`.

---

## Step 2: Check Existing Survey

Call `get_equipment_survey` with the `building_model_uid`.

If a survey already exists, show a summary of the populated sections and ask:
> "An equipment survey already exists for this building. Update specific sections, or replace entirely?"

If updating, focus extraction on the sections the user wants to change.

If this is a first submission, continue with full extraction.

---

## Step 3: Extract Equipment Data

Read source documents. Consult `references/equipment-schema.md` for the full field list and
`references/terminology-map.md` to translate document language into Audette enum values.

### Document priority

| Document type | Best for |
|---|---|
| **iAuditor / site survey** | Most reliable — direct observation. Equipment type, install year, condition. |
| **PCNA / CNA** | HVAC type, boiler/chiller size, DHW, elevators |
| **Equipment survey forms** | Model numbers → infer type and capacity |
| **Offering memoranda** | High-level system descriptions — verify against PCNA |

### What to extract (section by section)

Work through each section of `references/equipment-schema.md`. For each:

1. Search documents for relevant equipment
2. Map terminology using `references/terminology-map.md`
3. Record the value and source (document + page/section)
4. If a field can't be found: leave it `null`. Don't guess silently — flag it for the user.

Start with `_exists` flags — they determine whether the rest of a section matters.

**Air handling:** Look for "AHU", "MAU", "makeup air", "ERV", "HRV", "DOAS", "exhaust fan". Note heating/cooling integration and supply airflow rate (CFM).

**Central plant heater:** Look for "boiler", "furnace". Note fuel type, efficiency (AFUE), brand. Note distribution: baseboard, fan coil, VAV. Check for district heat connections.

**Central plant cooler:** Look for "chiller", "cooling tower", "condenser water loop". Note tonnage (convert: 1 ton = 3.517 kW).

**Central plant heat pump:** Look for central-plant-level heat pumps (not suite mini-splits). Note ASHP vs. GSHP.

**Domestic hot water:** Look for "DHW", "water heater", "hot water tank". Note fuel, central vs. suite-level, tank size in gallons (convert: × 3.785 = litres).

**Rooftop units:** Look for "RTU", "packaged unit on roof". Note heating fuel and whether cooling is DX. Note supply airflow if documented.

**Terminal cooler:** Look for suite-level or zone-level cooling-only equipment — PTACs, window ACs, split ACs. Distinct from heat pumps.

**Terminal heater:** Look for suite-level or zone-level heating-only equipment — electric baseboards, unit heaters, gas PTACs.

**Distributed heat pumps:** Look for "mini-split", "ductless heat pump", "water loop heat pump", "WLHP". Note COP if in specs. Note whether heat pumps handle all heating/cooling load or share it with another system (→ `load_ratio`).

**Visual identification from rooftop imagery:** Arrays of small gray boxes along the roof centerline typically indicate `split_air_source_heat_pump` systems. Count of boxes ≈ number of suites served.

**Other equipment:** Check for laundry facilities (washer/dryer type, common or in-suite), elevators (count, approximate install year), escalators, rooftop solar PV (kW nameplate).

**Generic HVAC:** Note anything that doesn't fit the above — radiant panels, pool heating, district energy connections, unit heaters on a separate loop. Every field is required; see `references/equipment-schema.md` for the full generic structure.

### Unit conversions

| From | To | Multiply by |
|---|---|---|
| MBH | kW | × 0.293 |
| tons | kW | × 3.517 |
| BTU/h | kW | ÷ 3,412 |
| gallons | litres | × 3.785 |

### Decrypting password-protected PDFs

If the Read tool fails on a PDF:

```bash
pip install pikepdf --break-system-packages
python3 -c "
import pikepdf, sys
src = sys.argv[1]
dst = src.replace('.pdf', '_decrypted.pdf')
pikepdf.open(src, password='').save(dst)
print(f'Decrypted → {dst}')
" "<path>"
```

---

## Step 4: Confirm with the User

Present a summary table before submitting anything:

```
Building: [Name] ([building_model_uid])
Existing survey: [Yes — submitted YYYY-MM-DD] / [None]

Extracted equipment:

Section               | Field                        | Value              | Source
----------------------|------------------------------|--------------------|------------------
central_plant_heater  | type                         | gas_boiler         | PCNA p.14
central_plant_heater  | terminal_units               | baseboards         | PCNA p.14
central_plant_heater  | size                         | 105 kW (3×120 MBH) | PCNA p.14
central_plant_heater  | install_year                 | 1994               | PCNA p.14
domestic_hot_water    | type                         | gas_heater         | PCNA p.15
domestic_hot_water    | central_distribution         | true               | PCNA p.15
...

⚠️ Not found — please supply or confirm null:
  - air_handling_equipment type
  - heat_pump COP values
```

Ask the user to confirm or correct before proceeding. For ambiguous fields, ask directly rather than making a silent choice.

---

## Step 5: Submit

Call `submit_equipment_survey` with the `building_model_uid` and the complete `equipment_survey` dict.

**Every top-level section must be present**, even if `_exists` is false (set all other fields to `null`).

Use the empty template from `references/equipment-schema.md` as a starting point and fill in confirmed values.

For `generic_hvac_equipment`: pass `[]` if no generic equipment. If items exist, all fields are required and non-nullable — omit the entry entirely rather than passing null values.

Re-modelling is triggered automatically on successful submission.

---

## Step 6: Confirmation

```
Equipment survey submitted.

  Building:     [building_name]
  Sections:     [list of sections where exists=true]
  Re-modelling: triggered — updated carbon plan will be available shortly

[If any sections were null:]
  Not provided: [list] — these can be updated later by running this skill again.

Next steps:
  1. Energy data     → audette-energy-data
  2. Full report     → report
```

---

## Error Handling

**MCP rejects the survey**
> Audette rejected the survey: [error]. This usually means an invalid enum value or a required field is missing. Check the field named in the error and resubmit.

**Equipment found in documents but type is ambiguous**
> I found [description] in [source]. This could be [option A] or [option B]. Which is correct?

**No source documents found**
> No PCNA, CNA, or equipment survey documents found in this workspace. Please add the relevant files and try again — or answer the questions manually.

---

## Rules

- Always call `switch_customer_account` before any MCP calls
- Always check for an existing survey before extracting
- Never submit without user confirmation (Step 4)
- Never invent equipment not mentioned in source documents — `null` is better than a wrong value
- Every section must be in the payload; omitting sections causes API errors
- Flag all ambiguous values in the confirmation table rather than silently choosing
- For `generic_hvac_equipment`, all fields are required and non-nullable — omit the entry rather than passing nulls

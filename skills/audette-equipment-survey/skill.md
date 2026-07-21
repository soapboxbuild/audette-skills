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

⚠️ **Never assume an existing survey is correct — audit its `*_size` units first.** Earlier runs (and
imports) stored the WRONG units in `*_size` fields — kW, kW-scaled, or tank volume in litres/gallons —
which silently corrupt the whole energy model. Before treating a stored survey as usable, sanity-check
every size against the tons rule (see "Unit conversions" below):
> - a `domestic_hot_water_heater_size` that equals tank litres/gallons (e.g. `169` for ~45-gal tanks) is wrong;
> - a `terminal_heater_size`/`_cooler_size` far below the load the equipment implies (e.g. `268` when
>   254 units × 36 MBH ÷ 12 ≈ 762 tons, or `199` when the DX load is 565 tons) is kW-scaled, not tons.

When a stored size fails the check, **re-derive it in tons and OVERWRITE the survey** via
`submit_equipment_survey` — do not carry the bad value forward, and do not report the survey as
"already correctly sized." A complete survey in the wrong units is worse than none.

If updating, focus extraction on the sections the user wants to change.

If this is a first submission, continue with full extraction.

---

## Step 3: Extract Equipment Data

Read source documents. Consult:
- `references/equipment-schema.md` — full field list and valid enum values
- `references/terminology-map.md` — translate document language into Audette enum values
- `references/audette-topology.md` — **how each equipment type drives the energy model** (multipliers, fuel resolution, rooftop detection mapping, common pitfalls)
- `references/submission-guide.md` — **exact call format, complete payload template, all 15 API validation rules, valid system combinations, error handling** — read this before Step 5

**Determine primary heating fuel first** (topology doc Section 1) — it affects every
downstream calculation. Use the fuel resolution priority rule before proceeding to other sections.

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

**Central plant heater:** Look for "boiler", "furnace". Note fuel type, efficiency (AFUE), brand. Note distribution: baseboard, fan coil, VAV. Check for district heat connections. Note capacity — submit in **ton-equivalents** (do not convert to kW).

**Central plant cooler:** Look for "chiller", "cooling tower", "condenser water loop". Note tonnage — submit in **tons** (do not convert to kW).

**Central plant heat pump:** Look for central-plant-level heat pumps (not suite mini-splits). Note ASHP vs. GSHP. Note capacity — submit in **ton-equivalents** (do not convert to kW).

**Domestic hot water:** Look for "DHW", "water heater", "hot water tank". Note fuel, central vs. suite-level. Note capacity as a **ton-equivalent** (see the note on DHW below — this is the heater's thermal capacity, not tank volume).

**Rooftop units:** Look for "RTU", "packaged unit on roof". Note heating fuel and whether cooling is DX. Note supply airflow if documented.

**Terminal cooler:** Look for suite-level or zone-level cooling-only equipment — PTACs, window ACs, split ACs. Distinct from heat pumps.

**Terminal heater:** Look for suite-level or zone-level heating-only equipment — electric baseboards, unit heaters, gas PTACs. Note capacity — submit in **ton-equivalents** (do not convert to kW).

**Distributed heat pumps:** Look for "mini-split", "ductless heat pump", "water loop heat pump", "WLHP". Note COP if in specs. Note whether heat pumps handle all heating/cooling load or share it with another system (→ `load_ratio`).

**Visual identification from rooftop imagery:** Arrays of small gray boxes along the roof centerline typically indicate `split_air_source_heat_pump` systems. Count of boxes ≈ number of suites served.

**Other equipment:** Check for laundry facilities (washer/dryer type, common or in-suite), elevators (count, approximate install year), escalators, rooftop solar PV (kW nameplate).

**Generic HVAC:** Note anything that doesn't fit the above — radiant panels, pool heating, district energy connections, unit heaters on a separate loop. Every field is required; see `references/equipment-schema.md` for the full generic structure.

### Unit conversions

| From | To | Multiply by |
|---|---|---|
| MBH | tons | ÷ 12 |
| BTU/h | tons | ÷ 12,000 |
| kW | tons | ÷ 3.517 |
| gallons | litres | × 3.785 (tank volume only — see DHW note below) |

> **All heating, cooling, and DHW capacity sizes** (`central_plant_cooler_size`, `central_plant_heater_size`, `central_plant_heat_pump_size`, `terminal_cooler_size`, `terminal_heater_size`, `terminal_heater_cooler_size`, `heat_pump_size`, `domestic_hot_water_heater_size`) must be submitted as **ton-equivalents** — never kW, never litres/gallons. Per Christopher (2026-07-16): "all heating cooling and DHW size must be converted to ton equivalents." This overrides ANY reference doc (`references/equipment-schema.md`, `references/submission-guide.md`, `references/audette-topology.md`, `references/terminology-map.md`) that shows kW, litres, or gallons for these `*_size` fields — if you see that, the reference doc is stale, not the requirement.
>
> **DHW note:** a DHW heater's nameplate/recovery capacity is a thermal rating (BTU/h or kW input) — convert that to tons the same way as any other heating capacity, and prefer this whenever it's documented. **Rule of thumb when only tank volume is known** (no nameplate/recovery rating in the source): `tons ≈ gallons ÷ 40` (litres ÷ 151), based on typical storage water heater sizing (~4.5 kW element per 40–50 gal tank ≈ 1 ton per ~40 gal, for both electric and gas storage units). Flag when this fallback was used instead of an actual nameplate rating, so it's distinguishable from a documented value.

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
central_plant_heater  | size                         | 30 tons (3×120 MBH ÷ 12) | PCNA p.14
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

## Step 4b: Pre-validate Against API Rules

Before submitting, verify the payload does not violate the 15 API validation rules
listed in `references/submission-guide.md`. Key checks:

1. `domestic_hot_water_heater_exists` must be `true` — API always requires DHW
2. `central_plant_cooler` and `terminal_cooler` are mutually exclusive — pick one
3. `central_plant_heater` and `terminal_heater` are mutually exclusive — pick one
4. At least one of `air_handling_equipment_exists` or `rooftop_unit_exists` must be `true`
5. If `rooftop_unit_exists = true`, `rooftop_unit_cooling_type` must be provided
6. If `heat_pump_type = "water_loop_heat_pump"`, a boiler must exist (Rule 13) and no chiller (Rule 14)
7. Furnace types conflict with: unit heaters, baseboards, central cooling, most AHU types (Rules 9–12)

Flag any conflicts in the confirmation table and ask the user to resolve before submitting.

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

---
name: equipment-gap-questionnaire
description: >
  This skill should be used when the user asks to "fill gaps in equipment survey",
  "complete the equipment survey", "interview building operator", "questionnaire for
  building systems", or wants to gather missing equipment details through interactive
  Q&A. Analyzes existing building system data from local documents, identifies gaps
  relative to Audette's equipment survey schema, and conducts a conversational interview
  with a building operator to collect missing information until the survey is 100% complete.
version: 1.0.0
---

# Equipment Gap Questionnaire

Conduct an interactive questionnaire with building operators to fill gaps in equipment
survey data. This skill extracts available system information from local documents, identifies
what's missing compared to Audette's equipment survey schema, and interviews the operator
using natural language Q&A until all required fields are complete.

## Required MCP Connections

| MCP | Tools used | If disconnected |
|-----|-----------|-----------------|
| **Audette** | `get_building_model_details`, `get_equipment_survey`, `submit_equipment_survey` | Cannot proceed — ask user to reconnect |

**No other MCPs required** - Uses local file reading (Read tool) for document extraction.

---

## Workflow Overview

```
1. Extract available data from documents/existing survey
2. Identify gaps relative to equipment-schema.md
3. Interview operator using AskUserQuestion
4. Parse natural language responses → map to schema fields
5. Ask follow-up questions for incomplete sections
6. Repeat until survey is 100% complete
7. Confirm final survey with operator
8. Submit to Audette
```

---

## Pre-flight

Call `switch_customer_account` with the Audette customer account UID from the system prompt.
This is required before any Audette write operations — omitting it causes HTTP 401.

If no account UID is in the system prompt, call `list_customer_accounts` and ask the user to select one.

## Step 1: Identify Building

The building UID is in the system prompt if this asset has been linked to Audette.
If not, call `list_buildings` to find it by name or address, or ask the user directly.
You need the **building_model_uid** — verify it exists by calling `get_building_model_details`.

---

## Step 2: Gather Available Equipment Data

### 2a. Check for Existing Survey

Call `get_equipment_survey` with the `building_model_uid`. If a survey exists, load it
as the starting point. Note which fields are already populated vs. null.

### 2b. Extract from Documents (Optional)

If project documents are available, use Grep/Read to search for system descriptions.

**Use Glob to find relevant documents:**
```
**/*.pdf
**/PCA*.pdf
**/CNA*.pdf
**/*equipment*.pdf
**/*mechanical*.pdf
```

**Use Grep with search patterns:**

| System | Search Pattern (case-insensitive) |
|--------|----------------------------------|
| Heating | `boiler\|furnace\|heat pump\|heating system\|HVAC\|BTU\|MMBH` |
| Cooling | `chiller\|air condition\|cooling\|DX\|tons\|SEER` |
| DHW | `domestic hot water\|DHW\|water heater\|gallon` |
| Ventilation | `ventilation\|air handling\|AHU\|makeup air\|ERV\|HRV\|CFM` |
| Lighting | `lighting\|LED\|fluorescent\|lamp\|fixture\|occupancy sensor` |
| Elevators | `elevator\|lift\|hydraulic\|traction` |
| Renewables | `solar\|photovoltaic\|PV\|renewable\|battery` |

**When Grep finds matches:** Use Read to get the surrounding context (pages/sections).
Extract specifications like capacity, efficiency, fuel type, installation dates.

Aggregate findings into notes about each system category.

### 2c. Load Equipment Schema

Read the equipment schema from the `audette-equipment-survey` skill:
`skills/audette-equipment-survey/references/equipment-schema.md`

This contains all sections, fields, valid enum values, and field descriptions you'll need
for gap analysis and question generation.

---

## Step 3: Perform Gap Analysis

For each major equipment section in the schema, determine its completeness:

| Section | Status Logic |
|---------|-------------|
| **Complete** | `_exists` field is set AND all required fields for that system are populated |
| **Partially complete** | `_exists = true` but some fields are null |
| **Unknown** | `_exists` field is null (don't know if system exists) |
| **Not applicable** | `_exists = false` (system doesn't exist in building) |

### Critical vs. Optional Fields

**Critical fields** (required if `_exists = true`):
- `*_type` (equipment type enum)
- `*_size` or `*_capacity` (impacts carbon model significantly)
- `*_average_installation_year` (determines remaining useful life)

**Optional but helpful fields**:
- `*_heating_type`, `*_cooling_type` (refines model)
- `*_terminal_units` (distribution method)
- `*_count` (for elevators, rooftop units)

### Gap Prioritization

Organize gaps into:

1. **Critical unknowns**: `_exists` is null (don't know if system exists)
2. **High priority**: `_exists = true` but type or size missing
3. **Medium priority**: Installation year, efficiency details missing
4. **Low priority**: Secondary characteristics missing

---

## Step 4: Generate Targeted Questions

For each gap, generate a natural language question appropriate for a building operator.

Read `references/question-templates.md` now — it contains example questions for each
equipment section, accounting for typical operator responses.

### Question Design Principles

**DO:**
- Use plain language, not technical jargon (unless operator is highly technical)
- Ask about observable equipment ("What type of boilers do you have?")
- Accept ranges and estimates ("About how old are the boilers? Best guess is fine.")
- Ask for counts and sizes together ("How many chillers, and what's the capacity?")
- Provide examples in parentheses ("Natural gas, electric, oil, or other?")

**DON'T:**
- Ask for exact enum values (operator won't know "condensing_gas_boiler" enum)
- Require precision when estimates work (installation year ±2 years is fine)
- Use acronyms without explanation (say "domestic hot water" not just "DHW")
- Ask multiple unrelated questions in one (break into separate questions)

### Example Question Transformations

| Schema Field | Bad Question | Good Question |
|--------------|--------------|---------------|
| `central_plant_heater_type` | "What's the central_plant_heater_type enum value?" | "What type of heating system serves the building? (Boiler, furnace, heat pump, or other?)" |
| `central_plant_heater_size` | "What's the heater size in kW?" | "What's the total heating capacity? (Can be in MBH, BTU/hr, kW, or tons — I'll convert to tons)" |
| `air_handling_equipment_exists` | "Does air_handling_equipment_exists = true?" | "Is there a central air handling unit or ventilation system?" |

---

## Step 5: Conduct Interactive Interview

Use **AskUserQuestion** to interview the building operator. Work through gaps in priority
order (critical → high → medium → low).

### Interview Flow

1. **Start with critical unknowns** (whether systems exist)
   - "Does the building have a central heating system, or is heating suite-level?"
   - "Is there a central chiller or cooling system?"
   
2. **For confirmed systems, gather details**
   - "You mentioned a central boiler. What type? (Gas, electric, oil?)"
   - "How many boilers are there, and what's the capacity of each?"
   - "About how old are the boilers? Even a rough estimate helps."

3. **Parse responses and map to schema**
   - "2 Weil-McLain gas boilers at 500 MBH each" →
     ```
     central_plant_heater_exists: true
     central_plant_heater_type: "gas_boiler"  (Weil-McLain typically makes non-condensing)
     central_plant_heater_size: 83.3  (1000 MBH ÷ 12 = 83.3 tons)
     ```

4. **Ask follow-ups for ambiguity**
   - Response: "Gas boilers"
   - Follow-up: "Are these condensing boilers (high-efficiency, AFUE ≥90%) or standard boilers?"

5. **Confirm and move to next gap**
   - "Got it — 2 standard gas boilers, 500 MBH each, installed around 2005. Now, about the
     cooling system..."

### Handling Natural Language Responses

Building operators will respond conversationally. Parse key information:

| Operator Response | Extract |
|-------------------|---------|
| "2 boilers, 500 MBH each" | Count: 2, Size per unit: 500 MBH → Total: 1000 MBH ÷ 12 = 83.3 tons |
| "Old gas boiler, maybe 1995" | Type: gas_boiler, Installation year: 1995 |
| "We have Carrier rooftop units on each floor, probably 15 total, 5 ton each" | Type: split_system_air_conditioner (likely), Count: 15, Size per unit: 5 tons → Total: 75 tons |
| "Hot water is in each suite, electric" | central_distribution: false, Type: electric_storage |
| "No chiller, just window ACs" | central_plant_cooler_exists: false |

### Clarification Strategy

When responses are ambiguous:

**If manufacturer/model mentioned:** Use it to infer type
- "Weil-McLain" → likely standard gas boiler (not condensing)
- "Navien" → likely condensing gas boiler or tankless water heater
- "Carrier" → could be rooftop unit or split system (ask follow-up)

**If capacity units unclear:** Ask for clarification
- "500" → "Is that 500 MBH, 500 kW, or 500 BTU/hr?"

**If age is vague:** Accept estimates
- "Pretty old" → "Best guess — installed in the 1990s, 2000s, or earlier?"

**If distribution method unclear:**
- "How is heat distributed? Radiators, baseboard, forced air, or something else?"

---

## Step 6: Validate Completeness

After each section, verify all required fields are populated.

### Completeness Checklist

For each section where `_exists = true`, confirm:
- [ ] Type field populated with valid enum value
- [ ] Size/capacity field populated (if applicable)
- [ ] Installation year populated (estimate acceptable)
- [ ] Distribution/terminal units specified (for central plants)

### Handle Edge Cases

**Multiple systems of different types:**
- If building has 2 boilers + 1 heat pump, ask: "Which is the primary heating system?"
  or "Do boilers handle majority of the load, or heat pump?"
- Survey schema expects one primary system per section. If truly hybrid, document in notes
  and choose the dominant system for the survey.

**Partial retrofits:**
- If half the building has new equipment and half has old: "What year was the most recent
  equipment installed? We'll use that as the average."

**Unknown details:**
- If operator genuinely doesn't know (e.g., "Not sure about chiller capacity"), note it:
  - Option 1: Estimate based on building size (e.g., "For a 50,000 SF building, typical
    chiller is 150-200 tons. Does that sound right?")
  - Option 2: Mark for site visit / nameplate verification

---

## Step 7: Review and Confirm

Once all gaps are filled, present the complete survey back to the operator for confirmation.

### Confirmation Format

```markdown
## Equipment Survey Summary

I've gathered the following information. Please review and confirm before I submit to Audette:

### Heating System ✓
- **Type:** Gas boiler (standard, non-condensing)
- **Capacity:** 83.3 tons (1,000 MBH total — two 500 MBH boilers)
- **Distribution:** Hydronic baseboard radiators
- **Installation Year:** 2005

### Cooling System ✓
- **Type:** Rooftop units (split system air conditioners)
- **Capacity:** 75 tons (15 units @ 5 tons each)
- **Installation Year:** 2010

### Domestic Hot Water ✓
- **Configuration:** Suite-level (not centrally distributed)
- **Type:** Electric storage water heaters
- **Capacity:** 4.5 kW element rating ÷ 3.517 = **1.28 tons** per unit (50 gal tank volume noted for reference — volume is not itself convertible to tons)
- **Installation Year:** 2015

[... continue for all sections ...]

**Does this look correct? Any changes needed before I submit?**
```

If operator identifies errors or additions, revise the affected sections and re-confirm.

---

## Step 8: Submit to Audette

Once confirmed, call `submit_equipment_survey` with the complete survey payload.

### Submission Format

Build the JSON payload according to the equipment schema. All top-level sections must be
present. For sections where equipment doesn't exist, set `_exists: false` and all other
fields to `null`.

Example payload structure:

```json
{
  "building_model_uid": "abc-123-def",
  "air_handling_equipment": {
    "air_handling_equipment_exists": true,
    "air_handling_equipment_type": "packaged_air_handling_unit",
    "air_handling_equipment_heating_type": "hydronic",
    "air_handling_equipment_cooling_type": "direct_expansion",
    "air_handling_equipment_supply_air_rate": 12000.0,
    "air_handling_equipment_average_installation_year": 2008
  },
  "central_plant_cooler": {
    "central_plant_cooler_exists": false,
    "central_plant_cooler_type": null,
    "central_plant_cooler_terminal_units": null,
    "central_plant_cooler_size": null,
    "central_plant_cooler_average_installation_year": null
  },
  "central_plant_heater": {
    "central_plant_heater_exists": true,
    "central_plant_heater_type": "gas_boiler",
    "central_plant_heater_terminal_units": "baseboards",
    "central_plant_heater_size": 293.0,
    "central_plant_heater_average_installation_year": 2005
  },
  ... [all other sections]
}
```

After submission, inform the operator that the survey is complete and carbon modeling will
be re-run automatically.

---

## Important Rules

### Parsing Natural Language

- **Be generous with interpretation**: "Old gas boilers" → infer `gas_boiler` type
- **Confirm assumptions**: "I'm assuming these are standard gas boilers, not condensing.
  Correct?"
- **Handle units gracefully**: Convert MBH, BTU/hr, or kW to ton-equivalents for every heating/cooling/DHW size field — never submit kW or gallons/litres for these fields
- **Accept estimates**: Installation year ±2 years is fine, capacity ±10% is fine

### Unit Conversions

Keep these conversions ready:

| From | To | Formula |
|------|-----|---------|
| MBH (1000 BTU/hr) | tons | MBH ÷ 12 |
| BTU/hr | tons | BTU/hr ÷ 12,000 |
| kW | tons | kW ÷ 3.517 |
| Gallons | Litres | Gallons × 3.785 (tank volume only — not a capacity conversion) |

> **All heating, cooling, and DHW capacity sizes** (`central_plant_cooler_size`, `central_plant_heater_size`, `central_plant_heat_pump_size`, `terminal_cooler_size`, `terminal_heater_size`, `terminal_heater_cooler_size`, `heat_pump_size`, `domestic_hot_water_heater_size`) must be submitted as **ton-equivalents** — never kW, never litres/gallons. Per Christopher (2026-07-16): "all heating cooling and DHW size must be converted to ton equivalents." A DHW heater's thermal/recovery rating converts to tons the same way as any other heating capacity; tank **volume** (gallons/litres) is a separate quantity that cannot be converted to tons — if only volume is documented with no power rating, say so rather than forcing a number.

### Enum Mapping

Read `references/enum-mapping.md` for common operator terms → schema enum mappings.

When operator says "gas boiler," infer:
- If they mention "high efficiency" or "condensing" → `condensing_gas_boiler`
- Otherwise → `gas_boiler` (standard)
- If unsure, ask: "Is this a condensing boiler (AFUE ≥90%)?"

### Never Invent Data

If operator doesn't know something and can't estimate:
- Mark it in notes: "Chiller capacity unknown — requires site visit for nameplate"
- Set field to `null` in submission
- Inform user which fields are still missing

---

## When to Use This Skill vs. Other Skills

**Use `equipment-gap-questionnaire` when:**
- Documents don't provide enough detail to complete survey
- User wants to interview building operator to fill gaps
- Existing survey is partially complete and needs finishing
- Interactive Q&A is preferred over manual form-filling

**Use `audette-equipment-survey` when:**
- Complete equipment data is already in documents (PCNA, CNA, etc.)
- No operator interview needed
- Extracting and submitting in one shot

**Use `system-details` when:**
- User wants a comprehensive overview (not submitting to Audette)
- Preparing for a meeting or review
- Synthesis-oriented, not submission-oriented

---

## Additional Resources

### Reference Files

For question templates and enum mapping:
- **`references/question-templates.md`** - Example questions for each equipment section,
  handling typical operator responses
- **`references/enum-mapping.md`** - Common operator terminology mapped to schema enum values

The equipment schema itself lives in the `audette-equipment-survey` skill and should be
loaded from there:
`skills/audette-equipment-survey/references/equipment-schema.md`

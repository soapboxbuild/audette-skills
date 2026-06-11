---
name: system-details
description: >
  This skill should be used when the user asks to "review building systems", "what are
  the HVAC systems", "describe the mechanical systems", "what equipment is in the building",
  "give me system details", "review major building systems", or any request for a comprehensive
  overview of a property's mechanical, electrical, and plumbing systems. Combines data from
  equipment surveys, topology analysis, and local document search to produce a detailed
  synthesis of all building systems including HVAC, domestic hot water, lighting, elevators,
  and renewable energy systems.
version: 1.0.0
---

# System Details

Generate a comprehensive description of a building's mechanical, electrical, and plumbing
systems by combining equipment surveys and topology analysis from Audette platform with
local document search.

## Required MCP Connections

| MCP | Tools used | If disconnected |
|-----|-----------|-----------------|
| **Audette** | `get_building_model_details`, `get_equipment_survey`, `get_building_equipment_topology` | Cannot access equipment data — ask user to reconnect |

**No other MCPs required** - Uses local file reading (Read tools) for document context.

---

## Step 1: Read Project Config and Identify Building

Read `.audette-config.json` from the workspace root. Extract `audette_account.name` and
`audette_account.uid`. If the file is missing, ask the user to run `workspace-setup` first.

Call `switch_customer_account` with `audette_account.uid` from config.

Ask the user which building they want system details for if not clear from context. You
need the **building_model_uid** from:
- The workspace config's `buildings[]` array
- A previous conversation reference
- The user telling you directly

Once you have the UID, verify it exists by calling `get_building_model_details`.

---

## Step 2: Gather Equipment Survey Data

Call `get_equipment_survey` with the `building_model_uid` to retrieve structured equipment
data if a survey has been submitted for this building.

The equipment survey contains:
- Central heating plant details (type, fuel, capacity, install year, terminal units)
- Central cooling plant details (type, capacity, install year, distribution)
- Domestic hot water systems (fuel type, central vs. suite-level, capacity)
- Air handling equipment (type, count, capacity, economizer presence)
- Rooftop units (count, capacity, heating/cooling types)
- Heat pumps (type, count, capacity)
- Lighting systems (technology, controls)
- Elevators (count, type)
- Photovoltaic systems (capacity in kW)

If no survey exists, note this — proceed with other data sources. If a survey exists
but has gaps (many null values), note which sections are incomplete.

---

## Step 3: Gather Equipment Topology

Call `get_building_equipment_topology` with the `building_model_uid` to retrieve the
modeled equipment topology.

This returns a structured graph of equipment relationships showing:
- How systems connect (e.g., boiler → distribution loop → terminal units)
- Equipment dependencies and flow paths
- System boundaries and interfaces

The topology is particularly useful for understanding:
- How heating/cooling is distributed through the building
- Central vs. decentralized system architecture
- Integration points between systems

If topology analysis hasn't been run, the call will return empty or minimal data. Note
this and rely on survey + document data.

---

## Step 4: Search Local Documents for System Context

Search project files for system specifications and descriptions. Two approaches available:

### Approach A: Semantic Search (RAG) - Recommended if Available

If `.rag-index/` exists in the workspace, use the `rag_search` MCP tool for semantic search:

```bash
# Check if RAG index exists
if [ -d ".rag-index" ]; then
  # Use semantic search for each system category
  heating_info=$(python3 skills/`rag_search`/scripts/query.py \
    "heating system boiler furnace specifications capacity" \
    --json --top-k 3)
  
  cooling_info=$(python3 skills/`rag_search`/scripts/query.py \
    "cooling system chiller air conditioning specifications" \
    --json --top-k 3)
  
  # Extract relevant chunks and read
  echo "$heating_info" | jq -r '.[].text'
fi
```

**Advantages of RAG:**
- Semantic understanding (finds "installed in 2005" for query "how old")
- Ranked by relevance (best matches first)
- Handles synonyms and paraphrasing

**When to use:**
- Large document sets (>10 PDFs)
- Questions requiring conceptual understanding
- User has already run ``rag_search`` ingestion

### Approach B: Keyword Search (Grep) - Fallback

If no RAG index exists, use Grep and Read tools.

Read `references/system-categories.md` now — it contains targeted search patterns for
each major system category.

**Step 4b-1: Identify relevant documents**

Use Glob to find likely documents:
```bash
**/*.pdf
**/PCA*.pdf
**/CNA*.pdf
**/*equipment*.pdf
**/*mechanical*.pdf
**/*specifications*.pdf
```

**Step 4b-2: Search for system keywords**

Use Grep to search across documents for each system category. Search patterns:

| Category | Search Pattern (case-insensitive) |
|----------|-----------------------------------|
| **Heating** | `boiler\|furnace\|heat pump\|heating system\|HVAC\|BTU\|MMBH\|kW heating` |
| **Cooling** | `chiller\|air condition\|cooling\|DX\|tons\|SEER\|EER\|refrigerant` |
| **DHW** | `domestic hot water\|DHW\|water heater\|gallon\|recovery rate` |
| **Ventilation** | `ventilation\|air handling\|AHU\|makeup air\|ERV\|HRV\|CFM\|air changes` |
| **Controls** | `building automation\|BAS\|BMS\|controls\|thermostat\|HVAC control` |
| **Lighting** | `lighting\|LED\|fluorescent\|lamp\|fixture\|occupancy sensor\|lux` |
| **Elevators** | `elevator\|lift\|hydraulic\|traction\|passenger\|freight` |
| **Renewables** | `solar\|photovoltaic\|PV\|renewable\|battery\|storage\|kW DC` |
| **Envelope** | `window\|glazing\|insulation\|R-value\|U-value\|envelope\|thermal` |

**Step 4b-3: Read relevant sections**

When Grep finds matches, use Read tool to read the surrounding context (pages/sections
where matches were found). Extract:
- Equipment specifications (capacity, efficiency, fuel type)
- Installation dates and ages
- System descriptions and topology
- Manufacturer and model numbers

### Step 4c: Cross-reference Findings

Compare information found in documents (via RAG or Grep) with data from equipment survey
(Step 2) and topology (Step 3). Note discrepancies or gaps.

**Best practice:** Use both approaches if available - RAG for discovery, Grep for validation of specific terms.

---

## Step 5: Synthesize the System Details Report

Combine data from Steps 2-4 into a structured narrative organized by system category.

### Report Structure

Organize the report into these sections:

#### 1. Executive Summary

Brief overview (2-3 sentences) covering:
- Building name and address
- Total square footage
- Primary HVAC configuration (e.g., "central gas-fired heating with suite-level cooling")
- Notable systems or recent upgrades

#### 2. Heating System

Describe:
- **Type:** Central plant (boiler/furnace/heat pump) or decentralized
- **Fuel:** Natural gas, electric, oil, steam district energy
- **Capacity:** Total heating capacity in kW or MBH
- **Distribution:** Baseboards, radiators, fan coils, VAV, radiant, forced air
- **Age:** Installation year and remaining useful life estimate
- **Efficiency:** AFUE, HSPF, or other efficiency ratings if available
- **Topology:** How heat is distributed (e.g., "two gas boilers serve a hydronic loop
  feeding baseboard radiators in residential units")

**Cross-reference:** Equipment survey `central_plant_heater` section + local document search +
topology graph.

#### 3. Cooling System

Describe:
- **Type:** Central chiller, rooftop units, split systems, window units, heat pumps
- **Capacity:** Total cooling capacity in tons or kW
- **Distribution:** Chilled water, DX, ductless mini-splits
- **Age:** Installation year and remaining useful life
- **Efficiency:** SEER, EER, kW/ton if available
- **Topology:** How cooling is distributed

**Cross-reference:** Equipment survey `central_plant_cooler`, `rooftop_units` sections +
document queries + topology.

#### 4. Domestic Hot Water

Describe:
- **Configuration:** Central distribution vs. suite-level heaters
- **Fuel:** Gas, electric, solar thermal
- **Capacity:** Storage tank size in gallons/litres, recovery rate
- **Age:** Installation year
- **Efficiency:** Energy factor (EF) or thermal efficiency if available

**Cross-reference:** Equipment survey `dhw_heater` section + local document search.

#### 5. Ventilation

Describe:
- **Type:** Central air handling units, dedicated outdoor air systems (DOAS), ERV/HRV,
  exhaust-only
- **Capacity:** CFM or air changes per hour (ACH)
- **Controls:** Constant volume, variable volume, demand-controlled ventilation
- **Heat recovery:** Presence of energy recovery ventilators
- **Age:** Installation year

**Cross-reference:** Equipment survey `air_handling_equipment` section + local document search +
topology.

#### 6. Building Controls & Automation

Describe:
- **BAS/BMS:** Presence and type of building automation system
- **HVAC controls:** Thermostats, zone controls, scheduling
- **Lighting controls:** Occupancy sensors, daylight harvesting, time clocks
- **Integration:** Systems integrated into BAS

**Cross-reference:** Equipment survey `lighting` section + local document search.

#### 7. Lighting

Describe:
- **Technology:** LED, fluorescent, incandescent, HID
- **Controls:** Manual, occupancy sensors, daylight dimming, networked controls
- **Recent upgrades:** LED retrofits or control upgrades
- **Coverage:** Common areas vs. tenant spaces

**Cross-reference:** Equipment survey `lighting` section + local document search.

#### 8. Elevators

Describe:
- **Count:** Number of passenger and freight elevators
- **Type:** Hydraulic, traction (geared or gearless)
- **Age:** Installation year and modernization history
- **Regenerative capability:** If elevator can feed power back to grid

**Cross-reference:** Equipment survey `elevators` section + local document search.

#### 9. Renewable Energy

Describe:
- **Solar PV:** Capacity in kW, location (rooftop, carport, ground-mount), age
- **Solar thermal:** If present for DHW or space heating
- **Other renewables:** Geothermal, wind, battery storage

**Cross-reference:** Equipment survey `photovoltaic` section + local document search.

#### 10. Building Envelope

Describe:
- **Windows:** Glazing type, U-value, age
- **Insulation:** Wall and roof insulation R-values
- **Air sealing:** Blower door test results if available
- **Recent upgrades:** Window replacements, envelope improvements

**Cross-reference:** Local document search only (not in equipment survey schema).

#### 11. Data Completeness & Gaps

Summarize:
- **Complete sections:** Which systems have comprehensive data
- **Incomplete sections:** Which systems need more data (e.g., "Lighting controls not
  documented in available sources")
- **Conflicting data:** Any discrepancies between equipment survey and documents (flag
  these for user review)
- **Recommended next steps:** Suggest site visits, equipment surveys, or document
  collection to fill gaps

---

## Step 6: Format and Present

### Output Format

Present the report as structured Markdown with:
- Clear section headers (use `##` for main categories)
- Bullet lists for specifications
- **Bold** for field labels
- Source citations in parentheses (e.g., "Central boiler plant (Equipment Survey, 2024)")
- Tables for multi-system comparisons if helpful

### Example Output Format

```markdown
# Building Systems Overview: [Building Name]

**Address:** [Full address]  
**Gross Floor Area:** [SF/SM]  
**Property Type:** [Office/Multifamily/etc.]  
**Report Generated:** [Date]

---

## Executive Summary

[2-3 sentence summary]

---

## 1. Heating System

**Type:** Central gas-fired boiler plant  
**Capacity:** 1,056 kW (3.6 MMBH)  
**Distribution:** Hydronic baseboard radiators  
**Fuel:** Natural gas  
**Installation Year:** 1994  
**Remaining Useful Life:** ~6 years (typical 30-year lifespan)  
**Efficiency:** 80% AFUE (estimated, non-condensing)

The building uses three atmospheric gas boilers (352 kW each) serving a hydronic
distribution loop that feeds baseboard radiators in all residential units. The system
is original to the building and nearing end of useful life. (Source: Equipment Survey
2024, PCNA Report p.14)

---

[Continue for all system categories...]
```

---

## Important Rules

- **Never invent data:** If a field is unknown across all sources, state "Not documented
  in available sources" rather than guessing
- **Flag conflicts:** If equipment survey says one thing and documents say another,
  present both and note the discrepancy
- **Cite sources:** Every major claim should reference where the data came from
  (Equipment Survey, document name + page, or topology analysis)
- **Use consistent units:** Convert to metric where possible, but show US units in
  parentheses for North American projects (e.g., "379 litres (100 gallons)")
- **Highlight age/obsolescence:** Flag systems nearing or past typical end-of-life
- **Note data quality:** Be transparent about gaps, estimates, and assumptions

---

## When to Use This Skill vs. Other Skills

**Use `system-details` when:**
- User wants a comprehensive overview of all building systems
- Preparing for a site visit or energy audit
- Onboarding a new building into the portfolio
- Due diligence review of mechanical systems

**Use `audette-equipment-survey` when:**
- User wants to **submit** new equipment data to Audette (not just review)
- Extracting data from PCNAs/CNAs to populate Audette database

**Use Read directly when:**
- User has a specific factual question answerable from one document
- Looking for a single piece of data (e.g., "What's the chiller capacity?")
- This skill is more comprehensive and synthesis-oriented

---

## Additional Resources

### Reference Files

For detailed query templates and system categorization:
- **`references/system-categories.md`** - Query templates for each system type, typical
  specifications to look for, and terminology mapping

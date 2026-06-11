---
name: equipment-estimator
description: >
  Estimates building equipment configurations using portfolio archetypes, aerial imagery
  analysis, and utility service data. Creates draft equipment surveys for buildings without
  documented equipment details. Use when: "estimate equipment for [property]", "predict HVAC
  for this building", "create equipment baseline from archetypes", or proactively when user
  has buildings in Audette but no equipment surveys submitted.
---

# Equipment Estimator

Predict building equipment configurations using portfolio intelligence, aerial imagery, and utility service data.

**Capabilities:**
- Learn equipment patterns from existing portfolio buildings (data-driven archetypes)
- Generate AI-based equipment baselines when portfolio data is sparse
- Analyze satellite imagery to identify rooftop equipment (RTUs, chillers, solar)
- Validate fuel types using utility service maps
- Create draft equipment surveys ready for Audette submission

**Dependencies:**
- **Audette MCP** (required) - list_buildings, get_equipment_survey, submit_equipment_survey
- **Playwright MCP** (required) - browser automation for Google Maps
- **WebSearch** (built-in) - utility service map lookup

**Modes:**
- Single building: Detailed analysis with full evidence table
- Batch portfolio: Process all buildings without surveys

---

## Step 1: Prerequisites Check

Call `switch_customer_account` with the account UID from `.audette-config.json` before any Audette tool calls.

Verify required dependencies before proceeding.

### Check Audette MCP

Call `ToolSearch` to verify Audette MCP tools are available:

```
ToolSearch(query: "select:list_buildings,get_equipment_survey,submit_equipment_survey")
```

If not found:
```
❌ Audette MCP not connected.

Please configure Audette MCP in Claude Desktop settings and restart.
```

**Stop execution** if Audette MCP not available.

### Check Playwright MCP

Call `ToolSearch` to verify Playwright MCP tools are available:

```
ToolSearch(query: "select:playwright__browser_navigate,playwright__browser_take_screenshot")
```

If not found:
```
❌ Playwright MCP required for aerial imagery analysis.

To install:
1. Install via Claude Code plugin marketplace: search for "playwright"
2. Restart Claude Desktop

Requirements:
- Node.js/npx installed on your system

See: https://github.com/microsoft/playwright-mcp
```

**Stop execution** if Playwright MCP not available.

### Read Project Configuration

Read `.audette-config.json` from workspace root:

```json
{
  "project_name": "...",
  "audette_account": {
    "name": "...",
    "uid": "..."
  },
  "buildings": [...]
}
```

If file missing:
```
❌ No .audette-config.json found.

Please run workspace-setup skill first to configure Audette account.
```

**Stop execution** if config missing.

Extract `audette_account.uid` for use in Audette MCP calls.

### Verify Audette Account

Call `list_customer_accounts` to verify account exists:

```
list_customer_accounts()
```

Check if `audette_account.uid` from config exists in returned list.

If not found:
```
⚠️  Account UID from config not found in Audette.

Configured: {uid}
Available accounts: {list}

Proceed anyway? (May fail later)
```

Ask the user whether to proceed despite the account mismatch. If user declines, stop execution.

### Load Portfolio Buildings

Call `list_buildings` to get all buildings in account:

```
list_buildings()
```

Extract building list. Store in memory for later use.

If no buildings found:
```
❌ No buildings found in Audette account.

Create buildings first using audette-create-building skill.
```

**Stop execution** if no buildings exist.

### Count Buildings with Equipment Surveys

For each building from `list_buildings`:

```
get_equipment_survey(building_model_uid: "{uid}")
```

Count buildings where survey is not null/empty.

**Portfolio assessment:**

```
✓ Prerequisites check complete

Audette account: {account_name}
Total buildings: {total}
Buildings with surveys: {surveyed}

Portfolio data quality:
- ≥10 surveys → "Good - strong archetype data"
- 3-9 surveys → "Fair - limited data, will supplement with AI archetypes"
- <3 surveys → "Sparse - will rely primarily on AI-generated archetypes"

Aerial imagery: Enabled (Playwright installed)
Fuel service validation: Enabled (WebSearch available)
```

Present status to user before proceeding.

---
## Step 2: Determine Execution Mode

Ask user whether to run single building or batch mode (if not specified in command args).

### Parse Command Arguments

If skill invoked with arguments:
- Building name or UID → single building mode
- "all" or "portfolio" → batch mode
- No arguments → ask user

### Ask User for Mode (if needed)

Ask the user:

```
**Which mode would you like to run?**

A) Single building - Detailed analysis with full evidence table
B) Batch portfolio - Process all buildings without surveys
```

Store mode selection.

---

## Step 3: Build Portfolio Archetypes

Create equipment archetypes from existing portfolio data (data-driven) and generate AI-based archetypes for gaps.

### Load Equipment Surveys

For each building with equipment survey (from Step 1):

```
get_equipment_survey(building_model_uid: "{uid}")
```

Extract:
- Building archetype (from building record)
- Gross floor area (for size binning)
- Year built (for age decade)
- State/province (for climate zone)
- Equipment survey data (all fields)

Store in list: `buildings_with_surveys[]`

### Cluster Buildings (Data-Driven Archetypes)

For each building in `buildings_with_surveys[]`:

**Extract clustering dimensions:**

```
archetype = building.building_archetype
size_bin = get_size_bin(building.gross_floor_area_square_feet)
age_decade = get_age_decade(building.year_built_original)
climate_zone = get_climate_zone(building.state_province)

cluster_key = f"{archetype}_{size_bin}_{age_decade}_{climate_zone}"
```

**Size binning function:**
```
def get_size_bin(sqft):
    if sqft < 5000: return 'tiny'
    elif sqft < 25000: return 'small'
    elif sqft < 100000: return 'medium'
    elif sqft < 500000: return 'large'
    else: return 'xlarge'
```

**Age decade function:**
```
def get_age_decade(year):
    decade = (year // 10) * 10
    return f"{decade}s"
```

**Climate zone function** (see `references/climate-zones.md`):
```
def get_climate_zone(state):
    cold = ['NY', 'MA', 'VT', 'NH', 'ME', 'WI', 'MN', 'ND', 'SD', 'MT', 'WY', 'ID']
    mild = ['WA', 'OR']
    hot_dry = ['AZ', 'NM', 'NV']
    hot_humid = ['FL', 'LA', 'MS', 'AL', 'GA', 'SC', 'AR']
    mixed = ['IL', 'IN', 'OH', 'PA', 'MI', 'VA', 'NC', 'TN', 'KY', 'WV', 'MD', 'DE', 'NJ', 'MO', 'KS']
    
    if state == 'CA': return 'mild'
    elif state == 'TX': return 'hot_humid'
    elif state in cold: return 'cold'
    elif state in mild: return 'mild'
    elif state in hot_dry: return 'hot_dry'
    elif state in hot_humid: return 'hot_humid'
    elif state in mixed: return 'mixed'
    else: return 'mixed'
```

**Group buildings by cluster_key:**

```
clusters = {}
for building in buildings_with_surveys:
    cluster_key = get_cluster_key(building)
    if cluster_key not in clusters:
        clusters[cluster_key] = []
    clusters[cluster_key].append(building.equipment_survey)
```

### Compute Median Equipment (Data-Driven)

For each cluster with ≥3 buildings:

**Categorical fields** (heating_type, cooling_type, dhw_fuel):
- Use mode (most common value)
- If tie, prefer more efficient option

**Numeric fields** (size_kw, install_year):
- Use median
- Exclude outliers (>2 std dev from mean)

**Boolean fields** (pv_exists):
- Use mode
- If ≥50% have it → exists = true

**Count fields** (cooling_count):
- Use median, round to integer
- Minimum 1 if exists = true

**Confidence score:**
```
confidence = min(cluster_size / 10, 1.0)
```

**Store archetype:**
```
data_driven_archetypes[cluster_key] = {
    "cluster_id": cluster_key,
    "building_count": len(cluster),
    "source": "data_driven",
    "median_equipment": {
        "heating_type": mode(heating_types),
        "cooling_type": mode(cooling_types),
        "dhw_fuel": mode(dhw_fuels),
        # ... all equipment fields
    },
    "confidence": min(len(cluster) / 10, 1.0)
}
```

### Generate AI-Based Presumptive Archetypes

For archetype combinations present in portfolio but with <3 surveyed buildings:

**Identify needed archetypes:**

Get all buildings from `list_buildings()` (including those without surveys).

Extract unique combinations of [archetype, size_bin, age_decade, climate_zone].

For each combination NOT in `data_driven_archetypes` (or with <3 buildings):

**Generate AI-based equipment prediction** using Claude's knowledge:

Read `references/ai-archetypes.md` for templates.

Match target building to closest template:
- Office: size and age determine equipment type
- Multifamily: size determines central vs suite-level
- Retail: RTUs dominant across all sizes
- Warehouse: Large RTUs typical

Apply climate adjustments:
- Cold: prefer gas heating
- Mild: heat pumps common
- Hot: large cooling capacity
- Mixed: balanced systems

Apply age adjustments:
- Pre-1980: gas boiler + minimal cooling
- 1980-2000: transition period
- Post-2000: RTUs dominant
- Post-2015: high efficiency + heat pumps

**Store AI archetype:**
```
ai_archetypes[cluster_key] = {
    "cluster_id": f"{cluster_key}_PRESUMPTIVE",
    "building_count": 0,
    "source": "ai_generated",
    "median_equipment": {
        "heating_type": "gas_boiler",  # from template
        "cooling_type": "rooftop_units",  # from template
        # ... all fields based on template
    },
    "confidence": 0.4,  # Always low-medium for AI
    "rationale": "Typical {age} {archetype} in {climate} climate: {explanation}"
}
```

### Merge Archetype Libraries

Create unified archetype library:

```
archetypes = {**ai_archetypes, **data_driven_archetypes}
```

Data-driven archetypes take precedence over AI-generated for same cluster_key.

**Report archetype status:**

```
📊 Archetype Library Built

Data-driven archetypes: {count_data_driven}
AI-generated archetypes: {count_ai}
Total coverage: {total_unique_combinations}

Ready to estimate equipment for target buildings.
```

---
## Step 4: Match Target Building to Archetype

For each target building (single mode: 1 building, batch mode: all buildings without surveys):

### Extract Target Building Dimensions

```
target_archetype = building.building_archetype
target_size_bin = get_size_bin(building.gross_floor_area_square_feet)
target_age_decade = get_age_decade(building.year_built_original)
target_climate_zone = get_climate_zone(building.state_province)

target_cluster_key = f"{target_archetype}_{target_size_bin}_{target_age_decade}_{target_climate_zone}"
```

### Find Matching Archetype

**Exact match first:**
```
if target_cluster_key in archetypes:
    matched_archetype = archetypes[target_cluster_key]
```

**Relax one dimension if no exact match:**
```
Try adjacent age decades (±10 years):
  target_age_decade = "1990s" → try "1980s", "2000s"

Try adjacent size bins:
  target_size_bin = "medium" → try "small", "large"

Try same archetype + climate, any age/size:
  "{target_archetype}_*_{target_climate_zone}"
```

**Fallback to archetype-only:**
```
Try same archetype, any size/age/climate:
  "{target_archetype}_*"
```

**Last resort:**
```
Use generic AI archetype for building type
```

### Create Draft Equipment Survey

Copy equipment fields from matched archetype:

```
draft_survey = {
    "central_plant_heating": {
        "heating_exists": matched_archetype.heating_type is not None,
        "heating_type": matched_archetype.heating_type,
        "heating_terminal_units": matched_archetype.heating_terminal_units,
        "heating_size_kw": matched_archetype.heating_size_kw,
        "heating_install_year": matched_archetype.heating_install_year,
        "heating_fuel": matched_archetype.heating_fuel
    },
    "central_plant_cooling": {
        "cooling_exists": matched_archetype.cooling_type is not None,
        "cooling_type": matched_archetype.cooling_type,
        "cooling_size_kw": matched_archetype.cooling_size_kw,
        "cooling_install_year": matched_archetype.cooling_install_year,
        "cooling_count": matched_archetype.cooling_count
    },
    # ... all other sections from schema
}
```

Store:
- `draft_survey` - current predictions
- `matched_archetype` - for evidence table
- `archetype_confidence` - for user review

---

## Step 5: Aerial Imagery Analysis

Capture satellite imagery and analyze for visible equipment.

**Note:** For brevity, Playwright MCP tools are referenced by short names:
- `browser_navigate()` → `playwright__browser_navigate()`
- `browser_wait_for()` → `playwright__browser_wait_for()`
- `browser_fill_form()` → `playwright__browser_fill_form()`
- `browser_press_key()` → `playwright__browser_press_key()`
- `browser_click()` → `playwright__browser_click()`
- `browser_evaluate()` → `playwright__browser_evaluate()`
- `browser_take_screenshot()` → `playwright__browser_take_screenshot()`

### Navigate to Google Maps

Use Playwright to navigate to building location:

```
browser_navigate(url: "https://www.google.com/maps")
```

Wait for page load:
```
browser_wait_for(selector: "input[aria-label*='Search']", timeout: 5000)
```

### Search for Building Address

Get full address from building record:
```
address = f"{building.street_address}, {building.city}, {building.state_province}"
```

Fill search box:
```
browser_fill_form(
    form_data: {
        "input[aria-label*='Search']": address
    }
)
```

Press Enter:
```
browser_press_key(key: "Enter")
```

Wait for map to center:
```
browser_wait_for(selector: ".widget-scene-canvas", timeout: 5000)
```

### Switch to Satellite View

Click satellite button:
```
browser_click(selector: "button[aria-label*='Satellite']")
```

Wait for satellite tiles to load (2 seconds):
```
# Use browser_evaluate to wait
browser_evaluate(expression: "new Promise(resolve => setTimeout(resolve, 2000))")
```

### Zoom to Rooftop Level

Zoom in to level 19-20 for rooftop detail:

```
# Zoom in 4-5 clicks (from default ~16 to 19-20)
for i in range(5):
    browser_click(selector: "button[aria-label*='Zoom in']")
    browser_evaluate(expression: "new Promise(resolve => setTimeout(resolve, 500))")
```

### Capture Screenshot

Take screenshot of current view:

```
browser_take_screenshot(full_page: false)
```

Returns base64-encoded image.

Decode and save to `/tmp/aerial_{building_uid}.png`:

```python
import base64
screenshot_data = base64.b64decode(screenshot_base64)
with open(f"/tmp/aerial_{building.uid}.png", "wb") as f:
    f.write(screenshot_data)
```

### Analyze Screenshot for Equipment

**Claude reads the screenshot directly** (multimodal capability).

Read the saved image:
```
Read(file_path: f"/tmp/aerial_{building.uid}.png")
```

**Analyze for equipment markers** (see `references/aerial-features.md`):

**Look for:**
1. **Rooftop Units (RTUs)**: Rectangular boxes, silver/gray, in rows
2. **Cooling Tower**: Circular/square, white, with fan housing
3. **Solar Panels**: Dark blue/black grid pattern
4. **Penthouse**: Raised structure in center of roof
5. **PTAC Units**: Grid pattern on building facade (not roof)

**Count visible equipment:**
- Count RTUs (most actionable signal)
- Note cooling tower presence
- Estimate solar coverage (% of roof area)

**Extract aerial findings:**

```
aerial_findings = {
    "rtus_visible": 4,  # counted from image
    "rtus_locations": "Center and east side of roof",
    "cooling_tower_visible": false,
    "solar_panels_visible": true,
    "solar_coverage_estimate": "~30% of roof area",
    "penthouse_present": false,
    "facade_units_visible": false,
    "image_quality": "high",  # clear view
    "confidence": "high"
}
```

### Override Draft Survey with Aerial Findings

**If RTUs visible:**
```
draft_survey.central_plant_cooling.cooling_type = "rooftop_units"
draft_survey.central_plant_cooling.cooling_count = aerial_findings.rtus_visible
draft_survey.central_plant_heating.heating_type = "rooftop_units"  # RTUs often have heating
```

**If cooling tower visible:**
```
draft_survey.central_plant_cooling.cooling_type = "chiller"
draft_survey.central_plant_cooling.central_plant = true
```

**If solar panels visible:**
```
draft_survey.pv_system.pv_exists = true
roof_area_sqft = building.gross_floor_area_sqft / building.floors_above_grade
coverage_pct = 0.30  # from estimate
draft_survey.pv_system.size_kw = roof_area_sqft * coverage_pct * 0.015
```

**If penthouse visible:**
```
# Suggests central plant
aerial_findings.notes = "Penthouse suggests central boiler/chiller"
```

### Handle Aerial Analysis Failures

**If Google Maps navigation fails:**
```
Try alternate address format (without unit number)
If still fails after 1 retry:
  - Skip aerial analysis for this building
  - Flag: "Aerial analysis failed - could not locate building"
  - Continue with archetype + fuel service only
  - aerial_findings.confidence = "none"
```

**If screenshot capture fails:**
```
Retry once
If still fails:
  - Skip aerial analysis
  - Flag: "Aerial analysis failed - screenshot capture error"
  - Continue with archetype only
  - aerial_findings.confidence = "none"
```

**If image quality is poor:**
```
Check for:
- Heavy shadows/trees obscuring roof
- Low resolution
- Snow/ice covering roof

If obscured:
  - aerial_findings.confidence = "low"
  - Use archetype prediction, flag aerial as unreliable
  - Note: "Aerial view obscured - relied on archetype"
```

---
## Step 6: Fuel Service Validation

Determine natural gas and steam service availability using WebSearch.

### Extract Building Location

```
city = building.city
state = building.state_province
address = building.street_address  # optional for precision
```

### Search for Gas Service

**Query 1: Service area map**
```
WebSearch(query: f"{city} {state} natural gas service area map")
```

**Query 2: Utility company** (if Query 1 inconclusive)
```
WebSearch(query: f"{city} {state} gas utility company")
```

**Query 3: Major utility** (if city has known major utility - see `references/fuel-service-heuristics.md`)
```
# Example for Brooklyn:
WebSearch(query: "National Grid NY service territory map")
```

### Parse Search Results

**Look for:**
- Utility company service area maps (PDFs, interactive maps)
- Municipality statements about gas service coverage
- Utility company territory descriptions

**Decision logic:**

```
IF search finds service map AND city is within marked territory:
  gas_service_available = true
  confidence = "high"
  utility_name = "..." (from map)
  source_url = "..." (map URL)

ELSE IF search mentions utility serves city/county:
  gas_service_available = true
  confidence = "medium"
  utility_name = "..." (from search)
  source_url = "..." (search result URL)

ELSE IF search returns no clear results:
  # Use heuristics based on city population
  # Determine population: check building.city_population if available,
  # or use Claude's knowledge of major cities, or search "{city} {state} population"
  IF city population >100K (urban):
    gas_service_available = true
    confidence = "low - assumed from location type"
  ELSE IF city population 10K-100K (suburban):
    gas_service_available = true
    confidence = "low - assumed from location type"
  ELSE (rural):
    gas_service_available = false
    confidence = "low - assumed from location type"

ELSE IF search states "no gas service" or "propane only":
  gas_service_available = false
  confidence = "high"
```

### Check for Steam Service (Large Buildings Only)

If building >100K sqft AND in known steam city:

```
Known steam systems:
- NYC: Con Edison Steam (Manhattan south of 96th St)
- Boston: Vicinity Energy
- San Francisco: limited district
- Denver: limited district
```

**Query:**
```
WebSearch(query: f"{city} district steam service")
```

If building in known steam district:
```
steam_service_available = true
confidence_steam = "medium"  # requires user confirmation
Flag for user confirmation (steam less common)
```

### Apply Fuel Constraints

Once gas service availability is determined:

```
IF gas_service_available = false:
  # Override any gas predictions from archetype
  IF draft_survey.central_plant_heating.heating_type in ['gas_boiler', 'gas_furnace']:
    # Use climate/age-aware fallback (see references/fuel-service-heuristics.md)
    IF climate_zone == 'cold' AND age_decade < '1990s':
      draft_survey.central_plant_heating.heating_type = 'oil'
    ELSE:
      draft_survey.central_plant_heating.heating_type = 'electric_resistance'
    fuel_override_applied = true
  
  IF draft_survey.dhw_heater.dhw_fuel == 'natural_gas':
    draft_survey.dhw_heater.dhw_fuel = 'electric'
    fuel_override_applied = true

ELSE IF gas_service_available = true:
  # Allow gas equipment types (no override needed)
  fuel_override_applied = false
```

### Store Fuel Service Findings

```
fuel_service = {
    "location": f"{city}, {state}",
    "gas_service_available": true/false,
    "gas_utility": "National Grid" or None,
    "steam_service_available": true/false,
    "confidence": "high|medium|low",
    "source": "https://..." or "heuristic: urban area",
    "notes": "Building within utility territory" or "",
    "fuel_override_applied": true/false
}
```

### Handle WebSearch Failures

If WebSearch tool unavailable or fails:

```
⚠️  WebSearch unavailable - cannot validate fuel service

Falling back to heuristics:
- Urban area → assume gas available (low confidence)
- Rural area → assume no gas (low confidence)

Predictions may be inaccurate - verify fuel availability manually.
```

Continue with heuristics-based guess, flag all fuel-related predictions as low confidence.

---
## Step 7: User Review and Confirmation

Present draft equipment survey with transparent evidence for all predictions.

### Single Building Mode: Detailed Evidence Table

**Present to user:**

```markdown
## Equipment Survey Draft: {building.building_name}

**Building**: {building.street_address}, {building.city} {building.state_province}
**Building UID**: {building.uid}
**Archetype match**: {matched_archetype.cluster_id} ({matched_archetype.building_count} similar buildings)
**Archetype source**: {Data-driven | AI-generated presumptive}
**Aerial imagery**: {aerial_findings.confidence} - {aerial_findings.notes}
**Gas service**: {fuel_service.gas_service_available} - {fuel_service.utility or "Not available"}

---

### Heating System

| Field | Predicted Value | Evidence | Confidence |
|-------|----------------|----------|------------|
| Exists | {Yes/No} | {Archetype: X% have heating} | {High/Medium/Low} |
| Type | {gas_boiler/etc} | {Aerial: RTUs visible | Archetype: Y% gas_boiler | AI archetype: typical} | {High/Medium/Low} |
| Fuel | {natural_gas/etc} | {Archetype + Gas service confirmed | Override: no gas service} | {High/Medium/Low} |
| Terminal units | {baseboards/etc} | {Archetype median} | {Medium} |
| Size (kW) | {175} | {Archetype median for size class} | {Medium} |
| Install year | {1995} | {Archetype median (building built {year})} | {Low} |

### Cooling System

| Field | Predicted Value | Evidence | Confidence |
|-------|----------------|----------|------------|
| Exists | {Yes/No} | {Aerial: 4 RTUs visible | Archetype: X% have cooling} | {Very High/High} |
| Type | {rooftop_units} | {Aerial: Direct observation | Archetype} | {Very High/High} |
| Count | {4} | {Aerial: Counted from imagery} | {High} |
| Size per unit (kW) | {35} | {Archetype median / count} | {Medium} |
| Install year | {1995} | {Archetype median} | {Low} |

### DHW (Domestic Hot Water)

| Field | Predicted Value | Evidence | Confidence |
|-------|----------------|----------|------------|
| Exists | {Yes/No} | {Archetype: X% have DHW} | {High/Medium} |
| Fuel | {natural_gas} | {Archetype + gas service confirmed} | {High} |
| Central distribution | {Yes} | {Archetype: X% centralized} | {Medium} |
| Tank size (litres) | {300} | {Archetype median} | {Medium} |
| Install year | {1995} | {Archetype median} | {Low} |

### Solar PV

| Field | Predicted Value | Evidence | Confidence |
|-------|----------------|----------|------------|
| Exists | {Yes/No} | {Aerial: Panels visible | Archetype} | {High/Medium} |
| Size (kW) | {75} | {Aerial: ~30% coverage × roof area} | {Medium} |

[... continue for all sections: elevators, air handling, etc.]

---

**⚠️ Low confidence fields** (please review):
- Install years: Based on archetype averages, not building-specific data
- Equipment sizes: Estimated from building size, not nameplate data
- {other low confidence fields}

**✓ High confidence fields**:
- Cooling type and count: Directly observed in aerial imagery
- Gas service: Confirmed via {utility} service map
- {other high confidence fields}
```

### Ask for User Action

Ask the user:

```
**How would you like to proceed?**

A) Submit this draft as-is to Audette
B) Edit specific fields before submitting
C) Show me the aerial imagery to verify
D) Cancel - don't submit
```

### If User Chooses "Edit" (Option B)

**Ask which section to edit:**

```
**Which section would you like to edit?**

A) Heating system
B) Cooling system
C) DHW (hot water)
D) Solar PV
E) Other sections
```

**Present current values for selected section** and ask for corrections:

For categorical fields (heating_type, cooling_type):
```
**Current: heating_type = gas_boiler**

Select new value:
A) gas_boiler (current)
B) electric_resistance
C) heat_pump
D) rooftop_units
E) Other (specify)
```

For numeric fields (size_kw, install_year):
```
**Current: heating_size_kw = 175**

Enter new value (or press Enter to keep current):
```

Ask the user for each field they want to change.

**Update draft survey** with user corrections.

**Re-present evidence table** with updated values and "User override" as evidence source:

```
| Field | Value | Evidence | Confidence |
|-------|-------|----------|------------|
| Type | heat_pump | User override (was: gas_boiler from archetype) | High |
```

**Re-ask for action** (Submit / Edit more / Cancel).

### If User Chooses "Show Imagery" (Option C)

**Display aerial screenshot:**

Read image from `/tmp/aerial_{building.uid}.png` and display inline.

**Point out identified equipment:**

```
📸 Aerial Imagery Analysis

[Image shown above]

Identified equipment:
- 4 RTUs visible in center of roof (marked with red boxes in my analysis)
- No cooling tower visible
- Solar panels covering ~30% of south-facing roof area
- No penthouse structure

Do these identifications look correct?
```

Ask user to confirm or correct aerial analysis.

If user corrects:
- Update `aerial_findings`
- Regenerate draft survey with corrections
- Re-present evidence table

**Return to action menu** (Submit / Edit / Cancel).

### Batch Mode: Summary Table

For batch portfolio mode, present summary table instead of detailed evidence:

```markdown
## Equipment Estimation Summary

Processed {N} buildings without surveys:

| Building | Heating | Cooling | Aerial | Gas Service | Confidence |
|----------|---------|---------|--------|-------------|------------|
| 123 Main St | gas_boiler | rooftop_units (4) | ✓ High | ✓ Available | High |
| 456 Oak Ave | heat_pump | chiller (2) | ✗ Failed | ✓ Available | Medium |
| 789 Elm Rd | gas_boiler | none | ✓ Medium | ✓ Available | Medium |
| ... | ... | ... | ... | ... | ... |

Legend:
- Aerial: ✓ = analysis succeeded, ✗ = failed/skipped
- Gas Service: ✓ = confirmed available, ✗ = not available
- Confidence: Overall prediction confidence (High/Medium/Low)

**Review options:**

A) Submit all drafts to Audette (triggers re-modeling for all buildings)
B) Review individual buildings before submitting (show detailed evidence for each)
C) Export all as JSON files for manual review
D) Cancel batch operation
```

Ask the user: for batch action selection.

### If Batch User Chooses "Review Individual" (Option B)

For each building in batch:
- Show detailed evidence table (same as single building mode)
- Ask: Submit / Edit / Skip this building
- Track: submitted, skipped, edited

After all buildings reviewed:
- Show summary of actions taken
- Proceed to submission step

### If Batch User Chooses "Export" (Option C)

Create `equipment-estimates/` directory:
```bash
mkdir -p equipment-estimates
```

For each building:
- Save draft survey to `equipment-estimates/{building_name}-draft.json`
- Save evidence report to `equipment-estimates/{building_name}-report.md`

Create summary CSV:
```csv
building_name,building_uid,heating_type,cooling_type,aerial_confidence,gas_service,overall_confidence
123 Main St,abc-123,gas_boiler,rooftop_units,high,available,high
...
```

Save to `equipment-estimates/portfolio-summary.csv`.

**Report to user:**
```
✓ Exported {N} draft surveys

Files saved:
- equipment-estimates/*.json - Draft survey JSONs
- equipment-estimates/*-report.md - Evidence reports
- equipment-estimates/portfolio-summary.csv - Summary table

You can review these files and manually submit surveys later using audette-equipment-survey skill.
```

**Stop here** (don't submit to Audette).

---

## Step 8: Submit Equipment Survey to Audette

After user confirms, submit draft survey(s) to Audette MCP.

### Validate Survey Completeness

Before submission, verify all required sections are present:

```
Required sections:
- central_plant_heating
- central_plant_cooling
- suite_level_heating
- suite_level_cooling
- dhw_heater
- air_handling_equipment
- rooftop_units
- pv_system
- elevators
```

**For each section:**

If `_exists = false`:
- All other fields in section must be `null`

If `_exists = true`:
- Required fields must have non-null values

**Check enum values:**
- heating_type, cooling_type, dhw_fuel must match schema allowed values
- See `references/equipment-schema.md` for valid enums

**Check numeric ranges:**
- size_kw > 0
- install_year between 1900 and current year
- tank_size_litres > 0

If validation fails:
```
❌ Survey validation failed:
- {list of validation errors}

Cannot submit. Please review and correct.
```

Fix errors or ask user to correct, then retry validation.

### Single Building: Submit Survey

Call `submit_equipment_survey`:

```
submit_equipment_survey(
    building_model_uid: building.uid,
    equipment_survey: draft_survey
)
```

**On success:**

```
✓ Equipment survey submitted successfully

Building: {building.building_name}
Audette is now re-modeling this building with updated equipment data.

Estimated re-modeling time: 2-5 minutes

Next steps:
- Wait for re-modeling to complete
- Review updated carbon reduction plan
- Generate decarbonization report with new baseline
```

**On error:**

```
❌ Survey submission failed

Error: {error_message}

Draft saved to: .audette-equipment-draft-{building_name}.json

You can:
- Review the error and retry
- Manually correct the JSON and submit via audette-equipment-survey skill
```

Save draft to file for manual review:

Write draft_survey JSON to file:
`.audette-equipment-draft-{building_name}.json`

Use JSON serialization with indent=2 for readability.

### Batch Mode: Submit All Surveys

For each building in batch (that user didn't skip):

```
submit_equipment_survey(
    building_model_uid: building.uid,
    equipment_survey: draft_survey
)
```

Track results:
- `submitted_successfully[]` - buildings submitted OK
- `submission_failed[]` - buildings that failed with error messages

**After all submissions:**

```
📊 Batch Submission Complete

✓ {N} surveys submitted successfully:
- {building_name_1}
- {building_name_2}
- ...

✗ {M} surveys failed:
- {building_name_X}: {error_message}
- {building_name_Y}: {error_message}

Failed drafts saved to:
- .audette-equipment-draft-{building_X}.json
- .audette-equipment-draft-{building_Y}.json

All successful buildings are now re-modeling in Audette.
Estimated completion: 2-5 minutes
```

### Save Estimation Metadata

For each submitted survey, save metadata alongside:

```json
{
  "building_uid": "abc-123",
  "building_name": "123 Main Street",
  "estimated_at": "2026-05-20T14:30:00Z",
  "archetype_cluster": {
    "cluster_id": "office_medium_1990s_cold",
    "building_count": 12,
    "source": "data_driven",
    "confidence": 0.85
  },
  "aerial_imagery": {
    "analyzed": true,
    "screenshot_path": "/tmp/aerial_abc-123.png",
    "rtus_counted": 4,
    "confidence": "high"
  },
  "fuel_service": {
    "gas_available": true,
    "utility": "National Grid",
    "source": "https://...",
    "confidence": "high"
  },
  "overall_confidence": "high",
  "low_confidence_fields": [
    "heating_install_year",
    "cooling_install_year",
    "dhw_install_year"
  ],
  "user_edits": []
}
```

Save to: `equipment-estimates/{building_name}-metadata.json`

### Update Project Config (Optional)

Add estimation tracking to `.audette-config.json`:

```json
{
  "project_name": "...",
  "audette_account": {...},
  "buildings": [...],
  "equipment_estimations": [
    {
      "building_uid": "abc-123",
      "estimated_at": "2026-05-20",
      "submitted": true,
      "confidence": "high",
      "archetype_source": "data_driven"
    }
  ]
}
```

This helps track which buildings have estimated vs. surveyed equipment.

---

## Step 9: Post-Submission Summary

After all submissions complete:

### Report Final Status

**Single building mode:**

```
✅ Equipment Estimation Complete

Building: {building.building_name}
Survey submitted: ✓
Archetype source: {data_driven | AI-generated}
Aerial analysis: {confidence}
Fuel service: {gas_service_available}
Overall confidence: {high | medium | low}

Low confidence fields flagged:
- {field_1}
- {field_2}

Recommendations:
- Review updated carbon plan when re-modeling completes (~3 min)
- Consider gathering additional operator input to improve low-confidence fields (equipment-gap-questionnaire skill - future enhancement)
- Run audette-equipment-survey skill if detailed documentation becomes available
```

**Batch mode:**

```
✅ Batch Equipment Estimation Complete

Total buildings processed: {N}
Surveys submitted: {N_success}
Surveys failed: {N_failed}
Average confidence: {avg_confidence}

Portfolio coverage:
- Buildings with surveys (before): {count_before}
- Buildings with surveys (after): {count_before + N_success}
- Coverage: {(count_before + N_success) / total_buildings * 100}%

Next steps:
- Wait ~5 minutes for all buildings to re-model
- Review carbon plans for newly estimated buildings
- Address low-confidence predictions with site surveys or additional operator input (equipment-gap-questionnaire skill - future enhancement)
```

### Suggest Next Actions

Based on confidence levels:

**If many low-confidence predictions:**
```
💡 Suggestion: {N} buildings have low overall confidence

Consider:
- Gathering additional operator input to fill gaps (equipment-gap-questionnaire skill - future enhancement)
- Site visit to verify equipment types
- Reviewing aerial imagery for unclear buildings
```

**If archetype data is sparse:**
```
💡 Suggestion: Portfolio archetype data is limited ({N} surveyed buildings)

Recommendation:
- Submit detailed equipment surveys for 5-10 more buildings (diverse types/sizes)
- Run equipment estimator again after more surveys added
- Confidence will improve as portfolio data grows
```

**If aerial analysis failed for many buildings:**
```
⚠️  Aerial analysis failed for {N} buildings

Possible reasons:
- Buildings not found in Google Maps (check addresses)
- Tree/vegetation obscuring rooftops
- Image quality too low

These buildings relied solely on archetypes - lower confidence.
```

### Cleanup

Remove temporary files:

```bash
rm /tmp/aerial_*.png
```

(Unless user requested to keep for review)

**End of skill execution.**

---

## Notes

### Confidence Levels

**Very High (>90%):**
- Direct observation from aerial imagery
- Hard constraint (fuel service confirmed/denied)
- Data-driven archetype with ≥10 buildings

**High (70-90%):**
- Data-driven archetype with 5-9 buildings
- Aerial imagery medium quality
- Fuel service medium confidence

**Medium (50-70%):**
- Data-driven archetype with 3-4 buildings
- AI-generated archetype
- Aerial imagery unclear or failed
- Fuel service low confidence (heuristics)

**Low (<50%):**
- AI-generated archetype only
- No aerial imagery
- No fuel service validation
- Install years (always estimates)

### Error Recovery

Skill continues gracefully if:
- Aerial imagery fails → use archetype only, flag it
- WebSearch fails → use heuristics, flag it
- Individual building submission fails → save draft, continue to next

Skill stops if:
- Audette MCP not connected
- Playwright MCP not installed
- No .audette-config.json
- No buildings in portfolio

### Performance

**Single building:**
- Prerequisites: 5 sec
- Archetype loading: 30-60 sec
- Baseline matching: 5 sec
- Aerial capture: 60-120 sec
- Fuel validation: 30-60 sec
- User review: variable
- Submission: 5 sec
- **Total: 5-10 minutes**

**Batch (10 buildings):**
- Prerequisites: 5 sec
- Archetype loading: 60 sec (once)
- Per building: 3-5 min
- User review: 2-5 min
- Submission: 30 sec
- **Total: 30-60 minutes**

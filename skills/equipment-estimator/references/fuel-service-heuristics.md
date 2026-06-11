# Fuel Service Validation Heuristics

Patterns for determining natural gas and steam service availability using WebSearch.

## Natural Gas Service

### WebSearch Queries

Try in order until service determination is made:

1. `"{city} {state} natural gas service area map"`
2. `"{city} {state} gas utility company"`
3. `"{major_utility_name} {state} service territory map"`

**Example:**
```
"Brooklyn NY natural gas service area map"
"Brooklyn NY gas utility company"
"National Grid NY service territory map"
```

### Major Utility Companies by Region

**Northeast:**
- Con Edison (NYC, Westchester)
- National Grid (Brooklyn, Queens, upstate NY, MA)
- Eversource (CT, MA, NH)
- PECO (Philadelphia, PA)
- PSE&G (NJ)

**Mid-Atlantic:**
- BGE (Baltimore, MD)
- Washington Gas (DC, MD, VA)
- Dominion Energy (VA, NC)

**Midwest:**
- Peoples Gas (Chicago, IL)
- Nicor Gas (Northern IL)
- DTE Energy (Detroit, MI)
- Consumers Energy (MI)

**West:**
- PG&E (Northern/Central CA)
- SoCalGas (Southern CA)
- NW Natural (Portland, OR)
- Puget Sound Energy (Seattle, WA)

**South:**
- Atlanta Gas Light (GA)
- Piedmont Natural Gas (NC, SC, TN)
- Florida City Gas (South FL)

### Decision Logic

```
IF WebSearch returns utility service map:
  IF building location is within marked service area:
    → gas_service_available = true
    → confidence = "high"
  ELSE:
    → gas_service_available = false
    → confidence = "high"

ELSE IF WebSearch mentions utility serves city/county:
  → gas_service_available = true
  → confidence = "medium"

ELSE IF WebSearch returns no clear results:
  → Use heuristics (see below)
  → confidence = "low"

ELSE IF WebSearch states "no gas service" or "propane only":
  → gas_service_available = false
  → confidence = "high"
```

### Heuristics (when WebSearch fails)

**Urban areas** (city population >100K):
- Likely gas service available
- confidence = "low - assumed from location type"

**Suburban areas** (city population 10K-100K):
- Likely gas service available
- confidence = "low - assumed from location type"

**Rural areas** (city population <10K):
- Unlikely gas service
- May use propane (treat as unavailable for natural gas)
- confidence = "low - assumed from location type"

**Known no-gas regions:**
- Rural Vermont, New Hampshire, Maine
- Rural parts of Pacific Northwest
- Mountain West rural areas

## Steam Service

### WebSearch Queries

```
"{city} district steam service"
"{city} steam utility"
```

### Known Steam Systems

**New York City:**
- Con Edison Steam
- Service area: Manhattan south of 96th Street
- Largest steam system in US

**Boston:**
- Vicinity Energy
- Downtown Boston, Cambridge

**Other cities with limited steam:**
- San Francisco (small district)
- Denver (small district)
- Philadelphia (university areas)
- Pittsburgh (downtown)

### Steam Decision Logic

```
IF building in known steam district AND >100K sqft:
  → steam_service_available = true
  → Flag for user confirmation (steam less common than assumed)

ELSE:
  → steam_service_available = false
```

## Propane vs Natural Gas

**Propane characteristics:**
- Rural areas without natural gas pipelines
- On-site storage tanks (visible in aerial imagery if ground-level)
- More expensive than natural gas
- Often used for heating + DHW

**For estimation purposes:**
- Treat propane as "no natural gas service"
- Do not predict gas_boiler or natural_gas fuel types
- Default to electric or oil heating

## Edge Cases

### Multiple Utilities in Same City

**Example:** Brooklyn served by National Grid, but parts of Brooklyn served by Con Edison

**Resolution:**
- Present both utilities to user
- Ask which serves specific address
- Document both in evidence table

### Service Territory Borders

**Example:** Building on edge of service map

**Resolution:**
- Flag as uncertain
- Present to user for confirmation
- Document: "Building near service territory border - verify with utility"

### Recent Expansion

**Example:** Utility expanded service area in last 2-3 years

**Resolution:**
- Service maps may be outdated
- Flag for user confirmation
- Document: "Service map may not reflect recent expansion"

## Applying Fuel Constraints

Once gas service availability is determined:

```
IF gas_service_available = false:
  → heating_type ≠ gas_boiler, gas_furnace, gas_heat_pump
  → dhw_fuel ≠ natural_gas
  → Override archetype if it predicted gas
  → Default to:
    - electric_resistance
    - heat_pump
    - oil (if older building in cold climate)

IF gas_service_available = true:
  → Allow gas equipment types
  → Prefer gas if archetype suggests it (common in cold climates)
  → Still allow electric/heat pump (especially newer buildings)
```

## Evidence Table Format

When documenting fuel service findings:

```markdown
**Fuel Service Validation:**
- Location: {city}, {state}
- Natural gas: {Available|Not Available}
- Utility: {utility_name}
- Source: {url or "heuristic: urban area"}
- Confidence: {high|medium|low}
- Notes: {any special considerations}

**Applied Constraints:**
- {Excluded gas equipment types if unavailable}
- {Allowed gas equipment if available}
```

**Example:**

```markdown
**Fuel Service Validation:**
- Location: Brooklyn, NY
- Natural gas: Available
- Utility: National Grid
- Source: https://www.nationalgridus.com/brooklyn-service-map
- Confidence: high
- Notes: Building within National Grid Brooklyn territory

**Applied Constraints:**
- Gas heating types allowed (gas_boiler preferred in cold climate)
- Natural gas DHW allowed
```

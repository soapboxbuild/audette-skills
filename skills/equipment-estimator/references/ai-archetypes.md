# AI-Generated Presumptive Archetypes

Templates for generating equipment baselines when insufficient portfolio data exists.

## When to Use

- Portfolio has <3 buildings with surveys for a given archetype combination
- No data-driven archetype available for target building
- Fallback to Claude's knowledge of typical building systems

## Generation Logic

For each [archetype, size_bin, age_decade, climate_zone] combination:

### Office Buildings

**Small Office (<25K sqft):**

Pre-1990, Cold climate:
```json
{
  "heating_type": "gas_boiler",
  "heating_terminal_units": "baseboards",
  "cooling_type": "rooftop_units",
  "cooling_count": 2,
  "dhw_fuel": "natural_gas",
  "led_ratio": 0.15,
  "rationale": "Typical small 1980s office: Gas boiler + RTUs common, minimal LED retrofits"
}
```

1990-2010, Cold climate:
```json
{
  "heating_type": "gas_boiler",
  "heating_terminal_units": "fan_coil_units",
  "cooling_type": "rooftop_units",
  "cooling_count": 3,
  "dhw_fuel": "natural_gas",
  "led_ratio": 0.25,
  "rationale": "1990s-2000s office: Gas boiler common, RTUs dominant, some LED retrofits"
}
```

Post-2010, Mild climate:
```json
{
  "heating_type": "heat_pump",
  "heating_terminal_units": "integrated",
  "cooling_type": "rooftop_units",
  "cooling_count": 3,
  "dhw_fuel": "electric",
  "led_ratio": 0.60,
  "rationale": "Modern office in mild climate: Heat pumps common, LED lighting likely"
}
```

**Medium Office (25-100K sqft):**

Pre-1990, Cold climate:
```json
{
  "heating_type": "gas_boiler",
  "heating_terminal_units": "fan_coil_units",
  "cooling_type": "rooftop_units",
  "cooling_count": 5,
  "dhw_fuel": "natural_gas",
  "led_ratio": 0.20,
  "rationale": "Medium 1980s office: Central boiler + multiple RTUs typical"
}
```

1990-2010, Cold climate:
```json
{
  "heating_type": "gas_boiler",
  "heating_terminal_units": "vav",
  "cooling_type": "rooftop_units",
  "cooling_count": 6,
  "dhw_fuel": "natural_gas",
  "led_ratio": 0.35,
  "rationale": "1990s-2000s medium office: VAV common, RTUs, some LED retrofits"
}
```

Post-2010, Any climate:
```json
{
  "heating_type": "gas_boiler",
  "heating_terminal_units": "vav",
  "cooling_type": "rooftop_units",
  "cooling_count": 6,
  "dhw_fuel": "natural_gas",
  "led_ratio": 0.65,
  "rationale": "Modern medium office: Efficient boiler + RTUs, extensive LED retrofits"
}
```

**Large Office (>100K sqft):**

Any age, Cold climate:
```json
{
  "heating_type": "gas_boiler",
  "heating_terminal_units": "vav",
  "cooling_type": "chiller",
  "cooling_count": 2,
  "dhw_fuel": "natural_gas",
  "led_ratio": 0.40,
  "rationale": "Large office: Central plant (boiler + chiller) typical, VAV distribution"
}
```

Any age, Hot climate:
```json
{
  "heating_type": "gas_boiler",
  "heating_terminal_units": "vav",
  "cooling_type": "chiller",
  "cooling_count": 3,
  "dhw_fuel": "natural_gas",
  "led_ratio": 0.40,
  "rationale": "Large office in hot climate: Central plant, larger cooling capacity"
}
```

### Multifamily Buildings

**Small Multifamily (<50 units, <50K sqft):**

Pre-1990, Cold climate:
```json
{
  "heating_type": "gas_boiler",
  "heating_terminal_units": "baseboards",
  "cooling_type": "ptac",
  "cooling_count": 0,
  "dhw_fuel": "natural_gas",
  "led_ratio": 0.10,
  "rationale": "Small older multifamily: Central boiler, suite-level cooling (PTAC), minimal LED"
}
```

1990-2010, Any climate:
```json
{
  "heating_type": "gas_boiler",
  "heating_terminal_units": "fan_coil_units",
  "cooling_type": "ptac",
  "cooling_count": 0,
  "dhw_fuel": "natural_gas",
  "led_ratio": 0.25,
  "rationale": "1990s-2000s multifamily: Central heating, PTAC cooling, some LED retrofits"
}
```

**Medium Multifamily (50-200 units, 50-200K sqft):**

Pre-1990, Cold climate:
```json
{
  "heating_type": "gas_boiler",
  "heating_terminal_units": "baseboards",
  "cooling_type": "none",
  "cooling_count": 0,
  "dhw_fuel": "natural_gas",
  "led_ratio": 0.15,
  "rationale": "Medium older multifamily: Central boiler common, often no cooling in cold climates"
}
```

1990-2010, Any climate:
```json
{
  "heating_type": "gas_boiler",
  "heating_terminal_units": "fan_coil_units",
  "cooling_type": "ptac",
  "cooling_count": 0,
  "dhw_fuel": "natural_gas",
  "led_ratio": 0.30,
  "rationale": "1990s-2000s medium multifamily: Central plant + suite-level PTAC"
}
```

Post-2010, Any climate:
```json
{
  "heating_type": "gas_boiler",
  "heating_terminal_units": "fan_coil_units",
  "cooling_type": "central_cooling",
  "cooling_count": 2,
  "dhw_fuel": "natural_gas",
  "led_ratio": 0.55,
  "rationale": "Modern medium multifamily: Central plant common, LED retrofits likely"
}
```

**Large Multifamily (>200 units, >200K sqft):**

Any age, Any climate:
```json
{
  "heating_type": "gas_boiler",
  "heating_terminal_units": "fan_coil_units",
  "cooling_type": "chiller",
  "cooling_count": 2,
  "dhw_fuel": "natural_gas",
  "led_ratio": 0.40,
  "rationale": "Large multifamily: Central plant (boiler + chiller) typical for building this size"
}
```

### Retail Buildings

**Any size, Any age:**

```json
{
  "heating_type": "rooftop_units",
  "heating_terminal_units": "integrated",
  "cooling_type": "rooftop_units",
  "cooling_count": 4,
  "dhw_fuel": "natural_gas",
  "led_ratio": 0.70,
  "rationale": "Retail: RTUs dominant across all sizes/ages, LED retrofits very common (energy savings focus)"
}
```

Small retail (<25K sqft):
```json
{
  "cooling_count": 2
}
```

Large retail (>100K sqft):
```json
{
  "cooling_count": 8
}
```

### Warehouse/Industrial

**Any size, Any age:**

```json
{
  "heating_type": "rooftop_units",
  "heating_terminal_units": "integrated",
  "cooling_type": "rooftop_units",
  "cooling_count": 6,
  "dhw_fuel": "natural_gas",
  "led_ratio": 0.50,
  "rationale": "Warehouse: Large RTUs typical, minimal heating in some climates, LED for cost savings"
}
```

Hot climate adjustment:
```json
{
  "cooling_count": 10,
  "rationale": "Warehouse in hot climate: Large cooling loads for product storage"
}
```

## Climate-Specific Adjustments

**Cold climates** (cold, mixed):
- Prefer gas heating (if available)
- Larger heating capacity
- DHW often natural gas
- Minimal cooling for older buildings

**Mild climates:**
- Heat pumps common (especially post-2010)
- Balanced heating/cooling
- Electric DHW more common

**Hot-Dry climates:**
- Minimal heating needs
- Large cooling capacity
- Electric resistance heating acceptable
- Solar PV more common

**Hot-Humid climates:**
- Minimal heating needs
- Large cooling + dehumidification
- Chillers for large buildings
- Electric resistance heating acceptable

## Age-Specific Adjustments

**Pre-1980:**
- Gas boiler + cast iron radiators/baseboards common
- Minimal cooling (especially cold climates)
- LED ratio: 0.05-0.15
- Older equipment, likely past useful life

**1980-2000:**
- Gas boiler + RTUs transition period
- More cooling than pre-1980
- LED ratio: 0.15-0.35
- Equipment at end of useful life

**Post-2000:**
- RTUs dominant for small/medium buildings
- Chillers for large buildings
- LED ratio: 0.35-0.65
- Heat pumps more common

**Post-2015:**
- High-efficiency equipment
- Heat pumps increasingly common
- LED ratio: 0.60-0.90
- Solar PV more common

## Confidence Scoring

AI-generated archetypes always receive:
```
confidence = 0.4 (Low-Medium)
source = "ai_generated"
```

This ensures user reviews AI predictions carefully and validates with aerial imagery + fuel service.

## Evidence Table Format

When using AI-generated archetype:

```markdown
| Field | Value | Evidence | Confidence |
|-------|-------|----------|------------|
| Type | gas_boiler | AI archetype: Typical 1990s office in cold climate | Low-Medium |
```

vs. data-driven archetype:

```markdown
| Field | Value | Evidence | Confidence |
|-------|-------|----------|------------|
| Type | gas_boiler | Portfolio archetype: 12 similar buildings | High |
```

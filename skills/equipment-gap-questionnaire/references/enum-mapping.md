# Enum Mapping: Operator Terms → Schema Values

This file maps common building operator terminology to valid enum values in the Audette
equipment survey schema. Use this to parse natural language responses into structured
survey fields.

---

## Air Handling Equipment Type

| Operator Says | Schema Enum |
|---------------|-------------|
| "Rooftop air handling unit", "packaged RTU", "packaged AHU" | `packaged_air_handling_unit` |
| "Split system AHU", "indoor air handler + outdoor unit" | `split_air_handling_unit` |
| "Make-up air unit", "MAU", "fresh air only", "garage ventilation" | `make_up_air_unit` |
| "ERV in each suite", "energy recovery ventilator" | `suite_energy_recovery_ventilator` |
| "HRV in each suite", "heat recovery ventilator", "air exchanger" | `suite_air_exchangers` |
| "Exhaust fans only", "no supply air", "exhaust-only" | `exhaust_only_air_handling_unit` |

---

## Air Handling Heating Type

| Operator Says | Schema Enum |
|---------------|-------------|
| "Electric heat", "electric resistance", "electric coils" | `electric_resistance` |
| "Gas heat", "gas-fired", "gas burner" | `gas` |
| "Hot water coils", "hydronic heating", "boiler-fed coils" | `hydronic` |

---

## Air Handling Cooling Type

| Operator Says | Schema Enum |
|---------------|-------------|
| "DX cooling", "direct expansion", "refrigerant coils", "compressor-based" | `direct_expansion` |
| "Chilled water", "hydronic cooling", "chiller-fed" | `hydronic` |

---

## Central Plant Cooler Type

| Operator Says | Schema Enum |
|---------------|-------------|
| "Air-cooled chiller", "air condenser", "no cooling tower" | `air_cooled_chiller` |
| "Water-cooled chiller", "cooling tower", "condenser water loop" | `water_cooled_chiller` |

---

## Central Plant Cooler Terminal Units

| Operator Says | Schema Enum |
|---------------|-------------|
| "Baseboards", "hydronic baseboards", "baseboard convectors" | `baseboards` |
| "Fan coils", "fan coil units", "FCUs", "fan coils in each suite" | `fan_coil_units` |
| "VAV boxes", "variable air volume", "VAV system" | `variable_air_volume_boxes` |
| "Constant volume boxes", "CV boxes", "fixed airflow" | `constant_volume_boxes` |

---

## Central Plant Heater Type

| Operator Says | Schema Enum | Notes |
|---------------|-------------|-------|
| "Gas boiler", "atmospheric boiler", "standard boiler" | `gas_boiler` | AFUE < 90%, standard efficiency |
| "Condensing boiler", "high-efficiency boiler", "condensing gas boiler", "AFUE ≥90%" | `condensing_gas_boiler` | AFUE ≥ 90%, typically ≥95% |
| "Electric boiler", "electric resistance boiler" | `electric_resistance_boiler` | Resistance elements |
| "Gas furnace", "forced air furnace", "standard gas furnace" | `gas_furnace` | AFUE < 90% |
| "High-efficiency furnace", "condensing furnace", "AFUE ≥90% furnace" | `high_efficiency_gas_furnace` | AFUE ≥ 90% |
| "Electric furnace", "electric forced air" | `electric_furnace` | Forced air, electric heat |
| "Hydronic furnace", "district heat furnace", "geothermal furnace" | `hydronic_furnace` | Water-source |

**Brand-based inference:**
- **Weil-McLain**: Typically `gas_boiler` (standard, non-condensing)
- **Navien**: Typically `condensing_gas_boiler`
- **Lochinvar**: Could be either — ask if condensing
- **Burnham**: Typically `gas_boiler` (standard)
- **Viessmann**: Typically `condensing_gas_boiler`

---

## Central Plant Heater Terminal Units

| Operator Says | Schema Enum |
|---------------|-------------|
| "Baseboards", "hydronic baseboards", "baseboard radiators" | `baseboards` |
| "Radiators", "cast iron radiators", "fin-tube radiators" | `baseboards` (use same enum) |
| "Fan coils", "fan coil units", "FCUs" | `fan_coil_units` |
| "VAV boxes", "variable air volume" | `variable_air_volume_boxes` |
| "Constant volume boxes", "CV boxes" | `constant_volume_boxes` |

---

## Central Plant Heat Pump Type

| Operator Says | Schema Enum |
|---------------|-------------|
| "Air-source heat pump", "ASHP", "air-to-air heat pump" | `air_source_heat_pump` |
| "Ground-source heat pump", "geothermal", "GSHP", "geo wells" | `ground_source_heat_pump` |

---

## Domestic Hot Water Heater Type

| Operator Says | Schema Enum |
|---------------|-------------|
| "Gas water heater", "gas tank", "gas storage" | `gas_storage` |
| "Electric water heater", "electric tank", "electric storage" | `electric_storage` |
| "Tankless gas", "gas instantaneous", "on-demand gas" | `gas_instantaneous` |
| "Tankless electric", "electric instantaneous", "on-demand electric" | `electric_instantaneous` |
| "Heat pump water heater", "HPWH" | `heat_pump_water_heater` |
| "Indirect tank", "boiler-fed tank", "indirect water heater" | `indirect_tank` |

**Brand-based inference:**
- **Rheem**: Could be gas or electric storage (ask)
- **A.O. Smith**: Could be gas or electric storage (ask)
- **Navien**: Typically `gas_instantaneous` (tankless)
- **Rinnai**: Typically `gas_instantaneous` (tankless)
- **Bradford White**: Typically `gas_storage` or `electric_storage`

---

## Rooftop Unit Type

| Operator Says | Schema Enum |
|---------------|-------------|
| "PTAC", "packaged terminal air conditioner", "through-wall units" | `packaged_terminal_air_conditioner` |
| "PTHP", "packaged terminal heat pump" | `packaged_terminal_heat_pump` |
| "Split system AC", "split air conditioner", "outdoor condenser + indoor handler" | `split_system_air_conditioner` |
| "Split system heat pump", "heat pump RTU" | `split_system_heat_pump` |

---

## Rooftop Unit Heating Type

| Operator Says | Schema Enum |
|---------------|-------------|
| "Electric heat", "electric resistance", "electric backup" | `electric_resistance` |
| "Gas heat", "gas-fired" | `gas` |
| "Hot water coils", "hydronic" | `hydronic` |

---

## Rooftop Unit Cooling Type

| Operator Says | Schema Enum |
|---------------|-------------|
| "DX cooling", "direct expansion", "refrigerant" | `direct_expansion` |
| "Chilled water", "hydronic cooling" | `hydronic` |

---

## Suite Heat Pump Type

| Operator Says | Schema Enum |
|---------------|-------------|
| "Mini-split", "ductless mini-split", "wall-mounted heat pump" | `mini_split_heat_pump` |
| "PTHP", "packaged terminal heat pump", "through-wall heat pump" | `packaged_terminal_heat_pump` |

**Brand-based inference:**
- **Mitsubishi**, **Daikin**, **Fujitsu**, **LG**: Typically `mini_split_heat_pump`

---

## Elevators / Escalators Type

| Operator Says | Schema Enum |
|---------------|-------------|
| "Hydraulic elevator", "hydraulic lift" | `hydraulic_elevator` |
| "Traction elevator", "cable elevator", "geared traction", "gearless traction" | `traction_elevator` |
| "Escalator", "moving stairs" | `escalator` |

---

## Unit Conversions

### Heating Capacity

| From | To kW | Formula |
|------|-------|---------|
| MBH (1000 BTU/hr) | kW | MBH × 0.293 |
| BTU/hr | kW | BTU/hr ÷ 3412 |
| Tons (rare for heating) | kW | Tons × 3.517 |

**Examples:**
- 500 MBH → 500 × 0.293 = 146.5 kW
- 1,000 MBH (1 MMBH) → 1000 × 0.293 = 293 kW
- 100,000 BTU/hr → 100,000 ÷ 3412 = 29.3 kW

### Cooling Capacity

| From | To kW | Formula |
|------|-------|---------|
| Tons | kW | Tons × 3.517 |
| BTU/hr | kW | BTU/hr ÷ 3412 |
| kW | Tons | kW ÷ 3.517 |

**Examples:**
- 5 tons → 5 × 3.517 = 17.6 kW
- 100 tons → 100 × 3.517 = 351.7 kW
- 200 tons → 200 × 3.517 = 703.4 kW

### Water Heater Capacity

| From | To Litres | Formula |
|------|-----------|---------|
| Gallons (US) | Litres | Gallons × 3.785 |
| Litres | Gallons | Litres ÷ 3.785 |

**Examples:**
- 50 gallons → 50 × 3.785 = 189 litres
- 100 gallons → 100 × 3.785 = 379 litres
- 200 litres → 200 ÷ 3.785 = 52.8 gallons

### Airflow

| From | To | Formula |
|------|-----|---------|
| CFM (cubic feet per minute) | m³/h | CFM × 1.699 |
| m³/h | CFM | m³/h ÷ 1.699 |

**Examples:**
- 10,000 CFM → 10,000 × 1.699 = 16,990 m³/h
- 5,000 CFM → 5,000 × 1.699 = 8,495 m³/h

---

## Ambiguity Resolution

### When Operator Says "Boiler"

Ask: "Is it a condensing boiler (high-efficiency, AFUE ≥90%) or standard boiler?"

- If they say "high-efficiency", "condensing", or mention AFUE ≥90% → `condensing_gas_boiler`
- If they say "old", "standard", "atmospheric", or don't know → `gas_boiler`
- If brand is Navien or Viessmann → likely `condensing_gas_boiler`
- If brand is Weil-McLain or Burnham → likely `gas_boiler`

### When Operator Says "Rooftop Units"

Ask: "Are those packaged units (all-in-one) or split systems (separate indoor/outdoor)?"

- If all-in-one → `packaged_air_handling_unit` (if serving zones) or `packaged_terminal_air_conditioner` (if serving single suite)
- If separate indoor/outdoor → `split_air_handling_unit` or `split_system_air_conditioner`

### When Operator Says "Heat Pump"

Ask: "Is that a central plant heat pump, rooftop heat pumps, or mini-splits in each suite?"

- If central → `central_plant_heat_pump` section
- If rooftop serving zones → `rooftop_units` section with type `split_system_heat_pump` or `packaged_terminal_heat_pump`
- If in each suite → `suite_heat_pumps` section with type `mini_split_heat_pump` or `packaged_terminal_heat_pump`

### When Operator Gives Count + Capacity

Parse carefully:

- "2 boilers at 500 MBH each" → Total: 1000 MBH = 293 kW
- "15 rooftop units, 5 tons each" → Total: 75 tons = 264 kW
- "3 chillers, 100 tons total" → Total: 100 tons = 351.7 kW (don't multiply by 3!)

---

## Handling Unknown or Vague Responses

### When Operator Doesn't Know Type

Try brand inference:
- "What brand is the [equipment]?" → Use brand → infer type

If still unknown, ask manufacturer or model number:
- "Is there a model number or nameplate you can check?"

### When Operator Doesn't Know Capacity

Estimate based on building size and verify:
- "For a [SF] building, typical [system] capacity is about [X]. Does that sound right?"

**Typical ranges:**

| Building Type | Heating (kW per 1000 SF) | Cooling (kW per 1000 SF) |
|---------------|--------------------------|--------------------------|
| Multifamily | 15-25 | 8-15 |
| Office | 20-30 | 12-20 |
| Retail | 25-35 | 15-25 |

### When Operator Doesn't Know Age

Try these approaches:
1. "Was the equipment installed when the building was built, or replaced later?"
2. "Has it been replaced in the last 10 years, or is it older?"
3. "Would you say it's new (0-5 years), middle-aged (6-15 years), or old (15+ years)?"

If genuinely unknown, set to `null` and note for site visit.

---

## Validation Rules

After mapping operator response to schema enum, validate:

1. **Enum is valid**: Check against equipment-schema.md allowed values
2. **Units converted correctly**: All capacities in kW, volumes in litres
3. **Total vs. per-unit**: Clarify if operator gave total or per-unit capacity
4. **Type consistency**: If operator says "condensing boiler", don't map to `gas_boiler`

If validation fails, ask clarifying follow-up question.

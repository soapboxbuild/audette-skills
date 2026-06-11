# Question Templates for Equipment Survey Gap Analysis

This file provides question templates for each equipment section, designed to elicit
natural language responses from building operators that can be parsed into equipment
survey schema fields.

---

## General Question Design

### Opening Questions (System Existence)

These determine if a system exists (`_exists` field):

```
"Does the building have [system]?"
"Is there a [system] in this building?"
"How is [function] handled in the building?"
```

Examples:
- "Does the building have a central heating system, or is heating handled at the suite level?"
- "Is there a chiller or central cooling system?"
- "How is domestic hot water provided — centrally or in each suite?"

### Detail Questions (System Specifications)

Once existence is confirmed, gather specifications:

```
"What type of [system] is it?"
"How many [units] are there?"
"What's the capacity of each?"
"About how old is the [system]?"
```

### Distribution Questions

For central plant systems, ask about distribution:

```
"How is [heating/cooling] distributed through the building?"
"What type of terminal units are used?"
```

---

## Air Handling Equipment

### Existence
```
"Is there a central air handling system or ventilation system in the building?"
"How is fresh air / ventilation provided?"
```

### Type
```
"What type of air handling system is it?
 - Rooftop air handling units?
 - Make-up air units (fresh air only)?
 - Energy recovery ventilators (ERVs)?
 - Suite-level exchangers?
 - Exhaust-only system?"
```

### Heating/Cooling Type
```
"Does the air handling system provide heating? If so, electric, gas, or hot water coils?"
"Does it provide cooling? If so, direct expansion (DX) or chilled water?"
```

### Capacity
```
"What's the total airflow capacity, if you know? (Can be in CFM or cubic meters per hour)"
```

### Installation Year
```
"About how old is the air handling system? Even a rough estimate helps."
```

### Common Operator Responses

| Response | Inferred Fields |
|----------|-----------------|
| "We have rooftop units on each floor" | Type: `packaged_air_handling_unit` |
| "Just exhaust fans, no supply" | Type: `exhaust_only_air_handling_unit` |
| "ERVs in each suite" | Type: `suite_energy_recovery_ventilator` |
| "Make-up air for the garage" | Type: `make_up_air_unit` |

---

## Central Plant Cooler (Chiller)

### Existence
```
"Does the building have a chiller or central cooling plant?"
"Is cooling centralized or handled by individual units?"
```

### Type
```
"What type of chiller is it — air-cooled or water-cooled?"
```

### Terminal Units
```
"How is chilled water distributed?
 - Fan coil units in each suite?
 - VAV boxes?
 - Baseboards?
 - Constant volume boxes?"
```

### Size
```
"What's the chiller capacity? (Can be in tons, kW, or BTU/hr)"
```

### Installation Year
```
"About how old is the chiller?"
```

### Common Operator Responses

| Response | Inferred Fields |
|----------|-----------------|
| "No chiller, just window ACs" | `central_plant_cooler_exists: false` |
| "200-ton Carrier chiller, air-cooled" | Type: `air_cooled_chiller`, Size: 703.4 kW |
| "Water-cooled chiller with cooling tower" | Type: `water_cooled_chiller` |
| "Chilled water to fan coils in each suite" | Terminal units: `fan_coil_units` |

---

## Central Plant Heater (Boiler / Furnace)

### Existence
```
"Does the building have a central heating system (boiler or furnace)?"
"Is heating centralized or handled in each suite?"
```

### Type
```
"What type of heating system is it?
 - Gas boiler?
 - Electric boiler?
 - Gas furnace (forced air)?
 - Heat pump?"

[If gas boiler] "Is it a condensing boiler (high-efficiency, AFUE ≥90%) or standard boiler?"
```

### Terminal Units
```
"How is heat distributed through the building?
 - Baseboards?
 - Radiators?
 - Fan coil units?
 - Forced air (VAV or constant volume)?"
```

### Size
```
"What's the total heating capacity? (Can be in MBH, BTU/hr, kW, or MW)

If multiple boilers: How many boilers, and what's the capacity of each?"
```

### Installation Year
```
"About how old are the boilers? Installation year or rough estimate?"
```

### Common Operator Responses

| Response | Inferred Fields |
|----------|-----------------|
| "2 Weil-McLain gas boilers, 500 MBH each" | Type: `gas_boiler` (Weil-McLain = non-condensing), Size: 293 kW total, Count: 2 |
| "High-efficiency Navien condensing boiler" | Type: `condensing_gas_boiler` |
| "Hot water baseboard radiators" | Terminal units: `baseboards` |
| "Old gas boiler, maybe 1995" | Installation year: ~1995 |
| "Electric furnace, forced air" | Type: `electric_furnace` |

---

## Central Plant Heat Pump

### Existence
```
"Does the building have a central heat pump system?"
```

### Type
```
"Is it an air-source or ground-source (geothermal) heat pump?"
```

### Size
```
"What's the heat pump capacity? (kW or tons)"
```

### Installation Year
```
"About how old is the heat pump?"
```

### Common Operator Responses

| Response | Inferred Fields |
|----------|-----------------|
| "Air-source heat pump, 50 tons" | Type: `air_source_heat_pump`, Size: 175.9 kW |
| "Geothermal wells, installed 2020" | Type: `ground_source_heat_pump`, Installation year: 2020 |

---

## Domestic Hot Water Heater

### Existence & Configuration
```
"How is domestic hot water provided?
 - Central tank with distribution loop?
 - Individual water heaters in each suite?"
```

### Type
```
"What type of water heater?
 - Gas storage tank?
 - Electric storage tank?
 - Tankless (gas or electric)?
 - Heat pump water heater?
 - Indirect tank (heated by boiler)?"
```

### Size
```
"What's the water heater capacity? (Gallons or litres)"
```

### Installation Year
```
"About how old are the water heaters?"
```

### Common Operator Responses

| Response | Inferred Fields |
|----------|-----------------|
| "Electric water heaters in each suite" | `central_distribution: false`, Type: `electric_storage` |
| "Central gas-fired tank, 100 gallons" | `central_distribution: true`, Type: `gas_storage`, Size: 379 litres |
| "Tankless gas water heaters" | Type: `gas_instantaneous` |
| "Indirect tank off the boiler" | Type: `indirect_tank` |
| "Heat pump water heater installed 2022" | Type: `heat_pump_water_heater`, Installation year: 2022 |

---

## Rooftop Units

### Existence
```
"Are there rooftop HVAC units serving the building?"
```

### Type
```
"What type of rooftop units?
 - Packaged terminal air conditioners (PTACs)?
 - Split systems (outdoor condenser + indoor air handler)?
 - Heat pumps?"
```

### Heating/Cooling Type
```
"Do the rooftop units provide heating? If so, electric resistance, gas, or heat pump?"
"For cooling, is it direct expansion (DX)?"
```

### Size
```
"How many rooftop units are there?
What's the cooling capacity? (Tons or kW per unit, or total)"
```

### Installation Year
```
"About how old are the rooftop units?"
```

### Common Operator Responses

| Response | Inferred Fields |
|----------|-----------------|
| "Carrier rooftop units, 15 total, 5 tons each" | Type: likely `split_system_air_conditioner`, Count: 15, Size: 264 kW total |
| "PTACs in each unit" | Type: `packaged_terminal_air_conditioner` |
| "Rooftop heat pumps with electric backup" | Type: `split_system_heat_pump`, Heating type: `electric_resistance` |

---

## Suite Heat Pumps

### Existence
```
"Are there mini-split heat pumps or PTACs in individual suites?"
```

### Type
```
"What type?
 - Mini-split heat pumps (ductless)?
 - Packaged terminal heat pumps (PTHP)?"
```

### Size
```
"What's the capacity per unit? (Tons or kW)"
```

### Installation Year
```
"About how old are the heat pumps?"
```

### Common Operator Responses

| Response | Inferred Fields |
|----------|-----------------|
| "Mitsubishi mini-splits in each suite, 1.5 tons" | Type: `mini_split_heat_pump`, Size: 5.3 kW per unit |
| "PTHPs, about 12,000 BTU each" | Type: `packaged_terminal_heat_pump`, Size: 3.5 kW |

---

## Elevators / Escalators

### Existence
```
"How many elevators does the building have?"
"Are there any escalators?"
```

### Type
```
"What type of elevators?
 - Hydraulic?
 - Traction (cable-driven)?
 - Escalators?"
```

### Count
```
"How many passenger elevators? Any freight elevators?"
```

### Installation Year
```
"About how old are the elevators? Have they been modernized?"
```

### Common Operator Responses

| Response | Inferred Fields |
|----------|-----------------|
| "2 passenger elevators, traction, installed 1998" | Type: `traction_elevator`, Count: 2, Installation year: 1998 |
| "1 hydraulic elevator, old — probably 1980s" | Type: `hydraulic_elevator`, Count: 1, Installation year: ~1985 |
| "3 elevators, modernized in 2015" | Count: 3, Installation year: 2015 (use modernization year) |

---

## Lighting

### Type
```
"What type of lighting is used in common areas?
 - LED?
 - Fluorescent (T8, T5)?
 - Older technology?"
```

### Controls
```
"Are there any lighting controls?
 - Occupancy sensors?
 - Daylight dimming?
 - Time clocks or scheduling?
 - Manual switches only?"
```

### Coverage
```
"Has there been an LED retrofit? If so, what percentage of the building is LED?"
```

### Common Operator Responses

| Response | Inferred Fields |
|----------|-----------------|
| "All LED after 2020 retrofit" | Type: LED, Controls: (ask follow-up) |
| "Mostly fluorescent, some LED in hallways" | Type: Mix (document as fluorescent primary) |
| "Occupancy sensors in common areas" | Controls: Occupancy sensors present |
| "Manual switches, no automation" | Controls: Manual only |

---

## Photovoltaic (Solar PV)

### Existence
```
"Does the building have solar panels (photovoltaic system)?"
```

### Capacity
```
"What's the solar system capacity? (kW or number of panels)"
```

### Installation Year
```
"When was the solar system installed?"
```

### Common Operator Responses

| Response | Inferred Fields |
|----------|-----------------|
| "50 kW rooftop solar, installed 2021" | Capacity: 50 kW, Installation year: 2021 |
| "No solar panels" | `photovoltaic_exists: false` |
| "120 panels, not sure about kW" | Estimate: ~40-50 kW (typical 350W panels), confirm |

---

## Follow-Up Question Patterns

### When Capacity is Ambiguous

```
"You mentioned [X]. Is that per unit or total for the building?"
"Is that [X] in MBH, kW, tons, or something else?"
```

### When Type is Unclear

```
"When you say [X], do you mean [option A] or [option B]?"
```

Example:
- Operator: "Rooftop units"
- Follow-up: "Are those packaged units (all-in-one) or split systems (separate indoor/outdoor)?"

### When Age is Vague

```
"You mentioned it's old. Best guess — installed in the 1990s, 2000s, or earlier?"
"Has it been replaced or modernized since the building was built?"
```

### When Count is Missing

```
"How many [units] are there?"
"Is there one [unit] for the whole building, or multiple?"
```

---

## Parsing Tips

### Extract Key Information

From: "2 Weil-McLain boilers, 500 MBH each, installed around 2005"

Extract:
- **Count**: 2
- **Brand**: Weil-McLain → infer standard gas boiler (non-condensing)
- **Capacity per unit**: 500 MBH
- **Total capacity**: 1000 MBH = 293 kW
- **Installation year**: ~2005

### Handle Manufacturer Names

Common brands and what they typically indicate:

| Brand | Typical Type |
|-------|--------------|
| Weil-McLain | Gas boiler (standard, non-condensing) |
| Navien | Condensing boiler or tankless water heater |
| Carrier | Rooftop units, chillers |
| Trane | Rooftop units, chillers |
| Mitsubishi | Mini-split heat pumps |
| Rheem | Water heaters (gas or electric) |
| A.O. Smith | Water heaters |

### Handle Multiple Systems

If operator describes multiple systems in one section:
- Identify the **primary** system (handles majority of load)
- Note the secondary in follow-up if needed
- Survey schema expects one primary system per section

Example:
- "We have 2 old boilers and 1 new heat pump"
- Ask: "Which handles most of the heating — the boilers or the heat pump?"

---

## Validation Checklist

After gathering information for each section, confirm:

- [ ] `_exists` field is set (true/false)
- [ ] If `_exists = true`, type field is populated with valid enum
- [ ] If `_exists = true`, size/capacity is populated (or noted as unknown)
- [ ] Installation year is populated (estimate acceptable)
- [ ] For central plants, distribution/terminal units are specified

If any critical field is still null after questioning, note it for site visit or nameplate
verification.

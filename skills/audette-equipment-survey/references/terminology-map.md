# Equipment Terminology Mapping

Translates language found in PCNAs, CNAs, iAuditor reports, and equipment surveys
to Audette enum values.

---

## Heating → `central_plant_heater_type`

| Document says | Audette value |
|---|---|
| "gas boiler", "natural gas boiler", "atmospheric boiler", "power-vent boiler" | `gas_boiler` |
| "condensing boiler", "high-efficiency boiler", "modcon", "AFUE 90%+" | `condensing_gas_boiler` |
| Lochinvar, Viessmann Vitodens, Triangle Tube (unspecified) | `condensing_gas_boiler` |
| Weil-McLain, Burnham, Peerless (unspecified) | `gas_boiler` |
| "electric boiler", "electric resistance boiler" | `electric_resistance_boiler` |
| "gas furnace", "forced-air gas", "warm-air furnace" (AFUE < 90%) | `gas_furnace` |
| "high-efficiency furnace", "90+ furnace", "condensing furnace" | `high_efficiency_gas_furnace` |
| "electric furnace", "electric forced-air" | `electric_furnace` |
| "district heat", "steam from utility", "hot water from district loop" | `hydronic_furnace` |

---

## Heating distribution → `central_plant_heater_terminal_units`

| Document says | Audette value |
|---|---|
| "baseboard", "fin-tube baseboard", "convector", "hydronic baseboard" | `baseboards` |
| "fan coil unit", "FCU", "4-pipe fan coil" | `fan_coil_units` |
| "VAV", "variable air volume", "VAV box" | `variable_air_volume_boxes` |
| "CAV", "constant volume", "single-duct terminal" | `constant_volume_boxes` |
| "unit heater" fed from central boiler | `fan_coil_units` |

---

## Cooling → `central_plant_cooler_type`

| Document says | Audette value |
|---|---|
| "chiller", "air-cooled chiller", "centrifugal chiller", "screw chiller" | `air_cooled_chiller` |
| "water-cooled chiller", "cooling tower", "condenser water loop" | `water_cooled_chiller` |

---

## Ventilation / AHU → `air_handling_equipment_type`

| Document says | Audette value |
|---|---|
| "makeup air unit", "MAU", "DOAS", "dedicated outdoor air" | `make_up_air_unit` |
| "air handling unit", "AHU", "central air handler" | `packaged_air_handling_unit` |
| "split AHU", "remote condenser AHU" | `split_air_handling_unit` |
| "suite air exchanger", "in-suite ventilation", "HRV per suite", "ERV per unit" | `suite_air_exchangers` |
| "energy recovery ventilator", "ERV", "HRV" (central building unit) | `suite_energy_recovery_ventilator` |
| "exhaust fan system", "exhaust-only ventilation" | `exhaust_only_air_handling_unit` |

---

## Domestic hot water → `domestic_hot_water_heater_type`

The API has three types. Map all document variants to one of these:

| Document says | Audette value |
|---|---|
| "gas water heater", "gas hot water tank", "natural gas DHW", "gas storage", "gas tankless", "on-demand gas", "combi boiler (DHW)" | `gas_heater` |
| "electric water heater", "electric tank", "electric tankless", "on-demand electric", "heat pump water heater", "HPWH" | `electric_heater` |
| "indirect water heater", "indirect tank", "boiler-fed DHW", "sidearm heater" | `indirect_heater` |

---

## Rooftop units → `rooftop_unit_heating_type` / `rooftop_unit_cooling_type`

There is no `type` field — describe the heating and cooling capabilities separately.

| Document says | Field | Value |
|---|---|---|
| "gas RTU", "gas-fired rooftop", "gas packaged unit" | `rooftop_unit_heating_type` | `gas` |
| "electric RTU", "electric heat rooftop" | `rooftop_unit_heating_type` | `electric_resistance` |
| "RTU with DX cooling", "packaged DX unit", "cooling-only RTU" | `rooftop_unit_cooling_type` | `direct_expansion` |

---

## Terminal cooling → `terminal_cooler_units`

| Document says | Audette value |
|---|---|
| "PTAC (cooling only)", "packaged terminal air conditioner" | `cooling_ptac` |
| "split A/C", "ductless A/C", "mini-split A/C (cooling only)" | `split_air_conditioner` |
| "window A/C", "window unit", "through-the-wall A/C" | `window_air_conditioner` |

---

## Terminal heating → `terminal_heater_units`

| Document says | Audette value |
|---|---|
| "electric baseboard", "electric fin baseboard" | `electric_baseboard` |
| "electric unit heater", "electric wall heater" | `electric_unit_heater` |
| "gas unit heater", "gas cabinet heater" | `gas_unit_heater` |
| "condensing gas unit heater" | `condensing_gas_unit_heater` |
| "electric PTAC (heat)", "electric resistance PTAC" | `electric_resistance_ptac` |
| "gas PTAC" | `gas_ptac` |

---

## Distributed heat pumps → `heat_pump_type`

| Document says | Audette value |
|---|---|
| "mini-split heat pump", "ductless heat pump", "split heat pump", "split ASHP" | `split_air_source_heat_pump` |
| "water loop heat pump", "WLHP", "heat pump loop" | `water_loop_heat_pump` |

---

## Unit conversions

**All `*_size` capacity fields submit in TONS** (heating, cooling, and DHW alike — never kW, never
litres/gallons; see skill.md). Convert TO tons:

| From | To | Multiply by |
|---|---|---|
| MBH (heating capacity) | **tons** | ÷ 12 |
| BTU/h | **tons** | ÷ 12,000 |
| kW | **tons** | ÷ 3.517 |
| DHW tank volume (gallons), only if no nameplate | **tons** | ÷ 40 (fallback — flag it) |

(Airflow fields `*_supply_air_rate` are the sole exception: submit in CFM, not tons.)

---

## Common PCNA / CNA section titles to scan

- "Mechanical Systems", "HVAC", "Heating Plant", "Cooling System"
- "Domestic Hot Water", "Plumbing Systems"
- "Vertical Transportation", "Elevators"
- "Electrical Systems" (for PV, electric equipment)
- "Laundry", "Common Amenities"
- Equipment schedules / appendices (model numbers, install years)

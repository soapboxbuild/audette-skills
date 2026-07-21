# Audette Equipment Survey Schema

Full reference for all sections, fields, and valid enum values.
Every top-level section must be present in the submitted payload.

> **UNITS — the estimator works in NATURAL engineering units** (cooling in tons, heating in MBH/kW,
> DHW by nameplate MBH or tank gallons, airflow in CFM, PV in kW — whatever is natural for the
> equipment). **The estimator does NOT apply Audette's ton-equivalent convention and does NOT submit
> directly.** It produces a natural-unit draft and hands it to the **`audette-equipment-survey`** skill,
> which is the single place that converts every capacity to ton-equivalents and calls
> `submit_equipment_survey` (the survey converts the estimator's numbers the same way it converts
> anything sourced from documents). So: estimate here in natural units; the survey converts + submits.

---

## air_handling_equipment

Centralized air handling units serving the whole building or major zones (not suite-level).

| Field | Type | Valid values |
|-------|------|-------------|
| `air_handling_equipment_exists` | bool | `true` / `false` |
| `air_handling_equipment_type` | enum\|null | `make_up_air_unit`, `packaged_air_handling_unit`, `split_air_handling_unit`, `suite_air_exchangers`, `suite_energy_recovery_ventilator`, `exhaust_only_air_handling_unit` |
| `air_handling_equipment_heating_type` | enum\|null | `electric_resistance`, `gas`, `hydronic` |
| `air_handling_equipment_cooling_type` | enum\|null | `direct_expansion`, `hydronic` |
| `air_handling_equipment_supply_air_rate` | float\|null | CFM |
| `air_handling_equipment_average_installation_year` | int\|null | e.g. `2005` |

**Type guide:**
- `make_up_air_unit` — fresh air supply only, no recirculation (common in garages, commercial kitchens)
- `packaged_air_handling_unit` — all components in one cabinet (heating, cooling, fan)
- `split_air_handling_unit` — separate indoor/outdoor components
- `suite_air_exchangers` — individual HRV/ERV units in each suite
- `suite_energy_recovery_ventilator` — ERV in each suite (recovers heat + moisture)
- `exhaust_only_air_handling_unit` — exhaust fans only, no supply

---

## central_plant_cooler

Centralized cooling plant serving the whole building (chiller + distribution).

| Field | Type | Valid values |
|-------|------|-------------|
| `central_plant_cooler_exists` | bool | `true` / `false` |
| `central_plant_cooler_type` | enum\|null | `air_cooled_chiller`, `water_cooled_chiller` |
| `central_plant_cooler_terminal_units` | enum\|null | `baseboards`, `constant_volume_boxes`, `fan_coil_units`, `variable_air_volume_boxes` |
| `central_plant_cooler_size` | float\|null | natural: tons (or kW) — survey converts |
| `central_plant_cooler_average_installation_year` | int\|null | e.g. `2010` |

**Terminal unit guide:**
- `baseboards` — hydronic baseboard convectors
- `fan_coil_units` — fan + coil unit in each zone/suite (FCU)
- `constant_volume_boxes` — fixed-flow air distribution
- `variable_air_volume_boxes` — VAV boxes (variable airflow)

---

## central_plant_heater

Centralized heating plant (boiler, furnace) serving the whole building.

| Field | Type | Valid values |
|-------|------|-------------|
| `central_plant_heater_exists` | bool | `true` / `false` |
| `central_plant_heater_type` | enum\|null | `condensing_gas_boiler`, `electric_furnace`, `electric_resistance_boiler`, `gas_boiler`, `gas_furnace`, `high_efficiency_gas_furnace`, `hydronic_furnace` |
| `central_plant_heater_terminal_units` | enum\|null | `baseboards`, `constant_volume_boxes`, `fan_coil_units`, `variable_air_volume_boxes` |
| `central_plant_heater_size` | float\|null | natural: MBH (or kW) — survey converts |
| `central_plant_heater_average_installation_year` | int\|null | e.g. `1998` |

**Type guide:**
- `gas_boiler` — standard atmospheric or power-vented gas boiler (AFUE < 90%)
- `condensing_gas_boiler` — high-efficiency condensing boiler (AFUE ≥ 90%, usually ≥ 95%)
- `high_efficiency_gas_furnace` — forced-air furnace, AFUE ≥ 90%
- `gas_furnace` — standard gas furnace (AFUE < 90%)
- `electric_resistance_boiler` — electric boiler (resistance elements)
- `electric_furnace` — electric forced-air furnace
- `hydronic_furnace` — water-source (district heat or geo) furnace

**Estimate in natural units** (the survey converts to tons at submit):
- 3 × 120 MBH boilers → estimate **360 MBH** total
- 500 MBH boiler → estimate **500 MBH**

---

## central_plant_heat_pump

Centralized heat pump system (not suite-level mini-splits).

| Field | Type | Valid values |
|-------|------|-------------|
| `central_plant_heat_pump_exists` | bool | `true` / `false` |
| `central_plant_heat_pump_type` | enum\|null | `air_source_heat_pump`, `ground_source_heat_pump` |
| `central_plant_heat_pump_size` | float\|null | natural: tons (or kW) — survey converts |
| `central_plant_heat_pump_average_installation_year` | int\|null | e.g. `2018` |

---

## domestic_hot_water_heater

Building domestic hot water system.

| Field | Type | Valid values |
|-------|------|-------------|
| `domestic_hot_water_heater_exists` | bool | `true` / `false` |
| `domestic_hot_water_heater_central_distribution` | bool | `true` = central tank + distribution loop; `false` = suite-level water heaters |
| `domestic_hot_water_heater_type` | enum\|null | `gas_storage`, `electric_storage`, `gas_instantaneous`, `electric_instantaneous`, `heat_pump_water_heater`, `indirect_tank` |
| `domestic_hot_water_heater_size` | float\|null | natural: nameplate MBH, or tank gallons — survey converts (never pre-convert here) |
| `domestic_hot_water_heater_average_installation_year` | int\|null | e.g. `2012` |

**Type guide:**
- `gas_storage` — gas-fired tank water heater (most common in multifamily)
- `electric_storage` — electric tank water heater
- `gas_instantaneous` — tankless gas (on-demand)
- `electric_instantaneous` — tankless electric
- `heat_pump_water_heater` — HPWH / heat pump water heater
- `indirect_tank` — storage tank heated by boiler (no burner of its own)

---

## rooftop_units

Packaged or split rooftop HVAC units serving zones or suites directly.

| Field | Type | Valid values |
|-------|------|-------------|
| `rooftop_unit_exists` | bool | `true` / `false` |
| `rooftop_unit_type` | enum\|null | `packaged_terminal_air_conditioner`, `packaged_terminal_heat_pump`, `split_system_air_conditioner`, `split_system_heat_pump` |
| `rooftop_unit_heating_type` | enum\|null | `electric_resistance`, `gas`, `hydronic` |
| `rooftop_unit_cooling_type` | enum\|null | `direct_expansion`, `hydronic` |
| `rooftop_unit_size` | float\|null | RTUs size by AIRFLOW — estimate `rooftop_unit_supply_air_rate` in CFM |
| `rooftop_unit_average_installation_year` | int\|null | e.g. `2015` |

---

## suite_heat_pumps

Mini-split or PTAC heat pumps at the suite level (not central plant).

| Field | Type | Valid values |
|-------|------|-------------|
| `suite_heat_pump_exists` | bool | `true` / `false` |
| `suite_heat_pump_type` | enum\|null | `mini_split_heat_pump`, `packaged_terminal_heat_pump` |
| `suite_heat_pump_size` | float\|null | natural: tons per unit (or kW) — survey converts |
| `suite_heat_pump_average_installation_year` | int\|null | e.g. `2020` |

---

## elevators_escalators

| Field | Type | Valid values |
|-------|------|-------------|
| `elevators_escalators_exists` | bool | `true` / `false` |
| `elevators_escalators_type` | enum\|null | `hydraulic_elevator`, `traction_elevator`, `escalator` |
| `elevators_escalators_count` | int\|null | Number of units |
| `elevators_escalators_average_installation_year` | int\|null | e.g. `1995` |

**Type guide:**
- `hydraulic_elevator` — uses hydraulic piston; common in low-rise (≤ 6 floors)
- `traction_elevator` — uses cables and counterweight; common in mid/high-rise

---

## photovoltaics

On-site solar PV system.

| Field | Type | Valid values |
|-------|------|-------------|
| `photovoltaics_exists` | bool | `true` / `false` |
| `photovoltaics_size` | float\|null | kW DC nameplate capacity |
| `photovoltaics_average_installation_year` | int\|null | e.g. `2022` |

---

## generic_hvac_equipment

Catch-all for equipment that doesn't fit the above categories (e.g. unit heaters,
radiant panels, district energy connections, swimming pool heating).

This is a **list** of objects, each with:

| Field | Type | Notes |
|-------|------|-------|
| `generic_hvac_equipment_type` | string | Free text — describe the equipment |
| `generic_hvac_equipment_heating_type` | enum\|null | `electric_resistance`, `gas`, `hydronic` |
| `generic_hvac_equipment_cooling_type` | enum\|null | `direct_expansion`, `hydronic` |
| `generic_hvac_equipment_size` | float\|null | natural (self-tag `size_units`: cfm\|mbtu\|tons) |
| `generic_hvac_equipment_average_installation_year` | int\|null | e.g. `2008` |

If no generic equipment exists, pass an empty list: `"generic_hvac_equipment": []`

---

## Full empty payload template

Use this as a starting point, then fill in values:

```json
{
  "air_handling_equipment": {
    "air_handling_equipment_exists": false,
    "air_handling_equipment_type": null,
    "air_handling_equipment_heating_type": null,
    "air_handling_equipment_cooling_type": null,
    "air_handling_equipment_supply_air_rate": null,
    "air_handling_equipment_average_installation_year": null
  },
  "central_plant_cooler": {
    "central_plant_cooler_exists": false,
    "central_plant_cooler_type": null,
    "central_plant_cooler_terminal_units": null,
    "central_plant_cooler_size": null,
    "central_plant_cooler_average_installation_year": null
  },
  "central_plant_heater": {
    "central_plant_heater_exists": false,
    "central_plant_heater_type": null,
    "central_plant_heater_terminal_units": null,
    "central_plant_heater_size": null,
    "central_plant_heater_average_installation_year": null
  },
  "central_plant_heat_pump": {
    "central_plant_heat_pump_exists": false,
    "central_plant_heat_pump_type": null,
    "central_plant_heat_pump_size": null,
    "central_plant_heat_pump_average_installation_year": null
  },
  "domestic_hot_water_heater": {
    "domestic_hot_water_heater_exists": false,
    "domestic_hot_water_heater_central_distribution": false,
    "domestic_hot_water_heater_type": null,
    "domestic_hot_water_heater_size": null,
    "domestic_hot_water_heater_average_installation_year": null
  },
  "rooftop_units": {
    "rooftop_unit_exists": false,
    "rooftop_unit_type": null,
    "rooftop_unit_heating_type": null,
    "rooftop_unit_cooling_type": null,
    "rooftop_unit_size": null,
    "rooftop_unit_average_installation_year": null
  },
  "suite_heat_pumps": {
    "suite_heat_pump_exists": false,
    "suite_heat_pump_type": null,
    "suite_heat_pump_size": null,
    "suite_heat_pump_average_installation_year": null
  },
  "elevators_escalators": {
    "elevators_escalators_exists": false,
    "elevators_escalators_type": null,
    "elevators_escalators_count": null,
    "elevators_escalators_average_installation_year": null
  },
  "photovoltaics": {
    "photovoltaics_exists": false,
    "photovoltaics_size": null,
    "photovoltaics_average_installation_year": null
  },
  "generic_hvac_equipment": []
}
```

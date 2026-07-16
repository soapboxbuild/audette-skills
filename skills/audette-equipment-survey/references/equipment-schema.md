# Audette Equipment Survey Schema

Full reference for all sections, fields, and valid enum values.
**Every top-level section must be present in the submitted payload**, even if `_exists` is false.

Source of truth: `submit_equipment_survey` tool on the live Audette MCP.

---

## air_handling_equipment

Central air handling units serving the whole building or major zones (not suite-level).

| Field | Type | Valid values |
|-------|------|-------------|
| `air_handling_equipment_exists` | bool | |
| `air_handling_equipment_type` | enum\|null | `make_up_air_unit`, `packaged_air_handling_unit`, `split_air_handling_unit`, `suite_air_exchangers`, `suite_energy_recovery_ventilator`, `exhaust_only_air_handling_unit` |
| `air_handling_equipment_heating_type` | enum\|null | `electric_resistance`, `gas`, `hydronic` |
| `air_handling_equipment_cooling_type` | enum\|null | `direct_expansion`, `hydronic` |
| `air_handling_equipment_supply_air_rate` | float\|null | CFM |
| `air_handling_equipment_average_installation_year` | int\|null | |

**Type guide:**
- `make_up_air_unit` — fresh air supply only, no recirculation (garages, commercial kitchens)
- `packaged_air_handling_unit` — all components in one cabinet
- `split_air_handling_unit` — separate indoor/outdoor components
- `suite_air_exchangers` — individual HRV/ERV in each suite
- `suite_energy_recovery_ventilator` — ERV per suite (recovers heat + moisture)
- `exhaust_only_air_handling_unit` — exhaust fans only, no supply

---

## central_plant_cooler

Centralized chiller plant with distribution to the building.

| Field | Type | Valid values |
|-------|------|-------------|
| `central_plant_cooler_exists` | bool | |
| `central_plant_cooler_type` | enum\|null | `air_cooled_chiller`, `water_cooled_chiller` |
| `central_plant_cooler_terminal_units` | enum\|null | `baseboards`, `constant_volume_boxes`, `fan_coil_units`, `variable_air_volume_boxes` |
| `central_plant_cooler_size` | float\|null | tons |
| `central_plant_cooler_average_installation_year` | int\|null | |

---

## central_plant_heater

Centralized boiler or furnace plant serving the building.

| Field | Type | Valid values |
|-------|------|-------------|
| `central_plant_heater_exists` | bool | |
| `central_plant_heater_type` | enum\|null | `condensing_gas_boiler`, `electric_furnace`, `electric_resistance_boiler`, `gas_boiler`, `gas_furnace`, `high_efficiency_gas_furnace`, `hydronic_furnace` |
| `central_plant_heater_terminal_units` | enum\|null | `baseboards`, `constant_volume_boxes`, `fan_coil_units`, `variable_air_volume_boxes` |
| `central_plant_heater_size` | float\|null | tons (ton-equivalent — see skill.md's unit-conversions note) |
| `central_plant_heater_average_installation_year` | int\|null | |

**Type guide:**
- `gas_boiler` — standard efficiency (AFUE < 90%)
- `condensing_gas_boiler` — high-efficiency condensing (AFUE ≥ 90%)
- `high_efficiency_gas_furnace` — forced-air, AFUE ≥ 90%
- `gas_furnace` — standard forced-air (AFUE < 90%)
- `electric_resistance_boiler` — electric boiler
- `electric_furnace` — electric forced-air
- `hydronic_furnace` — district heat or geo water source

---

## central_plant_heat_pump

Centralized heat pump (not suite-level). Use `heat_pump` for distributed mini-splits.

| Field | Type | Valid values |
|-------|------|-------------|
| `central_plant_heat_pump_exists` | bool | |
| `central_plant_heat_pump_type` | enum\|null | `air_source_heat_pump`, `ground_source_heat_pump` |
| `central_plant_heat_pump_size` | float\|null | tons (ton-equivalent — see skill.md's unit-conversions note) |
| `central_plant_heat_pump_average_installation_year` | int\|null | |

---

## domestic_hot_water_heater

Building domestic hot water system.

| Field | Type | Valid values |
|-------|------|-------------|
| `domestic_hot_water_heater_exists` | bool | |
| `domestic_hot_water_heater_central_distribution` | bool | `true` = central tank + loop; `false` = suite-level units |
| `domestic_hot_water_heater_type` | enum\|null | `electric_heater`, `gas_heater`, `indirect_heater` |
| `domestic_hot_water_heater_size` | float\|null | tons (ton-equivalent thermal/recovery capacity — prefer nameplate rating; fallback `gallons ÷ 40` if only tank volume is known; see skill.md's DHW note) |
| `domestic_hot_water_heater_average_installation_year` | int\|null | |

**Note:** The API uses three simplified types. See `terminology-map.md` for document-to-value mapping (gas storage, tankless, HPWH, etc. all map to one of these three).

---

## rooftop_unit

Packaged rooftop units — serving zones or suites directly from the roof.

| Field | Type | Valid values |
|-------|------|-------------|
| `rooftop_unit_exists` | bool | |
| `rooftop_unit_heating_type` | enum\|null | `electric_resistance`, `gas` |
| `rooftop_unit_cooling_type` | enum\|null | `direct_expansion` |
| `rooftop_unit_supply_air_rate` | float\|null | CFM total |
| `rooftop_unit_average_installation_year` | int\|null | |

**Note:** There is no `type` field — describe heating and cooling capabilities directly.

---

## terminal_cooler

Suite-level or zone-level cooling-only terminal equipment.

| Field | Type | Valid values |
|-------|------|-------------|
| `terminal_cooler_exists` | bool | |
| `terminal_cooler_units` | enum\|null | `cooling_ptac`, `split_air_conditioner`, `window_air_conditioner` |
| `terminal_cooler_size` | float\|null | tons |
| `terminal_cooler_average_installation_year` | int\|null | |

---

## terminal_heater

Suite-level or zone-level heating-only terminal equipment (not heat pumps, not central plant distribution).

| Field | Type | Valid values |
|-------|------|-------------|
| `terminal_heater_exists` | bool | |
| `terminal_heater_units` | enum\|null | `condensing_gas_unit_heater`, `electric_baseboard`, `electric_resistance_ptac`, `electric_unit_heater`, `gas_ptac`, `gas_unit_heater` |
| `terminal_heater_size` | float\|null | tons (ton-equivalent heating capacity — see skill.md's unit-conversions note) |
| `terminal_heater_cooler_size` | float\|null | tons (for PTAC units that provide both) |
| `terminal_heater_average_installation_year` | int\|null | |

---

## heat_pump

Distributed (suite-level) heat pumps — mini-splits, water loop heat pumps.

| Field | Type | Valid values |
|-------|------|-------------|
| `heat_pump_exists` | bool | |
| `heat_pump_type` | enum\|null | `water_loop_heat_pump`, `split_air_source_heat_pump` |
| `heat_pump_heating_coefficient_of_performance` | float\|null | e.g. `2.5` |
| `heat_pump_cooling_coefficient_of_performance` | float\|null | e.g. `3.5` |
| `heat_pump_heating_load_ratio` | float\|null | 0.0–1.0 fraction of heating load served |
| `heat_pump_cooling_load_ratio` | float\|null | 0.0–1.0 fraction of cooling load served |
| `heat_pump_size` | float\|null | tons per unit (ton-equivalent — see skill.md's unit-conversions note) |
| `heat_pump_installation_year` | int\|null | |

**Visual identification from rooftop imagery:** Arrays of small gray boxes along the roof centerline typically indicate `split_air_source_heat_pump` systems. Count ≈ number of suites.

---

## other_equipment

Miscellaneous building equipment: laundry, vertical transport, solar PV.

| Field | Type | Valid values |
|-------|------|-------------|
| `clothes_dryers_exists` | bool | |
| `clothes_dryers_type` | enum\|null | `electric`, `gas` |
| `clothes_dryers_energy_density` | float\|null | W/m² |
| `clothes_dryers_average_installation_year` | int\|null | |
| `clothes_washers_exists` | bool | |
| `clothes_washers_energy_density` | float\|null | W/m² |
| `clothes_washers_average_installation_year` | int\|null | |
| `elevators_exists` | bool | |
| `elevators_quantity` | int\|null | |
| `elevators_average_installation_year` | int\|null | |
| `escalator_exists` | bool | |
| `escalator_quantity` | int\|null | |
| `escalator_floor_area_served` | int\|null | m² |
| `escalator_variable_frequency_drive` | bool\|null | |
| `escalator_installation_year` | int\|null | |
| `rooftop_photovoltaics_exists` | bool | |
| `rooftop_photovoltaics_size` | float\|null | kW DC nameplate |
| `rooftop_photovoltaics_average_installation_year` | int\|null | |

---

## generic_hvac_equipment

Catch-all for equipment not covered above (radiant panels, unit heaters, district energy connections, pool heating, etc.). Pass an empty list `[]` if nothing applies.

**All fields are required and non-nullable. Omit the entry entirely rather than passing null.**

| Field | Type | Valid values |
|-------|------|-------------|
| `name` | string | Free text description |
| `end_use` | enum | `outdoor_air_cooling`, `outdoor_air_heating`, `skin_cooling`, `skin_heating` |
| `fuel` | string | e.g. `natural_gas`, `electricity`, `district_heat` |
| `size` | float | In `size_units` below |
| `size_units` | enum | `cfm`, `mbtu`, `tons` |
| `coefficient_of_performance` | float | e.g. `0.85` for gas; `3.5` for heat pump |
| `load_ratio` | float | 0.0–1.0 fraction of end-use load served |
| `installation_year` | int | |
| `life_span` | int | Years (e.g. `25`) |

---

## Full empty payload template

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
  "rooftop_unit": {
    "rooftop_unit_exists": false,
    "rooftop_unit_heating_type": null,
    "rooftop_unit_cooling_type": null,
    "rooftop_unit_supply_air_rate": null,
    "rooftop_unit_average_installation_year": null
  },
  "terminal_cooler": {
    "terminal_cooler_exists": false,
    "terminal_cooler_units": null,
    "terminal_cooler_size": null,
    "terminal_cooler_average_installation_year": null
  },
  "terminal_heater": {
    "terminal_heater_exists": false,
    "terminal_heater_units": null,
    "terminal_heater_size": null,
    "terminal_heater_cooler_size": null,
    "terminal_heater_average_installation_year": null
  },
  "heat_pump": {
    "heat_pump_exists": false,
    "heat_pump_type": null,
    "heat_pump_heating_coefficient_of_performance": null,
    "heat_pump_cooling_coefficient_of_performance": null,
    "heat_pump_heating_load_ratio": null,
    "heat_pump_cooling_load_ratio": null,
    "heat_pump_size": null,
    "heat_pump_installation_year": null
  },
  "other_equipment": {
    "clothes_dryers_exists": false,
    "clothes_dryers_type": null,
    "clothes_dryers_energy_density": null,
    "clothes_dryers_average_installation_year": null,
    "clothes_washers_exists": false,
    "clothes_washers_energy_density": null,
    "clothes_washers_average_installation_year": null,
    "elevators_exists": false,
    "elevators_quantity": null,
    "elevators_average_installation_year": null,
    "escalator_exists": false,
    "escalator_quantity": null,
    "escalator_floor_area_served": null,
    "escalator_variable_frequency_drive": null,
    "escalator_installation_year": null,
    "rooftop_photovoltaics_exists": false,
    "rooftop_photovoltaics_size": null,
    "rooftop_photovoltaics_average_installation_year": null
  },
  "generic_hvac_equipment": []
}
```

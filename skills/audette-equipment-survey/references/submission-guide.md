# Equipment Survey Submission Guide

Authoritative reference for `submit_equipment_survey` — extracted directly from the
product-platform-api source code. Use this alongside `equipment-schema.md` (enum values)
and `audette-topology.md` (model impact).

---

## Tool Call

```python
submit_equipment_survey(
    building_model_uid = "<UUID>",    # from get_building_model_details or buildings[]
    equipment_survey   = { ... }      # complete dict — all 11 top-level keys required
)
```

**Returns:** `{"success": True}` or `{"success": False, "error": "<message>"}`

Successful submission **automatically triggers re-modelling**. No separate call needed.

---

## Complete Payload Template

Every key must be present. Set `*_exists = false` and all other fields to `null` for
sections that don't apply. **Do not omit any top-level key — the API will reject the payload.**

```python
{
  "air_handling_equipment": {
    "air_handling_equipment_exists": bool,                  # REQUIRED
    "air_handling_equipment_type": str | null,              # see enum below
    "air_handling_equipment_heating_type": str | null,      # see enum below
    "air_handling_equipment_cooling_type": str | null,      # see enum below
    "air_handling_equipment_supply_air_rate": float | null, # CFM
    "air_handling_equipment_average_installation_year": int | null
  },

  "central_plant_cooler": {
    "central_plant_cooler_exists": bool,                    # REQUIRED
    "central_plant_cooler_type": str | null,
    "central_plant_cooler_terminal_units": str | null,
    "central_plant_cooler_size": float | null,              # tons
    "central_plant_cooler_average_installation_year": int | null
  },

  "central_plant_heater": {
    "central_plant_heater_exists": bool,                    # REQUIRED
    "central_plant_heater_type": str | null,
    "central_plant_heater_terminal_units": str | null,
    "central_plant_heater_size": float | null,              # tons (ton-equivalent)
    "central_plant_heater_average_installation_year": int | null
  },

  "central_plant_heat_pump": {
    "central_plant_heat_pump_exists": bool,                 # REQUIRED
    "central_plant_heat_pump_type": str | null,
    "central_plant_heat_pump_size": float | null,           # tons (ton-equivalent)
    "central_plant_heat_pump_average_installation_year": int | null
  },

  "domestic_hot_water_heater": {
    "domestic_hot_water_heater_exists": bool,               # REQUIRED — must be true
    "domestic_hot_water_heater_central_distribution": bool, # REQUIRED
    "domestic_hot_water_heater_type": str | null,
    "domestic_hot_water_heater_size": float | null,         # tons (ton-equivalent; prefer nameplate rating, else gallons ÷ 40)
    "domestic_hot_water_heater_average_installation_year": int | null
  },

  "rooftop_unit": {
    "rooftop_unit_exists": bool,                            # REQUIRED
    "rooftop_unit_heating_type": str | null,
    "rooftop_unit_cooling_type": str | null,                # REQUIRED if exists=true
    "rooftop_unit_supply_air_rate": float | null,           # CFM
    "rooftop_unit_average_installation_year": int | null
  },

  "terminal_cooler": {
    "terminal_cooler_exists": bool,                         # REQUIRED
    "terminal_cooler_units": str | null,
    "terminal_cooler_size": float | null,                   # tons
    "terminal_cooler_average_installation_year": int | null
  },

  "terminal_heater": {
    "terminal_heater_exists": bool,                         # REQUIRED
    "terminal_heater_units": str | null,
    "terminal_heater_size": float | null,                   # tons (ton-equivalent heating capacity)
    "terminal_heater_cooler_size": float | null,            # tons (for PTACs)
    "terminal_heater_average_installation_year": int | null
  },

  "heat_pump": {
    "heat_pump_exists": bool,                               # REQUIRED
    "heat_pump_type": str | null,
    "heat_pump_heating_coefficient_of_performance": float | null,
    "heat_pump_cooling_coefficient_of_performance": float | null,
    "heat_pump_heating_load_ratio": float | null,           # 0.0–1.0
    "heat_pump_cooling_load_ratio": float | null,           # 0.0–1.0
    "heat_pump_size": float | null,                         # tons per unit (ton-equivalent)
    "heat_pump_installation_year": int | null
  },

  "other_equipment": {
    "clothes_dryers_exists": bool,                          # REQUIRED
    "clothes_dryers_type": str | null,                      # "electric" | "gas"
    "clothes_dryers_energy_density": float | null,          # W/m²
    "clothes_dryers_average_installation_year": int | null,
    "clothes_washers_exists": bool,                         # REQUIRED
    "clothes_washers_energy_density": float | null,         # W/m²
    "clothes_washers_average_installation_year": int | null,
    "elevators_exists": bool,                               # REQUIRED
    "elevators_quantity": int | null,
    "elevators_average_installation_year": int | null,
    "escalator_exists": bool,                               # REQUIRED
    "escalator_quantity": int | null,
    "escalator_floor_area_served": int | null,              # m²
    "escalator_variable_frequency_drive": bool | null,
    "escalator_installation_year": int | null,
    "rooftop_photovoltaics_exists": bool,                   # REQUIRED
    "rooftop_photovoltaics_size": float | null,             # kW DC nameplate
    "rooftop_photovoltaics_average_installation_year": int | null
  },

  "generic_hvac_equipment": [                               # [] if nothing applies
    # Each item: ALL fields required and non-nullable
    {
      "name": str,                    # free text description
      "end_use": str,                 # "outdoor_air_cooling" | "outdoor_air_heating" | "skin_cooling" | "skin_heating"
      "fuel": str,                    # "natural_gas" | "electricity" | "district_heat"
      "size": float,                  # in size_units below
      "size_units": str,              # "cfm" | "mbtu" | "tons"
      "coefficient_of_performance": float,  # 0.85 for gas, 3.5 for heat pump — NEVER null
      "load_ratio": float,            # 0.0–1.0 — NEVER null
      "installation_year": int,       # e.g. 2005 — NEVER null
      "life_span": int                # years, e.g. 25 — NEVER null
    }
  ]
}
```

---

## Enum Values (exact strings — case-sensitive)

### `air_handling_equipment_type`
```
make_up_air_unit | packaged_air_handling_unit | split_air_handling_unit |
suite_air_exchangers | suite_energy_recovery_ventilator | exhaust_only_air_handling_unit
```

### `air_handling_equipment_heating_type` / `rooftop_unit_heating_type` / `terminal_heater` heating
```
electric_resistance | gas | hydronic
```

### `air_handling_equipment_cooling_type` / `rooftop_unit_cooling_type`
```
direct_expansion | hydronic
```

### `central_plant_cooler_type`
```
air_cooled_chiller | water_cooled_chiller
```

### `central_plant_cooler_terminal_units` / `central_plant_heater_terminal_units`
```
baseboards | constant_volume_boxes | fan_coil_units | variable_air_volume_boxes
```

### `central_plant_heater_type`
```
condensing_gas_boiler | electric_furnace | electric_resistance_boiler |
gas_boiler | gas_furnace | high_efficiency_gas_furnace | hydronic_furnace
```

### `central_plant_heat_pump_type`
```
air_source_heat_pump | ground_source_heat_pump
```

### `domestic_hot_water_heater_type`
```
electric_heater | gas_heater | indirect_heater
```

### `terminal_cooler_units`
```
cooling_ptac | split_air_conditioner | window_air_conditioner
```

### `terminal_heater_units`
```
condensing_gas_unit_heater | electric_baseboard | electric_resistance_ptac |
electric_unit_heater | gas_ptac | gas_unit_heater
```

### `heat_pump_type`
```
water_loop_heat_pump | split_air_source_heat_pump
```

### `generic_hvac_equipment.end_use`
```
outdoor_air_cooling | outdoor_air_heating | skin_cooling | skin_heating
```

### `generic_hvac_equipment.size_units`
```
cfm | mbtu | tons
```

---

## Validation Rules (enforced by API — will reject if violated)

These are checked by `CreateEquipmentListFromSurveyRequestValidator`. Getting any of these
wrong returns `{"success": False, "error": "..."}`.

### Rule 1: DHW is mandatory
`domestic_hot_water_heater_exists` **must be `true`** and `domestic_hot_water_heater_type`
must be provided. The API rejects surveys where DHW is marked as non-existent.

### Rule 2: Hydronic AHU cooling requires central cooler
If `air_handling_equipment_cooling_type == "hydronic"`, then
`central_plant_cooler_exists` must be `true`.

### Rule 3: Hydronic AHU heating requires central heater
If `air_handling_equipment_heating_type == "hydronic"`, then
`central_plant_heater_exists` must be `true`.

### Rule 4: Central cooler and terminal cooler are mutually exclusive
Cannot set both `central_plant_cooler_exists = true` AND `terminal_cooler_exists = true`.
**Pick one or neither.**

### Rule 5: Central heater and terminal heater are mutually exclusive
Cannot set both `central_plant_heater_exists = true` AND `terminal_heater_exists = true`.
**Pick one or neither.** (Exception: terminal heater can coexist with distributed heat pumps.)

### Rule 6: Must have at least one air delivery system
Either `air_handling_equipment_exists` OR `rooftop_unit_exists` must be `true`.
A building with neither is rejected.

### Rule 7: Rooftop unit requires cooling type
If `rooftop_unit_exists == true`, then `rooftop_unit_cooling_type` must be provided (not null).
RTUs without cooling are not modelled — use `air_handling_equipment` instead.

### Rule 8: Suite ERV cannot have heating or cooling coils
If `air_handling_equipment_type == "suite_energy_recovery_ventilator"`, both
`air_handling_equipment_heating_type` and `air_handling_equipment_cooling_type` must be `null`.

### Rule 9: Cannot have unit heater if furnace present
If `central_plant_heater_type` is a furnace type (`electric_furnace`, `gas_furnace`,
`high_efficiency_gas_furnace`), then `terminal_heater_units` cannot be a unit heater type.

### Rule 10: Cannot have baseboard if furnace present
If `central_plant_heater_type` is a furnace type, `terminal_heater_units` cannot be
`electric_baseboard`.

### Rule 11: Cannot have central cooling if furnace present
If `central_plant_heater_type` is a furnace type, `central_plant_cooler_exists` must be `false`.
Furnaces distribute air; chillers serve hydronic systems — these don't co-exist.

### Rule 12: Furnace requires specific AHU types only
If `central_plant_heater_type` is a furnace type, `air_handling_equipment_type` must be one of:
`exhaust_only_air_handling_unit`, `suite_energy_recovery_ventilator`, `suite_air_exchangers`,
or `null`.

### Rule 13: Water loop heat pump requires a boiler
If `heat_pump_type == "water_loop_heat_pump"`, `central_plant_heater_type` must be a boiler type
(`gas_boiler`, `condensing_gas_boiler`, `electric_resistance_boiler`).
The boiler is the loop heater — it's required for WLHP systems.

### Rule 14: Water loop heat pump cannot have a separate chiller
If `heat_pump_type == "water_loop_heat_pump"`, `central_plant_cooler_exists` must be `false`.
The heat pumps themselves provide cooling — no separate chiller is used.

### Rule 15: Suite air exchangers require a furnace
If `air_handling_equipment_type == "suite_air_exchangers"`, `central_plant_heater_type` must
be a furnace type. Suite air exchangers are ventilation-only; heating comes from the furnace.

---

## Valid System Combinations (Common Building Types)

Use these as starting templates — they are pre-validated against all 15 rules.

### Multi-unit residential — gas boiler + hydronic baseboards
```python
"air_handling_equipment": { "exists": true, "type": "suite_energy_recovery_ventilator",
    "heating_type": null, "cooling_type": null, ... }
"central_plant_heater": { "exists": true, "type": "gas_boiler",
    "terminal_units": "baseboards", ... }
"central_plant_cooler": { "exists": false, ... }
"terminal_cooler": { "exists": false, ... }
"heat_pump": { "exists": false, ... }
"rooftop_unit": { "exists": false, ... }
```

### Office — packaged RTUs (gas heat + DX cooling)
```python
"air_handling_equipment": { "exists": false, ... }
"rooftop_unit": { "exists": true, "heating_type": "gas",
    "cooling_type": "direct_expansion", ... }
"central_plant_heater": { "exists": false, ... }
"central_plant_cooler": { "exists": false, ... }
"terminal_heater": { "exists": false, ... }
"terminal_cooler": { "exists": false, ... }
"heat_pump": { "exists": false, ... }
```

### Office — central chiller + gas boiler (VAV system)
```python
"air_handling_equipment": { "exists": true, "type": "packaged_air_handling_unit",
    "heating_type": "hydronic", "cooling_type": "hydronic", ... }
"central_plant_heater": { "exists": true, "type": "gas_boiler",
    "terminal_units": "variable_air_volume_boxes", ... }
"central_plant_cooler": { "exists": true, "type": "air_cooled_chiller",
    "terminal_units": "variable_air_volume_boxes", ... }
"terminal_heater": { "exists": false, ... }
"terminal_cooler": { "exists": false, ... }
"heat_pump": { "exists": false, ... }
"rooftop_unit": { "exists": false, ... }
```

### MUR — mini-splits (split ASHP, all-electric)
```python
"air_handling_equipment": { "exists": true, "type": "make_up_air_unit",
    "heating_type": "electric_resistance", "cooling_type": null, ... }
"heat_pump": { "exists": true, "type": "split_air_source_heat_pump",
    "heating_load_ratio": 1.0, "cooling_load_ratio": 1.0, ... }
"central_plant_heater": { "exists": false, ... }
"central_plant_cooler": { "exists": false, ... }
"terminal_heater": { "exists": false, ... }
"terminal_cooler": { "exists": false, ... }
"rooftop_unit": { "exists": false, ... }
```

### MUR — water loop heat pump
```python
"air_handling_equipment": { "exists": true, "type": "suite_energy_recovery_ventilator",
    "heating_type": null, "cooling_type": null, ... }
"heat_pump": { "exists": true, "type": "water_loop_heat_pump", ... }
"central_plant_heater": { "exists": true, "type": "gas_boiler",   # REQUIRED by Rule 13
    "terminal_units": "fan_coil_units", ... }
"central_plant_cooler": { "exists": false, ... }                   # REQUIRED by Rule 14
"terminal_heater": { "exists": false, ... }
"terminal_cooler": { "exists": false, ... }
"rooftop_unit": { "exists": false, ... }
```

### Mixed (gas furnace + suite ERV)
```python
"air_handling_equipment": { "exists": true, "type": "suite_air_exchangers",  # Rule 15 → must have furnace
    "heating_type": null, "cooling_type": null, ... }
"central_plant_heater": { "exists": true, "type": "high_efficiency_gas_furnace",
    "terminal_units": null, ... }
"central_plant_cooler": { "exists": false, ... }                   # Rule 11
"terminal_heater": { "exists": false, ... }                        # Rule 9/10
"terminal_cooler": { "exists": false, ... }
"heat_pump": { "exists": false, ... }
"rooftop_unit": { "exists": false, ... }
```

---

## Error Handling

When the API returns `{"success": False, "error": "..."}`:

| Error contains | Most likely cause | Fix |
|---|---|---|
| "domestic_hot_water" | DHW exists=false | Set exists=true, provide type |
| "mutually exclusive" | Both central + terminal exist | Remove one |
| "requires" | Cross-dependency violation | Check Rules 2–3, 13–15 |
| "furnace" | Furnace + incompatible equipment | Check Rules 9–12 |
| "rooftop_unit" + "cooling" | RTU missing cooling_type | Add cooling_type |
| "air handling" / "rooftop" | Neither air system present | Add one (Rule 6) |
| enum / invalid value | Wrong string value | Check enum lists above |

**Always show the raw error to the user** — it usually names the exact field that failed.

---

## `generic_hvac_equipment` — Null Safety

Unlike all other sections, `generic_hvac_equipment` items **cannot contain null values**.
If you cannot determine a field's value, **omit that item entirely** rather than passing null.

Required non-nullable fields per item:
- `name` — describe as best you can ("Radiant heating panel", "Pool boiler", etc.)
- `end_use` — pick the closest enum value
- `fuel` — `"natural_gas"`, `"electricity"`, or `"district_heat"`
- `size` — estimate in the chosen units; note estimate in confirmation table
- `size_units` — `"cfm"`, `"mbtu"`, or `"tons"`
- `coefficient_of_performance` — use 0.85 for gas combustion, 3.5 for electric heat pump, 1.0 for electric resistance
- `load_ratio` — 1.0 if it's the only system for that end use; lower if shared
- `installation_year` — use decade midpoint if exact year unknown (e.g., 1995 for "mid-1990s")
- `life_span` — 25 years for HVAC is a safe default; use 15 for window units, 30 for chillers

# Audette Input Topology Reference

How equipment survey fields map to the Audette energy model's internal `BuildingState` proto
and which multipliers each equipment type drives. Use this to understand *why* each field
matters and what model parameters change when survey data is submitted.

---

## Overview: How Equipment Survey Drives the Model

When you submit an equipment survey via `submit_equipment_survey`, Audette updates the
`BuildingState` proto. The surrogate energy model (`SurrogateModelRunner`) reads these
fields to predict monthly consumption. The key output fields driven by equipment data are:

| BuildingState field | Proto type | Set by survey section |
|---------------------|------------|----------------------|
| `equipment_heating_fuel` | FuelDataPoint (ELECTRICITY / NATURAL_GAS / STEAM) | central_plant_heater, central_plant_heat_pump, rooftop_unit |
| `heating_multiplier` | FloatDataPoint (scalar, 1.0 = baseline) | central_plant_heater type + age |
| `cooling_multiplier` | FloatDataPoint | central_plant_cooler, heat_pump COP |
| `domestic_hot_water_multiplier` | FloatDataPoint | domestic_hot_water_heater type + age |
| `fans_multiplier` | FloatDataPoint | air_handling_equipment type + VFD presence |
| `pumps_multiplier` | FloatDataPoint | terminal_units type (VAV = lower) |
| `ventilation_rate_multiplier` | FloatDataPoint | air_handling_equipment supply_air_rate vs. floor area |
| `led_installed_ratio` | RatioDataPoint (0–1) | Not in survey schema directly — inferred from building age |
| `equipment_list` | google.protobuf.Struct (JSON) | Full serialized survey payload |

Multipliers use 1.0 as the archetype baseline. **< 1.0 = more efficient than baseline;
> 1.0 = less efficient.** Typical ranges: 0.5 – 2.0.

---

## 1. Primary Heating Fuel (`equipment_heating_fuel`)

This single field drives the entire heating consumption model — wrong fuel type means wrong
emission factors and completely wrong carbon plan.

**Resolution rule (apply in order, first match wins):**

1. `central_plant_heat_pump_exists = true` → **ELECTRICITY**
2. `heat_pump_exists = true` AND `heat_pump_heating_load_ratio = 1.0` → **ELECTRICITY**
3. `central_plant_heater_type ∈ {electric_resistance_boiler, electric_furnace}` → **ELECTRICITY**
4. `central_plant_heater_type = hydronic_furnace` AND district steam connection → **STEAM**
5. `central_plant_heater_type ∈ {gas_boiler, condensing_gas_boiler, gas_furnace, high_efficiency_gas_furnace, hydronic_furnace}` → **NATURAL_GAS**
6. `rooftop_unit_heating_type = gas` → **NATURAL_GAS**
7. `rooftop_unit_heating_type = electric_resistance` → **ELECTRICITY**
8. No heater exists → **ELECTRICITY** (default — flag this to the user)

**Mixed heating (e.g., gas boiler + heat pump supplemental):**
Use the fuel of the system covering the majority of heating load. Flag mixed systems in
the confirmation table and ask the user to confirm primary fuel.

---

## 2. Heating Multiplier (`heating_multiplier`)

Driven primarily by `central_plant_heater_type` and installation year.

| Equipment type | Typical multiplier | Notes |
|---|---|---|
| `condensing_gas_boiler` | 0.80 – 0.90 | AFUE ≥ 90% — model recognises this |
| `high_efficiency_gas_furnace` | 0.80 – 0.88 | AFUE ≥ 90% |
| `gas_boiler` | 0.95 – 1.05 | Standard AFUE 78–85% |
| `gas_furnace` | 0.95 – 1.05 | Standard AFUE ~80% |
| `electric_resistance_boiler` | 1.0 (by definition) | 100% efficient electrically |
| `electric_furnace` | 1.0 | COP = 1.0 |
| `hydronic_furnace` (district) | 0.85 – 1.0 | Depends on district supply temp |
| `air_source_heat_pump` (central) | 0.35 – 0.55 | COP ~2.0 – 3.0 |
| `ground_source_heat_pump` | 0.25 – 0.40 | COP ~3.0 – 4.5 |
| Distributed `split_air_source_heat_pump` | 0.30 – 0.50 | Varies with COP input |

**Age degradation:** Equipment installed > 20 years ago → add 0.05–0.15 to multiplier.
Always record `average_installation_year` — the model applies its own degradation curve.

**For distributed heat pumps (`heat_pump` section):**
The `heat_pump_heating_coefficient_of_performance` field directly sets the model's COP.
If the document shows HSPF (Heating Seasonal Performance Factor), convert:
- COP ≈ HSPF ÷ 3.41

---

## 3. Cooling Multiplier (`cooling_multiplier`)

Driven by `central_plant_cooler_type`, `heat_pump` COP, and `terminal_cooler` type.

| Equipment type | Typical multiplier | Notes |
|---|---|---|
| `water_cooled_chiller` | 0.70 – 0.85 | More efficient than air-cooled |
| `air_cooled_chiller` | 0.85 – 1.0 | Standard commercial |
| `split_air_source_heat_pump` | 0.65 – 0.90 | Driven by COP input |
| `water_loop_heat_pump` | 0.70 – 0.85 | Efficient in mild climates |
| `cooling_ptac` | 1.0 – 1.15 | Less efficient than central |
| `window_air_conditioner` | 1.1 – 1.3 | Least efficient |
| `split_air_conditioner` | 0.90 – 1.05 | Ductless split |
| No cooling | 0 | Set `terminal_cooler_exists = false` |

**For heat pumps:** Use `heat_pump_cooling_coefficient_of_performance` (or SEER/EER ÷ 3.41 for COP).
**`heat_pump_cooling_load_ratio` (0–1):** What fraction of the total cooling load this system
serves. If the building has both heat pumps and a chiller, set this < 1.0.

---

## 4. DHW Multiplier (`domestic_hot_water_multiplier`)

| DHW type | Fuel | Typical multiplier |
|---|---|---|
| `gas_heater` | NATURAL_GAS | 0.90 – 1.05 |
| `electric_heater` | ELECTRICITY | 0.95 – 1.0 |
| `indirect_heater` | Inherits from boiler | 0.80 – 0.95 (leverages boiler efficiency) |
| Heat pump water heater* | ELECTRICITY | 0.35 – 0.45 (COP ~2.5–3.5) |

*Heat pump water heaters map to `electric_heater` type in the schema — note in the
confirmation table that it is HPWH so the user understands this is an approximation.

`central_distribution = true` means a central tank with recirculation loop serving all
suites. `false` means individual point-of-use heaters per suite.

**Sizing:** submit `domestic_hot_water_heater_size` in **tons** like every other capacity — convert
the nameplate/recovery rating (BTU/h ÷ 12,000, kW ÷ 3.517), or when only tank volume is known use the
fallback `tons ≈ gallons ÷ 40` (see skill.md "DHW note"). **NEVER submit litres or gallons in the
size field.** (Tank volume in litres is only an internal input to the loss calculation, not the
submitted size.)

---

## 5. Fans Multiplier (`fans_multiplier`)

Driven primarily by air handling equipment type and whether VFDs are present.

| AHU type | VFD? | Typical multiplier |
|---|---|---|
| `packaged_air_handling_unit` | Yes (VAV) | 0.55 – 0.70 |
| `packaged_air_handling_unit` | No (CV) | 0.90 – 1.05 |
| `split_air_handling_unit` | Yes | 0.55 – 0.70 |
| `split_air_handling_unit` | No | 0.90 – 1.05 |
| `make_up_air_unit` | Yes | 0.50 – 0.65 |
| `make_up_air_unit` | No | 0.85 – 1.0 |
| `suite_air_exchangers` / `suite_energy_recovery_ventilator` | Inherent | 0.80 – 0.95 |
| `exhaust_only_air_handling_unit` | — | 0.60 – 0.80 (simpler system) |

**Supply air rate (`air_handling_equipment_supply_air_rate` in CFM)** drives the
`ventilation_rate_multiplier`. Compare to 0.15 CFM/ft² baseline for most commercial types:
- Higher than baseline → `ventilation_rate_multiplier > 1.0` (over-ventilated)
- Lower → `ventilation_rate_multiplier < 1.0` (under-ventilated or economizer strategy)

**VFD detection in documents:** Look for "variable frequency drive", "VFD", "variable speed
drive", "VSD", "variable air volume", "VAV". If `terminal_units = variable_air_volume_boxes`,
VFDs on AHU fans are almost certain.

---

## 6. Pumps Multiplier (`pumps_multiplier`)

Driven by terminal unit type — VAV systems use variable-speed pumps; constant-volume
systems use fixed-speed pumps.

| Terminal unit type | Typical pumps_multiplier |
|---|---|
| `variable_air_volume_boxes` | 0.55 – 0.75 |
| `fan_coil_units` | 0.80 – 0.95 |
| `constant_volume_boxes` | 0.90 – 1.05 |
| `baseboards` | 0.85 – 1.0 |
| No hydronic distribution | 0 (no pumps) |

---

## 7. Rooftop Equipment Detection → Survey Field Mapping

When satellite imagery is available, Audette uses computer vision to detect equipment.
The `RooftopEquipmentType` detections map to survey sections as follows:

| RooftopEquipmentType | Most likely survey section | Field mapping |
|---|---|---|
| `ROOF_TOP_UNIT` (8) | `rooftop_unit` | heating_type = gas or electric_resistance; cooling_type = direct_expansion |
| `AIR_HANDLING_UNIT` (1) | `air_handling_equipment` | type = packaged or split |
| `MAKE_UP_AIR_UNIT` (4) | `air_handling_equipment` | type = make_up_air_unit |
| `COOLING_TOWER` (2) | `central_plant_cooler` | type = water_cooled_chiller |
| `AIR_COOLED_EQUIPMENT` (0) | `central_plant_cooler` OR `terminal_cooler` | type = air_cooled_chiller (central) or split_air_conditioner (terminal) |
| `CONDENSING_UNIT` (3) | `central_plant_cooler` OR `heat_pump` | Outdoor condenser — check for indoor AHU match |
| `P_NATURAL_GAS` (6) | `rooftop_unit` OR `central_plant_heater` | heating_type = gas; check for integrated cooling |
| `PHOTO_VOLTAIC` (7) | `other_equipment` | rooftop_photovoltaics_exists = true |
| `P_HDR` (5) | `central_plant_heater` OR `rooftop_unit` | High-density packaged equipment |
| `SL` (9) | `generic_hvac_equipment` | Secondary load — unclassified |

**Detection confidence:** Only treat detections with confidence ≥ 0.7 as confirmed.
Lower confidence detections should be flagged in the confirmation table for user verification.

**Count-based inference:**
- Many small `CONDENSING_UNIT` boxes distributed across roof → likely `split_air_source_heat_pump` (one per suite)
- Few large `COOLING_TOWER` structures → likely `water_cooled_chiller` with cooling towers
- Long rows of `AIR_COOLED_EQUIPMENT` → likely `air_cooled_chiller` central plant

---

## 8. DataPoint Status (Data Quality)

After survey submission, all equipment-derived BuildingState fields are marked with
`status = USER_INPUT (4)`, overriding any previously `INFERRED (2)` or `DEFAULT (1)` values.
This means:

- **Before survey:** Model uses statistical defaults for your building archetype
- **After survey:** Model uses your actual equipment data — predictions improve significantly
- **After calibration:** Multipliers are further refined to match utility bills (`CALIBRATED (3)`)

The progression DATABASE → DEFAULT → INFERRED → USER_INPUT → CALIBRATED represents
increasing data fidelity. Always push toward USER_INPUT before calibration.

---

## 9. Common Extraction Pitfalls

**Mixed heating systems** (e.g., gas boiler + supplemental electric):
Set `equipment_heating_fuel` to the primary fuel. Record secondary system in `generic_hvac_equipment`.

**District heating** connecting via heat exchanger:
Maps to `central_plant_heater_type = hydronic_furnace`. Fuel depends on district source —
ask the user or note from the PCNA. If steam district: fuel = STEAM.

**VRF/VRV systems** (variable refrigerant flow):
These are distributed heat pumps. Map to `heat_pump_type = split_air_source_heat_pump`.
One outdoor unit serves multiple zones — the number of indoor units ≈ number of zones.

**PTAC units** (packaged terminal air conditioners):
- If heating AND cooling: `terminal_heater_units = electric_resistance_ptac` (or gas_ptac)
  AND `terminal_cooler_units = cooling_ptac`
- Note both `terminal_heater_size` (**tons** heating) AND `terminal_heater_cooler_size` (**tons** cooling) — convert MBH ÷ 12, kW ÷ 3.517; NEVER submit kW (see skill.md "Unit conversions")

**Heat pump water heaters (HPWH):**
Submit as `domestic_hot_water_heater_type = electric_heater`. Note in confirmation table.

**Fuel oil / propane boilers:**
Audette only supports ELECTRICITY, NATURAL_GAS, STEAM. Map oil/propane to NATURAL_GAS
as the closest equivalent and note the actual fuel in the confirmation table.

**No cooling system:**
Set `central_plant_cooler_exists = false`, `terminal_cooler_exists = false`, `heat_pump_exists = false`.
This is valid — the model handles uncooled buildings.

---

## 10. Post-Survey: What Calibration Needs

After equipment survey submission, `submit_equipment_survey` triggers re-modelling. To then
run calibration (`CalibrateBuildingStateRequest`), the surrogate model needs:

1. The updated `BuildingState` (returned from the equipment survey submission)
2. **Utility data**: Monthly electricity and gas bills with `start_date`, `end_date`,
   `energy_consumption` (kBtu or kWh), `utility_cost` (USD)
3. Minimum 12 months of data per fuel type for seasonal pattern matching

This is why the `audette-energy-data` skill should always run after `audette-equipment-survey` —
together they give the model both the physical system characteristics and the consumption history
needed to produce a calibrated carbon plan.

---

## 11. Field Completeness Impact

| Section | Model impact if missing |
|---|---|
| `central_plant_heater` or primary heating | **Critical** — wrong fuel type = wrong carbon accounting |
| `domestic_hot_water_heater` | High — DHW is 15–30% of gas consumption in residential |
| `air_handling_equipment` | High — fans represent 15–25% of commercial electricity |
| `central_plant_cooler` / `heat_pump` | High — cooling is 10–40% of electricity |
| `rooftop_unit` | Medium — only relevant for buildings with rooftop systems |
| `terminal_heater` / `terminal_cooler` | Medium — terminal equipment affects distribution losses |
| `other_equipment` (elevators, PV) | Low — small load corrections |
| `generic_hvac_equipment` | Low — catch-all, rarely changes model significantly |

When time is limited, prioritise the top 4 sections.

# System Categories Reference

This file provides detailed query templates, terminology mappings, and specification
checklists for each major building system category. Use this when querying document
intelligence to ensure comprehensive coverage.

---

## 1. Heating Systems

### Query Templates

**Primary query:**
```
heating system HVAC boiler furnace heat pump capacity fuel distribution specifications
```

**Refinement queries:**
```
boiler capacity MBH efficiency AFUE installation year
furnace BTU efficiency distribution forced air
heat pump HSPF COP capacity heating mode
district steam heating system connection
radiant floor heating hydronic system
```

### Key Specifications to Extract

- **System type:** Boiler, furnace, heat pump, district steam, electric resistance
- **Fuel source:** Natural gas, fuel oil, electricity, propane, district steam
- **Capacity:** MBH, kW, BTU/hr (note: 1 MBH = 293 W)
- **Efficiency:** AFUE (furnace/boiler), HSPF (heat pump), thermal efficiency %
- **Distribution method:** Forced air, hydronic (baseboards/radiators/fan coils), radiant
- **Installation year**
- **Manufacturer and model** (if available)
- **Number of units** (if multiple boilers/furnaces)
- **Terminal units:** Baseboards, radiators, fan coils, VAV boxes, radiant panels
- **Zoning:** Single zone, multi-zone, individual suite control
- **Controls:** Thermostats, BAS integration, scheduling

### Common Terminology

| Document term | Equipment survey mapping |
|---------------|--------------------------|
| "Atmospheric boiler" | `boiler_atmospheric` |
| "Condensing boiler" | `boiler_condensing` |
| "Hot water boiler" | `boiler_*` (check fuel type) |
| "Steam boiler" | `boiler_steam` |
| "Forced air furnace" | `furnace_*` (check fuel type) |
| "Baseboard heaters" | Terminal unit type: `baseboards` |
| "Cast iron radiators" | Terminal unit type: `radiators` |
| "Fan coil units" | Terminal unit type: `fan_coils` |
| "Air source heat pump" | `heat_pump_air_source` |
| "Ground source heat pump" | `heat_pump_ground_source` |

---

## 2. Cooling Systems

### Query Templates

**Primary query:**
```
cooling system air conditioning chiller DX rooftop unit RTU capacity specifications
```

**Refinement queries:**
```
chiller capacity tons kW efficiency kW/ton
rooftop unit RTU packaged unit capacity SEER
split system mini-split ductless heat pump cooling
direct expansion DX cooling coil
cooling tower condenser water
```

### Key Specifications to Extract

- **System type:** Central chiller, rooftop units, split systems, window AC, heat pumps
- **Capacity:** Tons, kW (note: 1 ton = 3.517 kW)
- **Efficiency:** SEER, EER, kW/ton (chillers)
- **Distribution:** Chilled water, DX refrigerant, ductless
- **Installation year**
- **Number of units**
- **Cooling tower:** If present, type (open/closed circuit), capacity
- **Refrigerant type:** R-410A, R-32, R-134a, etc.
- **Controls:** Thermostats, staging, variable speed
- **Zoning:** Central vs. suite-level control

### Common Terminology

| Document term | Equipment survey mapping |
|---------------|--------------------------|
| "Centrifugal chiller" | `chiller_centrifugal` |
| "Screw chiller" | `chiller_screw` |
| "Absorption chiller" | `chiller_absorption` |
| "Packaged rooftop unit" | `rooftop_unit` |
| "Split system" | `split_system` |
| "VRF/VRV system" | `heat_pump_vrf` (variable refrigerant flow) |
| "DX cooling" | Direct expansion (refrigerant-based) |
| "Chilled water" | Central chiller with water distribution |

---

## 3. Domestic Hot Water (DHW)

### Query Templates

**Primary query:**
```
domestic hot water DHW water heater storage tank capacity fuel specifications
```

**Refinement queries:**
```
water heater capacity gallons recovery rate efficiency
storage tank DHW circulation loop
tankless instantaneous water heater
solar thermal DHW preheat
```

### Key Specifications to Extract

- **Configuration:** Central distribution vs. suite-level heaters
- **Fuel type:** Natural gas, electricity, fuel oil, solar thermal
- **Storage capacity:** Gallons or litres (1 gallon = 3.785 L)
- **Recovery rate:** Gallons per hour at temperature rise
- **Efficiency:** Energy factor (EF), thermal efficiency %
- **Installation year**
- **Number of units**
- **Circulation:** Recirculation pump presence
- **Temperature:** Set point temperature
- **Solar preheat:** If integrated with solar thermal

### Common Terminology

| Document term | Equipment survey mapping |
|---------------|--------------------------|
| "Storage water heater" | Central or suite-level DHW |
| "Tankless water heater" | `instantaneous` or `tankless` |
| "Indirect water heater" | Uses boiler for heat source |
| "Solar thermal" | `solar_thermal_dhw` |
| "Electric resistance" | `electric_resistance_dhw` |
| "Heat pump water heater" | `heat_pump_dhw` |

---

## 4. Ventilation

### Query Templates

**Primary query:**
```
ventilation air handling AHU makeup air supply exhaust ERV HRV specifications
```

**Refinement queries:**
```
air handling unit AHU capacity CFM air changes per hour
energy recovery ventilator ERV heat recovery HRV
makeup air unit MAU outside air
demand controlled ventilation DCV CO2 sensor
exhaust fan bathroom kitchen
```

### Key Specifications to Extract

- **AHU type:** Constant air volume (CAV), variable air volume (VAV), DOAS
- **Capacity:** CFM (cubic feet per minute) or L/s
- **Number of units**
- **Supply/exhaust balance**
- **Heat recovery:** ERV (energy recovery), HRV (heat recovery) effectiveness %
- **Filters:** MERV rating, filter type
- **Controls:** Demand-controlled ventilation, CO2 sensors, scheduling
- **Economizer:** Air-side or water-side economizer presence
- **Installation year**

### Common Terminology

| Document term | Equipment survey mapping |
|---------------|--------------------------|
| "AHU" / "Air handler" | `air_handling_unit` |
| "RTU with economizer" | `rooftop_unit` with economizer flag |
| "ERV" | Energy recovery ventilator |
| "HRV" | Heat recovery ventilator |
| "DOAS" | Dedicated outdoor air system |
| "MAU" | Makeup air unit |
| "Exhaust only" | No supply ventilation |

---

## 5. Building Controls & Automation

### Query Templates

**Primary query:**
```
building automation system BAS building management BMS controls DDC thermostats
```

**Refinement queries:**
```
BAS vendor controls platform Tridium Niagara Johnson Controls Honeywell
direct digital controls DDC pneumatic controls
zone controls VAV box controls
thermostat programmable smart WiFi
lighting controls occupancy sensors daylight harvesting
```

### Key Specifications to Extract

- **BAS/BMS presence:** Yes/no, vendor, platform
- **HVAC controls:** DDC, pneumatic, manual, smart thermostats
- **Lighting controls:** Occupancy sensors, daylight dimming, time clocks, networked
- **Integration level:** Which systems are integrated into BAS
- **User interface:** Web-based, proprietary software, mobile app
- **Monitoring:** Remote monitoring, alarms, trending
- **Installation/upgrade year**

### Common Terminology

| Document term | Meaning |
|---------------|---------|
| "DDC controls" | Direct digital controls (digital communication) |
| "Pneumatic controls" | Older air-pressure-based controls |
| "BACnet" | Building automation communication protocol |
| "LON" / "LonWorks" | Legacy building automation protocol |
| "Smart thermostat" | WiFi-connected, programmable thermostat |
| "Occupancy sensor" | Motion detector for lighting or HVAC |
| "Daylight harvesting" | Automatic dimming based on natural light |

---

## 6. Lighting

### Query Templates

**Primary query:**
```
lighting fixtures LED fluorescent incandescent lamps controls occupancy sensors
```

**Refinement queries:**
```
LED lighting retrofit lumens wattage color temperature
occupancy sensors motion detectors lighting controls
daylight harvesting photocell dimming
emergency lighting exit signs
```

### Key Specifications to Extract

- **Technology:** LED, fluorescent (T8, T5, CFL), incandescent, HID (metal halide, HPS)
- **Coverage:** Common areas, tenant spaces, exterior
- **Controls:** Manual switches, occupancy sensors, daylight dimming, time clocks, BAS
- **Recent upgrades:** LED retrofit projects, control upgrades
- **Emergency lighting:** Battery backup, generator-backed
- **Exterior lighting:** Parking, façade, security
- **Power density:** Watts per square foot (if available)

### Common Terminology

| Document term | Meaning |
|---------------|---------|
| "T8 fluorescent" | 1-inch diameter fluorescent tube (common) |
| "T5 fluorescent" | 5/8-inch diameter tube (high-efficiency) |
| "LED retrofit" | Replacing older technology with LEDs |
| "High bay" | High-ceiling warehouse/industrial lighting |
| "Troffer" | Recessed ceiling fluorescent fixture |
| "Occupancy sensor" | Motion detector that turns lights on/off |
| "Photocell" | Light sensor for daylight dimming |

---

## 7. Elevators

### Query Templates

**Primary query:**
```
elevator lift number of elevators hydraulic traction passenger freight
```

**Refinement queries:**
```
elevator modernization upgrade year
hydraulic elevator traction elevator gearless
regenerative elevator energy recovery
elevator capacity speed stops
```

### Key Specifications to Extract

- **Count:** Number of passenger elevators, freight elevators
- **Type:** Hydraulic, traction (geared or gearless)
- **Capacity:** Pounds or kg, number of passengers
- **Speed:** Feet per minute or meters per second
- **Stops:** Number of floors served
- **Installation year**
- **Modernization:** Recent upgrades, control systems
- **Regenerative capability:** Can feed power back during descent
- **ADA compliance:** Accessibility features

### Common Terminology

| Document term | Meaning |
|---------------|---------|
| "Hydraulic elevator" | Uses hydraulic cylinder (low-rise buildings) |
| "Traction elevator" | Uses cables and counterweights (high-rise) |
| "Gearless traction" | More efficient, higher-speed traction |
| "Machine room" | Equipment room above/beside elevator shaft |
| "Machine-room-less" (MRL) | Compact modern design |
| "Regenerative drive" | Captures energy during descent |

---

## 8. Renewable Energy

### Query Templates

**Primary query:**
```
solar photovoltaic PV solar panels renewable energy capacity kW
```

**Refinement queries:**
```
solar PV system size kW production kWh
rooftop solar carport solar ground mount
inverter string inverter microinverter
solar thermal DHW space heating
battery storage energy storage system ESS
```

### Key Specifications to Extract

- **Solar PV capacity:** kW DC, kW AC
- **Installation location:** Rooftop, carport, ground-mount, façade
- **Panel count and type:** Monocrystalline, polycrystalline, thin-film
- **Inverter type:** String, microinverter, central
- **Installation year**
- **Annual production:** kWh/year (if available)
- **Solar thermal:** If present, capacity, DHW or space heating integration
- **Battery storage:** kW power, kWh capacity
- **Other renewables:** Geothermal, wind

### Common Terminology

| Document term | Meaning |
|---------------|---------|
| "kWp" / "kW DC" | Peak DC capacity of PV array |
| "kW AC" | AC capacity after inverter |
| "String inverter" | One inverter for multiple panels in series |
| "Microinverter" | Individual inverter per panel |
| "Net metering" | Utility credit for excess generation |
| "Solar thermal" | Hot water from solar collectors (not PV) |
| "ESS" / "BESS" | Energy storage system / battery ESS |

---

## 9. Building Envelope

### Query Templates

**Primary query:**
```
windows glazing U-value insulation R-value roof wall assembly thermal performance
```

**Refinement queries:**
```
window replacement double pane triple pane low-e coating
wall insulation R-value cavity insulation rigid insulation
roof insulation membrane white roof cool roof
air sealing blower door test infiltration ACH50
```

### Key Specifications to Extract

- **Windows:** Glazing type (single, double, triple), U-value, SHGC, age
- **Wall insulation:** R-value, type (fiberglass, spray foam, rigid), location (cavity, exterior)
- **Roof insulation:** R-value, type, membrane type
- **Air sealing:** Blower door test results (ACH50), infiltration rate
- **Recent upgrades:** Window replacement, insulation retrofit, air sealing
- **Thermal bridging:** Noted issues with continuous insulation
- **Roof type:** Flat, pitched, material (EPDM, TPO, asphalt shingle, metal)

### Common Terminology

| Document term | Meaning |
|---------------|---------|
| "U-value" | Heat transfer coefficient (lower = better insulation) |
| "R-value" | Thermal resistance (higher = better insulation) |
| "SHGC" | Solar heat gain coefficient (lower = less solar heat) |
| "Low-e coating" | Low-emissivity coating on glass (improves U-value) |
| "Double-pane" / "IGU" | Insulated glass unit (two panes) |
| "Triple-pane" | Three panes of glass (higher R-value) |
| "ACH50" | Air changes per hour at 50 Pa pressure (blower door test) |
| "Continuous insulation" | Insulation layer without thermal bridging |

---

## 10. Plumbing & Water Systems

### Query Templates

**Primary query:**
```
plumbing water fixtures low-flow toilets faucets water consumption
```

**Refinement queries:**
```
low-flow fixtures WaterSense water conservation
greywater system rainwater harvesting
irrigation landscape water use
water meter submetering tenant billing
```

### Key Specifications to Extract

- **Fixture types:** Toilets (GPF), faucets (GPM), showerheads (GPM)
- **Low-flow upgrades:** WaterSense certified fixtures
- **Water reuse:** Greywater systems, rainwater harvesting
- **Irrigation:** Landscape water use, drip vs. spray, smart controllers
- **Submetering:** Tenant-level water metering
- **Leak detection:** Monitoring systems
- **Hot water recirculation:** Presence and controls

### Common Terminology

| Document term | Meaning |
|---------------|---------|
| "GPF" | Gallons per flush (toilets, urinals) |
| "GPM" | Gallons per minute (faucets, showers) |
| "WaterSense" | EPA certification for water efficiency |
| "Dual-flush toilet" | Two flush options (1.1 GPF / 1.6 GPF typical) |
| "Low-flow showerhead" | 2.0 GPM or less |
| "Greywater" | Wastewater from sinks/showers reused for irrigation |
| "Rainwater harvesting" | Collecting roof runoff for non-potable use |

---

## Query Best Practices

### Multi-Stage Querying

For comprehensive coverage, use a staged approach:

1. **Broad query first:** Capture general system descriptions
2. **Refinement queries:** Target specific specifications or subsystems
3. **Gap-filling queries:** If initial queries miss key data, try alternative terminology

### Relevance Score Interpretation

| Score Range | Interpretation |
|-------------|----------------|
| **0.8 - 1.0** | Highly relevant, likely direct answer |
| **0.6 - 0.8** | Relevant, may contain answer with context |
| **0.4 - 0.6** | Tangentially relevant, verify carefully |
| **< 0.4** | Likely not relevant, use with caution |

### Handling Ambiguity

When documents use ambiguous terminology:
- Cross-reference with equipment survey data
- Look for capacity/size clues (e.g., "100-ton chiller" → central cooling)
- Note the ambiguity in the report and flag for user verification

### Missing Data Strategy

If queries return no relevant results:
1. Try alternative terminology (consult terminology tables above)
2. Broaden the query (e.g., "HVAC" instead of "air handling unit")
3. Check if documents have been ingested (use `list_documents`)
4. Note the gap in the final report and suggest document collection

---

## Cross-Referencing Checklist

When synthesizing data from multiple sources, verify:

- [ ] Equipment survey values match document descriptions (or note conflicts)
- [ ] Topology graph aligns with equipment survey configuration
- [ ] Capacities are in consistent units (convert MBH ↔ kW, tons ↔ kW, gal ↔ L)
- [ ] Installation years are plausible given building age
- [ ] System counts match (e.g., survey says 2 boilers, documents describe 2 boilers)
- [ ] Fuel types are consistent across sources
- [ ] Efficiency ratings are appropriate for equipment type and age

---

## Reporting Data Gaps

When presenting the final report, be transparent about data quality:

**Good examples:**
- "Chiller capacity not documented in available sources. Recommend site survey."
- "Equipment survey indicates 3 rooftop units; PCNA describes 2 units. Discrepancy
  requires verification."
- "Lighting controls described as 'occupancy sensors throughout' but specific coverage
  areas not documented."

**Avoid:**
- "Chiller capacity is approximately X tons" (when no data exists — don't guess)
- Omitting gaps silently
- Choosing one conflicting source without noting the conflict

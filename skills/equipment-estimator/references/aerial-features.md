# Aerial Equipment Feature Recognition

Visual markers for identifying building equipment from satellite imagery.

## Equipment Types and Visual Signatures

### Rooftop Units (RTUs)

**Visual signature:**
- Rectangular boxes, typically 6-12 ft long, 4-6 ft wide
- Silver, gray, or white color
- Often arranged in rows or grid pattern
- Shadow indicates height above roof (~3-5 ft tall)
- Typically 2-8 units for small/medium buildings

**What it tells us:**
- Cooling type: rooftop_units
- Heating type: likely rooftop_units (most RTUs have heating coils)
- Cooling count: count visible units
- Building likely <100K sqft (larger buildings use chillers)

**Common locations:**
- Center of flat roof
- Along roof edges
- Near HVAC zones (corners, perimeter)

### Cooling Towers

**Visual signature:**
- Circular or square footprint, 10-30 ft diameter
- White, beige, or light gray
- Fan housing visible from above (circular opening)
- Often paired with large rectangular chillers nearby
- Single unit or 2-4 units for redundancy

**What it tells us:**
- Cooling type: chiller (cooling towers reject heat from chillers)
- Central plant: true
- Building likely >50K sqft
- Commercial/office building likely

**Common locations:**
- Rooftop, often near mechanical penthouse
- Ground level (less common, but check building perimeter)

### Chillers

**Visual signature:**
- Large rectangular units, 15-25 ft long
- Dark gray or metallic
- Usually adjacent to cooling towers
- Piping visible between chiller and cooling tower
- 1-4 units typical

**What it tells us:**
- Cooling type: chiller
- Central plant: true
- Large building (>50K sqft)

**Common locations:**
- Rooftop mechanical area
- Basement/ground floor (not visible from aerial)

### Solar Panels (PV)

**Visual signature:**
- Dark blue or black grid pattern
- Uniform spacing and alignment
- Covers 10-100% of roof area
- Rectangular panels, typically 3x5 ft each
- Matte finish, no glare

**What it tells us:**
- pv_system_exists: true
- Estimate size_kw: coverage_% × roof_area_sqft × 0.015 kW/sqft

**Common locations:**
- South-facing roof sections (Northern Hemisphere)
- Flat roofs: entire surface
- Pitched roofs: south slope

### Penthouse/Mechanical Room

**Visual signature:**
- Raised structure in center or side of roof
- 20-50% of roof area
- Rectangular, 10-30 ft tall
- Often has louvers or vents on sides
- May have exhaust stacks

**What it tells us:**
- Central plant: likely (boiler/chiller inside)
- Large building
- Commercial/office building likely

**Common locations:**
- Center of roof
- One end of building

### PTAC Units (Facade)

**Visual signature:**
- Grid pattern on building facade (not roof)
- Rectangular boxes, 2-4 ft wide
- Regular spacing (one per room/unit)
- Often on multifamily or hotel buildings
- Visible on satellite imagery as texture on wall

**What it tells us:**
- Suite-level cooling: true
- Suite-level heating: likely
- Multifamily or hotel building
- Each unit serves one room/apartment

**Common locations:**
- Exterior walls, below windows
- Regular grid pattern (one per unit)

### Exhaust Vents

**Visual signature:**
- Small circular or square caps
- 1-3 ft diameter
- Multiple across roof (10-50+)
- Kitchen/bathroom exhaust
- Less prominent than RTUs

**What it tells us:**
- Ventilation exists
- Multifamily or office building
- May indicate suite-level HVAC

**Common locations:**
- Distributed across roof
- Clustered near kitchens (multifamily)

## Analysis Workflow

1. **Capture screenshot** at zoom level 19-20 (rooftop-level detail)
2. **Identify large equipment first**:
   - Look for RTUs (rectangular boxes in rows)
   - Look for cooling towers (circular, white)
   - Look for penthouse (raised structure)
3. **Count RTUs** if visible (this is the most actionable signal)
4. **Check for solar panels** (dark grid pattern)
5. **Examine building facade** for PTAC grid pattern
6. **Note equipment locations** for evidence table

## Confidence Assessment

**High confidence** (clearly visible):
- RTUs in full view, can count units
- Cooling tower clearly visible with fan housing
- Solar panels cover >20% of roof

**Medium confidence** (partially visible):
- RTUs partially obscured by shadows/trees
- Equipment present but count unclear
- Image resolution marginal

**Low confidence** (unclear):
- Roof heavily shadowed
- Trees obscure large portions of roof
- Image resolution too low
- Building >20 floors (rooftop too far)

## Common Failure Modes

1. **Trees/vegetation obscuring roof** → skip aerial analysis
2. **Construction/scaffolding present** → flag as unreliable
3. **Flat roof with no visible equipment** → may have basement/ground floor mechanical
4. **Very tall buildings** (>20 floors) → aerial view too distant, reduce confidence
5. **Image taken in winter** → snow may obscure equipment

## Equipment Sizing from Aerial

**RTU count → Cooling capacity estimate:**
```
Small building (<25K sqft): 3-4 RTUs → ~10 tons each → 30-40 tons total
Medium building (25-100K sqft): 5-8 RTUs → ~15 tons each → 75-120 tons total

Convert tons to kW: tons × 3.517 = kW
```

**Solar panel coverage → System size estimate:**
```
Panel density: ~15W per sqft of roof area
Coverage: estimate % of roof covered by panels

size_kw = roof_area_sqft × coverage_% × 0.015 kW/sqft

Example:
- 10,000 sqft roof
- 50% coverage
- 10,000 × 0.5 × 0.015 = 75 kW system
```

# Climate Zone Mapping

Maps US state/province codes to simplified climate zones for archetype clustering.

## Climate Zones

### Cold
- NY, MA, VT, NH, ME (Northeast)
- WI, MN, ND, SD (Upper Midwest)
- MT, WY, ID (Mountain North)

### Mild
- CA (coastal), WA, OR (Pacific Northwest)
- Northern CA (San Francisco Bay Area)

### Hot-Dry
- AZ, NM (Southwest desert)
- NV (Nevada)
- CA (inland valleys - Sacramento, Central Valley)
- TX (West Texas)

### Hot-Humid
- FL, LA, MS, AL, GA, SC (Deep South)
- TX (East Texas, Gulf Coast)
- AR (Arkansas)

### Mixed-Humid
- IL, IN, OH, PA, MI (Midwest/Mid-Atlantic)
- VA, NC, TN, KY, WV, MD, DE, NJ (Mid-Atlantic/Upper South)
- MO, KS (Central Plains)

## Default Mapping

```python
def get_climate_zone(state_province):
    """Map state/province to climate zone."""
    cold = ['NY', 'MA', 'VT', 'NH', 'ME', 'WI', 'MN', 'ND', 'SD', 'MT', 'WY', 'ID']
    mild = ['WA', 'OR']
    hot_dry = ['AZ', 'NM', 'NV']
    hot_humid = ['FL', 'LA', 'MS', 'AL', 'GA', 'SC', 'AR']
    mixed = ['IL', 'IN', 'OH', 'PA', 'MI', 'VA', 'NC', 'TN', 'KY', 'WV', 'MD', 'DE', 'NJ', 'MO', 'KS']
    
    # California special case: default to mild (coastal)
    # Texas special case: default to hot_humid (Gulf Coast)
    if state_province == 'CA':
        return 'mild'
    elif state_province == 'TX':
        return 'hot_humid'
    elif state_province in cold:
        return 'cold'
    elif state_province in mild:
        return 'mild'
    elif state_province in hot_dry:
        return 'hot_dry'
    elif state_province in hot_humid:
        return 'hot_humid'
    elif state_province in mixed:
        return 'mixed'
    else:
        return 'mixed'  # Default for unknown states
```

## Climate-Specific Equipment Patterns

**Cold climates:**
- Gas heating dominant (where available)
- Larger heating capacity
- DHW often centralized
- Snow/ice considerations for rooftop equipment

**Mild climates:**
- Heat pumps common
- Minimal heating capacity
- Economizers common
- Solar PV viable year-round

**Hot-Dry climates:**
- Large cooling capacity
- Evaporative cooling possible
- Solar PV very common
- Minimal heating needs

**Hot-Humid climates:**
- Large cooling capacity
- Dehumidification critical
- Chillers for large buildings
- Minimal heating needs

**Mixed climates:**
- Balanced heating/cooling
- Four-season equipment
- Variable systems common

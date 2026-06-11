# Archetype Clustering Rules

## Clustering Dimensions

Buildings are clustered by 4 dimensions to create equipment archetypes:

1. **Building Archetype** (from Audette)
   - office
   - multifamily
   - retail
   - warehouse
   - mixed_use
   - etc.

2. **Size Bin** (gross floor area in sqft)
   - tiny: <5,000
   - small: 5,000-25,000
   - medium: 25,000-100,000
   - large: 100,000-500,000
   - xlarge: ≥500,000

3. **Age Decade** (year built)
   - 1900s, 1910s, 1920s, ..., 2020s
   - Derived from year_built: `(year // 10) * 10`

4. **Climate Zone** (see climate-zones.md)
   - cold
   - mild
   - hot_dry
   - hot_humid
   - mixed

## Cluster Matching Logic

**For target building to estimate:**

1. Extract dimensions from building record
2. Find exact match: `archetype_size_age_climate`
3. If no exact match, try relaxing one dimension:
   - Try adjacent age decades (±10 years)
   - Try adjacent size bins
   - Try same archetype + climate, any age/size
4. If still no match, use archetype-only baseline
5. If no archetype match, use AI-generated presumptive archetype

## Minimum Cluster Size

- Clusters with ≥3 buildings: Use median equipment config
- Clusters with 1-2 buildings: Merge with broader cluster or flag as low confidence
- No clusters for combination: Generate AI-based presumptive archetype

## Median Equipment Calculation

For each cluster with ≥3 buildings:

**Categorical fields** (heating_type, cooling_type, dhw_fuel):
- Use mode (most common value)
- If tie, prefer more efficient option (heat_pump > gas_boiler > electric_resistance)

**Numeric fields** (size_kw, tank_size_litres, install_year):
- Use median
- Exclude outliers (>2 std dev from mean)

**Boolean fields** (pv_exists, elevator_exists):
- Use mode
- If ≥50% have it → exists = true

**Count fields** (cooling_count, rtus_count):
- Use median, round to nearest integer
- Minimum 1 if exists = true

## Confidence Scoring

```
confidence = min(cluster_size / 10, 1.0)

Examples:
- 3 buildings → 0.3
- 10 buildings → 1.0
- 25 buildings → 1.0
```

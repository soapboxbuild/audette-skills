---
name: osm-gfa-calculator
description: >
  Calculates Gross Floor Area (GFA) for a property using OpenStreetMap building
  footprints via Overpass API and floor counts. Use this skill when creating a building
  at a multi-building site and GFA is unknown, incomplete, or needs validation. Triggers
  on: "calculate GFA from footprints", "estimate floor area from OSM", "how big are the
  buildings", or when the audette-create-building skill needs GFA for a multi-building
  property.
---

# OSM GFA Calculator

Calculate Gross Floor Area (GFA) by querying OpenStreetMap building footprints via the public Overpass API, then multiplying footprint areas by floor counts.

**No MCP dependencies** - Uses public Overpass API and Nominatim API directly via HTTP.

## Inputs

| Input | Required | Source |
|-------|----------|--------|
| Property address(es) | Yes | Documents or user |
| Floor count per building | No | Documents, user, or OSM fallback |
| Reported total GFA | No | PCA or other documentation |
| Property type | No | Helps filter OSM results |

---

## Workflow

### Step 1: Geocode the Address

Use **Nominatim API** (OpenStreetMap's geocoding service) to get coordinates:

```bash
curl "https://nominatim.openstreetmap.org/search?format=json&q=${address}" \
  -H "User-Agent: audette-skills/1.0 (https://github.com/soapboxbuild/audette-skills)"
```

**Example:**
```bash
curl "https://nominatim.openstreetmap.org/search?format=json&q=350+5th+Avenue+New+York+NY" \
  -H "User-Agent: Audette-Orchestrator/1.0"
```

**Response:**
```json
[
  {
    "lat": "40.748817",
    "lon": "-73.985428",
    "display_name": "Empire State Building, 350, 5th Avenue, ...",
    "type": "building",
    "importance": 0.9
  }
]
```

**Take the first result** with `type: "building"` or highest `importance` score.

**If property has multiple addresses:**
- Geocode each separately
- You'll query OSM near each location in Step 2

**Rate limit:** 1 request per second. Add 1-second delay between geocoding calls.

**Error handling:**
- If Nominatim fails, ask user for coordinates directly
- If no results, try broader query (e.g., just street address without building name)

---

### Step 2: Query OSM Building Footprints

Use **Overpass API** to get building footprints near the coordinates:

**Endpoint:** `https://overpass-api.de/api/interpreter`

**Query format (Overpass QL):**
```
[out:json];
(
  way["building"](around:100,{lat},{lon});
  relation["building"](around:100,{lat},{lon});
);
out geom;
```

**Example request:**
```bash
curl -X POST https://overpass-api.de/api/interpreter \
  -H "User-Agent: Audette-Orchestrator/1.0" \
  --data '[out:json];way["building"](around:100,40.748817,-73.985428);out geom;'
```

**Radius strategy:**
1. Start with **100m** radius
2. If zero results, retry at **150m**
3. If still zero, retry at **200m**
4. **Never exceed 300m** (pulls in too many unrelated buildings)

**Response format:**
```json
{
  "elements": [
    {
      "type": "way",
      "id": 123456,
      "tags": {
        "building": "commercial",
        "building:levels": "10",
        "height": "35",
        "addr:street": "5th Avenue",
        "addr:housenumber": "350"
      },
      "geometry": [
        {"lat": 40.7489, "lon": -73.9680},
        {"lat": 40.7490, "lon": -73.9679},
        {"lat": 40.7491, "lon": -73.9678},
        ...
      ]
    }
  ]
}
```

**If multiple addresses:** Run separate queries and merge results (deduplicate by OSM way ID).

**Rate limit:** Fair use ~10 requests/second. No authentication needed.

**Error handling:**
- If Overpass API fails, try backup endpoint: `https://overpass.kumi.systems/api/interpreter`
- If both fail, ask user to provide building footprint dimensions manually

---

### Step 3: Filter Buildings

Not all buildings returned belong to the subject property. Apply filters:

**By OSM `building` tag:**
- **Keep:** `apartments`, `residential`, `commercial`, `retail`, `office`, `yes`
- **Exclude:** `house`, `garage`, `shed`, `church`, `school` (unless they match property type)

**By address matching:**
- If OSM building has `addr:housenumber` and `addr:street` tags, compare to property address
- Exact matches are very likely correct buildings

**By distance from geocoded point:**
- Prefer buildings closest to the address coordinates
- Buildings >100m away are less likely to belong to the property

**By sequential OSM IDs:**
- Buildings mapped together often have sequential way IDs (e.g., 685700222, 685700223)
- Sequential IDs suggest they're part of the same complex

**By cross-reference with documents:**
- If PCA/CNA lists specific building addresses or counts, use that to validate

**When in doubt:** Include the building and flag for user confirmation.

---

### Step 4: Calculate Footprint Area

Use the **Shoelace formula** on polygon coordinates.

**Algorithm:**
```python
import math

def calculate_polygon_area_sqft(coords, center_lat):
    """
    coords: list of {"lat": float, "lon": float} dicts
    center_lat: latitude in degrees (for projection)
    Returns: area in square feet
    """
    # Convert lat/lon degrees to meters
    rad = math.radians(center_lat)
    m_per_deg_lat = 111320
    m_per_deg_lon = 111320 * math.cos(rad)
    
    # Project coordinates to meters
    points = []
    for coord in coords:
        x = coord['lon'] * m_per_deg_lon
        y = coord['lat'] * m_per_deg_lat
        points.append((x, y))
    
    # Shoelace formula
    area = 0.0
    n = len(points)
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    
    area_sq_m = abs(area) / 2.0
    
    # Convert to square feet
    area_sq_ft = area_sq_m * 10.7639
    
    return area_sq_ft
```

**Save this as a Python script:**

Create `skills/osm-gfa-calculator/scripts/calculate_area.py`:
```python
#!/usr/bin/env python3
import sys
import json
import math

def calculate_polygon_area_sqft(coords, center_lat):
    rad = math.radians(center_lat)
    m_per_deg_lat = 111320
    m_per_deg_lon = 111320 * math.cos(rad)
    
    points = [(c['lon'] * m_per_deg_lon, c['lat'] * m_per_deg_lat) for c in coords]
    
    area = 0.0
    n = len(points)
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    
    area_sq_m = abs(area) / 2.0
    return area_sq_m * 10.7639

if __name__ == "__main__":
    data = json.loads(sys.argv[1])
    coords = data['coords']
    center_lat = data['center_lat']
    
    area = calculate_polygon_area_sqft(coords, center_lat)
    print(f"{area:.1f}")
```

**Usage:**
```bash
python3 skills/osm-gfa-calculator/scripts/calculate_area.py \
  '{"coords": [{"lat": 40.7489, "lon": -73.9680}, ...], "center_lat": 40.7489}'
```

---

### Step 5: Determine Floor Count

Priority order (most reliable first):

1. **Property documents** (PCA, CNA, offering memo) - always prefer this
2. **User input** - ask if documents unavailable
3. **OSM `building:levels` tag** - least reliable (often wrong or missing)

**If sources disagree:**
```
Building A footprint: 8,000 sq ft
- PCA says 4 floors → GFA = 32,000 sq ft
- OSM says 2 floors → GFA = 16,000 sq ft

Which floor count should I use? (PCA is typically more reliable)
```

Present both calculations and ask user to choose.

**If no floor count available:**
- For single-story buildings (e.g., retail, warehouse): assume 1 floor
- For multi-story: ask user for estimate or site visit data

---

### Step 6: Calculate GFA and Present Results

**GFA Formula:**
```
GFA = Footprint Area × Floor Count
```

**For multi-building properties:**
```
Total GFA = sum(Building[i].footprint × Building[i].floors)
```

**Present results in a table:**

| Building | Address | Footprint (sq ft) | Floors | GFA (sq ft) | OSM ID | Source |
|----------|---------|-------------------|--------|-------------|--------|--------|
| Building A | 350 5th Ave | 8,000 | 4 | 32,000 | 123456 | PCA |
| Building B | 352 5th Ave | 6,500 | 4 | 26,000 | 123457 | PCA |
| **Total** | | **14,500** | | **58,000** | | |

**Validation:**
- If documents report a total GFA, compare to calculated total
- Flag discrepancies >10%:
  ```
  Calculated GFA: 58,000 sq ft
  Reported GFA (PCA): 62,000 sq ft
  Difference: 4,000 sq ft (6.5%)
  
  This is within normal variance. Proceed with calculated GFA or use reported GFA?
  ```

---

## Example: Complete Workflow

**User:** "Calculate GFA for 600 W Virginia St, Seattle WA"

**Step 1: Geocode**
```bash
curl "https://nominatim.openstreetmap.org/search?format=json&q=600+W+Virginia+St+Seattle+WA" \
  -H "User-Agent: Audette-Orchestrator/1.0"
```
Result: `{"lat": "47.5691", "lon": "-122.3471"}`

**Step 2: Query OSM**
```bash
curl -X POST https://overpass-api.de/api/interpreter \
  --data '[out:json];way["building"](around:100,47.5691,-122.3471);out geom;'
```
Result: 3 buildings found

**Step 3: Filter**
- Building 1: `building=apartments`, `addr:housenumber=600` ✓ Match
- Building 2: `building=apartments`, `addr:housenumber=610` ✓ Nearby, likely same property
- Building 3: `building=house`, 150m away ✗ Exclude (single-family, too far)

**Step 4: Calculate areas**
- Building 1: 12,450 sq ft footprint
- Building 2: 10,800 sq ft footprint

**Step 5: Get floor counts**
- PCA lists "two 4-story buildings"
- Building 1 OSM: `building:levels=4` ✓ Matches
- Building 2 OSM: `building:levels=3` ✗ Discrepancy

Ask user: "PCA says 4 floors for both. OSM shows Building 2 as 3 floors. Use PCA (4) or OSM (3)?"

User confirms: Use PCA (4 floors for both)

**Step 6: Calculate GFA**
```
Building 1: 12,450 × 4 = 49,800 sq ft
Building 2: 10,800 × 4 = 43,200 sq ft
Total: 93,000 sq ft
```

**Validation:** PCA reports 95,000 sq ft total. Difference: 2,000 sq ft (2.1%) - within normal variance.

**Present result:**
```
Calculated GFA: 93,000 sq ft (from OSM footprints)
Reported GFA: 95,000 sq ft (from PCA)
Difference: 2.1%

Recommendation: Use 95,000 sq ft (PCA value) for building creation.
```

---

## Error Handling

### Geocoding Fails
```
Unable to geocode address "[address]".

Please provide coordinates manually:
- Latitude: 
- Longitude: 

Or try a simpler address (e.g., just "350 5th Avenue New York")
```

### No OSM Buildings Found
```
No buildings found in OpenStreetMap near [address].

This could mean:
1. The building hasn't been mapped in OSM
2. The address geocoded to the wrong location
3. The building is very new (not yet in OSM)

Please provide building footprint dimensions manually:
- Length (ft): 
- Width (ft): 
- Or total footprint area (sq ft):
```

### Floor Count Unknown
```
OSM does not have floor count data for this building.

Please provide floor count from:
1. Property documents (PCA, CNA, offering memo)
2. Visual inspection / site visit
3. Your best estimate

Number of floors:
```

### Overpass API Error
```
Overpass API request failed (HTTP 429 - Too Many Requests).

Retrying with backup endpoint...

If this continues to fail, please wait 60 seconds and try again.
```

---

## Important Rules

- **Always use Nominatim for geocoding** - It's free and doesn't require API keys
- **Respect rate limits:** 1 req/sec for Nominatim, ~10 req/sec for Overpass
- **Always include User-Agent header** with contact info
- **Prefer documented floor counts** over OSM tags (OSM is often outdated)
- **Flag discrepancies** >10% between calculated and reported GFA
- **When in doubt, ask the user** - Don't guess silently
- **Cache API responses** - Don't re-query for the same address

---

## Testing Checklist

Before returning GFA:

- [ ] Geocoding succeeded or user provided coordinates
- [ ] OSM query returned buildings or user provided dimensions
- [ ] Buildings filtered correctly (excluded neighbors)
- [ ] Footprint areas calculated using Shoelace formula
- [ ] Floor counts obtained from reliable source
- [ ] GFA calculated correctly (footprint × floors)
- [ ] Total validated against reported GFA (if available)
- [ ] Results presented in clear table format
- [ ] User confirmed results or flagged discrepancies

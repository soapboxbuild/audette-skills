---
name: kml-generator
description: >
  Generate KML files for visualizing building locations in Google Earth. Use when the
  user asks to "create a KML file", "generate KML", "make a map for Google Earth",
  "visualize addresses", "plot buildings on a map", "export portfolio locations", or
  mentions creating Google Earth visualizations from addresses or building data.
version: 1.0.0
---

# KML Generator

Generate KML (Keyhole Markup Language) files for visualizing building locations in Google Earth.

**No MCP dependencies** - Uses public Nominatim API for geocoding

## When to Use

- Converting address lists to Google Earth placemarks
- Generating KML files from building/property data
- Creating portfolio location visualizations
- Exporting geocoded data for presentations
- Preparing spatial data for Google Earth

---

## Workflow

### Step 1: Gather Input Data

Accept input in one of these formats:

**Address list:**
```
123 Main St, New York, NY 10001
456 Park Ave, Boston, MA 02108
789 State St, Chicago, IL 60601
```

**CSV with addresses:**
```csv
address,name,description
123 Main St New York NY,Building A,Office Tower
456 Park Ave Boston MA,Building B,Retail Center
```

**CSV with coordinates:**
```csv
lat,lng,name,description
40.7128,-74.0060,Building A,Office Tower
42.3601,-71.0589,Building B,Retail Center
```

**JSON from Audette:**
```json
[
  {
    "name": "Building A",
    "address": "123 Main St, New York, NY",
    "lat": 40.7128,
    "lng": -74.0060,
    "metadata": {
      "gfa": 50000,
      "carbon_intensity": 3.2
    }
  }
]
```

---

### Step 2: Geocode Addresses (if needed)

If input includes addresses without coordinates, use **Nominatim API**:

```bash
curl "https://nominatim.openstreetmap.org/search?format=json&q=${address}" \
  -H "User-Agent: audette-skills/1.0 (https://github.com/soapboxbuild/audette-skills)"
```

**Example:**
```bash
curl "https://nominatim.openstreetmap.org/search?format=json&q=123+Main+St+New+York+NY" \
  -H "User-Agent: Audette-Orchestrator/1.0"
```

**Response:**
```json
[
  {
    "lat": "40.7128",
    "lon": "-74.0060",
    "display_name": "123 Main Street, New York, NY, USA",
    "type": "building"
  }
]
```

**Rate limit:** 1 request per second. Add 1-second delay between calls.

**Batch processing:**
```python
import time
import requests

geocoded = []
for address in addresses:
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"format": "json", "q": address},
        headers={"User-Agent": "Audette-Orchestrator/1.0"}
    )
    if response.ok and response.json():
        result = response.json()[0]
        geocoded.append({
            "address": address,
            "lat": float(result["lat"]),
            "lng": float(result["lon"])
        })
    time.sleep(1)  # Rate limit
```

**Error handling:**
- If geocoding fails for an address, ask user to provide coordinates manually
- If multiple results returned, take first result or ask user to confirm

---

### Step 3: Generate KML File

Create KML XML structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{{document_name}}</name>
    <description>{{document_description}}</description>
    
    <!-- Default placemark style -->
    <Style id="default">
      <IconStyle>
        <Icon>
          <href>http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png</href>
        </Icon>
      </IconStyle>
    </Style>
    
    {{#each placemarks}}
    <Placemark>
      <name>{{name}}</name>
      <description><![CDATA[{{description}}]]></description>
      <styleUrl>#default</styleUrl>
      <Point>
        <coordinates>{{lng}},{{lat}},0</coordinates>
      </Point>
      {{#if metadata}}
      <ExtendedData>
        {{#each metadata}}
        <Data name="{{@key}}">
          <value>{{this}}</value>
        </Data>
        {{/each}}
      </ExtendedData>
      {{/if}}
    </Placemark>
    {{/each}}
    
  </Document>
</kml>
```

**Python script for generation:**

```python
def generate_kml(placemarks, document_name="Portfolio Locations", description=""):
    kml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        '  <Document>',
        f'    <name>{document_name}</name>',
        f'    <description>{description}</description>',
        '',
        '    <Style id="default">',
        '      <IconStyle>',
        '        <Icon>',
        '          <href>http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png</href>',
        '        </Icon>',
        '      </IconStyle>',
        '    </Style>',
        ''
    ]
    
    for pm in placemarks:
        kml_lines.extend([
            '    <Placemark>',
            f'      <name>{escape_xml(pm["name"])}</name>',
            f'      <description><![CDATA[{pm.get("description", "")}]]></description>',
            '      <styleUrl>#default</styleUrl>',
            '      <Point>',
            f'        <coordinates>{pm["lng"]},{pm["lat"]},0</coordinates>',
            '      </Point>',
        ])
        
        if "metadata" in pm and pm["metadata"]:
            kml_lines.append('      <ExtendedData>')
            for key, value in pm["metadata"].items():
                kml_lines.extend([
                    f'        <Data name="{key}">',
                    f'          <value>{value}</value>',
                    '        </Data>'
                ])
            kml_lines.append('      </ExtendedData>')
        
        kml_lines.append('    </Placemark>')
        kml_lines.append('')
    
    kml_lines.extend([
        '  </Document>',
        '</kml>'
    ])
    
    return '\n'.join(kml_lines)

def escape_xml(text):
    """Escape special XML characters"""
    return (text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;"))
```

---

### Step 4: Format Placemark Descriptions

Create rich descriptions with property details:

```python
def create_description(building):
    desc_parts = []
    
    # Address
    if "address" in building:
        desc_parts.append(f"<b>Address:</b> {building['address']}")
    
    # Building details
    if "gfa" in building.get("metadata", {}):
        desc_parts.append(f"<b>GFA:</b> {building['metadata']['gfa']:,} sq ft")
    
    if "carbon_intensity" in building.get("metadata", {}):
        desc_parts.append(f"<b>Carbon Intensity:</b> {building['metadata']['carbon_intensity']} kgCO2e/sqft/yr")
    
    if "eui" in building.get("metadata", {}):
        desc_parts.append(f"<b>EUI:</b> {building['metadata']['eui']} kWh/sqft/yr")
    
    return "<br/>".join(desc_parts)
```

---

### Step 5: Add Custom Styling (Optional)

**Color code by property type:**
```xml
<Style id="office">
  <IconStyle>
    <Icon>
      <href>http://maps.google.com/mapfiles/kml/pushpin/blue-pushpin.png</href>
    </Icon>
  </IconStyle>
</Style>

<Style id="residential">
  <IconStyle>
    <Icon>
      <href>http://maps.google.com/mapfiles/kml/pushpin/grn-pushpin.png</href>
    </Icon>
  </IconStyle>
</Style>
```

**Icon colors available:**
- `ylw-pushpin.png` - Yellow (default)
- `red-pushpin.png` - Red
- `blu-pushpin.png` - Blue
- `grn-pushpin.png` - Green
- `pink-pushpin.png` - Pink
- `ltblu-pushpin.png` - Light Blue
- `wht-pushpin.png` - White

---

### Step 6: Organize with Folders (Optional)

Group placemarks by category:

```xml
<Folder>
  <name>Office Buildings</name>
  <description>Portfolio office properties</description>
  
  <Placemark>
    <name>Building A</name>
    ...
  </Placemark>
  
  <Placemark>
    <name>Building B</name>
    ...
  </Placemark>
</Folder>

<Folder>
  <name>Retail Properties</name>
  <description>Portfolio retail properties</description>
  
  <Placemark>
    <name>Building C</name>
    ...
  </Placemark>
</Folder>
```

---

### Step 7: Validate and Export

**Validation checks:**
- [ ] All placemarks have valid coordinates (lat: -90 to 90, lng: -180 to 180)
- [ ] XML is well-formed (no unclosed tags)
- [ ] Special characters escaped in names/descriptions
- [ ] Coordinates in correct order (lng, lat, altitude)
- [ ] File has .kml extension

**Test the KML:**
If possible, open in Google Earth to verify:
- All placemarks appear at correct locations
- Descriptions display properly
- Icons render correctly
- Folders are organized as expected

**Export:**
```python
# Write to file
with open("portfolio_locations.kml", "w", encoding="utf-8") as f:
    f.write(kml_content)

print("KML file generated: portfolio_locations.kml")
print("You can open this file in:")
print("- Google Earth Desktop")
print("- Google Earth Pro")
print("- Google My Maps (File > Import)")
```

---

## Example: Complete Workflow

**User:** "Create a KML file for these addresses: 350 5th Ave New York NY, 600 W Virginia St Seattle WA"

**Step 1: Parse input**
```python
addresses = [
    "350 5th Ave, New York, NY",
    "600 W Virginia St, Seattle, WA"
]
```

**Step 2: Geocode via Nominatim**
```python
import time
import requests

placemarks = []
for addr in addresses:
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"format": "json", "q": addr},
        headers={"User-Agent": "Audette-Orchestrator/1.0"}
    )
    
    if response.ok and response.json():
        result = response.json()[0]
        placemarks.append({
            "name": addr.split(",")[0],  # Use first part as name
            "description": addr,
            "lat": float(result["lat"]),
            "lng": float(result["lon"])
        })
    
    time.sleep(1)  # Rate limit
```

**Step 3: Generate KML**
```python
kml = generate_kml(
    placemarks=placemarks,
    document_name="Portfolio Locations",
    description="Two building portfolio"
)
```

**Step 4: Write file**
```python
with open("portfolio.kml", "w", encoding="utf-8") as f:
    f.write(kml)
```

**Result:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Portfolio Locations</name>
    <description>Two building portfolio</description>
    
    <Placemark>
      <name>350 5th Ave</name>
      <description><![CDATA[350 5th Ave, New York, NY]]></description>
      <Point>
        <coordinates>-73.985428,40.748817,0</coordinates>
      </Point>
    </Placemark>
    
    <Placemark>
      <name>600 W Virginia St</name>
      <description><![CDATA[600 W Virginia St, Seattle, WA]]></description>
      <Point>
        <coordinates>-122.3471,47.5691,0</coordinates>
      </Point>
    </Placemark>
    
  </Document>
</kml>
```

---

## Error Handling

### Geocoding Failure
```
Unable to geocode address: "[address]"

Please provide coordinates manually:
- Latitude (-90 to 90):
- Longitude (-180 to 180):
```

### Invalid Coordinates
```
Invalid coordinates for "[name]":
- Latitude: [lat] (must be -90 to 90)
- Longitude: [lng] (must be -180 to 180)

Please correct and try again.
```

### Rate Limit Exceeded
```
Nominatim rate limit reached (1 req/sec).

Processing addresses with 1-second delay between each...

[Progress: 5/20 addresses geocoded]
```

---

## Important Rules

- **Respect Nominatim rate limit:** 1 request per second
- **Always include User-Agent header** with contact info
- **Coordinates order is lng,lat** (not lat,lng) in KML Point elements
- **Escape XML special characters** in names and descriptions
- **Validate coordinates** are within valid ranges before generating KML
- **Cache geocoding results** to avoid redundant API calls
- **Test KML in Google Earth** if possible before delivering to user

---

## Testing Checklist

Before delivering KML file:

- [ ] All addresses geocoded or coordinates provided
- [ ] XML is well-formed (validates)
- [ ] Coordinates in correct order (lng, lat, 0)
- [ ] Special characters escaped
- [ ] Descriptions include useful property details
- [ ] File has .kml extension
- [ ] User can open file in Google Earth

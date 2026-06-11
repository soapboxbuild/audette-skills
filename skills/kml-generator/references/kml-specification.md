# KML Specification and Advanced Features

This reference provides detailed information about KML (Keyhole Markup Language) format, advanced features, and customization options.

## KML Basics

KML is an XML-based format for expressing geographic annotation and visualization. It was developed for Google Earth but is now an Open Geospatial Consortium (OGC) standard.

### Minimal KML Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Document Name</name>
    <Placemark>
      <name>Placemark Name</name>
      <Point>
        <coordinates>-74.0060,40.7128,0</coordinates>
      </Point>
    </Placemark>
  </Document>
</kml>
```

### Coordinate Format

Coordinates are specified as: `longitude,latitude,altitude`

- **Longitude**: -180 to 180 (East is positive)
- **Latitude**: -90 to 90 (North is positive)
- **Altitude**: Meters above sea level (optional, defaults to 0)

**Important**: Longitude comes FIRST, then latitude (opposite of common usage).

## Placemarks

Placemarks mark positions on the Earth's surface.

### Basic Placemark

```xml
<Placemark>
  <name>Building A</name>
  <description>Office Tower - 50,000 sqft</description>
  <Point>
    <coordinates>-74.0060,40.7128,0</coordinates>
  </Point>
</Placemark>
```

### Placemark with HTML Description

```xml
<Placemark>
  <name>Building A</name>
  <description>
    <![CDATA[
      <h3>Building A</h3>
      <p><b>Type:</b> Office Tower</p>
      <p><b>GFA:</b> 50,000 sqft</p>
      <p><b>Carbon Intensity:</b> 3.2 kgCO2e/sqft</p>
      <a href="https://example.com/report.pdf">View Report</a>
    ]]>
  </description>
  <Point>
    <coordinates>-74.0060,40.7128,0</coordinates>
  </Point>
</Placemark>
```

### Placemark with Extended Data

Extended data provides structured metadata:

```xml
<Placemark>
  <name>Building A</name>
  <ExtendedData>
    <Data name="GFA">
      <displayName>Gross Floor Area</displayName>
      <value>50000</value>
    </Data>
    <Data name="Carbon_Intensity">
      <displayName>Carbon Intensity</displayName>
      <value>3.2</value>
    </Data>
    <Data name="Energy_Cost">
      <displayName>Annual Energy Cost</displayName>
      <value>$120,000</value>
    </Data>
  </ExtendedData>
  <Point>
    <coordinates>-74.0060,40.7128,0</coordinates>
  </Point>
</Placemark>
```

## Styling

### Icon Styles

Customize placemark icons:

```xml
<Style id="office-building">
  <IconStyle>
    <color>ff0000ff</color>  <!-- AABBGGRR format -->
    <scale>1.2</scale>
    <Icon>
      <href>http://maps.google.com/mapfiles/kml/shapes/office.png</href>
    </Icon>
  </IconStyle>
</Style>

<Placemark>
  <name>Office Building</name>
  <styleUrl>#office-building</styleUrl>
  <Point>
    <coordinates>-74.0060,40.7128,0</coordinates>
  </Point>
</Placemark>
```

### Common Google Earth Icons

Base URL: `http://maps.google.com/mapfiles/kml/`

- **Pushpins**: `pushpin/ylw-pushpin.png`, `pushpin/red-pushpin.png`, `pushpin/grn-pushpin.png`
- **Shapes**: `shapes/donut.png`, `shapes/square.png`, `shapes/star.png`
- **Buildings**: `shapes/homegardenbusiness.png`, `shapes/office.png`
- **Numbered**: `paddle/1.png`, `paddle/2.png`, etc.

### Color Format

Colors in KML use AABBGGRR format (Alpha, Blue, Green, Red):

- `ff0000ff` = Red (opaque)
- `ff00ff00` = Green (opaque)
- `ffff0000` = Blue (opaque)
- `7f0000ff` = Red (50% transparent)
- `ffffffff` = White (opaque)

### Label Styles

Control label appearance:

```xml
<Style id="large-label">
  <LabelStyle>
    <color>ffffffff</color>
    <scale>1.5</scale>
  </LabelStyle>
  <IconStyle>
    <Icon>
      <href>http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png</href>
    </Icon>
  </IconStyle>
</Style>
```

## Folders

Organize placemarks into folders:

```xml
<Document>
  <name>Portfolio</name>
  
  <Folder>
    <name>Northeast Region</name>
    <Placemark>
      <name>NYC Building</name>
      <Point><coordinates>-74.0060,40.7128,0</coordinates></Point>
    </Placemark>
    <Placemark>
      <name>Boston Building</name>
      <Point><coordinates>-71.0589,42.3601,0</coordinates></Point>
    </Placemark>
  </Folder>
  
  <Folder>
    <name>West Coast</name>
    <Placemark>
      <name>SF Building</name>
      <Point><coordinates>-122.4194,37.7749,0</coordinates></Point>
    </Placemark>
  </Folder>
</Document>
```

### Nested Folders

Folders can be nested:

```xml
<Folder>
  <name>United States</name>
  <Folder>
    <name>Northeast</name>
    <Placemark>...</Placemark>
  </Folder>
  <Folder>
    <name>Southeast</name>
    <Placemark>...</Placemark>
  </Folder>
</Folder>
```

## Advanced Geometry

### Lines (Paths)

```xml
<Placemark>
  <name>Path</name>
  <LineString>
    <coordinates>
      -122.4,37.8,0
      -122.5,37.9,0
      -122.6,38.0,0
    </coordinates>
  </LineString>
</Placemark>
```

### Polygons (Areas)

```xml
<Placemark>
  <name>Building Footprint</name>
  <Polygon>
    <outerBoundaryIs>
      <LinearRing>
        <coordinates>
          -122.4,37.8,0
          -122.5,37.8,0
          -122.5,37.9,0
          -122.4,37.9,0
          -122.4,37.8,0
        </coordinates>
      </LinearRing>
    </outerBoundaryIs>
  </Polygon>
</Placemark>
```

## Balloon Customization

Customize the information balloon that appears when clicking a placemark:

```xml
<Style id="custom-balloon">
  <BalloonStyle>
    <text>
      <![CDATA[
        <h2>$[name]</h2>
        <p><b>Description:</b> $[description]</p>
        <p><b>GFA:</b> $[GFA]</p>
        <hr/>
        <small>Data from Audette Platform</small>
      ]]>
    </text>
    <bgColor>ffffffff</bgColor>
    <textColor>ff000000</textColor>
  </BalloonStyle>
</Style>
```

Available placeholders:
- `$[name]` - Placemark name
- `$[description]` - Placemark description
- `$[field_name]` - Any extended data field

## Network Links

Load KML dynamically from a URL:

```xml
<NetworkLink>
  <name>Portfolio Data</name>
  <Link>
    <href>https://example.com/portfolio.kml</href>
    <refreshMode>onInterval</refreshMode>
    <refreshInterval>3600</refreshInterval>
  </Link>
</NetworkLink>
```

Refresh modes:
- `onChange` - Refresh when file changes
- `onInterval` - Refresh at specified interval (seconds)
- `onExpire` - Refresh when cache expires

## Ground Overlays

Overlay images on the map:

```xml
<GroundOverlay>
  <name>Site Plan</name>
  <Icon>
    <href>https://example.com/siteplan.png</href>
  </Icon>
  <LatLonBox>
    <north>40.8</north>
    <south>40.7</south>
    <east>-73.9</east>
    <west>-74.1</west>
    <rotation>0</rotation>
  </LatLonBox>
</GroundOverlay>
```

## Best Practices

### Performance

1. **Limit placemarks**: Keep under 1000 per file for good performance
2. **Use network links**: For large datasets, split into multiple files
3. **Optimize icons**: Use cached Google icons when possible
4. **Minimize descriptions**: Keep HTML descriptions concise

### Organization

1. **Use folders**: Group related placemarks logically
2. **Meaningful names**: Use clear, descriptive names
3. **Consistent styling**: Define styles once, reuse via styleUrl
4. **Document metadata**: Use extended data for structured fields

### Compatibility

1. **Use standard icons**: Google-hosted icons work across platforms
2. **Test in Google Earth**: Verify rendering before distribution
3. **Validate XML**: Ensure well-formed XML structure
4. **Include namespace**: Always use proper KML namespace

## Color-Coding Patterns

### By Performance Tier

```xml
<!-- High Performance (Green) -->
<Style id="high-performance">
  <IconStyle>
    <color>ff00ff00</color>
    <Icon><href>http://maps.google.com/mapfiles/kml/pushpin/grn-pushpin.png</href></Icon>
  </IconStyle>
</Style>

<!-- Medium Performance (Yellow) -->
<Style id="medium-performance">
  <IconStyle>
    <Icon><href>http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png</href></Icon>
  </IconStyle>
</Style>

<!-- Low Performance (Red) -->
<Style id="low-performance">
  <IconStyle>
    <Icon><href>http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png</href></Icon>
  </IconStyle>
</Style>
```

### By Property Type

Use different icons for different building types:

```xml
<Style id="office">
  <IconStyle>
    <Icon><href>http://maps.google.com/mapfiles/kml/shapes/office.png</href></Icon>
  </IconStyle>
</Style>

<Style id="retail">
  <IconStyle>
    <Icon><href>http://maps.google.com/mapfiles/kml/shapes/shopping.png</href></Icon>
  </IconStyle>
</Style>

<Style id="industrial">
  <IconStyle>
    <Icon><href>http://maps.google.com/mapfiles/kml/shapes/factory.png</href></Icon>
  </IconStyle>
</Style>
```

## Common Issues

### Coordinate Order

**Wrong**: `<coordinates>40.7128,-74.0060,0</coordinates>` (lat, lng)
**Correct**: `<coordinates>-74.0060,40.7128,0</coordinates>` (lng, lat)

### XML Escaping

Escape special characters in text:
- `&` → `&amp;`
- `<` → `&lt;`
- `>` → `&gt;`
- `"` → `&quot;`
- `'` → `&apos;`

Or use CDATA for HTML content:
```xml
<description><![CDATA[<b>Bold text</b>]]></description>
```

### Missing Namespace

Always include the KML namespace:
```xml
<kml xmlns="http://www.opengis.net/kml/2.2">
```

## Examples

See the `examples/` directory for complete KML files demonstrating:
- Simple portfolio with placemarks
- Styled portfolio with custom icons
- Portfolio with extended data and folders
- Network-linked dynamic KML

## External Resources

- **KML Reference**: https://developers.google.com/kml/documentation/kmlreference
- **KML Tutorial**: https://developers.google.com/kml/documentation/kml_tut
- **Google Earth User Guide**: https://www.google.com/earth/outreach/learn/
- **OGC KML Standard**: https://www.ogc.org/standards/kml

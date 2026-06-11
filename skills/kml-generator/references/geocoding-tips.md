# Geocoding Best Practices

This reference provides guidance on geocoding addresses for KML generation, handling errors, and optimizing batch operations.

## Overview

Geocoding converts addresses (e.g., "123 Main St, New York, NY") into geographic coordinates (latitude, longitude). The Audette API Server MCP provides the `geocode_address` tool for this purpose.

## Using the Geocoding Tool

### Basic Usage

```python
from audette_mcp import geocode_address

# Geocode a single address
result = geocode_address("123 Main St, New York, NY 10001")

# Returns:
{
    "lat": 40.7128,
    "lng": -74.0060,
    "formatted_address": "123 Main Street, New York, NY 10001, USA",
    "accuracy": "ROOFTOP"  # or RANGE_INTERPOLATED, GEOMETRIC_CENTER, APPROXIMATE
}
```

### Accuracy Levels

Geocoding results include an accuracy indicator:

1. **ROOFTOP** - Precise location (best)
2. **RANGE_INTERPOLATED** - Interpolated between two points (good)
3. **GEOMETRIC_CENTER** - Center of result (e.g., street center)
4. **APPROXIMATE** - Approximate location (city/zip level)

For building-level accuracy, prefer ROOFTOP or RANGE_INTERPOLATED results.

## Address Format

### Best Practices

**Good address formats:**
- `123 Main Street, New York, NY 10001`
- `456 Park Avenue, Boston, MA 02108, USA`
- `789 State St, Chicago, IL 60601`

**Poor address formats:**
- `123 Main` (missing city/state)
- `NY, NY` (too ambiguous)
- `Building on Main Street` (not a valid address)

### Recommended Format

Use this format for best results:
```
[Street Number] [Street Name], [City], [State] [ZIP Code]
```

Include:
- Street number and name
- City
- State (two-letter abbreviation)
- ZIP code (optional but improves accuracy)

## Batch Geocoding

### Strategy

For large address lists:

1. **Batch in reasonable chunks** - Process 50-100 addresses at a time
2. **Rate limiting** - Respect API rate limits (if applicable)
3. **Cache results** - Store geocoded results to avoid re-processing
4. **Handle failures gracefully** - Continue processing even if some fail

### Example Implementation

```python
import time
import json
from pathlib import Path

def batch_geocode(addresses, cache_file='geocode_cache.json', delay=0.1):
    """
    Geocode a list of addresses with caching
    
    Args:
        addresses: List of address strings
        cache_file: Path to cache file
        delay: Delay between requests (seconds)
    
    Returns:
        Dict mapping addresses to results
    """
    # Load cache
    cache = {}
    if Path(cache_file).exists():
        cache = json.loads(Path(cache_file).read_text())
    
    results = {}
    failed = []
    
    for i, address in enumerate(addresses, 1):
        # Check cache first
        if address in cache:
            print(f"[{i}/{len(addresses)}] Using cached: {address}")
            results[address] = cache[address]
            continue
        
        # Geocode
        try:
            print(f"[{i}/{len(addresses)}] Geocoding: {address}")
            result = geocode_address(address)
            results[address] = result
            cache[address] = result
            
            # Save cache after each success
            Path(cache_file).write_text(json.dumps(cache, indent=2))
            
            # Rate limiting
            time.sleep(delay)
            
        except Exception as e:
            print(f"  ⚠️  Failed: {e}")
            failed.append(address)
            results[address] = None
    
    if failed:
        print(f"\n⚠️  {len(failed)} addresses failed:")
        for addr in failed:
            print(f"  - {addr}")
    
    return results
```

## Error Handling

### Common Errors

1. **Address not found**
   - Cause: Invalid or ambiguous address
   - Solution: Verify address format, add more details (ZIP, city)

2. **Multiple results**
   - Cause: Ambiguous address (e.g., "123 Main St" exists in multiple cities)
   - Solution: Include city, state, ZIP for disambiguation

3. **API rate limit**
   - Cause: Too many requests in short time
   - Solution: Add delays between requests, use caching

4. **Invalid characters**
   - Cause: Special characters or formatting issues
   - Solution: Clean addresses before geocoding

### Validation Strategy

Validate geocoding results:

```python
def validate_geocode_result(result, expected_region=None):
    """
    Validate geocoding result
    
    Args:
        result: Geocoding result dict
        expected_region: Optional (lat_min, lat_max, lng_min, lng_max) tuple
    
    Returns:
        True if valid, False otherwise
    """
    if result is None:
        return False
    
    # Check required fields
    if 'lat' not in result or 'lng' not in result:
        return False
    
    lat = result['lat']
    lng = result['lng']
    
    # Check coordinate ranges
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return False
    
    # Check expected region (if provided)
    if expected_region:
        lat_min, lat_max, lng_min, lng_max = expected_region
        if not (lat_min <= lat <= lat_max and lng_min <= lng <= lng_max):
            return False
    
    # Check accuracy (prefer ROOFTOP or RANGE_INTERPOLATED)
    accuracy = result.get('accuracy', 'UNKNOWN')
    if accuracy in ['APPROXIMATE', 'UNKNOWN']:
        print(f"⚠️  Low accuracy: {accuracy}")
        return False  # or True with warning, depending on requirements
    
    return True
```

### Regional Validation

For portfolios in known regions, validate coordinates:

```python
# Northeast US region bounds
NORTHEAST_BOUNDS = (
    39.0,   # lat_min (approx southern PA)
    45.0,   # lat_max (approx northern ME)
    -80.0,  # lng_min (western NY/PA)
    -66.0   # lng_max (eastern ME)
)

# Validate
if not validate_geocode_result(result, NORTHEAST_BOUNDS):
    print("⚠️  Result outside expected region!")
```

## Fallback Strategies

### When Geocoding Fails

1. **Check Audette platform**
   - Building may already exist with coordinates
   - Query via `list_buildings` MCP tool

2. **Manual coordinates**
   - Ask user to provide coordinates
   - Use Google Maps to find coordinates manually

3. **Partial results**
   - Generate KML with successful results
   - Report failed addresses separately

4. **Alternative geocoding**
   - Try simplified address (e.g., just city/state)
   - Use ZIP code centroid as fallback

### Example Fallback Logic

```python
def geocode_with_fallback(address, building_id=None):
    """Geocode with fallback to Audette platform"""
    
    # Try direct geocoding
    try:
        result = geocode_address(address)
        if validate_geocode_result(result):
            return result
    except:
        pass
    
    # Fallback: Check Audette platform
    if building_id:
        building = get_building_details(building_id)
        if building and 'latitude' in building and 'longitude' in building:
            return {
                'lat': building['latitude'],
                'lng': building['longitude'],
                'formatted_address': address,
                'source': 'audette_platform'
            }
    
    # No fallback available
    return None
```

## Address Cleaning

### Preprocessing

Clean addresses before geocoding:

```python
import re

def clean_address(address):
    """
    Clean and standardize address format
    
    Args:
        address: Raw address string
    
    Returns:
        Cleaned address string
    """
    # Remove extra whitespace
    address = ' '.join(address.split())
    
    # Standardize abbreviations
    replacements = {
        r'\bSt\b': 'Street',
        r'\bAve\b': 'Avenue',
        r'\bRd\b': 'Road',
        r'\bBlvd\b': 'Boulevard',
        r'\bDr\b': 'Drive',
        r'\bLn\b': 'Lane',
        r'\bCt\b': 'Court',
        r'\bPl\b': 'Place',
    }
    
    for pattern, replacement in replacements.items():
        address = re.sub(pattern, replacement, address, flags=re.IGNORECASE)
    
    # Remove invalid characters
    address = re.sub(r'[^\w\s,.-]', '', address)
    
    return address.strip()
```

### Validation Before Geocoding

```python
def is_valid_address(address):
    """Check if address is likely valid before geocoding"""
    
    # Must have minimum length
    if len(address) < 10:
        return False
    
    # Should contain a number (street number)
    if not re.search(r'\d', address):
        return False
    
    # Should contain state abbreviation or full name
    states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
              'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
              'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
              'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
              'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
    
    if not any(state in address.upper() for state in states):
        return False
    
    return True
```

## CSV Integration

### Reading Addresses from CSV

```python
import csv

def load_addresses_from_csv(csv_path, address_col='address'):
    """Load addresses from CSV file"""
    
    addresses = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            address = row.get(address_col, '').strip()
            if address and is_valid_address(address):
                addresses.append({
                    'address': address,
                    'name': row.get('name', 'Unnamed'),
                    'metadata': row  # Preserve all original data
                })
    
    return addresses
```

### Writing Results to CSV

```python
def write_geocoded_results(results, output_path):
    """Write geocoded results to CSV"""
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['name', 'address', 'lat', 'lng', 'formatted_address', 'accuracy', 'status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        for item in results:
            result = item.get('geocode_result')
            writer.writerow({
                'name': item['name'],
                'address': item['address'],
                'lat': result['lat'] if result else '',
                'lng': result['lng'] if result else '',
                'formatted_address': result.get('formatted_address', '') if result else '',
                'accuracy': result.get('accuracy', '') if result else '',
                'status': 'success' if result else 'failed'
            })
```

## Performance Optimization

### Caching Strategy

1. **Session cache** - In-memory cache for current session
2. **Persistent cache** - JSON file for across sessions
3. **Cache invalidation** - Clear cache if API changes or addresses update

### Parallel Processing

For very large batches (1000+ addresses), consider parallel processing:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def parallel_geocode(addresses, max_workers=5):
    """Geocode addresses in parallel"""
    
    results = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_address = {
            executor.submit(geocode_address, addr): addr 
            for addr in addresses
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_address):
            address = future_to_address[future]
            try:
                result = future.result()
                results[address] = result
            except Exception as e:
                print(f"Failed to geocode {address}: {e}")
                results[address] = None
    
    return results
```

**Caution**: Only use parallel processing if API rate limits allow.

## Best Practices Summary

1. **Validate addresses** before geocoding
2. **Clean and standardize** address format
3. **Use caching** to avoid redundant API calls
4. **Handle failures gracefully** - continue processing, report errors
5. **Check accuracy** - validate ROOFTOP/RANGE_INTERPOLATED results
6. **Regional validation** - verify coordinates are in expected region
7. **Batch processing** - process in chunks with rate limiting
8. **Preserve original data** - keep address alongside coordinates
9. **Fallback to platform** - check Audette for existing coordinates
10. **Document limitations** - report accuracy and failures to user

## Common Patterns

### Portfolio Geocoding Workflow

```
1. Load addresses from CSV/JSON
2. Clean and validate addresses
3. Check cache for existing results
4. Batch geocode remaining addresses
5. Validate geocoding results
6. Fallback to Audette platform for failures
7. Write results to CSV
8. Generate KML from successful results
9. Report failures to user
```

### Report Integration

When generating reports with maps:
1. Extract building addresses from report data
2. Geocode addresses (with caching)
3. Generate KML with report highlights
4. Include KML link in report
5. Deliver KML alongside PDF

## Troubleshooting

### Low Accuracy Results

If getting APPROXIMATE or GEOMETRIC_CENTER results:
- Add more address details (ZIP code, unit number)
- Verify address spelling
- Try alternative address formats
- Check if building exists in Audette platform

### Coordinates Outside Expected Region

If coordinates are far from expected location:
- Verify address is correct (not another city with same street name)
- Check for typos in city/state
- Add ZIP code for disambiguation
- Manually verify result in Google Maps

### Rate Limiting Errors

If hitting rate limits:
- Increase delay between requests
- Reduce batch size
- Use caching to avoid re-geocoding
- Contact admin to increase quota

## Additional Resources

- Audette API Server MCP documentation
- Google Geocoding API documentation
- Address standardization tools (USPS, SmartyStreets)

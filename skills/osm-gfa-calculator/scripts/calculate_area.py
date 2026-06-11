#!/usr/bin/env python3
"""
Calculate polygon area from lat/lon coordinates using Shoelace formula.
Returns area in square feet.
"""
import sys
import json
import math

def calculate_polygon_area_sqft(coords, center_lat):
    """
    Calculate area of a polygon given lat/lon coordinates.

    Args:
        coords: list of {"lat": float, "lon": float} dicts
        center_lat: latitude in degrees (for projection)

    Returns:
        float: area in square feet
    """
    # Convert lat/lon degrees to meters
    rad = math.radians(center_lat)
    m_per_deg_lat = 111320
    m_per_deg_lon = 111320 * math.cos(rad)

    # Project coordinates to meters
    points = [
        (c['lon'] * m_per_deg_lon, c['lat'] * m_per_deg_lat)
        for c in coords
    ]

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

if __name__ == "__main__":
    # Read JSON from command line argument
    data = json.loads(sys.argv[1])
    coords = data['coords']
    center_lat = data['center_lat']

    area = calculate_polygon_area_sqft(coords, center_lat)

    # Print area rounded to 1 decimal place
    print(f"{area:.1f}")

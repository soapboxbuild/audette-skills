#!/usr/bin/env python3
"""
KML Validation Script

Validates KML files for proper structure and common issues.
"""

import argparse
import sys
from xml.etree import ElementTree as ET
from pathlib import Path


def validate_kml(kml_path: str) -> bool:
    """
    Validate KML file

    Returns:
        True if valid, False otherwise
    """
    issues = []

    try:
        # Parse XML
        tree = ET.parse(kml_path)
        root = tree.getroot()

        # Check root element
        if not root.tag.endswith('kml'):
            issues.append("Root element is not 'kml'")

        # Find Document
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        doc = root.find('kml:Document', ns) or root.find('Document')

        if doc is None:
            issues.append("No Document element found")
        else:
            # Check placemarks
            placemarks = doc.findall('.//kml:Placemark', ns) or doc.findall('.//Placemark')

            if not placemarks:
                issues.append("No Placemark elements found")
            else:
                print(f"Found {len(placemarks)} placemarks")

                # Validate each placemark
                for i, pm in enumerate(placemarks, 1):
                    # Check for Point
                    point = pm.find('.//kml:Point', ns) or pm.find('.//Point')
                    if point is None:
                        issues.append(f"Placemark #{i}: No Point element")
                        continue

                    # Check coordinates
                    coords = point.find('.//kml:coordinates', ns) or point.find('.//coordinates')
                    if coords is None:
                        issues.append(f"Placemark #{i}: No coordinates element")
                        continue

                    # Validate coordinate format
                    coord_text = coords.text.strip()
                    try:
                        parts = coord_text.split(',')
                        if len(parts) < 2:
                            issues.append(f"Placemark #{i}: Invalid coordinate format: {coord_text}")
                            continue

                        lng = float(parts[0])
                        lat = float(parts[1])

                        # Validate ranges
                        if not (-90 <= lat <= 90):
                            issues.append(f"Placemark #{i}: Latitude out of range: {lat}")
                        if not (-180 <= lng <= 180):
                            issues.append(f"Placemark #{i}: Longitude out of range: {lng}")

                    except (ValueError, IndexError) as e:
                        issues.append(f"Placemark #{i}: Invalid coordinates: {coord_text}")

    except ET.ParseError as e:
        issues.append(f"XML parsing error: {e}")
        return False

    except Exception as e:
        issues.append(f"Unexpected error: {e}")
        return False

    # Report results
    if issues:
        print(f"\n❌ Validation FAILED with {len(issues)} issue(s):\n")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("\n✅ Validation PASSED")
        return True


def main():
    parser = argparse.ArgumentParser(description="Validate KML files")
    parser.add_argument('kml_file', help='KML file to validate')

    args = parser.parse_args()

    if not Path(args.kml_file).exists():
        print(f"Error: File not found: {args.kml_file}", file=sys.stderr)
        sys.exit(1)

    print(f"Validating: {args.kml_file}\n")

    valid = validate_kml(args.kml_file)
    sys.exit(0 if valid else 1)


if __name__ == '__main__':
    main()

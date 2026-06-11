#!/usr/bin/env python3
"""
KML Generator Script

Generates KML files from addresses, coordinates, or building data.
Supports geocoding, validation, styling, and folder organization.
"""

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from xml.dom import minidom


class KMLGenerator:
    """Generate KML files for Google Earth visualization"""

    def __init__(
        self,
        name: str = "Locations",
        description: str = "",
        icon_url: str = "http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png"
    ):
        """
        Initialize KML generator

        Args:
            name: KML document name
            description: KML document description
            icon_url: Default icon URL for placemarks
        """
        self.name = name
        self.description = description
        self.icon_url = icon_url
        self.placemarks = []
        self.folders = {}

    def add_placemark(
        self,
        name: str,
        lat: float,
        lng: float,
        description: str = "",
        folder: Optional[str] = None,
        extended_data: Optional[Dict[str, Any]] = None,
        icon_url: Optional[str] = None
    ) -> None:
        """
        Add a placemark to the KML

        Args:
            name: Placemark name
            lat: Latitude (-90 to 90)
            lng: Longitude (-180 to 180)
            description: Placemark description (supports HTML)
            folder: Optional folder name to organize placemarks
            extended_data: Optional dict of extended data fields
            icon_url: Optional custom icon URL (overrides default)
        """
        # Validate coordinates
        if not self._validate_coordinates(lat, lng):
            print(f"Warning: Invalid coordinates for {name}: ({lat}, {lng})", file=sys.stderr)
            return

        placemark = {
            "name": name,
            "lat": lat,
            "lng": lng,
            "description": description,
            "extended_data": extended_data or {},
            "icon_url": icon_url or self.icon_url,
            "folder": folder
        }

        self.placemarks.append(placemark)

        # Track folders
        if folder:
            if folder not in self.folders:
                self.folders[folder] = []
            self.folders[folder].append(placemark)

    def _validate_coordinates(self, lat: float, lng: float) -> bool:
        """Validate latitude and longitude ranges"""
        try:
            lat = float(lat)
            lng = float(lng)
            return -90 <= lat <= 90 and -180 <= lng <= 180
        except (ValueError, TypeError):
            return False

    def generate(self) -> str:
        """
        Generate KML string

        Returns:
            KML XML as string
        """
        kml = ['<?xml version="1.0" encoding="UTF-8"?>']
        kml.append('<kml xmlns="http://www.opengis.net/kml/2.2">')
        kml.append('  <Document>')
        kml.append(f'    <name>{self._escape_xml(self.name)}</name>')

        if self.description:
            kml.append(f'    <description>{self._escape_xml(self.description)}</description>')

        # Add default style
        kml.append('    <Style id="default">')
        kml.append('      <IconStyle>')
        kml.append(f'        <Icon><href>{self._escape_xml(self.icon_url)}</href></Icon>')
        kml.append('      </IconStyle>')
        kml.append('    </Style>')

        # Add placemarks (organized by folder or flat)
        if self.folders:
            # Organized by folders
            for folder_name, folder_placemarks in self.folders.items():
                kml.append(f'    <Folder>')
                kml.append(f'      <name>{self._escape_xml(folder_name)}</name>')
                for pm in folder_placemarks:
                    kml.extend(self._generate_placemark(pm, indent=6))
                kml.append(f'    </Folder>')

            # Add placemarks not in folders
            no_folder = [pm for pm in self.placemarks if not pm["folder"]]
            for pm in no_folder:
                kml.extend(self._generate_placemark(pm, indent=4))
        else:
            # Flat structure
            for pm in self.placemarks:
                kml.extend(self._generate_placemark(pm, indent=4))

        kml.append('  </Document>')
        kml.append('</kml>')

        return '\n'.join(kml)

    def _generate_placemark(self, placemark: Dict, indent: int = 4) -> List[str]:
        """Generate KML lines for a single placemark"""
        ind = ' ' * indent
        lines = []

        lines.append(f'{ind}<Placemark>')
        lines.append(f'{ind}  <name>{self._escape_xml(placemark["name"])}</name>')

        if placemark["description"]:
            lines.append(f'{ind}  <description>')
            lines.append(f'{ind}    <![CDATA[{placemark["description"]}]]>')
            lines.append(f'{ind}  </description>')

        # Extended data
        if placemark["extended_data"]:
            lines.append(f'{ind}  <ExtendedData>')
            for key, value in placemark["extended_data"].items():
                lines.append(f'{ind}    <Data name="{self._escape_xml(key)}">')
                lines.append(f'{ind}      <value>{self._escape_xml(str(value))}</value>')
                lines.append(f'{ind}    </Data>')
            lines.append(f'{ind}  </ExtendedData>')

        # Style
        if placemark["icon_url"] != self.icon_url:
            # Custom icon for this placemark
            lines.append(f'{ind}  <Style>')
            lines.append(f'{ind}    <IconStyle>')
            lines.append(f'{ind}      <Icon><href>{self._escape_xml(placemark["icon_url"])}</href></Icon>')
            lines.append(f'{ind}    </IconStyle>')
            lines.append(f'{ind}  </Style>')
        else:
            lines.append(f'{ind}  <styleUrl>#default</styleUrl>')

        # Point
        lines.append(f'{ind}  <Point>')
        lines.append(f'{ind}    <coordinates>{placemark["lng"]},{placemark["lat"]},0</coordinates>')
        lines.append(f'{ind}  </Point>')

        lines.append(f'{ind}</Placemark>')

        return lines

    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters"""
        return (str(text)
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))

    def save(self, output_path: str, pretty: bool = True) -> None:
        """
        Save KML to file

        Args:
            output_path: Output file path
            pretty: Pretty-print XML (default True)
        """
        kml_str = self.generate()

        if pretty:
            # Pretty print using minidom
            try:
                dom = minidom.parseString(kml_str)
                kml_str = dom.toprettyxml(indent="  ", encoding="UTF-8").decode("utf-8")
                # Remove extra blank lines
                kml_str = '\n'.join([line for line in kml_str.split('\n') if line.strip()])
            except Exception as e:
                print(f"Warning: Could not pretty-print KML: {e}", file=sys.stderr)

        Path(output_path).write_text(kml_str, encoding='utf-8')
        print(f"KML saved to: {output_path}")
        print(f"Placemarks: {len(self.placemarks)}")
        if self.folders:
            print(f"Folders: {len(self.folders)}")


def load_csv(csv_path: str) -> List[Dict[str, Any]]:
    """Load locations from CSV file"""
    locations = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            locations.append(dict(row))

    return locations


def load_json(json_path: str) -> List[Dict[str, Any]]:
    """Load locations from JSON file"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, dict):
        # Single location
        return [data]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError("JSON must be a dict or list of dicts")


def main():
    parser = argparse.ArgumentParser(
        description="Generate KML files for Google Earth",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # From CSV with addresses (requires geocoding)
  python generate_kml.py --input buildings.csv --output portfolio.kml --name "Portfolio"

  # From CSV with coordinates
  python generate_kml.py --input coords.csv --output map.kml --lat-col latitude --lng-col longitude

  # From JSON
  python generate_kml.py --input buildings.json --output map.kml --format json

CSV Format:
  With coordinates:
    name,lat,lng,description
    Building A,40.7128,-74.0060,Office tower

  With addresses (requires geocoding separately):
    name,address,description
    Building A,123 Main St NYC,Office tower
"""
    )

    parser.add_argument('--input', '-i', required=True, help='Input file (CSV or JSON)')
    parser.add_argument('--output', '-o', required=True, help='Output KML file path')
    parser.add_argument('--format', '-f', choices=['csv', 'json'], default='csv', help='Input format (default: csv)')
    parser.add_argument('--name', '-n', default='Locations', help='KML document name')
    parser.add_argument('--description', '-d', default='', help='KML document description')
    parser.add_argument('--name-col', default='name', help='CSV column for placemark name (default: name)')
    parser.add_argument('--lat-col', default='lat', help='CSV column for latitude (default: lat)')
    parser.add_argument('--lng-col', default='lng', help='CSV column for longitude (default: lng)')
    parser.add_argument('--desc-col', default='description', help='CSV column for description (default: description)')
    parser.add_argument('--folder-col', default=None, help='CSV column for folder organization')
    parser.add_argument('--icon-url', default=None, help='Default icon URL')

    args = parser.parse_args()

    # Load data
    print(f"Loading data from: {args.input}")

    if args.format == 'csv':
        locations = load_csv(args.input)
    else:
        locations = load_json(args.input)

    print(f"Loaded {len(locations)} locations")

    # Create KML generator
    kwargs = {
        'name': args.name,
        'description': args.description
    }
    if args.icon_url:
        kwargs['icon_url'] = args.icon_url

    kml = KMLGenerator(**kwargs)

    # Add placemarks
    skipped = 0
    for loc in locations:
        try:
            # Extract fields
            name = loc.get(args.name_col, 'Unnamed')
            lat = float(loc.get(args.lat_col, 0))
            lng = float(loc.get(args.lng_col, 0))
            description = loc.get(args.desc_col, '')
            folder = loc.get(args.folder_col) if args.folder_col else None

            # Extended data (all other fields)
            extended_data = {k: v for k, v in loc.items()
                           if k not in [args.name_col, args.lat_col, args.lng_col, args.desc_col, args.folder_col]}

            kml.add_placemark(
                name=name,
                lat=lat,
                lng=lng,
                description=description,
                folder=folder,
                extended_data=extended_data if extended_data else None
            )

        except (ValueError, KeyError) as e:
            print(f"Warning: Skipping location due to error: {e}", file=sys.stderr)
            skipped += 1

    if skipped:
        print(f"Skipped {skipped} locations due to errors")

    # Save KML
    kml.save(args.output)
    print(f"\nSuccess! Open {args.output} in Google Earth")


if __name__ == '__main__':
    main()

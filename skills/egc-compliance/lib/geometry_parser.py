"""
Geometry Parser — Extract 3D geometry from EnergyPlus IDF files.

Parses BuildingSurface:Detailed objects to extract surface names, types,
zones, and vertex coordinates for visualization.
"""

from pathlib import Path
from typing import Dict, List, Any, Union


# BuildingSurface:Detailed field indices per IDF spec
FIELD_NAME = 0
FIELD_TYPE = 1
FIELD_CONSTRUCTION = 2
FIELD_ZONE = 3
FIELD_VERTEX_COUNT = 10
FIELD_COORD_START = 11


def parse_idf_geometry(idf_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Extract 3D geometry from EnergyPlus IDF file.

    Args:
        idf_path: Path to .idf file

    Returns:
        {
            "surfaces": [
                {
                    "name": str,
                    "type": str,  # "Wall", "Roof", "Floor", "Ceiling"
                    "zone": str,
                    "vertices": [[x, y, z], ...],
                    "construction": str
                },
                ...
            ],
            "bounds": {
                "min": [x, y, z],
                "max": [x, y, z],
                "center": [x, y, z]
            },
            "zone_count": int,
            "surface_count_by_type": {
                "Wall": int,
                "Roof": int,
                "Floor": int,
                "Ceiling": int
            }
        }

    Raises:
        ValueError: If IDF file is malformed or missing required data
    """
    # Read IDF file
    idf_path = Path(idf_path)
    if not idf_path.exists():
        raise ValueError(f"IDF file not found: {idf_path}")

    with open(idf_path, 'r') as f:
        lines = f.readlines()

    # Parse surfaces by collecting all fields for each object
    surfaces = []
    zones = set()

    in_surface = False
    current_fields = []

    for line_num, line in enumerate(lines, 1):
        # Strip comments
        if '!' in line:
            code_part = line.split('!')[0]
        else:
            code_part = line

        code_part = code_part.strip()

        # Skip empty lines
        if not code_part:
            continue

        # Detect BuildingSurface:Detailed start
        if 'BuildingSurface:Detailed,' in code_part:
            in_surface = True
            current_fields = []
            continue

        if in_surface:
            # Check if this is the end of the object
            is_end = code_part.endswith(';')

            # Split line by commas to get individual values
            # Strip trailing comma/semicolon first, then split
            clean_line = code_part.rstrip(',;')
            # Split preserves empty fields between commas
            values = [v.strip() for v in clean_line.split(',')]
            current_fields.extend(values)

            # If end of object, process the fields
            if is_end:
                # Parse the collected fields
                if len(current_fields) >= 11:
                    try:
                        name = current_fields[FIELD_NAME]
                        surf_type = current_fields[FIELD_TYPE]
                        construction = current_fields[FIELD_CONSTRUCTION]
                        zone = current_fields[FIELD_ZONE]
                        zones.add(zone)
                        vertex_count = int(current_fields[FIELD_VERTEX_COUNT])
                    except (ValueError, IndexError) as e:
                        raise ValueError(
                            f"Failed to parse BuildingSurface:Detailed header at line {line_num}. "
                            f"Error: {e}. Fields: {current_fields[:11]}"
                        )

                    # Validate that we have enough coordinate fields for the claimed vertex count
                    required_fields = FIELD_COORD_START + (vertex_count * 3)
                    if len(current_fields) < required_fields:
                        raise ValueError(
                            f"Surface '{name}' claims {vertex_count} vertices but only "
                            f"{len(current_fields) - FIELD_COORD_START} coordinate values provided. "
                            f"Expected {vertex_count * 3} coordinates (line {line_num})"
                        )

                    # Extract vertices (groups of 3 coordinates)
                    vertices = []
                    for i in range(vertex_count):
                        try:
                            x = float(current_fields[FIELD_COORD_START + i * 3])
                            y = float(current_fields[FIELD_COORD_START + i * 3 + 1])
                            z = float(current_fields[FIELD_COORD_START + i * 3 + 2])
                            vertices.append([x, y, z])
                        except (ValueError, IndexError) as e:
                            raise ValueError(
                                f"Failed to parse vertex {i+1} of surface '{name}' at line {line_num}. "
                                f"Error: {e}. Coordinate fields: {current_fields[FIELD_COORD_START + i * 3:FIELD_COORD_START + i * 3 + 3]}"
                            )

                    surfaces.append({
                        'name': name,
                        'type': surf_type,
                        'construction': construction,
                        'zone': zone,
                        'vertices': vertices
                    })

                in_surface = False

    # Calculate bounds from all vertices
    all_vertices = []
    for surface in surfaces:
        all_vertices.extend(surface['vertices'])

    if all_vertices:
        xs = [v[0] for v in all_vertices]
        ys = [v[1] for v in all_vertices]
        zs = [v[2] for v in all_vertices]

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        min_z, max_z = min(zs), max(zs)

        bounds = {
            'min': [min_x, min_y, min_z],
            'max': [max_x, max_y, max_z],
            'center': [
                (min_x + max_x) / 2,
                (min_y + max_y) / 2,
                (min_z + max_z) / 2
            ]
        }
    else:
        bounds = {
            'min': [0.0, 0.0, 0.0],
            'max': [0.0, 0.0, 0.0],
            'center': [0.0, 0.0, 0.0]
        }

    # Count surfaces by type
    surface_count_by_type = {
        'Wall': 0,
        'Roof': 0,
        'Floor': 0,
        'Ceiling': 0
    }
    for surface in surfaces:
        surf_type = surface['type']
        if surf_type in surface_count_by_type:
            surface_count_by_type[surf_type] += 1

    return {
        'surfaces': surfaces,
        'bounds': bounds,
        'zone_count': len(zones),
        'surface_count_by_type': surface_count_by_type
    }

"""
Model Adapter - Bridges BuildingCollector flat schema to IDFGenerator nested schema.

BuildingCollector outputs:
    {
        "geometry": {"footprint_sqft": 8000, "stories": 4, ...},
        "envelope": {"wall_r_value": 13, ...},
        "systems": {"heating_efficiency": 0.85, ...},
        "lighting": {"lpd_w_per_sf": 0.8},
        ...
    }

IDFGenerator expects:
    {
        "project": {...},
        "stories": [{...}],
        "constructions": [{...}],
        "hvac_equipment": [{...}],
        "window_defs": [{...}]
    }

This adapter performs the schema transformation.
"""

import math
from typing import Dict, Any, List


def schema_to_idf_payload(building_model: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert BuildingCollector flat schema to IDFGenerator nested payload.

    Args:
        building_model: Flat schema from BuildingCollector or scenario modifiers

    Returns:
        Nested payload ready for IDFGenerator
    """
    # Extract sections with defaults
    geometry = building_model.get('geometry', {})
    envelope = building_model.get('envelope', {})
    systems = building_model.get('systems', {})
    lighting = building_model.get('lighting', {})
    schedules = building_model.get('schedules', {})

    # Project metadata
    project = {
        'name': building_model.get('building_uid', 'Building'),
        'building_type': building_model.get('building_type') or geometry.get('building_type', 'Office'),
        'location': building_model.get('location', 'Chicago IL'),
        'climate_zone': building_model.get('climate_zone', '5A'),
        'lighting_lpd': lighting.get('interior_lpd_w_per_sqft') or lighting.get('lpd_w_per_sf', 0.8)
    }

    # Calculate total conditioned area
    footprint_sqft = float(geometry.get('footprint_sqft', 10000))
    num_stories = int(geometry.get('stories', 2))
    conditioned_area = footprint_sqft * num_stories
    project['conditioned_area_ft2'] = conditioned_area

    # Generate rectangular footprint geometry
    # Assume square footprint if width/depth not provided
    width = float(geometry.get('width_ft') or math.sqrt(footprint_sqft))
    depth = float(geometry.get('depth_ft') or math.sqrt(footprint_sqft))
    # FIX Bug A: Read from flat schema keys (floor_to_floor_ft, not floor_to_floor_height)
    floor_to_floor = float(geometry.get('floor_to_floor_ft') or geometry.get('floor_to_floor', 13.0))
    floor_to_ceiling = float(geometry.get('floor_to_ceiling_ft') or geometry.get('floor_to_ceiling', 10.0))
    wwr = float(geometry.get('wwr', 0.3))

    # Round to avoid floating point artifacts
    w = round(width, 2)
    d = round(depth, 2)

    # FIX Bug A: Create vertices in FEET (IDFGenerator applies ft_to_m internally)
    # Previously converted to meters here, causing double-conversion and 3× too small geometry
    vertices = [[0.0, d], [0.0, 0.0], [w, 0.0], [w, d]]

    # Generate stories list
    stories = []
    for i in range(num_stories):
        story_label = i + 1
        z_origin = i * floor_to_floor

        stories.append({
            'name': f'Story_{story_label}',
            'z_origin': z_origin,
            'floor_to_floor': floor_to_floor,  # FIX Bug A: Correct key (not floor_to_floor_height)
            'floor_to_ceiling': floor_to_ceiling,  # FIX Bug A: Correct key
            'spaces': [{
                'name': f'Zone_{story_label}',
                'width': w,
                'depth': d,
                'vertices': vertices,
                'window_to_wall_ratio': wwr
            }]
        })

    # Constructions (envelope)
    # Prefer r_value over u_value (scenario modifiers write r_value)
    wall_r = envelope.get('wall_r_value')
    if wall_r is None and envelope.get('wall_u_value'):
        wall_r = 1.0 / envelope['wall_u_value']
    wall_r = wall_r or 13.0

    roof_r = envelope.get('roof_r_value')
    if roof_r is None and envelope.get('roof_u_value'):
        roof_r = 1.0 / envelope['roof_u_value']
    roof_r = roof_r or 20.0

    slab_r = envelope.get('slab_r_value')
    if slab_r is None and envelope.get('slab_u_value'):
        slab_r = 1.0 / envelope['slab_u_value']
    slab_r = slab_r or 5.0

    constructions = [{
        'name': 'Default Construction',
        'wall_r_value': wall_r,
        'roof_r_value': roof_r,
        'slab_r_value': slab_r
    }]

    # Window definitions
    window_u = envelope.get('window_u_factor', 0.35)
    window_shgc = envelope.get('window_shgc', 0.40)

    window_defs = [{
        'name': 'Default Window',
        'u_factor': window_u,
        'shgc': window_shgc
    }]

    # HVAC equipment
    heating_eff = systems.get('heating_efficiency')
    if heating_eff is None:
        heating_cop = systems.get('heating_cop', 3.3)
        heating_eff = heating_cop  # COP for heat pumps, efficiency for boilers

    cooling_eer = systems.get('cooling_eer', 11.0)

    hvac_equipment = [{
        'name': 'Default HVAC',
        'equipment_type': systems.get('heating_type', 'heat_pump'),
        'heating_efficiency': heating_eff,
        'heating_cop': heating_eff,  # For backward compat
        'cooling_eer': cooling_eer,
        'ventilation_cfm_per_sqft': systems.get('ventilation_cfm_per_sqft', 0.06),
        'infiltration_ach': systems.get('infiltration_ach', 0.3)
    }]

    # Schedules
    occupancy_schedule = {
        'weekday': schedules.get('weekday_schedule', '08:00-18:00'),
        'weekend': schedules.get('weekend_schedule', '10:00-14:00'),
        'hours_per_week': schedules.get('operating_hours_per_week', 50)
    }

    return {
        'project': project,
        'stories': stories,
        'constructions': constructions,
        'window_defs': window_defs,
        'hvac_equipment': hvac_equipment,
        'schedules': occupancy_schedule
    }

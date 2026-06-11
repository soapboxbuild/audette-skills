"""
Resolves ECM data across multiple Audette plans per building.

Logic:
1. Query all plans for building
2. Identify the published/reported plan (near-term ECMs)
3. Identify the "Audette Recommendations" plan (solar + long-term roadmap)
4. Merge: published plan measures take precedence;
   Recommendations plan provides any measures not in the published plan (especially solar)
5. For each measure, extract measure_cost (total installed) and annual_savings_kwh
"""

from typing import Dict, List, Optional


def resolve_all_plans(client, building_uid: str) -> dict:
    """
    Returns:
    {
      'plans_queried': [list of plan names],
      'published_plan_id': str or None,
      'recommendations_plan_id': str or None,
      'measures': [
        {
          'name': str,
          'year': int,
          'annual_savings_kwh': float,
          'cost': float or None,       # total installed cost (measure_cost)
          'cost_is_estimated': bool,   # True if user_provided_cost == False
          'category': str,             # 'lighting', 'hvac', 'dhw', 'envelope', 'solar'
          'solar_gen_kwh': float,      # Only for solar measures; annual generation
        }
      ],
      'solar_kwh_yr': float,           # Total solar generation from any plan
      'solar_cost': float or None,
    }
    """
    all_plans = client.list_plans(building_uid)

    # Identify plans
    published_plan = None
    recommendations_plan = None

    for plan in all_plans:
        if plan.get('is_reported') and plan.get('is_published'):
            if published_plan is None:
                published_plan = plan
        if 'recommendation' in plan.get('name', '').lower():
            recommendations_plan = plan

    # Fallback: if no published plan, use the first plan
    if published_plan is None and all_plans:
        published_plan = all_plans[0]

    # Query both plans
    measures_by_name = {}  # name → measure dict; published plan wins

    plans_to_query = []
    if published_plan:
        plans_to_query.append(('published', published_plan))
    if recommendations_plan and recommendations_plan != published_plan:
        plans_to_query.append(('recommendations', recommendations_plan))

    solar_kwh_yr = 0.0
    solar_cost = None

    for plan_role, plan in plans_to_query:
        plan_data = client.get_plan(plan['id'])
        measures = plan_data.get('carbon_reduction_plan', {}).get('measures', [])

        for m in measures:
            name = m.get('measure_name') or m.get('name', 'Unknown')
            category = _classify_measure(name)

            # Extract solar specially
            if category == 'solar':
                gen = m.get('annual_generation_kwh') or m.get('annual_savings_kwh', 0)
                solar_kwh_yr = max(solar_kwh_yr, gen)
                cost = m.get('measure_cost') or m.get('cost')
                if cost:
                    solar_cost = cost
                continue  # Don't add solar to regular measures list

            # Skip no-action / placeholder entries
            if m.get('is_no_action') or (m.get('annual_savings_kwh', 0) == 0 and not m.get('measure_cost')):
                continue

            # Published plan wins
            if name in measures_by_name and plan_role == 'recommendations':
                continue

            measures_by_name[name] = {
                'name': name,
                'year': m.get('implementation_year') or m.get('year'),
                'annual_savings_kwh': float(m.get('annual_savings_kwh', 0)),
                'cost': m.get('measure_cost'),
                'cost_is_estimated': not m.get('user_provided_cost', False),
                'category': category,
                'solar_gen_kwh': 0.0,
            }

    # Add solar as separate entry if found
    if solar_kwh_yr > 0:
        measures_by_name['_solar'] = {
            'name': 'Solar PV',
            'year': None,
            'annual_savings_kwh': solar_kwh_yr,
            'cost': solar_cost,
            'cost_is_estimated': solar_cost is None,
            'category': 'solar',
            'solar_gen_kwh': solar_kwh_yr,
        }

    return {
        'plans_queried': [p['name'] for _, p in plans_to_query],
        'published_plan_id': published_plan['id'] if published_plan else None,
        'recommendations_plan_id': recommendations_plan['id'] if recommendations_plan else None,
        'measures': sorted(measures_by_name.values(), key=lambda m: m['year'] or 9999),
        'solar_kwh_yr': solar_kwh_yr,
        'solar_cost': solar_cost,
    }


def _classify_measure(name: str) -> str:
    name_lower = name.lower()
    if 'solar' in name_lower or 'pv' in name_lower or 'photovoltaic' in name_lower:
        return 'solar'
    if 'led' in name_lower or 'light' in name_lower:
        return 'lighting'
    if 'hvac' in name_lower or 'heat pump' in name_lower or 'pthp' in name_lower or 'ptac' in name_lower:
        return 'hvac'
    if 'water heat' in name_lower or 'dhw' in name_lower or 'shower' in name_lower:
        return 'dhw'
    if 'insul' in name_lower or 'window' in name_lower or 'envelope' in name_lower:
        return 'envelope'
    if 'refrigerat' in name_lower:
        return 'appliance'
    if 'thermostat' in name_lower:
        return 'controls'
    return 'other'

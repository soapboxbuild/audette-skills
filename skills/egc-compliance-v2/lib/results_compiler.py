"""
Compiles raw EnergyPlus results into the report data dictionary.

Compliance logic:
  PASS if as_built EUI <= code_min EUI
  (lower EUI = more efficient = better)

Solar is shown supplementally but does NOT affect the compliance verdict.
"""

KWH_TO_KBTU = 3.41214   # 1 kWh = 3.41214 kBtu


def compile(building: dict, raw_results: dict, ecm_data: dict) -> dict:
    """
    Returns report dict with compliance verdict and scenario EUIs.
    """
    gfa = building['gfa_ft2']

    scenarios = {}
    for name in ['as_built', 'code_min', 'retrofit']:
        r = raw_results[name]
        kwh = r['total_site_kwh_yr']
        eui = kwh / gfa
        scenarios[name] = {
            'eui_kwh_ft2': round(eui, 2),
            'eui_kbtu_ft2': round(eui * KWH_TO_KBTU, 1),
            'total_kwh_yr': round(kwh, 0),
            'electric_kwh_yr': round(r.get('electric_kwh_yr', 0), 0),
            'gas_kwh_yr': round(r.get('gas_kwh_yr', 0), 0),
            'end_uses': r.get('end_uses', {}),
        }

    # Compliance: as_built EUI vs code_min EUI
    as_built_eui = scenarios['as_built']['eui_kwh_ft2']
    code_min_eui = scenarios['code_min']['eui_kwh_ft2']
    margin = code_min_eui - as_built_eui  # positive = as_built is better (PASS)

    # Net solar scenario (informational only)
    solar_kwh = ecm_data.get('solar_kwh_yr', 0)
    if solar_kwh > 0:
        net_kwh = max(0, raw_results['retrofit']['total_site_kwh_yr'] - solar_kwh)
        net_eui = net_kwh / gfa
        scenarios['net_solar'] = {
            'eui_kwh_ft2': round(net_eui, 2),
            'eui_kbtu_ft2': round(net_eui * KWH_TO_KBTU, 1),
            'solar_kwh_yr': solar_kwh,
            'label': 'Retrofit + Solar PV (informational only — not used for compliance)',
        }

    return {
        'building': building,
        'scenarios': scenarios,
        'compliance_pass': margin >= 0,
        'compliance_margin_kwh_ft2': round(margin, 2),
        'compliance_margin_pct': round(margin / code_min_eui * 100, 1) if code_min_eui else 0,
        'compliance_margin_kbtu_ft2': round(margin * KWH_TO_KBTU, 1),
        'solar_kwh_yr': solar_kwh,
        'ecm_measures': ecm_data['measures'],
        'standard': 'ASHRAE 90.1-2016',
        'criterion': 'EGC 5.1a Performance Path',
    }

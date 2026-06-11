#!/usr/bin/env python3
"""
EGC Compliance v2 — Green Communities 5.1a ASHRAE 90.1-2016 Performance Path
"""

import argparse
import json
import sys
from pathlib import Path

def main(building_uid: str, output_dir: str = "."):
    """
    Full workflow:
    1. Resolve building data from Audette MCP
    2. Resolve ECM plans and costs
    3. Build 3 EnergyPlus IDF scenarios
    4. Run calibration loop on as-built scenario
    5. Run all 3 scenarios
    6. Compile results + compliance verdict
    7. Generate matplotlib charts
    8. Render PDF via Playwright
    9. Fill BPS Excel template
    10. Report output paths
    """
    from lib.audette_client import AudetteClient
    from lib.plan_resolver import resolve_all_plans
    from lib.idf_builder import IDFBuilder
    from lib.energyplus_runner import EnergyPlusRunner
    from lib.calibrator import Calibrator
    from lib import results_compiler
    from lib.chart_builder import build_all as build_charts
    from lib.pdf_generator import render as render_pdf
    from lib.bps_excel_filler import fill as fill_bps

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Step 1: Building data
    client = AudetteClient()
    building = client.get_building_data(building_uid)
    print(f"[1/9] Building: {building['name']}, GFA {building['gfa_ft2']:,} ft², CZ {building['climate_zone']}")

    # Step 2: ECM plans
    ecm_data = resolve_all_plans(client, building_uid)
    print(f"[2/9] Found {len(ecm_data['measures'])} ECMs across {len(ecm_data['plans_queried'])} plans")

    # Step 3: Build IDFs
    base_dir = Path(__file__).parent
    builder = IDFBuilder(building, base_dir=base_dir)
    idfs = {
        'as_built': builder.build_as_built(),
        'code_min': builder.build_code_min(),   # Uses 90.1-2016 CZ-specific params
        'retrofit': builder.build_retrofit(ecm_data['measures'])
    }
    print("[3/9] IDF files generated")

    # Step 4: Calibrate as-built
    calibrator = Calibrator(building, base_dir=base_dir)
    calibrated_idf, cal_log = calibrator.calibrate(idfs['as_built'])
    idfs['as_built'] = calibrated_idf
    print(f"[4/9] Calibrated: simulated EUI {cal_log['final_eui_kwh_ft2']:.2f} vs target {cal_log['target_eui_kwh_ft2']:.2f} kWh/ft²·yr")

    # Save calibration log
    cal_log_path = output_path / 'calibration_log.json'
    cal_log_path.write_text(json.dumps(cal_log, indent=2))

    # Step 5: Run simulations
    runner = EnergyPlusRunner(base_dir=base_dir)
    raw_results = {}
    for scenario, idf_content in idfs.items():
        idf_path = output_path / f"{building['slug']}_{scenario}.idf"
        idf_path.write_text(idf_content)
        print(f"[5/9] Running {scenario}...", end=' ', flush=True)
        raw_results[scenario] = runner.run(idf_path, weather_epw=builder.get_epw_path())
        print(f"EUI = {raw_results[scenario].get('eui_kwh_ft2', 0):.2f} kWh/ft²·yr")

    # Step 6: Compile + verdict
    report = results_compiler.compile(building, raw_results, ecm_data)
    print(f"[6/9] Compliance: {'PASS' if report['compliance_pass'] else 'FAIL'} "
          f"(margin {report['compliance_margin_kwh_ft2']:+.2f} kWh/ft²·yr)")

    # Step 7: Charts
    charts = build_charts(report)
    print("[7/9] Charts generated")

    # Step 8: PDF
    pdf_path = output_path / f"{building['slug']}_EGC_Compliance_Report.pdf"
    render_pdf(report, charts, ecm_data, pdf_path, base_dir=base_dir)
    print(f"[8/9] PDF: {pdf_path}")

    # Step 9: BPS Excel
    xlsx_path = output_path / f"5-1a_BPS_{building['slug']}_filled.xlsx"
    fill_bps(report, building, xlsx_path, base_dir=base_dir)
    print(f"[9/9] BPS Excel: {xlsx_path}")

    print("\nDone.")
    print(f"  PDF:   {pdf_path}")
    print(f"  Excel: {xlsx_path}")
    return str(pdf_path), str(xlsx_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--building-uid', required=True)
    parser.add_argument('--output-dir', default='.')
    args = parser.parse_args()
    main(args.building_uid, args.output_dir)

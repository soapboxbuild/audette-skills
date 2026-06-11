"""
Fills the Green Communities 5-1a ASHRAE BPS Excel template.

Key cells (Sheet "BPS Summary"):
  B5: Project Name
  B6: Address
  B7: Climate Zone
  B8: Contact Name
  B9: Contact Email
  B12: Prebuild Baseline EUI (kBtu/ft2/yr)  <- Code-Min EUI
  B13: Prebuild Proposed EUI (kBtu/ft2/yr)  <- As-Built EUI
  B14: Postbuild Proposed EUI (kBtu/ft2/yr) <- Retrofit EUI (gross, NO solar)
  B15: % Improvement

NOTE: Postbuild is post-retrofit, NOT post-solar. Solar must NOT be in B14.
"""

from pathlib import Path
import openpyxl
import shutil


KWH_TO_KBTU = 3.41214


def fill(report: dict, building: dict, output_path: Path, base_dir: Path):
    """Fill the BPS template and save to output_path."""
    template_path = base_dir / 'templates' / 'bps_5_1a_template.xlsx'
    shutil.copy(template_path, output_path)

    wb = openpyxl.load_workbook(output_path)
    ws = wb.active  # or wb['BPS Summary'] if named

    # Project info
    _set(ws, 'B5', building.get('name', ''))
    _set(ws, 'B6', building.get('address', ''))
    _set(ws, 'B7', building.get('climate_zone', ''))
    _set(ws, 'B8', building.get('contact_name', 'Michael Brod'))
    _set(ws, 'B9', building.get('contact_email', 'mbrod@rosecompanies.com'))

    # EUI values (kBtu/ft2/yr)
    code_min_kbtu = report['scenarios']['code_min']['eui_kbtu_ft2']
    as_built_kbtu = report['scenarios']['as_built']['eui_kbtu_ft2']
    retrofit_kbtu = report['scenarios']['retrofit']['eui_kbtu_ft2']

    _set(ws, 'B12', round(code_min_kbtu, 1))   # Prebuild Baseline = Code Min
    _set(ws, 'B13', round(as_built_kbtu, 1))   # Prebuild Proposed = As-Built
    _set(ws, 'B14', round(retrofit_kbtu, 1))   # Postbuild Proposed = Retrofit (NO solar)

    # Compliance improvement %
    pct_improvement = (code_min_kbtu - as_built_kbtu) / code_min_kbtu * 100
    _set(ws, 'B15', round(pct_improvement, 1))

    wb.save(output_path)
    wb.close()
    print(f"BPS Excel filled: {output_path}")


def _set(ws, cell_ref: str, value):
    ws[cell_ref] = value

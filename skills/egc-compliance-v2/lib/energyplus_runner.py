"""Runs EnergyPlus and parses annual results from output."""
import subprocess
import os
import csv
import tempfile
from pathlib import Path


class EnergyPlusRunner:
    def __init__(self, base_dir):
        self.base_dir = base_dir

    def run(self, idf_path: Path, weather_epw: Path) -> dict:
        """Run EnergyPlus on idf_path, return results dict."""
        work_dir = idf_path.parent
        result = subprocess.run(
            ['energyplus', '-w', str(weather_epw), '-d', str(work_dir), str(idf_path)],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            raise RuntimeError(f"EnergyPlus failed: {result.stderr[-500:]}")
        return self._parse_results(work_dir, idf_path.stem)

    def run_string(self, idf_content: str) -> dict:
        """Run EnergyPlus from an IDF string (used by calibrator)."""
        # Find the EPW file from the data dir
        epw_dir = self.base_dir / 'data' / 'epw'
        epw_files = list(epw_dir.glob('*.epw'))
        if not epw_files:
            raise RuntimeError("No EPW file found in data/epw/")
        weather_epw = epw_files[0]

        with tempfile.TemporaryDirectory() as tmpdir:
            idf_path = Path(tmpdir) / 'calibration_run.idf'
            idf_path.write_text(idf_content)
            result = subprocess.run(
                ['energyplus', '-w', str(weather_epw), '-d', tmpdir, str(idf_path)],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode != 0:
                raise RuntimeError(f"EnergyPlus failed: {result.stderr[-500:]}")
            return self._parse_results(Path(tmpdir), 'calibration_run')

    def _parse_results(self, work_dir: Path, stem: str) -> dict:
        """Parse EnergyPlus HTML/CSV output for annual totals."""
        meter_csv = work_dir / f"{stem}Meter.csv"
        results = {
            'total_site_kwh_yr': 0,
            'electric_kwh_yr': 0,
            'gas_kwh_yr': 0,
            'end_uses': {}
        }
        J_TO_KWH = 1 / 3_600_000
        if meter_csv.exists():
            with open(meter_csv) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    for k, v in row.items():
                        if 'Electricity:Facility' in k and 'Annual' in k:
                            results['electric_kwh_yr'] = float(v or 0) * J_TO_KWH
                        if 'NaturalGas:Facility' in k and 'Annual' in k:
                            results['gas_kwh_yr'] = float(v or 0) * J_TO_KWH
        results['total_site_kwh_yr'] = results['electric_kwh_yr'] + results['gas_kwh_yr']

        # Try to parse end use breakdown from HTML table summary
        html_file = work_dir / f"{stem}Table.html"
        if html_file.exists():
            results['end_uses'] = _parse_end_uses_html(html_file, J_TO_KWH)

        return results


def _parse_end_uses_html(html_path: Path, j_to_kwh: float) -> dict:
    """Attempt basic parse of EnergyPlus end-use table from HTML output."""
    end_uses = {
        'heating': 0, 'cooling': 0, 'dhw': 0,
        'lighting': 0, 'plug_loads': 0
    }
    try:
        content = html_path.read_text(errors='replace')
        import re
        # Simple heuristic: look for rows with known end-use names
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', content, re.DOTALL | re.IGNORECASE)
        for row in rows:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
            if not cells:
                continue
            label = re.sub(r'<[^>]+>', '', cells[0]).strip().lower()
            # Try to get the total column (last numeric cell)
            nums = []
            for c in cells[1:]:
                txt = re.sub(r'<[^>]+>', '', c).strip().replace(',', '')
                try:
                    nums.append(float(txt))
                except ValueError:
                    pass
            if not nums:
                continue
            total_j = nums[-1]
            total_kwh = total_j * j_to_kwh
            if 'heat' in label:
                end_uses['heating'] += total_kwh
            elif 'cool' in label:
                end_uses['cooling'] += total_kwh
            elif 'water' in label or 'dhw' in label or 'service' in label:
                end_uses['dhw'] += total_kwh
            elif 'light' in label:
                end_uses['lighting'] += total_kwh
            elif 'plug' in label or 'equipment' in label:
                end_uses['plug_loads'] += total_kwh
    except Exception:
        pass
    return end_uses

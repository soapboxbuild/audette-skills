"""
Scenario Engine — Orchestrates 4-scenario energy code compliance analysis.

Generates and executes 4 scenarios in parallel:
1. Baseline - Actual building as-is
2. Reference - ASHRAE 90.1 Appendix G baseline
3. 90.1-2022 - Code-compliant prescriptive design
4. Retrofit - Baseline + ECMs from Audette MCP
"""

import copy
import json
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Dict, Any, List, Optional

from lib.idf_generator import IDFGenerator
from lib.simulation_runner import SimulationRunner

logger = logging.getLogger(__name__)

# System type fuel mappings for tracking energy sources across scenarios
SYSTEM_TYPE_REGISTRY = {
    "gas_boiler": {
        "heating_fuel": "NaturalGas",
        "cooling_fuel": "Electricity",
        "dhw_fuel": "NaturalGas"
    },
    "heat_pump": {
        "heating_fuel": "Electricity",
        "cooling_fuel": "Electricity",
        "dhw_fuel": "Electricity"
    },
    "pthp": {
        "heating_fuel": "Electricity",
        "cooling_fuel": "Electricity",
        "dhw_fuel": "NaturalGas"
    },
    "electric_resistance": {
        "heating_fuel": "Electricity",
        "cooling_fuel": "Electricity",
        "dhw_fuel": "Electricity"
    },
    "chiller_boiler": {
        "heating_fuel": "NaturalGas",
        "cooling_fuel": "Electricity",
        "dhw_fuel": "NaturalGas"
    },
    "district": {
        "heating_fuel": "Electricity",
        "cooling_fuel": "Electricity",
        "dhw_fuel": "Electricity"
    }
}


class ScenarioEngine:
    """Orchestrates 4-scenario energy code compliance analysis."""

    def __init__(self, building_model: Dict[str, Any], climate_zone: str):
        """
        Initialize scenario engine.

        Args:
            building_model: Validated building model from BuildingCollector
            climate_zone: ASHRAE climate zone (e.g., "5A")
        """
        self.building_model = building_model
        self.climate_zone = climate_zone

    def _generate_baseline_idf(self) -> str:
        """
        Generate baseline scenario IDF (actual building as-is).

        Returns:
            IDF content string
        """
        gen = IDFGenerator(self.building_model)
        return gen.generate()

    def _apply_appendix_g_rules(self, building_model: Dict) -> Dict:
        """
        Apply ASHRAE 90.1 Appendix G transformations to building model.

        Args:
            building_model: Building model dict (will be modified in-place)

        Returns:
            Modified building_model
        """
        climate_zone = self.climate_zone
        building_type = building_model['project'].get('building_type', 'Office')
        area_ft2 = building_model['project'].get('conditioned_area_ft2', 50000)

        # Appendix G envelope values by climate zone (Table G3.1-5)
        appendix_g_envelope = {
            '5A': {
                'wall_u_factor': 0.124,  # Btu/h·ft²·°F
                'roof_u_factor': 0.063,
                'window_u_factor': 0.57,
                'window_shgc': 0.40
            },
            '4A': {
                'wall_u_factor': 0.124,
                'roof_u_factor': 0.063,
                'window_u_factor': 0.57,
                'window_shgc': 0.40
            }
        }

        # Get envelope values for this climate zone (default to 5A)
        envelope = appendix_g_envelope.get(climate_zone, appendix_g_envelope['5A'])

        # Apply envelope transformations
        for construction in building_model.get('constructions', []):
            construction['wall_r_value'] = 1.0 / envelope['wall_u_factor']
            construction['roof_r_value'] = 1.0 / envelope['roof_u_factor']

        for window in building_model.get('window_defs', []):
            window['u_factor'] = envelope['window_u_factor']
            window['shgc'] = envelope['window_shgc']

        # Determine HVAC system type based on building type and area (Table G3.1.1)
        if building_type == 'Residential':
            system_type = 'PTAC'
            heating_cop = 3.3
            cooling_eer = 10.0
        elif area_ft2 < 25000:
            system_type = 'PSZ-AC'
            heating_cop = 3.3
            cooling_eer = 11.0
        elif area_ft2 < 150000:
            system_type = 'Packaged VAV'
            heating_cop = 3.3
            cooling_eer = 11.5
        else:
            system_type = 'VAV with reheat'
            heating_cop = 3.3
            cooling_eer = 12.0

        # Apply HVAC transformations (using IdealLoadsAirSystem with Appendix G efficiencies)
        for equipment in building_model.get('hvac_equipment', []):
            equipment['equipment_type'] = system_type
            equipment['heating_cop'] = heating_cop
            equipment['cooling_eer'] = cooling_eer

        return building_model

    def _generate_reference_idf(self) -> str:
        """
        Generate Reference scenario IDF (ASHRAE 90.1 Appendix G baseline).

        Returns:
            IDF content string
        """
        # Deep copy to avoid modifying original
        ref_model = copy.deepcopy(self.building_model)

        # Apply Appendix G transformations
        ref_model = self._apply_appendix_g_rules(ref_model)

        # Generate IDF
        gen = IDFGenerator(ref_model)
        return gen.generate()

    def _generate_code_2022_idf(self) -> str:
        """
        Generate 90.1-2022 scenario IDF (code-compliant prescriptive minimums).

        Returns:
            IDF content string
        """
        # Load prescriptive minimums from data file
        code_data_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'data',
            'ashrae_901_2022.json'
        )

        with open(code_data_path) as f:
            code_data = json.load(f)

        zone_data = code_data['climate_zones'].get(self.climate_zone)
        if not zone_data:
            raise ValueError(f"Climate zone {self.climate_zone} not found in ASHRAE 90.1-2022 data")

        # Deep copy building model
        code_model = copy.deepcopy(self.building_model)

        # Apply envelope minimums
        for construction in code_model.get('constructions', []):
            construction['wall_r_value'] = zone_data['envelope']['wall_r_value']
            construction['roof_r_value'] = zone_data['envelope']['roof_r_value']
            construction['slab_r_value'] = zone_data['envelope']['slab_r_value']

        for window in code_model.get('window_defs', []):
            window['u_factor'] = zone_data['envelope']['window_u_factor']
            window['shgc'] = zone_data['envelope']['window_shgc']

        # Apply HVAC minimums
        for equipment in code_model.get('hvac_equipment', []):
            equipment['heating_cop'] = zone_data['systems']['heating_cop_min']
            equipment['cooling_eer'] = zone_data['systems']['cooling_eer_min']

        # Apply lighting minimums
        building_type = code_model['project']['building_type'].lower()
        lpd_key = f"{building_type}_lpd"
        if lpd_key in zone_data['lighting']:
            code_model['project']['lighting_lpd'] = zone_data['lighting'][lpd_key]

        # Generate IDF
        gen = IDFGenerator(code_model)
        return gen.generate()

    def _apply_retrofit_measures(
        self,
        building_model: Dict,
        measures: List[Dict]
    ) -> Dict:
        """
        Apply retrofit measures (ECMs) to building model.

        Args:
            building_model: Building model dict (will be modified in-place)
            measures: List of retrofit measure dicts with measure_type and parameters

        Returns:
            Modified building_model
        """
        for measure in measures:
            measure_type = measure.get('measure_type')
            params = measure.get('parameters', {})

            if measure_type == 'envelope_upgrade':
                # Apply to all constructions
                for construction in building_model.get('constructions', []):
                    if 'wall_r_value' in params:
                        construction['wall_r_value'] = params['wall_r_value']
                    if 'roof_r_value' in params:
                        construction['roof_r_value'] = params['roof_r_value']
                    if 'slab_r_value' in params:
                        construction['slab_r_value'] = params['slab_r_value']

                # Apply to windows
                for window in building_model.get('window_defs', []):
                    if 'window_u_factor' in params:
                        window['u_factor'] = params['window_u_factor']
                    if 'window_shgc' in params:
                        window['shgc'] = params['window_shgc']

            elif measure_type == 'hvac_replacement':
                # Apply to all equipment
                for equipment in building_model.get('hvac_equipment', []):
                    if 'heating_cop' in params:
                        equipment['heating_cop'] = params['heating_cop']
                    if 'cooling_eer' in params:
                        equipment['cooling_eer'] = params['cooling_eer']

            elif measure_type == 'lighting_upgrade':
                # Apply to project-level LPD
                if 'lighting_lpd' in params:
                    building_model['project']['lighting_lpd'] = params['lighting_lpd']

        return building_model

    def _generate_retrofit_idf(self, measures: Optional[List[Dict]] = None) -> str:
        """
        Generate Retrofit scenario IDF (baseline + ECMs).

        Args:
            measures: Optional list of retrofit measures from Audette MCP

        Returns:
            IDF content string
        """
        if not measures:
            # No retrofit measures, return baseline
            return self._generate_baseline_idf()

        # Deep copy building model
        retrofit_model = copy.deepcopy(self.building_model)

        # Apply measures
        retrofit_model = self._apply_retrofit_measures(retrofit_model, measures)

        # Generate IDF
        gen = IDFGenerator(retrofit_model)
        return gen.generate()

    def _run_parallel_simulations(
        self,
        idf_dict: Dict[str, str],
        max_retries: int = 1
    ) -> Dict[str, Dict]:
        """
        Execute all scenarios in parallel using ThreadPoolExecutor.

        Args:
            idf_dict: Dict of scenario name -> IDF content string
            max_retries: Number of retries with parameter correction (default: 1)

        Returns:
            Dict of scenario name -> simulation results
        """
        runner = SimulationRunner()
        results = {}

        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submit all scenarios
            futures = {
                name: executor.submit(
                    runner.run_with_retry,
                    idf_content,
                    self.climate_zone,
                    max_retries=3  # SimulationRunner's internal retry
                )
                for name, idf_content in idf_dict.items()
            }

            # Wait for all to complete with progress logging
            import threading

            def log_progress():
                """Log progress every 2 seconds until all done."""
                while not all(f.done() for f in futures.values()):
                    time.sleep(2)
                    if not all(f.done() for f in futures.values()):
                        done_count = sum(1 for f in futures.values() if f.done())
                        logger.info(f"Scenarios complete: {done_count}/{len(futures)}")

            # Start progress logging in background
            progress_thread = threading.Thread(target=log_progress, daemon=True)
            progress_thread.start()

            # Wait for all futures to complete
            wait(futures.values())

            # Collect results
            for name, future in futures.items():
                try:
                    result = future.result()

                    # If failed and retries allowed, attempt parameter correction
                    if not result['success'] and max_retries > 0:
                        logger.warning(f"{name} scenario failed, attempting parameter correction...")
                        corrected_idf = self._parse_error_and_correct(
                            result.get('error', ''),
                            result.get('fatal_errors', []),
                            idf_dict[name]
                        )

                        if corrected_idf:
                            # Retry with corrected IDF
                            logger.info(f"Retrying {name} with corrected IDF...")
                            result = runner.run_with_retry(
                                corrected_idf,
                                self.climate_zone,
                                max_retries=1
                            )
                            result['retry_attempted'] = True

                    results[name] = result

                except Exception as e:
                    logger.exception(f"Scenario {name} raised exception")
                    results[name] = {
                        'success': False,
                        'error': str(e),
                        'fatal_errors': [str(e)]
                    }

        return results

    def _parse_error_and_correct(
        self,
        error_msg: str,
        fatal_errors: List[str],
        idf_content: str
    ) -> Optional[str]:
        """
        Parse error message and attempt to correct IDF parameters.

        Args:
            error_msg: Error message string
            fatal_errors: List of fatal error strings
            idf_content: Original IDF content

        Returns:
            Corrected IDF string, or None if cannot correct
        """
        for error in fatal_errors:
            error_lower = error.lower()

            if "design heating load is zero" in error_lower:
                # Increase infiltration rate
                idf_content = re.sub(
                    r'(ZoneInfiltration:DesignFlowRate,.*?\n.*?Flow/ExteriorArea,\s*)(\d+\.?\d*)',
                    r'\g<1>0.0003',
                    idf_content,
                    flags=re.DOTALL
                )
                logger.info("Corrected: Increased infiltration to 0.3 ACH")
                return idf_content

            elif "window u-factor" in error_lower and "below" in error_lower:
                # Set to minimum valid value (0.5)
                idf_content = re.sub(
                    r'(WindowMaterial:SimpleGlazingSystem,.*?\n.*?U-Factor,\s*)(\d+\.?\d*)',
                    r'\g<1>0.5',
                    idf_content,
                    flags=re.DOTALL
                )
                logger.info("Corrected: Adjusted window U-factor to 0.5")
                return idf_content

            elif "window u-factor" in error_lower and "above" in error_lower:
                # Set to maximum valid value (1.2)
                idf_content = re.sub(
                    r'(WindowMaterial:SimpleGlazingSystem,.*?\n.*?U-Factor,\s*)(\d+\.?\d*)',
                    r'\g<1>1.2',
                    idf_content,
                    flags=re.DOTALL
                )
                logger.info("Corrected: Adjusted window U-factor to 1.2")
                return idf_content

        # No correction available
        return None

    def _calculate_deltas(
        self,
        baseline_results: Dict,
        scenario_results: Dict,
        scenario_name: str = ''
    ) -> Dict:
        """
        Calculate energy savings and compliance metrics vs baseline.

        Args:
            baseline_results: Baseline scenario results
            scenario_results: Scenario results to compare
            scenario_name: Scenario name (for compliance margin calculation)

        Returns:
            Dict with delta calculations
        """
        baseline_eui = baseline_results.get('eui_kwh_per_sf', 0)
        scenario_eui = scenario_results.get('eui_kwh_per_sf', 0)

        baseline_energy = baseline_results.get('total_site_energy_kwh', 0)
        scenario_energy = scenario_results.get('total_site_energy_kwh', 0)

        # Delta calculations (negative = savings)
        eui_delta = scenario_eui - baseline_eui
        eui_delta_pct = (eui_delta / baseline_eui) * 100 if baseline_eui > 0 else 0

        energy_savings_kwh = baseline_energy - scenario_energy
        energy_savings_pct = (energy_savings_kwh / baseline_energy) * 100 if baseline_energy > 0 else 0

        # End-use deltas
        end_use_deltas_kwh = {}
        baseline_end_uses = baseline_results.get('end_uses_kwh', {})
        scenario_end_uses = scenario_results.get('end_uses_kwh', {})

        for end_use in baseline_end_uses:
            baseline_val = baseline_end_uses[end_use]
            scenario_val = scenario_end_uses.get(end_use, 0)
            end_use_deltas_kwh[end_use] = scenario_val - baseline_val

        # Cost estimate (simple: $0.12/kWh)
        cost_savings_annual = energy_savings_kwh * 0.12

        deltas = {
            'eui_delta_kwh_per_sf': round(eui_delta, 2),
            'eui_delta_pct': round(eui_delta_pct, 1),
            'energy_savings_kwh': round(energy_savings_kwh, 0),
            'energy_savings_pct': round(energy_savings_pct, 1),
            'end_use_deltas_kwh': {k: round(v, 0) for k, v in end_use_deltas_kwh.items()},
            'cost_savings_annual': round(cost_savings_annual, 2)
        }

        # Special calculation for code_2022: compliance margin
        if scenario_name == 'code_2022':
            # Compliance margin: positive = building exceeds code (NON-COMPLIANT)
            # eui_delta = code_eui - baseline_eui
            # If baseline=70, code=60: delta=-10, margin=+14.3% → baseline EXCEEDS → NON-COMPLIANT
            # If baseline=50, code=60: delta=+10, margin=-16.7% → baseline below → COMPLIANT
            compliance_margin_pct = eui_delta_pct
            deltas['compliance_margin_pct'] = round(compliance_margin_pct, 1)

        return deltas

    def generate_all_scenarios(
        self,
        retrofit_measures: Optional[List[Dict]] = None
    ) -> Dict[str, str]:
        """
        Generate IDF content for all 4 scenarios.

        Args:
            retrofit_measures: Optional list of ECMs from Audette MCP

        Returns:
            Dict mapping scenario name to IDF content string
        """
        logger.info("Generating all 4 scenarios...")

        idf_dict = {
            'baseline': self._generate_baseline_idf(),
            'reference': self._generate_reference_idf(),
            'code_2022': self._generate_code_2022_idf(),
            'retrofit': self._generate_retrofit_idf(retrofit_measures)
        }

        logger.info("All scenarios generated")
        return idf_dict

    def run_all_scenarios(
        self,
        idf_dict: Dict[str, str],
        max_retries: int = 1
    ) -> Dict[str, Any]:
        """
        Execute all scenarios in parallel and aggregate results.

        Args:
            idf_dict: Dict of scenario name -> IDF content
            max_retries: Number of retries with parameter correction (default: 1)

        Returns:
            Aggregated results dict with baseline-anchored deltas
        """
        import datetime

        logger.info("Running all scenarios in parallel...")

        # Execute simulations
        sim_results = self._run_parallel_simulations(idf_dict, max_retries)

        # Aggregate results
        aggregated = {}
        baseline_results = sim_results.get('baseline', {})
        baseline_success = baseline_results.get('success', False)

        # Process each scenario
        for scenario_name in ['baseline', 'reference', 'code_2022', 'retrofit']:
            scenario_result = sim_results.get(scenario_name, {})

            if scenario_name == 'baseline':
                # Baseline: raw metrics only
                aggregated[scenario_name] = {
                    'success': scenario_result.get('success', False),
                    'raw': scenario_result if scenario_result.get('success') else {}
                }
                if not scenario_result.get('success'):
                    aggregated[scenario_name]['error'] = scenario_result.get('error')
                    aggregated[scenario_name]['fatal_errors'] = scenario_result.get('fatal_errors', [])
            else:
                # Other scenarios: raw + deltas (if baseline succeeded)
                aggregated[scenario_name] = {
                    'success': scenario_result.get('success', False),
                    'raw': scenario_result if scenario_result.get('success') else {}
                }

                if not scenario_result.get('success'):
                    aggregated[scenario_name]['error'] = scenario_result.get('error')
                    aggregated[scenario_name]['fatal_errors'] = scenario_result.get('fatal_errors', [])
                    if 'retry_attempted' in scenario_result:
                        aggregated[scenario_name]['retry_attempted'] = True
                elif baseline_success:
                    # Calculate deltas vs baseline
                    aggregated[scenario_name]['vs_baseline'] = self._calculate_deltas(
                        baseline_results,
                        scenario_result,
                        scenario_name
                    )

        # Add system type information for fuel tracking
        retrofit_measures = []  # Would come from method parameter if available
        baseline_system = self.building_model.get("systems", {}).get("system_type", "gas_boiler")
        code_system = "heat_pump"  # ASHRAE 90.1-2022 prescriptive
        retrofit_system = "pthp"  # Default if no retrofit measures specified
        if retrofit_measures and len(retrofit_measures) > 0:
            retrofit_system = retrofit_measures[0].get("parameters", {}).get("system_type", "pthp")

        aggregated['system_info'] = {
            "baseline_system": baseline_system,
            "code_system": code_system,
            "retrofit_system": retrofit_system
        }

        # Add metadata
        aggregated['metadata'] = {
            'building_uid': self.building_model.get('building_uid', 'unknown'),
            'building_name': self.building_model.get('project', {}).get('name', 'Unknown'),
            'climate_zone': self.climate_zone,
            'simulation_date': datetime.datetime.now().isoformat(),
            'appendix_g_simplifications': [
                'Single orientation (baseline orientation used, not 4-orientation average)'
            ]
        }

        # Add warnings if baseline failed
        if not baseline_success:
            aggregated['metadata']['warnings'] = [
                'Baseline scenario failed - delta calculations unavailable'
            ]

        logger.info("Results aggregation complete")
        return aggregated

    def _calc_polygon_area(self, vertices: List[List[float]]) -> float:
        """
        Calculate polygon area using shoelace formula.

        Args:
            vertices: List of [x, y, z] coordinates

        Returns:
            Area in square meters
        """
        n = len(vertices)
        if n < 3:
            return 0.0

        # Use first two dimensions (x, y) for area
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += vertices[i][0] * vertices[j][1]
            area -= vertices[j][0] * vertices[i][1]

        return abs(area) / 2.0

    def visualize_idf(self, idf_content: str, scenario_name: str) -> str:
        """
        Generate interactive 3D geometry visualization for an IDF.

        Args:
            idf_content: IDF file content as string
            scenario_name: Scenario identifier (baseline, reference, etc.)

        Returns:
            HTML artifact content for display in conversation

        Raises:
            ValueError: If IDF parsing fails
        """
        from pathlib import Path
        import tempfile
        from datetime import datetime
        from jinja2 import Environment, FileSystemLoader
        from geometry_parser import parse_idf_geometry

        # Write IDF to temp file for parser
        with tempfile.NamedTemporaryFile(mode='w', suffix='.idf', delete=False) as f:
            f.write(idf_content)
            temp_path = f.name

        try:
            # Parse geometry
            geometry = parse_idf_geometry(temp_path)

            # Calculate total surface area
            total_area = sum(
                self._calc_polygon_area(surf['vertices'])
                for surf in geometry['surfaces']
            )

            # Render template
            template_dir = Path(__file__).parent / 'templates'
            env = Environment(loader=FileSystemLoader(str(template_dir)))
            template = env.get_template('geometry_viewer.html.j2')

            html = template.render(
                building_name=self.building_model.get('project', {}).get('name', 'Building'),
                scenario=scenario_name,
                geometry=geometry,
                metadata={
                    'total_surface_area_m2': total_area,
                    'zone_count': geometry['zone_count'],
                    'generation_timestamp': datetime.now().isoformat()
                }
            )

            return html

        finally:
            # Clean up temp file
            Path(temp_path).unlink()

    def save_idf_files(
        self,
        idf_dict: Dict[str, str],
        output_dir: str = '.'
    ) -> Dict[str, str]:
        """
        Save baseline and ASHRAE 90.1-2022 IDF files to disk.

        Args:
            idf_dict: Dictionary mapping scenario names to IDF content
                     (e.g., {'baseline': '...', 'code_2022': '...'})
            output_dir: Directory to save files (default: current directory)

        Returns:
            Dictionary mapping scenario names to saved file paths

        Raises:
            ValueError: If required scenarios are missing from idf_dict
        """
        from pathlib import Path

        # Validate required scenarios
        if 'baseline' not in idf_dict:
            raise ValueError("idf_dict must contain 'baseline' scenario")
        if 'code_2022' not in idf_dict:
            raise ValueError("idf_dict must contain 'code_2022' scenario")

        # Get building name for filenames
        building_name = self.building_model.get('project', {}).get('name', 'Building')
        # Sanitize building name for filesystem
        safe_name = building_name.replace(' ', '_').replace('/', '_')

        # Create output directory if needed
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save files
        saved_files = {}

        baseline_filename = f"{safe_name}_baseline.idf"
        baseline_path = output_path / baseline_filename
        baseline_path.write_text(idf_dict['baseline'])
        saved_files['baseline'] = str(baseline_path.absolute())

        code_2022_filename = f"{safe_name}_90.1_2022.idf"
        code_2022_path = output_path / code_2022_filename
        code_2022_path.write_text(idf_dict['code_2022'])
        saved_files['code_2022'] = str(code_2022_path.absolute())

        return saved_files

    def inject_audette_retrofit(
        self,
        results: Dict[str, Any],
        platform_retrofit_kwh: float,
        audette_solar_kwh: float,
        gfa_ft2: float
    ) -> Dict[str, Any]:
        """
        Replace EnergyPlus retrofit result with Audette MCP plan data.

        This method constructs a retrofit scenario result from the Audette
        Recommendations plan instead of running an EnergyPlus simulation.
        The end-use breakdown is a proportional approximation for visualization.

        Args:
            results: Existing results dict from run_all_scenarios()
            platform_retrofit_kwh: Net site energy from Audette plan (after solar)
            audette_solar_kwh: Solar generation from Audette plan (positive kWh)
            gfa_ft2: Building gross floor area in square feet

        Returns:
            Updated results dict with Audette retrofit scenario
        """
        BTU_PER_WH = 3.412141

        baseline_raw = results["baseline"]["raw"]
        baseline_total = baseline_raw["total_site_energy_kwh"]

        # Gross retrofit consumption = net + solar (before solar credit)
        gross_retrofit_kwh = platform_retrofit_kwh + audette_solar_kwh
        scale_factor = gross_retrofit_kwh / baseline_total

        # Scale end uses proportionally (visualization only - not physically accurate)
        if scale_factor <= 1.0:
            # Normal case: retrofit reduces consumption
            retrofit_eu = {
                k: v * scale_factor
                for k, v in baseline_raw.get("end_uses_kwh", {}).items()
            }
        else:
            # Degenerate case: retrofit increases consumption (should not happen for valid plans)
            # Show as single undifferentiated block instead of scaled breakdown
            logger.warning(
                f"Audette retrofit gross consumption ({gross_retrofit_kwh:.0f} kWh) "
                f"exceeds baseline ({baseline_total:.0f} kWh). "
                f"End-use breakdown unavailable - showing as single block."
            )
            retrofit_eu = {"audette_plan_total": float(platform_retrofit_kwh)}

        # Add solar as negative credit
        retrofit_eu["solar_generation"] = -float(audette_solar_kwh)

        # Construct retrofit result
        results["retrofit"] = {
            "success": True,
            "raw": {
                "total_site_energy_kwh": float(platform_retrofit_kwh),
                "conditioned_area_ft2": float(gfa_ft2),
                "eui_kwh_per_sf": platform_retrofit_kwh / gfa_ft2,
                "eui_kbtu_per_sf": platform_retrofit_kwh * BTU_PER_WH / gfa_ft2,
                "total_site_energy_kbtu": platform_retrofit_kwh * BTU_PER_WH,
                "end_uses_kwh": retrofit_eu,
                "source": "Audette Recommendations Plan (MCP)",
            }
        }

        # Calculate deltas vs baseline
        if results["baseline"].get("success"):
            results["retrofit"]["vs_baseline"] = self._calculate_deltas(
                baseline_raw,
                results["retrofit"]["raw"],
                "retrofit"
            )

        logger.info(
            f"Injected Audette retrofit: {platform_retrofit_kwh:.0f} kWh net, "
            f"{audette_solar_kwh:.0f} kWh solar, scale_factor={scale_factor:.3f}"
        )

        return results

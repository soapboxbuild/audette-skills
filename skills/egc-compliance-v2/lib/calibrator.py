"""
Calibrates the as-built EnergyPlus model to match Audette utility actuals.

Calibration parameters (in priority order):
1. infiltration_ach (primary) — range 0.15 to 0.80
2. plug_load_w_ft2 (secondary) — range 0.50 to 1.20

Target: simulated total site kWh/yr within ±3% of Audette actuals
(electric + gas converted to kWh using 1 therm = 29.3 kWh)

DO NOT calibrate by adjusting DHW efficiency, HVAC efficiency, or envelope.
Those parameters are scenario-specific and must not be used as calibration knobs.
"""

MAX_ITERATIONS = 15
TOLERANCE_PCT = 3.0


class Calibrator:
    def __init__(self, building: dict, base_dir):
        self.b = building
        self.base_dir = base_dir

    def calibrate(self, initial_idf_content: str) -> tuple:
        """
        Returns (calibrated_idf_content: str, calibration_log: dict)
        """
        from lib.energyplus_runner import EnergyPlusRunner

        runner = EnergyPlusRunner(self.base_dir)

        target_kwh = (
            self.b['utility_electric_kwh_yr'] +
            self.b['utility_gas_kwh_yr']  # Already converted to kWh
        )
        gfa = self.b['gfa_ft2']
        target_eui = target_kwh / gfa

        # Initial calibration parameters
        infiltration = 0.35  # ACH starting point
        plug_load = 0.75     # W/ft2 starting point

        current_idf = initial_idf_content
        sim_kwh = 0.0
        error_pct = 0.0

        for i in range(MAX_ITERATIONS):
            # Update IDF with current calibration params
            current_idf = _inject_calibration_params(
                initial_idf_content, infiltration, plug_load
            )

            # Run simulation
            result = runner.run_string(current_idf)
            sim_kwh = result['total_site_kwh_yr']
            error_pct = (sim_kwh - target_kwh) / target_kwh * 100

            if abs(error_pct) <= TOLERANCE_PCT:
                return current_idf, {
                    'target_kwh_yr': target_kwh,
                    'final_kwh_yr': sim_kwh,
                    'target_eui_kwh_ft2': target_eui,
                    'final_eui_kwh_ft2': sim_kwh / gfa,
                    'error_pct': error_pct,
                    'iterations': i + 1,
                    'final_infiltration_ach': infiltration,
                    'final_plug_load_w_ft2': plug_load,
                    'converged': True,
                }

            # Adjust params
            if sim_kwh > target_kwh:
                # Too high: reduce infiltration first, then plug loads
                if infiltration > 0.20:
                    infiltration *= 0.95
                else:
                    plug_load *= 0.97
            else:
                # Too low: increase infiltration
                if infiltration < 0.60:
                    infiltration *= 1.05
                else:
                    plug_load *= 1.03

        # Did not converge — return best effort
        return current_idf, {
            'target_kwh_yr': target_kwh,
            'final_kwh_yr': sim_kwh,
            'target_eui_kwh_ft2': target_eui,
            'final_eui_kwh_ft2': sim_kwh / gfa,
            'error_pct': error_pct,
            'iterations': MAX_ITERATIONS,
            'final_infiltration_ach': infiltration,
            'final_plug_load_w_ft2': plug_load,
            'converged': False,
        }


def _inject_calibration_params(idf_content: str, infiltration_ach: float, plug_load_w_ft2: float) -> str:
    """
    Replace sentinel values in IDF string.
    CALIBRATION_INFILTRATION_ACH → actual ACH
    CALIBRATION_PLUG_LOAD_W_M2  → actual W/m2
    """
    plug_load_w_m2 = plug_load_w_ft2 * 10.764
    idf = idf_content.replace('CALIBRATION_INFILTRATION_ACH', f'{infiltration_ach:.4f}')
    idf = idf.replace('CALIBRATION_PLUG_LOAD_W_M2', f'{plug_load_w_m2:.4f}')
    return idf

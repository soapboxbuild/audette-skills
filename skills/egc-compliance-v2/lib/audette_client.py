"""
Wraps Audette MCP tool calls with consistent error handling.
All method names are stable; internal tool call strings may need updating
if Audette MCP tool names change.
"""

import json
import subprocess


class AudetteClient:
    """
    In Claude Code context, call Audette MCP tools directly using the
    available mcp__ tool functions. This class provides a clean interface.

    NOTE FOR CLAUDE CODE: Replace the _call() stub with direct MCP tool invocations.
    Example:
        mcp__claude_ai_Audette_AI__get_building_model_report(building_uid=uid)
    """

    def get_building_data(self, building_uid: str) -> dict:
        """
        Returns normalized building dict:
        {
          'name': str,
          'slug': str,          # filesystem-safe name, e.g. 'emanuelvillage'
          'address': str,
          'gfa_ft2': float,
          'stories': int,
          'climate_zone': str,  # e.g. '5A'
          'latitude': float,
          'longitude': float,
          'city': str,
          'state': str,
          'utility_electric_kwh_yr': float,
          'utility_gas_kwh_yr': float,   # converted from therms/CCF
          'eui_kwh_ft2': float,          # Audette platform EUI (calibration target)
          'hvac_type': str,              # 'ptac', 'split', 'vav', etc.
          'hvac_heating_fuel': str,      # 'gas', 'electric', 'heat_pump'
          'heating_efficiency': float,   # AFUE or COP
          'cooling_eer': float,
          'dhw_fuel': str,
          'dhw_efficiency': float,       # EF or COP
          'wall_u_ip': float,            # U-factor, IP units (Btu/hr·ft²·°F)
          'roof_u_ip': float,
          'window_u_ip': float,
          'window_shgc': float,
          'lighting_lpd_w_ft2': float,
          'infiltration_ach': float,     # To be set by calibrator
          'plug_load_w_ft2': float,      # To be set by calibrator
          'dhw_gal_unit_day': float,
          'units': int,
        }
        """
        # Call: get_building_model_report(building_uid=building_uid)
        # Also call: get_building_model_details(building_uid=building_uid) for envelope/systems
        raise NotImplementedError("Replace with MCP call")

    def list_plans(self, building_uid: str) -> list:
        """Returns list of plan dicts with at minimum: id, name, is_published, is_reported."""
        # Call: list_building_plans(building_model_uid=building_uid)
        raise NotImplementedError("Replace with MCP call")

    def get_plan(self, plan_id: str) -> dict:
        """Returns full plan dict including measures list."""
        # Call: get_carbon_reduction_plan_by_id(id=plan_id)
        raise NotImplementedError("Replace with MCP call")

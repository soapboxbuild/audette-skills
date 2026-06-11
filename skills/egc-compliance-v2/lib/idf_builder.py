"""
Builds EnergyPlus IDF content for 3 scenarios.

Key design decisions:
- 15-zone simplified box model (5 perimeter + core zones × N floors)
- All 3 scenarios share the same geometry
- Only systems/envelope parameters differ between scenarios
- code_min scenario MUST use 90.1-2016 prescriptive minimums (NOT as-built values)
- Site:Location uses the actual building lat/lon (NOT Boston defaults)
"""

import json
from pathlib import Path


# ASHRAE 90.1-2016 prescriptive minimums by climate zone
ASHRAE_901_2016 = {
    '5A': {
        'wall_u_ip': 0.064,
        'roof_u_ip': 0.027,
        'window_u_ip': 0.36,
        'window_shgc': 0.40,
        'ptac_eer': 12.0,
        'ptac_cop': 3.516,
        'boiler_afue': 0.82,
        'dhw_ef': 0.82,
        'lpd_w_ft2_dwelling': 0.60,
        'lpd_w_ft2_corridor': 0.41,
        'design_day_htg_db_c': -12.8,
        'design_day_clg_db_c': 32.2,
        'design_day_clg_wb_c': 22.8,
        'site_lat': 41.27,
        'site_lon': -72.89,
        'site_tz': -5,
        'site_elev_m': 7.0,
        'site_label': 'New Haven Tweed Airport',
        'epw_file': 'CT_New_Haven_725045_TMY3.epw',
    },
    '4A': {
        'wall_u_ip': 0.064,
        'roof_u_ip': 0.027,
        'window_u_ip': 0.40,
        'window_shgc': 0.40,
        'ptac_eer': 12.0,
        'ptac_cop': 3.516,
        'boiler_afue': 0.82,
        'dhw_ef': 0.82,
        'lpd_w_ft2_dwelling': 0.60,
        'lpd_w_ft2_corridor': 0.41,
        'design_day_htg_db_c': -4.4,
        'design_day_clg_db_c': 34.4,
        'design_day_clg_wb_c': 24.4,
        'site_lat': 38.95,
        'site_lon': -77.45,
        'site_tz': -5,
        'site_elev_m': 85.0,
        'site_label': 'Washington Dulles',
        'epw_file': 'VA_Sterling_724030_TMY3.epw',
    },
}


class IDFBuilder:
    def __init__(self, building: dict, base_dir: Path):
        self.b = building
        self.cz = building['climate_zone']
        self.code_params = ASHRAE_901_2016[self.cz]
        self.data_dir = base_dir / 'data'
        self.epw_dir = base_dir / 'data' / 'epw'

    def get_epw_path(self) -> Path:
        return self.epw_dir / self.code_params['epw_file']

    def _geometry_block(self) -> str:
        """
        Generate 15-zone box geometry for the building.
        5 zones per floor (N/S/E/W perimeter + core) × N floors.
        Perimeter zone depth: 15 ft. WWR: 0.30 default.
        """
        gfa = self.b['gfa_ft2']
        stories = self.b['stories']
        floor_gfa = gfa / stories

        aspect = 1.2
        width_ft = (floor_gfa / aspect) ** 0.5
        depth_ft = floor_gfa / width_ft

        floor_height_ft = 9.0
        perim_depth_ft = 15.0
        wwr = self.b.get('wwr', 0.30)

        # Convert to meters
        W = width_ft * 0.3048   # building width (E-W)
        D = depth_ft * 0.3048   # building depth (N-S)
        FH = floor_height_ft * 0.3048
        PD = perim_depth_ft * 0.3048

        lines = []

        # Zone names per floor
        zone_ids = ['N', 'S', 'E', 'W', 'C']

        # Define zones
        for floor in range(1, stories + 1):
            z0 = (floor - 1) * FH
            z1 = floor * FH
            for zid in zone_ids:
                zname = f"Zone_{zid}_F{floor}"
                lines.append(f"Zone, {zname};")

        lines.append("")

        # BuildingSurface:Detailed for each zone on each floor
        # Coordinate system: UpperLeftCorner, CounterClockWise, Relative
        # Building origin at SW corner (0,0,0)
        # X = East, Y = North, Z = Up

        surf_idx = [0]

        def surf(name, stype, construction, zone, outside_bc, sun_exp, wind_exp, vertices):
            surf_idx[0] += 1
            verts = '\n'.join(f"    {x:.4f}, {y:.4f}, {z:.4f}," for x, y, z in vertices)
            # Remove trailing comma from last vertex
            verts_lines = verts.rstrip(',')
            lines.append(f"""BuildingSurface:Detailed,
    {name},
    {stype},
    {construction},
    {zone},
    {outside_bc},
    ,
    {sun_exp},
    {wind_exp},
    autocalculate,
    {len(vertices)},
{verts_lines};
""")

        def fen(name, ftype, construction, host_surf, vertices):
            verts = '\n'.join(f"    {x:.4f}, {y:.4f}, {z:.4f}," for x, y, z in vertices)
            verts_lines = verts.rstrip(',')
            lines.append(f"""FenestrationSurface:Detailed,
    {name},
    {ftype},
    {construction},
    {host_surf},
    ,
    autocalculate,
    ,
    ,
    {len(vertices)},
{verts_lines};
""")

        for floor in range(1, stories + 1):
            z0 = (floor - 1) * FH
            z1 = floor * FH
            zc = z0  # floor base

            # Zone extents (meters from SW corner):
            # N zone: y from D-PD to D, x from 0 to W
            # S zone: y from 0 to PD, x from 0 to W
            # E zone: x from W-PD to W, y from PD to D-PD
            # W zone: x from 0 to PD, y from PD to D-PD
            # C zone: x from PD to W-PD, y from PD to D-PD

            zones_geom = {
                'N': (0, D - PD, W, D),
                'S': (0, 0, W, PD),
                'E': (W - PD, PD, W, D - PD),
                'W': (0, PD, PD, D - PD),
                'C': (PD, PD, W - PD, D - PD),
            }

            for zid in zone_ids:
                zname = f"Zone_{zid}_F{floor}"
                x0, y0, x1, y1 = zones_geom[zid]
                zw = x1 - x0
                zd = y1 - y0

                # Floor
                surf(f"Floor_{zid}_F{floor}", "Floor", "IntFloor", zname,
                     "Ground" if floor == 1 else "Zone",
                     "NoSun", "NoWind",
                     [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)])

                # Ceiling
                surf(f"Ceil_{zid}_F{floor}", "Ceiling", "Roof" if floor == stories else "IntFloor",
                     zname,
                     "Outdoors" if floor == stories else "Zone",
                     "SunExposed" if floor == stories else "NoSun",
                     "WindExposed" if floor == stories else "NoWind",
                     [(x0, y1, z1), (x1, y1, z1), (x1, y0, z1), (x0, y0, z1)])

                # Exterior walls for perimeter zones
                if zid == 'N':
                    # North wall (y = D)
                    sname = f"Wall_N_F{floor}"
                    surf(sname, "Wall", "ExtWall", zname, "Outdoors", "SunExposed", "WindExposed",
                         [(x0, D, z0), (x0, D, z1), (x1, D, z1), (x1, D, z0)])
                    # Window on N wall
                    wh = FH * wwr
                    wz0 = z0 + (FH - wh) / 2
                    wz1 = wz0 + wh
                    ww = zw * 0.8
                    wx0 = x0 + (zw - ww) / 2
                    fen(f"Win_N_F{floor}", "Window", "Window", sname,
                        [(wx0, D, wz0), (wx0, D, wz1), (wx0 + ww, D, wz1), (wx0 + ww, D, wz0)])

                elif zid == 'S':
                    # South wall (y = 0)
                    sname = f"Wall_S_F{floor}"
                    surf(sname, "Wall", "ExtWall", zname, "Outdoors", "SunExposed", "WindExposed",
                         [(x1, 0, z0), (x1, 0, z1), (x0, 0, z1), (x0, 0, z0)])
                    wh = FH * wwr
                    wz0 = z0 + (FH - wh) / 2
                    wz1 = wz0 + wh
                    ww = zw * 0.8
                    wx0 = x0 + (zw - ww) / 2
                    fen(f"Win_S_F{floor}", "Window", "Window", sname,
                        [(wx0 + ww, 0, wz0), (wx0 + ww, 0, wz1), (wx0, 0, wz1), (wx0, 0, wz0)])

                elif zid == 'E':
                    # East wall (x = W)
                    sname = f"Wall_E_F{floor}"
                    surf(sname, "Wall", "ExtWall", zname, "Outdoors", "SunExposed", "WindExposed",
                         [(W, y0, z0), (W, y0, z1), (W, y1, z1), (W, y1, z0)])
                    wh = FH * wwr
                    wz0 = z0 + (FH - wh) / 2
                    wz1 = wz0 + wh
                    ww = zd * 0.8
                    wy0 = y0 + (zd - ww) / 2
                    fen(f"Win_E_F{floor}", "Window", "Window", sname,
                        [(W, wy0, wz0), (W, wy0, wz1), (W, wy0 + ww, wz1), (W, wy0 + ww, wz0)])

                elif zid == 'W':
                    # West wall (x = 0)
                    sname = f"Wall_W_F{floor}"
                    surf(sname, "Wall", "ExtWall", zname, "Outdoors", "SunExposed", "WindExposed",
                         [(0, y1, z0), (0, y1, z1), (0, y0, z1), (0, y0, z0)])
                    wh = FH * wwr
                    wz0 = z0 + (FH - wh) / 2
                    wz1 = wz0 + wh
                    ww = zd * 0.8
                    wy0 = y0 + (zd - ww) / 2
                    fen(f"Win_W_F{floor}", "Window", "Window", sname,
                        [(0, wy0 + ww, wz0), (0, wy0 + ww, wz1), (0, wy0, wz1), (0, wy0, wz0)])

        return '\n'.join(lines)

    def _site_location_block(self) -> str:
        cp = self.code_params
        return f"""Site:Location,
    {cp['site_label']},
    {cp['site_lat']},   !- Latitude
    {cp['site_lon']},   !- Longitude
    {cp['site_tz']},    !- Time Zone
    {cp['site_elev_m']}; !- Elevation (m)
"""

    def _design_days_block(self) -> str:
        cp = self.code_params
        return f"""SizingPeriod:DesignDay,
    Htg 99.6pct Condns DB,
    1, 21, WinterDesignDay,
    {cp['design_day_htg_db_c']}, 0.0, , , WetBulb,
    {cp['design_day_htg_db_c']}, , , , , 99063, 5.8, 340,
    No, No, No, ASHRAEClearSky, , , , , 0.0;

SizingPeriod:DesignDay,
    Clg 1pct Condns DB,
    7, 21, SummerDesignDay,
    {cp['design_day_clg_db_c']}, 11.0, DefaultMultipliers, , WetBulb,
    {cp['design_day_clg_wb_c']}, , , , , 99063, 4.4, 230,
    No, No, No, ASHRAEClearSky, , , , , 1.0;
"""

    def _materials_block(self, scenario: str) -> str:
        if scenario == 'code_min':
            wall_u = self.code_params['wall_u_ip']
            roof_u = self.code_params['roof_u_ip']
            win_u = self.code_params['window_u_ip']
            win_shgc = self.code_params['window_shgc']
        else:
            wall_u = self.b['wall_u_ip']
            roof_u = self.b['roof_u_ip']
            win_u = self.b['window_u_ip']
            win_shgc = self.b['window_shgc']

        wall_r_si = (1.0 / wall_u) * 0.1761
        roof_r_si = (1.0 / roof_u) * 0.1761
        win_u_si = win_u * 5.678

        return f"""
Material:NoMass, Wall_Insulation, Rough, {wall_r_si:.4f}, 0.9, 0.6, 0.6;
Material:NoMass, Roof_Insulation, Rough, {roof_r_si:.4f}, 0.9, 0.6, 0.6;
Material, Concrete_Slab, MediumRough, 0.1, 0.51, 1200, 840, 0.9, 0.7, 0.7;

Construction, ExtWall, Wall_Insulation;
Construction, Roof, Roof_Insulation;
Construction, IntFloor, Concrete_Slab;

WindowMaterial:SimpleGlazingSystem,
    Window_Glazing, {win_u_si:.3f}, {win_shgc:.2f};

Construction, Window, Window_Glazing;
"""

    def _hvac_block(self, scenario: str) -> str:
        """Generate ZoneHVAC:PackagedTerminalAirConditioner for each zone."""
        if scenario == 'code_min':
            htg_eff = self.code_params['boiler_afue']
            clg_cop = self.code_params['ptac_eer'] / 3.412
        else:
            htg_eff = self.b['heating_efficiency']
            clg_cop = self.b['cooling_eer'] / 3.412

        stories = self.b['stories']
        zone_ids = ['N', 'S', 'E', 'W', 'C']
        lines = []

        # Always-on schedule
        lines.append("""Schedule:Compact,
    AlwaysOn, Fraction, Through:12/31, For:AllDays, Until:24:00, 1.0;
""")

        for floor in range(1, stories + 1):
            for zid in zone_ids:
                zname = f"Zone_{zid}_F{floor}"
                ptac_name = f"PTAC_{zid}_F{floor}"
                fan_name = f"{ptac_name}_Fan"
                htg_coil = f"{ptac_name}_HtgCoil"
                clg_coil = f"{ptac_name}_ClgCoil"
                inlet = f"{zname}_Inlet"
                outlet = f"{zname}_Outlet"

                lines.append(f"""Fan:OnOff,
    {fan_name},
    AlwaysOn,
    0.7,         !- Fan Efficiency
    75,          !- Pressure Rise Pa
    autosize,    !- Max Flow Rate m3/s
    0.9,         !- Motor Efficiency
    1.0,         !- Motor In Airstream Fraction
    {inlet},
    {fan_name}_Outlet;

Coil:Heating:Gas,
    {htg_coil},
    AlwaysOn,
    {htg_eff:.3f},   !- Gas Burner Efficiency
    autosize,    !- Nominal Capacity W
    {fan_name}_Outlet,
    {htg_coil}_Outlet;

Coil:Cooling:DX:SingleSpeed,
    {clg_coil},
    AlwaysOn,
    autosize,    !- Gross Rated Total Cooling Capacity W
    autosize,    !- Gross Rated Sensible Heat Ratio
    {clg_cop:.3f},   !- Gross Rated COP
    autosize,    !- Rated Air Flow Rate m3/s
    ,
    {htg_coil}_Outlet,
    {clg_coil}_Outlet,
    HPACCoolCapFT,
    HPACCoolCapFFF,
    HPACEIRFT,
    HPACEIRFFF,
    HPACPLFFPLR;

ZoneHVAC:PackagedTerminalAirConditioner,
    {ptac_name},
    AlwaysOn,
    {inlet},
    {outlet},
    ,            !- Outdoor Air Mixer Object Type
    ,            !- Outdoor Air Mixer Name
    autosize,    !- Cooling Supply Air Flow Rate m3/s
    autosize,    !- Heating Supply Air Flow Rate m3/s
    autosize,    !- No-Load Supply Air Flow Rate m3/s
    0.0,         !- Outdoor Air Flow Rate During Cooling
    0.0,         !- Outdoor Air Flow Rate During Heating
    0.0,         !- Outdoor Air Flow Rate No Load
    Fan:OnOff,
    {fan_name},
    Coil:Heating:Gas,
    {htg_coil},
    Coil:Cooling:DX:SingleSpeed,
    {clg_coil},
    ,
    ,
    CyclingFan;

ZoneHVAC:EquipmentList,
    {zname}_EquipList,
    SequentialLoad, SequentialLoad,
    ZoneHVAC:PackagedTerminalAirConditioner,
    {ptac_name},
    1, 1;

ZoneHVAC:EquipmentConnections,
    {zname},
    {zname}_EquipList,
    {inlet},
    ,
    {zname}_ZoneAirNode,
    {outlet};

NodeList,
    {inlet},
    {inlet};
""")

        # DX coil performance curves (required)
        lines.append("""Curve:Biquadratic,
    HPACCoolCapFT, 0.942587793, 0.009543347, 0.000683770, -0.011042676, 0.000005249, -0.000009720,
    17.22222, 21.66667, 18.33333, 46.11111, , , Dimensionless;

Curve:Quadratic,
    HPACCoolCapFFF, 0.8, 0.2, 0.0, 0.5, 1.5;

Curve:Biquadratic,
    HPACEIRFT, 0.342414409, -0.034885008, 0.000621416, 0.013605226, 0.000252809, -0.000320170,
    17.22222, 21.66667, 18.33333, 46.11111, , , Dimensionless;

Curve:Quadratic,
    HPACEIRFFF, 1.1552227, -0.1553227, 0.0, 0.5, 1.5;

Curve:Quadratic,
    HPACPLFFPLR, 0.85, 0.15, 0.0, 0.0, 1.0;
""")

        return '\n'.join(lines)

    def _dhw_block(self, scenario: str) -> str:
        """
        CRITICAL: code_min ALWAYS uses dhw_ef=0.82 (NOT as-built value).
        """
        if scenario == 'code_min':
            dhw_eff = self.code_params['dhw_ef']  # MUST be 0.82, not as-built
        else:
            dhw_eff = self.b['dhw_efficiency']

        daily_gal = self.b['dhw_gal_unit_day'] * self.b['units']
        flow_m3_s = (daily_gal * 3.785e-3) / 86400  # gal/day → m3/s

        return f"""
Schedule:Compact,
    DHW_Setpoint, Temperature, Through:12/31, For:AllDays,
    Until:24:00, 60.0;

Schedule:Compact,
    DHW_Flow, Dimensionless, Through:12/31, For:AllDays,
    Until:24:00, 1.0;

WaterHeater:Mixed,
    DHW_Heater,
    0.3,             !- Tank Volume m3
    DHW_Setpoint,    !- Setpoint Temp Schedule
    2.0,             !- Deadband Delta T (C)
    82.0,            !- Max Temp Limit (C)
    Cycle,           !- Heater Control Type
    6300,            !- Max Capacity W
    0.0,             !- Min Capacity W
    ,                !- Ignition Minimum Flow Rate
    0.0,             !- Ignition Delay
    Gas,             !- Heater Fuel Type
    {dhw_eff:.3f},   !- Heater Thermal Efficiency ({scenario.upper()} VALUE)
    ,                !- Part Load Factor Curve
    20,              !- Off Cycle Parasitic Fuel Consumption Rate W
    Gas,
    0.0,             !- Off Cycle Parasitic Heat Fraction to Tank
    15,              !- On Cycle Parasitic Fuel Consumption Rate W
    Gas,
    0.0,             !- On Cycle Parasitic Heat Fraction to Tank
    Zone,            !- Ambient Temp Indicator
    Zone_C_F1,       !- Ambient Temp Zone Name
    ,
    ,
    ,
    ,
    ,
    Mains;           !- Source Side Flow Control Mode

WaterUse:Equipment,
    DHW_Use,
    General,         !- End-Use Subcategory
    {flow_m3_s:.6f}, !- Peak Flow Rate m3/s
    DHW_Flow,        !- Flow Rate Schedule
    DHW_Setpoint,    !- Target Temp Schedule
    ,
    ,
    ,
    DHW_Heater;
"""

    def _lighting_block(self, scenario: str) -> str:
        """Generate Lights object per zone."""
        if scenario == 'code_min':
            lpd = self.code_params['lpd_w_ft2_dwelling']
        else:
            lpd = self.b['lighting_lpd_w_ft2']

        lpd_si = lpd * 10.764  # W/ft2 → W/m2

        stories = self.b['stories']
        zone_ids = ['N', 'S', 'E', 'W', 'C']
        lines = []

        lines.append("""Schedule:Compact,
    LightsSchedule, Fraction,
    Through:12/31,
    For:Weekdays, Until:08:00, 0.1, Until:22:00, 0.9, Until:24:00, 0.3,
    For:Weekends, Until:09:00, 0.1, Until:23:00, 0.8, Until:24:00, 0.3,
    For:Holidays, Until:24:00, 0.1;
""")

        for floor in range(1, stories + 1):
            for zid in zone_ids:
                zname = f"Zone_{zid}_F{floor}"
                lines.append(f"""Lights,
    Lights_{zid}_F{floor},
    {zname},
    LightsSchedule,
    Watts/Area,      !- Design Level Calculation Method
    ,
    {lpd_si:.4f},   !- Watts per Zone Floor Area W/m2
    ,
    0.0,             !- Return Air Fraction
    0.32,            !- Radiant Fraction
    0.25,            !- Visible Fraction
    General;
""")

        return '\n'.join(lines)

    def _plug_loads_block(self) -> str:
        """Generate ElectricEquipment (plug loads) per zone using calibration sentinel."""
        stories = self.b['stories']
        zone_ids = ['N', 'S', 'E', 'W', 'C']
        lines = []

        lines.append("""Schedule:Compact,
    PlugLoadSchedule, Fraction,
    Through:12/31,
    For:AllDays, Until:24:00, 1.0;
""")

        for floor in range(1, stories + 1):
            for zid in zone_ids:
                zname = f"Zone_{zid}_F{floor}"
                lines.append(f"""ElectricEquipment,
    PlugLoad_{zid}_F{floor},
    {zname},
    PlugLoadSchedule,
    Watts/Area,
    ,
    CALIBRATION_PLUG_LOAD_W_M2,   !- W/m2 (replaced by calibrator)
    ,
    0.0,
    0.3,
    0.0,
    General;
""")

        return '\n'.join(lines)

    def _infiltration_block(self) -> str:
        """Generate ZoneInfiltration:DesignFlowRate per zone using calibration sentinel."""
        stories = self.b['stories']
        zone_ids = ['N', 'S', 'E', 'W', 'C']
        lines = []

        lines.append("""Schedule:Compact,
    InfiltrationSchedule, Fraction,
    Through:12/31,
    For:AllDays, Until:24:00, 1.0;
""")

        for floor in range(1, stories + 1):
            for zid in zone_ids:
                zname = f"Zone_{zid}_F{floor}"
                lines.append(f"""ZoneInfiltration:DesignFlowRate,
    Infil_{zid}_F{floor},
    {zname},
    InfiltrationSchedule,
    AirChanges/Hour,
    ,
    ,
    ,
    CALIBRATION_INFILTRATION_ACH,   !- ACH (replaced by calibrator)
    0.0,
    0.0,
    0.0,
    0.0;
""")

        return '\n'.join(lines)

    def _output_requests_block(self) -> str:
        return """
Output:Variable, *, Zone Ideal Loads Heat Energy, Annual;
Output:Variable, *, Zone Ideal Loads Cool Energy, Annual;
Output:Meter, Electricity:Facility, Annual;
Output:Meter, NaturalGas:Facility, Annual;
Output:Meter, WaterSystems:NaturalGas, Annual;
OutputControl:Table:Style, HTML;
Output:Table:SummaryReports, AllSummary;
"""

    def _base_idf_header(self) -> str:
        return """Version, 24.1;
Timestep, 6;
GlobalGeometryRules, UpperLeftCorner, CounterClockWise, Relative;
SimulationControl, Yes, Yes, Yes, No, Yes;
RunPeriod, Annual, 1, 1, , 12, 31, , Sunday, Yes, Yes, No;
"""

    def build_as_built(self) -> str:
        return '\n'.join([
            self._base_idf_header(),
            f'Building, {self.b["slug"]}_AsBuilt, 0, City, 0.04, 0.4, FullExterior, 25, 6;',
            self._site_location_block(),
            self._design_days_block(),
            self._materials_block('as_built'),
            self._geometry_block(),
            self._hvac_block('as_built'),
            self._dhw_block('as_built'),
            self._lighting_block('as_built'),
            self._plug_loads_block(),
            self._infiltration_block(),
            self._output_requests_block(),
        ])

    def build_code_min(self) -> str:
        return '\n'.join([
            self._base_idf_header(),
            f'Building, {self.b["slug"]}_CodeMin901_2016, 0, City, 0.04, 0.4, FullExterior, 25, 6;',
            self._site_location_block(),
            self._design_days_block(),
            self._materials_block('code_min'),  # 90.1-2016 envelope
            self._geometry_block(),             # Same geometry as as-built
            self._hvac_block('code_min'),       # 90.1-2016 HVAC
            self._dhw_block('code_min'),        # 90.1-2016 DHW (EF=0.82) - CRITICAL
            self._lighting_block('code_min'),   # 90.1-2016 LPD
            self._plug_loads_block(),
            self._infiltration_block(),
            self._output_requests_block(),
        ])

    def build_retrofit(self, measures: list) -> str:
        return '\n'.join([
            self._base_idf_header(),
            f'Building, {self.b["slug"]}_Retrofit, 0, City, 0.04, 0.4, FullExterior, 25, 6;',
            self._site_location_block(),
            self._design_days_block(),
            self._materials_block('retrofit'),
            self._geometry_block(),
            self._hvac_block('retrofit'),
            self._dhw_block('retrofit'),
            self._lighting_block('retrofit'),
            self._plug_loads_block(),
            self._infiltration_block(),
            self._output_requests_block(),
        ])

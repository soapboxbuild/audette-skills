---
name: egc-compliance
description: >
  Run ASHRAE 90.1-2022 energy code compliance analysis with 4-scenario EnergyPlus 
  simulations. Generates interactive comparison artifacts showing baseline, reference, 
  code-compliant, and retrofit performance. Use when the user wants to check energy 
  code compliance, run code analysis, evaluate 90.1 performance, or compare building 
  scenarios for ASHRAE compliance.
---

# EGC Compliance Analysis

This skill performs conversational ASHRAE 90.1-2022 energy code compliance analysis using detailed EnergyPlus simulations. It coordinates four parallel scenarios — Baseline (as-is), Reference (Appendix G), 90.1-2022 Code Minimum, and Retrofit — and generates an interactive HTML artifact with charts, tables, and detailed metrics.

## When to Use

Use this skill when the user wants to:
- Check if a building meets ASHRAE 90.1-2022 energy code requirements
- Run energy code compliance analysis
- Compare building performance against code minimums
- Evaluate retrofit scenarios alongside code baselines
- Generate detailed energy modeling results with visual comparisons

Do NOT use this skill for:
- Simple energy queries (use Audette MCP `get_building_model_report` instead)
- Compliance with other codes (IECC, local amendments, etc.)
- Performance path modeling (this is prescriptive path only)

## When to Use

> **Note:** For quick compliance snapshots without EnergyPlus simulations, use  from the Audette MCP instead. This skill is for full ASHRAE 90.1-2022 EnergyPlus modeling with 4-scenario comparison.

## Prerequisites

### Required Software
- **EnergyPlus** must be installed. First-time setup takes 5-10 minutes (200MB download).
- **Python 3.8+** with dependencies from `requirements.txt`

### Required MCP Connections
- **Audette MCP** — Required for building data (`get_building_model_details`)
- **Report Factory MCP** — Optional, for generating compliance reports from results

### Required Workspace Setup
- `.audette-config.json` in project root with building UIDs cached
- Project must have at least one building created in Audette

## Model Calibration Requirements

**CRITICAL:** All EnergyPlus models must be calibrated to match Audette platform data exactly.

### 1. Baseline Model Calibration
The **Audette Baseline model** must calibrate exactly to the EUI (Energy Use Intensity) available on the Audette platform:

- Query `get_building_model_report` from Audette MCP to get the actual EUI
- Iteratively adjust EnergyPlus baseline model parameters until simulated EUI matches platform EUI within ±2%
- Calibration parameters (in order of impact):
  1. Infiltration rate (ACH)
  2. Internal loads (occupancy, equipment, lighting schedules)
  3. HVAC efficiency and operation schedules
  4. Envelope properties (if platform data allows adjustments)

**Validation:** Baseline EUI must match `building_model.energy_use_intensity` from Audette within tolerance before proceeding.

### 2. Reference and Code Model Derivation
The **EnergyPlus Reference model** and **90.1-2022 Code model** must use the calibrated Baseline configuration as their starting point:

- Start with the calibrated Baseline IDF
- Apply only the specific changes required by ASHRAE Appendix G (Reference) or 90.1-2022 prescriptive requirements (Code)
- Do NOT re-calibrate these models — they inherit the Baseline's calibration

**Purpose:** This ensures that differences between scenarios reflect only the code/reference requirements, not modeling inconsistencies.

### 3. Retrofit Model Calibration
The **Retrofit model** must be calibrated to the post-retrofit plan performance available on the Audette platform:

- Query `get_carbon_reduction_plan_by_id` from Audette MCP to get the planned retrofit measures and predicted post-retrofit EUI
- Apply the retrofit measures to the calibrated Baseline model
- Adjust retrofit performance parameters to match the platform's predicted post-retrofit EUI within ±3%
- If platform doesn't provide post-retrofit EUI, use the measure-specific savings from the platform's calculations

**Validation:** Retrofit EUI must match the platform's post-retrofit prediction before comparing against Reference/Code scenarios.

### Calibration Workflow Integration
Insert calibration between **Step 3: Data Collection** and **Step 6: Simulation Execution**:

1. Collect building data (Step 3)
2. **[NEW] Calibrate Baseline to platform EUI (Step 4)**
3. **[NEW] Verify Reference/Code derive from calibrated Baseline (Step 4)**
4. **[NEW] Calibrate Retrofit to platform post-retrofit predictions (Step 4)**
5. Prepare scenarios (Step 5)
6. Run scenarios with calibrated models (Step 6)

See detailed calibration procedures in the workflow section below.

## Workflow

### Step 1: Intent Detection and Building Resolution

When the user requests energy code compliance analysis, parse their natural language input to identify the target building. Common phrases:
- "Run energy compliance for [building name]"
- "Check if [address] meets 90.1"
- "Show 4-scenario comparison for [building]"
- "Analyze code compliance for the building at [address]"

**Resolution process:**

1. **Read workspace config**: Load `.audette-config.json` from the project root to get cached building list:
   ```python
   import json
   from pathlib import Path
   
   config_path = Path.cwd() / '.audette-config.json'
   config = json.load(open(config_path))
   buildings = config.get('buildings', [])
   ```

2. **Match user input**: Compare the user's input against building names, addresses, or UIDs in the cached list. Match flexibly (partial strings, address fragments, etc.).

3. **Handle ambiguity**:
   - If **multiple matches** found: Present options to user and ask them to choose
   - If **no matches** found: Check if config exists but is empty, then offer to run `audette-create-building` skill
   - If **config missing**: Tell user to run `workspace-setup` skill first

4. **Extract building UID**: Once resolved, extract the `building_uid` (or `building_model_uid`, used interchangeably) for data collection.

**Example conversational flow:**
> User: "Run energy compliance for 123 Main Street"
> 
> You: I found 123 Main Street (Office, 50,000 sf) in your workspace. I'll run ASHRAE 90.1-2022 compliance analysis for this building. This involves:
> - Collecting building data from Audette MCP
> - Running 4 parallel EnergyPlus simulations (~2-3 min)
> - Generating an interactive comparison artifact
> 
> Proceed?

### Step 2: Pre-flight Checks

Before collecting data or running simulations, verify all prerequisites are met.

#### 2.1 Check EnergyPlus Installation

```bash
which energyplus
```

**If not found:**
- Explain: "EnergyPlus is not installed. This is required for running energy simulations. First-time setup downloads ~200MB and takes 5-10 minutes."
- Ask: "Would you like me to install EnergyPlus now?"
- If approved, run:
  ```bash
  bash lib/install.sh
  ```
- After installation, verify with `which energyplus` again
- **Do not proceed** without user consent to install

#### 2.2 Verify Audette MCP Connectivity

```python
# Try calling a lightweight Audette MCP tool to verify connection
try:
    from mcp__claude_ai_Audette_AI__list_buildings import list_buildings
    buildings = list_buildings()
    # Connection verified
except Exception as e:
    # MCP is down or disconnected
    print(f"Cannot reach Audette MCP: {e}")
    # Tell user and STOP
```

**If MCP is unreachable:**
- "Cannot reach Audette MCP. This skill requires MCP for building data. Please reconnect Audette MCP in Cowork settings and try again."
- **Do not proceed** — this is a hard requirement

#### 2.3 Initialize DataManager

Create the SQLite database if it doesn't exist:

```python
from pathlib import Path
import sys

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / 'lib'))

from lib.data_manager import DataManager

# Create database in .audette subdirectory
db_dir = Path.cwd() / '.audette'
db_dir.mkdir(exist_ok=True)
db_path = db_dir / 'egc-compliance.db'

dm = DataManager(str(db_path))
print(f"Database initialized at {db_path}")
```

### Step 3: Data Collection

Use `BuildingCollector` to gather complete building data from multiple sources with cascading priority.

```python
from lib.building_collector import BuildingCollector

collector = BuildingCollector()
```

#### 3.1 Query Audette MCP

Start by querying the Audette MCP for building model details:

```python
building_uid = "building-12345"  # From Step 1

try:
    mcp_data = collector.query_mcp(building_uid)
    print("Querying Audette MCP... Retrieved:")
    # Show what was found: geometry, systems, envelope, etc.
except ValueError as e:
    print(f"MCP query failed: {e}")
    # Stop here if MCP is required
```

**Progress update to user:**
> "Querying Audette MCP... Found geometry (5,000 sf, 2 stories), HVAC systems (heat pump), but missing envelope details (wall R-value, window U-factor)."

#### 3.2 Identify Gaps

Check what's missing by comparing against the schema:

```python
gaps = collector.identify_gaps(mcp_data)

if gaps:
    print(f"Missing {len(gaps)} required fields:")
    for gap in gaps:
        print(f"  - {gap}")
```

#### 3.3 Extract from PDFs (if gaps exist)

If gaps are found, attempt to extract from PDF documents in the project:

```python
from pathlib import Path

# Find PDFs in project (common locations)
pdf_paths = list(Path.cwd().glob('**/*.pdf'))

for pdf_path in pdf_paths:
    if not gaps:
        break  # All gaps filled
    
    print(f"Extracting from {pdf_path.name}...")
    pdf_data = collector.extract_from_pdf(str(pdf_path))
    
    # Merge into building_data
    for section, section_data in pdf_data.items():
        if section not in building_data:
            building_data[section] = section_data
        elif isinstance(section_data, dict):
            building_data[section].update(section_data)
    
    # Re-check gaps
    gaps = collector.identify_gaps(building_data)
```

**Progress update:**
> "Extracting from CNA Report... Found envelope details (wall R-13, roof R-20, window U-0.35). Still missing: infiltration rate, lighting power density."

#### 3.4 Launch 3D Geometry Modeler (if needed)

If critical geometry fields are missing, offer the 3D modeler:

```python
needs_modeler = collector.needs_geometry_modeler(gaps)

if needs_modeler:
    print("Critical geometry fields are missing. Would you like to use the 3D geometry modeler?")
    print("This opens an interactive browser tool where you can define the building shape.")
    # If user approves, launch modeler (future implementation)
    # For now, skip and proceed to Q&A
```

#### 3.5 Fill Gaps via Interactive Q&A

For remaining gaps, generate user-friendly prompts and ask interactively:

```python
if gaps:
    prompts = collector.generate_qa_prompts(gaps)
    qa_responses = {}
    
    for gap_path, prompt_text in prompts.items():
        # Ask user conversationally
        print(f"\n{prompt_text}")
        user_input = input("> ")
        
        # Parse and store
        qa_responses[gap_path] = float(user_input)  # Adjust type as needed
    
    # Fill gaps with Q&A responses
    building_data = collector.fill_gaps_via_qa(building_data, gaps, qa_responses)
```

**Example conversational Q&A:**
> You: "I need the infiltration rate in ACH (air changes per hour). Typical range: 0.2-0.5 for tight construction, 0.5-1.0 for older buildings. What should I use?"
> 
> User: "0.3"
> 
> You: "Got it. What is the interior lighting power density in W/sqft? Typical for offices: 0.6-1.0 W/sqft."

#### 3.6 Validate Complete Model

After all collection steps, validate against the schema:

```python
is_valid, errors = collector.validate_complete_model(building_data)

if not is_valid:
    print("Model validation failed:")
    for error in errors:
        print(f"  - {error}")
    # Stop and ask user to correct
else:
    print("Building model validated successfully!")
```

#### 3.7 Show Data Source Summary

Provide transparency about where data came from:

```python
sources = collector.get_data_source_summary()

# Calculate percentages
total_fields = len(sources)
mcp_count = sum(1 for s in sources.values() if s == 'audette_mcp')
pdf_count = sum(1 for s in sources.values() if s == 'pdf')
qa_count = sum(1 for s in sources.values() if s == 'user_qa')

print(f"\nData sources: Audette MCP {mcp_count/total_fields*100:.0f}%, Documents {pdf_count/total_fields*100:.0f}%, User input {qa_count/total_fields*100:.0f}%")
```

**Progress update:**
> "Data collection complete. Sources: Audette MCP 75%, Documents 20%, User input 5%."

### Step 4: Model Calibration

**CRITICAL STEP:** Before running scenarios, calibrate the Baseline and Retrofit models to match Audette platform performance data.

#### 4.1 Retrieve Platform EUI (Baseline Target)

Query the actual building EUI from Audette platform:

```python
from mcp__claude_ai_Audette_AI__get_building_model_report import get_building_model_report

# Get actual building performance from platform
platform_data = get_building_model_report(building_uid)
platform_eui = platform_data.get('energy_use_intensity')  # kWh/sf-yr

if not platform_eui:
    print("⚠️  Platform EUI not available. Calibration cannot proceed.")
    print("Options:")
    print("  1. Upload utility data to Audette platform first")
    print("  2. Proceed without calibration (not recommended for compliance)")
    # Handle user choice...
else:
    print(f"Target Baseline EUI from platform: {platform_eui:.1f} kWh/sf-yr")
```

#### 4.2 Run Initial Baseline Simulation

Generate and run an uncalibrated Baseline IDF to establish starting point:

```python
from lib.scenario_engine import ScenarioEngine

engine = ScenarioEngine(building_data, climate_zone)

# Generate initial baseline IDF
initial_idf = engine._generate_baseline_idf()

# Run single simulation
baseline_result = engine.run_scenario('baseline', initial_idf)
initial_eui = baseline_result['raw']['eui_kwh_per_sf']

print(f"Initial simulated EUI: {initial_eui:.1f} kWh/sf-yr")
print(f"Target platform EUI: {platform_eui:.1f} kWh/sf-yr")
print(f"Calibration error: {abs(initial_eui - platform_eui) / platform_eui * 100:.1f}%")
```

#### 4.3 Iterative Calibration Loop (Baseline)

If error > 2%, enter calibration loop:

```python
calibration_params = {
    'infiltration_ach': building_data['envelope']['infiltration_ach'],
    'occupancy_density': building_data['internal_loads']['occupancy_density'],
    'equipment_lpd': building_data['internal_loads']['equipment_lpd'],
    'lighting_lpd': building_data['lighting']['interior_lpd_w_per_sqft']
}

tolerance_pct = 2.0
max_iterations = 10
iteration = 0

while abs(initial_eui - platform_eui) / platform_eui * 100 > tolerance_pct and iteration < max_iterations:
    iteration += 1
    print(f"\nCalibration iteration {iteration}:")
    
    # Calculate adjustment factors based on error direction
    error_ratio = platform_eui / initial_eui
    
    if initial_eui > platform_eui:
        # Simulated EUI too high → reduce loads
        print("  Simulated EUI too high. Reducing internal loads...")
        calibration_params['equipment_lpd'] *= 0.95
        calibration_params['occupancy_density'] *= 0.95
    else:
        # Simulated EUI too low → increase loads or infiltration
        print("  Simulated EUI too low. Increasing infiltration...")
        calibration_params['infiltration_ach'] *= 1.05
    
    # Update building_data with new params
    building_data['envelope']['infiltration_ach'] = calibration_params['infiltration_ach']
    building_data['internal_loads']['occupancy_density'] = calibration_params['occupancy_density']
    building_data['internal_loads']['equipment_lpd'] = calibration_params['equipment_lpd']
    
    # Regenerate and re-run
    engine = ScenarioEngine(building_data, climate_zone)
    calibrated_idf = engine._generate_baseline_idf()
    baseline_result = engine.run_scenario('baseline', calibrated_idf)
    initial_eui = baseline_result['raw']['eui_kwh_per_sf']
    
    error_pct = abs(initial_eui - platform_eui) / platform_eui * 100
    print(f"  New EUI: {initial_eui:.1f} kWh/sf-yr (error: {error_pct:.1f}%)")

if abs(initial_eui - platform_eui) / platform_eui * 100 <= tolerance_pct:
    print(f"\n✅ Baseline model calibrated successfully!")
    print(f"   Final EUI: {initial_eui:.1f} kWh/sf-yr")
    print(f"   Platform EUI: {platform_eui:.1f} kWh/sf-yr")
    print(f"   Error: {abs(initial_eui - platform_eui) / platform_eui * 100:.1f}%")
    
    # Save calibrated parameters
    calibrated_building_data = building_data.copy()
else:
    print(f"\n⚠️  Could not calibrate within {tolerance_pct}% after {max_iterations} iterations")
    print(f"   Final error: {abs(initial_eui - platform_eui) / platform_eui * 100:.1f}%")
    print("   Proceeding with best-effort calibration...")
```

**Progress update:**
> "Baseline calibration complete. Model matches platform EUI within 1.5% (45.2 vs 45.9 kWh/sf-yr)."

#### 4.4 Derive Reference and Code Models from Calibrated Baseline

**IMPORTANT:** Do NOT re-calibrate Reference or Code models. They must inherit the Baseline calibration:

```python
# Reference and Code models start from calibrated_building_data
reference_building_data = calibrated_building_data.copy()
code_building_data = calibrated_building_data.copy()

# Apply ONLY the specific code/reference requirements
# e.g., for ASHRAE Appendix G Reference building:
#   - Prescribed envelope values
#   - Prescribed HVAC efficiencies
#   - Prescribed lighting levels
# DO NOT adjust infiltration, occupancy, or other calibration parameters

print("Reference and Code models derived from calibrated Baseline")
print("  → Calibration inherited, only code requirements applied")
```

#### 4.5 Retrieve Platform Retrofit Predictions

Query planned retrofit performance:

```python
from mcp__claude_ai_Audette_AI__get_carbon_reduction_plan_by_id import get_carbon_reduction_plan_by_id

try:
    retrofit_plan = get_carbon_reduction_plan_by_id(building_uid)
    retrofit_measures = retrofit_plan.get('measures', [])
    
    # Get predicted post-retrofit EUI from platform
    platform_retrofit_eui = retrofit_plan.get('predicted_eui')  # kWh/sf-yr
    
    if platform_retrofit_eui:
        print(f"Target Retrofit EUI from platform: {platform_retrofit_eui:.1f} kWh/sf-yr")
    else:
        print("Platform doesn't provide post-retrofit EUI prediction")
        print("Using measure-specific savings instead")
        
except Exception as e:
    print(f"No retrofit plan found: {e}")
    retrofit_measures = None
    platform_retrofit_eui = None
```

#### 4.6 Calibrate Retrofit Model (if platform predictions available)

Similar to Baseline calibration, but targeting post-retrofit EUI:

```python
if platform_retrofit_eui and retrofit_measures:
    # Start from calibrated Baseline, apply retrofit measures
    retrofit_building_data = calibrated_building_data.copy()
    
    # Apply measures to building_data
    for measure in retrofit_measures:
        if measure['type'] == 'envelope_upgrade':
            retrofit_building_data['envelope']['wall_r_value'] = measure['new_r_value']
        elif measure['type'] == 'hvac_replacement':
            retrofit_building_data['systems']['heating_cop'] = measure['new_cop']
        # ... apply other measures
    
    # Run initial retrofit simulation
    engine_retrofit = ScenarioEngine(retrofit_building_data, climate_zone)
    retrofit_idf = engine._generate_retrofit_idf(retrofit_measures)
    retrofit_result = engine.run_scenario('retrofit', retrofit_idf)
    retrofit_eui = retrofit_result['raw']['eui_kwh_per_sf']
    
    # Calibration loop (if needed)
    tolerance_pct = 3.0  # Slightly higher tolerance for retrofit
    
    if abs(retrofit_eui - platform_retrofit_eui) / platform_retrofit_eui * 100 > tolerance_pct:
        print(f"\nRetrofit model needs calibration:")
        print(f"  Simulated: {retrofit_eui:.1f} kWh/sf-yr")
        print(f"  Platform prediction: {platform_retrofit_eui:.1f} kWh/sf-yr")
        
        # Adjust retrofit performance parameters to match platform
        # (Similar iteration loop as Baseline, but adjusting measure effectiveness)
        # ...
    
    print(f"\n✅ Retrofit model calibrated to platform predictions")
else:
    print("Retrofit scenario will use uncalibrated measure savings")
```

**Validation checkpoint:**
```python
# Before proceeding to full scenario runs, verify calibration
calibration_summary = {
    'baseline': {
        'simulated_eui': initial_eui,
        'platform_eui': platform_eui,
        'error_pct': abs(initial_eui - platform_eui) / platform_eui * 100
    }
}

if platform_retrofit_eui:
    calibration_summary['retrofit'] = {
        'simulated_eui': retrofit_eui,
        'platform_eui': platform_retrofit_eui,
        'error_pct': abs(retrofit_eui - platform_retrofit_eui) / platform_retrofit_eui * 100
    }

print("\n=== CALIBRATION SUMMARY ===")
for scenario, data in calibration_summary.items():
    print(f"{scenario.upper()}:")
    print(f"  Simulated: {data['simulated_eui']:.1f} kWh/sf-yr")
    print(f"  Platform: {data['platform_eui']:.1f} kWh/sf-yr")
    print(f"  Error: {data['error_pct']:.1f}%")
    
    if data['error_pct'] > 5:
        print(f"  ⚠️  WARNING: Calibration error exceeds 5%")

# Ask user to confirm before running full scenario suite
print("\nCalibration complete. Proceed with Reference and Code scenarios?")
```

### Step 5: Scenario Preparation

Load ASHRAE 90.1-2022 prescriptive requirements and prepare weather files.

#### 4.1 Determine Climate Zone

Extract climate zone from building data or ask user:

```python
climate_zone = building_data.get('climate_zone')

if not climate_zone:
    print("Climate zone not found. Common zones:")
    print("  5A = Chicago, NY, Boston")
    print("  4A = DC, Baltimore")
    print("  3A = Atlanta, Dallas")
    climate_zone = input("Enter climate zone: ")
```

#### 4.2 Load ASHRAE 90.1-2022 Requirements

```python
import json

code_data_path = Path(__file__).parent / 'data' / 'ashrae_901_2022.json'
with open(code_data_path) as f:
    code_data = json.load(f)

zone_reqs = code_data['climate_zones'].get(climate_zone)
print(f"Loaded ASHRAE 90.1-2022 requirements for climate zone {climate_zone}")
```

#### 4.3 Query Audette MCP for Retrofit Plan (Preferred)

**NEW APPROACH:** Fetch the Audette Recommendations plan directly instead of simulating retrofit with EnergyPlus. This is faster and more accurate.

```python
try:
    from mcp__claude_ai_Audette_AI__list_building_plans import list_building_plans
    from mcp__claude_ai_Audette_AI__get_carbon_reduction_plan_by_id import get_carbon_reduction_plan_by_id
    
    # List all plans for this building
    plans_response = list_building_plans(building_model_uid=building_uid)
    plans = plans_response.get('plans', [])
    
    # Find "Audette Recommendations" plan (or first non-budgeted plan)
    audette_plan = None
    for plan in plans:
        if plan.get('name') == 'Audette Recommendations':
            audette_plan = plan
            break
        elif not plan.get('is_budgeted', False) and audette_plan is None:
            audette_plan = plan  # Fallback to first non-budgeted
    
    if audette_plan:
        plan_id = audette_plan['id']
        plan_details = get_carbon_reduction_plan_by_id(id=plan_id)
        
        # Extract energy totals at target horizon (default: 2050)
        target_year = 2050
        platform_retrofit_kwh = plan_details.get('total_site_energy_kwh', 0)  # Net energy after solar
        audette_solar_kwh = plan_details.get('solar_generation_kwh', 0)  # Solar generation
        
        print(f"✓ Found Audette Recommendations plan (ID: {plan_id})")
        print(f"  Target year: {target_year}")
        print(f"  Net site energy: {platform_retrofit_kwh:,.0f} kWh/yr")
        print(f"  Solar generation: {audette_solar_kwh:,.0f} kWh/yr")
        
        use_audette_retrofit = True
        retrofit_measures = None  # Not needed when using Audette plan
    else:
        print("No Audette Recommendations plan found - will simulate retrofit with EnergyPlus")
        use_audette_retrofit = False
        retrofit_measures = None
except Exception as e:
    print(f"Could not fetch Audette plan: {e}")
    use_audette_retrofit = False
    retrofit_measures = None
```

**Note:** When `use_audette_retrofit = True`, skip generating the retrofit IDF. Only baseline, reference, and code_2022 scenarios will be simulated.

#### 4.4 Download Weather File

Use `WeatherManager` to get the weather file for this climate zone:

```python
from lib.weather_manager import WeatherManager

wm = WeatherManager()  # Uses ~/.audette/weather cache
epw_path = wm.get_weather_file(climate_zone)
print(f"Weather file ready: {epw_path}")
```

**Progress update:**
> "Preparing 4 scenarios: Baseline (as-is), Reference (Appendix G), 90.1-2022 Code Minimum, Retrofit. Weather file downloaded for climate zone 5A."

### Step 6: Simulation Execution

Run 4 parallel EnergyPlus simulations using `ScenarioEngine`.

#### 6.1 Initialize ScenarioEngine

```python
from lib.scenario_engine import ScenarioEngine

engine = ScenarioEngine(building_data, climate_zone)
```

#### 6.2 Generate Scenario IDFs and Verify Geometry

```python
print("Generating IDF files...")

if use_audette_retrofit:
    # Only generate baseline, reference, code_2022 (retrofit from Audette MCP)
    print("  - Baseline, Reference, Code 2022 (retrofit from Audette MCP)")
    idf_dict = {
        'baseline': engine._generate_baseline_idf(),
        'reference': engine._generate_reference_idf(),
        'code_2022': engine._generate_code_2022_idf()
    }
else:
    # Generate all 4 scenarios including EnergyPlus retrofit
    print("  - All 4 scenarios (including EnergyPlus retrofit)")
    idf_dict = engine.generate_all_scenarios(retrofit_measures=retrofit_measures)

print("IDF generation complete")

# NEW: Visualize baseline geometry for inspection
print("\n" + "="*60)
print("GEOMETRY VERIFICATION")
print("="*60)
print("\nVisualizing baseline geometry...")

viewer_html = engine.visualize_idf(
    idf_content=idf_dict['baseline'], 
    scenario_name='baseline'
)
print(viewer_html)  # Displays interactive 3D artifact

# NEW: User confirmation gate
print("\n⚠️  Please inspect the 3D geometry above.")
print("\nVerify:")
print("  • Overall building shape and proportions")
print("  • Number of stories matches expected")
print("  • Wall heights look correct")
print("  • Roof is properly positioned")
print("\nDoes the geometry look correct? (Type 'yes' to proceed, or describe issues)")

# Wait for user response in conversation
# If user confirms "yes", proceed to simulations
# If user identifies issues, adjust parameters and regenerate

print("\n✅ Geometry verified. Proceeding to simulations...")

# NEW: Save IDF files to project directory
print("\n" + "="*60)
print("SAVING IDF FILES")
print("="*60)

saved_files = engine.save_idf_files(idf_dict, output_dir='.')

print(f"\n✅ Saved IDF files:")
print(f"   • Baseline: {saved_files['baseline']}")
print(f"   • ASHRAE 90.1-2022: {saved_files['code_2022']}")
```

**Why:** The geometry visualization provides early error detection before expensive simulations. Users can catch modeling errors (wrong heights, incorrect footprints, missing surfaces) in seconds rather than waiting 2-3 minutes for simulation failures. After confirmation, IDF files are saved to the project directory for reference and potential reuse.

**User Experience:**
1. After IDF generation, 3D viewer automatically displays
2. User rotates/zooms to inspect building shape
3. User confirms geometry is correct
4. Baseline and ASHRAE 90.1-2022 IDF files are saved to current directory
5. Simulations proceed

**Error Recovery:**
If user spots geometry issues:
```python
# Example: User says "walls are too short"
print("\n🔧 Let's adjust the parameters.")
print("\nWhich aspect needs correction?")
print("  A) Building footprint (vertices)")
print("  B) Wall heights (floor-to-floor)")  
print("  C) Number of stories")
print("  D) Something else")

# User selects option B
print("\nCurrent floor-to-floor height: 10 ft")
print("Enter new floor-to-floor height (ft): ")
# User enters: 12

building_data['stories'][0]['floor_to_floor'] = 12

print("\nRegenerating IDF with corrected parameters...")
idf_dict['baseline'] = engine._generate_baseline_idf()

print("\nRe-visualizing geometry...")
viewer_html = engine.visualize_idf(idf_dict['baseline'], 'baseline')
print(viewer_html)

print("\nDoes the geometry look correct now?")
# Repeat until user confirms
```

#### 6.3 Run Parallel Simulations with Live Progress

```python
import time
from threading import Thread

print("Running simulations in parallel...")
print("This typically takes 2-3 minutes. Live updates below:")

# Start simulations
results = engine.run_all_scenarios(idf_dict, max_retries=1)
```

The `ScenarioEngine` handles:
- Parallel execution (4 workers)
- Live progress logging every 2 seconds
- Automatic retry on failure with parameter correction
- Error parsing from EnergyPlus `.err` files

**Progress updates (automatic from ScenarioEngine):**
> "Running simulations... Baseline (done), Reference (50%), 90.1-2022 (25%), Retrofit (pending)"
> 
> "Scenarios complete: 3/4"
> 
> "All simulations complete"

#### 5.4 Handle Simulation Failures

If any scenario fails, `ScenarioEngine` attempts automatic correction and retry. If failures persist:

```python
failed = [name for name, result in results.items() if not result.get('success')]

if failed:
    print(f"\nWarning: {len(failed)} scenario(s) failed:")
    for name in failed:
        error = results[name].get('error', 'Unknown error')
        fatal_errors = results[name].get('fatal_errors', [])
        
        print(f"\n{name.upper()} FAILED:")
        print(f"  Error: {error}")
        if fatal_errors:
            print(f"  Details: {fatal_errors[0]}")
        
        # Offer interactive debugging
        print("\nWould you like to:")
        print("  1. Adjust parameters and retry this scenario")
        print("  2. Continue with successful scenarios only")
        print("  3. Abort and review all inputs")
        
        # Handle user choice...
```

**Common failure modes and corrections:**

| Error | Automatic Fix | User Action if Fix Fails |
|-------|---------------|-------------------------|
| "Design heating load is zero" | Increase infiltration to 0.3 ACH | Review HVAC system definition |
| "Window U-factor below minimum" | Adjust to 0.5 | Verify window specs from documents |
| "HVAC sizing failure" | Increase equipment capacity | Check heating/cooling loads |

### Step 7: Results and Artifacts

After `run_all_scenarios()` returns, apply the calibration pipeline before building artifacts.

#### 7.1 Apply Calibration Pipeline

EnergyPlus IdealLoads output must be calibrated to match real equipment performance and platform baseline energy.

```python
from lib.calibration import calibrate_results
from lib.building_collector import BuildingCollector

BTU_PER_WH = 3.412141

# Pull values from building_model (already populated by BuildingCollector)
baseline_boiler_eff  = building_data.get("systems", {}).get("boiler_eff", 0.80)
baseline_cooling_eer = building_data.get("systems", {}).get("cooling_eer", 10.0)
retrofit_heating_cop = retrofit_measures[0]["parameters"].get("heating_cop", 2.5) if retrofit_measures else 3.3
retrofit_cooling_eer = retrofit_measures[0]["parameters"].get("cooling_eer", 11.0) if retrofit_measures else 11.0
code_heating_cop     = 3.3    # ASHRAE 90.1-2022 Table 6.8.1-3 Zone 5A; use ashrae_901_2022.json for other zones
code_cooling_eer     = 11.0   # ASHRAE 90.1-2022 Table 6.8.1-2; use ashrae_901_2022.json for other zones

baseline_cooling_cop = baseline_cooling_eer / BTU_PER_WH
code_cooling_cop     = code_cooling_eer     / BTU_PER_WH
retrofit_cooling_cop = retrofit_cooling_eer / BTU_PER_WH

scenario_heating_factors = {
    "baseline":  1.0 / baseline_boiler_eff,
    "reference": 1.0 / code_heating_cop,
    "code_2022": 1.0 / code_heating_cop,
    "retrofit":  1.0 / retrofit_heating_cop,
}
scenario_cooling_cops = {
    "baseline":  baseline_cooling_cop,
    "reference": code_cooling_cop,
    "code_2022": code_cooling_cop,
    "retrofit":  retrofit_cooling_cop,
}

# DHW: use BuildingCollector.estimate_dhw_thermal_kwh() added in Change 3
dhw_thermal_kwh    = BuildingCollector.estimate_dhw_thermal_kwh(building_data)
dhw_baseline_ef    = building_data.get("systems", {}).get("dhw_ef", 0.67)
dhw_code_cop       = 2.5   # HPWH COP; look up ashrae_901_2022.json["dhw_cop"] for zone
dhw_gas_kwh        = BuildingCollector.get_dhw_fuel_kwh(dhw_thermal_kwh, "gas", dhw_baseline_ef)
dhw_elec_kwh       = BuildingCollector.get_dhw_fuel_kwh(dhw_thermal_kwh, "heat_pump", dhw_code_cop)

scenario_dhw = {
    "baseline":  {"gas": dhw_gas_kwh,  "elec": 0.0},
    "reference": {"gas": 0.0,           "elec": dhw_elec_kwh},
    "code_2022": {"gas": 0.0,           "elec": dhw_elec_kwh},
    "retrofit":  {"gas": dhw_gas_kwh,  "elec": 0.0},
}

# platform_baseline_kwh comes from the Audette MCP:
# report = get_building_model_report(building_uid=building_uid)
# platform_baseline_kwh = report["total_annual_energy_kwh"]  (TMY-normalized)
gfa_ft2 = building_data["project"]["conditioned_area_ft2"]

results, cal_report = calibrate_results(
    results, gfa_ft2, platform_baseline_kwh,
    scenario_heating_factors, scenario_cooling_cops, scenario_dhw
)

print(f"Calibration applied:")
print(f"  Residual correction: {cal_report['_residual_kwh']:.1f} kWh/yr")
for scenario in ['baseline', 'reference', 'code_2022', 'retrofit']:
    if scenario in cal_report:
        print(f"  {scenario}: heat={cal_report[scenario]['heat_delta']:.0f}, cool={cal_report[scenario]['cool_delta']:.0f}, dhw={cal_report[scenario]['dhw_delta']:.0f} kWh")
```

#### 7.1b Inject Audette Retrofit (if using MCP plan)

If `use_audette_retrofit = True`, replace the EnergyPlus retrofit result with the Audette MCP plan:

```python
if use_audette_retrofit:
    # Inject Audette Recommendations plan as retrofit scenario
    results = engine.inject_audette_retrofit(
        results=results,
        platform_retrofit_kwh=platform_retrofit_kwh,
        audette_solar_kwh=audette_solar_kwh,
        gfa_ft2=gfa_ft2
    )
    
    print(f"\n✓ Audette retrofit injected:")
    print(f"  Net energy: {platform_retrofit_kwh:,.0f} kWh/yr")
    print(f"  Solar: {audette_solar_kwh:,.0f} kWh/yr")
    print(f"  EUI: {results['retrofit']['raw']['eui_kwh_per_sf']:.1f} kWh/sf-yr")
    print(f"  Source: {results['retrofit']['raw']['source']}")
```

**Note:** The end-use breakdown shown in the chart is a proportional approximation for visualization. The actual compliance verdict uses the MCP's net energy value directly.

**Note:** The `code_heating_cop` and `code_cooling_eer` values should ultimately be read from `data/ashrae_901_2022.json` keyed by `climate_zone`. The lookup pattern is:
```python
with open(data_dir / 'ashrae_901_2022.json') as f:
    code_data = json.load(f)
zone_data = code_data["climate_zones"][climate_zone]
code_heating_cop = zone_data["heat_pump_heating_cop"]
code_cooling_eer = zone_data["heat_pump_cooling_eer"]
```

#### 7.2 Save to Database

```python
import uuid
from datetime import datetime

# Create simulation run record
run_id = f"run-{uuid.uuid4().hex[:8]}"
dm.save_simulation_run({
    'run_id': run_id,
    'building_uid': building_uid,
    'status': 'complete',
    'error_log': None
})

# Save individual scenarios
for scenario_name in ['baseline', 'reference', 'code_2022', 'retrofit']:
    scenario_result = results[scenario_name]
    
    if scenario_result.get('success'):
        raw = scenario_result['raw']
        dm.save_scenario({
            'scenario_id': f"{run_id}-{scenario_name}",
            'run_id': run_id,
            'scenario_type': scenario_name,
            'eui_total': raw['eui_kwh_per_sf'],
            'eui_heating': raw['end_uses_kwh']['heating'] / raw['conditioned_area_ft2'],
            'eui_cooling': raw['end_uses_kwh']['cooling'] / raw['conditioned_area_ft2'],
            # ... other end uses
        })

print(f"Results saved to database: {db_path}")
```

#### 6.2 Generate Interactive Artifact

```python
from lib.artifact_builder import ArtifactBuilder

builder = ArtifactBuilder()
html_artifact = builder.build_artifact(results)

# Display artifact (in Claude Desktop, this renders as interactive HTML)
print("\n=== INTERACTIVE ARTIFACT ===\n")
print(html_artifact)
print("\n=== END ARTIFACT ===\n")
```

The artifact includes:
- **Dashboard Tab**: Stacked bar chart (Chart.js) showing end-use breakdown by scenario
- **Table Tab**: Sortable table with EUI, savings %, compliance margin, cost savings
- **Explorer Tab**: Accordion view with detailed metrics per scenario

#### 6.3 Explain Key Findings

Provide conversational summary of results:

```python
baseline_eui = results['baseline']['raw']['eui_kwh_per_sf']
code_2022_eui = results['code_2022']['raw']['eui_kwh_per_sf']

if results['code_2022'].get('vs_baseline'):
    compliance_margin = results['code_2022']['vs_baseline']['compliance_margin_pct']
    
    # Compliance margin: positive = baseline exceeds code = NON-COMPLIANT
    # Negative = baseline below code = COMPLIANT
    if compliance_margin < 0:
        print(f"\n✅ Building achieves {abs(compliance_margin):.1f}% better than 90.1-2022 minimum.")
        print(f"   Baseline EUI: {baseline_eui:.1f} kWh/sf-yr")
        print(f"   Code minimum: {code_2022_eui:.1f} kWh/sf-yr")
        print(f"   Compliance margin: {code_2022_eui - baseline_eui:.1f} kWh/sf-yr below code")
    else:
        print(f"\n❌ Building is {compliance_margin:.1f}% worse than 90.1-2022 minimum.")
        print(f"   Baseline EUI: {baseline_eui:.1f} kWh/sf-yr")
        print(f"   Code minimum: {code_2022_eui:.1f} kWh/sf-yr")
        print(f"   Gap: {baseline_eui - code_2022_eui:.1f} kWh/sf-yr must be reduced")

# Show retrofit benefits if available
if results['retrofit'].get('vs_baseline'):
    retrofit_savings_pct = results['retrofit']['vs_baseline']['energy_savings_pct']
    print(f"\n📊 Retrofit scenario shows {retrofit_savings_pct:.1f}% energy savings vs. baseline")
```

**Example output:**
> "Analysis complete! Here are the key findings:
> 
> ✅ Building achieves 8% better than 90.1-2022 minimum.
>    Baseline EUI: 45.2 kWh/sf-yr
>    Code minimum: 49.1 kWh/sf-yr
>    Compliance margin: +3.9 kWh/sf-yr
> 
> The building already exceeds code requirements due to high-efficiency HVAC and LED lighting. See the artifact above for detailed breakdowns."

#### 6.4 Offer Next Steps

```python
print("\nWhat would you like to do next?")
print("  • Edit parameters and re-run scenarios")
print("  • Generate a compliance report (uses Report Factory MCP)")
print("  • Export results to CSV")
print("  • Compare against building benchmarks")
```

### Step 8: Re-run and Parameter Editing

If the user wants to adjust parameters and re-run, handle selective re-execution.

#### 7.1 Accept Parameter Changes

```python
print("Which parameters would you like to adjust?")
print("Examples:")
print("  • envelope.wall_r_value = 15")
print("  • systems.heating_cop = 3.5")
print("  • lighting.interior_lpd_w_per_sqft = 0.7")

# Parse user input conversationally
# Update building_data with new values
```

#### 7.2 Determine Affected Scenarios

```python
# Logic to determine which scenarios need re-run
# e.g., if envelope changed, re-run all 4
# if only retrofit measures changed, re-run only retrofit

affected_scenarios = ['baseline', 'code_2022']  # Example
print(f"Re-running {len(affected_scenarios)} scenarios: {', '.join(affected_scenarios)}")
```

#### 7.3 Re-run Simulations

```python
# Generate new IDFs only for affected scenarios
new_idf_dict = {}
if 'baseline' in affected_scenarios:
    new_idf_dict['baseline'] = engine._generate_baseline_idf()
# ... etc

# Run simulations
new_results = engine.run_all_scenarios(new_idf_dict, max_retries=1)

# Merge with cached results
for scenario, result in new_results.items():
    results[scenario] = result
```

#### 7.4 Regenerate Artifact

```python
# Rebuild artifact with updated results
html_artifact = builder.build_artifact(results)
print(html_artifact)
```

## Error Handling

### EnergyPlus Not Installed

**Detection:**
```bash
which energyplus  # Returns empty if not installed
```

**Action:**
- Don't proceed without user consent
- Explain: "First-time setup requires installing EnergyPlus (200MB, 5-10 minutes). This is a one-time installation."
- Ask: "Proceed with installation?"
- If approved: Run `bash lib/install.sh`
- If declined: "Cannot run simulations without EnergyPlus. Exiting."

### Audette MCP Unreachable

**Detection:**
```python
try:
    from mcp__claude_ai_Audette_AI__list_buildings import list_buildings
    list_buildings()
except Exception as e:
    # MCP down
```

**Action:**
- "Cannot reach Audette MCP. This skill requires MCP for building data."
- "Please reconnect Audette MCP in Cowork settings and try again."
- **Do not proceed** — fail gracefully

### Simulation Failures

**Detection:**
```python
if not scenario_result.get('success'):
    error = scenario_result.get('error')
    fatal_errors = scenario_result.get('fatal_errors', [])
```

**Action:**
1. **Parse error** from `.err` file (done automatically by `SimulationRunner`)
2. **Show specific issue** with context:
   > "Baseline simulation failed: Window U-factor (0.15) is below EnergyPlus minimum (0.2)."
3. **Offer actionable fix**:
   > "Typical window U-factors: 0.3-0.6 for double-pane. Current: 0.15. Adjust to 0.35?"
4. **Allow retry** with corrected parameters
5. **If retry fails** after 3 attempts: Continue with successful scenarios and note the failure in results

### Missing Required Data

**Detection:**
```python
gaps = collector.identify_gaps(building_data)
if gaps:
    # Data is missing
```

**Action:**
- **Don't guess** or use arbitrary defaults
- **Ask conversationally**:
  > "I need the window U-factor for this building. Typical range for 1990s construction: 0.4-0.6 Btu/hr-sf-F. What should I use?"
- **Provide context** from schema prompts (via `generate_qa_prompts()`)
- **Validate input** before proceeding

### Weather File Download Failure

**Detection:**
```python
try:
    epw_path = wm.get_weather_file(climate_zone)
except ValueError as e:
    # Climate zone not supported or download failed
```

**Action:**
- Show error: "Weather file download failed for climate zone {zone}"
- List supported zones from `WeatherManager.CLIMATE_ZONE_WEATHER`
- Ask user to verify climate zone
- If persistent failure: Check network connectivity, offer manual EPW upload

## Examples

### Example 1: Successful Compliance Check

```
User: "Run energy compliance for 123 Main Street"

Claude: I found 123 Main Street (Office, 50,000 sf) in your workspace. 
I'll run ASHRAE 90.1-2022 compliance analysis. This involves:
- Collecting building data from Audette MCP
- Running 4 parallel EnergyPlus simulations (~2-3 min)
- Generating an interactive comparison artifact

Proceed? [yes]

✓ EnergyPlus installed (v24.1.0)
✓ Audette MCP connected
✓ Database initialized

Querying Audette MCP... Found geometry (50,000 sf, 5 stories), 
HVAC systems (VAV with boiler/chiller), envelope (R-13 walls, 
R-20 roof, U-0.35 windows).

Missing: infiltration rate, interior LPD.

I need the infiltration rate in ACH. Typical: 0.2-0.5 for modern 
construction. What should I use? [0.3]

What is the interior lighting power density in W/sqft? Typical 
for offices: 0.6-1.0. [0.8]

✓ Building model validated
✓ Data sources: Audette MCP 85%, User input 15%

Preparing 4 scenarios... Weather file ready for zone 5A.

Running simulations...
  Baseline (done) | Reference (done) | 90.1-2022 (done) | Retrofit (done)

All simulations complete!

[INTERACTIVE ARTIFACT DISPLAYED]

✅ Building achieves 12% better than 90.1-2022 minimum.
   Baseline EUI: 42.3 kWh/sf-yr
   Code minimum: 48.1 kWh/sf-yr
   Compliance margin: +5.8 kWh/sf-yr

Building already exceeds code due to high-efficiency HVAC and 
LED lighting. Retrofit scenario shows additional 8% savings with 
envelope upgrades.

What would you like to do next?
```

### Example 2: Failure with Recovery

```
User: "Check 90.1 compliance for the building"

Claude: I see multiple buildings in your workspace:
  1. 123 Main Street (Office)
  2. 456 Oak Avenue (Retail)

Which one? [1]

Running compliance analysis for 123 Main Street...

Querying Audette MCP... Connection failed.

❌ Cannot reach Audette MCP. This skill requires MCP for building 
data. Please reconnect Audette MCP in Cowork settings and try again.

[User reconnects MCP]

User: "Try again"

Claude: ✓ Audette MCP reconnected

Querying Audette MCP... Found complete building model.
✓ No additional data needed

Preparing scenarios... 

Running simulations...
  Baseline (FAILED) | Reference (done) | 90.1-2022 (done) | Retrofit (pending)

⚠️ Baseline simulation failed: Window U-factor (0.12) is below 
EnergyPlus minimum (0.2). This is likely a data error.

Typical window U-factors: 0.3-0.6 for double-pane. 
Adjust to 0.35 and retry? [yes]

Retrying Baseline with corrected U-factor...
  Baseline (done) ✓

✅ All simulations complete.

[ARTIFACT DISPLAYED]
```

## Important Notes

- **Never skip validation**: Always validate building model against schema before running expensive simulations
- **Progressive disclosure**: Don't overwhelm user with all options upfront — guide through workflow step-by-step
- **Transparent data sources**: Always show where data came from (MCP %, Documents %, User %)
- **Fail gracefully**: If critical components fail (MCP, EnergyPlus), explain clearly and stop rather than continuing with bad data
- **Interactive debugging**: When simulations fail, parse errors and offer specific fixes rather than generic "try again"
- **Cache results**: Save all simulation outputs to database for historical comparison and re-use
- **Conversational tone**: This is executed by Claude in conversation — write as "You do X", not "The system does X"

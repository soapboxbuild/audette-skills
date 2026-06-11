---
name: audette-setup
description: >
  Interactive setup and demonstration that tests all Audette Orchestrator functionality
  by creating a real example project. Use when users first install the plugin, ask to
  "set up Audette", "get started", "test everything", or want a guided tour with hands-on
  demonstrations. Creates workspace, building profile, energy data, equipment survey, and
  final report with fabricated demo data.
version: 1.0.0
---

# Audette Setup

Let's get you up and running with a **live demonstration** that will:
- ✅ Test all functionality end-to-end
- 🏗️ Create a real example project
- 📊 Generate demonstration data
- 📄 Produce a sample report

**Time:** 5-10 minutes
**Result:** Complete working example you can learn from

---

## How This Works

I'll walk you through each capability by **actually doing it** with demo data:

1. **System checks** - Verify prerequisites
2. **Workspace setup** - Create demo project folder
3. **Building creation** - Add a real building profile
4. **Energy data** - Generate/extract 12 months of utility data
5. **Equipment survey** - Document building systems
6. **RAG indexing** - Index demo documents (if available)
7. **Report generation** - Create decarbonization roadmap

At each step, I'll:
- 🎯 **Explain** what we're doing
- ⚙️ **Execute** the actual function
- ✅ **Verify** it worked
- 💡 **Show** you the results

---

## Step-by-Step Execution

### Step 1: Pre-Flight Checks ✈️

**What I'm doing:** Verifying system prerequisites

**Checks:**
1. Audette MCP connected (for building profiles)
4. Public APIs accessible (OSM, Nominatim)

**Execute checks:**

```bash
# System tools
pdftotext -v 2>&1 | head -1
python3 --version

# Public APIs
curl -s "https://nominatim.openstreetmap.org/search?format=json&q=Seattle+WA" \
  -H "User-Agent: audette-skills/1.0 (https://github.com/soapboxbuild/audette-skills)" | jq -r '.[0].lat'
```

**MCP test:** Call `list_customer_accounts()` to verify Audette connection.

**If checks fail:**
- MCP error: Check `claude_desktop_config.json`, restart Claude Desktop
- API timeout: Check internet connection

**On success:** ✅ Proceed to workspace creation

---

### Step 2: Create Demo Workspace 📁

**What I'm doing:** Setting up a complete project structure for "Green Tower Office Building"

**Execute:**

Create workspace at `/tmp/audette-demo-{timestamp}` with structure:

```
audette-demo-{timestamp}/
├── .audette-config.json
├── utility-bills/
│   └── (will create demo bill)
├── equipment/
│   └── (will create demo survey)
├── documents/
│   └── (will create demo PCA)
└── reports/
    └── (will generate roadmap)
```

**Trigger:** `workspace-setup` skill

**User choice:** 
> "I'll use fabricated demo data. Which building type would you like to explore?"
> - **A) Large Office Building** (50,000 sq ft, urban, 1985)
> - **B) Multifamily Residential** (100 units, suburban, 1970)
> - **C) Retail Center** (75,000 sq ft, strip mall, 1995)
> - **D) Specify your own** (provide address and details)

**Default if no answer:** Option A (Large Office)

**Result:**
- ✅ Workspace created
- ✅ `.audette-config.json` initialized
- ✅ Linked to your Audette account
- 💡 Show config file contents

---

### Step 3: Create Building Profile 🏢

**What I'm doing:** Creating a real building in your Audette account with calculated GFA

**Demo building (Option A - Large Office):**
- **Name:** Green Tower Office Building
- **Address:** 1200 First Avenue, Seattle, WA 98101
- **Type:** office
- **Year Built:** 1985
- **Floors:** 12

**Execute:**

1. **Geocode address** → Get GPS coordinates via Nominatim
2. **Query OSM footprint** → Find building outline via Overpass API
3. **Calculate GFA** → Use Shoelace formula for polygon area × floors
4. **Create in Audette** → Call `create_building()` MCP tool

**Trigger:** `audette-create-building` skill OR direct MCP call

**Result:**
- ✅ Building created with `building_uid` and `building_model_uid`
- ✅ GFA calculated from OSM (or estimated ~50,000 sq ft)
- ✅ Added to workspace config
- 💡 Show building summary

---

### Step 4: Generate Energy Data 📊

**What I'm doing:** Creating 12 months of realistic utility data

**Demo data approach:**

**Option 1: Fabricate realistic data**
Generate synthetic utility bills based on building type and climate:
- Monthly electricity: 35,000 - 55,000 kWh (office baseline with seasonal variation)
- Monthly natural gas: 800 - 2,500 GJ (heating season peaks)
- Costs: $0.12/kWh electricity, $0.30/GJ gas (Seattle rates)
- Dates: Last 12 complete months

**Option 2: User provides real bills**
> "Would you like to use fabricated demo data, or do you have real utility bills to extract?"
> - **Fabricated** → I'll generate realistic synthetic data
> - **Real PDFs** → Point me to your utility-bills folder

**Execute (fabricated path):**

1. **Generate CSV data:**
```csv
month,electricity_kwh,electricity_cost,gas_gj,gas_cost
2024-01,52000,6240,2400,720
2024-02,48000,5760,2200,660
2024-03,42000,5040,1800,540
... (12 months total)
```

2. **Create demo PDF bill** (one sample for show):
```
SEATTLE CITY LIGHT
Account: DEMO-12345
Service Period: January 2024

Electric Charges
Usage: 52,000 kWh
Total: $6,240.00
```

3. **Trigger:** `audette-energy-data` skill
4. **Upload to Audette:** Call `add_building_utility_data` MCP tool

**Result:**
- ✅ 12 months of energy data validated
- ✅ Saved to workspace
- ✅ Sample PDF created in `utility-bills/`
- 💡 Show monthly consumption chart (simple table)

---

### Step 5: Equipment Survey 🔧

**What I'm doing:** Documenting building HVAC and major systems

**Demo equipment (Large Office baseline):**

**Heating:**
- 2× Natural gas boilers (500 MBH each, installed 2010)
- Hot water distribution with variable speed pumps

**Cooling:**
- 3× Rooftop air conditioning units (40 tons each, installed 2015)
- Direct expansion cooling

**Ventilation:**
- 4× Rooftop air handling units with economizers
- Demand control ventilation (CO2 sensors)

**Domestic Hot Water:**
- 1× Natural gas water heater (75 gallon, commercial)

**Lighting:**
- 60% LED (retrofitted 2020)
- 40% fluorescent T8 (original)

**Controls:**
- Basic BMS (Building Management System)
- Programmable thermostats by zone

**Execute:**

**Option 1: Fabricate survey**
Generate complete equipment survey JSON and markdown report

**Option 2: Interactive questionnaire**
> "Would you like to:"
> - **A) Use fabricated demo equipment** (typical 1985 office, partial retrofits)
> - **B) Answer a few questions** to customize the equipment (5-10 questions)
> - **C) Extract from a document** (if you have a PCA/CNA PDF)

**Trigger:** `audette-equipment-survey` skill OR `submit_equipment_survey()` MCP

**Result:**
- ✅ Complete equipment inventory
- ✅ Mapped to Audette schema
- ✅ Saved as `equipment/green-tower-survey.json`
- 💡 Show system summary table

---

### Step 6: RAG Document Indexing 🔍 (Optional)

**What I'm doing:** Creating searchable document index for semantic queries

**Check dependencies:**
```bash
python3 -c "import sentence_transformers; print('Available')" 2>&1
```

**If available:**

1. **Create demo documents:**
   - `documents/pca-summary.pdf` - Property condition assessment excerpt
   - `documents/engineer-report.pdf` - Mechanical systems report

2. **Generate sample content:**
```
PROPERTY CONDITION ASSESSMENT - GREEN TOWER
Prepared by: Building Analytics Inc.
Date: March 2024

HVAC SYSTEMS
The building heating is provided by two natural gas-fired
boilers located in the basement mechanical room. Each boiler
has a rated capacity of 500 MBH and was installed in 2010.
The boilers are in good condition with regular maintenance.

Expected remaining useful life: 8-10 years.
Replacement cost: $45,000 per unit.

The cooling system consists of three rooftop packaged air
conditioning units...
```

3. **Trigger:** `rag_ingest` MCP tool
4. **Test query:** "What type of heating system is installed?"

**If not available:**
⚠️ Skip - RAG is optional. Note: "Install `Soapbox RAG (via rag_ingest MCP)` for document search"

**Result (if available):**
- ✅ Documents indexed with embeddings
- ✅ Test query returns relevant excerpt
- 💡 Show sample Q&A

---

### Step 7: Generate Decarbonization Roadmap 📄

**What I'm doing:** Creating a complete HTML report with interactive charts

**Execute:**

1. **Prepare report data:**
   - Baseline emissions from energy data
   - Equipment inventory for measure recommendations
   - Placeholder carbon reduction measures:
     - Boiler replacement with heat pumps (-180 tCO2e/yr, $120k)
     - LED lighting completion (-25 tCO2e/yr, $15k)
     - Rooftop solar PV installation (-100 tCO2e/yr, $200k)
     - HVAC controls upgrade (-40 tCO2e/yr, $30k)

2. **Trigger:** `report` skill with template `decarbonization-roadmap`

3. **Generate artifacts:**
   - HTML report with:
     - Executive summary
     - Baseline emissions breakdown (Scope 1, 2, 3)
     - Measure economics table
     - Implementation timeline (Gantt chart)
     - Cash flow analysis (line chart)
     - Emissions trajectory (area chart)
   - All charts use Chart.js
   - "Print to PDF" button included

**Result:**
- ✅ Full decarbonization roadmap created
- ✅ Interactive HTML artifact displayed
- ✅ Saved to `reports/green-tower-roadmap.html`
- 💡 Open artifact and explore charts

---

### Step 8: Review & Next Steps 🎯

**What we accomplished:**

| Task | Status | Location |
|------|--------|----------|
| System checks | ✅ | All prerequisites verified |
| Workspace setup | ✅ | `/tmp/audette-demo-{timestamp}` |
| Building created | ✅ | Green Tower in Audette account |
| Energy data | ✅ | 12 months, `utility-bills/` |
| Equipment survey | ✅ | Complete inventory, `equipment/` |
| RAG indexing | ✅/⚠️ | `documents/` (if installed) |
| Report generated | ✅ | `reports/green-tower-roadmap.html` |

**File tree:**
```
audette-demo-{timestamp}/
├── .audette-config.json (linked to Audette account)
├── utility-bills/
│   ├── energy-data.csv (12 months)
│   └── sample-bill-2024-01.pdf
├── equipment/
│   └── green-tower-survey.json
├── documents/
│   ├── pca-summary.pdf
│   └── .rag-index/ (if RAG enabled)
└── reports/
    └── green-tower-roadmap.html ⭐
```

**Try these next:**

1. **Explore the report artifact**
   - Click on charts to see interactivity
   - Use Print → Save as PDF
   - See investment-grade styling

2. **Modify the demo data**
   - Edit `energy-data.csv` with different values
   - Re-run `audette-energy-data` skill
   - Regenerate report to see changes

3. **Ask questions (if RAG enabled)**
   - "What's the condition of the boilers?"
   - "When were the RTUs installed?"
   - "What's the replacement cost for HVAC?"

4. **Start a real project**
   - Use this demo as a template
   - Replace with actual building data
   - Follow the same workflow

---

## Demonstration Complete! 🎉

You now have a **complete working example** of the entire Audette Orchestrator workflow.

**What you learned:**
- ✅ How to structure projects
- ✅ How to onboard buildings with GFA calculation
- ✅ How to handle energy data
- ✅ How to document equipment
- ✅ How to generate professional reports

**Ready for real work?**

**Typical workflow for actual projects:**

1. **Week 1: Data Collection**
   ```
   - Create workspace
   - Add building (use actual address)
   - Gather utility bills (ask client)
   - Collect property assessments
   ```

2. **Week 2: Analysis**
   ```
   - Extract energy data from PDFs
   - Interview building operator (equipment survey)
   - Index documents with RAG
   - Review in Audette platform
   ```

3. **Week 3: Modeling**
   ```
   - Run baseline calibration in Audette
   - Identify reduction measures
   - Run financial analysis
   - Review measure economics
   ```

4. **Week 4: Delivery**
   ```
   - Generate final report
   - Add client logo
   - Export to PDF
   - Present to stakeholders
   ```

**Try next:**
- `system-details` — Generate building systems report
- `audette-energy-data` — Process real utility bills

**Need help?**
Ask me:
- "How do I onboard my building?"
- "Extract these utility bills"
- "Generate a BPS compliance report"
- "What's the difference between report templates?"

---

## Cleanup

I've created demo data. Would you like to keep it or clean up?

**Keep it if:**
- You want a reference example
- You're learning the workflows
- You'll use it for testing

**Delete it if:**
- You're ready to start real projects
- You want a clean slate
- Disk space is limited

**To clean up:**
```bash
rm -rf /tmp/audette-demo-*
```

**Note:** The building "Green Tower Office Building" was created in your Audette account. You can delete it from the Audette dashboard if desired, or keep it as a sandbox.

---

## Welcome Aboard! 🚀

You're now equipped to create world-class decarbonization roadmaps with AI.

The Audette Orchestrator helps you:
- ⚡ **Work faster** - Automation saves hours
- 🎯 **Work accurately** - Fewer manual errors
- 📊 **Work professionally** - Beautiful deliverables

**Let's decarbonize buildings together!** 🌱

Have questions? Just ask - I'm your AI assistant for building decarbonization.

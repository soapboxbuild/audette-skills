---
name: audette-create-building
description: >
  Creates a new building in the Audette platform by extracting property details from
  documents in the project folder. Use this skill whenever the user wants to add a
  property to Audette, onboard a new asset, or create a building model. Triggers on:
  "create a building for [property]", "add [property] to Audette", "onboard this asset",
  or proactively when the user shares property documents with no building yet in Audette.
version: 1.0.0
requires:
  - audette-mcp
---

# Audette Create Building

Extract property details from documents and create a building in the Audette platform.

**Required:** Audette MCP  
**Optional:** `osm-gfa-calculator` skill (for multi-building sites without documented GFA)

---

## Step 1: Pre-flight

Read `.audette-config.json` from the workspace root. If missing, stop and tell the user to run `workspace-setup` first.

Call `list_customer_accounts` (page: 1, per_page: 100; paginate until all pages loaded). Find the account matching `audette_account.uid` from config. If not found, warn the user and list available accounts before proceeding.

Call `switch_customer_account` with the correct `customer_account_uid`. All subsequent tool calls operate in this account's context.

---

## Step 2: Duplicate Check

Call `list_buildings`. Scan the results for a building at the same address the user is trying to add.

If a match is found, show it:

```
A building at this address already exists in Audette:
- Name: [name]
- Model UID: [building_model_uid]
- Archetype: [archetype]

Use the existing model, or create a new one?
```

If the user wants the existing model, save its `building_model_uid` to config (Step 10) and skip to Step 8. Otherwise continue.

---

## Step 3: Identify the Property

If the user named a specific property, focus on that. Otherwise check `.file-index.md` or ask:

> "Which property would you like to add to Audette?"

---

## Step 4: Extract Building Attributes

Read property documents to extract the required and optional fields. Good sources:
- **Executive summaries** — address, unit count, stories, year built
- **CNA/PCNA reports** — construction type, floor area, building count
- **Offering memoranda** — property type, location, building description
- **Equipment surveys** — HVAC types, LED coverage
- **Due diligence reports** — physical observations

Read `references/archetypes.md` to map property type to Audette archetype.

### Decrypting Encrypted PDFs

Many PDFs arrive password-protected. If the Read tool fails, try `pikepdf`:

```bash
pip install pikepdf --break-system-packages
python3 -c "
import pikepdf, sys
src = sys.argv[1]
dst = src.replace('.pdf', '_decrypted.pdf')
pdf = pikepdf.open(src, password='')
pdf.save(dst)
print(f'Decrypted → {dst}')
" "<path_to_locked.pdf>"
```

Then read the `_decrypted.pdf` copy.

### Fields

| Field | Required | Notes |
|-------|----------|-------|
| `street_address` | Yes | Street only, no city/state |
| `city` | Yes | |
| `state_province` | Yes | Two-letter code (e.g. "NY", "ON") |
| `postal_zip_code` | Yes | |
| `country` | Yes | e.g. "USA", "Canada" |
| `building_archetype` | Yes | See `references/archetypes.md` |
| `floors_above_grade` | Yes | Stories above ground; basement does not count |
| `gross_floor_area_square_feet` | Yes | Gross (not net rentable) |
| `building_name` | No | Display name; leave null if not obvious |
| `year_built_original` | No | Original construction year |
| `led_installed_ratio` | No | 0.0–1.0 fraction of lighting already LED |
| `available_roof_area_ratio` | No | 0.0–1.0 fraction of roof usable for solar — ask if a site assessment exists |

### Extraction Patterns

**Address:**
```
"123 Main Street, New York, NY 10001"
→ street_address: "123 Main Street"
   city: "New York"
   state_province: "NY"
   postal_zip_code: "10001"
   country: "USA"
```

**Floor count:**
```
"4-story building"          → 4
"Two 6-story towers"        → 6 each
"Ground floor + 5 floors"   → 6 total
"3-story + basement"        → 3 (basement excluded)
```

**GFA from NRA:** If only net rentable area is documented, estimate GFA at ~115% of NRA and flag it:
```
NRA 85,000 sq ft → estimated GFA 97,750 sq ft (15% common area factor — please confirm)
```

**Archetypes — common mappings:**

| Document says | Use |
|--------------|-----|
| Apartment, condo, multifamily, co-op, HUD, Section 8 | `multi_unit_residential` |
| Townhouse, row house | `townhomes` |
| Assisted living, memory care, skilled nursing | `longterm_care` |
| Office, co-working | `office` |
| Medical office, clinic, outpatient | `medical_office` |
| Hotel, motel, extended stay | `hotel` |
| School, university, daycare | `school` |
| Grocery, supermarket | `food_retail_grocery` |
| Enclosed retail, big box, department store | `non_food_retail_closed` |
| Strip mall, open-air retail plaza | `non_food_retail_open` |
| Enclosed shopping mall | `enclosed_mall` |
| Fast food, fast casual, coffee shop | `quick_service_restaurant` |
| Sit-down restaurant, bar | `full_service_restaurant` |
| Gym, sports facility, community centre | `recreation_complex` |
| Warehouse, distribution, industrial | `warehouse` |

Mixed-use: choose the dominant use by floor area. If unclear, ask.

---

## Step 5: Calculate GFA (Multi-Building Sites)

Skip this step for single-building properties with documented GFA.

If the property has multiple buildings and GFA is undocumented, only totalled, or suspect, invoke the **`osm-gfa-calculator`** skill. Provide: property address(es), floor count per building, reported total GFA (for validation), and property type.

Use the calculated per-building breakdown in Step 6.

---

## Step 6: Confirm Inputs

Present all extracted data for user approval before calling any tools:

```
Ready to create building in Audette:

  Address:    [street_address], [city], [state_province] [postal_zip_code], [country]
  Name:       [building_name or "not set"]
  Archetype:  [building_archetype]
  GFA:        [gross_floor_area_square_feet] sq ft[  ← estimated from NRA if applicable]
  Floors:     [floors_above_grade]
  Year built: [year_built_original or "not set"]
  LED ratio:  [led_installed_ratio or "not set"]
  Roof ratio: [available_roof_area_ratio or "not set"]

Correct? (yes / edit)
```

If "edit", ask which fields to update. If the address is wrong, go back to Step 4.

---

## Step 7: Create Building

Call `create_building` with the confirmed fields. Pass `null` for any optional field that was not determined.

The response contains `building_model_uid` — save this immediately. **There is no separate `building_uid`.**

---

## Step 8: Building Details

After creation, collect a few additional attributes via `edit_building_attributes`. These are not settable at creation time but affect every financial projection downstream. Ask them now while the user is engaged.

**Leasing structure** — ask:
> "Is this building gross-leased (landlord pays utilities), net-leased (tenants pay utilities), or mixed?"

Map to the `leasing_structure` field. This determines landlord vs. tenant GHG scope attribution.

If net or mixed, also ask for landlord share percentages (electricity, natural gas, steam). Set `default_landlord_share_electricity`, `default_landlord_share_natural_gas`, `default_landlord_share_steam` accordingly.

**Financial defaults** — ask (or accept "use defaults" to skip):
> "Do you want to set financial assumptions? Discount rate, utility cost inflation, electricity/gas rates, or asset value?"

If yes, collect and pass any of: `default_discount_rate`, `default_utility_inflation_rate`, `default_electricity_utility_rate`, `default_natural_gas_utility_rate`, `assumed_gross_asset_value`, `assumed_exit_cap_rate`, `assumed_exit_year`.

**Internal identifier** — ask:
> "Do you have an internal property ID for this building (e.g. from your asset management system)?"

If yes, set `customer_building_identifier`.

Call `edit_building_attributes` once with all collected updates. If the user skips all of the above, skip this step.

---

## Step 9: Property Assignment

Call `list_properties` and show the results. Ask:
> "Should this building be assigned to a property? ([list property names] — or create new / skip)"

- **Existing property** → call `assign_property_to_building` with the matching `property_uid`
- **New property** → confirm the exact property name with the user, then call `create_property_for_building`
- **Skip** → continue

---

## Step 10: Compliance Snapshot

Call `run_compliance_analysis` with the new `building_model_uid`. Present the results as a brief summary:

> "**Compliance snapshot for [building name]:**
> [List applicable regulations, compliance status, and highest-priority gap]"

Note: this is a quick orientation, not a full compliance review. The full analysis lives in the `report` skill.

---

## Step 11: Update Config

Add the new building to `.audette-config.json`:

- Append to `buildings[]`: `name`, `building_model_uid`, `address`, `city`, `state`, `archetype`
- If assigned to a property, also store `property_uid`
- Update `last_updated` to current ISO timestamp

Write the updated config back.

---

## Step 12: Confirmation

```
Building created.

  Model UID:  [building_model_uid]
  Name:       [building_name or address]
  Account:    [account_name]
  Property:   [property_name or "unassigned"]

Compliance: [one-line summary of top finding]

Next steps:
  1. Equipment survey  → audette-equipment-survey
  2. Energy data       → audette-energy-data
  3. Full report       → report
```

---

## Error Handling

**Audette MCP not connected**
> The Audette MCP is required. Please reconnect it and try again.

**Account not found in config**
> The account in your workspace config was not found. Available accounts: [list]. Run `workspace-setup` to update the config.

**Required field missing from documents**
> Unable to extract [field] from the documents provided. Please provide it directly.

**GFA conflict (OSM vs. documented)**
```
OSM calculated:  93,000 sq ft
Documented:     120,000 sq ft
Difference:      29%

Possible reasons: basement included in documented figure, OSM footprint incomplete,
or floor count assumption is off. Which should I use?
```

---

## Rules

- Always call `switch_customer_account` before any other tool call
- Always check for duplicate buildings before creating
- Never fabricate GFA, floor count, or address — ask if missing
- Always flag GFA estimated from NRA
- Always confirm all inputs with the user before calling `create_building`
- Always call `edit_building_attributes` for leasing structure if the user engages — this is load-bearing for financial accuracy
- Always run `run_compliance_analysis` after creation
- Always update config after creation
- `building_model_uid` is the only UID returned — there is no `building_uid`

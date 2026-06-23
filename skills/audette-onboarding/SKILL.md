---
name: audette-onboarding
description: >
  Full Audette onboarding workflow for a Soapbox asset that has no Audette building yet.
  Reads footprint data and uploaded documents (OM, PCA), confirms required fields with the
  user, creates one Audette building per footprint in parallel, links them to a property,
  patches the asset's audette_property_id via the Soapbox API, and submits utility or
  equipment data. Use this skill whenever an asset needs to be set up in Audette for the
  first time. Triggers on: "create Audette buildings", "onboard to Audette", "set up in
  Audette", "add this asset to Audette", "create buildings for [property]", or proactively
  whenever an ## Audette Onboarding Context section is present in the thread.
version: 1.0.0
requires:
  - audette-mcp
---

# Audette Onboarding

End-to-end workflow: read the footprint data and documents → confirm all fields → create buildings → link property → patch the Soapbox asset → submit utility or equipment data.

**Required:** Audette MCP  
**Soapbox API:** `PATCH /api/assets/{asset_id}` to record the Audette property link

---

## Context format

The thread will contain a section like this (injected by the Soapbox platform):

```
## Audette Onboarding Context
asset_id: {uuid}
asset_name: {name}
audette_account_uid: {uid}
address: {full address}
property_type: {multifamily/office/etc}
year_built: {year}

Buildings to create:
1. {name or "Building 1"} — {floors} floors, {height_m}m, {area_m2}m², class: {class}, overture_id: {id}
2. ...

Uploaded documents: {list of OM/PCA files}
ESPM property id: {id or null}
ESPM data: {summary or null}
```

If this section is missing, ask the user for the asset_id, account UID, address, and any documents before continuing.

---

## Step 1 — Switch Account

Call `audette__switch_customer_account` with the `audette_account_uid` from the Audette Onboarding Context.

This is required before any Audette write operations — omitting it causes an HTTP 401 and every subsequent call fails.

---

## Step 2 — Extract from Documents

Read any OM, PCA, or other documents listed in **Uploaded documents**. Look for:

| Field | Where to look |
|-------|--------------|
| Year built | Executive summary, cover page, "Year Built" line |
| Property type | Cover page, property description section |
| Unit count | Summary page, "Number of Units" or "Unit Mix" table |
| Gross floor area | Summary page; if only NRA is listed, estimate GFA = NRA × 1.15 and flag it |
| Utility structure | "Utility Summary" or lease section — who pays (landlord/tenant)? |
| Primary fuel | Utility section — look for "gas" or "electric" metering; boiler vs. heat pump |
| Construction type | "Building Description" or "Physical Description" section |
| HVAC description | Equipment section — boiler, fan coil, PTAC, VRF, forced air, etc. |
| Water heater type | Equipment section — gas central, electric, heat pump, tankless |

### Decrypting password-protected PDFs

If a PDF fails to open, try:

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

### Mapping property type to building_class

| Document says | building_class |
|--------------|----------------|
| Apartment, condo, multifamily, co-op, rental | `residential` |
| Office, co-working, professional | `commercial` |
| Warehouse, distribution, manufacturing | `industrial` |
| Mixed-use (retail + residential, etc.) | `mixed_use` |

When uncertain, choose the dominant use by floor area.

### Estimating missing fields

Some fields can be reasonably estimated if not in the documents:

- **height_m** — if not stated: `num_floors × 3.5`
- **construction_type** for post-2000 multifamily (1–6 stories): `wood_frame` or `light_gauge_steel` (both are standard; wood_frame is more common in western US/Canada, light_gauge_steel in urban markets)
- **primary_fuel** for all-electric buildings: look for absence of gas meters or "100% electric" language

Always label estimated values clearly in the confirmation table (Step 3).

---

## Step 3 — Confirm with User

Before creating anything, present a confirmation table showing every building and its attributes. This is the last human checkpoint — take care to surface anything uncertain.

```
Ready to create [N] building(s) in Audette for **[asset_name]**:

| # | Name | Floors | Height | GFA (m²) | Class | Year Built | Fuel | Construction |
|---|------|--------|--------|----------|-------|-----------|------|--------------|
| 1 | Prose Frontier — Bldg 1 | 5 | 17.5m *(assumed)* | 4,820 *(from Overture)* | residential *(from OM)* | 2018 *(from OM)* | natural_gas *(from OM)* | wood_frame *(assumed — please confirm)* |
| 2 | ... | | | | | | | |

**Legend:** *(from OM)* = extracted from document · *(from Overture)* = footprint data · *(assumed — please confirm)* = estimated

Any corrections before I proceed?
```

Wait for explicit confirmation ("looks good", "yes", corrections, etc.) before moving to Step 4. If any required field is still unknown after extraction, ask for it here — don't proceed with a gap.

### Required fields for `create_building`

- `name`
- `address` (full street address)
- `building_class` — `commercial`, `residential`, `industrial`, or `mixed_use`
- `year_built`
- `gross_floor_area_m2`
- `num_floors`
- `primary_fuel` — `electric`, `natural_gas`, `dual_fuel`, `district_steam`, or `other`
- `construction_type` — `wood_frame`, `light_gauge_steel`, `heavy_timber`, `masonry`, `concrete`, `steel_frame`, or `other`

Optional but valuable if available: `height_m`, `num_units`, `overture_id`

---

## Step 4 — Create Buildings (MANDATORY PARALLEL — ALL IN ONE TURN)

Once the user confirms, you MUST call `audette__create_building` for **every building in a single turn** — emit all tool calls simultaneously before waiting for any result. Do NOT create one building, wait for the result, then create the next. That is the wrong approach and will be slow.

**Correct pattern (11 buildings → 11 simultaneous tool calls in one turn):**
```
Turn N: [create_building(bldg1), create_building(bldg2), ..., create_building(bldg11)]  ← all at once
Turn N+1: receive all results, note each building_uid
```

**Wrong pattern (do NOT do this):**
```
Turn N:   create_building(bldg1)  → wait
Turn N+1: create_building(bldg2)  → wait   ← sequential, too slow
...
```

For each building, capture the returned `building_uid`. Label them clearly (e.g., "Bldg 1 UID", "Bldg 2 UID") — you need them for Steps 5 and beyond.

**Naming convention:** If multiple buildings, use `{asset_name} — Bldg {N}` (e.g., "Prose Frontier — Bldg 1"). For a single building, just use the asset name.

If any individual building creation fails, note the failure, report it clearly after all calls complete, and offer to retry just the failed one. Don't abort the remaining buildings.

---

## Step 5 — Create and Link Property

### Primary building

Call `audette__create_property_for_building` on the first (primary) building. Store the returned `property_uid` — you need it for the asset patch and for linking non-primary buildings.

### Non-primary buildings (if more than one)

For each additional building, call `audette__assign_property_to_building(building_uid, property_uid)`. These can also be called in parallel.

### Fund assignment (if provided)

If a `fund_uid` was provided in the Audette Onboarding Context, call `audette__assign_fund_to_property(property_uid, fund_uid)`.

---

## Step 6 — Patch the Soapbox Asset

Call `PATCH /api/assets/{asset_id}` with:

```json
{ "audette_property_id": "<property_uid>" }
```

Use the `asset_id` from the Audette Onboarding Context and the `property_uid` from Step 5.

This links the Soapbox asset record to the Audette property so the platform knows onboarding is complete and can surface the Audette data.

---

## Step 7 — Utility Data (ESPM path)

**Only follow this step if `ESPM data` was provided in context (not null).**

Call `audette__add_building_utility_data` for each building using the ESPM energy data from context. If monthly consumption data is available per-building, map it directly. If only portfolio-level ESPM data is available, distribute it proportionally by GFA.

After submitting, move to Step 9 (skip Step 8).

---

## Step 8 — Equipment Survey (No-ESPM path)

**Follow this step only if no ESPM data was available.**

The equipment survey gives Audette enough information to model the building even without utility bills. Extract what you can from the OM/PCA documents (HVAC type, water heater type, appliances, lighting), then for anything not found, use vintage-and-type assumptions.

Present the full equipment picture to the user before calling the API:

```
Equipment survey for [building_name]:
- Heating system: gas boiler (central) ← from OM
- Cooling: package terminal AC (PTAC) ← from OM
- Water heater: gas central ← from OM
- Lighting: mix LED/fluorescent ← assumed for 2003 vintage — please confirm
- Appliances: in-suite electric ← assumed for multifamily — please confirm
```

For missing fields, state the assumption clearly:
> "New [year_built] construction in [climate_zone / city] — assuming [standard equipment for that vintage and type]"

Wait for the user to confirm or correct the assumptions, then call `audette__submit_equipment_survey` for each building. These can be submitted in parallel.

---

## Step 9 — Completion Summary

Report the results:

```
Audette onboarding complete for **[asset_name]**

Buildings created:
  Bldg 1: [name] — UID: [building_uid]
  Bldg 2: [name] — UID: [building_uid]

Property: [property_name] — UID: [property_uid]
Asset patched: audette_property_id = [property_uid]

Data submitted: [ESPM utility data / equipment survey]

[If any step failed:]
⚠ Failed: [describe what failed and offer to retry]

Next steps:
  - View building in Audette dashboard
  - Run full decarbonization report → report skill
  - Add utility bills → audette-energy-data skill
```

---

## Error Handling

**Building creation failure**
> "Building [N] ([name]) failed to create: [error]. The other buildings were created successfully. Retry Bldg [N]?"

**Property creation failure**
> "Created [N] buildings but failed to create the property: [error]. Buildings are unlinked. Retry property creation?"

**Asset patch failure**
> "Property created (UID: [uid]) but the asset patch failed: [error]. You can manually set `audette_property_id` on the asset, or I can retry."

**Missing required field (not in documents, not in context)**
> "I couldn't find [field] in the documents. Please provide it before I continue."

**Audette MCP not connected**
> "The Audette MCP is required for this workflow. Please reconnect it and try again."

---

## Rules

- Always call `audette__switch_customer_account` before any other Audette tool call
- Never create buildings without explicit user confirmation of the attribute table (Step 3)
- Always label extracted vs. assumed values in the confirmation table
- Always capture and report each `building_uid` immediately after creation — don't rely on re-fetching
- Create all buildings in parallel (single turn); link property in parallel for non-primary buildings
- Always patch the Soapbox asset (`PATCH /api/assets/{asset_id}`) after the property is created
- If ESPM data is present, use it (Step 7); only fall back to equipment survey (Step 8) if no ESPM
- A failure on one building should not abort the rest — continue and report at the end

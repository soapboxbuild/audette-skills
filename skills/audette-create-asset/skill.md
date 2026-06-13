---
name: audette-create-asset
description: >
  Creates all buildings in Audette for a multi-building property/asset, assigning every
  building to the same Audette property. Use when the user wants to onboard a property
  that contains multiple buildings (e.g. a campus, complex, or portfolio entry with N
  towers/phases). Triggers on: "create asset in Audette", "onboard this property",
  "add all buildings for [property]", "set up [property name] in Audette". Requires
  audette-mcp and the asset's audette_property_id to be set.
version: 1.0.0
requires:
  - audette-mcp
---

# Audette Create Asset

Create all buildings for a property in Audette and assign them to the property in one pass.

**Use this skill when:** the asset has multiple buildings, or when you want to onboard
a full property at once rather than building by building.  
**Use `audette-create-building` instead when:** creating a single building interactively.

---

## Step 1: Pre-flight

Read `.audette-config.json` from the workspace root. If missing, stop:
> "Run `workspace-setup` first to initialise the workspace."

Call `list_customer_accounts`. Switch to the account matching `audette_account.uid`:
```
call switch_customer_account(customer_account_uid)
```

---

## Step 2: Resolve the Property

The property to use comes from the asset context. Check in this order:

1. **`audette_property_id` in config** — if `.audette-config.json` has `property.uid`, use it.
2. **User statement** — if the user named or pasted a property name, search `list_properties` for it.
3. **Ask** if neither is available:
   > "Which Audette property should these buildings be assigned to?"
   Call `list_properties` and show the names.

Once resolved, store `property_uid` and `property_name`. All buildings created in this run will be assigned to this property.

---

## Step 3: Enumerate Buildings

Determine how many distinct buildings exist at this property and extract per-building attributes.

**Sources to check (in order):**
- `.file-index.md` — look for site plan, PCNA/CNA, offering memo, or rent roll
- Property documents — executive summary or physical description section
- Site plan or survey if available

**For each building, extract:**

| Field | Required | Notes |
|-------|----------|-------|
| `street_address` | Yes | Use property address for all; add unit/bldg suffix if multiple on same parcel |
| `city`, `state_province`, `postal_zip_code`, `country` | Yes | Same for all buildings in same complex |
| `building_archetype` | Yes | See `references/archetypes.md`; usually same across buildings |
| `floors_above_grade` | Yes | Per building — may differ (e.g. Tower A = 12F, Tower B = 8F) |
| `gross_floor_area_square_feet` | Yes | Per building |
| `building_name` | Recommended | Use `property_name + " — Bldg A"` / `"Tower 1"` / phase label if no explicit name |
| `year_built_original` | No | Per building if phased development |

**Naming convention when no explicit names exist:**
```
Single building:       use property_name directly
Two buildings:         "[property] — Building A", "[property] — Building B"
Numbered towers:       "[property] — Tower 1", "[property] — Tower 2"
Phased:                "[property] — Phase I", "[property] — Phase II"
```

**If building count is unclear**, ask:
> "How many buildings does [property name] have? I can see [N] from the documents."

---

## Step 4: Confirm All Buildings

Present the full list before creating anything:

```
Ready to create [N] building(s) in Audette for property "[property_name]":

  1. [building_name]
     [address] · [archetype] · [GFA] sq ft · [floors]F · built [year or "unknown"]

  2. [building_name]
     [address] · [archetype] · [GFA] sq ft · [floors]F · built [year or "unknown"]

  ...

All will be assigned to property: [property_name] ([property_uid])

Proceed? (yes / edit / cancel)
```

If "edit", ask which building and which field to correct. Re-present after edits.

---

## Step 5: Create Buildings (One by One)

For each building in the confirmed list:

1. Call `create_building` with the extracted fields. Pass `null` for any optional field not determined.
2. Capture `building_model_uid` from the response — this is the only UID returned.
3. Immediately call `assign_property_to_building`:
   ```
   assign_property_to_building(
     property_uid = <property_uid>,
     building_model_uids = [<building_model_uid>]
   )
   ```
4. Confirm assignment before moving to the next building:
   ```
   ✓ [building_name] created and assigned to [property_name]
   ```

If any `create_building` call fails, stop and report the error — do not proceed to the next building until the user decides whether to retry, skip, or cancel.

---

## Step 6: Update Config

After all buildings are created, update `.audette-config.json`:

- For each created building, append to `buildings[]`:
  ```json
  {
    "name": "<building_name>",
    "building_model_uid": "<uid>",
    "address": "<street_address>",
    "city": "<city>",
    "state": "<state_province>",
    "archetype": "<archetype>",
    "property_uid": "<property_uid>",
    "property_name": "<property_name>"
  }
  ```
- Set `property.uid` and `property.name` at the top level if not already set.
- Update `last_updated` to current ISO timestamp.

Write the updated config back.

---

## Step 7: Summary

```
[N] building(s) created and assigned to "[property_name]".

  [building_name_1]  —  [building_model_uid_1]
  [building_name_2]  —  [building_model_uid_2]
  ...

Next steps:
  • Equipment survey   → audette-equipment-survey  (for each building)
  • Energy data        → audette-energy-data        (for each building)
  • Full report        → report
```

---

## Error Handling

**`audette_property_id` not set on this asset**
> "This asset has no Audette property linked. Go to asset Settings → Audette to select the property, then re-run this skill."

**`create_building` fails for one building**
> "Building [N] ([name]) failed: [error message]. Would you like to retry, skip it, or cancel the remaining buildings?"

**Duplicate building detected (address already in Audette)**
> "A building at this address already exists in Audette ([existing_name], uid [uid]). Skip creation and assign the existing building instead? (yes / no)"
If yes: call `assign_property_to_building` with the existing `building_model_uid` and continue.

**GFA missing or undocumented**
> "I could not find the gross floor area for [building_name]. Please provide it (in sq ft) or run the `osm-gfa-calculator` skill to estimate it from the building footprint."

---

## Rules

- Always call `switch_customer_account` before any tool calls
- Always confirm the full building list before creating anything
- Always call `assign_property_to_building` immediately after each successful `create_building` — do not batch
- Never fabricate GFA, floor count, or address
- On any creation failure, stop and ask the user before continuing
- `building_model_uid` is the only UID returned by `create_building` — there is no `building_uid`

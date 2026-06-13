---
name: audette-create-asset
description: >
  Creates all buildings in Audette for a property/asset and assigns them to an Audette
  property. Handles single-building and multi-building properties. Works for new assets
  with no Audette property linked yet — creates or selects the property as part of the
  flow. Triggers on: "create asset in Audette", "onboard this property", "add all
  buildings for [property]", "set up [property name] in Audette".
version: 1.2.0
requires:
  - audette-mcp
---

# Audette Create Asset

Onboard a property into Audette — create its building(s) and assign them to a property.
Works for new assets with no prior Audette linkage, single-building properties, and
multi-building complexes.

---

## Step 0: Index Available Files

**Before anything else**, call `list_files` to get a summary of what's available.

- If the result shows **many files** (100+), use `search_files` to find relevant documents rather than reading everything:
  - `search_files("PCNA")` or `search_files("building condition")`
  - `search_files("offering")` or `search_files("executive summary")`
  - `search_files("lease")` or `search_files("rent roll")`
  - `search_files("utility")` or `search_files("energy")`
- If the result shows a **manageable list** (<50 files), scan the names directly.

Show the user a brief summary:
```
Found [N] file(s). Relevant documents detected:
  • [filename] — likely [document type]
  ...
```

If no files are found, ask:
> "No files are attached to this asset yet. Would you like to upload any documents (lease, PCNA, offering memo, utility bills) before I start? You can use the 📎 button in the chat composer. Once uploaded, just say 'continue' and I'll pick them up."

If files exist, proceed. If the user wants to add more, wait for them to upload and say continue.

---

## Step 1: Pre-flight

Call `list_customer_accounts`. Find the account to use:
- If the user's asset has `audette_account_id` set in Soapbox settings, use that account.
- Otherwise ask the user which account to use and show the list.

Call `switch_customer_account(customer_account_uid)`.

---

## Step 2: Resolve the Property

A property in Audette groups one or more buildings. Determine which to use:

**Check `audette_property_id` (from asset settings):**
- If the user's asset has `audette_property_id` set in Soapbox settings, use it — skip to Step 3.

**No property linked yet — ask:**
> "This asset isn't linked to an Audette property yet. Should I:
> 1. Create a new property named '[asset name]'
> 2. Link to an existing property
> 3. Skip property assignment for now"

- **Create new:** confirm the property name (default = asset name), then call `create_property_for_building` after the first building is created (Step 6).
- **Existing:** call `list_properties`, show names, let user pick. Store `property_uid`.
- **Skip:** proceed without property assignment.

---

## Step 3: Duplicate Check

Call `list_buildings`. Check whether any building at this property's address already exists.

If a match is found:
```
A building at this address already exists in Audette:
  Name:      [name]
  Model UID: [building_model_uid]
  Archetype: [archetype]

Use the existing building, or create a new one?
```

If using existing, collect its `building_model_uid`, assign it to the property (Step 6), update config (Step 7), and skip to Step 8.

---

## Step 4: Enumerate Buildings

Determine how many distinct buildings exist at this property and extract per-building attributes from the uploaded documents.

**Sources to check (use `read_file` for each relevant document):**
- Offering memorandum or executive summary — address, unit count, stories, year built
- CNA/PCNA reports — construction type, floor area, building count
- Rent rolls — address, unit count
- Equipment surveys — HVAC types, LED coverage
- Site plans if available

**Single building:** most properties have one. Proceed with a single entry.
**Multiple buildings:** extract per-building attributes for each.

For each building, extract:

| Field | Required | Notes |
|-------|----------|-------|
| `street_address` | Yes | Property address; add bldg suffix only if multiple on same parcel |
| `city`, `state_province`, `postal_zip_code`, `country` | Yes | Same for all buildings in same complex |
| `building_archetype` | Yes | See `references/archetypes.md` |
| `floors_above_grade` | Yes | Per building — may differ across towers |
| `gross_floor_area_square_feet` | Yes | Per building |
| `building_name` | Recommended | See naming convention below |
| `year_built_original` | No | Per building if phased |

**Naming convention:**
```
1 building:    use property/asset name directly
2 buildings:   "[property] — Building A", "[property] — Building B"
N towers:      "[property] — Tower 1", "[property] — Tower 2", …
Phased:        "[property] — Phase I", "[property] — Phase II", …
```

If building count is unclear, ask:
> "How many buildings does [property name] have? I can see [N] from the documents."

---

## Step 5: Confirm All Buildings

Present the full list before creating anything:

```
Ready to create [N] building(s) in Audette:

  1. [building_name]
     [address] · [archetype] · [GFA] sq ft · [floors]F[· built [year]]

  2. [building_name]  ← only shown if N > 1
     ...

Property: [property_name] (will be [created / assigned to existing / skipped])

Proceed? (yes / edit / cancel)
```

If "edit", ask which building and field. Re-present after changes.

---

## Step 6: Create Buildings

For each building in the confirmed list:

1. Call `create_building` with the extracted fields (`null` for any undetermined optional field).
2. Capture `building_model_uid` — the only UID returned.
3. **Property assignment:**
   - If `property_uid` is known: call `assign_property_to_building(property_uid, [building_model_uid])`
   - If creating a new property and this is the **first** building: call `create_property_for_building(property_name, [building_model_uid])`. Capture the returned `property_uid` for subsequent buildings.
   - If skipping: no assignment call.
4. Confirm before moving on:
   ```
   ✓ [building_name] created[and assigned to [property_name]]
   ```

On any failure: stop and ask the user to retry, skip, or cancel — do not proceed automatically.

---

## Step 7: Summary

```
[N] building(s) created[and assigned to "[property_name]"].

  [building_name_1]  —  [building_model_uid_1]
  [building_name_2]  —  [building_model_uid_2]  ← only if N > 1

Next steps:
  • Equipment survey   → audette-equipment-survey
  • Energy data        → audette-energy-data
  • Full report        → report
```

---

## Error Handling

**No files found and user declines to upload**
Proceed without documents — ask for each required field manually.

**`create_building` fails**
> "[building_name] failed: [error]. Retry, skip this building, or cancel remaining?"

**Duplicate detected**
> "A building at this address already exists ([name], [uid]). Assign the existing building to this property instead? (yes / no)"

**GFA missing**
> "I couldn't find the gross floor area for [building_name]. Please provide it in sq ft."

**Property creation fails**
> "Couldn't create property '[name]': [error]. Try a different name, link to an existing property, or skip property assignment?"

---

## Rules

- Always call `list_files` first — never assume the asset has no documents
- Always call `switch_customer_account` before any Audette tool calls
- Treat single-building properties identically to multi-building — no minimum required
- Always confirm the full list before any `create_building` call
- Call `assign_property_to_building` or `create_property_for_building` immediately after each successful creation
- On any failure, stop and surface the error before continuing
- `building_model_uid` is the only UID returned by `create_building`
- Never fabricate GFA, floor count, or address — ask if missing

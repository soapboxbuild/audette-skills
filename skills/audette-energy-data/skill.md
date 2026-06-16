---
name: audette-energy-data
description: >
  Extracts utility bill data from PDF or Excel files in the project folder, validates
  12-month concurrent and continuous coverage across all meters, and submits the records
  to Audette — triggering a re-model. Use this skill when the user wants to compile energy
  data for a building, extract utility bills, or upload consumption data to Audette.
  Triggers on: "compile energy data", "extract utility bills", "process energy files",
  "prepare energy data for [building]", "upload utility data", or "get consumption from bills".
version: 1.0.0
requires:
  - audette-mcp
---

# Audette Energy Data

Extract utility bill data from PDFs and Excel files, validate 12-month coverage, and submit to Audette.

**Required:** Audette MCP  
**Note:** Only `electricity`, `natural_gas`, and `steam` are submitted to Audette. `oil` and `water` are captured in the local CSV for reference but the Audette model does not use them.

---

## Pre-flight

Call `switch_customer_account` with the Audette customer account UID from the system prompt.
This is required before any Audette write operations — omitting it causes HTTP 401.

If no account UID is in the system prompt, call `list_customer_accounts` and ask the user to select one.

## Step 1: Identify the Building

The building UID is in the system prompt if this asset has been linked to Audette.
If not, call `list_buildings` to find it by name or address, or ask:
> "Which building is this utility data for?"

Note the `building_model_uid` — it's required for submission.

---

## Step 2: Check Existing Utility Data

Call `get_building_utility_data` with the `building_model_uid`.

If records already exist, show a summary:
```
This building already has utility data in Audette:
  Electricity: [N] records, [start] to [end]
  Natural gas: [N] records, [start] to [end]

Replace all existing data, append new records, or cancel?
```

If replacing, proceed — the `add_building_utility_data` call will overwrite.  
If appending, note the existing date range so duplicate periods can be flagged in Step 7.  
If cancelling, stop here.

---

## Step 3: Scan for Utility Bill Files

Scan the project folder recursively for utility bill files:
- PDFs or Excel files (`.xlsx`, `.xls`) whose names contain: `bill`, `invoice`, `utility`, `electric`, `gas`, `steam`, `water`, `energy`, `statement`
- Any file inside a folder named: `utilities`, `bills`, `invoices`, `energy`

List the files found and confirm with the user:
> "I found [N] utility bill file(s): [list]. Extract data from all of them?"

If no files found, ask the user to provide the file location or upload bills to the workspace.

---

## Step 4: Extract Data from Files

For each file, use the Read tool (PDFs) or read Excel files directly. A single file may contain multiple months or energy types — extract all as separate rows.

### Required Fields

| Field | Notes |
|-------|-------|
| **Supplier** | Utility company name (e.g. "Eversource", "National Grid") |
| **Account number** | As printed on the bill |
| **Energy type** | Normalize to: `electricity`, `natural_gas`, `steam`, `oil`, `water`, `other` |
| **Start date** | Billing period start — `YYYY-MM-DD` |
| **End date** | Billing period end — `YYYY-MM-DD` |
| **Consumption** | Numeric only |
| **Unit** | e.g. `kWh`, `therms`, `ccf`, `MMBtu`, `lbs` |
| **Cost** | Total billed, numeric only. Negative for credits. |
| **Currency** | `USD` or `CAD` |

**Extraction rules:**
- If a field is missing or unreadable, leave it blank — do not guess
- Delivery + supply shown separately → combine into one row with total cost
- Same Supplier + Account + Start + End duplicated → keep first, flag to user

**Energy type mapping:**

| Bill says | Use |
|-----------|-----|
| Electric, Electricity, Power | `electricity` |
| Natural Gas, Gas, NG | `natural_gas` |
| Steam, District Steam | `steam` |
| Fuel Oil, Oil, #2 Oil | `oil` |
| Water, Sewer | `water` |

### Decrypting Encrypted PDFs

If the Read tool fails on a PDF:

```bash
pip install pikepdf --break-system-packages
python3 -c "
import pikepdf, sys
src = sys.argv[1]
dst = src.replace('.pdf', '_decrypted.pdf')
pikepdf.open(src, password='').save(dst)
print(f'Decrypted → {dst}')
" "<path_to_locked.pdf>"
```

### Monthly Cost Estimation

If a bill shows a 12-month consumption chart but only the current period's total cost, estimate other months using the blended rate:

```
rate = current_total_cost / current_period_consumption
estimated_cost = monthly_consumption × rate
```

Tell the user:
> "Monthly costs for [Supplier] were estimated using the blended rate from the current bill ($X.XX/unit). Actual monthly costs may vary."

---

## Step 5: Save Raw CSV

Write all extracted rows to `utility-data-<building-slug>-raw.csv` using these columns:

```
Supplier, Account number, Energy type, Start date, End date, Consumption, Unit, Cost, Currency
```

---

## Step 6: Validate

Run the validation script against the raw CSV:

```bash
python3 <skill_base_dir>/scripts/validate_energy_data.py \
  --input utility-data-<building-slug>-raw.csv \
  --output utility-data-<building-slug>-<YYYY-MM-DD>.csv
```

The script:
- Normalises units: electricity → `kWh`, thermal → `GJ`
- Checks continuity per meter — fills 1-month gaps via linear regression
- Finds 12-month concurrent window across all meters
- Attempts year-based time-shifting if meters don't naturally overlap
- Exits 0 on PASS (validated CSV written), exits 1 on FAIL

### Handling Failures

If the script exits 1, show the failure report verbatim and ask:
> "Would you like to remove the failing meter and rerun, or obtain the missing bills and try again?"

Do not proceed to submission until the script exits 0.

---

## Step 7: Confirm Before Submitting

Show the validation summary and ask for confirmation:

```
Validation passed. Ready to submit to Audette:

  Building:   [building_name] ([building_model_uid])
  Meters:     [N]
  Period:     [start] to [end]
  Records:    [N] rows
  Submitting: electricity, natural_gas, steam only
  [oil/water if present]: captured in CSV, not submitted to Audette

Submit?
```

---

## Step 8: Submit to Audette

Map the validated CSV rows to the MCP format. Only submit rows where `Energy type` is `electricity`, `natural_gas`, or `steam`.

For each qualifying row:

| CSV field | MCP field | Notes |
|-----------|-----------|-------|
| `Energy type` | `utility_type` | exact match |
| `Start date` | `start_date` | `YYYY-MM-DD` |
| `End date` | `end_date` | `YYYY-MM-DD` |
| `Consumption` | `energy_consumption` | already normalised |
| `Unit` (`kWh` or `GJ`) | `energy_consumption_unit` | lowercase: `kwh` or `gj` |
| `Currency` | `currency` | `USD` or `CAD` |
| `Cost` | `utility_cost` | **always pass `0` if unknown — never `null`/`None`** (see note below) |
| `Account number` | `account_number` | optional |
| `Supplier` | `utility_provider` | optional |

Call `add_building_utility_data` with `building_model_uid` and the full `utility_data` array in a single call.

**⚠️ `utility_cost` must always be a number — never `null` or omitted.** Pass `0` when cost is unknown or estimated. Passing `null` causes the calibration service (SMR) to throw `AutoCalibratorError: Unexpected <class 'TypeError'>: cannot unpack non-iterable NoneType object` during re-modelling.

The MCP server validates independently and triggers re-modelling on success.

---

## Step 9: Confirmation

```
Utility data submitted.

  Building:     [building_name]
  Records:      [N] submitted ([N] electricity, [N] natural_gas, [N] steam)
  Period:       [start] to [end]
  Re-modelling: triggered — updated carbon plan available shortly

Local CSV saved: utility-data-<building-slug>-<YYYY-MM-DD>.csv
[If oil/water present]: oil/water records saved locally only (not supported by Audette model)

Next steps:
  1. Equipment survey  → audette-equipment-survey
  2. Full report       → report
```

---

## Error Handling

**No utility bills found**
> No utility bill files found in this workspace. Upload bills (PDF or Excel) to the project folder and try again.

**MCP validation failure** (server rejects submission)
> Audette rejected the submission: [error message]. This usually means gaps in coverage or mismatched date ranges. Check the validated CSV and re-run.

**Scanned / image PDFs**
> [filename] appears to be a scanned image — text extraction is not possible. Please use an OCR tool (e.g. Adobe Acrobat, Tesseract) to extract the text first, or retype the data into the CSV template manually.

---

## Rules

- Always call `switch_customer_account` before any MCP calls
- Always check existing utility data before submitting
- Never submit without user confirmation (Step 7)
- Never fabricate consumption values — if extraction fails, tell the user
- Always flag estimated costs clearly
- Always save a local CSV regardless of submission outcome — it is the audit trail
- `oil` and `water` records go into the CSV but are silently excluded from the MCP payload
- The MCP validates on its own — if it rejects, report the error verbatim

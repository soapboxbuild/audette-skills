"""
validate_energy_data.py

Validates utility data CSVs for:
  - Unit normalisation: electricity → kWh, thermal → GJ (water/other unchanged)
  - Continuity per meter (fills 1-month gaps via linear regression)
  - 12-month concurrent coverage across all meters
  - Time-shifting by whole years when meters don't naturally overlap

Usage:
    python validate_energy_data.py --input raw.csv --output validated.csv

Exit codes:
    0 = PASS (validated CSV written)
    1 = FAIL (no CSV written)
"""

import argparse
import csv
import sys
from collections import defaultdict
from datetime import date, datetime
from itertools import product


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_date(s):
    """Parse YYYY-MM-DD string to date."""
    return datetime.strptime(s.strip(), "%Y-%m-%d").date()


def month_key(d):
    """Return (year, month) tuple for a date."""
    return (d.year, d.month)


def month_add(ym, months):
    """Add N months to a (year, month) tuple."""
    y, m = ym
    m += months
    y += (m - 1) // 12
    m = (m - 1) % 12 + 1
    return (y, m)


def month_diff(ym1, ym2):
    """Number of months from ym1 to ym2 (positive if ym2 is later)."""
    return (ym2[0] - ym1[0]) * 12 + (ym2[1] - ym1[1])


def ym_to_date(ym):
    """Convert (year, month) to first day of that month."""
    return date(ym[0], ym[1], 1)


def month_range(start_ym, end_ym):
    """Inclusive list of (year, month) tuples from start to end."""
    result = []
    cur = start_ym
    while cur <= end_ym:
        result.append(cur)
        cur = month_add(cur, 1)
    return result


def linear_regression(points):
    """
    Simple linear regression on (x, y) pairs.
    Returns (slope, intercept).
    """
    n = len(points)
    if n < 2:
        raise ValueError("Need at least 2 points for regression")
    sx = sum(p[0] for p in points)
    sy = sum(p[1] for p in points)
    sxx = sum(p[0] ** 2 for p in points)
    sxy = sum(p[0] * p[1] for p in points)
    denom = n * sxx - sx * sx
    if denom == 0:
        return 0, sy / n
    slope = (n * sxy - sx * sy) / denom
    intercept = (sy - slope * sx) / n
    return slope, intercept


def predict(slope, intercept, x):
    return max(0.0, slope * x + intercept)


# ---------------------------------------------------------------------------
# Unit normalisation
# ---------------------------------------------------------------------------

# Electricity energy types → normalise to kWh
ELECTRICITY_TYPES = {"electricity"}

# Thermal energy types → normalise to GJ
THERMAL_TYPES = {"natural_gas", "steam", "oil", "other"}

# Water and unknown types are left unconverted
NO_CONVERT_TYPES = {"water"}

# Conversion factors → kWh (for electricity)
TO_KWH = {
    "kwh":  1.0,
    "mwh":  1_000.0,
    "gwh":  1_000_000.0,
    "wh":   0.001,
    # thermal units that appear on electric bills (rare but possible)
    "btu":  0.000293071,
    "mmbtu": 293.071,
    "mbtu":  293.071,   # ESPM uses MBtu to mean MMBtu
    "gj":   277.778,
    "mj":   0.277778,
}

# Conversion factors → GJ (for thermal)
TO_GJ = {
    "gj":     1.0,
    "mj":     0.001,
    "kj":     0.000001,
    "kwh":    0.0036,
    "mwh":    3.6,
    "gwh":    3_600.0,
    "btu":    0.000001055056,
    "mmbtu":  1.055056,
    "mbtu":   1.055056,   # ESPM MBtu = MMBtu
    "therm":  0.105480,
    "therms": 0.105480,
    "ccf":    0.105480 * 1.02,   # ~1.02 therms/ccf
    "mcf":    1.05506,            # 1 Mcf ≈ 1000 cf ≈ 1.055 GJ
    "lbs":    0.001259,           # lbs of steam at typical conditions
    "klbs":   1.259,              # 1000 lbs steam
    # gallons depend on fuel type — handled separately
}

# Gallons conversion by energy type
GALLONS_TO_GJ = {
    "oil":         0.14615,   # #2 fuel oil
    "natural_gas": 0.09654,   # propane
}


def normalise_unit_key(unit: str) -> str:
    """Lowercase and strip punctuation for lookup."""
    return unit.lower().strip().rstrip("s").rstrip(".")  # naive plural strip


def convert_consumption(value: float, unit: str, energy_type: str):
    """
    Convert consumption value to the target unit for its energy type.
    Returns (converted_value, target_unit) or (value, unit) if no conversion found.
    Logs a warning to stderr if the unit is unrecognised.
    """
    etype = energy_type.lower().strip()
    ukey = normalise_unit_key(unit)

    if etype in NO_CONVERT_TYPES:
        return value, unit  # no conversion for water

    if etype in ELECTRICITY_TYPES:
        factor = TO_KWH.get(ukey)
        if factor is None:
            # try stripping trailing 's' one more time
            factor = TO_KWH.get(ukey.rstrip("s"))
        if factor is not None:
            return round(value * factor, 4), "kWh"
        print(f"  WARNING: unknown electricity unit '{unit}' — left unconverted",
              file=sys.stderr)
        return value, unit

    if etype in THERMAL_TYPES:
        # Special case: gallons depends on energy type
        if ukey in ("gallon", "gallons", "gal"):
            factor = GALLONS_TO_GJ.get(etype)
            if factor:
                return round(value * factor, 4), "GJ"
            print(f"  WARNING: no gallons conversion for energy type '{energy_type}' "
                  f"— left unconverted", file=sys.stderr)
            return value, unit

        factor = TO_GJ.get(ukey)
        if factor is None:
            factor = TO_GJ.get(ukey.rstrip("s"))
        if factor is not None:
            return round(value * factor, 4), "GJ"
        print(f"  WARNING: unknown thermal unit '{unit}' for '{energy_type}' "
              f"— left unconverted", file=sys.stderr)
        return value, unit

    # Fallback — unknown energy type
    return value, unit


def normalise_units(rows):
    """
    Apply unit normalisation to all rows in place.
    Returns list of (supplier, account, energy_type, unit) tuples that were converted.
    """
    conversions = []
    for row in rows:
        etype = row.get("Energy type", "")
        unit  = row.get("Unit", "")
        try:
            consumption = float(row.get("Consumption") or 0)
        except ValueError:
            continue

        new_val, new_unit = convert_consumption(consumption, unit, etype)
        if new_unit != unit:
            row["Consumption"] = new_val
            row["Unit"] = new_unit
            conversions.append(
                f"{row.get('Supplier')} / {row.get('Account number')} / "
                f"{etype}: {unit} → {new_unit}"
            )
    return conversions


# ---------------------------------------------------------------------------
# Core data structures
# ---------------------------------------------------------------------------

def meter_key(row):
    return (row["Supplier"], row["Account number"], row["Energy type"])


def load_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Step 1: Build monthly series per meter
# ---------------------------------------------------------------------------

def build_meter_series(rows):
    """
    Returns:
        meters: dict of meter_key -> dict of (year,month) -> row
    """
    meters = defaultdict(dict)
    for row in rows:
        key = meter_key(row)
        try:
            start = parse_date(row["Start date"])
        except (ValueError, KeyError):
            continue
        ym = month_key(start)
        if ym in meters[key]:
            # duplicate — keep existing (already handled upstream)
            continue
        meters[key][ym] = row
    return dict(meters)


# ---------------------------------------------------------------------------
# Step 2: Fill 1-month gaps via linear regression
# ---------------------------------------------------------------------------

def fill_gaps(meter_series):
    """
    For each meter, scan for gaps. Fill 1-month gaps via linear regression
    on the 4 adjacent months (2 before, 2 after). Mark filled rows.

    Returns:
        filled_series: updated meter_series
        failures: list of failure dicts
        interpolated: list of interpolated row descriptors
    """
    failures = []
    interpolated = []

    for key, monthly in meter_series.items():
        supplier, account, etype = key
        all_months = sorted(monthly.keys())
        if not all_months:
            continue

        start_ym = all_months[0]
        end_ym = all_months[-1]
        full_range = month_range(start_ym, end_ym)

        i = 0
        while i < len(full_range):
            ym = full_range[i]
            if ym not in monthly:
                # Found a gap — measure its length
                gap_start = i
                while i < len(full_range) and full_range[i] not in monthly:
                    i += 1
                gap_end = i - 1
                gap_months = full_range[gap_start:gap_end + 1]
                gap_size = len(gap_months)

                if gap_size > 1:
                    failures.append({
                        "meter": f"{supplier} / {account} / {etype}",
                        "reason": f"Gap of {gap_size} months: "
                                  f"{gap_months[0][0]}-{gap_months[0][1]:02d} to "
                                  f"{gap_months[-1][0]}-{gap_months[-1][1]:02d}",
                    })
                    continue

                # gap_size == 1 — attempt interpolation
                gap_ym = gap_months[0]
                gap_idx = full_range.index(gap_ym)

                # Collect 2 before and 2 after
                before = [m for m in full_range[:gap_idx] if m in monthly][-2:]
                after  = [m for m in full_range[gap_idx + 1:] if m in monthly][:2]

                if len(before) < 2 or len(after) < 2:
                    failures.append({
                        "meter": f"{supplier} / {account} / {etype}",
                        "reason": f"Cannot fill gap at "
                                  f"{gap_ym[0]}-{gap_ym[1]:02d}: fewer than 2 "
                                  f"adjacent months on one side",
                    })
                    continue

                # Use month index as x for regression
                neighbors = before + after
                ref = neighbors[0]
                x_points_c = [(month_diff(ref, m), float(monthly[m]["Consumption"] or 0))
                              for m in neighbors]
                x_points_k = [(month_diff(ref, m), float(monthly[m]["Cost"] or 0))
                              for m in neighbors]

                sc, ic = linear_regression(x_points_c)
                sk, ik = linear_regression(x_points_k)
                gap_x = month_diff(ref, gap_ym)

                # Build a synthetic row by copying the nearest real row
                template = monthly[before[-1]].copy()
                template["Start date"] = ym_to_date(gap_ym).strftime("%Y-%m-%d")
                gap_end_ym = month_add(gap_ym, 1)
                gap_end_date = date(gap_end_ym[0], gap_end_ym[1], 1)
                # last day of gap month
                import calendar
                last_day = calendar.monthrange(gap_ym[0], gap_ym[1])[1]
                template["End date"] = date(gap_ym[0], gap_ym[1], last_day).strftime("%Y-%m-%d")
                template["Consumption"] = round(predict(sc, ic, gap_x), 2)
                template["Cost"] = round(predict(sk, ik, gap_x), 2)
                template["_interpolated"] = "true"

                monthly[gap_ym] = template
                interpolated.append(
                    f"{supplier} / {account} / {etype} — "
                    f"{gap_ym[0]}-{gap_ym[1]:02d} (interpolated)"
                )
            else:
                i += 1

    return meter_series, failures, interpolated


# ---------------------------------------------------------------------------
# Step 3: Find concurrent window
# ---------------------------------------------------------------------------

def concurrent_window(meter_series):
    """
    Find the largest overlapping date range across all meters.
    Returns (start_ym, end_ym) or None if no overlap.
    """
    starts = []
    ends = []
    for monthly in meter_series.values():
        months = sorted(monthly.keys())
        starts.append(months[0])
        ends.append(months[-1])

    overlap_start = max(starts)
    overlap_end = min(ends)

    if overlap_start > overlap_end:
        return None
    return overlap_start, overlap_end


def window_months(start_ym, end_ym):
    return month_diff(start_ym, end_ym) + 1


# ---------------------------------------------------------------------------
# Step 4: Time-shifting
# ---------------------------------------------------------------------------

def try_time_shift(meter_series, max_shift_years=3):
    """
    Try all combinations of year offsets (multiples of 12 months) for each
    meter to maximise the concurrent window.

    Returns:
        best_shifts: dict of meter_key -> year offset applied
        best_window: (start_ym, end_ym) or None
    """
    keys = list(meter_series.keys())
    shifts_to_try = list(range(-max_shift_years * 12, (max_shift_years + 1) * 12, 12))

    best_length = -1
    best_total_shift = float("inf")
    best_shifts = {k: 0 for k in keys}
    best_window = None

    for combo in product(shifts_to_try, repeat=len(keys)):
        # Build shifted meter series
        shifted = {}
        for k, shift in zip(keys, combo):
            shifted[k] = {month_add(ym, shift): row
                          for ym, row in meter_series[k].items()}

        win = concurrent_window(shifted)
        if win is None:
            continue
        length = window_months(*win)
        total_shift = sum(abs(s) for s in combo)

        # Prefer longer window; break ties by minimum total absolute shift
        if length > best_length or (length == best_length and total_shift < best_total_shift):
            best_length = length
            best_total_shift = total_shift
            best_shifts = dict(zip(keys, combo))
            best_window = win

    return best_shifts, best_window


# ---------------------------------------------------------------------------
# Step 5: Apply shifts and trim to 12-month window
# ---------------------------------------------------------------------------

def apply_shifts_and_trim(meter_series, shifts, window_start, window_end):
    """
    Return a flat list of rows, shifted and trimmed to the 12-month window.
    Rows get updated Start/End dates to reflect the shift.
    """
    output_rows = []
    target_months = set(month_range(window_start, window_end))

    for key, shift in shifts.items():
        monthly = meter_series[key]
        for ym, row in monthly.items():
            shifted_ym = month_add(ym, shift)
            if shifted_ym not in target_months:
                continue
            out = row.copy()
            if shift != 0:
                # Adjust dates
                try:
                    orig_start = parse_date(row["Start date"])
                    orig_end   = parse_date(row["End date"])
                    new_start = date(orig_start.year + shift // 12,
                                     orig_start.month, orig_start.day)
                    new_end   = date(orig_end.year + shift // 12,
                                     orig_end.month, orig_end.day)
                    out["Start date"] = new_start.strftime("%Y-%m-%d")
                    out["End date"]   = new_end.strftime("%Y-%m-%d")
                    out["_time_shifted"] = f"{'+' if shift > 0 else ''}{shift // 12}y"
                except (ValueError, OverflowError):
                    pass
            output_rows.append(out)

    return output_rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Validate utility energy data CSV")
    parser.add_argument("--input",  required=True, help="Path to raw extracted CSV")
    parser.add_argument("--output", required=True, help="Path to write validated CSV")
    args = parser.parse_args()

    # Load
    rows = load_csv(args.input)
    if not rows:
        print("FAIL\nReason: Input CSV is empty.")
        sys.exit(1)

    # Normalise units (electricity → kWh, thermal → GJ)
    unit_conversions = normalise_units(rows)

    # Build series
    meter_series = build_meter_series(rows)
    if not meter_series:
        print("FAIL\nReason: No valid meters found (check date formats).")
        sys.exit(1)

    # Fill gaps
    meter_series, gap_failures, interpolated = fill_gaps(meter_series)
    if gap_failures:
        print("FAIL")
        for f in gap_failures:
            print(f"Meter: {f['meter']}")
            print(f"Reason: {f['reason']}")
            print("Action needed: Obtain the missing bills or remove this meter.")
        sys.exit(1)

    # Check concurrent window
    window = concurrent_window(meter_series)
    shifts = {k: 0 for k in meter_series}

    if window is None or window_months(*window) < 12:
        # Attempt time-shifting
        shifts, window = try_time_shift(meter_series)
        if window is None or window_months(*window) < 12:
            nat_win = concurrent_window(meter_series)
            print("FAIL")
            if nat_win is None:
                print("Reason: No overlapping months found across all meters, "
                      "even after time-shifting up to 3 years.")
            else:
                months_found = window_months(*window) if window else window_months(*nat_win)
                print(f"Reason: Only {months_found} month(s) of concurrent coverage "
                      f"achievable (need 12), even after time-shifting up to 3 years.")
            print("Action needed: Obtain additional billing history for the "
                  "meters with less coverage.")
            sys.exit(1)

    # Trim to exactly 12 months (take the first 12 of the window)
    win_start, win_end = window
    all_months = month_range(win_start, win_end)
    if len(all_months) > 12:
        win_end = all_months[11]  # first 12 months

    # Apply shifts and trim
    output_rows = apply_shifts_and_trim(meter_series, shifts, win_start, win_end)

    # Sort: energy type, then start date
    output_rows.sort(key=lambda r: (r.get("Energy type", ""), r.get("Start date", "")))

    # Build fieldnames — original + any extra flags
    base_fields = ["Supplier", "Account number", "Energy type",
                   "Start date", "End date", "Consumption", "Unit", "Cost", "Currency"]
    extra_fields = []
    if any(r.get("_interpolated") for r in output_rows):
        extra_fields.append("_interpolated")
    if any(r.get("_time_shifted") for r in output_rows):
        extra_fields.append("_time_shifted")
    fieldnames = base_fields + extra_fields

    # Strip internal keys not in fieldnames
    for row in output_rows:
        for k in ["_interpolated", "_time_shifted"]:
            if k not in fieldnames:
                row.pop(k, None)
        # Ensure all base fields exist
        for f in base_fields:
            row.setdefault(f, "")

    write_csv(args.output, output_rows, fieldnames)

    # Report
    print("PASS")
    print(f"Meters: {len(meter_series)}")
    print(f"Period: {ym_to_date(win_start)} to {ym_to_date(win_end)}")

    if unit_conversions:
        print(f"Unit conversions: {len(unit_conversions)}")
        for c in sorted(set(unit_conversions)):
            print(f"  {c}")
    else:
        print("Unit conversions: none")

    shifted_meters = [f"{k[2]} (account {k[1]}) shifted "
                      f"{'+' if shifts[k] > 0 else ''}{shifts[k] // 12}y"
                      for k in meter_series if shifts.get(k, 0) != 0]
    if shifted_meters:
        print("Time shifts applied:")
        for s in shifted_meters:
            print(f"  {s}")
    else:
        print("Time shifts applied: none")

    if interpolated:
        print(f"Interpolated rows: {len(interpolated)}")
        for i in interpolated:
            print(f"  {i}")
    else:
        print("Interpolated rows: 0")

    print(f"Output: {args.output} ({len(output_rows)} rows)")
    sys.exit(0)


if __name__ == "__main__":
    main()

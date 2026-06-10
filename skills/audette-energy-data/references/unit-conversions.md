# Unit Conversion Reference

All consumption values are automatically normalised by `validate_energy_data.py` before validation.

## Target units by energy type

| Energy type | Target unit | Notes |
|------------|-------------|-------|
| `electricity` | `kWh` | |
| `natural_gas` | `GJ` | |
| `steam` | `GJ` | |
| `oil` | `GJ` | |
| `other` | `GJ` | |
| `water` | _(unchanged)_ | No standard energy equivalent |

---

## Electricity → kWh

| From unit | Factor | Example |
|-----------|--------|---------|
| `kWh` | 1.0 | No change |
| `MWh` | × 1,000 | 1 MWh = 1,000 kWh |
| `GWh` | × 1,000,000 | |
| `Wh` | × 0.001 | |
| `BTU` | × 0.000293071 | |
| `MMBtu` / `MBtu` | × 293.071 | ESPM uses MBtu to mean million BTU |
| `GJ` | × 277.778 | |
| `MJ` | × 0.277778 | |

---

## Thermal → GJ

| From unit | Factor | Notes |
|-----------|--------|-------|
| `GJ` | 1.0 | No change |
| `MJ` | × 0.001 | |
| `kJ` | × 0.000001 | |
| `kWh` | × 0.0036 | |
| `MWh` | × 3.6 | |
| `BTU` | × 0.000001055 | |
| `MMBtu` / `MBtu` | × 1.055056 | ESPM uses MBtu to mean million BTU |
| `therm` / `therms` | × 0.105480 | |
| `ccf` | × 0.10759 | ~1.02 therms/ccf |
| `Mcf` | × 1.05506 | 1,000 cubic feet of natural gas |
| `lbs` | × 0.001259 | Lbs of steam at typical conditions |
| `klbs` | × 1.259 | 1,000 lbs of steam |
| `gallons` (oil) | × 0.14615 | #2 fuel oil |
| `gallons` (natural_gas) | × 0.09654 | Propane |

---

## Unrecognised units

If a unit is not in the table above, the script logs a warning to stderr and leaves the value unconverted. The row will still be included in the output — check the warning and update the conversion table if needed.

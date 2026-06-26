#!/usr/bin/env python3
"""Tests for intervention_engine.py"""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "intervention_engine.py"
DCF_SCRIPT = Path(__file__).parent.parent / "dcf_engine.py"

# ─── Shared fixtures ──────────────────────────────────────────────────────────

MF_INPUTS = {
    "profile": {"asset_type": "multifamily", "region": "us", "currency": "USD"},
    "unit_mix": [
        {"type": "1BR-A1", "count": 120, "avg_sf": 731, "market_rent": 1540},
        {"type": "2BR-B1", "count": 80, "avg_sf": 1105, "market_rent": 2000},
    ],
    "going_in_occupancy": 0.95,
    "loss_to_lease_pct": 0.02,
    "vacancy_pct": 0.05,
    "concessions_pct": 0.01,
    "bad_debt_pct": 0.0015,
    "other_income_per_unit": 2049,
    "opex": {
        "payroll_per_unit": 1400,
        "om_per_unit": 700,
        "marketing_per_unit": 300,
        "ga_per_unit": 275,
        "utilities_per_unit": 835,
        "management_fee_pct": 0.025,
        "insurance_per_unit": 600,
        "taxes_per_unit": 2200,
        "reserves_per_unit": 150,
    },
    "growth": {
        "rent": [0.04, 0.04, 0.03, 0.03, 0.03],
        "expense": [0.03, 0.03, 0.03, 0.03, 0.03],
    },
    "hold_period_years": 5,
    "exit_cap_rate": 0.05,
    "sale_costs_pct": 0.015,
}

COMMERCIAL_INPUTS = {
    "profile": {
        "asset_type": "office",
        "region": "us",
        "lease_structure": "gross",
        "currency": "USD",
    },
    "total_sf": 100_000,
    "current_occupancy": 0.88,
    "passing_rent_psf": 42.0,
    "market_rent_psf": 45.0,
    "opex_psf": 18.0,
    "management_fee_pct": 0.03,
    "capex_psf": 1.5,
    "ti_psf_at_renewal": 35.0,
    "lc_pct_of_lease_value": 0.04,
    "avg_lease_term_years": 5,
    "renewal_probability": 0.65,
    "growth": {"rent": [0.025] * 5, "expense": [0.03] * 5},
    "hold_period_years": 5,
    "exit_cap_rate": 0.065,
    "sale_costs_pct": 0.015,
}


def run_dcf(inputs: dict) -> dict:
    result = subprocess.run(
        [sys.executable, str(DCF_SCRIPT), "--inputs", json.dumps(inputs)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"DCF engine failed: {result.stderr}"
    return json.loads(result.stdout)


def run_engine(base: dict, intervention: dict, market_cap_rate: float = 0.05) -> dict:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--base",
            json.dumps(base),
            "--intervention",
            json.dumps(intervention),
            "--market-cap-rate",
            str(market_cap_rate),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Intervention engine failed: {result.stderr}"
    return json.loads(result.stdout)


def make_base_model(dcf_inputs: dict) -> dict:
    """Run DCF engine and inject exit_cap_rate into output."""
    dcf = run_dcf(dcf_inputs)
    dcf["exit_cap_rate"] = dcf_inputs["exit_cap_rate"]
    return dcf


# ─── Tests ────────────────────────────────────────────────────────────────────


def test_yoc_formula():
    """YOC = steady-state NOI uplift / total capex."""
    base = make_base_model(MF_INPUTS)
    # 200-unit property, add $2M capex, $150k/yr steady-state NOI uplift
    intervention = {
        "total_capex": 2_000_000,
        "noi_uplift_annual": 150_000,
    }
    out = run_engine(base, intervention, market_cap_rate=0.05)
    expected_yoc = 150_000 / 2_000_000  # 0.075
    assert abs(out["yoc"] - expected_yoc) < 1e-4, (
        f"Expected YOC {expected_yoc:.4f}, got {out['yoc']:.4f}"
    )


def test_investment_spread():
    """Investment Spread = YOC − market cap rate."""
    base = make_base_model(MF_INPUTS)
    intervention = {
        "total_capex": 2_000_000,
        "noi_uplift_annual": 150_000,
    }
    market_cap_rate = 0.05
    out = run_engine(base, intervention, market_cap_rate=market_cap_rate)
    expected_spread = out["yoc"] - market_cap_rate
    assert abs(out["investment_spread"] - expected_spread) < 1e-6, (
        f"Expected spread {expected_spread:.6f}, got {out['investment_spread']:.6f}"
    )


def test_investment_spread_negative_when_yoc_below_market():
    """When YOC < market cap rate, investment spread should be negative."""
    base = make_base_model(MF_INPUTS)
    intervention = {
        "total_capex": 5_000_000,
        "noi_uplift_annual": 100_000,  # 2% YOC < 5% market
    }
    out = run_engine(base, intervention, market_cap_rate=0.05)
    assert out["investment_spread"] < 0, "Spread should be negative when YOC < market cap"


def test_payback_period():
    """Payback should occur when cumulative NOI uplift covers capex."""
    base = make_base_model(MF_INPUTS)
    # Capex $1M all in year 1; NOI uplift $400k/yr → pays back ~2.5 years
    intervention = {
        "total_capex": 1_000_000,
        "deployment_schedule": [1.0, 0.0, 0.0, 0.0, 0.0],
        "noi_uplift_schedule": [400_000, 400_000, 400_000, 400_000, 400_000],
    }
    out = run_engine(base, intervention, market_cap_rate=0.05)
    # Year 1: net = 400k - 1M = -600k
    # Year 2: net = -600k + 400k = -200k
    # Year 3: net = -200k + 400k = +200k → payback in year 3 at 200/400 = 0.5 through
    expected_payback = 2.5
    assert out["payback_years"] is not None
    assert abs(out["payback_years"] - expected_payback) < 0.1, (
        f"Expected payback ~{expected_payback}, got {out['payback_years']}"
    )


def test_payback_exceeds_hold():
    """If capex never pays back within hold, payback_years should be None (inf)."""
    base = make_base_model(MF_INPUTS)
    intervention = {
        "total_capex": 10_000_000,
        "noi_uplift_annual": 50_000,  # tiny uplift — never recoups in 5 yrs
    }
    out = run_engine(base, intervention, market_cap_rate=0.05)
    assert out["payback_years"] is None, (
        "payback_years should be None when investment doesn't pay back within hold"
    )


def test_irr_delta_positive_for_value_add():
    """A positive NOI uplift should increase IRR over the base."""
    base = make_base_model(MF_INPUTS)
    base_irr = base["unlevered_irr"]
    intervention = {
        "total_capex": 1_000_000,
        "noi_uplift_annual": 200_000,
    }
    out = run_engine(base, intervention, market_cap_rate=0.05)
    assert out["irr_delta"] > 0, (
        f"Expected positive IRR delta; got {out['irr_delta']:.4f}"
    )
    assert out["with_intervention"]["unlevered_irr"] > base_irr


def test_exit_value_delta_reflects_noi_uplift():
    """Exit value should increase when NOI at exit increases."""
    base = make_base_model(MF_INPUTS)
    base_exit = base["exit_value"]
    intervention = {
        "total_capex": 500_000,
        "noi_uplift_annual": 100_000,
    }
    out = run_engine(base, intervention, market_cap_rate=0.05)
    assert out["exit_value_delta"] > 0, "Exit value should increase with NOI uplift"
    # Sanity: delta should be roughly uplift / exit_cap_rate * (1 - sale_costs)
    approx = 100_000 / MF_INPUTS["exit_cap_rate"] * (1 - 0.015)
    assert abs(out["exit_value_delta"] - approx) / approx < 0.05, (
        f"Exit delta {out['exit_value_delta']:,.0f} vs approx {approx:,.0f}"
    )


def test_noi_delta_by_year_structure():
    """noi_delta_by_year must have one entry per hold year with correct keys."""
    base = make_base_model(MF_INPUTS)
    intervention = {
        "total_capex": 1_000_000,
        "noi_uplift_schedule": [50_000, 75_000, 100_000, 100_000, 100_000],
    }
    out = run_engine(base, intervention, market_cap_rate=0.05)
    deltas = out["noi_delta_by_year"]
    assert len(deltas) == 5, f"Expected 5 years of NOI deltas, got {len(deltas)}"
    for row in deltas:
        assert "year" in row
        assert "noi_delta" in row
    # First year uplift should match schedule
    assert abs(deltas[0]["noi_delta"] - 50_000) < 1, (
        f"Year 1 delta expected 50000, got {deltas[0]['noi_delta']}"
    )


def test_summary_card_contains_yoc_and_spread():
    """summary_card must contain 'Yield on Cost' and 'Investment Spread'."""
    base = make_base_model(MF_INPUTS)
    intervention = {
        "total_capex": 2_000_000,
        "noi_uplift_annual": 120_000,
    }
    out = run_engine(base, intervention, market_cap_rate=0.05)
    card = out["summary_card"]
    assert "Yield on Cost" in card, "summary_card missing 'Yield on Cost'"
    assert "Investment Spread" in card, "summary_card missing 'Investment Spread'"


def test_commercial_no_double_count_ti_lc():
    """
    For commercial assets, the base unlevered_cf already deducts TI/LC.
    Adding an intervention capex should not double-count those costs.
    Verify that the intervention output's with_intervention NOI equals
    base NOI + uplift (not base NOI + uplift − TI/LC again).
    """
    base = make_base_model(COMMERCIAL_INPUTS)
    intervention = {
        "total_capex": 500_000,
        "deployment_schedule": [1.0, 0.0, 0.0, 0.0, 0.0],
        "noi_uplift_schedule": [20_000, 40_000, 60_000, 80_000, 100_000],
    }
    out = run_engine(base, intervention, market_cap_rate=0.065)
    modified = out["with_intervention"]["annual"]
    base_annual = base["annual"]

    # NOI in modified should be base NOI + uplift (no extra TI/LC deduction)
    for i in range(5):
        expected_noi = base_annual[i]["noi"] + intervention["noi_uplift_schedule"][i]
        got_noi = modified[i]["noi"]
        assert abs(got_noi - expected_noi) < 1, (
            f"Year {i+1}: expected NOI {expected_noi:,.0f}, "
            f"got {got_noi:,.0f} — possible TI/LC double-count"
        )

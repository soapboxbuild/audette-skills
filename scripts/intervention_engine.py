#!/usr/bin/env python3
"""
intervention_engine.py — Capital intervention overlay engine.

Takes a base DCF model output and layers one or more capital interventions
(capex programs) on top, computing:
  - Yield on Cost (YOC)
  - Investment Spread
  - Payback period
  - IRR delta
  - Exit value delta
  - NOI delta by year
  - Summary card

YOC = stabilized NOI uplift (final-year NOI delta) / total capex
Investment Spread = YOC − market cap rate

For commercial assets, unlevered_cf already deducts TI/LC — do NOT
double-count them in intervention cashflows.

Usage:
    python3 intervention_engine.py \\
        --base '<json>' \\
        --intervention '<json>' \\
        --market-cap-rate 0.05

Output: JSON to stdout with keys:
    yoc                 float
    investment_spread   float
    payback_years       float
    irr_delta           float
    exit_value_delta    float
    noi_delta_by_year   list of {year, noi_delta}
    with_intervention   dict  (full modified annual + summary metrics)
    summary_card        str
"""

import argparse
import json
import sys
from typing import Optional


# ─── IRR via Newton-Raphson ───────────────────────────────────────────────────

def _npv(rate: float, cashflows: list) -> float:
    return sum(cf / (1 + rate) ** t for t, cf in enumerate(cashflows))


def _npv_derivative(rate: float, cashflows: list) -> float:
    return sum(-t * cf / (1 + rate) ** (t + 1) for t, cf in enumerate(cashflows))


def irr(cashflows: list, guess: float = 0.10, max_iter: int = 1000,
        tol: float = 1e-8) -> Optional[float]:
    rate = guess
    for _ in range(max_iter):
        npv_val = _npv(rate, cashflows)
        deriv = _npv_derivative(rate, cashflows)
        if abs(deriv) < 1e-14:
            return None
        new_rate = rate - npv_val / deriv
        if abs(new_rate - rate) < tol:
            return new_rate
        rate = new_rate
        rate = max(-0.99, min(rate, 10.0))
    return None


# ─── Core Computation ─────────────────────────────────────────────────────────

def compute_intervention(
    base_model: dict,
    intervention: dict,
    market_cap_rate: float,
) -> dict:
    """
    Overlay an intervention on a base DCF model.

    base_model keys expected:
        annual          list of {year, noi, unlevered_cf, ...}
        going_in_noi    float
        stabilized_noi  float
        exit_value      float
        unlevered_irr   float
        exit_cap_rate   float  (optional — used for exit recalc)

    intervention keys:
        total_capex         float   required
        deployment_schedule list[float]  optional — fraction per year (must sum ≤ 1.0)
                             defaults to spending all capex in year 1
        noi_uplift_schedule list[float]  optional — NOI uplift delivered per year
                             defaults to linear ramp from 0 to full uplift across hold
        noi_uplift_annual   float   optional — steady-state annual NOI uplift (final year)
                             if omitted, inferred from noi_uplift_schedule[-1] or 0
        noi_uplift_pct      float   optional — NOI uplift as % of base stabilized_noi
                             used only when noi_uplift_annual not provided
        sale_costs_pct      float   optional — defaults to 0.015
        asset_name          str     optional
    """

    annual = base_model["annual"]
    hold = len(annual)
    base_stabilized_noi = base_model.get("stabilized_noi", annual[-1]["noi"])
    base_exit_value = base_model.get("exit_value", 0.0)
    base_irr = base_model.get("unlevered_irr", 0.0)
    base_going_in_noi = base_model.get("going_in_noi", annual[0]["noi"])

    # Resolve exit_cap_rate: prefer base_model field, fall back to
    # implied cap from going_in_noi / exit_value
    exit_cap_rate = base_model.get("exit_cap_rate")
    if exit_cap_rate is None and base_exit_value and base_stabilized_noi:
        # Implied from last-year NOI and exit_value
        # exit_value ≈ exit_noi / cap_rate → cap_rate ≈ exit_noi / exit_value
        # exit_noi is stabilized_noi grown by one more year; approximate with stab_noi
        exit_cap_rate = base_stabilized_noi / base_exit_value
    if exit_cap_rate is None or exit_cap_rate <= 0:
        exit_cap_rate = 0.05

    total_capex = float(intervention["total_capex"])
    sale_costs_pct = float(intervention.get("sale_costs_pct", 0.015))

    # ── Resolve NOI uplift per year ─────────────────────────────────────────
    # Priority: noi_uplift_schedule > noi_uplift_annual > noi_uplift_pct
    if "noi_uplift_schedule" in intervention:
        raw = intervention["noi_uplift_schedule"]
        # Pad or truncate to hold length
        uplift_by_year = list(raw) + [raw[-1]] * max(0, hold - len(raw))
        uplift_by_year = uplift_by_year[:hold]
    elif "noi_uplift_annual" in intervention:
        full_uplift = float(intervention["noi_uplift_annual"])
        # Linear ramp: 0 in year 1, full uplift by final year
        uplift_by_year = [
            full_uplift * (yr / hold) for yr in range(1, hold + 1)
        ]
    elif "noi_uplift_pct" in intervention:
        full_uplift = base_stabilized_noi * float(intervention["noi_uplift_pct"])
        uplift_by_year = [
            full_uplift * (yr / hold) for yr in range(1, hold + 1)
        ]
    else:
        uplift_by_year = [0.0] * hold

    # ── Resolve capex deployment schedule ───────────────────────────────────
    if "deployment_schedule" in intervention:
        raw_sched = intervention["deployment_schedule"]
        # Pad or truncate
        deployment = list(raw_sched) + [0.0] * max(0, hold - len(raw_sched))
        deployment = deployment[:hold]
    else:
        # Default: all capex in year 1
        deployment = [1.0] + [0.0] * (hold - 1)

    capex_by_year = [total_capex * d for d in deployment]

    # ── Build modified annual cashflows ─────────────────────────────────────
    modified_annual = []
    for i, base_yr in enumerate(annual):
        yr_noi_delta = uplift_by_year[i]
        new_noi = base_yr["noi"] + yr_noi_delta
        # unlevered_cf = noi + uplift − capex_spent_this_year
        new_ucf = base_yr["unlevered_cf"] + yr_noi_delta - capex_by_year[i]
        row = dict(base_yr)
        row["noi"] = round(new_noi, 0)
        row["unlevered_cf"] = round(new_ucf, 0)
        row["noi_intervention_uplift"] = round(yr_noi_delta, 0)
        row["capex_deployed"] = round(capex_by_year[i], 0)
        modified_annual.append(row)

    # ── Recompute exit value ─────────────────────────────────────────────────
    # Exit NOI = stabilized (final year) NOI with intervention
    new_stabilized_noi = modified_annual[-1]["noi"]
    # Back-compute the exit_noi growth multiplier the base DCF used:
    # base_exit_value = base_exit_noi / exit_cap_rate * (1 - sale_costs_pct)
    # base_exit_noi = base_stabilized_noi * growth_multiplier
    # → growth_multiplier = base_exit_value * exit_cap_rate / (base_stabilized_noi * (1 - sale_costs_pct))
    if base_stabilized_noi > 0 and base_exit_value > 0:
        exit_noi_multiplier = (
            base_exit_value * exit_cap_rate / (base_stabilized_noi * (1 - sale_costs_pct))
        )
    else:
        exit_noi_multiplier = 1.0
    new_exit_noi = new_stabilized_noi * exit_noi_multiplier
    new_exit_value = new_exit_noi / exit_cap_rate * (1 - sale_costs_pct)
    exit_value_delta = new_exit_value - base_exit_value

    # ── Recompute unlevered IRR with intervention ────────────────────────────
    # Purchase price: use going-in NOI / exit_cap_rate as implied
    implied_purchase = base_going_in_noi / exit_cap_rate
    new_cfs = [-implied_purchase] + [yr["unlevered_cf"] for yr in modified_annual]
    new_cfs[-1] += new_exit_value

    new_irr = irr(new_cfs) or 0.0
    irr_delta = new_irr - base_irr

    # ── YOC & Investment Spread ──────────────────────────────────────────────
    # YOC = stabilized NOI uplift (final year delta) / total capex
    final_year_noi_delta = uplift_by_year[-1]  # steady-state uplift
    yoc = final_year_noi_delta / total_capex if total_capex > 0 else 0.0
    investment_spread = yoc - market_cap_rate

    # ── Payback period ───────────────────────────────────────────────────────
    # Cumulative NOI uplift − cumulative capex deployed → find year crossover
    cumulative_net = 0.0
    payback_years: Optional[float] = None
    for i in range(hold):
        cumulative_net += uplift_by_year[i] - capex_by_year[i]
        if cumulative_net >= 0 and payback_years is None:
            # Interpolate within year
            if i == 0:
                payback_years = float(i + 1)
            else:
                prev_cum = cumulative_net - (uplift_by_year[i] - capex_by_year[i])
                yr_net = uplift_by_year[i] - capex_by_year[i]
                frac = -prev_cum / yr_net if yr_net != 0 else 0.0
                payback_years = float(i) + frac

    if payback_years is None:
        payback_years = float("inf")  # doesn't pay back within hold

    # ── NOI delta by year ────────────────────────────────────────────────────
    noi_delta_by_year = [
        {"year": annual[i]["year"], "noi_delta": round(uplift_by_year[i], 0)}
        for i in range(hold)
    ]

    # ── Summary card ─────────────────────────────────────────────────────────
    asset_name = intervention.get("asset_name", base_model.get("asset_name", "Asset"))
    payback_str = (
        f"{payback_years:.1f} yrs" if payback_years != float("inf") else ">hold period"
    )
    card_lines = [
        f"{asset_name} — Intervention Analysis",
        "─" * 52,
        f"Total Capex:        ${total_capex:>12,.0f}",
        f"NOI Uplift (stab.): ${final_year_noi_delta:>12,.0f}",
        f"Yield on Cost:      {yoc*100:>11.1f}%",
        f"Investment Spread:  {investment_spread*100:>+11.1f}%  vs {market_cap_rate*100:.1f}% mkt cap",
        f"Payback Period:     {payback_str:>15s}",
        f"IRR Delta:          {irr_delta*100:>+11.2f}%  ({base_irr*100:.1f}% → {new_irr*100:.1f}%)",
        f"Exit Value Delta:   ${exit_value_delta:>+12,.0f}",
        "─" * 52,
    ]
    summary_card = "\n".join(card_lines)

    with_intervention = {
        "annual": modified_annual,
        "going_in_noi": base_going_in_noi,
        "stabilized_noi": new_stabilized_noi,
        "exit_value": round(new_exit_value, 0),
        "unlevered_irr": round(new_irr, 6),
    }

    return {
        "yoc": round(yoc, 6),
        "investment_spread": round(investment_spread, 6),
        "payback_years": round(payback_years, 4) if payback_years != float("inf") else None,
        "irr_delta": round(irr_delta, 6),
        "exit_value_delta": round(exit_value_delta, 0),
        "noi_delta_by_year": noi_delta_by_year,
        "with_intervention": with_intervention,
        "summary_card": summary_card,
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Compute capital intervention overlay on a base DCF model."
    )
    parser.add_argument("--base", required=True,
                        help="Base DCF model JSON (output of dcf_engine.py + exit_cap_rate)")
    parser.add_argument("--intervention", required=True,
                        help="Intervention definition JSON")
    parser.add_argument("--market-cap-rate", type=float, required=True,
                        help="Current market cap rate for investment spread calc")
    args = parser.parse_args()

    base_model = json.loads(args.base)
    intervention = json.loads(args.intervention)
    market_cap_rate = args.market_cap_rate

    result = compute_intervention(base_model, intervention, market_cap_rate)
    print(json.dumps(result))


if __name__ == "__main__":
    main()

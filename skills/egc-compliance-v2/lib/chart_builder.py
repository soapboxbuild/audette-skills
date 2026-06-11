"""
Generates two matplotlib charts as base64-encoded PNG strings:
1. EUI bar chart (grouped bars: as-built, code-min, retrofit, net-solar)
2. End-use stacked bar chart (same scenarios, stacked by end use)

All charts must be base64-embedded — NOT saved to file, NOT referenced by URL.
Chart.js MUST NOT be used (fails in Playwright headless print).
"""

import io
import base64
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend — must be set before importing pyplot
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


COLORS = {
    'as_built': '#2C5F8F',    # Navy blue
    'code_min': '#E07B39',    # Orange
    'retrofit': '#3B8B5E',    # Green
    'net_solar': '#7B5EA7',   # Purple
}

END_USE_COLORS = {
    'heating': '#E05252',
    'cooling': '#5299E0',
    'dhw': '#E0A252',
    'lighting': '#F5E642',
    'plug_loads': '#9E9E9E',
}


def fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return b64


def build_eui_bar_chart(report: dict) -> str:
    """
    Horizontal grouped bar chart showing EUI for each scenario.
    Includes a horizontal dashed line at code_min EUI.
    Returns base64 PNG string.
    """
    scenarios = report['scenarios']
    names = ['As-Built\n(Calibrated)', 'Code Min\n(90.1-2016)', 'Retrofit\nPlan']
    values = [
        scenarios['as_built']['eui_kwh_ft2'],
        scenarios['code_min']['eui_kwh_ft2'],
        scenarios['retrofit']['eui_kwh_ft2'],
    ]
    colors = [COLORS['as_built'], COLORS['code_min'], COLORS['retrofit']]

    if 'net_solar' in scenarios:
        names.append('Retrofit +\nSolar (info.)')
        values.append(scenarios['net_solar']['eui_kwh_ft2'])
        colors.append(COLORS['net_solar'])

    fig, ax = plt.subplots(figsize=(6, 3))
    x = np.arange(len(names))
    bars = ax.bar(x, values, color=colors, width=0.6, zorder=3)

    # Value labels on bars
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.15,
                f'{val:.1f}', ha='center', va='bottom', fontsize=8, fontweight='bold')

    # Compliance threshold line (code min)
    code_min = scenarios['code_min']['eui_kwh_ft2']
    ax.axhline(y=code_min, color=COLORS['code_min'], linewidth=1.5,
               linestyle='--', zorder=4, alpha=0.7)

    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=8)
    ax.set_ylabel('Site EUI (kWh/ft²·yr)', fontsize=9)
    ax.set_ylim(0, max(values) * 1.25)
    ax.grid(axis='y', alpha=0.3, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()

    return fig_to_base64(fig)


def build_end_use_chart(report: dict) -> str:
    """
    Stacked bar chart of end uses by scenario.
    Returns base64 PNG string.
    """
    scenarios = report['scenarios']
    scenario_keys = ['as_built', 'code_min', 'retrofit']
    scenario_labels = ['As-Built', 'Code Min', 'Retrofit']
    end_uses = ['heating', 'cooling', 'dhw', 'lighting', 'plug_loads']

    fig, ax = plt.subplots(figsize=(6, 3))
    x = np.arange(len(scenario_keys))
    bottom = np.zeros(len(scenario_keys))

    gfa = report['building']['gfa_ft2']

    for eu in end_uses:
        vals = []
        for sk in scenario_keys:
            eu_kwh = scenarios[sk]['end_uses'].get(eu, 0)
            eu_eui = eu_kwh / gfa if gfa else 0
            vals.append(eu_eui)

        ax.bar(x, vals, bottom=bottom, label=eu.replace('_', ' ').title(),
               color=END_USE_COLORS[eu], width=0.6, zorder=3)
        bottom += np.array(vals)

    ax.set_xticks(x)
    ax.set_xticklabels(scenario_labels, fontsize=8)
    ax.set_ylabel('Site EUI (kWh/ft²·yr)', fontsize=9)
    ax.legend(loc='upper right', fontsize=7, ncol=1)
    ax.grid(axis='y', alpha=0.3, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()

    return fig_to_base64(fig)


def build_all(report: dict) -> dict:
    return {
        'eui_bar': build_eui_bar_chart(report),
        'end_use_stack': build_end_use_chart(report),
    }

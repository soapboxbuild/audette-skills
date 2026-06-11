"""
Artifact Builder - Generate interactive HTML artifacts from ScenarioEngine results.

This module creates self-contained HTML files with Chart.js visualizations,
sortable tables, and persistent user preferences via window.storage API.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup  # FIX: For Chart.js bundle (prevents HTML entity encoding)

logger = logging.getLogger(__name__)


# FIX: Audette design system palette (hot pink accent, grey scale progression)
END_USE_COLORS = {
    'heating': '#EB15AD',  # Hot pink (primary accent)
    'cooling': '#020401',  # Off-black
    'interior_lighting': '#667085',  # Dark grey
    'interior_equipment': '#A896C5',  # Plum (mid-tone)
    'fans': '#E8E8E8',  # Mid grey
    'pumps': '#F3F3F6',  # Light grey
    'dhw': '#EF81DA'  # Mid pink
}


class ArtifactBuilder:
    """Generates interactive HTML artifacts from ScenarioEngine results."""

    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize Jinja2 environment with custom filters.

        Args:
            template_dir: Path to templates directory. Defaults to lib/templates.
        """
        if template_dir:
            self.template_dir = Path(template_dir)
        else:
            self.template_dir = Path(__file__).parent / 'templates'

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )

        # Register custom filters
        self.env.filters['format_number'] = self._format_number

        # FIX Bug 9: Load Chart.js bundle for inline embedding
        # FIX: Wrap in Markup() to prevent Jinja2 autoescape from HTML-entity-encoding the bundle
        chartjs_path = self.template_dir / 'chart.umd.min.js'
        if chartjs_path.exists():
            with open(chartjs_path) as f:
                # Markup tells Jinja2 this is safe HTML, preventing " → &#34; conversion
                self.chartjs_bundle = Markup(f.read())
        else:
            logger.warning(f"Chart.js bundle not found at {chartjs_path}, using CDN fallback")
            self.chartjs_bundle = None

        logger.info(f"ArtifactBuilder initialized with template_dir: {self.template_dir}")

    def _prepare_chart_data(self, results: Dict) -> Dict:
        """
        Transform results into Chart.js dataset format.

        Args:
            results: Output from ScenarioEngine.run_all_scenarios()

        Returns:
            {
                'labels': ['Baseline', 'Reference', '90.1-2022', 'Retrofit'],
                'datasets': [
                    {
                        'label': 'Heating',
                        'data': [45.2, 52.1, 38.7, 30.2],
                        'backgroundColor': '#F94646',
                        'stack': 'energy'
                    },
                    ...
                ]
            }
        """
        scenarios = ['baseline', 'reference', 'code_2022', 'retrofit']
        end_use_labels = ['heating', 'cooling', 'interior_lighting',
                          'interior_equipment', 'fans', 'pumps', 'dhw']

        # Prepare labels
        labels = []
        for scenario in scenarios:
            label = self._get_scenario_label(scenario, results[scenario]['success'])
            labels.append(label)

        # Prepare datasets (one per end-use)
        datasets = []
        for end_use in end_use_labels:
            data = []
            for scenario in scenarios:
                if results[scenario]['success']:
                    end_uses = results[scenario]['raw'].get('end_uses_kwh', {})
                    kwh = end_uses.get(end_use, 0)
                    area = results[scenario]['raw'].get('conditioned_area_ft2', 1)
                    # Convert to kWh/sf and round to 2 decimals
                    data.append(round(kwh / area, 2))
                else:
                    # Failed scenario - null value (Chart.js will skip)
                    data.append(None)

            datasets.append({
                'label': end_use.replace('_', ' ').title(),
                'data': data,
                'backgroundColor': self._get_end_use_color(end_use),
                'stack': 'energy'
            })

        return {
            'labels': labels,
            'datasets': datasets
        }

    def _get_end_use_color(self, end_use: str) -> str:
        """Return consistent color for end-use category."""
        return END_USE_COLORS.get(end_use, '#808080')

    def _get_scenario_label(self, scenario: str, success: bool) -> str:
        """Return scenario label with failure indicator if needed."""
        labels = {
            'baseline': 'Audette Baseline',
            'reference': 'DoE Reference',
            'code_2022': '90.1-2022',
            'retrofit': 'Audette Retrofit'
        }
        label = labels.get(scenario, scenario)
        return label if success else f"{label} ⚠️"

    def _prepare_table_data(self, results: Dict) -> List[Dict]:
        """
        Transform results into table rows.

        CHANGED: Now uses 90.1-2022 code as benchmark instead of baseline.
        All deltas are vs code_2022 (the compliance target).

        Args:
            results: Output from ScenarioEngine.run_all_scenarios()

        Returns:
            [
                {'scenario': 'Baseline', 'success': True, 'eui': 85.3, 'savings_pct': -15.2, ...},
                {'scenario': '90.1-2022', 'success': True, 'eui': 72.1, 'savings_pct': None, ...},
                {'scenario': 'Retrofit', 'success': True, 'eui': 65.3, 'savings_pct': 9.4, ...},
                ...
            ]
        """
        scenarios = ['baseline', 'reference', 'code_2022', 'retrofit']
        scenario_names = {
            'baseline': 'Audette Baseline',
            'reference': 'DoE Reference',
            'code_2022': '90.1-2022 (Benchmark)',
            'retrofit': 'Audette Retrofit'
        }

        table_data = []

        for scenario in scenarios:
            scenario_result = results[scenario]
            row = {
                'scenario': scenario_names[scenario],
                'success': scenario_result['success']
            }

            if scenario_result['success']:
                raw = scenario_result['raw']

                # Basic metrics
                row['eui'] = raw['eui_kwh_per_sf']
                row['total'] = raw['total_site_energy_kwh']
                row['unmet_hrs'] = raw['unmet_heating_hours'] + raw['unmet_cooling_hours']

                # Deltas (only if not code_2022 - it's the benchmark)
                if scenario == 'code_2022':
                    row['savings_pct'] = None
                    row['savings_kwh'] = None
                    row['cost'] = None
                    row['compliance'] = None  # Benchmark has 0% margin by definition
                else:
                    vs_code = scenario_result.get('vs_code_2022', {})
                    row['savings_pct'] = vs_code.get('energy_savings_pct')
                    row['savings_kwh'] = vs_code.get('energy_savings_kwh')
                    row['cost'] = vs_code.get('cost_savings_annual')

                    # All non-code scenarios show compliance margin
                    # Positive = better than code, Negative = worse than code
                    row['compliance'] = vs_code.get('energy_savings_pct')
            else:
                # Failed scenario - populate with None
                row['eui'] = None
                row['total'] = None
                row['savings_pct'] = None
                row['savings_kwh'] = None
                row['cost'] = None
                row['compliance'] = None
                row['unmet_hrs'] = None
                row['error'] = scenario_result.get('error', 'Simulation failed')

            table_data.append(row)

        return table_data

    def _prepare_explorer_data(self, results: Dict) -> Dict:
        """
        Transform results into accordion structure for explorer tab.

        Args:
            results: Output from ScenarioEngine.run_all_scenarios()

        Returns:
            {
                'baseline': {
                    'summary': {
                        'total_kwh': 125000,
                        'area_ft2': 10764,
                        'unmet_heating': 10.5,
                        'unmet_cooling': 5.2
                    },
                    'end_uses': {
                        'heating': {'kwh': 48672, 'kwh_per_sf': 4.52, 'pct': 38.9},
                        ...
                    }
                },
                ...
            }
        """
        scenarios = ['baseline', 'reference', 'code_2022', 'retrofit']
        explorer_data = {}

        for scenario in scenarios:
            scenario_result = results[scenario]

            if not scenario_result['success']:
                explorer_data[scenario] = {'success': False}
                continue

            raw = scenario_result['raw']
            total_kwh = raw['total_site_energy_kwh']
            area = raw['conditioned_area_ft2']

            # Summary metrics
            summary = {
                'total_kwh': total_kwh,
                'area_ft2': area,
                'unmet_heating': raw['unmet_heating_hours'],
                'unmet_cooling': raw['unmet_cooling_hours']
            }

            # End-use breakdown
            end_uses = {}
            for end_use, kwh in raw.get('end_uses_kwh', {}).items():
                end_uses[end_use] = {
                    'kwh': kwh,
                    'kwh_per_sf': round(kwh / area, 1),
                    'pct': round((kwh / total_kwh) * 100, 1)
                }

            explorer_data[scenario] = {
                'success': True,
                'summary': summary,
                'end_uses': end_uses
            }

        return explorer_data

    def _validate_results(self, results: Dict) -> None:
        """
        Validate results structure and provenance, add defaults for missing metadata.

        CRITICAL: This validates that all successful scenarios have proper provenance
        tags indicating they came from actual EnergyPlus simulations. Results without
        provenance or with non-EnergyPlus sources are rejected.

        Args:
            results: Output from ScenarioEngine.run_all_scenarios()

        Raises:
            ValueError: If results structure is invalid or provenance is missing
        """
        required_keys = ['baseline', 'reference', 'code_2022', 'retrofit', 'metadata']

        for key in required_keys:
            if key not in results:
                raise ValueError(f"Missing required key: {key}")

        # CRITICAL: Validate provenance for all successful scenarios
        # This prevents rendering of results from mock/fake data
        scenarios = ['baseline', 'reference', 'code_2022', 'retrofit']
        for scenario in scenarios:
            scenario_result = results[scenario]

            # Only validate successful scenarios
            if scenario_result.get('success', False):
                raw_results = scenario_result.get('raw', {})

                # Check for provenance tag
                source = raw_results.get('source')

                if source is None:
                    raise ValueError(
                        f"PROVENANCE ERROR: Scenario '{scenario}' is marked successful but "
                        f"has no 'source' field. This indicates the result may not be from "
                        f"actual EnergyPlus simulation. Cannot render artifact for compliance "
                        f"analysis without verified simulation provenance."
                    )

                if source != 'energyplus':
                    raise ValueError(
                        f"PROVENANCE ERROR: Scenario '{scenario}' has source='{source}' but "
                        f"only source='energyplus' is permitted for compliance analysis. "
                        f"Mock or synthetic data cannot be used for regulatory reporting."
                    )

                logger.info(f"Provenance validated for {scenario}: source={source}")

        # Add default metadata if missing
        if 'building_name' not in results['metadata']:
            results['metadata']['building_name'] = 'Unknown Building'
            logger.warning("Missing building_name in metadata, using default")

        if 'climate_zone' not in results['metadata']:
            results['metadata']['climate_zone'] = 'Unknown'
            logger.warning("Missing climate_zone in metadata, using default")

    @staticmethod
    def _format_number(value: float) -> str:
        """Format number with thousands separators: 125000 → '125,000'"""
        return f"{value:,.0f}"

    def build_artifact(self, results: Dict) -> str:
        """
        Generate single-file HTML artifact with tabs.

        Args:
            results: Output from ScenarioEngine.run_all_scenarios()

        Returns:
            HTML string ready for Claude Desktop artifact rendering

        Raises:
            ValueError: If results structure invalid or artifact >2MB
        """
        # Validate input
        self._validate_results(results)

        # Check if all scenarios failed
        successful_count = sum(
            1 for s in ['baseline', 'reference', 'code_2022', 'retrofit']
            if results[s]['success']
        )

        if successful_count == 0:
            return self._build_error_artifact(results)

        # Prepare data
        chart_data = self._prepare_chart_data(results)
        table_data = self._prepare_table_data(results)
        explorer_data = self._prepare_explorer_data(results)

        # Load template
        template = self.env.get_template('egc_artifact.html.j2')

        # Render
        html = template.render(
            results=results,
            chart_data_json=json.dumps(chart_data),
            table_data=table_data,
            explorer_data=explorer_data,
            metadata=results['metadata'],
            scenario_names={
                'baseline': 'Audette Baseline',
                'reference': 'DoE Reference',
                'code_2022': '90.1-2022 Benchmark',
                'retrofit': 'Audette Retrofit'
            },
            chartjs_bundle=self.chartjs_bundle  # FIX Bug 9: Pass inline Chart.js
        )

        # Validate size
        self._validate_size(html)

        return html

    def _build_error_artifact(self, results: Dict) -> str:
        """Generate minimal error artifact when all scenarios fail."""
        template = self.env.get_template('error_artifact.html.j2')
        return template.render(
            building_name=results['metadata'].get('building_name', 'Unknown'),
            errors={
                scenario: results[scenario].get('error', 'Unknown error')
                for scenario in ['baseline', 'reference', 'code_2022', 'retrofit']
            }
        )

    def _validate_size(self, html: str) -> None:
        """
        Check artifact size.

        Raises:
            ValueError: If >2MB (hard limit)

        Warns:
            If >500KB (soft limit)
        """
        size_bytes = len(html.encode('utf-8'))
        size_kb = size_bytes / 1024

        if size_kb > 2048:  # 2MB hard limit
            raise ValueError(f"Artifact too large: {size_kb:.1f}KB (max 2048KB)")

        if size_kb > 500:  # Soft warning
            logger.warning(f"Artifact size {size_kb:.1f}KB exceeds recommended 500KB limit")

        logger.info(f"Artifact size: {size_kb:.1f}KB")

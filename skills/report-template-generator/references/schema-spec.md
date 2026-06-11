# Report Schema Specification

The schema file (`schema.json`) is the contract between a report template and its
data. Every `{{placeholder}}` in the markdown template must have a matching entry
here, and vice versa.

## Top-level structure

```json
{
  "report_name": "Human-readable report title",
  "version": "1.0",
  "description": "What this report is for and who reads it",
  "fields": {
    "field_name": { ... }
  },
  "sections": {
    "section_name": { ... }
  }
}
```

## Field definition

Each field in the `fields` object:

```json
{
  "field_name": {
    "type": "string",
    "description": "What this field represents",
    "required": true,
    "source_hint": "audette_mcp:get_building_model_details.building_name",
    "default": null,
    "example": "123 Main Street Office Tower",
    "format": null
  }
}
```

### Field types

| Type | Description | Example value |
|------|-------------|---------------|
| `string` | Plain text | `"123 Main St"` |
| `number` | Numeric value (integer or decimal) | `45000` |
| `date` | ISO date string | `"2025-03-15"` |
| `boolean` | True/false flag | `true` |
| `array` | List of items (for repeating rows) | `[{"name": "RTU-1", "age": 12}]` |
| `object` | Nested group of fields | `{"street": "123 Main", "city": "Toronto"}` |
| `currency` | Number displayed as money | `125000.00` |
| `percentage` | Number displayed as percent | `0.85` |

### Source hints

The `source_hint` tells the generated skill where to look for data. Format:

```
<provider>:<tool_or_method>.<field_path>
```

Examples:
- `audette_mcp:get_building_model_details.building_name` — pull from Audette MCP
- `audette_mcp:get_equipment_survey.equipment_list` — equipment survey data
- `audette_mcp:get_carbon_reduction_plan_by_id.measures` — carbon plan measures
- `audette_mcp:get_building_model_report.energy_use_intensity` — building metrics
- `user_input` — ask the user to provide this value
- `calculated:field_a / field_b` — derived from other fields
- `static:Audette Inc.` — hardcoded value, same every time

When `source_hint` is an Audette MCP tool, the generated skill will try to call
that tool first. If the MCP isn't connected, it falls back to asking the user.

### Format strings

Optional `format` field controls display:

| Format | Effect | Example |
|--------|--------|---------|
| `"comma"` | Thousands separator | `45,000` |
| `"decimal:2"` | Fixed decimal places | `85.50` |
| `"currency:USD"` | Dollar formatting | `$125,000.00` |
| `"currency:CAD"` | Canadian dollar | `CA$125,000.00` |
| `"percent"` | Multiply by 100 + % | `85%` |
| `"date:long"` | Full date | `March 15, 2025` |
| `"date:short"` | Compact date | `2025-03-15` |

## Section definition (optional)

Sections group fields and can be marked conditional:

```json
{
  "sections": {
    "energy_analysis": {
      "description": "Energy consumption breakdown",
      "condition": "has_energy_data",
      "fields": ["annual_energy_kwh", "energy_use_intensity", "energy_cost"]
    }
  }
}
```

When `condition` references a boolean field, the entire section is included or
excluded based on that field's value.

## Array fields (for tables)

Array fields define the shape of each item:

```json
{
  "equipment_list": {
    "type": "array",
    "description": "List of major equipment",
    "required": true,
    "source_hint": "audette_mcp:get_equipment_survey.equipment",
    "items": {
      "name": { "type": "string", "description": "Equipment name" },
      "type": { "type": "string", "description": "Equipment category" },
      "age_years": { "type": "number", "description": "Age in years" },
      "condition": { "type": "string", "description": "Good/Fair/Poor" },
      "replacement_cost": { "type": "currency", "description": "Estimated cost" }
    },
    "example": [
      {
        "name": "RTU-1",
        "type": "Rooftop Unit",
        "age_years": 15,
        "condition": "Poor",
        "replacement_cost": 45000
      },
      {
        "name": "Boiler-1",
        "type": "Gas Boiler",
        "age_years": 8,
        "condition": "Fair",
        "replacement_cost": 30000
      }
    ]
  }
}
```

In the markdown template, array fields use the `{{#each}}` helper:

```markdown
| Equipment | Type | Age | Condition | Est. Cost |
|-----------|------|-----|-----------|-----------|
{{#each equipment_list}}
| {{name}} | {{type}} | {{age_years}} | {{condition}} | {{format_currency replacement_cost}} |
{{/each}}
```

# .rag-scripts/schema_loader.py
import yaml
import json
from pathlib import Path
from typing import Dict, Any


class SchemaValidationError(Exception):
    """Raised when schema validation fails"""
    pass


class SchemaLoader:
    """Loads and validates extraction schemas from YAML or JSON files"""

    def __init__(self, schema_path: Path):
        self.schema_path = Path(schema_path)
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

    def load(self) -> Dict[str, Any]:
        """Load schema from file and validate structure"""
        if self.schema_path.suffix in ['.yaml', '.yml']:
            with open(self.schema_path, 'r') as f:
                schema = yaml.safe_load(f)
        elif self.schema_path.suffix == '.json':
            with open(self.schema_path, 'r') as f:
                schema = json.load(f)
        else:
            raise ValueError(f"Unsupported schema format: {self.schema_path.suffix}")

        self.validate(schema)
        return schema

    def validate(self, schema: Dict[str, Any]) -> None:
        """Validate schema has required structure"""
        if schema is None:
            raise SchemaValidationError("Schema is empty or invalid")
        if "fields" not in schema:
            raise SchemaValidationError("Schema missing required key: fields")

        for field_name, field_spec in schema["fields"].items():
            required_keys = ["label", "type", "search_terms"]
            for key in required_keys:
                if key not in field_spec:
                    raise SchemaValidationError(
                        f"Field '{field_name}' missing required key: {key}"
                    )

            valid_types = ["text", "number", "date", "table_sum", "table_row"]
            if field_spec["type"] not in valid_types:
                raise SchemaValidationError(
                    f"Field '{field_name}' has invalid type: {field_spec['type']}"
                )

            if not isinstance(field_spec["search_terms"], list):
                raise SchemaValidationError(
                    f"Field '{field_name}' search_terms must be a list"
                )

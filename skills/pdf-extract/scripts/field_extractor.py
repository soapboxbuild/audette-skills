# .rag-scripts/field_extractor.py
from typing import List, Dict, Any, Tuple, Optional
from extractors import TextProximityExtractor, TableCellExtractor, RegexExtractor
import re


class FieldExtractor:
    """Orchestrates multiple extraction strategies to find field values"""

    def __init__(self, pages_text: List[str], tables: List[Tuple[int, List[List[str]]]]):
        self.pages_text = pages_text
        self.tables = tables
        self.text_extractor = TextProximityExtractor()
        self.table_extractor = TableCellExtractor()
        self.regex_extractor = RegexExtractor()

    def extract_field(self, field_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract a single field using multiple strategies

        Args:
            field_spec: Field specification from schema

        Returns:
            {
                "value": extracted value (cleaned/typed) or None,
                "page": page number where found (1-indexed) or None,
                "confidence": "high" | "medium" | "low" | "none",
                "method": extraction method or None
            }
        """
        search_terms = field_spec["search_terms"]
        fallback_terms = field_spec.get("fallback", [])
        all_terms = search_terms + fallback_terms

        page_range = field_spec.get("page_range")
        pattern = field_spec.get("pattern")
        field_type = field_spec["type"]

        # Filter pages by range
        pages_to_search = self._filter_pages_by_range(page_range)

        # Strategy 1: Try table extraction first (highest confidence)
        if self.tables:
            tables_in_range = self._filter_tables_by_range(page_range)
            table_result = self.table_extractor.extract(
                tables=[t[1] for t in tables_in_range],
                search_terms=all_terms,
                pattern=pattern
            )
            if table_result["value"] is not None:
                # Find which page this came from
                page_num = tables_in_range[0][0] if tables_in_range else None
                return self._format_result(table_result, page_num, field_type)

        # Strategy 2: Try text proximity on each page
        for page_idx, page_text in pages_to_search:
            text_result = self.text_extractor.extract(
                text=page_text,
                search_terms=all_terms,
                pattern=pattern
            )
            if text_result["value"] is not None:
                return self._format_result(text_result, page_idx + 1, field_type)

        # Strategy 3: Regex fallback if pattern provided
        if pattern:
            combined_text = "\n".join([p[1] for p in pages_to_search])
            regex_result = self.regex_extractor.extract(
                text=combined_text,
                search_terms=all_terms,
                pattern=pattern
            )
            if regex_result["value"] is not None:
                # Can't determine exact page with regex, use first page in range
                page_num = pages_to_search[0][0] + 1 if pages_to_search else None
                return self._format_result(regex_result, page_num, field_type)

        # Not found
        return {
            "value": None,
            "page": None,
            "confidence": "none",
            "method": None
        }

    def _filter_pages_by_range(self, page_range: Optional[List[int]]) -> List[Tuple[int, str]]:
        """Return (page_index, text) tuples for pages in range"""
        if not page_range:
            return list(enumerate(self.pages_text))

        start_idx = page_range[0] - 1
        end_idx = page_range[1]

        return [(i, text) for i, text in enumerate(self.pages_text) if start_idx <= i < end_idx]

    def _filter_tables_by_range(self, page_range: Optional[List[int]]) -> List[Tuple[int, List[List[str]]]]:
        """Return tables that fall within page range"""
        if not page_range:
            return self.tables

        return [
            (page_num, table)
            for page_num, table in self.tables
            if page_range[0] <= page_num <= page_range[1]
        ]

    def _format_result(self, result: Dict[str, Any], page_num: Optional[int], field_type: str) -> Dict[str, Any]:
        """Clean and type-convert extracted value"""
        value = result["value"]

        # Type conversion and cleaning
        if value is not None:
            if field_type == "number":
                # Remove commas and convert to int/float
                value = str(value).replace(",", "").strip()
                try:
                    value = int(value) if "." not in value else float(value)
                except ValueError:
                    # Try to extract first number found
                    match = re.search(r"[\d,]+\.?\d*", str(value))
                    if match:
                        value = match.group(0).replace(",", "")
                        value = int(value) if "." not in value else float(value)
                    else:
                        value = None
            elif field_type == "text":
                value = str(value).strip()

        return {
            "value": value,
            "page": page_num,
            "confidence": result["confidence"],
            "method": result["method"]
        }

# .rag-scripts/extractors.py
import re
from typing import Dict, Any, List, Optional


class BaseExtractor:
    """Base class for field extraction strategies"""

    def extract(self, text: str, search_terms: List[str], pattern: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract field value from text

        Returns:
            {
                "value": extracted value or None,
                "confidence": "high" | "medium" | "low" | "none",
                "method": extraction method name or None
            }
        """
        raise NotImplementedError


class TextProximityExtractor(BaseExtractor):
    """Extract value near search term label"""

    def extract(self, text: str, search_terms: List[str], pattern: Optional[str] = None) -> Dict[str, Any]:
        lines = text.split('\n')

        for search_term in search_terms:
            for i, line in enumerate(lines):
                if search_term.lower() in line.lower():
                    # Try same line first (after colon or label)
                    same_line_match = self._extract_from_same_line(line, search_term)
                    if same_line_match:
                        return {
                            "value": same_line_match,
                            "confidence": "high",
                            "method": "text_proximity"
                        }

                    # Try next line
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line:
                            return {
                                "value": next_line,
                                "confidence": "medium",
                                "method": "text_proximity"
                            }

        return {"value": None, "confidence": "none", "method": None}

    def _extract_from_same_line(self, line: str, search_term: str) -> Optional[str]:
        """Extract value from same line as label"""
        # Find the search term and extract what comes after
        pattern = re.escape(search_term) + r'\s*:?\s*(.+)'
        match = re.search(pattern, line, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            # Reject if it's just a colon or empty
            if value and value != ':':
                return value
        return None


class TableCellExtractor(BaseExtractor):
    """Extract value from table cells"""

    def extract(self, tables: List[List[List[str]]], search_terms: List[str], pattern: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract from pdfplumber table structures

        Args:
            tables: List of tables, each table is list of rows, each row is list of cells
            search_terms: Terms to search for in table cells
            pattern: Optional regex to validate extracted value
        """
        for table in tables:
            for row_idx, row in enumerate(table):
                for col_idx, cell in enumerate(row):
                    if cell is None:
                        continue

                    # Check if cell contains search term
                    for search_term in search_terms:
                        if search_term.lower() in str(cell).lower():
                            # Look for value in adjacent cells (right, then below)
                            value = self._get_adjacent_value(table, row_idx, col_idx)
                            if value:
                                if pattern and not re.search(pattern, value):
                                    continue
                                return {
                                    "value": value,
                                    "confidence": "high",
                                    "method": "table_cell"
                                }

        return {"value": None, "confidence": "none", "method": None}

    def _get_adjacent_value(self, table: List[List[str]], row_idx: int, col_idx: int) -> Optional[str]:
        """Get value from cell to the right or below"""
        row = table[row_idx]

        # Try cell to the right
        if col_idx + 1 < len(row):
            right_cell = row[col_idx + 1]
            if right_cell and str(right_cell).strip():
                return str(right_cell).strip()

        # Try cell below
        if row_idx + 1 < len(table):
            next_row = table[row_idx + 1]
            if col_idx < len(next_row):
                below_cell = next_row[col_idx]
                if below_cell and str(below_cell).strip():
                    return str(below_cell).strip()

        return None


class RegexExtractor(BaseExtractor):
    """Extract using regex pattern fallback"""

    def extract(self, text: str, search_terms: List[str], pattern: Optional[str] = None) -> Dict[str, Any]:
        if not pattern:
            return {"value": None, "confidence": "none", "method": None}

        # Find section of text near search terms
        for search_term in search_terms:
            search_pos = text.lower().find(search_term.lower())
            if search_pos >= 0:
                # Search in vicinity (200 chars after the term)
                context = text[search_pos:search_pos + 200]
                match = re.search(pattern, context)
                if match:
                    return {
                        "value": match.group(0),
                        "confidence": "medium",
                        "method": "regex"
                    }

        # Full text fallback
        match = re.search(pattern, text)
        if match:
            return {
                "value": match.group(0),
                "confidence": "low",
                "method": "regex"
            }

        return {"value": None, "confidence": "none", "method": None}

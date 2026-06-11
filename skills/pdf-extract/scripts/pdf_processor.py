"""PDF text and table extraction using pdfplumber."""
from pathlib import Path
from typing import List, Optional, Tuple
import pdfplumber


class PDFProcessor:
    """Extract text and tables from PDF files."""

    def __init__(self, pdf_path: Path):
        """Initialize PDF processor.

        Args:
            pdf_path: Path to PDF file

        Raises:
            FileNotFoundError: If PDF file does not exist
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    def get_page_count(self) -> int:
        """Get total number of pages in PDF.

        Returns:
            Number of pages
        """
        with pdfplumber.open(self.pdf_path) as pdf:
            return len(pdf.pages)

    def extract_text(self, page_range: Optional[List[int]] = None) -> List[str]:
        """Extract text from PDF pages.

        Args:
            page_range: Optional [start, end] page range (1-indexed, inclusive).
                       If None, extracts all pages.

        Returns:
            List of text strings, one per page
        """
        texts = []
        with pdfplumber.open(self.pdf_path) as pdf:
            total_pages = len(pdf.pages)

            # Determine page range
            if page_range:
                start_page = max(1, page_range[0])
                end_page = min(total_pages, page_range[1])
            else:
                start_page = 1
                end_page = total_pages

            # Extract text from each page (convert to 0-indexed)
            for page_num in range(start_page - 1, end_page):
                page = pdf.pages[page_num]
                text = page.extract_text() or ""
                texts.append(text)

        return texts

    def extract_tables(self, page_range: Optional[List[int]] = None) -> List[Tuple[int, List[List[str]]]]:
        """Extract tables from PDF pages.

        Args:
            page_range: Optional [start, end] page range (1-indexed, inclusive).
                       If None, extracts from all pages.

        Returns:
            List of tuples: (page_number, table_data)
            where table_data is a list of rows, each row is a list of cell values
        """
        tables = []
        with pdfplumber.open(self.pdf_path) as pdf:
            total_pages = len(pdf.pages)

            # Determine page range
            if page_range:
                start_page = max(1, page_range[0])
                end_page = min(total_pages, page_range[1])
            else:
                start_page = 1
                end_page = total_pages

            # Extract tables from each page (convert to 0-indexed)
            for page_num in range(start_page - 1, end_page):
                page = pdf.pages[page_num]
                page_tables = page.extract_tables()

                # Add each table found on this page
                for table in page_tables:
                    # Convert 0-indexed page_num back to 1-indexed for return value
                    tables.append((page_num + 1, table))

        return tables

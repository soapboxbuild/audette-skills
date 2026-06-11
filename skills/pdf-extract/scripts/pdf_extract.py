#!/usr/bin/env python3
"""
PDF Extraction Framework
Schema-driven extraction of structured data from PDFs
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import glob

from schema_loader import SchemaLoader
from pdf_processor import PDFProcessor
from field_extractor import FieldExtractor


def extract_from_pdf(pdf_path: Path, schema_path: Path) -> Dict[str, Any]:
    """
    Extract fields from a single PDF using schema

    Args:
        pdf_path: Path to PDF file
        schema_path: Path to extraction schema (YAML/JSON)

    Returns:
        Dictionary with source_file and extracted fields
    """
    # Load schema
    loader = SchemaLoader(schema_path)
    schema = loader.load()

    # Extract PDF content
    processor = PDFProcessor(pdf_path)
    pages_text = processor.extract_text()
    tables = processor.extract_tables()

    # Extract each field
    extractor = FieldExtractor(pages_text, tables)
    extracted_fields = {}

    for field_name, field_spec in schema["fields"].items():
        result = extractor.extract_field(field_spec)
        extracted_fields[field_name] = result

    return {
        "source_file": pdf_path.name,
        "fields": extracted_fields
    }


def extract_batch(pdf_pattern: str, schema_path: Path) -> List[Dict[str, Any]]:
    """
    Extract from multiple PDFs matching a glob pattern

    Args:
        pdf_pattern: Glob pattern for PDF files
        schema_path: Path to extraction schema

    Returns:
        List of extraction results
    """
    pdf_files = glob.glob(pdf_pattern)
    results = []

    for pdf_file in pdf_files:
        try:
            result = extract_from_pdf(Path(pdf_file), schema_path)
            results.append(result)
            print(f"✓ Extracted from {pdf_file}", file=sys.stderr)
        except Exception as e:
            print(f"✗ Failed to extract from {pdf_file}: {e}", file=sys.stderr)

    return results


def dump_pdf_content(pdf_path: Path, dump_text: bool = False, dump_tables: bool = False, pages: str = None):
    """
    Dump raw PDF content for exploration

    Args:
        pdf_path: Path to PDF
        dump_text: Whether to dump text
        dump_tables: Whether to dump tables
        pages: Page range like "1-6"
    """
    processor = PDFProcessor(pdf_path)

    # Parse page range
    page_range = None
    if pages:
        if "-" in pages:
            start, end = pages.split("-")
            page_range = [int(start), int(end)]
        else:
            page_num = int(pages)
            page_range = [page_num, page_num]

    if dump_text:
        pages_text = processor.extract_text(page_range)
        for i, text in enumerate(pages_text):
            page_num = (page_range[0] if page_range else 1) + i
            print(f"\n{'='*60}")
            print(f"PAGE {page_num} TEXT")
            print(f"{'='*60}\n")
            print(text)

    if dump_tables:
        tables = processor.extract_tables(page_range)
        for page_num, table in tables:
            print(f"\n{'='*60}")
            print(f"PAGE {page_num} TABLE")
            print(f"{'='*60}\n")
            for row in table:
                print(" | ".join([str(cell) if cell else "" for cell in row]))


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Extract structured data from PDFs using schemas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract from single PDF
  %(prog)s report.pdf --schema schemas/freddie_mac_pca.yaml

  # Batch extraction
  %(prog)s "*.pdf" --schema schemas/freddie_mac_pca.yaml --output results.json

  # Dump PDF content for exploration
  %(prog)s report.pdf --dump-text --dump-tables --pages 1-6
        """
    )

    parser.add_argument("pdf", help="PDF file path or glob pattern")
    parser.add_argument("--schema", type=Path, help="Extraction schema (YAML/JSON)")
    parser.add_argument("--output", type=Path, help="Output JSON file (default: stdout)")
    parser.add_argument("--dump-text", action="store_true", help="Dump raw text content")
    parser.add_argument("--dump-tables", action="store_true", help="Dump extracted tables")
    parser.add_argument("--pages", help="Page range (e.g., 1-6 or 3)")

    args = parser.parse_args()

    # Dump mode (exploration)
    if args.dump_text or args.dump_tables:
        if "*" in args.pdf:
            print("Error: --dump-* modes require a single PDF file", file=sys.stderr)
            sys.exit(1)
        dump_pdf_content(Path(args.pdf), args.dump_text, args.dump_tables, args.pages)
        return

    # Extraction mode (requires schema)
    if not args.schema:
        print("Error: --schema required for extraction mode", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    # Single file or batch
    if "*" in args.pdf:
        results = extract_batch(args.pdf, args.schema)
    else:
        results = [extract_from_pdf(Path(args.pdf), args.schema)]

    # Output results
    output_json = json.dumps(results, indent=2)

    if args.output:
        args.output.write_text(output_json)
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Automatic extraction workflow:
1. Discover schemas from similar PDFs
2. Apply schemas for batch extraction
3. Output structured JSON

This is the "smart" workflow that doesn't require manual schema creation.
"""
import argparse
import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import List, Dict
import subprocess

sys.path.insert(0, str(Path(__file__).parent))
from discover_schemas import SchemaDiscovery
from pdf_processor import PDFProcessor
import yaml


def group_similar_pdfs(pdf_files: List[Path], max_groups: int = 5) -> Dict[str, List[Path]]:
    """
    Group PDFs by similarity (page count, file size as proxy).

    In a more advanced version, this could use:
    - Document structure similarity
    - Content similarity
    - Filename patterns

    For now: group by approximate page count ranges
    """
    groups = defaultdict(list)

    for pdf_path in pdf_files:
        try:
            processor = PDFProcessor(pdf_path)
            page_count = processor.get_page_count()

            # Group by page count bins (1-5, 6-15, 16-30, 31-50, 51+)
            if page_count <= 5:
                group_key = "1-5_pages"
            elif page_count <= 15:
                group_key = "6-15_pages"
            elif page_count <= 30:
                group_key = "16-30_pages"
            elif page_count <= 50:
                group_key = "31-50_pages"
            else:
                group_key = "51+_pages"

            groups[group_key].append(pdf_path)

        except Exception as e:
            print(f"Warning: Could not process {pdf_path.name}: {e}", file=sys.stderr)
            continue

    return dict(groups)


def auto_extract(
    pdf_files: List[Path],
    output_dir: Path,
    min_documents: int = 3,
    min_confidence: float = 0.6
) -> Dict:
    """
    Automatically discover schemas and extract from PDFs.

    Workflow:
    1. Group similar PDFs
    2. For each group with 3+ docs, discover schema
    3. Extract data using discovered schema
    4. Output results

    Returns:
        Dict with extraction statistics
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Processing {len(pdf_files)} PDF files...")
    print(f"Grouping similar documents...\n")

    # Group similar PDFs
    groups = group_similar_pdfs(pdf_files)

    print(f"Found {len(groups)} document groups:")
    for group_name, group_pdfs in groups.items():
        print(f"  - {group_name}: {len(group_pdfs)} documents")

    print()

    # Process each group
    results = {
        'groups_processed': 0,
        'schemas_discovered': 0,
        'documents_extracted': 0,
        'extractions': []
    }

    discovery = SchemaDiscovery(
        min_documents=min_documents,
        min_confidence=min_confidence
    )

    for group_name, group_pdfs in groups.items():
        print(f"\n{'='*60}")
        print(f"Processing group: {group_name} ({len(group_pdfs)} documents)")
        print(f"{'='*60}\n")

        if len(group_pdfs) < min_documents:
            print(f"Skipping: need at least {min_documents} documents (got {len(group_pdfs)})\n")
            continue

        # Discover schema for this group
        schema = discovery.discover(group_pdfs)

        if not schema:
            print(f"Could not discover schema for group {group_name}\n")
            continue

        results['schemas_discovered'] += 1

        # Save discovered schema
        schema_path = output_dir / f"schema_{group_name}.yaml"
        clean_schema = {'fields': {}}
        for field_name, field_spec in schema['fields'].items():
            clean_spec = {k: v for k, v in field_spec.items() if not k.startswith('_')}
            clean_schema['fields'][field_name] = clean_spec

        with open(schema_path, 'w') as f:
            f.write(f"# Auto-discovered schema for: {group_name}\n")
            f.write(f"# Documents: {len(group_pdfs)}\n\n")
            yaml.dump(clean_schema, f, sort_keys=False, default_flow_style=False)

        print(f"✓ Schema saved: {schema_path}")

        # Extract from PDFs using discovered schema
        print(f"Extracting data from {len(group_pdfs)} documents...")

        extract_script = Path(__file__).parent / "pdf_extract.py"
        output_json = output_dir / f"extracted_{group_name}.json"

        # Build list of PDF paths for extraction
        pdf_list = " ".join([f'"{str(p)}"' for p in group_pdfs])

        # Run extraction
        cmd = [
            'python3',
            str(extract_script),
            *[str(p) for p in group_pdfs],
            '--schema', str(schema_path),
            '--output', str(output_json)
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                # Load results to count
                with open(output_json) as f:
                    extractions = json.load(f)
                    results['documents_extracted'] += len(extractions)
                    results['extractions'].extend(extractions)

                print(f"✓ Extracted {len(extractions)} documents → {output_json}")
            else:
                print(f"✗ Extraction failed: {result.stderr}", file=sys.stderr)

        except subprocess.TimeoutExpired:
            print(f"✗ Extraction timeout", file=sys.stderr)
        except Exception as e:
            print(f"✗ Extraction error: {e}", file=sys.stderr)

        results['groups_processed'] += 1

    # Save combined results
    if results['extractions']:
        combined_output = output_dir / "all_extractions.json"
        with open(combined_output, 'w') as f:
            json.dump(results['extractions'], f, indent=2)
        print(f"\n✓ Combined extractions saved: {combined_output}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Automatic PDF extraction with schema discovery',
        epilog="""
Example:
  # Process all PDFs, auto-discover schemas, extract data
  %(prog)s documents/*.pdf --output results/

This will:
  1. Group similar PDFs
  2. Discover schemas for each group (3+ docs)
  3. Extract data using discovered schemas
  4. Save schemas and extracted data to output directory
        """
    )

    parser.add_argument(
        'pdfs',
        nargs='+',
        help='PDF files to process'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('extracted'),
        help='Output directory for schemas and data (default: extracted/)'
    )
    parser.add_argument(
        '--min-documents',
        type=int,
        default=3,
        help='Minimum documents for schema discovery (default: 3)'
    )
    parser.add_argument(
        '--min-confidence',
        type=float,
        default=0.6,
        help='Minimum field confidence (default: 0.6)'
    )

    args = parser.parse_args()

    # Convert to Path objects
    pdf_files = [Path(p) for p in args.pdfs]
    pdf_files = [p for p in pdf_files if p.exists() and p.suffix.lower() == '.pdf']

    if not pdf_files:
        print("Error: No valid PDF files found", file=sys.stderr)
        sys.exit(1)

    # Run auto-extraction
    results = auto_extract(
        pdf_files=pdf_files,
        output_dir=args.output,
        min_documents=args.min_documents,
        min_confidence=args.min_confidence
    )

    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Groups processed: {results['groups_processed']}")
    print(f"Schemas discovered: {results['schemas_discovered']}")
    print(f"Documents extracted: {results['documents_extracted']}")
    print(f"\nOutput directory: {args.output}/")
    print(f"  - Schemas: schema_*.yaml")
    print(f"  - Extracted data: extracted_*.json")
    print(f"  - Combined: all_extractions.json")


if __name__ == '__main__':
    main()

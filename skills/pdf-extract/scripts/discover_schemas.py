#!/usr/bin/env python3
"""
Automatic schema discovery from PDF documents.

Analyzes a batch of PDFs, detects common patterns, and generates extraction schemas
automatically when 3+ documents share similar structure.
"""
import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict, Counter
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from pdf_processor import PDFProcessor
import yaml


class PatternDetector:
    """Detects common patterns across multiple PDFs."""

    def __init__(self):
        self.label_patterns = [
            # Common label formats
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*:',  # "Property Name:"
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*-',  # "Property Name -"
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\|', # "Property Name |"
        ]

        self.number_pattern = r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b'
        self.year_pattern = r'\b(19|20)\d{2}\b'
        self.currency_pattern = r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?'

    def extract_labels(self, text: str) -> Set[str]:
        """Extract potential field labels from text."""
        labels = set()

        for pattern in self.label_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                label = match.group(1).strip()
                # Filter out very short or very long labels
                if 3 <= len(label) <= 50 and not label.isdigit():
                    labels.add(label)

        return labels

    def detect_field_type(self, value: str) -> str:
        """Detect the likely type of a field value."""
        value = value.strip()

        if re.match(self.currency_pattern, value):
            return 'number'
        elif re.match(self.year_pattern, value):
            return 'number'
        elif re.match(r'^\d{1,3}(?:,\d{3})*(?:\.\d+)?$', value):
            return 'number'
        elif re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}$', value):
            return 'date'
        else:
            return 'text'


class SchemaDiscovery:
    """Discovers schemas from a batch of PDFs."""

    def __init__(self, min_documents: int = 3, min_confidence: float = 0.6):
        """
        Args:
            min_documents: Minimum number of documents needed to create a schema
            min_confidence: Minimum percentage of documents that must share a field (0.0-1.0)
        """
        self.min_documents = min_documents
        self.min_confidence = min_confidence
        self.pattern_detector = PatternDetector()

    def analyze_pdf(self, pdf_path: Path) -> Dict:
        """Analyze a single PDF to extract patterns."""
        try:
            processor = PDFProcessor(pdf_path)

            # Extract text from first 10 pages (most metadata is early)
            pages_text = processor.extract_text(page_range=[1, min(10, processor.get_page_count())])
            full_text = "\n".join(pages_text)

            # Extract tables
            tables = processor.extract_tables(page_range=[1, min(10, processor.get_page_count())])

            # Extract potential field labels
            labels = self.pattern_detector.extract_labels(full_text)

            # Extract table headers (common field names)
            table_labels = set()
            for page_num, table in tables:
                if table and len(table) > 0:
                    # First row often contains headers
                    headers = table[0]
                    for cell in headers:
                        if cell and isinstance(cell, str):
                            clean_header = cell.strip()
                            if 3 <= len(clean_header) <= 50:
                                table_labels.add(clean_header)

            return {
                'path': pdf_path,
                'labels': labels,
                'table_labels': table_labels,
                'num_pages': processor.get_page_count(),
                'has_tables': len(tables) > 0,
                'success': True
            }

        except Exception as e:
            print(f"Warning: Failed to analyze {pdf_path.name}: {e}", file=sys.stderr)
            return {
                'path': pdf_path,
                'labels': set(),
                'table_labels': set(),
                'success': False,
                'error': str(e)
            }

    def find_common_labels(self, analyses: List[Dict]) -> Dict[str, Dict]:
        """Find labels that appear in multiple documents."""
        label_counts = Counter()
        label_docs = defaultdict(list)

        for analysis in analyses:
            if not analysis['success']:
                continue

            # Combine text and table labels
            all_labels = analysis['labels'] | analysis['table_labels']

            for label in all_labels:
                label_counts[label] += 1
                label_docs[label].append(analysis['path'].name)

        # Filter to labels that meet minimum confidence threshold
        total_docs = len([a for a in analyses if a['success']])
        min_occurrences = max(self.min_documents, int(total_docs * self.min_confidence))

        common_labels = {}
        for label, count in label_counts.items():
            if count >= min_occurrences:
                common_labels[label] = {
                    'count': count,
                    'percentage': count / total_docs,
                    'documents': label_docs[label]
                }

        return common_labels

    def generate_field_name(self, label: str) -> str:
        """Generate a valid field name from a label."""
        # Convert to snake_case
        field_name = label.lower()
        field_name = re.sub(r'[^\w\s]', '', field_name)  # Remove special chars
        field_name = re.sub(r'\s+', '_', field_name)     # Spaces to underscores
        return field_name

    def infer_field_type(self, label: str) -> str:
        """Infer field type from label text."""
        label_lower = label.lower()

        # Year patterns
        if any(word in label_lower for word in ['year', 'date', 'built', 'constructed']):
            if 'date' in label_lower:
                return 'date'
            return 'number'

        # Number patterns
        if any(word in label_lower for word in [
            'number', 'count', 'total', 'amount', 'cost', 'price', 'value',
            'area', 'size', 'square', 'feet', 'sf', 'units', 'stories', 'floors'
        ]):
            return 'number'

        # Default to text
        return 'text'

    def infer_search_terms(self, label: str) -> List[str]:
        """Generate search term variations for a label."""
        terms = [label]

        # Add variations
        # Remove punctuation variations
        if ':' in label or '-' in label:
            terms.append(re.sub(r'[:\-]', '', label).strip())

        # Add plural/singular variations for common terms
        if label.endswith('s') and len(label) > 4:
            terms.append(label[:-1])  # Singular
        elif not label.endswith('s'):
            terms.append(label + 's')  # Plural

        return list(set(terms))

    def generate_schema(self, common_labels: Dict[str, Dict], schema_name: str) -> Dict:
        """Generate a schema from common labels."""
        fields = {}

        for label, info in sorted(common_labels.items(), key=lambda x: x[1]['count'], reverse=True):
            field_name = self.generate_field_name(label)
            field_type = self.infer_field_type(label)
            search_terms = self.infer_search_terms(label)

            field_spec = {
                'label': label,
                'type': field_type,
                'search_terms': search_terms,
                'page_range': [1, 10]  # Conservative default
            }

            # Add pattern for number fields
            if field_type == 'number':
                if 'year' in label.lower():
                    field_spec['pattern'] = r'(19|20)\d{2}'
                else:
                    field_spec['pattern'] = r'[\d,]+'

            # Add comment with discovery metadata
            field_spec['_discovered_from'] = {
                'documents': info['count'],
                'percentage': round(info['percentage'] * 100, 1)
            }

            fields[field_name] = field_spec

        schema = {
            'fields': fields,
            '_metadata': {
                'schema_name': schema_name,
                'auto_generated': True,
                'min_confidence': self.min_confidence,
                'fields_discovered': len(fields)
            }
        }

        return schema

    def discover(self, pdf_files: List[Path]) -> Optional[Dict]:
        """
        Discover schema from a list of PDF files.

        Returns:
            Schema dict if enough common patterns found, None otherwise
        """
        if len(pdf_files) < self.min_documents:
            print(f"Need at least {self.min_documents} PDFs for schema discovery (got {len(pdf_files)})")
            return None

        print(f"Analyzing {len(pdf_files)} PDFs for common patterns...")

        # Analyze each PDF
        analyses = []
        for pdf_path in pdf_files:
            print(f"  Analyzing: {pdf_path.name}")
            analysis = self.analyze_pdf(pdf_path)
            analyses.append(analysis)

        # Count successful analyses
        successful = [a for a in analyses if a['success']]
        if len(successful) < self.min_documents:
            print(f"Only {len(successful)} PDFs analyzed successfully (need {self.min_documents})")
            return None

        print(f"\n✓ Successfully analyzed {len(successful)}/{len(pdf_files)} documents")

        # Find common labels
        common_labels = self.find_common_labels(analyses)

        if not common_labels:
            print("No common fields found across documents")
            return None

        print(f"✓ Found {len(common_labels)} common fields")
        print("\nCommon fields detected:")
        for label, info in sorted(common_labels.items(), key=lambda x: x[1]['count'], reverse=True):
            print(f"  - {label}: {info['count']} documents ({info['percentage']*100:.1f}%)")

        # Generate schema
        schema_name = 'auto_discovered'
        schema = self.generate_schema(common_labels, schema_name)

        return schema


def main():
    parser = argparse.ArgumentParser(
        description='Automatically discover extraction schemas from PDF documents',
        epilog="""
Examples:
  # Discover schema from all PDFs in folder
  %(prog)s documents/*.pdf --output schemas/auto_schema.yaml

  # Require fields in 80%% of documents
  %(prog)s docs/*.pdf --min-confidence 0.8 --output schema.yaml

  # Need at least 5 matching documents
  %(prog)s *.pdf --min-documents 5
        """
    )

    parser.add_argument(
        'pdfs',
        nargs='+',
        help='PDF files to analyze (supports glob patterns)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output schema file path (.yaml or .json)'
    )
    parser.add_argument(
        '--min-documents',
        type=int,
        default=3,
        help='Minimum documents needed to create schema (default: 3)'
    )
    parser.add_argument(
        '--min-confidence',
        type=float,
        default=0.6,
        help='Minimum percentage of documents that must share a field (0.0-1.0, default: 0.6)'
    )
    parser.add_argument(
        '--format',
        choices=['yaml', 'json'],
        default='yaml',
        help='Output format (default: yaml)'
    )

    args = parser.parse_args()

    # Convert glob patterns to Path objects
    pdf_files = [Path(p) for p in args.pdfs]
    pdf_files = [p for p in pdf_files if p.exists() and p.suffix.lower() == '.pdf']

    if not pdf_files:
        print("Error: No valid PDF files found", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(pdf_files)} PDF files\n")

    # Discover schema
    discovery = SchemaDiscovery(
        min_documents=args.min_documents,
        min_confidence=args.min_confidence
    )

    schema = discovery.discover(pdf_files)

    if not schema:
        print("\n✗ Could not generate schema (not enough common patterns)")
        sys.exit(1)

    # Output schema
    if args.output:
        output_path = args.output

        # Clean metadata for export
        clean_schema = {'fields': {}}
        for field_name, field_spec in schema['fields'].items():
            # Remove discovery metadata from field spec
            clean_spec = {k: v for k, v in field_spec.items() if not k.startswith('_')}
            clean_schema['fields'][field_name] = clean_spec

        # Write file
        if args.format == 'yaml' or output_path.suffix in ['.yaml', '.yml']:
            with open(output_path, 'w') as f:
                f.write("# Auto-generated schema\n")
                f.write(f"# Discovered from {len(pdf_files)} PDF documents\n")
                f.write(f"# Minimum confidence: {args.min_confidence*100:.0f}%\n\n")
                yaml.dump(clean_schema, f, sort_keys=False, default_flow_style=False)
            print(f"\n✓ Schema saved to: {output_path} (YAML)")
        else:
            with open(output_path, 'w') as f:
                json.dump(clean_schema, f, indent=2)
            print(f"\n✓ Schema saved to: {output_path} (JSON)")

        print(f"  Fields: {len(schema['fields'])}")
        print(f"\nNext steps:")
        print(f"  1. Review and refine: {output_path}")
        print(f"  2. Test extraction:")
        print(f"     python3 pdf_extract.py sample.pdf --schema {output_path}")

    else:
        # Print to stdout
        print("\n" + "="*60)
        print("GENERATED SCHEMA")
        print("="*60 + "\n")

        clean_schema = {'fields': {}}
        for field_name, field_spec in schema['fields'].items():
            clean_spec = {k: v for k, v in field_spec.items() if not k.startswith('_')}
            clean_schema['fields'][field_name] = clean_spec

        if args.format == 'yaml':
            print(yaml.dump(clean_schema, sort_keys=False, default_flow_style=False))
        else:
            print(json.dumps(clean_schema, indent=2))


if __name__ == '__main__':
    main()

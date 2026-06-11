---
name: pdf-extract
description: >
  Extract structured data from PDFs using schema-driven field extraction. Use this skill when
  the user asks to "extract data from PDFs", "parse property reports", "extract fields from documents",
  "create a schema for extraction", or when you need to convert unstructured PDFs into structured JSON.
  Supports single file extraction, batch processing with glob patterns, and exploration mode for schema development.
version: 1.0.0
---

# PDF Extract

Extract structured data from PDFs using schema-driven field extraction. A generalized, extensible framework that works with ANY document type - property assessments, utility bills, inspection reports, financial statements, etc.

**No MCP dependencies** - Uses local Python libraries only (pdfplumber, PyYAML)

**Storage:** Schemas in `skills/pdf-extract/schemas/`, outputs to JSON

---

## What This Skill Does

1. **Schema-Driven Extraction**: Define what to extract using YAML schemas
2. **Multiple Strategies**: Table cell matching, text proximity, regex fallback
3. **Batch Processing**: Extract from multiple PDFs with glob patterns
4. **Exploration Mode**: Dump raw PDF content to design schemas

---

## When to Use This Skill

**Use pdf-extract when:**
- Need to extract structured fields from PDFs (property data, utility usage, inspection findings)
- Have multiple similar documents to process (batch extraction)
- Want to convert unstructured PDFs to JSON for RAG indexing
- User asks to "extract X from these PDFs" or "parse property reports"

**Don't use when:**
- PDF is just text to read (use Read tool directly)
- Need full semantic search (use Soapbox RAG (`rag_ingest` MCP tool) instead)
- Document is already structured (CSV, JSON, etc.)

---

## Setup: Install Dependencies

Before first use, install required Python packages:

```bash
pip install --break-system-packages pdfplumber PyYAML pytest
```

---

## Workflow Option 1: Automatic Schema Discovery (Recommended)

**When you have 3+ similar PDFs**, use automatic schema discovery:

```bash
# Automatically discover schemas and extract data
python3 skills/pdf-extract/scripts/auto_extract.py documents/*.pdf --output results/
```

**What happens:**
1. Groups similar PDFs by page count and structure
2. Discovers common fields across each group (3+ documents)
3. Generates schemas automatically
4. Extracts data using discovered schemas
5. Saves schemas and extracted data

**Output:**
```
results/
├── schema_6-15_pages.yaml         # Auto-discovered schema
├── extracted_6-15_pages.json       # Extracted data
└── all_extractions.json            # Combined results
```

**Or discover schema only (without extraction):**

```bash
# Discover and save schema
python3 skills/pdf-extract/scripts/discover_schemas.py documents/*.pdf \
  --output schemas/my_schema.yaml \
  --min-confidence 0.7
```

**Then review and refine the schema before extraction.**

---

## Workflow Option 2: Manual Schema Creation

### Step 1: Explore PDF Content (Design Schema)

For custom schemas or when you have fewer than 3 documents, explore the PDF to see how data is structured:

```bash
python3 skills/pdf-extract/scripts/pdf_extract.py document.pdf \
  --dump-text --dump-tables --pages 1-6
```

**What to look for:**
- How labels appear ("Property name:", "Year Built", etc.)
- Whether data is in tables or plain text
- Page numbers where key information appears

---

## Step 2: Create Extraction Schema

Create a YAML schema defining what fields to extract. Use the example template:

```bash
# Copy template as starting point
cp skills/pdf-extract/schemas/example_document.yaml \
   skills/pdf-extract/schemas/my_document.yaml

# Edit to match your document structure
```

**Schema Format:**

```yaml
fields:
  property_name:
    label: Property Name              # Human-readable name
    type: text                        # text | number | date
    search_terms:                     # Labels to search for
      - "Property name"
      - "Subject Property"
    fallback:                         # Alternative terms (optional)
      - "Project name"
    page_range: [1, 3]                # Pages to search (optional, 1-indexed)
    pattern: "regex pattern"          # Validation/extraction regex (optional)
```

**Field Types:**
- `text` - String values (names, addresses, IDs)
- `number` - Integers or floats (commas removed automatically)
- `date` - Date values (future enhancement)

**Extraction Strategies:**
The framework tries multiple strategies in order:
1. **Table cell extraction** (highest confidence) - finds values in table cells adjacent to labels
2. **Text proximity** (high confidence) - finds values near labels (same line or next line)
3. **Regex fallback** (medium/low confidence) - searches with patterns when other methods fail

---

## Step 3: Extract from Single PDF

Extract structured data from a single PDF:

```bash
python3 skills/pdf-extract/scripts/pdf_extract.py document.pdf \
  --schema skills/pdf-extract/schemas/my_document.yaml
```

**Output (JSON to stdout):**

```json
[
  {
    "source_file": "document.pdf",
    "fields": {
      "property_name": {
        "value": "Carolina Club",
        "page": 1,
        "confidence": "high",
        "method": "text_proximity"
      },
      "year_built": {
        "value": 2002,
        "page": 3,
        "confidence": "high",
        "method": "table_cell"
      }
    }
  }
]
```

**Confidence Levels:**
- `high` - Found in table cell or same line as label
- `medium` - Found on line after label, or via regex near label
- `low` - Found via regex with no nearby label
- `none` - Not found

---

## Step 4: Batch Extraction

Extract from multiple PDFs using glob patterns:

```bash
python3 skills/pdf-extract/scripts/pdf_extract.py "documents/*.pdf" \
  --schema skills/pdf-extract/schemas/my_document.yaml \
  --output extracted_data.json
```

**Progress output to stderr:**
```
✓ Extracted from documents/building_a.pdf
✓ Extracted from documents/building_b.pdf
✗ Failed to extract from documents/corrupted.pdf: Invalid PDF
Results written to extracted_data.json
```

---

## Integration with Local RAG

The PDF extraction framework works great with the `rag_ingest` skill:

**Workflow:**
1. **Extract structured data** from PDFs → JSON
2. **Index extracted fields** into RAG for semantic search
3. **Query** to find buildings/properties by any field

**Example:**

```bash
# 1. Extract data from property assessments
python3 skills/pdf-extract/scripts/pdf_extract.py "assessments/*.pdf" \
  --schema skills/pdf-extract/schemas/property_assessment.yaml \
  --output property_data.json

# 2. Index the extracted JSON into RAG
# (Future enhancement: auto-index extracted data)

# 3. Query: "Find all buildings built before 2000"
python3 skills/rag_ingest/scripts/query.py \
  --query "buildings constructed before year 2000" \
  --top-k 5
```

---

## Creating Custom Schemas

### Example: Utility Bill Extraction

```yaml
# schemas/utility_bill.yaml
fields:
  account_number:
    label: Account Number
    type: text
    search_terms: ["Account #", "Account No", "Acct"]
    page_range: [1, 1]
    pattern: "\\d{10,12}"
    
  billing_period:
    label: Billing Period
    type: text
    search_terms: ["Billing Period", "Service Period"]
    page_range: [1, 1]
    
  total_kwh:
    label: Total kWh Usage
    type: number
    search_terms: ["Total kWh", "Total Usage", "Energy Used"]
    page_range: [1, 2]
    pattern: "[\\d,]+"
    
  total_cost:
    label: Total Amount Due
    type: number
    search_terms: ["Amount Due", "Total Due", "Balance"]
    page_range: [1, 2]
    pattern: "\\$[\\d,]+\\.\\d{2}"
```

### Example: Inspection Report Extraction

```yaml
# schemas/inspection_report.yaml
fields:
  inspection_date:
    label: Inspection Date
    type: date
    search_terms: ["Date of Inspection", "Inspection Date"]
    page_range: [1, 1]
    pattern: "\\d{1,2}/\\d{1,2}/\\d{4}"
    
  inspector_name:
    label: Inspector Name
    type: text
    search_terms: ["Inspector", "Inspected by"]
    page_range: [1, 1]
    
  building_condition:
    label: Overall Condition
    type: text
    search_terms: ["Overall Condition", "General Condition", "Rating"]
    page_range: [1, 3]
    
  critical_findings:
    label: Critical Findings Count
    type: number
    search_terms: ["Critical Findings", "Immediate Action Required"]
    page_range: [1, 10]
```

---

## Troubleshooting

**Field not found:**
- Check `page_range` includes the right pages (use `--dump-text` to verify)
- Add more `search_terms` or `fallback` terms
- Use `--dump-text` to see raw text and verify label exists

**Wrong value extracted:**
- Add a `pattern` to validate/filter the extracted value
- Check if data is in a table (use `--dump-tables`)
- Tighten `page_range` to avoid wrong section

**Low confidence:**
- Data in tables = highest confidence
- Data next to label = high confidence
- Data found by regex only = lower confidence
- Consider restructuring schema to improve extraction

---

## Architecture

```
pdf_extract.py          # Main CLI and orchestration
├── schema_loader.py    # Load and validate YAML/JSON schemas
├── pdf_processor.py    # Extract text and tables with pdfplumber
├── field_extractor.py  # Orchestrate extraction strategies
└── extractors.py       # Individual extraction strategies
    ├── TextProximityExtractor
    ├── TableCellExtractor
    └── RegexExtractor
```

---

## Testing

Run the test suite to verify everything works:

```bash
cd skills/pdf-extract/scripts
pytest -v
```

**Expected output:**
```
19 passed in 0.30s
```

---

## Advanced Usage

### Page Range Optimization

For large PDFs, limit extraction to relevant pages:

```yaml
fields:
  executive_summary:
    label: Executive Summary
    type: text
    search_terms: ["Executive Summary", "Summary"]
    page_range: [1, 3]  # Only search first 3 pages
    
  detailed_findings:
    label: Detailed Findings
    type: text
    search_terms: ["Findings", "Analysis"]
    page_range: [10, 50]  # Skip first pages
```

### Pattern Validation

Use regex patterns to validate extracted values:

```yaml
fields:
  year_built:
    label: Year Built
    type: number
    search_terms: ["Year Built", "Construction Year"]
    pattern: "(19|20)\\d{2}"  # Only 1900-2099
    
  zip_code:
    label: ZIP Code
    type: text
    search_terms: ["ZIP", "Zip Code"]
    pattern: "\\d{5}(-\\d{4})?"  # ZIP or ZIP+4
```

---

## Example: Full Workflow

```bash
# 1. Explore a sample PDF
python3 skills/pdf-extract/scripts/pdf_extract.py sample_report.pdf \
  --dump-text --pages 1-3

# 2. Create schema based on exploration
# Edit: skills/pdf-extract/schemas/my_schema.yaml

# 3. Test on single PDF
python3 skills/pdf-extract/scripts/pdf_extract.py sample_report.pdf \
  --schema skills/pdf-extract/schemas/my_schema.yaml

# 4. Batch process all PDFs
python3 skills/pdf-extract/scripts/pdf_extract.py "reports/*.pdf" \
  --schema skills/pdf-extract/schemas/my_schema.yaml \
  --output all_reports.json

# 5. Use extracted data
cat all_reports.json | jq '.[] | {name: .fields.property_name.value, year: .fields.year_built.value}'
```

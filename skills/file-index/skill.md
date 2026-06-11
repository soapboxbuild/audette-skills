---
name: file-index
description: >
  Scans every file in the current project workspace and builds an intelligent file index —
  a quick-reference summary of what each file contains, organized by folder. Use when the
  user asks to index, catalog, or get an overview of their project files, or when starting
  work on a new project. Also triggers RAG ingestion so files become semantically searchable.
  Triggers on: "index my files", "what files do I have", "create a file index",
  "catalog my project", "index this workspace".
version: 1.0.0
---

# File Index

Scan the project workspace, describe each file in plain English, and save the result as
`FILE-INDEX.md`. Optionally ingest files into the RAG system so they become semantically
searchable by all other skills.

**No required MCP dependencies** — file reading is local only.  
**Optional:** Audette MCP (for `rag_ingest` — makes files searchable)

---

## What makes a good index

Each entry should answer: "Do I have a file about X, and where is it?"
- Real description of the content, not just the filename
- Group by folder so the structure is clear
- Flag important files (contracts, executed agreements, financial data) with ⭐

---

## Step 1: Scan the workspace

List all files recursively. Skip:
- Hidden files and folders (anything starting with `.`)
- `FILE-INDEX.md` itself
- Build artifacts (`node_modules/`, `dist/`, `__pycache__/`, `.git/`)

Note the folder structure — use it to organize the index.

---

## Step 2: Analyze each file

Read each file and write a 1–2 sentence description. Approach by type:

**PDFs** — Use the Read tool. If the PDF is image-only (no extractable text), note "Scanned PDF — no text extractable."

**Word docs (.docx)** — Use the Read tool.

**Excel / CSV** — Read the first few rows to understand the data structure and what it contains.

**Text, Markdown, JSON** — Read directly.

**Images** — Note the filename and skip content analysis.

**Unknown types** — Note the extension and skip.

Each description should capture:
- Document type (contract, report, form, utility bill, PCNA, etc.)
- Who or what it's about
- Key visible details (date ranges, property addresses, dollar amounts, parties)

---

## Step 3: Write FILE-INDEX.md

Save to the workspace root. Format:

```markdown
# File Index
*Last updated: [date]*
*Total files: N*

## Root

| File | Description |
|------|-------------|
| [filename](filename) | ⭐ Executed purchase agreement for 123 Main St, signed 2025-03-15 |

## utilities/

| File | Description |
|------|-------------|
| [filename](utilities/jan-2025.pdf) | Eversource electricity bill for Jan 2025, account 12345, 18,420 kWh |
| [filename](utilities/feb-2025.pdf) | Eversource electricity bill for Feb 2025, account 12345, 16,890 kWh |
```

Mark files with ⭐ when they're executed contracts, financial agreements, or primary deliverables.

---

## Step 4: RAG ingestion (optional but recommended)

If the Audette MCP is connected and `.audette-config.json` exists, offer to ingest the
indexed files into the RAG system:

> "I've indexed N files. Would you like me to also ingest them into the search index so
> you can ask questions across all your documents? (yes / skip)"

If yes, call `rag_ingest` for each supported file type (PDF, XLSX, DOCX, TXT, MD, CSV).
Use the `workspace_id` from `.audette-config.json` if available.

```
For each file:
  - Call rag_ingest with file_path, workspace_id (from config), source: "upload"
  - Files where skipped=true were already indexed — no need to re-ingest
```

Report how many were ingested vs. already indexed vs. skipped (unsupported type).

---

## Step 5: Confirm

Tell the user:
- How many files were indexed
- Notable finds (e.g., "Found 2 executed contracts, 12 utility bills, 1 PCNA report")
- Whether RAG ingestion ran and how many files are now searchable

---

## Keeping the Index Fresh

If `FILE-INDEX.md` already exists, offer to update rather than rebuild — re-analyze files
that are new or modified since the last update (compare modification dates). For RAG,
idempotent `rag_ingest` calls will skip unchanged files automatically via content hash.

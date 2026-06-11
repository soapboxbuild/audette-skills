---
name: workspace-rag
description: >
  Index workspace documents into the Soapbox RAG system and search across them
  semantically. Use when the user wants to search their project documents, asks
  "what do my files say about X", needs to find information across multiple PDFs
  or spreadsheets, or wants to make documents searchable for downstream skills.
  Also use proactively after workspace-setup to index the project folder.
  Triggers on: "index my documents", "search my files", "what does the PCNA say
  about X", "find mentions of X across documents", "ingest files into search".
version: 1.0.0
requires:
  - soapbox-rag
---

# Workspace RAG

Index project documents into the Soapbox RAG system and run semantic searches
across them. The RAG index persists across sessions and is shared with all agents
in the org.

**Required:** Soapbox RAG (provides `rag_ingest`, `rag_search`, `rag_list`, `rag_delete`)  
**Optional:** `.audette-config.json` (for workspace scoping)

---

## When to Use RAG vs. Direct File Reading

| Use RAG when | Use Read tool when |
|---|---|
| Searching across many files | Reading one known file |
| Query is semantic ("what type of HVAC...") | Query is exact ("show me line 45 of...") |
| File contents are already indexed | File was just added and not yet indexed |
| Cross-document synthesis needed | Single-document extraction |

---

## Step 1: Check What's Already Indexed

Call `rag_list` with the workspace_id from `.audette-config.json` (if available):

```
rag_list(workspace_id: "ws_abc123")
```

If the document you need is already indexed and recent, skip to Step 3.
If the project has never been indexed, proceed to Step 2.

---

## Step 2: Ingest Documents

Call `rag_ingest` for each relevant file. Supported types: PDF, XLSX, DOCX, TXT, MD, CSV.

```
rag_ingest(
  file_path: "/absolute/path/to/document.pdf",
  workspace_id: "ws_abc123",   // from .audette-config.json, or omit for org-wide
  source: "agent"
)
```

**Returns:** `{ documentId, chunkCount, skipped }` — `skipped: true` means the file was already indexed with the same content (idempotent).

**Batch indexing:** To index an entire project folder, list the files first and call `rag_ingest` for each supported file. Skip images and binary files.

**workspace_id:** Always pass the workspace_id from `.audette-config.json` to scope documents to the current project. Omit only for org-wide reference documents.

---

## Step 3: Search

Call `rag_search` with a natural language query:

```
rag_search(
  query: "what type of heating system does the building have",
  workspace_id: "ws_abc123",
  limit: 5
)
```

**Returns:** `{ results: [{ content, filename, workspaceId, score }] }`

Search finds semantically relevant chunks — it doesn't need exact keyword matches. Good queries:
- "HVAC system type and installation year"
- "boiler capacity MBH"
- "year built construction type"
- "utility account number electricity"

**Workspace scope:** Searches the specified workspace AND org-wide documents together. Workspace results are weighted higher.

---

## Step 4: Use the Results

Results come as text chunks with source filenames and relevance scores. For each result:
- Note the `filename` to understand the source
- The `content` is a 512-token excerpt — enough context for most extractions
- Higher `score` = more relevant

If results are insufficient, try:
- A different query phrasing
- Ingesting additional documents (Step 2)
- Increasing `limit` (max 20)

---

## Step 5: Keep the Index Fresh

After adding new documents to the workspace:
- Call `rag_ingest` for each new file — already-indexed files are skipped automatically
- No need to delete and re-index unless a file's content changed

To remove a document:
```
rag_delete(document_id: "uuid-of-document")
```

---

## Integration with Other Skills

**workspace-setup** calls this skill automatically after initialization to index the project folder.

**audette-energy-data** can search RAG for utility bill data instead of reading files directly, when documents are already indexed.

**audette-equipment-survey** uses RAG to find equipment details in PCNAs and CNAs.

**system-details** calls `rag_search` to pull context from documents before synthesizing a building systems report.

---

## Rules

- Always use the `workspace_id` from `.audette-config.json` — never mix org-wide and workspace-scoped indexes
- Ingest before searching if the workspace has never been indexed
- `rag_ingest` is idempotent — safe to call repeatedly on the same file
- Don't ingest image files, videos, or binaries — they produce no text
- For sensitive documents, confirm with the user before indexing

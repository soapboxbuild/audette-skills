---
name: workspace-setup
description: >
  Set up or verify an Audette client workspace. Links an Audette account, connects
  a customer document folder, caches the account's building list, and saves everything
  to .audette-config.json. Use when starting a new client project, onboarding a
  property, or when the user says "set up workspace", "configure this project", or
  "which account is this".
version: 1.0.0
requires:
  - audette-mcp
---

# Workspace Setup

Set up, verify, and refresh the Audette workspace config (`.audette-config.json`).
This file is the single source of truth for all downstream Audette skills: which
account is active, where customer files live, which buildings exist, and where
the file index is.

## When to Use

**Initial setup** (no config exists yet):
- "Set up this workspace" / "configure this project"
- "Link a customer folder"
- User shares property documents but `.audette-config.json` doesn't exist

**Pre-flight check** (another skill calls this first):
- Before any Audette action (building creation, equipment survey, report generation)
- "Which account is this project linked to?"

**Refreshing** (existing config is stale):
- "Refresh the workspace"
- New buildings have been added outside this workspace

---

## Config Schema (v3)

```json
{
  "schema_version": 3,
  "project_name": "<client or project name>",
  "customer": {
    "name": "<client/customer name>",
    "logo_path": "<path to saved logo, or null>"
  },
  "customer_folder": {
    "platform": "google_drive | box | sharepoint | local",
    "folder_url": "<full URL or local path>",
    "description": "<optional>"
  },
  "audette_account": {
    "name": "<account name>",
    "uid": "<account uid>"
  },
  "buildings": [
    {
      "name": "<building name>",
      "building_uid": "<uid>",
      "building_model_uid": "<model uid>",
      "address": "<street address>",
      "city": "<city>",
      "state": "<state>",
      "archetype": "<archetype or null>"
    }
  ],
  "file_index_path": ".file-index.md",
  "last_updated": "<ISO timestamp>"
}
```

---

## Workflow

### Step 1: Verify Audette MCP

Call `list_customer_accounts` from the Audette MCP. If it fails, stop:

> The Audette MCP is required but not connected. Please add it to your MCP config and restart.

### Step 2: Check for Existing Config

Look for `.audette-config.json` at the workspace root.

- **Missing** → proceed to Step 3
- **Exists, schema_version = 3** → show summary, ask "Refresh or proceed with existing?"
- **Exists, schema_version < 3** → migrate (see Migration section below), then continue

### Step 3: Project Name

Ask: *"What's the client or project name for this workspace?"*

### Step 4: Customer Folder

Ask where the customer's documents are stored:

> Where are the customer documents?
> 1. Google Drive — provide folder URL
> 2. Box — provide folder URL
> 3. SharePoint — provide folder URL
> 4. Local folder — provide path
> 5. No centralized folder (files uploaded individually)

For local paths, verify the path exists before saving. For "no folder", save `{"platform": "local", "folder_url": ".", "description": "Files uploaded individually"}`.

### Step 5: Client Logo (Optional)

Ask: *"Do you have a client logo for reports? Provide a file path, Google Drive URL, or type 'skip'."*

If provided, save the logo to `.audette-logos/<project-slug>.<ext>` in the workspace root. Set `customer.logo_path` to this path.

If skipped, set `customer.logo_path` to `null`.

### Step 6: Audette Account

Call `list_customer_accounts`. Present the list and ask the user to select one.

If the intended account isn't listed, set `audette_account.uid` to `"PENDING"` and note that the account must be created in Audette first.

### Step 7: Buildings Cache

Ask: *"Do you already have buildings in this Audette account? (yes / no / skip)"*

- **Yes** — ask for building UIDs, call `get_building_model_details` for each, populate `buildings[]`
- **No / skip** — initialize `buildings: []`

### Step 8: Write Config

Write `.audette-config.json` with all collected values and `"last_updated": <ISO timestamp>`.

### Step 9: File Index

Invoke the `file-index` skill to scan the workspace and create `.file-index.md`.

### Step 10: RAG Indexing

Invoke the `workspace-rag` skill to ingest all project documents into the Soapbox RAG
index. This makes documents semantically searchable by all subsequent skills.

Pass the `workspace_id` from the newly written config so documents are scoped to this project.

If the Soapbox RAG is not connected, skip this step and note:
> "RAG indexing skipped — Soapbox RAG not connected. Run `workspace-rag` manually when available."

### Step 11: Confirm

Show a summary:

```
Workspace setup complete.

Project:    [project_name]
Customer:   [customer.name]
Documents:  [platform] — [folder_url]
Account:    [account.name] ([account.uid])
Buildings:  [N] cached
File index: .file-index.md
RAG index:  [N files indexed / skipped]
```

---

## Refreshing an Existing Config

Re-call `list_customer_accounts` to verify the account still exists. Ask which fields to update. Set `last_updated` to current timestamp. Write back.

---

## Migration from v1/v2 to v3

Keep: `project_name`, `customer_folder.platform`, `customer_folder.folder_url`, `audette_account.*`, `buildings[]`

Remove: `mcp_health`, `espm_account`, `gcp`, `document_intelligence`, `customer_folder.mount_path`, `customer_folder.folder_id`

Transform: `customer.logo_url` (file:// URL) → `customer.logo_path` (plain path). If not a file:// URL, set to null.

Add: `schema_version: 3`, `file_index_path: ".file-index.md"`, `last_updated: <now>`

---

## Pre-flight Contract

Every downstream Audette skill must start by:

1. Reading `.audette-config.json` — if missing, tell user to run `workspace-setup`
2. Checking `schema_version === 3` — if lower, tell user to run `workspace-setup` to migrate
3. Verifying Audette MCP is connected

Use cached data from `buildings[]` and `audette_account.uid` before making MCP calls.
After creating a new building, add it to `buildings[]`, update `last_updated`, write config back.

---

## Rules

- Never write API keys or secrets into the config
- Always ask before overwriting an existing config (except during migration)
- Save logos to `.audette-logos/` in the workspace root
- Update `last_updated` whenever config changes

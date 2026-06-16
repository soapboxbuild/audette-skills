---
name: update-memory
description: >
  Track client project activity and maintain a chronological timeline of meetings,
  documents, and building updates. Creates PROJECT-HISTORY.md for agent context
  and sets up daily automated updates. Use when starting a new project ("set up
  memory"), updating project history ("refresh memory"), or when the user asks to
  "track changes" or "remember project activity".
version: 1.0.0
---

# Update Memory

Automatically track client project activity and maintain a chronological timeline.
Monitors meetings, documents, building model updates, and action items.

**Designed for client projects, not software development.** Tracks business activities:
meeting outcomes, contract deliverables, building data updates, and project milestones.

**Optional:** Audette MCP (for building tracking — skipped gracefully if not connected)

---

## What This Creates

- `PROJECT-HISTORY.md` — chronological timeline of project activity
- `CLAUDE.md` — project context file with pointer to history
- `.audette-memory/` — building state snapshots for change detection
- Daily cron job at 2:47am

---

## Step 1: Pre-flight

Get the Audette customer account UID from the system prompt. If present, call
`switch_customer_account` with that UID, then call `list_buildings` to get the
building list for change tracking.

If no account UID is in the system prompt, or if the Audette MCP call fails, note that
building tracking will be skipped — continue with file tracking only.

Extract `project_name` from context or ask the user if not clear.

---

## Step 2: Determine Scan Range

Check whether `PROJECT-HISTORY.md` already exists.

- **First run** (file missing) — scan all project history
- **Update run** (file exists) — parse the `*Last updated:*` timestamp and scan only
  files modified after that date

---

## Step 3: Scan and Categorize Files

List all files in the workspace recursively. Skip hidden files/folders, `PROJECT-HISTORY.md`,
and `.audette-memory/`.

For update runs, filter to only files modified after the last update timestamp.

Categorize each file by name pattern (see `references/file-patterns.md`):
- **Meetings** — filenames containing: meeting, notes, agenda, minutes
- **Contracts** — filenames containing: contract, agreement, signed, executed
- **Reports** — filenames containing: report, assessment, analysis, study
- **Utilities** — filenames containing: utility, bill, energy, electric, gas
- **Documents** — everything else

---

## Step 4: Extract Action Items from Meeting Files

For each file categorized as a meeting, read its content using the Read tool.

Search for lines matching patterns from `references/action-item-patterns.md`:
- Lines starting with: `TODO:`, `Action:`, `Action Item N:`, `[ ]`, `- [ ]`

Extract and clean those lines to build an action items list for that meeting.

---

## Step 5: Track Building Updates (if Audette MCP connected)

For each building returned by `list_buildings` (called in Step 1):

1. Call `get_building_model_details` with `building_model_uid`
2. Check `.audette-memory/building-<uid>-snapshot.json` for a previous snapshot
3. If snapshot exists, compare key fields: `baseline_eui`, `gfa`, `archetype`, `year_built`
4. If fields changed (or first run), note the change as a timeline entry
5. Save current state as the new snapshot

If a building query fails, log a warning and skip that building.

---

## Step 6: Format Timeline

Group all entries by date (newest first). For each date section:

```markdown
## YYYY-MM-DD

### Meetings
- [meeting topic extracted from filename]

### Documents
- **filename.pdf** — [category]

### Building Updates
- **Building Name** — [field]: [old] → [new]

### Action Items
- [extracted action item]
```

---

## Step 7: Write or Update PROJECT-HISTORY.md

**First run:** Write a new file with header + all entries.

**Update run:** Read the existing file, insert new entries after the header (before
existing entries), and update the `*Last updated:*` timestamp.

Header format:
```markdown
# Project History: [project_name]

*Last updated: [ISO timestamp]*

---
```

---

## Step 8: Create or Update CLAUDE.md

If `CLAUDE.md` does not exist, create it with a pointer to `PROJECT-HISTORY.md`.

If it exists but lacks a `PROJECT-HISTORY.md` reference, append a section pointing to it.

---

## Step 9: Schedule Daily Updates (First Run Only)

On first run, create a recurring cron job:

```
CronCreate: "47 2 * * *", prompt: "/update-memory", recurring: true
```

Note to user that recurring tasks auto-expire after 7 days — re-run this skill to refresh.

---

## Step 10: Confirm

**First run:**
> Memory initialized. Timeline created with N meetings, N documents, N building snapshots.
> Daily updates scheduled for 2:47am.

**Update run with changes:**
> Memory updated. N new files, N building updates since [last update date].

**Update run, no changes:**
> No changes since [last update date]. PROJECT-HISTORY.md is current.

---

## Rules

- Never block on missing account UID or Audette MCP failure — skip building tracking and continue with file tracking
- Never block on individual file read failures — skip the file with a warning
- Always sort timeline entries newest-first
- Use Read tool for all file content — no bash pdftotext or Python dependencies

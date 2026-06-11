---
name: report-template-generator
description: >
  Meta-skill that guides the user through designing a new reusable report template.
  Walks through structure, branding, and data fields, then saves the finished HTML as
  a named example in the report skill's template library — making it available for
  future report generation. Use when the user wants to "create a report template",
  "design a report layout", "build a reusable report", "set up a report format", or
  says "I keep making the same report". Also trigger when the user wants a repeatable
  deliverable for buildings, energy audits, assessments, or client presentations.
version: 1.0.0
---

# Report Template Generator

Guide the user through designing a new report template, then save it as a named
example in the `report` skill's template library for future reuse.

**No MCP dependencies** — this is a design and authoring skill.

## What this skill produces

A new HTML example file added to:
```
skills/report/assets/templates/<report-type>/examples/<YYYY-MM-DD>-<name>.html
```

Once saved, this example appears as an option the next time the user generates a
report of that type. The `report` skill will ask "Which example should I base this on?"
and include the new template.

---

## Phase 1: Understand the report

Interview the user to define what this template is for:

1. **Report type** — which base type does this extend?
   - `decarb-roadmap` — decarbonization roadmap
   - `bps-compliance` — BPS / regulatory compliance
   - `acquisition-dd` — acquisition due diligence
   - Or propose a new type if none fit

2. **Template name** — a short slug (e.g., "minimal-layout", "investor-summary", "full-detail")

3. **Audience** — who reads this? (client, internal team, investors, regulators)

4. **Sections** — what major sections should it include? Offer suggestions based on
   the report type, but let the user drive.

5. **Visual style** — any specific branding preferences beyond the Audette defaults?
   Read `references/branding.md` for the standard palette and typography.

Keep this conversational. Extract from context what you can and confirm rather than
re-asking.

---

## Phase 2: Design the template

Using the agreed structure, describe what each section should look like. For each section:
- What data does it display?
- What charts or tables?
- How much detail vs. summary?

Reference `references/example-template.md` to show the user what a well-structured
template looks like.

Reference `references/example-schema.json` to explain how data fields map to template
placeholders.

Show the user a description of the proposed layout and get approval before building.

---

## Phase 3: Build the HTML

Generate a complete self-contained HTML file for this template. Requirements:

- **Self-contained** — no external file references except Chart.js CDN
- **Embeds sample data** — use realistic placeholder values so the user can evaluate
  the layout without needing real building data
- **Follows design tokens** from `skills/report/assets/design-tokens.md`
- **Chart.js from CDN**: `https://cdn.jsdelivr.net/npm/chart.js`
- **Font**: DM Sans from Google Fonts
- **Print-ready**: includes `@media print` styles, correct page margins

The sample data should be realistic for the report type:
- A real-sounding building name, address, and archetype
- Plausible numbers (EUI, emissions, costs) drawn from the report type's typical ranges
- All sections populated — no empty or placeholder-only sections

Show the HTML as an artifact and ask: "Does this layout work, or would you like any changes?"

---

## Phase 4: Iterate

If the user requests changes:
- Cosmetic (colors, font sizes, layout) → regenerate immediately
- Structural (new sections, different charts) → discuss, then regenerate

Keep iterating until the user says the layout is right.

---

## Phase 5: Save

Once approved, save the HTML to:
```
skills/report/assets/templates/<report-type>/examples/<YYYY-MM-DD>-<name>.html
```

Then update the manifest at:
```
skills/report/assets/templates/<report-type>/manifest.md
```

Add an entry to the examples table:
```markdown
| `<YYYY-MM-DD>-<name>.html` | [brief description] |
```

Confirm to the user:
> "Saved as `<path>`. It will appear as an option next time you generate a
> [report type] report."

Remind them to commit and push:
```bash
git add skills/report/assets/templates/<type>/examples/<file>.html \
        skills/report/assets/templates/<type>/manifest.md
git commit -m "feat(report): add <name> template example"
git push
```

---

## Rules

- Always show the proposed layout and get approval before saving
- Use realistic sample data — templates with empty sections are not useful as examples
- The saved HTML must be completely self-contained (open it in a browser to verify)
- Update the manifest every time you save a new example
- The template must work for all buildings of the given type, not just the sample property

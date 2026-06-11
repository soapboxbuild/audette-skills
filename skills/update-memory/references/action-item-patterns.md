# Action Item Extraction Patterns

This reference defines patterns for extracting action items from meeting notes.

## Recognized Patterns

### Pattern 1: TODO prefix
```
TODO: Get pricing quote for heat pump system
```

### Pattern 2: Action prefix
```
Action: Schedule site visit with contractor by 2026-06-15
```

### Pattern 3: Action Item numbered
```
Action Item 1: Review utility bill data
Action Item 2: Contact facilities manager
```

### Pattern 4: Checkbox syntax
```
[ ] Follow up with building owner
- [ ] Submit permit application
```

### Pattern 5: AI/Assignee format
```
AI (John): Send contract to legal team
```

## Extraction Logic

1. Scan each line of meeting notes (text files, parsed PDFs/Word docs)
2. Match line against patterns (case-insensitive)
3. Extract the action text (remove prefix/marker)
4. Trim whitespace
5. Add to action items list

## Edge Cases

- **Multiple action items on one line:** Split by semicolons if present
- **Multi-line action items:** Only capture first line (prevents paragraph capture)
- **Nested action items:** Treat each line independently (flatten hierarchy)

## Non-Action Item Lines

These should NOT be extracted as action items:
- **Section headers:** "# Action Items", "## Next Steps"
- **Completed items:** `[x]`, `- [x]`, "DONE:", "Completed:"
- **Questions:** Lines ending with "?"
- **Notes/context:** Lines that don't start with action patterns

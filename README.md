# audette-skills

Audette AI workflows as a Claude Code / opencode plugin — skills and agents for building energy modeling, carbon reduction planning, and decarbonization roadmaps.

## Install

### Claude Code

```bash
claude plugin marketplace add soapboxbuild/audette-skills
claude plugin install audette-skills
```

Two MCP servers are configured automatically on install:
- **Audette MCP** (`mcp-server.prod.audette.io`) — building models, carbon plans, equipment surveys. OAuth login on first use.
- **Soapbox MCP** (`api.admin.soapbox.build`) — RAG document search. OAuth login on first use.

### opencode

Add to your `opencode.json`:

```json
{
  "plugins": ["soapboxbuild/audette-skills"]
}
```

## Skills

| Skill | Requires |
|-------|---------|
| `workspace-setup` | Audette MCP |
| `audette-create-building` | Audette MCP |
| `audette-energy-data` | Audette MCP |
| `audette-equipment-survey` | Audette MCP |
| `equipment-gap-questionnaire` | Audette MCP |
| `report` | Audette MCP |
| `workspace-rag` | Soapbox MCP |
| `file-index` | Soapbox MCP (optional) |
| `system-details` | Audette MCP + Soapbox MCP |
| `pdf-extract` | None |
| `osm-gfa-calculator` | None |
| `kml-generator` | None |
| `local-rag` | Soapbox MCP |
| `update-memory` | None |

## License

Apache 2.0

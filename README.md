# audette-skills

Audette AI workflows as a Claude Code / opencode / Paperclip plugin — skills, MCP tools, and agents for building energy modeling, carbon reduction planning, and decarbonization roadmaps.

## Install

### Claude Code

Add the plugin:
```bash
claude plugin marketplace add soapboxbuild/audette-skills
claude plugin install audette-skills
```

Then add the MCP server to `~/.claude.json`:
```json
{
  "mcpServers": {
    "audette": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@soapboxbuild/audette-skills"],
      "env": { "AUDETTE_API_KEY": "your-key-here" }
    }
  }
}
```

### opencode

```json
{
  "mcp": {
    "audette": {
      "type": "local",
      "command": ["npx", "-y", "@soapboxbuild/audette-skills"]
    }
  }
}
```

Set `AUDETTE_API_KEY` in your environment.

## Skills

| Skill | Description |
|-------|-------------|
| `workspace-setup` | Initialize an Audette project workspace |
| *(more coming)* | |

## License

Apache 2.0

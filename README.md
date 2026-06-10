# audette-skills

Audette AI workflows as a Claude Code / opencode plugin — skills and agents for building energy modeling, carbon reduction planning, and decarbonization roadmaps.

## Install

### Claude Code

```bash
claude plugin marketplace add soapboxbuild/audette-skills
claude plugin install audette-skills
```

The Audette MCP server is configured automatically. You'll be prompted to log in to Audette on first use.

### opencode

Add to your `opencode.json`:

```json
{
  "plugins": ["soapboxbuild/audette-skills"]
}
```

## Skills

| Skill | Requires Audette MCP |
|-------|---------------------|
| `workspace-setup` | Yes |
| *(more coming)* | |

## License

Apache 2.0

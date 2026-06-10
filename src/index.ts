import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { getConfig } from "./lib/config.js";

const config = getConfig();
void config; // used by tools — referenced here to fail fast on missing key

const server = new McpServer({
  name: "audette-skills",
  version: "0.1.0",
});

// Tools are registered here as skills are ported.
// See: https://github.com/soapboxbuild/audette-skills/tree/main/skills

const transport = new StdioServerTransport();
await server.connect(transport);

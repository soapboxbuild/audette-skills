export interface Config {
  apiKey: string;
  baseUrl: string;
}

export function getConfig(): Config {
  const apiKey = process.env.AUDETTE_API_KEY;
  if (!apiKey) {
    throw new Error(
      "AUDETTE_API_KEY environment variable is required. " +
        "Set it in your MCP server config: " +
        '{"env": {"AUDETTE_API_KEY": "your-key-here"}}'
    );
  }
  return {
    apiKey,
    baseUrl: process.env.AUDETTE_BASE_URL ?? "https://api.audette.io",
  };
}

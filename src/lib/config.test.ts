import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

describe("getConfig", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    vi.resetModules();
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  it("throws a clear error when AUDETTE_API_KEY is missing", async () => {
    delete process.env.AUDETTE_API_KEY;
    const { getConfig } = await import("./config.js");
    expect(() => getConfig()).toThrow(
      "AUDETTE_API_KEY environment variable is required"
    );
  });

  it("returns the API key when set", async () => {
    process.env.AUDETTE_API_KEY = "test-key-123";
    const { getConfig } = await import("./config.js");
    const config = getConfig();
    expect(config.apiKey).toBe("test-key-123");
  });

  it("uses default base URL when AUDETTE_BASE_URL is not set", async () => {
    process.env.AUDETTE_API_KEY = "test-key-123";
    delete process.env.AUDETTE_BASE_URL;
    const { getConfig } = await import("./config.js");
    const config = getConfig();
    expect(config.baseUrl).toBe("https://api.audette.io");
  });

  it("uses AUDETTE_BASE_URL when set", async () => {
    process.env.AUDETTE_API_KEY = "test-key-123";
    process.env.AUDETTE_BASE_URL = "https://staging.audette.io";
    const { getConfig } = await import("./config.js");
    const config = getConfig();
    expect(config.baseUrl).toBe("https://staging.audette.io");
  });
});

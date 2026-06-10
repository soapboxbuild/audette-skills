import type { Config } from "./config.js";

export class AudetteClient {
  private readonly baseUrl: string;
  private readonly headers: Record<string, string>;

  constructor(config: Config) {
    this.baseUrl = config.baseUrl;
    this.headers = {
      Authorization: `Bearer ${config.apiKey}`,
      "Content-Type": "application/json",
    };
  }

  protected async get<T>(path: string): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      headers: this.headers,
    });
    if (!res.ok) {
      throw new Error(`Audette API error ${res.status}: ${await res.text()}`);
    }
    return res.json() as Promise<T>;
  }

  protected async post<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      throw new Error(`Audette API error ${res.status}: ${await res.text()}`);
    }
    return res.json() as Promise<T>;
  }
}

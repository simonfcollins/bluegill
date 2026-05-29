// src/agent.ts
import axios, { AxiosInstance } from "axios";
import { GenerateRequest, SessionIdRequest, Message } from "./types";

const VALID_PROVIDERS = ["ollama"];

export class Agent {
  private apiUrl: string;
  private _provider?: string;
  public model?: string;
  public sessionId?: string;
  private timeout: number;
  private client: AxiosInstance;

  constructor({
    apiUrl = "http://localhost:54345",
    provider,
    model,
    sessionId,
    timeout = 60000,
  }: {
    apiUrl?: string;
    provider?: string;
    model?: string;
    sessionId?: string;
    timeout?: number;
  } = {}) {
    this.apiUrl = apiUrl.replace(/\/$/, ""); // remove trailing slash
    this.model = model;
    this.sessionId = sessionId;
    this.timeout = timeout;

    if (provider !== undefined) this.provider = provider;

    this.client = axios.create({
      baseURL: this.apiUrl,
      timeout: this.timeout,
    });
  }

  // ------------------------
  // Core Methods
  // ------------------------

  async generateWithModel(
    provider: string,
    model: string,
    prompt: string
  ): Promise<string> {
    if (!prompt) return "";

    const payload: GenerateRequest = {
      provider,
      model,
      session_id: this.sessionId,
      prompt,
    };

    try {
      const response = await this.client.post("/generate", payload);
      return response.data.result ?? "";
    } catch {
      return "";
    }
  }

  async generate(prompt: string): Promise<string> {
    if (!this.isReady()) {
      throw new Error("Agent not fully configured");
    }

    return this.generateWithModel(this.provider!, this.model!, prompt);
  }

  async clearSession(): Promise<void> {
    if (!this.sessionId) return;

    const payload: SessionIdRequest = { session_id: this.sessionId };

    try {
      await this.client.post("/clear", payload);
    } catch {
      // silent fail
    }
  }

  async createSession(): Promise<string> {
    try {
      const response = await this.client.post("/new");
      this.sessionId = response.data.session_id;
      return this.sessionId ?? "";
    } catch {
      return "";
    }
  }

  async dump(): Promise<Message[]> {
    if (!this.sessionId) return [];

    try {
      const response = await this.client.get("/dump", {
        params: { session_id: this.sessionId },
      });
      return response.data.messages ?? [];
    } catch {
      return [];
    }
  }

  async compact(): Promise<void> {
    throw new Error("Not implemented");
  }

  // ------------------------
  // Helpers
  // ------------------------

  isReady(): boolean {
    return !!this.provider && !!this.model && !!this.sessionId;
  }

  // ------------------------
  // Properties
  // ------------------------

  get provider(): string | undefined {
    return this._provider;
  }

  set provider(provider: string | undefined) {
    if (provider !== undefined && !VALID_PROVIDERS.includes(provider)) {
      throw new Error(`Unsupported provider: ${provider}`);
    }
    this._provider = provider;
  }
}
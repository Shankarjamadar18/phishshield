import { afterEach, describe, expect, it, vi } from "vitest";
import { getBackendState } from "@/lib/api";

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
const health = { status: "ok", service: "PhishShield API", version: "0.1.0" };

afterEach(() => vi.unstubAllGlobals());

describe("getBackendState", () => {
  it("is unreachable when /health gets no response", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    expect((await getBackendState()).kind).toBe("unreachable");
  });

  it("is db_unavailable when /ready returns 503", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve(
          url.endsWith("/health")
            ? json(health)
            : json({ status: "not_ready", dependencies: { database: { status: "down", error: "OperationalError" } } }, 503),
        ),
      ),
    );
    expect((await getBackendState()).kind).toBe("db_unavailable");
  });

  it("is ready when /health and /ready both succeed", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        Promise.resolve(
          url.endsWith("/health")
            ? json(health)
            : json({ status: "ready", dependencies: { database: { status: "up", error: null } } }),
        ),
      ),
    );
    expect((await getBackendState()).kind).toBe("ready");
  });
});

import { afterEach, describe, expect, it, vi } from "vitest";

import { getHealth, getNotifications, runAgentOnce } from "./api";

describe("api client", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("requests configured endpoints with the default API base URL", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue({ status: "ok" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await getHealth();

    expect(fetchMock).toHaveBeenCalledWith("http://localhost:8000/health", {
    });
  });

  it("uses POST for manual agent runs", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue({ summary: {} }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await runAgentOnce();

    expect(fetchMock).toHaveBeenCalledWith("http://localhost:8000/agent/run-once", {
      method: "POST",
    });
  });

  it("surfaces JSON error detail from failed responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: vi.fn().mockResolvedValue({ detail: "Database unavailable" }),
      }),
    );

    await expect(getNotifications()).rejects.toThrow("Database unavailable");
  });

  it("falls back to status text when failed response body is not JSON", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        json: vi.fn().mockRejectedValue(new Error("not json")),
      }),
    );

    await expect(getHealth()).rejects.toThrow("Request failed with status 503");
  });
});

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import { getHealth, getNotifications, runAgentOnce } from "./api";

vi.mock("./api", () => ({
  getHealth: vi.fn(),
  getNotifications: vi.fn(),
  runAgentOnce: vi.fn(),
}));

const health = {
  email_source: "mock",
  database: "ok",
  scheduler: { poll_interval_seconds: 30 },
};

const notifications = [
  {
    email_id: "incident-1",
    sender: "ops@example.com",
    subject: "Server down",
    priority: "HIGH",
    category: "SERVER_DOWN",
    reason: "Production API unavailable.",
    received_at: "2026-06-04T09:00:00Z",
  },
];

describe("App", () => {
  beforeEach(() => {
    getHealth.mockResolvedValue(health);
    getNotifications.mockResolvedValue(notifications);
    runAgentOnce.mockResolvedValue({
      summary: {
        fetched: 2,
        classified: 2,
        notifications_created: 1,
        skipped_duplicates: 0,
        ignored: 1,
      },
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("loads dashboard data and renders notification counts", async () => {
    render(<App />);

    expect(await screen.findByText("ops@example.com")).toBeInTheDocument();
    expect(screen.getByText("Server down")).toBeInTheDocument();
    expect(screen.getByText("Production API unavailable.")).toBeInTheDocument();
    expect(screen.getByText("MOCK")).toBeInTheDocument();
    expect(screen.getByText("OK")).toBeInTheDocument();
  });

  it("runs the agent and displays the returned summary", async () => {
    const user = userEvent.setup();
    render(<App />);

    await screen.findByText("ops@example.com");
    await user.click(screen.getByRole("button", { name: /run agent now/i }));

    await waitFor(() => expect(runAgentOnce).toHaveBeenCalledTimes(1));
    expect(screen.getByText("2 fetched")).toBeInTheDocument();
    expect(screen.getByText("2 classified")).toBeInTheDocument();
    expect(screen.getByText("1 notifications")).toBeInTheDocument();
    expect(screen.getByText("0 duplicates skipped")).toBeInTheDocument();
    expect(screen.getByText("1 ignored")).toBeInTheDocument();
  });

  it("shows an API error when dashboard data fails to load", async () => {
    getHealth.mockRejectedValue(new Error("Could not reach API"));

    render(<App />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not reach API");
  });
});

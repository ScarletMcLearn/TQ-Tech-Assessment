import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { NotificationTable } from "./NotificationTable";

const notification = {
  email_id: "incident-1",
  sender: "ops@example.com",
  subject: "Server down",
  priority: "HIGH",
  category: "SERVER_DOWN",
  reason: "Production API unavailable.",
  received_at: "2026-06-04T09:00:00Z",
};

describe("NotificationTable", () => {
  it("renders an empty state after loading finishes with no notifications", () => {
    render(<NotificationTable notifications={[]} isLoading={false} />);

    expect(screen.getByText("No important emails yet")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Run the agent or wait for the next poll to classify mock emails.",
      ),
    ).toBeInTheDocument();
  });

  it("keeps the table structure visible while loading", () => {
    render(<NotificationTable notifications={[]} isLoading />);

    expect(screen.getByRole("table", { name: "" })).toBeInTheDocument();
    expect(screen.getByText("Sender")).toBeInTheDocument();
  });

  it("renders notification details and priority badge", () => {
    render(<NotificationTable notifications={[notification]} isLoading={false} />);

    expect(screen.getByText("ops@example.com")).toBeInTheDocument();
    expect(screen.getByText("Server down")).toBeInTheDocument();
    expect(screen.getByText("HIGH")).toHaveClass("priority-high");
    expect(screen.getByText("SERVER_DOWN")).toBeInTheDocument();
    expect(screen.getByText("Production API unavailable.")).toBeInTheDocument();
  });
});

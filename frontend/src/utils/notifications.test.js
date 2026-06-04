import { describe, expect, it } from "vitest";

import { sortNotifications } from "./notifications";

describe("sortNotifications", () => {
  it("sorts by priority and newest received time without mutating input", () => {
    const notifications = [
      {
        email_id: "low-new",
        priority: "LOW",
        received_at: "2026-06-04T12:00:00Z",
      },
      {
        email_id: "high-old",
        priority: "HIGH",
        received_at: "2026-06-04T08:00:00Z",
      },
      {
        email_id: "medium",
        priority: "MEDIUM",
        received_at: "2026-06-04T10:00:00Z",
      },
      {
        email_id: "high-new",
        priority: "HIGH",
        received_at: "2026-06-04T11:00:00Z",
      },
    ];

    const sorted = sortNotifications(notifications);

    expect(sorted.map((notification) => notification.email_id)).toEqual([
      "high-new",
      "high-old",
      "medium",
      "low-new",
    ]);
    expect(notifications.map((notification) => notification.email_id)).toEqual([
      "low-new",
      "high-old",
      "medium",
      "high-new",
    ]);
  });

  it("keeps unknown priorities after known priorities", () => {
    const sorted = sortNotifications([
      {
        email_id: "unknown",
        priority: "CRITICAL",
        received_at: "2026-06-04T12:00:00Z",
      },
      {
        email_id: "low",
        priority: "LOW",
        received_at: "2026-06-04T08:00:00Z",
      },
    ]);

    expect(sorted.map((notification) => notification.email_id)).toEqual([
      "low",
      "unknown",
    ]);
  });
});

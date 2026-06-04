import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatusStrip } from "./StatusStrip";

describe("StatusStrip", () => {
  it("renders defaults before health data loads", () => {
    render(<StatusStrip health={null} lastUpdated={null} />);

    expect(screen.getByText("MOCK")).toBeInTheDocument();
    expect(screen.getByText("30s")).toBeInTheDocument();
    expect(screen.getByText("CHECKING")).toBeInTheDocument();
    expect(screen.getByText("pending")).toBeInTheDocument();
  });

  it("renders configured health status", () => {
    render(
      <StatusStrip
        health={{
          email_source: "mock",
          database: "ok",
          scheduler: { poll_interval_seconds: 45 },
        }}
        lastUpdated={new Date("2026-06-04T09:00:00Z")}
      />,
    );

    expect(screen.getByText("MOCK")).toBeInTheDocument();
    expect(screen.getByText("45s")).toBeInTheDocument();
    expect(screen.getByText("OK")).toBeInTheDocument();
  });
});

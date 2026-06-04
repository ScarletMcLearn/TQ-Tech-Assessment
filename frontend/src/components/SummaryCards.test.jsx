import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SummaryCards } from "./SummaryCards";

describe("SummaryCards", () => {
  it("renders priority counts and defaults missing counts to zero", () => {
    render(<SummaryCards counts={{ HIGH: 2, MEDIUM: 1 }} />);

    expect(
      within(screen.getByText("High priority").closest("article")).getByText("2"),
    ).toBeInTheDocument();
    expect(
      within(screen.getByText("Medium priority").closest("article")).getByText("1"),
    ).toBeInTheDocument();
    expect(
      within(screen.getByText("Low priority").closest("article")).getByText("0"),
    ).toBeInTheDocument();
  });
});

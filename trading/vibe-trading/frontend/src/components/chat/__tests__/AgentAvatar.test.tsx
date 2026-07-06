import { render, screen } from "@testing-library/react";
import { AgentAvatar } from "../AgentAvatar";

describe("AgentAvatar", () => {
  it("renders the letter P", () => {
    render(<AgentAvatar />);
    expect(screen.getByText("P")).toBeInTheDocument();
  });

  it("has gradient background styling", () => {
    const { container } = render(<AgentAvatar />);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toMatch(/bg-gradient/);
  });
});

import { render, screen } from "@testing-library/react";
import { ProgressBar } from "../ProgressBar";

describe("ProgressBar", () => {
  it("renders nothing when total <= 0", () => {
    const { container } = render(<ProgressBar current={5} total={0} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders nothing for negative total", () => {
    const { container } = render(<ProgressBar current={5} total={-1} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders a progress element", () => {
    render(<ProgressBar current={3} total={10} ariaLabel="test progress" />);
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("clamps current to [0, total]", () => {
    const { container: c1 } = render(<ProgressBar current={-5} total={10} />);
    const fill1 = c1.querySelector(".bg-primary") as HTMLElement;
    expect(fill1.style.width).toBe("0%");

    const { container: c2 } = render(<ProgressBar current={20} total={10} />);
    const fill2 = c2.querySelector(".bg-primary") as HTMLElement;
    expect(fill2.style.width).toBe("100%");
  });

  it("computes correct width percentage", () => {
    const { container } = render(<ProgressBar current={3} total={10} />);
    const fill = container.querySelector(".bg-primary") as HTMLElement;
    expect(fill.style.width).toBe("30%");
  });

  it("shows count when showCount is true", () => {
    render(<ProgressBar current={3} total={10} showCount />);
    expect(screen.getByText("3/10")).toBeInTheDocument();
  });

  it("does not show count by default", () => {
    const { container } = render(<ProgressBar current={3} total={10} />);
    expect(container.querySelector("span")).not.toBeInTheDocument();
  });

  it("uses h-1 height class by default (xs)", () => {
    const { container } = render(<ProgressBar current={3} total={10} />);
    const track = container.querySelector(".bg-muted");
    expect(track?.classList.contains("h-1")).toBe(true);
  });

  it("uses h-2 height class when height=sm", () => {
    const { container } = render(<ProgressBar current={3} total={10} height="sm" />);
    const track = container.querySelector(".bg-muted");
    expect(track?.classList.contains("h-2")).toBe(true);
  });
});

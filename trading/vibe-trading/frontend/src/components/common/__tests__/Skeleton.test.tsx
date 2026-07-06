import { render } from "@testing-library/react";
import { Skeleton, SkeletonMetrics, SkeletonChart } from "../Skeleton";

describe("Skeleton", () => {
  it("renders with animate-pulse class", () => {
    const { container } = render(<Skeleton />);
    const el = container.firstChild as HTMLElement;
    expect(el.classList.contains("animate-pulse")).toBe(true);
  });

  it("applies custom className", () => {
    const { container } = render(<Skeleton className="h-4 w-20" />);
    const el = container.firstChild as HTMLElement;
    expect(el.classList.contains("h-4")).toBe(true);
    expect(el.classList.contains("w-20")).toBe(true);
  });

  it("applies custom style", () => {
    const { container } = render(<Skeleton style={{ height: 42 }} />);
    const el = container.firstChild as HTMLElement;
    expect(el.style.height).toBe("42px");
  });
});

describe("SkeletonMetrics", () => {
  it("renders 6 skeleton items", () => {
    const { container } = render(<SkeletonMetrics />);
    const items = container.querySelectorAll(".animate-pulse");
    // Each of the 6 items has 2 skeleton elements (label + value)
    expect(items.length).toBe(12);
  });
});

describe("SkeletonChart", () => {
  it("renders with default height of 300", () => {
    const { container } = render(<SkeletonChart />);
    const el = container.firstChild as HTMLElement;
    expect(el.style.height).toBe("300px");
  });

  it("renders with custom height", () => {
    const { container } = render(<SkeletonChart height={200} />);
    const el = container.firstChild as HTMLElement;
    expect(el.style.height).toBe("200px");
  });
});

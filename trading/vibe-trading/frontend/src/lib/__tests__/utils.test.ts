import { cn } from "../utils";

describe("cn", () => {
  it("merges class names", () => {
    expect(cn("px-2", "py-1")).toBe("px-2 py-1");
  });

  it("deduplicates tailwind conflicts — last wins", () => {
    expect(cn("px-2", "px-4")).toBe("px-4");
  });

  it("handles conditional classes via clsx", () => {
    expect(cn("base", false && "hidden", "end")).toBe("base end");
  });

  it("handles undefined and null inputs", () => {
    expect(cn("a", undefined, null, "b")).toBe("a b");
  });

  it("handles empty input", () => {
    expect(cn()).toBe("");
  });

  it("merges complex tailwind conflicts", () => {
    expect(cn("bg-red-500", "bg-blue-500")).toBe("bg-blue-500");
  });

  it("preserves non-conflicting classes from different groups", () => {
    expect(cn("text-red-500", "bg-blue-500")).toBe("text-red-500 bg-blue-500");
  });
});

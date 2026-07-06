import { renderHook, act } from "@testing-library/react";
import { useDarkMode } from "../useDarkMode";

describe("useDarkMode", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove("dark");
  });

  it("defaults to light when no preference stored and OS is light", () => {
    const { result } = renderHook(() => useDarkMode());
    expect(result.current.dark).toBe(false);
  });

  it("reads dark preference from localStorage", () => {
    localStorage.setItem("qa-theme", "dark");
    const { result } = renderHook(() => useDarkMode());
    expect(result.current.dark).toBe(true);
  });

  it("reads light preference from localStorage", () => {
    localStorage.setItem("qa-theme", "light");
    const { result } = renderHook(() => useDarkMode());
    expect(result.current.dark).toBe(false);
  });

  it("toggles dark mode", () => {
    const { result } = renderHook(() => useDarkMode());
    expect(result.current.dark).toBe(false);

    act(() => result.current.toggle());
    expect(result.current.dark).toBe(true);

    act(() => result.current.toggle());
    expect(result.current.dark).toBe(false);
  });

  it("persists preference to localStorage on change", () => {
    const { result } = renderHook(() => useDarkMode());
    expect(localStorage.getItem("qa-theme")).toBe("light");

    act(() => result.current.toggle());
    expect(localStorage.getItem("qa-theme")).toBe("dark");

    act(() => result.current.toggle());
    expect(localStorage.getItem("qa-theme")).toBe("light");
  });

  it("toggles dark class on document.documentElement", () => {
    const { result } = renderHook(() => useDarkMode());
    expect(document.documentElement.classList.contains("dark")).toBe(false);

    act(() => result.current.toggle());
    expect(document.documentElement.classList.contains("dark")).toBe(true);

    act(() => result.current.toggle());
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });
});

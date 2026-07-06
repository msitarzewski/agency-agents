import { useEffect, useState } from "react";

export function useDarkMode() {
  const [dark, setDark] = useState(() => {
    const saved = localStorage.getItem("qa-theme");
    if (saved) return saved === "dark";
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("qa-theme", dark ? "dark" : "light");
  }, [dark]);

  return { dark, toggle: () => setDark((d) => !d) };
}

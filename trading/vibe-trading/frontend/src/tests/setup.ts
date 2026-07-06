import "@testing-library/jest-dom/vitest";
// Initialize i18n so `useTranslation()` resolves real strings in tests.
// With no localStorage entry under jsdom this falls back to English, keeping
// the suite's English assertions stable.
import "../i18n";

// ── Global mocks for jsdom ───────────────────────────────────

// jsdom doesn't implement ResizeObserver (ECharts + layout components need it)
globalThis.ResizeObserver = class {
  observe() {}
  unobserve() {}
  disconnect() {}
} as unknown as typeof ResizeObserver;

// jsdom doesn't implement matchMedia
if (typeof window !== "undefined") {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }),
  });
}

const STORAGE_KEY = "vibe_trading_api_auth_key";

export function getApiAuthKey(): string {
  return window.localStorage.getItem(STORAGE_KEY) || "";
}

export function setApiAuthKey(value: string): void {
  const trimmed = value.trim();
  if (trimmed) {
    window.localStorage.setItem(STORAGE_KEY, trimmed);
  } else {
    window.localStorage.removeItem(STORAGE_KEY);
  }
}

export function authHeaders(): Record<string, string> {
  const key = getApiAuthKey();
  return key ? { Authorization: `Bearer ${key}` } : {};
}

export function authQuerySuffix(): string {
  const key = getApiAuthKey();
  return key ? `api_key=${encodeURIComponent(key)}` : "";
}

export function withAuthQuery(url: string): string {
  const suffix = authQuerySuffix();
  if (!suffix) return url;
  return `${url}${url.includes("?") ? "&" : "?"}${suffix}`;
}

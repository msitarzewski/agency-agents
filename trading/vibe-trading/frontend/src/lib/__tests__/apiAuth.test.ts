import { getApiAuthKey, setApiAuthKey, authHeaders, authQuerySuffix, withAuthQuery } from "../apiAuth";

describe("apiAuth", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe("getApiAuthKey", () => {
    it("returns empty string when nothing stored", () => {
      expect(getApiAuthKey()).toBe("");
    });
    it("returns stored key", () => {
      localStorage.setItem("vibe_trading_api_auth_key", "my-secret");
      expect(getApiAuthKey()).toBe("my-secret");
    });
  });

  describe("setApiAuthKey", () => {
    it("stores trimmed value", () => {
      setApiAuthKey("  abc-123  ");
      expect(localStorage.getItem("vibe_trading_api_auth_key")).toBe("abc-123");
    });
    it("removes key when value is empty/whitespace", () => {
      setApiAuthKey("abc");
      setApiAuthKey("   ");
      expect(localStorage.getItem("vibe_trading_api_auth_key")).toBeNull();
    });
    it("removes key when value is empty string", () => {
      setApiAuthKey("abc");
      setApiAuthKey("");
      expect(localStorage.getItem("vibe_trading_api_auth_key")).toBeNull();
    });
  });

  describe("authHeaders", () => {
    it("returns empty object when no key set", () => {
      expect(authHeaders()).toEqual({});
    });
    it("returns Bearer header when key exists", () => {
      setApiAuthKey("token-xyz");
      expect(authHeaders()).toEqual({ Authorization: "Bearer token-xyz" });
    });
  });

  describe("authQuerySuffix", () => {
    it("returns empty string when no key", () => {
      expect(authQuerySuffix()).toBe("");
    });
    it("returns encoded query param when key exists", () => {
      setApiAuthKey("key with spaces");
      expect(authQuerySuffix()).toBe("api_key=key%20with%20spaces");
    });
  });

  describe("withAuthQuery", () => {
    it("returns url unchanged when no key", () => {
      expect(withAuthQuery("https://api.com/data")).toBe("https://api.com/data");
    });
    it("appends with ? when url has no query string", () => {
      setApiAuthKey("abc");
      expect(withAuthQuery("https://api.com/data")).toBe("https://api.com/data?api_key=abc");
    });
    it("appends with & when url already has query string", () => {
      setApiAuthKey("abc");
      expect(withAuthQuery("https://api.com/data?foo=bar")).toBe("https://api.com/data?foo=bar&api_key=abc");
    });
  });
});
